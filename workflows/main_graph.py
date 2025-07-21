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

from agents.editor import EditorLlm
from agents.researcher import ResearcherLlm
from agents.writer import WriterLlm
from tools.tool_secrets import PROD_TAVILY_API_KEY
from tools.web_search_tool import get_search_tools
from utils import load_prompt
from workflows.constant import RESEARCH_NODE, WRITE_NODE, EDIT_NODE, WEB_SEARCH_NODE

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class WorkflowConfig:
    """Configuration for the main workflow"""
    enable_logging: bool = True
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 3
    editor_style: str = "General"

def build_workflow(editor_style: str = "General"):
    class State(TypedDict):
        messages: Annotated[list, add_messages]  # List of messages (human, agent, tool)
        topic: str  # The research topic

    # Create agents
    research_llm = ResearcherLlm()
    search_tools = get_search_tools()
    #research_llm.llm.bind_tools(search_tools)

    writer_llm = WriterLlm()

    editor_llm = EditorLlm()
    
    # Update editor prompt based on style
    if editor_style == "General":
        editor_llm.prompt_template = load_prompt('prompts/editor.txt')
    elif editor_style == "Emotional":
        editor_llm.prompt_template = load_prompt('prompts/editor_emotional.txt')
    elif editor_style == "Hilarious":
        editor_llm.prompt_template = load_prompt('prompts/editor_hilarious.txt')
    elif editor_style == "Critical":
        editor_llm.prompt_template = load_prompt('prompts/editor_critical.txt')

    def create_agent_node(llm, field_name: str):
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
                result = llm.process_query({
                    "messages": state["messages"],
                    field_name: field_value
                })
                
                return {"messages": result["messages"], "topic": state["topic"]}

            except Exception as e:
                return {
                    "messages": state["messages"] + [AIMessage(content=f"Agent error: {str(e)}")],
                    "topic": state["topic"]
                }

        return agent_node

    # Create standardized agent nodes
    researcher = create_agent_node(research_llm, 'topic')
    writer = create_agent_node(writer_llm, 'research_summary')
    editor = create_agent_node(editor_llm, 'article_draft')
    search_tool_node = ToolNode(search_tools)

    graph_builder = StateGraph(State)

    graph_builder.add_node(RESEARCH_NODE, researcher)
    graph_builder.add_node(WRITE_NODE, writer)
    graph_builder.add_node(EDIT_NODE, editor)
    graph_builder.add_node(WEB_SEARCH_NODE, search_tool_node)
    graph_builder.add_edge(START, RESEARCH_NODE)

    def route_after_research(state: State) -> str:
        """
        Route to web_search if the researcher requests a tool call, otherwise to write.
        """
        try:
            last_message = state["messages"][-1]
            logger.info(last_message)
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                logger.info(f"tool_calls activated")
                return WEB_SEARCH_NODE
            return WRITE_NODE
        except (IndexError, AttributeError) as e:
            print(f"Routing error: {str(e)}")
            return WRITE_NODE  # Default to write if no messages or tool_calls

    graph_builder.add_conditional_edges(
        RESEARCH_NODE,
        route_after_research,
        {
            WEB_SEARCH_NODE: WEB_SEARCH_NODE,
            WRITE_NODE: WRITE_NODE
        }
    )

    graph_builder.add_edge(WEB_SEARCH_NODE, RESEARCH_NODE)
    graph_builder.add_edge(WRITE_NODE, EDIT_NODE)
    graph_builder.set_finish_point(EDIT_NODE)

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
        compiled_graph = build_workflow(config.editor_style if config else "General")

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

# if __name__ == "__main__":
#     #from langchain_tavily import TavilySearch
#
#     tool = TavilySearch(
#         max_results=10,
#         tavily_api_key=PROD_TAVILY_API_KEY,
#         description="Search the web for current information about topics. Use this to gather comprehensive research data, recent developments, statistics, and factual information. Provide specific search queries to get the most relevant results."
#     )
#
#     result = tool.run("Impress your crush")
#     print(result)


