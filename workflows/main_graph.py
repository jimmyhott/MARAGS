# workflows/main_graph.py

import logging
import time
from dataclasses import dataclass
from typing import TypedDict, Optional, Dict, Any, Annotated

from langchain_core.messages import AIMessage
from langchain_tavily import TavilySearch
from langgraph.graph import START, add_messages
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from agents.editor import EditorAgent
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from tools.tool_secrets import TAVILY_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowConfig:
    """Configuration for the main workflow"""
    enable_logging: bool = True
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 3

def build_workflow():
    class State(TypedDict):
        messages: Annotated[list, add_messages]  # List of messages (human, agent, tool)
        topic: str  # The research topic

    # Create agents
    research_agent = ResearcherAgent()
    search_tools = get_search_tools()
    search_tool_node = ToolNode(search_tools)
    research_agent.llm.bind_tools(search_tools)

    writer_agent = WriterAgent()
    editor_agent = EditorAgent()

    def create_agent_node(agent, field_name: str, agent_name: str):
        """Create a standardized agent node function."""
        def agent_node(state: State) -> State:
            try:
                # Get field value from state or last AI message
                field_value = state.get(field_name) or next(
                    (msg.content for msg in reversed(state["messages"]) 
                     if hasattr(msg, 'type') and msg.type == 'ai' and hasattr(msg, 'content')), 
                    ""
                )
                
                # Process with agent
                result = agent.process_query({
                    "messages": state["messages"],
                    field_name: field_value
                })
                
                return {"messages": result["messages"], "topic": state["topic"]}
                
            except Exception as e:
                return {
                    "messages": state["messages"] + [AIMessage(content=f"{agent_name} error: {str(e)}")],
                    "topic": state["topic"]
                }
        
        return agent_node

    # Create standardized agent nodes
    researcher = create_agent_node(research_agent, 'topic', 'Researcher')
    writer = create_agent_node(writer_agent, 'research_summary', 'Writer')
    editor = create_agent_node(editor_agent, 'article_draft', 'Editor')


    graph_builder = StateGraph(State)

    graph_builder.add_node('research', researcher)
    graph_builder.add_node('write', writer)
    graph_builder.add_node('edit', editor)
    graph_builder.add_node('web_search', search_tool_node)

    graph_builder.add_edge(START, 'research')

    def route_after_research(state: State) -> str:
        """
        Route to web_search if the researcher requests a tool call, otherwise to write.
        """
        try:
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "web_search"
            return "write"
        except (IndexError, AttributeError) as e:
            print(f"Routing error: {str(e)}")
            return "write"  # Default to write if no messages or tool_calls

    graph_builder.add_conditional_edges(
        'research',
        route_after_research,
        {
            "web_search": "web_search",
            "write": "write"
        }
    )

    graph_builder.add_edge('web_search', 'research')
    graph_builder.add_edge('write', 'edit')
    graph_builder.set_finish_point('edit')

    # Compile the graph before returning
    return graph_builder.compile()

def main_workflow(
    topic: str,
    config: Optional[WorkflowConfig] = None,
    return_full_state: bool = False
) -> str | Dict[str, Any]:
    """
    Execute the main article generation workflow.

    Args:
        topic: The topic to research and write about
        config: Optional configuration for the workflow
        return_full_state: If True, returns the complete state instead of just the final article

    Returns:
        The final article or complete workflow state if return_full_state is True

    Raises:
        ValueError: If topic is empty or invalid
        RuntimeError: If workflow execution fails
    """
    # Validate input
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty or whitespace only")

    # Use default config if none provided
    if config is None:
        config = WorkflowConfig()

    # Setup logging
    if config.enable_logging:
        logger.info(f"Starting workflow for topic: {topic}")
        start_time = time.time()

    try:
        # Build and execute the workflow
        compiled_graph = build_workflow()

        initial_state = {
            'topic': topic.strip(),
            'messages': []
        }

        # Execute with retry logic
        final_state = None
        last_exception = None

        for attempt in range(config.retry_attempts):
            try:
                if config.enable_logging:
                    logger.info(f"Workflow execution attempt {attempt + 1}/{config.retry_attempts}")

                final_state = compiled_graph.invoke(initial_state)
                break

            except Exception as e:
                last_exception = e
                if config.enable_logging:
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt < config.retry_attempts - 1:
                    time.sleep(1)  # Brief pause before retry

        if final_state is None:
            raise RuntimeError(f"Workflow failed after {config.retry_attempts} attempts. Last error: {str(last_exception)}")

        # Validate final state
        messages = final_state.get('messages', [])
        if not messages:
            raise RuntimeError("Workflow completed but no messages were generated")

        # Log completion
        if config.enable_logging:
            execution_time = time.time() - start_time
            logger.info(f"Workflow completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Generated {len(messages)} messages")

        # Return appropriate result
        if return_full_state:
            return final_state
        else:
            # Return the last AI message content as the final article
            ai_messages = [msg for msg in messages if hasattr(msg, 'type') and msg.type == 'ai']
            if ai_messages:
                return ai_messages[-1].content
            else:
                return str(messages[-1].content) if hasattr(messages[-1], 'content') else str(messages[-1])

    except Exception as e:
        if config.enable_logging:
            logger.error(f"Workflow execution failed: {str(e)}")
        raise RuntimeError(f"Workflow execution failed: {str(e)}") from e

def get_search_tools():
    tool = TavilySearch(max_results=2, tavily_api_key=TAVILY_API_KEY)
    tools = [tool]
    return tools


def main_workflow_with_progress(topic: str, progress_callback=None) -> str:
    """
    Execute the main workflow with progress tracking.

    Args:
        topic: The topic to research and write about
        progress_callback: Optional callback function to report progress

    Returns:
        The final article
    """
    def progress_wrapper(stage: str, message: str = ""):
        if progress_callback:
            progress_callback(stage, message)
        logger.info(f"Progress - {stage}: {message}")

    progress_wrapper("initializing", "Setting up workflow")
    config = WorkflowConfig(enable_logging=True)

    progress_wrapper("executing", "Running research and writing pipeline")
    result = main_workflow(topic, config)

    progress_wrapper("completed", "Article generation finished")
    return result
