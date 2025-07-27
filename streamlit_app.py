import logging
import sys
import time
import traceback
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from workflows.main_graph import main_workflow, WorkflowConfig, build_workflow

# Configure page
st.set_page_config(
    page_title="MARAGS - Multi-Agent Report and Article Generation System",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    /* Article images */
    .article-container img {
        max-width: 100%;
        height: auto;
        margin: 1.5rem auto;
        display: block;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Image captions (italicized text after images) */
    .article-container img + em,
    .article-container img + p > em:first-child {
        display: block;
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: -1rem;
        margin-bottom: 1.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
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
    .generated-image {
        max-width: 100%;
        border-radius: 8px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)


# Debug logging setup
def setup_debug_logging():
    """Setup detailed logging for debugging"""
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
    """Helper function to log debug information"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    debug_msg = f"[{timestamp}] {message}"
    if data:
        debug_msg += f"\nData: {data}"
    return debug_msg


def display_workflow_graph(enable_image_generation=True):
    """Display the workflow graph structure using Mermaid"""
    try:
        # Build the workflow to get the graph
        compiled_graph = build_workflow(enable_image_generation=enable_image_generation)

        # Generate Mermaid diagram
        mermaid_code = compiled_graph.get_graph().draw_mermaid()

        # Create HTML with Mermaid
        mermaid_html = f"""
        <div class="mermaid">
        {mermaid_code}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
        mermaid.initialize({{startOnLoad: true, theme: 'default'}});
        </script>
        """

        # Display using Streamlit components
        components.html(mermaid_html, height=400)

    except Exception as e:
        st.error(f"Failed to display workflow graph: {str(e)}")
        st.code(f"Error: {str(e)}")


def main():
    # Initialize session state for debugging
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False
    if 'debug_logs' not in st.session_state:
        st.session_state.debug_logs = []
    if 'error_logs' not in st.session_state:
        st.session_state.error_logs = []
    if 'show_graph' not in st.session_state:
        st.session_state.show_graph = False

    # Setup debug logger
    if st.session_state.debug_mode:
        logger = setup_debug_logging()
    else:
        logger = logging.getLogger(__name__)

    # Header
    st.markdown('<h1 class="main-header">📝 Multi-Agents Blogpost Generation System</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Generate comprehensive blogpost using AI-powered research, writing, and editing agents with optional image generation</p>',
        unsafe_allow_html=True)

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Debug Mode Toggle
        st.subheader("🐛 Debug Mode")
        debug_mode = st.checkbox("Enable Debug Mode", value=st.session_state.debug_mode)
        if debug_mode != st.session_state.debug_mode:
            st.session_state.debug_mode = debug_mode
            st.session_state.debug_logs = []
            st.session_state.error_logs = []
            st.rerun()

        if debug_mode:
            st.info("🔍 Debug mode enabled - check console and logs for detailed information")

            # Debug controls
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

        # Image Generation Toggle
        st.subheader("🎨 Image Generation")
        enable_image_generation = st.checkbox(
            "Enable Image Generation",
            value=True,
            help="Allow the editor to generate images to accompany the article"
        )

        # Editor Style Configuration
        st.subheader("Editor Style")
        editor_style = st.selectbox(
            "Choose Editor Style",
            options=["General", "Emotional", "Hilarious", "Critical"],
            index=0,
            help="Select the tone and style for the final article"
        )

        st.markdown("---")

        # Workflow Graph Display
        st.subheader("📊 Workflow Structure")
        if st.button("🔍 Show Workflow Graph"):
            st.session_state.show_graph = True

        if st.session_state.get('show_graph', False):
            with st.expander("📊 Workflow Graph Structure", expanded=True):
                display_workflow_graph(enable_image_generation)

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

        # Progress tracking
        if 'progress' not in st.session_state:
            st.session_state.progress = None
        if 'workflow_results' not in st.session_state:
            st.session_state.workflow_results = None

        # Progress callback function
        def progress_callback(stage, message):
            st.session_state.progress = f"{stage}: {message}"
            if st.session_state.debug_mode:
                debug_msg = debug_info(f"Progress: {stage}", message)
                st.session_state.debug_logs.append(debug_msg)
            st.rerun()

        if generate_button and topic.strip():
            # Debug logging
            if st.session_state.debug_mode:
                debug_msg = debug_info("Generate button clicked", {"topic": topic})
                st.session_state.debug_logs.append(debug_msg)

            # Clear previous results
            st.session_state.workflow_results = None

            # Create configuration
            config = WorkflowConfig(
                enable_logging=enable_logging,
                timeout_seconds=timeout_seconds,
                retry_attempts=retry_attempts,
                editor_style=editor_style,
                enable_image_generation=enable_image_generation
            )

            if st.session_state.debug_mode:
                debug_msg = debug_info("Configuration created", {
                    "enable_logging": enable_logging,
                    "timeout_seconds": timeout_seconds,
                    "retry_attempts": retry_attempts,
                    "editor_style": editor_style,
                    "enable_image_generation": enable_image_generation
                })
                st.session_state.debug_logs.append(debug_msg)

            # Progress container
            progress_container = st.container()

            with progress_container:
                st.markdown('<div class="progress-container">', unsafe_allow_html=True)
                st.subheader("🔄 Progress")
                progress_bar = st.progress(0)
                status_text = st.empty()
                st.markdown('</div>', unsafe_allow_html=True)

            try:
                # Update progress
                progress_bar.progress(25)
                status_text.text("Initializing workflow...")
                time.sleep(0.5)

                if st.session_state.debug_mode:
                    debug_msg = debug_info("Workflow initialization started")
                    st.session_state.debug_logs.append(debug_msg)

                progress_bar.progress(50)
                status_text.text("Agents orchestrating research, writing, and editing...")

                # Run the workflow with full state to get all outputs
                if st.session_state.debug_mode:
                    debug_msg = debug_info("Running workflow with full state return")
                    st.session_state.debug_logs.append(debug_msg)

                result = main_workflow(topic, 1000, config, return_full_state=True)
                st.session_state.workflow_results = result

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

                # Log detailed error information
                if st.session_state.debug_mode:
                    error_msg = debug_info("Workflow execution failed", {
                        "error_type": type(e).__name__,
                        "error_message": str(e),
                        "traceback": traceback.format_exc()
                    })
                    st.session_state.error_logs.append(error_msg)

                    # Show detailed error in debug mode
                    with st.expander("🐛 Detailed Error Information"):
                        st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                        st.text(f"Error Type: {type(e).__name__}")
                        st.text(f"Error Message: {str(e)}")
                        st.text("Full Traceback:")
                        st.code(traceback.format_exc())
                        st.markdown('</div>', unsafe_allow_html=True)

        # Display progress if available
        if st.session_state.progress:
            st.info(f"🔄 {st.session_state.progress}")

        # Display results using the new state structure
        if st.session_state.workflow_results:
            st.markdown("---")
            st.subheader("📋 Workflow Results")

            results = st.session_state.workflow_results

            # Access the state fields directly
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

            # Generated Images
                # Check if there are generated images to embed
                if generated_images:
                    # Create a mapping of image prompts to URLs for easy replacement
                    image_map = {}
                    for img in generated_images:
                        if img.get('url') and img.get('prompt'):
                            image_map[img['prompt']] = img['url']

                    # Replace image placeholders in the article with actual URLs
                    final_article = edited_article

                    # Look for markdown image syntax and ensure URLs are properly embedded
                    import re

                    # Pattern to find markdown images
                    image_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

                    def replace_image(match):
                        alt_text = match.group(1)
                        url = match.group(2)

                        # If the URL is a placeholder or matches a prompt, replace with actual URL
                        for prompt, actual_url in image_map.items():
                            if prompt.lower() in alt_text.lower() or prompt.lower() in url.lower():
                                return f'![{alt_text}]({actual_url})'

                        # If it's already a valid URL, keep it
                        if url.startswith('http'):
                            return match.group(0)

                        # Otherwise, try to find a matching image
                        for prompt, actual_url in image_map.items():
                            if any(word in alt_text.lower() for word in prompt.lower().split()):
                                return f'![{alt_text}]({actual_url})'

                        return match.group(0)

                    final_article = re.sub(image_pattern, replace_image, final_article)

                    # Display the article with embedded images
                    st.markdown(final_article)
                else:
                    # No images, display article as is
                    st.markdown(edited_article)

                st.markdown('</div>', unsafe_allow_html=True)

            # Final Edited Article
            if edited_article:
                st.markdown('<div class="article-container">', unsafe_allow_html=True)
                st.markdown('<div class="stage-header">📄 Final Edited Article</div>', unsafe_allow_html=True)
                st.markdown(edited_article)
                st.markdown('</div>', unsafe_allow_html=True)

            # Show complete conversation in debug mode
            if st.session_state.debug_mode:
                st.markdown("---")
                st.subheader("🐛 Debug Information")

                # Show state fields
                with st.expander("📊 State Fields"):
                    st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                    st.text(f"Topic: {results.get('topic', 'N/A')}")
                    st.text(f"Word Count: {results.get('word_count', 'N/A')}")
                    st.text(f"Research Summary Length: {len(research_summary) if research_summary else 0} chars")
                    st.text(f"Article Draft Length: {len(article_draft) if article_draft else 0} chars")
                    st.text(f"Edited Article Length: {len(edited_article) if edited_article else 0} chars")
                    st.text(f"Generated Images: {len(generated_images)}")
                    st.text(f"Total Messages: {len(results.get('messages', []))}")
                    st.markdown('</div>', unsafe_allow_html=True)

                # Show complete message history
                messages = results.get('messages', [])
                if messages:
                    with st.expander(f"💬 Complete Message History ({len(messages)} messages)"):
                        st.markdown('<div class="debug-container">', unsafe_allow_html=True)

                        for i, message in enumerate(messages):
                            if hasattr(message, 'content') and message.content:
                                if hasattr(message, 'type'):
                                    if message.type == 'human':
                                        st.markdown(f"**👤 Human Message {i + 1}:**")
                                        st.text(message.content[:500] + "..." if len(
                                            message.content) > 500 else message.content)
                                    elif message.type == 'ai':
                                        st.markdown(f"**🤖 AI Message {i + 1}:**")
                                        st.text(message.content[:500] + "..." if len(
                                            message.content) > 500 else message.content)
                                        # Check for tool calls
                                        if hasattr(message, 'tool_calls') and message.tool_calls:
                                            st.markdown("**Tool Calls:**")
                                            for tool_call in message.tool_calls:
                                                st.text(f"  - {tool_call.get('name', 'Unknown tool')}")
                                    elif message.type == 'tool':
                                        st.markdown(f"**🔧 Tool Message {i + 1}:**")
                                        st.text(str(message.content)[:500] + "..." if len(
                                            str(message.content)) > 500 else str(message.content))
                                else:
                                    st.markdown(f"**📝 Message {i + 1}:**")
                                    st.text(
                                        str(message.content)[:500] + "..." if len(str(message.content)) > 500 else str(
                                            message.content))

                                st.markdown("---")

                        st.markdown('</div>', unsafe_allow_html=True)

        # Clear results button
        if st.session_state.workflow_results:
            if st.button("🗑️ Clear Results"):
                st.session_state.workflow_results = None
                st.session_state.progress = None
                st.rerun()

        # Debug logs display
        if st.session_state.debug_mode and (st.session_state.debug_logs or st.session_state.error_logs):
            st.markdown("---")
            st.subheader("🐛 System Logs")

            # Debug logs
            if st.session_state.debug_logs:
                with st.expander(f"📋 Debug Logs ({len(st.session_state.debug_logs)} entries)"):
                    st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                    for log in st.session_state.debug_logs[-10:]:  # Show last 10 logs
                        st.text(log)
                    st.markdown('</div>', unsafe_allow_html=True)

            # Error logs
            if st.session_state.error_logs:
                with st.expander(f"❌ Error Logs ({len(st.session_state.error_logs)} entries)"):
                    st.markdown('<div class="debug-container">', unsafe_allow_html=True)
                    for error in st.session_state.error_logs[-5:]:  # Show last 5 errors
                        st.text(error)
                    st.markdown('</div>', unsafe_allow_html=True)

            # Session state inspection
            with st.expander("🔍 Session State Inspection"):
                # Filter out large values for readability
                filtered_state = {}
                for k, v in st.session_state.items():
                    if k == 'workflow_results' and v:
                        # Special handling for workflow results
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


if __name__ == "__main__":
    main()