from typing import Callable

from agents.base_agent import BaseLlm


class EditorLlm(BaseLlm):
    """Editor agent for refining and polishing articles."""
    
    def __init__(self, prompt_path='prompts/editor.txt'):
        super().__init__(prompt_path)

