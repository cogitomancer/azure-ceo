"""
Stable Azure App Configuration plugin (v1 SDK).
Manages feature flags for experiments.
"""

from semantic_kernel.functions import kernel_function
from typing import Annotated, List, Dict
from azure.appconfiguration import AzureAppConfigurationClient
from azure.identity import DefaultAzureCredential
import json


class AppConfigPlugin:
    """
    Stable plugin for managing feature flags in Azure App Configuration.
    Uses the v1 Azure SDK, which is production-safe.
    """

    def __init__(self, config: dict):
        self.config = config
        self.credential = DefaultAzureCredential()

        self.client = AzureAppConfigurationClient(
            base_url=config["app_configuration"]["endpoint"],
            credential=self.credential
        )

    # ----------------------------------------------------------------------
    # CREATE FEATURE FLAG
    # ----------------------------------------------------------------------
    @kernel_function(
        name="create_feature_flag",
        description="Create a feature flag for A/B/n testing (stable SDK)."
    )
    async def create_feature_flag(
        self,
        experiment_name: Annotated[str, "Name of the experiment"],
        variants_json: Annotated[str, "JSON list of variants"],
    ) -> Annotated[str, "Feature flag creation result"]:
        """
        Create a stable feature flag using the v1 API.
        Traffic allocation is NOT set here — ExperimentRunner handles it.
        """

        try:
            variants = json.loads(variants_json)

            flag_key = f".appconfig.featureflag/{experiment_name}"

            feature_flag = {
                "id": experiment_name,
                "enabled": True,
                "conditions": {
                    "client_filters": [
                        {
                            "name": "Microsoft.Targeting",
                            "parameters": {
                                "Audience": {
                                    "Users": [],
                                    "Groups": [],
                                    "DefaultRolloutPercentage": 5  # safety limit
                                }
                            }
                        }
                    ]
                },
                "variants": [
                    {
                        "name": v["variant_id"],
                        "configuration_value": v.get("body", ""),
                        "status_override": "Enabled"
                    }
                    for v in variants
                ],
            }

            self.client.set_configuration_setting(
                key=flag_key,
                value=json.dumps(feature_flag),
                content_type="application/vnd.microsoft.appconfig.ff+json;charset=utf-8"
            )

            return (
                f"Feature flag created for experiment '{experiment_name}'. "
                f"Variants: {[v['variant_id'] for v in variants]}. "
                f"Initial exposure capped at 5%."
            )

        except Exception as e:
            return f"ERROR creating feature flag: {str(e)}"

    # ----------------------------------------------------------------------
    # UPDATE TRAFFIC ALLOCATION
    # ----------------------------------------------------------------------
    @kernel_function(
        name="update_traffic_allocation",
        description="Update traffic allocation across variants (stable SDK)."
    )
    async def update_traffic_allocation(
        self,
        experiment_name: Annotated[str, "Experiment name"],
        allocations_json: Annotated[str, "JSON dict of {variant_id: percent}"],
    ) -> Annotated[str, "Traffic allocation update result"]:

        try:
            allocations = json.loads(allocations_json)

            flag_key = f".appconfig.featureflag/{experiment_name}"
            current = self.client.get_configuration_setting(key=flag_key)
            flag_config = json.loads(current.value)

            # sort keys for deterministic percentile windows
            variant_ids = list(allocations.keys())

            # rebuild percentile allocation window
            percent_ranges = []
            cumulative = 0

            for v in variant_ids:
                pct = allocations[v]
                next_cumulative = cumulative + pct

                percent_ranges.append({
                    "variant": v,
                    "from": cumulative,
                    "to": next_cumulative
                })

                cumulative = next_cumulative

            flag_config["allocation"] = {"percentile": percent_ranges}

            self.client.set_configuration_setting(
                key=flag_key,
                value=json.dumps(flag_config),
                content_type=current.content_type
            )

            return f"Updated allocation: {allocations}"

        except Exception as e:
            return f"ERROR updating allocation: {str(e)}"
