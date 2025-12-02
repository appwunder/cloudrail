from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkbssopenapi.request.v20171214 import QueryAccountBillRequest, QueryBillOverviewRequest
import json
import logging

from .base import CloudProviderService, CostRecord

logger = logging.getLogger(__name__)


class AlibabaBSSService(CloudProviderService):
    """Alibaba Cloud BSS (Business Support System) service implementation"""

    def __init__(self, credentials: Dict[str, Any], account_id: str, region: Optional[str] = None):
        """
        Initialize Alibaba Cloud BSS service

        Args:
            credentials: Dict containing 'access_key_id', 'access_key_secret'
            account_id: Alibaba Cloud Account ID
            region: Default region (default: cn-hangzhou for BSS API)
        """
        super().__init__(credentials, account_id, region or 'cn-hangzhou')
        self.access_key_id = credentials.get('access_key_id')
        self.access_key_secret = credentials.get('access_key_secret')
        self._client = None

    def validate_credentials(self) -> bool:
        """Validate Alibaba Cloud credentials format"""
        required_fields = ['access_key_id', 'access_key_secret']
        return all(field in self.credentials and self.credentials[field] for field in required_fields)

    def authenticate(self) -> bool:
        """Authenticate with Alibaba Cloud using Access Key"""
        try:
            # Create AcsClient for BSS API
            # BSS API is typically in cn-hangzhou region
            self._client = AcsClient(
                ak=self.access_key_id,
                secret=self.access_key_secret,
                region_id='cn-hangzhou'  # BSS API endpoint
            )

            logger.info(f"Successfully authenticated with Alibaba Cloud for account {self.account_id}")
            return True

        except Exception as e:
            logger.error(f"Alibaba Cloud authentication failed: {str(e)}")
            raise Exception(f"Alibaba Cloud authentication failed: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Alibaba Cloud and verify access"""
        try:
            if not self._client:
                self.authenticate()

            # Try to query account bill overview for current month
            request = QueryBillOverviewRequest.QueryBillOverviewRequest()
            request.set_accept_format('json')

            # Set billing cycle (current month)
            current_month = datetime.now().strftime("%Y-%m")
            request.set_BillingCycle(current_month)

            response = self._client.do_action_with_exception(request)
            result = json.loads(response)

            if result.get('Success'):
                return {
                    "success": True,
                    "message": "Successfully connected to Alibaba Cloud",
                    "account_info": {
                        "account_id": self.account_id,
                        "billing_cycle": current_month
                    }
                }
            else:
                return {
                    "success": False,
                    "message": "Connection failed",
                    "error": result.get('Message', 'Unknown error')
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": str(e)
            }

    def get_account_info(self) -> Dict[str, Any]:
        """Get Alibaba Cloud account information"""
        return {
            "account_id": self.account_id,
            "access_key_id": self.access_key_id,
            "region": self.region
        }

    def fetch_costs(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "daily"
    ) -> List[CostRecord]:
        """
        Fetch cost data from Alibaba Cloud BSS API

        Args:
            start_date: Start date
            end_date: End date
            granularity: daily or monthly

        Returns:
            List of cost records
        """
        if not self._client:
            self.authenticate()

        logger.info(f"Fetching Alibaba Cloud costs for {self.account_id} from {start_date} to {end_date}")

        cost_records = []

        try:
            # Alibaba Cloud BSS API works on monthly billing cycles
            # Generate list of billing cycles to query
            current_date = start_date.replace(day=1)
            end_month = end_date.replace(day=1)

            while current_date <= end_month:
                billing_cycle = current_date.strftime("%Y-%m")

                # Query bill overview for the month
                request = QueryBillOverviewRequest.QueryBillOverviewRequest()
                request.set_accept_format('json')
                request.set_BillingCycle(billing_cycle)

                try:
                    response = self._client.do_action_with_exception(request)
                    result = json.loads(response)

                    if result.get('Success') and result.get('Data'):
                        items = result['Data'].get('Items', {}).get('Item', [])

                        for item in items:
                            product_name = item.get('ProductName', 'Unknown')
                            pretax_gross_amount = float(item.get('PretaxGrossAmount', 0))
                            currency = item.get('Currency', 'CNY')
                            product_code = item.get('ProductCode', '')

                            # Create cost record
                            cost_record = CostRecord(
                                date=current_date,
                                service_name=self.format_service_name(product_name),
                                service_category=product_code,
                                resource_id=None,
                                resource_name=None,
                                region=item.get('BillingRegion', None),
                                cost=pretax_gross_amount,
                                currency=currency,
                                usage_quantity=None,
                                usage_unit=None,
                                tags={},
                                provider_metadata={
                                    "provider": "alibaba",
                                    "account_id": self.account_id,
                                    "billing_cycle": billing_cycle,
                                    "product_code": product_code
                                }
                            )

                            cost_records.append(cost_record)

                except Exception as e:
                    logger.warning(f"Failed to fetch costs for billing cycle {billing_cycle}: {str(e)}")

                # Move to next month
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)

            logger.info(f"Fetched {len(cost_records)} cost records from Alibaba Cloud")
            return cost_records

        except Exception as e:
            logger.error(f"Error while fetching Alibaba Cloud costs: {str(e)}")
            raise Exception(f"Failed to fetch Alibaba Cloud costs: {str(e)}")

    def format_service_name(self, raw_service: str) -> str:
        """Standardize Alibaba Cloud service names"""
        # Alibaba service name mapping
        service_mapping = {
            'ecs': 'Elastic Compute Service',
            'oss': 'Object Storage Service',
            'rds': 'Relational Database Service',
            'slb': 'Server Load Balancer',
            'vpc': 'Virtual Private Cloud',
            # Add more mappings as needed
        }

        service_lower = raw_service.lower()
        return service_mapping.get(service_lower, raw_service)

    def close(self):
        """Close Alibaba Cloud client connections"""
        if self._client:
            self._client = None
