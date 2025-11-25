"""
Azure App Configuration service for feature flags.
"""

from azure.appconfiguration import AzureAppConfigurationClient
from azure.identity import DefaultAzureCredential
import json
import logging
from typing import Dict, Optional


class AppConfigService:
    """Client for Azure App Configuration."""
    
    def __init__(self, config: dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.credential = DefaultAzureCredential()
        
        self.client = AzureAppConfigurationClient(
            base_url=config["app_configuration"]["endpoint"],
            credential=self.credential
        )
    
    def create_feature_flag(
        self, 
        flag_name: str, 
        variants: List[Dict],
        enabled: bool = True
    ) -> Dict:
        """Create a feature flag for A/B testing."""
        
        flag_key = f".appconfig.featureflag/{flag_name}"
        
        flag_value = {
            "id": flag_name,
            "enabled": enabled,
            "conditions": {
                "client_filters": []
            },
            "variants": variants,
            "allocation": {
                "default_when_enabled": variants[0]["name"] if variants else "default"
            }
        }
        
        try:
            self.client.set_configuration_setting(
                key=flag_key,
                value=json.dumps(flag_value),
                content_type="application/vnd.microsoft.appconfig.ff+json;charset=utf-8"
            )
            
            self.logger.info(f"Created feature flag: {flag_name}")
            return flag_value
            
        except Exception as e:
            self.logger.error(f"Error creating feature flag: {e}")
            raise
    
    def get_feature_flag(self, flag_name: str) -> Optional[Dict]:
        """Get a feature flag configuration."""
        
        flag_key = f".appconfig.featureflag/{flag_name}"
        
        try:
            setting = self.client.get_configuration_setting(key=flag_key)
            return json.loads(setting.value)
        except Exception as e:
            self.logger.warning(f"Feature flag not found: {e}")
            return None
    
    def update_feature_flag(self, flag_name: str, flag_value: Dict):
        """Update an existing feature flag."""
        
        flag_key = f".appconfig.featureflag/{flag_name}"
        
        try:
            self.client.set_configuration_setting(
                key=flag_key,
                value=json.dumps(flag_value),
                content_type="application/vnd.microsoft.appconfig.ff+json;charset=utf-8"
            )
            
            self.logger.info(f"Updated feature flag: {flag_name}")
        except Exception as e:
            self.logger.error(f"Error updating feature flag: {e}")
            raise
    
    def delete_feature_flag(self, flag_name: str):
        """Delete a feature flag."""
        
        flag_key = f".appconfig.featureflag/{flag_name}"
        
        try:
            self.client.delete_configuration_setting(key=flag_key)
            self.logger.info(f"Deleted feature flag: {flag_name}")
        except Exception as e:
            self.logger.error(f"Error deleting feature flag: {e}")
            raise