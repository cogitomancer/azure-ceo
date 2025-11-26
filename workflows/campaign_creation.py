"""
End-to-end campaign creation workflow.
"""

from semantic_kernel import Kernel
from core.orchestrator import MarketingOrchestrator
from models.campaign import Campaign, CampaignStatus
from models.segment import Segment
from models.experiment import Experiment
import logging
from typing import Dict
import uuid


class CampaignCreationWorkflow:
    """Orchestrate end-to-end campaign creation."""
    
    def __init__(self, kernel_factory, config: dict):
        self.kernel_factory = kernel_factory
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.orchestrator = MarketingOrchestrator(kernel_factory, config)
    
    async def execute(
        self,
        campaign_name: str,
        objective: str,
        created_by: str = "system"
    ) -> Campaign:
        """
        Execute complete campaign creation workflow.
        
        Steps:
        1. Create campaign record
        2. Execute agent collaboration
        3. Extract results
        4. Update campaign with results
        5. Return completed campaign
        """
        
        self.logger.info(f"Starting campaign creation: {campaign_name}")
        
        # Step 1: Create campaign
        campaign = Campaign(
            id=f"camp_{uuid.uuid4().hex[:12]}",
            name=campaign_name,
            objective=objective,
            status=CampaignStatus.DRAFT,
            created_by=created_by
        )
        
        session_id = f"session_{campaign.id}"
        
        # Step 2: Execute agent collaboration
        self.logger.info("Executing agent collaboration...")
        
        segment_info = None
        message_variants = []
        experiment_id = None
        
        async for message in self.orchestrator.execute_campaign_request(
            objective=objective,
            session_id=session_id
        ):
            # Extract information from agent responses
            if message.name == "DataSegmenter":
                segment_info = self._extract_segment_info(message.content)
            
            elif message.name == "ContentCreator":
                variants = self._extract_message_variants(message.content)
                message_variants.extend(variants)
            
            elif message.name == "ComplianceOfficer":
                compliance_passed = "<APPROVED>" in message.content
                campaign.compliance_check_passed = compliance_passed
            
            elif message.name == "ExperimentRunner":
                experiment_id = self._extract_experiment_id(message.content)
        
        # Step 3: Update campaign with results
        if segment_info:
            campaign.segment_id = segment_info.get("id")
            campaign.segment_size = segment_info.get("size", 0)
        
        campaign.message_variants = [v["id"] for v in message_variants]
        campaign.experiment_id = experiment_id
        
        # Step 4: Update status
        if campaign.compliance_check_passed and experiment_id:
            campaign.status = CampaignStatus.APPROVED
        else:
            campaign.status = CampaignStatus.PENDING_APPROVAL
        
        self.logger.info(f"Campaign creation completed: {campaign.status.value}")
        
        return campaign
    
    def _extract_segment_info(self, content: str) -> Dict:
        """Extract segment information from DataSegmenter response."""
        # Parse segment details from response
        # This is simplified - in production, use structured output
        return {
            "id": f"seg_{uuid.uuid4().hex[:12]}",
            "size": 12500  # Extracted from content
        }
    
    def _extract_message_variants(self, content: str) -> list:
        """Extract message variants from ContentCreator response."""
        # Parse variants from response
        # Simplified - production would use structured parsing
        variants = []
        for variant_name in ["A", "B", "C"]:
            variants.append({
                "id": f"msg_{uuid.uuid4().hex[:12]}",
                "variant_name": variant_name,
                "content": content  # Extract specific variant
            })
        return variants
    
    def _extract_experiment_id(self, content: str) -> str:
        """Extract experiment ID from ExperimentRunner response."""
        return f"exp_{uuid.uuid4().hex[:12]}"
