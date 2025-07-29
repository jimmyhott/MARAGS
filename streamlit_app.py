import logging
import sys
import time
import traceback
from datetime import datetime
import re

import streamlit as st
import streamlit.components.v1 as components

from workflows.main_graph import main_workflow, WorkflowConfig, build_workflow

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="MARAGS - Multi-Agent Report and Article Generation System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM STYLING
# ============================================================================

CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }

    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }

    /* Container Styles */
    .article-container {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        margin: 1rem 0;
    }

    .research-container {
        background-color: #e8f5e8;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }

    .draft-container {
        background-color: #fff3cd;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }

    .image-container {
        background-color: #f0e6ff;
        padding: 2rem;
        border-radius: 10px;
        border-left: 5px solid #6f42c1;
        margin: 1rem 0;
    }

    .progress-container {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .debug-container {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 8px;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
        font-family: monospace;
        font-size: 0.9rem;
    }

    /* Image Styles */
    .article-container img {
        max-width: 100%;
        height: auto;
        margin: 1.5rem auto;
        display: block;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .article-container img + em,
    .article-container img + p > em:first-child {
        display: block;
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: -1rem;
        margin-bottom: 1.5rem;
    }

    .generated-image {
        max-width: 100%;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    /* Button and UI Elements */
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        border: none;
        padding: 0.75rem;
        border-radius: 5px;
        font-size: 1.1rem;
        font-weight: bold;
    }

    .stButton > button:hover {
        background-color: #1565c0;
    }

    .stage-header {
        font-size: 1.3rem;
        font-weight: bold;
        color: #333;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
</style>
"""


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def setup_debug_logging():
    """Setup detailed logging for debugging."""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('streamlit_debug.log')
        ]
    )
    return logging.getLogger(__name__)


def debug_info(message, data=None):
    """Helper function to log debug information."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    debug_msg = f"[{timestamp}] {message}"
    if data:
        debug_msg += f"\nData: {data}"
    return debug_msg


def initialize_session_state():
    """Initialize all session state variables."""
    defaults = {
        'debug_mode': False,
        'debug_logs': [],
        'error_logs': [],
        'show_graph': False,
        'progress': None,
        'workflow_results': None
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def replace_image_placeholders(article_text, generated_images):
    """Replace image placeholders in article with actual URLs."""
    if not generated_images:
        return article_text

    # Create a mapping of image prompts to URLs
    image_map = {}
    for img in generated_images:
        if img.get('url') and img.get('prompt'):
            image_map[img['prompt']] = img['url']

    # Pattern to find markdown images
    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

    def replace_image(match):
        alt_text = match.group(1)
        url = match.group(2)

        # If URL is already valid, keep it
        if url.startswith('http'):
            return match.group(0)

        # Try to find matching image by prompt
        for prompt, actual_url in image_map.items():
            if (prompt.lower() in alt_text.lower() or
                    prompt.lower() in url.lower() or
                    any(word in alt_text.lower() for word in prompt.lower().split())):
                return f'![{alt_text}]({actual_url})'

        return match.group(0)

    return re.sub(image_pattern, replace_image, article_text)


# ============================================================================
# UI COMPONENTS
# ============================================================================

def display_workflow_graph(enable_image_generation=True):
    """Display the workflow graph structure using Mermaid."""
    try:
        compiled_graph = build_workflow(enable_image_generation=enable_image_generation)
        mermaid_code = compiled_graph.get_graph().draw_mermaid()

        mermaid_html = f"""
        <div class="mermaid">
        {mermaid_code}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
        mermaid.initialize({{startOnLoad: true, theme: 'default'}});
        </script>
        """

        components.html(mermaid_html, height=400)

    except Exception as e:
        st.error(f"Failed to display workflow graph: {str(e)}")


def render_sidebar():
    """Render the sidebar configuration."""
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Debug Mode
        st.subheader("🐛 Debug Mode")
        debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)

        if debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_mode
            st.session_state.debug_logs = []
            st.session_state.error_logs = []
            st.rerun()

        if debug_mode:
            st.info("🔍 Debug mode enabled - check console and logs for detailed information")

            if st.button("📋 View Debug Logs"):
                st.session_state.show_debug_logs = True

            if st.button("🗑️ Clear Debug Logs"):
                st.session_state.debug_logs = []
                st.session_state.error_logs = []
                st.success("Debug logs cleared!")

        # Workflow Configuration
        st.subheader("Workflow Settings")
        enable_logging = st.checkbox("Enable Logging", value=True)
        retry_attempts = st.slider("Retry Attempts", min_value=1, max_value=5, value=3)
        timeout_seconds = st.number_input("Timeout (seconds)", min_value=30, max_value=300, value=120, step=30)

        # Image Generation
        st.subheader("🎨 Image Generation")
        enable_image_generation = st.checkbox(
            "Enable Image Generation",
            value=True,
            help="Allow the editor to generate images to accompany the article"
        )

        # Editor Style
        st.subheader("Editor Style")
        editor_style = st.selectbox(
            "Choose Editor Style",
            options=["General", "Emotional", "Hilarious", "Critical"],
            index=0,
            help="Select the tone and style for the final article"
        )

        st.markdown("---")

        # Workflow Graph
        st.subheader("📊 Workflow Structure")
        if st.button("🔍 Show Workflow Graph"):
            st.session_state.show_graph = True

        if st.session_state.get('show_graph', False):
            with st.expander("📊 Workflow Graph Structure", expanded=True):
                display_workflow_graph(enable_image_generation)

        return {
            'enable_logging': enable_logging,
            'retry_attempts': retry_attempts,
            'timeout_seconds': timeout_seconds,
            'enable_image_generation': enable_image_generation,
            'editor_style': editor_style
        }


def display_results(results):
    """Display workflow results."""
    st.markdown("---")
    st.subheader("📋 Workflow Results")

    research_summary = results.get('research_summary')
    article_draft = results.get('article_draft')
    edited_article = results.get('edited_article')
    generated_images = results.get('generated_images', [])

    # Research Summary
    if research_summary:
        st.markdown('<div class="research-container">', unsafe_allow_html=True)
        st.markdown('<div class="stage-header">🔍 Research Summary</div>', unsafe_allow_html=True)
        st.markdown(research_summary)
        st.markdown('</div>', unsafe_allow_html=True)

    # Draft Article
    if article_draft:
        st.markdown('<div class="draft-container">', unsafe_allow_html=True)
        st.markdown('<div class="stage-header">✍️ Draft Article</div>', unsafe_allow_html=True)
        st.markdown(article_draft)
        st.markdown('</div>', unsafe_allow_html=True)

    # Final Edited Article with Images
    if edited_article:
        st.markdown('<div class="article-container">', unsafe_allow_html=True)
        st.markdown('<div class="stage-header">📄 Final Edited Article</div>', unsafe_allow_html=True)

        # Replace image placeholders if images were generated
        final_article = replace_image_placeholders(edited_article, generated_images)
        st.markdown(final_article)

        st.markdown('</div>', unsafe_allow_html=True)

    # Debug information
    if st.session_state.debug_mode:
        display_debug_info(results)


def display_debug_info(results):
    """Display debug information."""
    st.markdown("---")
    st.subheader("🐛 Debug Information")

    # State fields
    with st.expander("📊 State Fields"):
        st.markdown('<div class="debug-container">', unsafe_allow_html=True)

        debug_data = {
            "Topic": results.get('topic', 'N/A'),
            "Word Count": results.get('word_count', 'N/A'),
            "Research Summary Length": f"{len(results.get('research_summary', ''))} chars",
            "Article Draft Length": f"{len(results.get('article_draft', ''))} chars",
            "Edited Article Length": f"{len(results.get('edited_article', ''))} chars",
            "Generated Images": len(results.get('generated_images', [])),
            "Total Messages": len(results.get('messages', []))
        }

        for key, value in debug_data.items():
            st.text(f"{key}: {value}")

        st.markdown('</div>', unsafe_allow_html=True)

    # Message history
    messages = results.get('messages', [])
    if messages:
        with st.expander(f"💬 Complete Message History ({len(messages)} messages)"):
            st.markdown('<div class="debug-container">', unsafe_allow_html=True)

            for i, message in enumerate(messages):
                if hasattr(message, 'content') and message.content:
                    message_type = getattr(message, 'type', 'unknown')

                    if message_type == 'human':
                        st.markdown(f"**👤 Human Message {i + 1}:**")
                    elif message_type == 'ai':
                        st.markdown(f"**🤖 AI Message {i + 1}:**")
                    elif message_type == 'tool':
                        st.markdown(f"**🔧 Tool Message {i + 1}:**")
                    else:
                        st.markdown(f"**📝 Message {i + 1}:**")

                    content = str(message.content)
                    st.text(content[:500] + "..." if len(content) > 500 else content)

                    # Show tool calls for AI messages
                    if message_type == 'ai' and hasattr(message, 'tool_calls') and message.tool_calls:
                        st.markdown("**Tool Calls:**")
                        for tool_call in message.tool_calls:
                            st.text(f"  - {tool_call.get('name', 'Unknown tool')}")

                    st.markdown("---")

            st.markdown('</div>', unsafe_allow_html=True)


def display_logs():
    """Display debug and error logs."""
    if st.session_state.debug_mode and (st.session_state.debug_logs or st.session_state.error_logs):
        st.markdown("---")
        st.subheader("🐛 System Logs")

        # Debug logs
        if st.session_state.debug_logs:
            with st.expander(f"📋 Debug Logs ({len(st.session_state.debug_logs)} entries)"):
                st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                for log in st.session_state.debug_logs[-10:]:
                    st.text(log)
                st.markdown('</div>', unsafe_allow_html=True)

        # Error logs
        if st.session_state.error_logs:
            with st.expander(f"❌ Error Logs ({len(st.session_state.error_logs)} entries)"):
                st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                for error in st.session_state.error_logs[-5:]:
                    st.text(error)
                st.markdown('</div>', unsafe_allow_html=True)

        # Session state inspection
        with st.expander("🔍 Session State Inspection"):
            filtered_state = {}
            for k, v in st.session_state.items():
                if k == 'workflow_results' and v:
                    filtered_state[k] = {
                        'has_research_summary': bool(v.get('research_summary')),
                        'has_article_draft': bool(v.get('article_draft')),
                        'has_edited_article': bool(v.get('edited_article')),
                        'has_generated_images': bool(v.get('generated_images')),
                        'image_count': len(v.get('generated_images', [])),
                        'message_count': len(v.get('messages', []))
                    }
                else:
                    filtered_state[k] = str(v)[:200] + "..." if len(str(v)) > 200 else v

            st.json(filtered_state)


def run_workflow(topic, config):
    """Run the article generation workflow."""
    # Progress container
    progress_container = st.container()

    with progress_container:
        st.markdown('<div class="progress-container">', unsafe_allow_html=True)
        st.subheader("🔄 Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        st.markdown('</div>', unsafe_allow_html=True)

    try:
        # Initialize
        progress_bar.progress(25)
        status_text.text("Initializing workflow...")
        time.sleep(0.5)

        if st.session_state.debug_mode:
            debug_msg = debug_info("Workflow initialization started")
            st.session_state.debug_logs.append(debug_msg)

        # Run workflow
        progress_bar.progress(50)
        status_text.text("Agents orchestrating research, writing, and editing...")

        if st.session_state.debug_mode:
            debug_msg = debug_info("Running workflow with full state return")
            st.session_state.debug_logs.append(debug_msg)

        result = main_workflow(topic, 1000, config, return_full_state=True)
        st.session_state.workflow_results = result

        # Complete
        progress_bar.progress(100)
        status_text.text("Article generated successfully! ✅")
        time.sleep(1)

        if st.session_state.debug_mode:
            debug_msg = debug_info("Workflow completed successfully", {
                "has_messages": bool(result.get('messages')),
                "message_count": len(result.get('messages', [])),
                "has_research_summary": bool(result.get('research_summary')),
                "has_article_draft": bool(result.get('article_draft')),
                "has_edited_article": bool(result.get('edited_article')),
                "has_generated_images": bool(result.get('generated_images'))
            })
            st.session_state.debug_logs.append(debug_msg)

    except Exception as e:
        progress_bar.progress(0)
        status_text.text(f"Error: {str(e)} ❌")
        st.error(f"Failed to generate article: {str(e)}")

        # Log error
        if st.session_state.debug_mode:
            error_msg = debug_info("Workflow execution failed", {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "traceback": traceback.format_exc()
            })
            st.session_state.error_logs.append(error_msg)

            # Show detailed error
            with st.expander("🐛 Detailed Error Information"):
                st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                st.text(f"Error Type: {type(e).__name__}")
                st.text(f"Error Message: {str(e)}")
                st.text("Full Traceback:")
                st.code(traceback.format_exc())
                st.markdown('</div>', unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    # Initialize session state
    initialize_session_state()

    # Setup logging if debug mode is enabled
    logger = setup_debug_logging() if st.session_state.debug_mode else logging.getLogger(__name__)

    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Header
    st.markdown('<h1 class="main-header">📝 Multi-Agents Blogpost Generation System</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Generate comprehensive blogpost using AI-powered research, writing, and editing agents with optional image generation</p>',
        unsafe_allow_html=True
    )

    # Sidebar configuration
    config_values = render_sidebar()

    # Main content area
    col1, col2, col3 = st.columns([0.5, 3, 0.5])

    with col2:
        # Topic input
        st.subheader("🎯 Enter Your Topic")
        topic = st.text_area(
            "What would you like to write about?",
            placeholder="Enter a topic for your article...",
            height=100,
            help="Be specific and descriptive for better results"
        )

        # Generate button
        generate_button = st.button("🚀 Generate Blogpost", type="primary")

        # Handle generation
        if generate_button and topic.strip():
            # Debug logging
            if st.session_state.debug_mode:
                debug_msg = debug_info("Generate button clicked", {"topic": topic})
                st.session_state.debug_logs.append(debug_msg)

            # Clear previous results
            st.session_state.workflow_results = None

            # Create configuration
            config = WorkflowConfig(
                enable_logging=config_values['enable_logging'],
                timeout_seconds=config_values['timeout_seconds'],
                retry_attempts=config_values['retry_attempts'],
                editor_style=config_values['editor_style'],
                enable_image_generation=config_values['enable_image_generation']
            )

            if st.session_state.debug_mode:
                debug_msg = debug_info("Configuration created", config_values)
                st.session_state.debug_logs.append(debug_msg)

            # Run workflow
            run_workflow(topic, config)

        # Display progress if available
        if st.session_state.progress:
            st.info(f"🔄 {st.session_state.progress}")

        # Display results
        if st.session_state.workflow_results:
            display_results(st.session_state.workflow_results)

        # Clear results button
        if st.session_state.workflow_results:
            if st.button("🗑️ Clear Results"):
                st.session_state.workflow_results = None
                st.session_state.progress = None
                st.rerun()

        # Display logs
        display_logs()


if __name__ == "__main__":
    main()