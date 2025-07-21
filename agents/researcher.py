from agents.base_agent import BaseLlm


class ResearcherLlm(BaseLlm):
    """Researcher agent for gathering information about topics."""
    
    def __init__(self, prompt_path='prompts/researcher.txt'):
        super().__init__(prompt_path)





