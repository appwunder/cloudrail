from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
import logging

from app.services.aws_client import aws_client_manager
from app.models.aws_account import AWSAccount
from app.models.cost_data import CostData

logger = logging.getLogger(__name__)


class RecommendationsService:
    """Service for generating cost optimization recommendations"""

    def __init__(self, db: Session):
        self.db = db

    async def get_all_recommendations(
        self,
        tenant_id: str,
        aws_account: Optional[AWSAccount] = None
    ) -> List[Dict]:
        """
        Get all cost optimization recommendations for a tenant

        Args:
            tenant_id: Tenant UUID
            aws_account: Optional specific AWS account

        Returns:
            List of recommendation dictionaries
        """
        recommendations = []

        if aws_account:
            # Get AWS-specific recommendations
            compute_recs = await self._get_compute_optimizer_recommendations(aws_account)
            recommendations.extend(compute_recs)

            ebs_recs = await self._get_unattached_volumes_recommendations(aws_account)
            recommendations.extend(ebs_recs)

            snapshot_recs = await self._get_old_snapshots_recommendations(aws_account)
            recommendations.extend(snapshot_recs)

            idle_recs = await self._get_idle_resources_recommendations(aws_account)
            recommendations.extend(idle_recs)

            ri_sp_recs = await self._get_ri_savings_plans_recommendations(aws_account)
            recommendations.extend(ri_sp_recs)

            rds_recs = await self._get_rds_rightsizing_recommendations(aws_account)
            recommendations.extend(rds_recs)

        # Get cost-based recommendations from our data
        cost_recs = await self._get_cost_based_recommendations(tenant_id)
        recommendations.extend(cost_recs)

        # Sort by potential savings (descending)
        recommendations.sort(key=lambda x: x.get('potential_savings', 0), reverse=True)

        return recommendations

    async def _get_compute_optimizer_recommendations(
        self,
        aws_account: AWSAccount
    ) -> List[Dict]:
        """Get EC2 rightsizing recommendations from AWS Compute Optimizer"""
        recommendations = []

        try:
            # Get Compute Optimizer client
            compute_optimizer = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region,
                service_name='compute-optimizer'
            )

            # Get EC2 recommendations
            response = compute_optimizer.get_ec2_instance_recommendations(maxResults=100)

            for rec in response.get('instanceRecommendations', []):
                current_instance = rec.get('currentInstanceType', '')
                recommended_options = rec.get('recommendationOptions', [])

                if recommended_options:
                    best_option = recommended_options[0]
                    recommended_instance = best_option.get('instanceType', '')

                    # Calculate estimated savings
                    savings_opportunity = rec.get('finding', '') == 'Underprovisioned'
                    estimated_savings = 0

                    if 'savingsOpportunity' in best_option:
                        savings_data = best_option['savingsOpportunity']
                        estimated_savings = savings_data.get('estimatedMonthlySavings', {}).get('value', 0)

                    recommendations.append({
                        'id': f"compute-{rec.get('instanceArn', '')}",
                        'type': 'rightsizing',
                        'category': 'compute',
                        'severity': 'medium' if estimated_savings > 50 else 'low',
                        'title': f'Rightsize EC2 Instance',
                        'description': f'Instance {current_instance} can be optimized to {recommended_instance}',
                        'resource': rec.get('instanceArn', ''),
                        'current_config': current_instance,
                        'recommended_config': recommended_instance,
                        'potential_savings': float(estimated_savings),
                        'savings_currency': 'USD',
                        'finding': rec.get('finding', ''),
                        'action': 'Change instance type',
                        'effort': 'medium'
                    })

        except Exception as e:
            logger.warning(f"Could not fetch Compute Optimizer recommendations: {str(e)}")
            # This is expected if Compute Optimizer is not enabled

        return recommendations

    async def _get_unattached_volumes_recommendations(
        self,
        aws_account: AWSAccount
    ) -> List[Dict]:
        """Detect unattached EBS volumes"""
        recommendations = []

        try:
            ec2 = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region,
                service_name='ec2'
            )

            # Get all volumes
            response = ec2.describe_volumes(
                Filters=[{'Name': 'status', 'Values': ['available']}]
            )

            for volume in response.get('Volumes', []):
                volume_id = volume['VolumeId']
                size_gb = volume['Size']
                volume_type = volume['VolumeType']

                # Estimate monthly cost (rough estimate)
                cost_per_gb = {
                    'gp2': 0.10,
                    'gp3': 0.08,
                    'io1': 0.125,
                    'io2': 0.125,
                    'st1': 0.045,
                    'sc1': 0.025
                }
                monthly_cost = size_gb * cost_per_gb.get(volume_type, 0.10)

                recommendations.append({
                    'id': f"ebs-{volume_id}",
                    'type': 'unused_resource',
                    'category': 'storage',
                    'severity': 'high' if monthly_cost > 10 else 'medium',
                    'title': 'Delete Unattached EBS Volume',
                    'description': f'EBS volume {volume_id} ({size_gb}GB {volume_type}) is unattached and costing money',
                    'resource': volume_id,
                    'current_config': f'{size_gb}GB {volume_type}',
                    'recommended_config': 'Delete or snapshot and delete',
                    'potential_savings': monthly_cost,
                    'savings_currency': 'USD',
                    'action': 'Create snapshot if needed, then delete volume',
                    'effort': 'low'
                })

        except Exception as e:
            logger.warning(f"Could not fetch EBS volumes: {str(e)}")

        return recommendations

    async def _get_old_snapshots_recommendations(
        self,
        aws_account: AWSAccount
    ) -> List[Dict]:
        """Detect old EBS snapshots that can be deleted"""
        recommendations = []

        try:
            ec2 = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region,
                service_name='ec2'
            )

            # Get snapshots older than 180 days
            response = ec2.describe_snapshots(OwnerIds=['self'])

            cutoff_date = datetime.now() - timedelta(days=180)

            for snapshot in response.get('Snapshots', []):
                start_time = snapshot['StartTime']
                # Remove timezone info for comparison
                if start_time.tzinfo:
                    start_time = start_time.replace(tzinfo=None)

                if start_time < cutoff_date:
                    snapshot_id = snapshot['SnapshotId']
                    size_gb = snapshot['VolumeSize']
                    age_days = (datetime.now() - start_time).days

                    # EBS snapshot cost: ~$0.05 per GB-month
                    monthly_cost = size_gb * 0.05

                    recommendations.append({
                        'id': f"snapshot-{snapshot_id}",
                        'type': 'old_resource',
                        'category': 'storage',
                        'severity': 'low',
                        'title': 'Delete Old EBS Snapshot',
                        'description': f'Snapshot {snapshot_id} is {age_days} days old ({size_gb}GB)',
                        'resource': snapshot_id,
                        'current_config': f'{size_gb}GB, {age_days} days old',
                        'recommended_config': 'Delete if no longer needed',
                        'potential_savings': monthly_cost,
                        'savings_currency': 'USD',
                        'action': 'Review and delete if not needed',
                        'effort': 'low'
                    })

        except Exception as e:
            logger.warning(f"Could not fetch snapshots: {str(e)}")

        return recommendations

    async def _get_idle_resources_recommendations(
        self,
        aws_account: AWSAccount
    ) -> List[Dict]:
        """Detect idle EC2 instances and RDS databases"""
        recommendations = []

        try:
            # Get CloudWatch client
            cloudwatch = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region,
                service_name='cloudwatch'
            )

            ec2 = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region,
                service_name='ec2'
            )

            # Get all running instances
            response = ec2.describe_instances(
                Filters=[{'Name': 'instance-state-name', 'Values': ['running']}]
            )

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=7)

            for reservation in response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']

                    # Get CPU utilization
                    cpu_response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/EC2',
                        MetricName='CPUUtilization',
                        Dimensions=[{'Name': 'InstanceId', 'Value': instance_id}],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=86400,  # 1 day
                        Statistics=['Average']
                    )

                    datapoints = cpu_response.get('Datapoints', [])
                    if datapoints:
                        avg_cpu = sum(d['Average'] for d in datapoints) / len(datapoints)

                        # If average CPU < 5% over 7 days, consider it idle
                        if avg_cpu < 5.0:
                            # Rough monthly cost estimate (simplified)
                            estimated_cost = 50.0  # Placeholder

                            recommendations.append({
                                'id': f"idle-{instance_id}",
                                'type': 'idle_resource',
                                'category': 'compute',
                                'severity': 'high',
                                'title': 'Stop or Terminate Idle EC2 Instance',
                                'description': f'Instance {instance_id} ({instance_type}) has {avg_cpu:.1f}% average CPU utilization',
                                'resource': instance_id,
                                'current_config': f'{instance_type}, {avg_cpu:.1f}% CPU',
                                'recommended_config': 'Stop or terminate',
                                'potential_savings': estimated_cost,
                                'savings_currency': 'USD',
                                'action': 'Stop instance if temporary, terminate if not needed',
                                'effort': 'low'
                            })

        except Exception as e:
            logger.warning(f"Could not analyze idle resources: {str(e)}")

        return recommendations

    async def _get_cost_based_recommendations(
        self,
        tenant_id: str
    ) -> List[Dict]:
        """Generate recommendations based on cost data analysis"""
        recommendations = []

        # Get top services by cost
        thirty_days_ago = date.today() - timedelta(days=30)

        top_services = self.db.query(
            CostData.service,
            func.sum(CostData.cost).label('total_cost')
        ).filter(
            CostData.tenant_id == tenant_id,
            CostData.date >= thirty_days_ago
        ).group_by(
            CostData.service
        ).order_by(
            func.sum(CostData.cost).desc()
        ).limit(5).all()

        for service_data in top_services:
            service = service_data.service
            total_cost = service_data.total_cost

            if total_cost > 100:  # Only recommend for services costing >$100/month
                recommendations.append({
                    'id': f"cost-{service}",
                    'type': 'cost_analysis',
                    'category': 'general',
                    'severity': 'medium',
                    'title': f'Review {service} Usage',
                    'description': f'{service} is a top cost driver at ${total_cost:.2f}/month',
                    'resource': service,
                    'current_config': f'${total_cost:.2f}/month',
                    'recommended_config': 'Review usage and optimize',
                    'potential_savings': total_cost * 0.15,  # Estimate 15% potential savings
                    'savings_currency': 'USD',
                    'action': 'Analyze usage patterns and look for optimization opportunities',
                    'effort': 'medium'
                })

        return recommendations

    async def _get_ri_savings_plans_recommendations(
        self,
        aws_account: AWSAccount
    ) -> List[Dict]:
        """Analyze Reserved Instance and Savings Plans opportunities"""
        recommendations = []

        try:
            # Get Cost Explorer client
            ce_client = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region='us-east-1',  # Cost Explorer is only in us-east-1
                service_name='ce'
            )

            # Get RI coverage
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)

            # Get RI coverage for EC2
            try:
                ri_coverage_response = ce_client.get_reservation_coverage(
                    TimePeriod={
                        'Start': start_date.isoformat(),
                        'End': end_date.isoformat()
                    },
                    Granularity='MONTHLY',
                    GroupBy=[
                        {'Type': 'DIMENSION', 'Key': 'SERVICE'}
                    ]
                )

                for coverage_group in ri_coverage_response.get('CoveragesByTime', []):
                    for group in coverage_group.get('Groups', []):
                        service = group.get('Keys', ['Unknown'])[0]
                        coverage = group.get('Coverage', {})
                        coverage_pct = float(coverage.get('CoverageHours', {}).get('CoverageHoursPercentage', '0'))

                        # If coverage is low, recommend RI/SP
                        if coverage_pct < 70 and coverage_pct > 0:
                            on_demand_cost = float(coverage.get('CoverageCost', {}).get('OnDemandCost', '0'))
                            # Estimate 30-40% savings with RI/SP
                            estimated_savings = on_demand_cost * 0.35

                            if estimated_savings > 10:  # Only recommend if savings > $10/month
                                recommendations.append({
                                    'id': f"ri-sp-{service}",
                                    'type': 'reserved_instance',
                                    'category': 'commitment',
                                    'severity': 'high' if estimated_savings > 100 else 'medium',
                                    'title': f'Purchase Reserved Instances or Savings Plans for {service}',
                                    'description': f'{service} has only {coverage_pct:.1f}% RI coverage. Consider purchasing RIs or Savings Plans.',
                                    'resource': service,
                                    'current_config': f'{coverage_pct:.1f}% covered',
                                    'recommended_config': 'Target 70-80% coverage with RI or Savings Plans',
                                    'potential_savings': estimated_savings,
                                    'savings_currency': 'USD',
                                    'action': 'Analyze usage patterns and purchase appropriate RI/SP commitments',
                                    'effort': 'high',
                                    'details': {
                                        'coverage_percentage': coverage_pct,
                                        'on_demand_cost': on_demand_cost,
                                        'recommendation_type': 'Reserved Instance / Savings Plan'
                                    }
                                })
            except Exception as e:
                logger.debug(f"Could not fetch RI coverage: {str(e)}")

            # Get Savings Plans recommendations
            try:
                sp_recommendations = ce_client.get_savings_plans_purchase_recommendation(
                    SavingsPlansType='COMPUTE_SP',
                    TermInYears='ONE_YEAR',
                    PaymentOption='NO_UPFRONT',
                    LookbackPeriodInDays='SIXTY_DAYS'
                )

                for rec in sp_recommendations.get('SavingsPlansPurchaseRecommendation', {}).get('SavingsPlansPurchaseRecommendationDetails', []):
                    hourly_commitment = float(rec.get('HourlyCommitmentToPurchase', 0))
                    estimated_monthly_savings = float(rec.get('EstimatedMonthlySavingsAmount', 0))
                    estimated_roi = float(rec.get('EstimatedROI', '0'))

                    if estimated_monthly_savings > 10:
                        recommendations.append({
                            'id': f"sp-{rec.get('AccountId', 'unknown')}",
                            'type': 'savings_plan',
                            'category': 'commitment',
                            'severity': 'high' if estimated_monthly_savings > 100 else 'medium',
                            'title': 'Purchase Compute Savings Plan',
                            'description': f'Savings Plan can save ${estimated_monthly_savings:.2f}/month with {estimated_roi:.1f}% ROI',
                            'resource': 'Compute Savings Plan',
                            'current_config': 'On-Demand pricing',
                            'recommended_config': f'${hourly_commitment:.2f}/hour commitment',
                            'potential_savings': estimated_monthly_savings,
                            'savings_currency': 'USD',
                            'action': f'Purchase Compute Savings Plan with ${hourly_commitment:.2f}/hour commitment',
                            'effort': 'high',
                            'details': {
                                'hourly_commitment': hourly_commitment,
                                'estimated_roi': estimated_roi,
                                'term': '1 Year',
                                'payment_option': 'No Upfront',
                                'recommendation_type': 'Savings Plan'
                            }
                        })
            except Exception as e:
                logger.debug(f"Could not fetch Savings Plans recommendations: {str(e)}")

        except Exception as e:
            logger.warning(f"Could not fetch RI/Savings Plans recommendations: {str(e)}")

        return recommendations

    async def _get_rds_rightsizing_recommendations(
        self,
        aws_account: AWSAccount
    ) -> List[Dict]:
        """Generate RDS instance rightsizing recommendations based on CloudWatch metrics"""
        recommendations = []

        try:
            # Get RDS client
            rds_client = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region,
                service_name='rds'
            )

            # Get CloudWatch client for metrics
            cloudwatch = aws_client_manager.assume_role(
                role_arn=aws_account.role_arn,
                external_id=aws_account.external_id,
                region=aws_account.region,
                service_name='cloudwatch'
            )

            # Get all RDS instances
            response = rds_client.describe_db_instances()

            for db_instance in response.get('DBInstances', []):
                instance_id = db_instance['DBInstanceIdentifier']
                instance_class = db_instance['DBInstanceClass']
                engine = db_instance['Engine']
                allocated_storage = db_instance['AllocatedStorage']

                # Get CPU utilization metrics for the past 14 days
                end_time = datetime.now()
                start_time = end_time - timedelta(days=14)

                cpu_metrics = cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='CPUUtilization',
                    Dimensions=[
                        {'Name': 'DBInstanceIdentifier', 'Value': instance_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,  # 1 day
                    Statistics=['Average', 'Maximum']
                )

                # Get connection count
                connection_metrics = cloudwatch.get_metric_statistics(
                    Namespace='AWS/RDS',
                    MetricName='DatabaseConnections',
                    Dimensions=[
                        {'Name': 'DBInstanceIdentifier', 'Value': instance_id}
                    ],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=86400,
                    Statistics=['Average', 'Maximum']
                )

                # Analyze metrics
                if cpu_metrics.get('Datapoints'):
                    avg_cpu = sum(dp['Average'] for dp in cpu_metrics['Datapoints']) / len(cpu_metrics['Datapoints'])
                    max_cpu = max(dp['Maximum'] for dp in cpu_metrics['Datapoints'])
                else:
                    avg_cpu = 0
                    max_cpu = 0

                if connection_metrics.get('Datapoints'):
                    avg_connections = sum(dp['Average'] for dp in connection_metrics['Datapoints']) / len(connection_metrics['Datapoints'])
                    max_connections = max(dp['Maximum'] for dp in connection_metrics['Datapoints'])
                else:
                    avg_connections = 0
                    max_connections = 0

                # Determine if rightsizing is needed
                recommendation_reason = None
                suggested_class = None
                severity = 'low'

                # Check for over-provisioned instances (low CPU and low connections)
                if avg_cpu < 20 and max_cpu < 40:
                    recommendation_reason = f'CPU utilization is low (avg: {avg_cpu:.1f}%, max: {max_cpu:.1f}%)'
                    # Suggest one tier down
                    if 'db.t3.medium' in instance_class:
                        suggested_class = instance_class.replace('medium', 'small')
                    elif 'db.t3.large' in instance_class:
                        suggested_class = instance_class.replace('large', 'medium')
                    elif 'db.m5.large' in instance_class:
                        suggested_class = 'db.t3.large'
                    elif 'db.m5.xlarge' in instance_class:
                        suggested_class = instance_class.replace('xlarge', 'large')
                    elif 'db.r5.large' in instance_class:
                        suggested_class = 'db.t3.large'

                    severity = 'medium'

                # Check for under-provisioned instances (high CPU consistently)
                elif avg_cpu > 70 or max_cpu > 90:
                    recommendation_reason = f'CPU utilization is high (avg: {avg_cpu:.1f}%, max: {max_cpu:.1f}%)'
                    # Suggest one tier up
                    if 'db.t3.small' in instance_class:
                        suggested_class = instance_class.replace('small', 'medium')
                    elif 'db.t3.medium' in instance_class:
                        suggested_class = instance_class.replace('medium', 'large')
                    elif 'db.t3.large' in instance_class:
                        suggested_class = 'db.m5.large'

                    severity = 'high'

                if suggested_class and suggested_class != instance_class:
                    # Estimate cost savings/increase
                    # Rough pricing estimates per hour (actual prices vary by region)
                    instance_pricing = {
                        'db.t3.micro': 0.017,
                        'db.t3.small': 0.034,
                        'db.t3.medium': 0.068,
                        'db.t3.large': 0.136,
                        'db.m5.large': 0.192,
                        'db.m5.xlarge': 0.384,
                        'db.r5.large': 0.240,
                        'db.r5.xlarge': 0.480,
                    }

                    current_hourly = instance_pricing.get(instance_class, 0.1)
                    suggested_hourly = instance_pricing.get(suggested_class, 0.1)
                    monthly_savings = (current_hourly - suggested_hourly) * 730  # 730 hours/month avg

                    recommendations.append({
                        'id': f"rds-{instance_id}",
                        'type': 'rightsizing',
                        'category': 'database',
                        'severity': severity,
                        'title': f'Rightsize RDS Instance {instance_id}',
                        'description': f'{recommendation_reason}. Consider changing from {instance_class} to {suggested_class}.',
                        'resource': instance_id,
                        'current_config': f'{instance_class} ({engine})',
                        'recommended_config': f'{suggested_class} ({engine})',
                        'potential_savings': abs(monthly_savings),
                        'savings_currency': 'USD',
                        'action': f'{"Downsize" if monthly_savings > 0 else "Upsize"} RDS instance to {suggested_class}',
                        'effort': 'medium',
                        'details': {
                            'avg_cpu_utilization': avg_cpu,
                            'max_cpu_utilization': max_cpu,
                            'avg_connections': avg_connections,
                            'max_connections': max_connections,
                            'engine': engine,
                            'allocated_storage_gb': allocated_storage,
                            'change_type': 'downsize' if monthly_savings > 0 else 'upsize'
                        }
                    })

        except Exception as e:
            logger.warning(f"Could not fetch RDS rightsizing recommendations: {str(e)}")

        return recommendations
