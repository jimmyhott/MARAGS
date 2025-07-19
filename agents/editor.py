from agents.base_agent import BaseAgent


class EditorAgent(BaseAgent):
    """Editor agent for refining and polishing articles."""
    
    def __init__(self, prompt_path='prompts/editor.txt'):
        super().__init__(prompt_path)
