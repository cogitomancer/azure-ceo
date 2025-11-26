"""
Azure App Configuration plugin for feature flag management.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated
from azure.appconfiguration import AzureAppConfigurationClient
from azure.identity import DefaultAzureCredential
import json


class AppConfigPlugin:
    """
    Plugin for managing feature flags and A/B test configurations.
    Integrates with Azure App Configuration for experiment control.
    """
    
    def __init__(self, config: dict):
        self.config = config
        self.credential = DefaultAzureCredential()
        
        self.app_config_client = AzureAppConfigurationClient(
            base_url=config["app_configuration"]["endpoint"],
            credential=self.credential
        )
    
    @kernel_function(
        name="create_feature_flag",
        description="Create a variant feature flag for A/B/n testing"
    )
    async def create_feature_flag(
        self,
        experiment_name: Annotated[str, "Name of the experiment"],
        variants: Annotated[str, "JSON string of variants with descriptions"],
        traffic_allocation: Annotated[str, "Percentage allocation per variant (e.g., '33,33,34')"]
    ) -> Annotated[str, "Feature flag creation result"]:
        """
        Create feature flag for experiment with variant configuration.
        """
        
        try:
            # Parse inputs
            variant_list = json.loads(variants)
            allocations = [int(x) for x in traffic_allocation.split(",")]
            
            if sum(allocations) != 100:
                return "ERROR: Traffic allocations must sum to 100%"
            
            # Create feature flag configuration
            feature_flag = {
                "id": f"experiment_{experiment_name}",
                "enabled": True,
                "conditions": {
                    "client_filters": [
                        {
                            "name": "Microsoft.Targeting",
                            "parameters": {
                                "Audience": {
                                    "Users": [],
                                    "Groups": [],
                                    "DefaultRolloutPercentage": 5  # Safety: start at 5%
                                }
                            }
                        }
                    ]
                },
                "variants": [
                    {
                        "name": variant["name"],
                        "configuration_value": variant["content"],
                        "status_override": "Enabled"
                    }
                    for variant in variant_list
                ],
                "allocation": {
                    "percentile": [
                        {
                            "variant": variant_list[i]["name"],
                            "from": sum(allocations[:i]),
                            "to": sum(allocations[:i+1])
                        }
                        for i in range(len(variant_list))
                    ]
                }
            }
            
            # Set in App Configuration
            self.app_config_client.set_configuration_setting(
                key=f".appconfig.featureflag/{experiment_name}",
                value=json.dumps(feature_flag),
                content_type="application/vnd.microsoft.appconfig.ff+json;charset=utf-8"
            )
            
            return f"""
            Feature flag created successfully!
            
            Experiment: {experiment_name}
            Variants: {', '.join([v['name'] for v in variant_list])}
            Traffic allocation: {traffic_allocation}
            Initial exposure: 5% (safety limit)
            Status: ACTIVE
            
            Flag ID: experiment_{experiment_name}
            """
            
        except Exception as e:
            return f"ERROR creating feature flag: {str(e)}"
    
    @kernel_function(
        name="update_traffic_allocation",
        description="Update traffic allocation percentages for a running experiment"
    )
    async def update_traffic_allocation(
        self,
        experiment_name: Annotated[str, "Name of the experiment"],
        new_allocation: Annotated[str, "New percentage allocation"]
    ) -> Annotated[str, "Update result"]:
        """
        Dynamically adjust traffic to variants (e.g., kill underperforming variant).
        """
        
        try:
            # Retrieve current flag
            flag_key = f".appconfig.featureflag/{experiment_name}"
            current_setting = self.app_config_client.get_configuration_setting(key=flag_key)
            flag_config = json.loads(current_setting.value)
            
            # Update allocation
            allocations = [int(x) for x in new_allocation.split(",")]
            
            # Rebuild allocation config
            variants = flag_config["variants"]
            flag_config["allocation"]["percentile"] = [
                {
                    "variant": variants[i]["name"],
                    "from": sum(allocations[:i]),
                    "to": sum(allocations[:i+1])
                }
                for i in range(len(variants))
            ]
            
            # Update in App Configuration
            self.app_config_client.set_configuration_setting(
                key=flag_key,
                value=json.dumps(flag_config),
                content_type=current_setting.content_type
            )
            
            return f"Traffic allocation updated: {new_allocation}"
            
        except Exception as e:
            return f"ERROR updating traffic: {str(e)}"