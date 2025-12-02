from typing import List, Dict, Any, Optional
from datetime import date, timedelta
import json
from google.cloud import billing_v1
from google.oauth2 import service_account
from google.auth.exceptions import GoogleAuthError
import logging

from .base import CloudProviderService, CostRecord

logger = logging.getLogger(__name__)


class GCPBillingService(CloudProviderService):
    """Google Cloud Platform Billing service implementation"""

    def __init__(self, credentials: Dict[str, Any], account_id: str, region: Optional[str] = None):
        """
        Initialize GCP Billing service

        Args:
            credentials: Dict containing 'service_account_json' key with service account JSON
            account_id: GCP Project ID
            region: Default region (optional)
        """
        super().__init__(credentials, account_id, region)
        self.project_id = account_id
        self._cloud_billing_client = None
        self._service_account_info = None

    def validate_credentials(self) -> bool:
        """Validate GCP credentials format"""
        if 'service_account_json' not in self.credentials:
            return False

        service_account_data = self.credentials['service_account_json']

        # Parse JSON if it's a string
        if isinstance(service_account_data, str):
            try:
                service_account_data = json.loads(service_account_data)
            except json.JSONDecodeError:
                return False

        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
        return all(field in service_account_data for field in required_fields)

    def authenticate(self) -> bool:
        """Authenticate with GCP using service account credentials"""
        try:
            service_account_data = self.credentials['service_account_json']

            # Parse JSON if it's a string
            if isinstance(service_account_data, str):
                service_account_data = json.loads(service_account_data)

            self._service_account_info = service_account_data

            # Create credentials from service account info
            credentials = service_account.Credentials.from_service_account_info(
                service_account_data,
                scopes=['https://www.googleapis.com/auth/cloud-billing.readonly']
            )

            # Initialize Cloud Billing client
            self._cloud_billing_client = billing_v1.CloudBillingClient(credentials=credentials)

            logger.info(f"Successfully authenticated with GCP for project {self.project_id}")
            return True

        except (GoogleAuthError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"GCP authentication failed: {str(e)}")
            raise Exception(f"GCP authentication failed: {str(e)}")

    def test_connection(self) -> Dict[str, Any]:
        """Test connection to GCP and verify access"""
        try:
            if not self._cloud_billing_client:
                self.authenticate()

            # Try to get project billing info
            project_name = f"projects/{self.project_id}"

            try:
                billing_info = self._cloud_billing_client.get_project_billing_info(name=project_name)

                return {
                    "success": True,
                    "message": "Successfully connected to GCP",
                    "account_info": {
                        "project_id": self.project_id,
                        "billing_enabled": billing_info.billing_enabled,
                        "billing_account": billing_info.billing_account_name if billing_info.billing_account_name else "N/A"
                    }
                }
            except Exception as e:
                return {
                    "success": True,
                    "message": "Authentication successful, but unable to retrieve billing info",
                    "account_info": {
                        "project_id": self.project_id,
                        "note": "Limited permissions or billing not enabled"
                    },
                    "warning": str(e)
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Connection test failed: {str(e)}",
                "error": str(e)
            }

    def get_account_info(self) -> Dict[str, Any]:
        """Get GCP project information"""
        if not self._service_account_info:
            raise Exception("Not authenticated. Call authenticate() first.")

        return {
            "project_id": self.project_id,
            "service_account_email": self._service_account_info.get('client_email', 'N/A'),
            "auth_provider": self._service_account_info.get('auth_provider_x509_cert_url', 'N/A')
        }

    def fetch_costs(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "daily"
    ) -> List[CostRecord]:
        """
        Fetch cost data from GCP Cloud Billing

        Note: This is a simplified implementation. In production, you would use
        BigQuery to query the billing export data for detailed cost breakdowns.
        GCP doesn't provide a direct API for historical cost data like AWS Cost Explorer.

        Args:
            start_date: Start date
            end_date: End date
            granularity: daily or monthly

        Returns:
            List of cost records
        """
        if not self._cloud_billing_client:
            self.authenticate()

        logger.info(f"Fetching GCP costs for {self.project_id} from {start_date} to {end_date}")

        # NOTE: GCP Cloud Billing API doesn't provide historical cost data directly
        # You need to export billing data to BigQuery and query it from there
        # This is a placeholder implementation

        logger.warning(
            "GCP cost fetching requires BigQuery billing export. "
            "Please configure billing export to BigQuery and use the BigQuery client to fetch costs."
        )

        # Return empty list for now - in production, implement BigQuery querying
        # See: https://cloud.google.com/billing/docs/how-to/export-data-bigquery
        return []

    def format_service_name(self, raw_service: str) -> str:
        """Standardize GCP service names"""
        # GCP service name mapping
        service_mapping = {
            'compute': 'Compute Engine',
            'storage': 'Cloud Storage',
            'bigquery': 'BigQuery',
            'cloudsql': 'Cloud SQL',
            'kubernetes': 'Google Kubernetes Engine',
            # Add more mappings as needed
        }

        service_lower = raw_service.lower()
        return service_mapping.get(service_lower, raw_service)

    def close(self):
        """Close GCP client connections"""
        if self._cloud_billing_client:
            self._cloud_billing_client = None
