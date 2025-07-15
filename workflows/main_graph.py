# workflows/main_graph.py
from langgraph.graph import StateGraph
from typing import TypedDict, Optional, Dict, Any
from agents.researcher import ResearcherAgent
from agents.writer import WriterAgent
from agents.editor import EditorAgent
from llm.azure_llm_client import get_azure_llm
from llm.local_llm_client import get_local_llm
import logging
from dataclasses import dataclass
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkflowState(TypedDict):
    topic: str
    research_summary: str
    draft: str
    final_article: str

@dataclass
class WorkflowConfig:
    """Configuration for the main workflow"""
    use_local_llm: bool = False
    enable_logging: bool = True
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 3

def build_workflow():
    llm = get_azure_llm()
    researcher = ResearcherAgent(llm)
    writer = WriterAgent(llm)
    editor = EditorAgent(llm)

    # Each node receives and returns the state dictionary
    def research_node(state):
        topic = state.get('topic')
        research_summary = researcher.run(topic)
        state['research_summary'] = research_summary
        return state

    def write_node(state):
        research_summary = state.get('research_summary')
        draft = writer.run(research_summary)
        state['draft'] = draft
        return state

    def edit_node(state):
        draft = state.get('draft')
        final_article = editor.run(draft)
        state['final_article'] = final_article
        return state

    
    graph = StateGraph(WorkflowState)
    graph.add_node('research', research_node)
    graph.add_node('write', write_node)
    graph.add_node('edit', edit_node)

    graph.add_edge('research', 'write')
    graph.add_edge('write', 'edit')

    graph.set_entry_point('research')
    graph.set_finish_point('edit')

    # Compile the graph before returning
    return graph.compile()

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
            'research_summary': '',
            'draft': '',
            'final_article': ''
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
        if not final_state.get('final_article'):
            raise RuntimeError("Workflow completed but no final article was generated")
        
        # Log completion
        if config.enable_logging:
            execution_time = time.time() - start_time
            logger.info(f"Workflow completed successfully in {execution_time:.2f} seconds")
            logger.info(f"Generated article length: {len(final_state['final_article'])} characters")
        
        # Return appropriate result
        if return_full_state:
            return final_state
        else:
            return final_state.get('final_article', '')
            
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
