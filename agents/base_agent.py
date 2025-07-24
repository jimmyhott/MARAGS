# agents/base_agent.py

import os
from typing import Dict, Any, List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage

from llm.azure_secrets import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
from utils import load_prompt
from workflows.state import State


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

    def create_node(self, expected_fields: Optional[List[str]] = None, output_field: Optional[str] = None):
        """
        Create a LangGraph node for this agent.

        Args:
            expected_fields: List of field names this agent expects from state.
                           If None, no validation is performed.
            output_field: Name of the field to store this agent's output in state.
                         If None, output is only stored in messages.

        Returns:
            A node function compatible with LangGraph.
        """

        def node(state: State) -> State:
            print(f"\n{self.__class__.__name__} is processing...")

            # Build agent state with messages and topic (always needed)
            agent_state = {
                "messages": state["messages"],
                "topic": state["topic"]
            }

            # Add expected fields to agent state
            if expected_fields:
                for field_name in expected_fields:
                    # Check if field exists in state
                    if field_name in state:
                        agent_state[field_name] = state[field_name]
                    else:
                        # If not in state, try to extract from last AI message
                        # This provides backward compatibility with implicit data flow
                        field_value = None
                        for msg in reversed(state["messages"]):
                            if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content'):
                                field_value = msg.content
                                break

                        if field_value is None:
                            raise ValueError(f"Expected field '{field_name}' not found in state or messages")

                        agent_state[field_name] = field_value

            # Process the query
            result = self.process_query(agent_state)

            # If output_field is specified, store the agent's output in that field
            if output_field and result["messages"]:
                last_message = result["messages"][-1]
                if hasattr(last_message, 'content'):
                    result[output_field] = last_message.content

            return result

        return node

    def bind_tools(self, tools):
        """
        Bind tools to the LLM and return self for method chaining.

        Args:
            tools: List of tools to bind to the LLM

        Returns:
            self: Returns the instance for method chaining
        """
        self.llm = self.llm.bind_tools(tools)
        return self