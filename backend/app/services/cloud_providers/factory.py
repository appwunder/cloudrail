from typing import Dict, Any
from app.models.cloud_account import CloudProvider
from .base import CloudProviderService
from .gcp_service import GCPBillingService
from .azure_service import AzureCostManagementService
from .alibaba_service import AlibabaBSSService


class CloudProviderServiceFactory:
    """Factory for creating cloud provider service instances"""

    @staticmethod
    def create_service(
        provider: CloudProvider,
        credentials: Dict[str, Any],
        account_id: str,
        region: str = None
    ) -> CloudProviderService:
        """
        Create appropriate cloud provider service based on provider type

        Args:
            provider: Cloud provider enum
            credentials: Provider-specific credentials
            account_id: Account/Project/Subscription ID
            region: Default region (optional)

        Returns:
            CloudProviderService instance

        Raises:
            ValueError: If provider is not supported
        """
        if provider == CloudProvider.AWS:
            # Import AWS service only when needed to avoid circular imports
            from app.services.aws_service import AWSCostExplorerService
            return AWSCostExplorerService(credentials, account_id, region)

        elif provider == CloudProvider.GCP:
            return GCPBillingService(credentials, account_id, region)

        elif provider == CloudProvider.AZURE:
            return AzureCostManagementService(credentials, account_id, region)

        elif provider == CloudProvider.ALIBABA:
            return AlibabaBSSService(credentials, account_id, region)

        else:
            raise ValueError(f"Unsupported cloud provider: {provider}")

    @staticmethod
    def test_credentials(
        provider: CloudProvider,
        credentials: Dict[str, Any],
        account_id: str,
        region: str = None
    ) -> Dict[str, Any]:
        """
        Test credentials for a cloud provider without creating a full service instance

        Args:
            provider: Cloud provider enum
            credentials: Provider-specific credentials
            account_id: Account/Project/Subscription ID
            region: Default region (optional)

        Returns:
            Dict with test results
        """
        try:
            service = CloudProviderServiceFactory.create_service(
                provider=provider,
                credentials=credentials,
                account_id=account_id,
                region=region
            )

            with service:
                result = service.test_connection()
                return result

        except Exception as e:
            return {
                "success": False,
                "message": f"Credentials test failed: {str(e)}",
                "error": str(e)
            }
