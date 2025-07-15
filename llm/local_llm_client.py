from langchain_ollama import OllamaLLM

def get_local_llm(model_name="llama3"):
    return OllamaLLM(model=model_name)