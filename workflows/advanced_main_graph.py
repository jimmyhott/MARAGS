# workflows/main_graph.py

import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

from langgraph.constants import END
from langgraph.graph import START
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from agents.advanced_researcher import AdvancedResearcherLlm
from agents.editor import EditorLlm
from agents.researcher import ResearcherLlm
from agents.writer import WriterLlm
from tools.image_generation_tool import get_image_generation_tools
from tools.advanced_web_search_tool import get_search_tools

from utils import load_prompt
from workflows.advanced_state import AdvancedState
from workflows.constant import RESEARCH_NODE, WRITE_NODE, EDIT_NODE, WEB_SEARCH_NODE, IMAGE_GENERATION_NODE, \
    ADVANCED_RESEARCH_NODE, ADVANCED_WEB_SEARCH_NODE
from workflows.state import State

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
    enable_image_generation: bool = True  # Add this flag
    max_iterations: int = 10  # Maximum number of tool call iterations
    max_execution_time: int = 300  # Maximum execution time in seconds (5 minutes)



def build_workflow():
    # Create agents
    advanced_research_llm = AdvancedResearcherLlm()
    search_tools = get_search_tools()

    # Use the new bind_tools method for cleaner syntax
    advanced_research_llm.bind_tools(search_tools)

    # Create standardized agent nodes with explicit data flow
    researcher = advanced_research_llm.create_node(
        expected_fields=['topic'],
        output_field='trending_topics'
    )

    search_tool_node = ToolNode(search_tools)

    graph_builder = StateGraph(AdvancedState)

    graph_builder.add_node(ADVANCED_RESEARCH_NODE, researcher)
    graph_builder.add_node(ADVANCED_WEB_SEARCH_NODE, search_tool_node)

    graph_builder.add_edge(START, ADVANCED_RESEARCH_NODE)

    def route_after_research(state: AdvancedState) -> str:
        """
        Route to web_search if the researcher requests a tool call, otherwise to write.
        """
        try:
            last_message = state["messages"][-1] if state["messages"] else None
            logger.info(f"ROUTE CHECK: Last message: {last_message}")
            logger.info(f"ROUTE CHECK: Trending topics so far: {state.get('trending_topics')}")

            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                logger.info(f"Tool calls detected, routing to web search")
                return ADVANCED_WEB_SEARCH_NODE
            return END
        except (IndexError, AttributeError) as e:
            logger.warning(f"Routing error: {str(e)}, defaulting to write node")
            return END


    # Add conditional routing from researcher
    graph_builder.add_conditional_edges(
        ADVANCED_RESEARCH_NODE,
        route_after_research,
        {
            ADVANCED_WEB_SEARCH_NODE: ADVANCED_WEB_SEARCH_NODE,
            END: END
        }
    )

    # Add edge from web search back to researcher (creates the loop)
    graph_builder.add_edge(ADVANCED_WEB_SEARCH_NODE, ADVANCED_RESEARCH_NODE)

    # Set the researcher node as the finish point (it will end when no more tool calls are needed)
    graph_builder.set_finish_point(ADVANCED_RESEARCH_NODE)

    # Compile the graph before returning
    return graph_builder.compile()


def main_workflow(
        config: Optional[WorkflowConfig] = None,
        return_full_state: bool = False
) -> str | Dict[str, Any]:
    """
    Execute the main article generation workflow.

    Args:
        config: Optional configuration for the workflow
        return_full_state: If True, returns the complete state instead of just the final article

    Returns:
        The final article or complete workflow state if return_full_state is True

    Raises:
        ValueError: If topic is empty or invalid
        RuntimeError: If workflow execution fails
    """
    # Use default config if none provided
    if config is None:
        config = WorkflowConfig()

    try:
        # Build and execute the workflow
        compiled_graph = build_workflow()

        initial_state = {
            'topic': 'viral news stories trending topics',
            'messages': [],
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
            raise RuntimeError(
                f"Workflow failed after {config.retry_attempts} attempts. Last error: {str(last_exception)}")
        else:
            # Log execution statistics
            execution_time = time.time() - final_state.get('start_time', time.time())
            iteration_count = final_state.get('iteration_count', 0)
            
            logger.info(f"Workflow completed in {execution_time:.2f}s with {iteration_count} iterations")
            
            print("\n" + "=" * 80)
            print("🔥 TOP 10 TRENDING TOPICS ACROSS CATEGORIES 🔥")
            print("=" * 80 + "\n")

            for idx, topic in enumerate(final_state['trending_topics'], 1):
                print(f"{idx}. [{topic['category'].upper()}]")
                print(f"   📌 Topic: {topic['title']}")
                print(f"   📝 Description: {topic['description']}")
                print(f"   🔑 Keywords: {', '.join(topic['keywords'])}")
                print(f"   📈 Trending Because: {topic['trending_reason']}")
                print(f"   🔗 Source: {topic['source']}")
                print("-" * 80)

        return final_state if return_full_state else "Workflow completed successfully"

    except Exception as e:
        if config.enable_logging:
            logger.error(f"Workflow execution failed: {str(e)}")
        raise RuntimeError(f"Workflow execution failed: {str(e)}") from e


def main_workflow_with_progress(topic: str, word_count: int, progress_callback=None) -> str:
    """
    Execute the main workflow with progress tracking.

    Args:
        topic: The topic to research and write about
        word_count: Target word count for the article
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
    result = main_workflow(config)

    progress_wrapper("completed", "Article generation finished")
    return result

if __name__ == "__main__":
    main_workflow()