from utils import load_prompt


class EditorAgent:
    def __init__(self, llm, prompt_path='prompts/editor.txt'):
        self.llm = llm
        self.prompt_template = load_prompt(prompt_path)

    def run(self, topic):
        prompt = f"Research the following topic and provide a summary:\n{topic}"
        return self.llm.invoke(prompt)

