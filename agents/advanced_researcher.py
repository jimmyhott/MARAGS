import logging
from pathlib import Path

from agents.base_agent import BaseLlm

logger = logging.getLogger(__name__)

class AdvancedResearcherLlm(BaseLlm):
    """Advanced researcher agent for gathering and aggregating trending topics."""

    def __init__(self, prompt_path='prompts/advanced_researcher.txt'):
        # Get the project root (assuming this file is in 'agents' folder)
        project_root = Path(__file__).parent.parent
        full_path = project_root / prompt_path
        super().__init__(str(full_path))

