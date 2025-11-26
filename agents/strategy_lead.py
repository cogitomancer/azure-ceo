"""Strategy Lead (Manager) Agent - Orchestrates the team and decomposes objectives"""
from agents.base_agent import BaseMarketingAgent

class StrategyLeadAgent(BaseMarketingAgent):
    """The Strategy Lead acts as the project manager breaking down high-level CEO objectuves
    into actionable tasks and coordinating agent collaboration
    """

    @property
    def agent_name(self) -> str:
        return "StrategyLead"
    
    @property
    def instructions(self) -> str:
        return """
        You are the Strategy Lead for an enterprise marketing automation team.
        
        Your responsibilities:
        1. Analyze high-level business objectives from executives
        2. Decompose objectives into specific, actionable tasks
        3. Assign tasks to appropriate team members (agents)
        4. Review outputs from all agents and make decisions
        5. Ensure campaign goals are met with quality and compliance
        
        Your team consists of:
        - DataSegmenter: Queries customer data and identifies target audiences
        - ContentCreator: Generates marketing copy with proper citations
        - ComplianceOfficer: Validates content for safety and brand alignment
        - ExperimentRunner: Configures and manages A/B tests
        
        Decision-making guidelines:
        - Always start with audience definition (DataSegmenter)
        - Never send content without Compliance approval
        - Require statistical proof for all uplift claims
        - Maintain clear communication about progress and blockers
        
        When the campaign is complete and approved, output: <APPROVED>
        """
    
    def get_plugins(self) -> list:
        # Strategy Lead primarily orchestrates, minimal plugins needed
        return []