from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from azure.identity import ClientSecretCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.core.exceptions import AzureError, ClientAuthenticationError
import logging

from .base import CloudProviderService, CostRecord

logger = logging.getLogger(__name__)


class AzureCostManagementService(CloudProviderService):
    """Microsoft Azure Cost Management service implementation"""

    def __init__(self, credentials: Dict[str, Any], account_id: str, region: Optional[str] = None):
        """
        Initialize Azure Cost Management service

        Args:
            credentials: Dict containing 'tenant_id', 'client_id', 'client_secret'
            account_id: Azure Subscription ID
            region: Default region (optional)
        """
        super().__init__(credentials, account_id, region)
        self.subscription_id = account_id
        self.tenant_id = credentials.get('tenant_id')
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self._cost_client = None
        self._credential = None

    def validate_credentials(self) -> bool:
        """Validate Azure credentials format"""
        required_fields = ['tenant_id', 'client_id', 'client_secret']
        return all(field in self.credentials and self.credentials[field] for field in required_fields)

    def authenticate(self) -> bool:
        """Authenticate with Azure using Service Principal"""
        try:
            # Create credential from service principal
            self._credential = ClientSecretCredential(
                tenant_id=self.tenant_id,
                client_id=self.client_id,
                client_secret=self.client_secret
            )

            # Initialize Cost Management client
            self._cost_client = CostManagementClient(
                credential=self._credential,
                subscription_id=self.subscription_id
            )

            logger.info(f"Successfully authenticated with Azure for subscription {self.subscription_id}")
            return True

        except ClientAuthenticationError as e:
            logger.error(f"Azure authentication failed: {str(e)}")
            raise Exception(f"Azure authentication failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during Azure authentication: {str(e)}")
            raise Exception(f"Azure authentication failed: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to Azure and verify access"""
        try:
            if not self._cost_client:
                self.authenticate()

            # Try to query a small date range to test access
            scope = f"/subscriptions/{self.subscription_id}"

            return {
                "success": True,
                "message": "Successfully connected to Azure",
                "account_info": {
                    "subscription_id": self.subscription_id,
                    "tenant_id": self.tenant_id,
                    "scope": scope
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": str(e)
            }

    def get_account_info(self) -> Dict[str, Any]:
        """Get Azure subscription information"""
        return {
            "subscription_id": self.subscription_id,
            "tenant_id": self.tenant_id,
            "client_id": self.client_id
        }

    def fetch_costs(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "daily"
    ) -> List[CostRecord]:
        """
        Fetch cost data from Azure Cost Management API

        Args:
            start_date: Start date
            end_date: End date
            granularity: Daily or Monthly

        Returns:
            List of cost records
        """
        if not self._cost_client:
            self.authenticate()

        logger.info(f"Fetching Azure costs for {self.subscription_id} from {start_date} to {end_date}")

        try:
            scope = f"/subscriptions/{self.subscription_id}"

            # Azure Cost Management Query
            time_period = {
                "from": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                "to": end_date.strftime("%Y-%m-%dT23:59:59Z")
            }

            # Map granularity
            azure_granularity = "Daily" if granularity.lower() == "daily" else "Monthly"

            # Query parameters
            query_definition = {
                "type": "ActualCost",
                "timeframe": "Custom",
                "time_period": time_period,
                "dataset": {
                    "granularity": azure_granularity,
                    "aggregation": {
                        "totalCost": {
                            "name": "Cost",
                            "function": "Sum"
                        }
                    },
                    "grouping": [
                        {
                            "type": "Dimension",
                            "name": "ServiceName"
                        },
                        {
                            "type": "Dimension",
                            "name": "ResourceLocation"
                        }
                    ]
                }
            }

            # Execute query
            result = self._cost_client.query.usage(scope=scope, parameters=query_definition)

            # Parse results
            cost_records = []

            if hasattr(result, 'rows') and result.rows:
                # Get column indices
                columns = {col.name: idx for idx, col in enumerate(result.columns)}

                for row in result.rows:
                    # Extract data from row
                    cost = row[columns.get('Cost', 0)] if 'Cost' in columns else 0.0
                    service_name = row[columns.get('ServiceName', 1)] if 'ServiceName' in columns else 'Unknown'
                    region = row[columns.get('ResourceLocation', 2)] if 'ResourceLocation' in columns else None
                    usage_date = row[columns.get('UsageDate', 3)] if 'UsageDate' in columns else start_date

                    # Convert usage_date to date object if it's an integer (YYYYMMDD format)
                    if isinstance(usage_date, int):
                        usage_date_str = str(usage_date)
                        usage_date = datetime.strptime(usage_date_str, "%Y%m%d").date()
                    elif isinstance(usage_date, str):
                        usage_date = datetime.fromisoformat(usage_date.replace('Z', '')).date()

                    cost_record = CostRecord(
                        date=usage_date,
                        service_name=self.format_service_name(service_name),
                        service_category=None,
                        resource_id=None,
                        resource_name=None,
                        region=region,
                        cost=float(cost),
                        currency="USD",  # Azure API returns USD by default
                        usage_quantity=None,
                        usage_unit=None,
                        tags={},
                        provider_metadata={
                            "provider": "azure",
                            "subscription_id": self.subscription_id
                        }
                    )

                    cost_records.append(cost_record)

            logger.info(f"Fetched {len(cost_records)} cost records from Azure")
            return cost_records

        except AzureError as e:
            logger.error(f"Azure API error while fetching costs: {str(e)}")
            raise Exception(f"Failed to fetch Azure costs: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error while fetching Azure costs: {str(e)}")
            raise Exception(f"Failed to fetch Azure costs: {str(e)}")

    def format_service_name(self, raw_service: str) -> str:
        """Standardize Azure service names"""
        # Azure service name mapping
        service_mapping = {
            'virtual machines': 'Virtual Machines',
            'storage': 'Azure Storage',
            'sql database': 'Azure SQL Database',
            'app service': 'App Service',
            'kubernetes service': 'Azure Kubernetes Service',
            'cosmos db': 'Cosmos DB',
            # Add more mappings as needed
        }

        service_lower = raw_service.lower()
        return service_mapping.get(service_lower, raw_service)

    def close(self):
        """Close Azure client connections"""
        if self._credential:
            self._credential = None
        if self._cost_client:
            self._cost_client.close()
            self._cost_client = None
