from pathlib import Path

from agents.base_agent import BaseLlm


class AdvancedResearcherLlm(BaseLlm):
    """Researcher agent for gathering information about topics."""

    def __init__(self, prompt_path='prompts/advanced_researcher.txt'):
        # Get the project root (assuming this file is in 'agents' folder)
        project_root = Path(__file__).parent.parent
        full_path = project_root / prompt_path
        super().__init__(str(full_path))
