from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.services.aws_client import aws_client_manager
from app.models.aws_account import AWSAccount
from app.models.cost_data import CostData, CostSummary
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


class CostService:
    """Service for fetching and managing AWS cost data"""

    def __init__(self, db: Session):
        self.db = db

    async def fetch_costs_for_account(
        self,
        aws_account: AWSAccount,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Fetch cost data from AWS Cost Explorer for a specific account

        Args:
            aws_account: AWSAccount model instance
            start_date: Start date for cost data
            end_date: End date for cost data

        Returns:
            Dictionary with fetched cost data summary
        """
        try:
            # Get Cost Explorer client
            ce_client = aws_client_manager.get_cost_explorer_client(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region
            )

            # Format dates for AWS API
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # Fetch cost and usage data with tags
            response = ce_client.get_cost_and_usage(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Granularity='DAILY',
                Metrics=['UnblendedCost'],
                GroupBy=[
                    {'Type': 'DIMENSION', 'Key': 'SERVICE'},
                    {'Type': 'DIMENSION', 'Key': 'REGION'}
                ]
            )

            # Also try to fetch with tags (some accounts may not have tags enabled)
            try:
                tags_response = ce_client.get_cost_and_usage(
                    TimePeriod={
                        'Start': start_str,
                        'End': end_str
                    },
                    Granularity='DAILY',
                    Metrics=['UnblendedCost'],
                    GroupBy=[
                        {'Type': 'TAG', 'Key': 'Environment'},
                        {'Type': 'TAG', 'Key': 'Project'},
                        {'Type': 'TAG', 'Key': 'Team'}
                    ]
                )
            except Exception as e:
                logger.warning(f"Could not fetch tag-based costs: {str(e)}")
                tags_response = None

            # Process and store the cost data
            records_inserted = 0
            total_cost = 0.0

            for result in response.get('ResultsByTime', []):
                result_date = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d').date()

                for group in result.get('Groups', []):
                    service = group['Keys'][0] if len(group['Keys']) > 0 else 'Unknown'
                    region = group['Keys'][1] if len(group['Keys']) > 1 else 'Unknown'

                    cost_amount = float(group['Metrics']['UnblendedCost']['Amount'])
                    currency = group['Metrics']['UnblendedCost']['Unit']

                    if cost_amount > 0:  # Only store non-zero costs
                        # Check if record already exists
                        existing = self.db.query(CostData).filter(
                            CostData.aws_account_id == aws_account.id,
                            CostData.date == result_date,
                            CostData.service == service,
                            CostData.region == region
                        ).first()

                        if existing:
                            # Update existing record
                            existing.cost = cost_amount
                            existing.currency = currency
                        else:
                            # Create new record
                            cost_record = CostData(
                                tenant_id=aws_account.tenant_id,
                                aws_account_id=aws_account.id,
                                date=result_date,
                                service=service,
                                region=region,
                                cost=cost_amount,
                                currency=currency
                            )
                            self.db.add(cost_record)
                            records_inserted += 1

                        total_cost += cost_amount

            # Commit all changes
            self.db.commit()

            # Update account sync status
            aws_account.last_sync_at = datetime.utcnow()
            aws_account.sync_status = "success"
            self.db.commit()

            logger.info(f"Fetched cost data for account {aws_account.account_id}: {records_inserted} records, ${total_cost:.2f}")

            return {
                "success": True,
                "records_inserted": records_inserted,
                "total_cost": total_cost,
                "currency": "USD",
                "start_date": start_str,
                "end_date": end_str
            }

        except Exception as e:
            logger.error(f"Error fetching costs for account {aws_account.account_id}: {str(e)}")
            aws_account.sync_status = "error"
            self.db.commit()

            return {
                "success": False,
                "error": str(e)
            }

    async def get_cost_summary(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        aws_account_id: Optional[str] = None
    ) -> Dict:
        """
        Get cost summary for a tenant

        Args:
            tenant_id: Tenant UUID
            start_date: Start date
            end_date: End date
            aws_account_id: Optional AWS account filter

        Returns:
            Dictionary with cost summary data
        """
        query = self.db.query(
            CostData.service,
            func.sum(CostData.cost).label('total_cost')
        ).filter(
            CostData.tenant_id == tenant_id,
            CostData.date >= start_date,
            CostData.date <= end_date
        )

        if aws_account_id:
            query = query.filter(CostData.aws_account_id == aws_account_id)

        results = query.group_by(CostData.service).all()

        # Calculate total and breakdown
        total_cost = sum(result.total_cost for result in results)

        breakdown = [
            {
                "service": result.service,
                "cost": round(result.total_cost, 2),
                "percentage": round((result.total_cost / total_cost * 100) if total_cost > 0 else 0, 2)
            }
            for result in results
        ]

        # Sort by cost descending
        breakdown.sort(key=lambda x: x['cost'], reverse=True)

        return {
            "total_cost": round(total_cost, 2),
            "currency": "USD",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "breakdown": breakdown
        }

    async def get_cost_trend(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        aws_account_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get daily cost trend for a tenant

        Args:
            tenant_id: Tenant UUID
            start_date: Start date
            end_date: End date
            aws_account_id: Optional AWS account filter

        Returns:
            List of daily cost data points
        """
        query = self.db.query(
            CostData.date,
            func.sum(CostData.cost).label('total_cost')
        ).filter(
            CostData.tenant_id == tenant_id,
            CostData.date >= start_date,
            CostData.date <= end_date
        )

        if aws_account_id:
            query = query.filter(CostData.aws_account_id == aws_account_id)

        results = query.group_by(CostData.date).order_by(CostData.date).all()

        return [
            {
                "date": result.date.isoformat(),
                "cost": round(result.total_cost, 2)
            }
            for result in results
        ]

    async def get_cost_by_region(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        aws_account_id: Optional[str] = None
    ) -> Dict:
        """
        Get cost breakdown by region

        Args:
            tenant_id: Tenant UUID
            start_date: Start date
            end_date: End date
            aws_account_id: Optional AWS account filter

        Returns:
            Dictionary with cost breakdown by region
        """
        query = self.db.query(
            CostData.region,
            func.sum(CostData.cost).label('total_cost')
        ).filter(
            CostData.tenant_id == tenant_id,
            CostData.date >= start_date,
            CostData.date <= end_date
        )

        if aws_account_id:
            query = query.filter(CostData.aws_account_id == aws_account_id)

        results = query.group_by(CostData.region).all()

        # Calculate total and breakdown
        total_cost = sum(result.total_cost for result in results)

        breakdown = [
            {
                "region": result.region,
                "cost": round(result.total_cost, 2),
                "percentage": round((result.total_cost / total_cost * 100) if total_cost > 0 else 0, 2)
            }
            for result in results
        ]

        # Sort by cost descending
        breakdown.sort(key=lambda x: x['cost'], reverse=True)

        return {
            "total_cost": round(total_cost, 2),
            "currency": "USD",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "breakdown": breakdown
        }

    async def get_month_over_month_comparison(
        self,
        tenant_id: str,
        current_month_start: date,
        current_month_end: date,
        aws_account_id: Optional[str] = None
    ) -> Dict:
        """
        Compare current month costs with previous month

        Args:
            tenant_id: Tenant UUID
            current_month_start: Start of current month
            current_month_end: End of current month
            aws_account_id: Optional AWS account filter

        Returns:
            Dictionary with month-over-month comparison
        """
        # Calculate previous month dates
        prev_month_end = current_month_start - timedelta(days=1)
        days_in_current = (current_month_end - current_month_start).days + 1
        prev_month_start = prev_month_end - timedelta(days=days_in_current - 1)

        # Get current month costs
        current_query = self.db.query(
            func.sum(CostData.cost).label('total_cost')
        ).filter(
            CostData.tenant_id == tenant_id,
            CostData.date >= current_month_start,
            CostData.date <= current_month_end
        )

        if aws_account_id:
            current_query = current_query.filter(CostData.aws_account_id == aws_account_id)

        current_total = current_query.scalar() or 0.0

        # Get previous month costs
        prev_query = self.db.query(
            func.sum(CostData.cost).label('total_cost')
        ).filter(
            CostData.tenant_id == tenant_id,
            CostData.date >= prev_month_start,
            CostData.date <= prev_month_end
        )

        if aws_account_id:
            prev_query = prev_query.filter(CostData.aws_account_id == aws_account_id)

        prev_total = prev_query.scalar() or 0.0

        # Calculate change
        change_amount = current_total - prev_total
        change_percentage = ((change_amount / prev_total) * 100) if prev_total > 0 else 0

        return {
            "current_month": {
                "start_date": current_month_start.isoformat(),
                "end_date": current_month_end.isoformat(),
                "total_cost": round(current_total, 2)
            },
            "previous_month": {
                "start_date": prev_month_start.isoformat(),
                "end_date": prev_month_end.isoformat(),
                "total_cost": round(prev_total, 2)
            },
            "change": {
                "amount": round(change_amount, 2),
                "percentage": round(change_percentage, 2),
                "trend": "up" if change_amount > 0 else "down" if change_amount < 0 else "flat"
            },
            "currency": "USD"
        }

    async def get_cost_forecast(
        self,
        aws_account: AWSAccount,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Get cost forecast from AWS Cost Explorer

        Args:
            aws_account: AWSAccount model instance
            start_date: Forecast start date
            end_date: Forecast end date

        Returns:
            Dictionary with forecast data
        """
        try:
            ce_client = aws_client_manager.get_cost_explorer_client(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region
            )

            # Format dates
            start_str = start_date.strftime('%Y-%m-%d')
            end_str = end_date.strftime('%Y-%m-%d')

            # Get forecast
            response = ce_client.get_cost_forecast(
                TimePeriod={
                    'Start': start_str,
                    'End': end_str
                },
                Metric='UNBLENDED_COST',
                Granularity='DAILY'
            )

            # Process forecast data
            forecast_data = []
            for result in response.get('ForecastResultsByTime', []):
                forecast_date = datetime.strptime(result['TimePeriod']['Start'], '%Y-%m-%d').date()
                mean_value = float(result['MeanValue'])

                forecast_data.append({
                    "date": forecast_date.isoformat(),
                    "cost": round(mean_value, 2)
                })

            total_forecast = sum(item['cost'] for item in forecast_data)

            return {
                "success": True,
                "start_date": start_str,
                "end_date": end_str,
                "total_forecast": round(total_forecast, 2),
                "currency": "USD",
                "forecast": forecast_data
            }

        except Exception as e:
            logger.error(f"Error getting cost forecast: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_cost_by_tags(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date,
        tag_key: str,
        aws_account_id: Optional[str] = None
    ) -> Dict:
        """
        Get cost breakdown by a specific tag key

        Args:
            tenant_id: Tenant UUID
            start_date: Start date
            end_date: End date
            tag_key: The tag key to group by (e.g., 'Environment', 'Project')
            aws_account_id: Optional AWS account filter

        Returns:
            Dictionary with cost breakdown by tag values
        """
        # Query cost data and extract tag values
        query = self.db.query(CostData).filter(
            CostData.tenant_id == tenant_id,
            CostData.date >= start_date,
            CostData.date <= end_date,
            CostData.tags.isnot(None)
        )

        if aws_account_id:
            query = query.filter(CostData.aws_account_id == aws_account_id)

        results = query.all()

        # Aggregate costs by tag value
        tag_costs = {}
        for record in results:
            if record.tags and tag_key in record.tags:
                tag_value = record.tags[tag_key]
                if tag_value not in tag_costs:
                    tag_costs[tag_value] = 0.0
                tag_costs[tag_value] += record.cost

        # Calculate total and percentages
        total_cost = sum(tag_costs.values())

        breakdown = [
            {
                "tag_value": tag_value,
                "cost": round(cost, 2),
                "percentage": round((cost / total_cost * 100) if total_cost > 0 else 0, 2)
            }
            for tag_value, cost in tag_costs.items()
        ]

        # Sort by cost descending
        breakdown.sort(key=lambda x: x['cost'], reverse=True)

        return {
            "tag_key": tag_key,
            "total_cost": round(total_cost, 2),
            "currency": "USD",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "breakdown": breakdown
        }

    async def get_multi_account_summary(
        self,
        tenant_id: str,
        start_date: date,
        end_date: date
    ) -> Dict:
        """
        Get aggregated cost summary across all AWS accounts

        Args:
            tenant_id: Tenant UUID
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with multi-account cost breakdown
        """
        from app.models.aws_account import AWSAccount

        # Get all accounts for tenant
        accounts = self.db.query(AWSAccount).filter(
            AWSAccount.tenant_id == tenant_id,
            AWSAccount.is_active == True
        ).all()

        account_summaries = []
        total_cost = 0.0

        for account in accounts:
            # Get cost for this account
            account_query = self.db.query(
                func.sum(CostData.cost).label('total_cost')
            ).filter(
                CostData.tenant_id == tenant_id,
                CostData.aws_account_id == account.id,
                CostData.date >= start_date,
                CostData.date <= end_date
            )

            account_total = account_query.scalar() or 0.0
            total_cost += account_total

            account_summaries.append({
                "account_id": str(account.id),
                "account_name": account.account_name,
                "aws_account_id": account.account_id,
                "cost": round(account_total, 2),
                "region": account.region
            })

        # Calculate percentages
        for summary in account_summaries:
            summary["percentage"] = round(
                (summary["cost"] / total_cost * 100) if total_cost > 0 else 0,
                2
            )

        # Sort by cost descending
        account_summaries.sort(key=lambda x: x['cost'], reverse=True)

        return {
            "total_cost": round(total_cost, 2),
            "currency": "USD",
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "account_count": len(accounts),
            "accounts": account_summaries
        }
