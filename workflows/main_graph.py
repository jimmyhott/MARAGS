# workflows/main_graph.py

import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

from langgraph.constants import END
from langgraph.graph import START
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from agents.editor import EditorLlm
from agents.researcher import ResearcherLlm
from agents.writer import WriterLlm
from tools.image_generation_tool import get_image_generation_tools
from tools.web_search_tool import get_search_tools
from utils import load_prompt
from workflows.constant import RESEARCH_NODE, WRITE_NODE, EDIT_NODE, WEB_SEARCH_NODE, IMAGE_GENERATION_NODE
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



def build_workflow(editor_style: str = "General", enable_image_generation: bool = True):
    # Create agents
    research_llm = ResearcherLlm()
    search_tools = get_search_tools()

    # Use the new bind_tools method for cleaner syntax
    research_llm.bind_tools(search_tools)

    writer_llm = WriterLlm()
    editor_llm = EditorLlm()
    # Bind image generation tools to editor if enabled
    if enable_image_generation:
        image_tools = get_image_generation_tools()
        editor_llm.bind_tools(image_tools)

    # Load shared image generation instructions
    image_instructions = load_prompt('prompts/image_generation_instruction.txt') if enable_image_generation else ""

    # Update editor prompt based on style
    editor_prompts = {
        "General": 'prompts/editor.txt',
        "Emotional": 'prompts/editor_emotional.txt',
        "Hilarious": 'prompts/editor_hilarious.txt',
        "Critical": 'prompts/editor_critical.txt'
    }

    if editor_style in editor_prompts:
        base_prompt = load_prompt(editor_prompts[editor_style])
        # Append image instructions if enabled
        if enable_image_generation:
            editor_llm.prompt_template = base_prompt.replace(
                "{article_draft}",
                "{article_draft}\n\n" + image_instructions
            )
        else:
            editor_llm.prompt_template = base_prompt

    logger.info(editor_llm.prompt_template)


    # Create standardized agent nodes with explicit data flow
    researcher = research_llm.create_node(
        expected_fields=['topic'],
        output_field='research_summary'
    )

    writer = writer_llm.create_node(
        expected_fields=['research_summary', 'word_count'],
        output_field='article_draft'
    )

    editor = editor_llm.create_node(
        expected_fields=['article_draft'],  # Added topic for context
        output_field='edited_article'
    )

    search_tool_node = ToolNode(search_tools)

    # Create image generation tool node if enabled
    if enable_image_generation:
        image_tool_node = ToolNode(image_tools)

    graph_builder = StateGraph(State)

    graph_builder.add_node(RESEARCH_NODE, researcher)
    graph_builder.add_node(WRITE_NODE, writer)
    graph_builder.add_node(EDIT_NODE, editor)
    graph_builder.add_node(WEB_SEARCH_NODE, search_tool_node)

    # Add image generation node if enabled
    if enable_image_generation:
        graph_builder.add_node(IMAGE_GENERATION_NODE, image_tool_node)

    graph_builder.add_edge(START, RESEARCH_NODE)

    def route_after_research(state: State) -> str:
        """
        Route to web_search if the researcher requests a tool call, otherwise to write.
        """
        try:
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                logger.info(f"Tool calls detected, routing to web search")
                return WEB_SEARCH_NODE
            return WRITE_NODE
        except (IndexError, AttributeError) as e:
            logger.warning(f"Routing error: {str(e)}, defaulting to write node")
            return WRITE_NODE

    def route_after_edit(state: State) -> str:
        """
        Route to image_generation if the editor requests a tool call, otherwise finish.
        """
        try:
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                logger.info(f"Image generation tool calls detected, routing to image generation")
                return IMAGE_GENERATION_NODE
            return END  # Changed from "end" to END
        except (IndexError, AttributeError) as e:
            logger.warning(f"Routing error: {str(e)}, finishing workflow")
            return END  # Changed from "end" to END


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

    # Add conditional routing after editor
    if enable_image_generation:
        graph_builder.add_conditional_edges(
            EDIT_NODE,
            route_after_edit,
            {
                IMAGE_GENERATION_NODE: IMAGE_GENERATION_NODE,
                END: END
            }
        )
        # After image generation, go back to editor to incorporate the images
        graph_builder.add_edge(IMAGE_GENERATION_NODE, EDIT_NODE)
    else:
        graph_builder.set_finish_point(EDIT_NODE)

    # Compile the graph before returning
    return graph_builder.compile()


def main_workflow(
        topic: str,
        word_count: int,
        config: Optional[WorkflowConfig] = None,
        return_full_state: bool = False
) -> str | Dict[str, Any]:
    """
    Execute the main article generation workflow.

    Args:
        topic: The topic to research and write about
        word_count: Target word count for the article
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

    if word_count <= 0:
        raise ValueError("Word count must be positive")

    # Use default config if none provided
    if config is None:
        config = WorkflowConfig()

    # Setup logging
    if config.enable_logging:
        logger.info(f"Starting workflow for topic: {topic} (target: {word_count} words)")
        start_time = time.time()

    try:
        # Build and execute the workflow
        compiled_graph = build_workflow(config.editor_style)

        initial_state = {
            'topic': topic.strip(),
            'word_count': word_count,
            'messages': [],
            # Initialize all expected output fields as None
            'research_summary': None,
            'article_draft': None,
            'edited_article': None
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

        # Validate final state
        if not final_state.get('edited_article'):
            # Fallback to extracting from messages if explicit field is not set
            messages = final_state.get('messages', [])
            if not messages:
                raise RuntimeError("Workflow completed but no messages were generated")

        # Log completion
        if config.enable_logging:
            execution_time = time.time() - start_time
            logger.info(f"Workflow completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Generated {len(final_state.get('messages', []))} messages")

        # Return appropriate result
        if return_full_state:
            return final_state
        else:
            # Prefer the explicit edited_article field
            if final_state.get('edited_article'):
                return final_state['edited_article']

            # Fallback to last AI message
            messages = final_state.get('messages', [])
            ai_messages = [msg for msg in messages if hasattr(msg, 'type') and msg.type == 'ai']
            if ai_messages:
                return ai_messages[-1].content
            else:
                return str(messages[-1].content) if messages and hasattr(messages[-1], 'content') else ""

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
    result = main_workflow(topic, word_count, config)

    progress_wrapper("completed", "Article generation finished")
    return result