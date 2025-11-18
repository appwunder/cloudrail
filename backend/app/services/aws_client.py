import boto3
from typing import Optional
from botocore.exceptions import ClientError, BotoCoreError
import logging

logger = logging.getLogger(__name__)


class AWSClientManager:
    """Manages AWS client connections using cross-account IAM roles"""

    def __init__(self):
        self._clients = {}

    def get_cost_explorer_client(
        self,
        role_arn: str,
        external_id: Optional[str] = None,
        region: str = "us-east-1"
    ):
        """
        Get Cost Explorer client using cross-account IAM role

        Args:
            role_arn: IAM role ARN for cross-account access
            external_id: Optional external ID for additional security
            region: AWS region

        Returns:
            boto3 Cost Explorer client
        """
        # Create cache key
        cache_key = f"{role_arn}:{region}:ce"

        # Return cached client if available
        if cache_key in self._clients:
            return self._clients[cache_key]

        try:
            # Create STS client to assume role
            sts_client = boto3.client('sts', region_name=region)

            # Prepare assume role parameters
            assume_role_params = {
                'RoleArn': role_arn,
                'RoleSessionName': 'CloudCostlySession'
            }

            if external_id:
                assume_role_params['ExternalId'] = external_id

            # Assume the role
            assumed_role = sts_client.assume_role(**assume_role_params)

            # Get temporary credentials
            credentials = assumed_role['Credentials']

            # Create Cost Explorer client with assumed role credentials
            ce_client = boto3.client(
                'ce',
                region_name=region,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            # Cache the client
            self._clients[cache_key] = ce_client

            return ce_client

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to create AWS Cost Explorer client: {str(e)}")
            raise Exception(f"Failed to connect to AWS: {str(e)}")

    def get_pricing_client(
        self,
        role_arn: str,
        external_id: Optional[str] = None,
        region: str = "us-east-1"
    ):
        """
        Get Pricing client using cross-account IAM role

        Args:
            role_arn: IAM role ARN for cross-account access
            external_id: Optional external ID for additional security
            region: AWS region (pricing API is only available in us-east-1)

        Returns:
            boto3 Pricing client
        """
        # Pricing API is only available in us-east-1
        region = "us-east-1"
        cache_key = f"{role_arn}:{region}:pricing"

        if cache_key in self._clients:
            return self._clients[cache_key]

        try:
            sts_client = boto3.client('sts', region_name=region)

            assume_role_params = {
                'RoleArn': role_arn,
                'RoleSessionName': 'CloudCostlyPricingSession'
            }

            if external_id:
                assume_role_params['ExternalId'] = external_id

            assumed_role = sts_client.assume_role(**assume_role_params)
            credentials = assumed_role['Credentials']

            pricing_client = boto3.client(
                'pricing',
                region_name=region,
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )

            self._clients[cache_key] = pricing_client
            return pricing_client

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to create AWS Pricing client: {str(e)}")
            raise Exception(f"Failed to connect to AWS Pricing API: {str(e)}")

    def clear_cache(self):
        """Clear all cached clients"""
        self._clients.clear()


# Global client manager instance
aws_client_manager = AWSClientManager()
