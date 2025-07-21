import os
from typing import Dict, Any

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from llm.azure_secrets import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
from utils import load_prompt


class BaseLlm:
    """Base class for all agents with standardized functionality."""
    
    def __init__(self, prompt_path: str):
        """
        Initialize the agent with a prompt template.
        
        Args:
            prompt_path: Path to the prompt template file
        """
        os.environ["AZURE_OPENAI_API_KEY"] = AZURE_OPENAI_API_KEY
        os.environ["AZURE_OPENAI_ENDPOINT"] = AZURE_OPENAI_ENDPOINT
        os.environ["OPENAI_API_VERSION"] = "2024-12-01-preview"
        os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"] = "gpt-4o"

        self.llm = init_chat_model(model_provider="azure_openai", model=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"])

        # self.llm = AzureChatOpenAI(
        #     azure_deployment=os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"],
        #     openai_api_key=os.environ["AZURE_OPENAI_API_KEY"],
        #     azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        #     openai_api_version=os.environ["OPENAI_API_VERSION"],
        #     temperature=0,
        # )
        self.prompt_template = load_prompt(prompt_path)

    def process_query(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a query using the prompt template and LLM.
        
        Args:
            state: A dictionary containing 'messages' (list of messages) and additional fields
                  specific to each agent (e.g., 'topic', 'research_summary', 'article_draft')
        
        Returns:
            Updated state with the agent's response appended to messages.
        """
        messages = state["messages"]
        
        # Format the prompt with the state fields (excluding 'messages')
        prompt_kwargs = {k: v for k, v in state.items() if k != "messages"}
        formatted_prompt = self.prompt_template.format(**prompt_kwargs)
        
        # Combine existing messages with the new prompt
        input_messages = messages + [HumanMessage(content=formatted_prompt)]
        
        # Invoke the LLM
        response = self.llm.invoke(input_messages)
        
        # Return updated state with response appended to messages
        return {
            "messages": messages + [response],
            **prompt_kwargs  # Preserve all other state fields
        } 