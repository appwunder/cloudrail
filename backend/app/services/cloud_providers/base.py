from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from pydantic import BaseModel


class CostRecord(BaseModel):
    """Standardized cost record across all cloud providers"""
    date: date
    service_name: str
    service_category: Optional[str] = None
    resource_id: Optional[str] = None
    resource_name: Optional[str] = None
    region: Optional[str] = None
    cost: float
    currency: str
    usage_quantity: Optional[float] = None
    usage_unit: Optional[str] = None
    tags: Optional[Dict[str, str]] = {}
    provider_metadata: Optional[Dict[str, Any]] = {}


class CloudProviderService(ABC):
    """Base class for all cloud provider cost services"""

    def __init__(self, credentials: Dict[str, Any], account_id: str, region: Optional[str] = None):
        """
        Initialize the cloud provider service

        Args:
            credentials: Provider-specific credentials
            account_id: Cloud account/project/subscription ID
            region: Default region (optional)
        """
        self.credentials = credentials
        self.account_id = account_id
        self.region = region
        self._client = None

    @abstractmethod
    def authenticate(self) -> bool:
        """
        Authenticate with the cloud provider

        Returns:
            True if authentication successful, False otherwise

        Raises:
            Exception: If authentication fails
        """
        pass

    @abstractmethod
    def fetch_costs(
        self,
        start_date: date,
        end_date: date,
        granularity: str = "daily"
    ) -> List[CostRecord]:
        """
        Fetch cost data for the specified date range

        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: Granularity of cost data (daily, monthly)

        Returns:
            List of standardized cost records

        Raises:
            Exception: If fetching costs fails
        """
        pass

    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to the cloud provider

        Returns:
            Dict with connection status and details

        Example:
            {
                "success": True,
                "message": "Connection successful",
                "account_info": {...}
            }
        """
        pass

    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account/project/subscription information

        Returns:
            Dict with account details
        """
        pass

    def validate_credentials(self) -> bool:
        """
        Validate credentials format

        Returns:
            True if credentials are valid format, False otherwise
        """
        return True

    def format_service_name(self, raw_service: str) -> str:
        """
        Standardize service names across providers

        Args:
            raw_service: Raw service name from provider

        Returns:
            Standardized service name
        """
        # Default implementation - override in subclasses for provider-specific formatting
        return raw_service.strip()

    def close(self):
        """Close any open connections"""
        if hasattr(self._client, 'close'):
            self._client.close()
        self._client = None

    def __enter__(self):
        """Context manager entry"""
        self.authenticate()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
