from agents.base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    """Researcher agent for gathering information about topics."""
    
    def __init__(self, prompt_path='prompts/researcher.txt'):
        super().__init__(prompt_path)





