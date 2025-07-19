from agents.base_agent import BaseAgent


class WriterAgent(BaseAgent):
    """Writer agent for creating articles from research summaries."""
    
    def __init__(self, prompt_path='prompts/writer.txt'):
        super().__init__(prompt_path)

