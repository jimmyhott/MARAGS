# MARAGS - AI Article Generator

A comprehensive article generation system using AI-powered research, writing, and editing workflows.

## Features

- **Three-Stage Workflow**: Research → Write → Edit
- **Multiple LLM Support**: Azure OpenAI and Local Ollama
- **Streamlit UI**: User-friendly web interface
- **Progress Tracking**: Real-time workflow progress
- **Error Handling**: Robust retry mechanisms
- **Configuration Options**: Customizable workflow settings

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd MARAGS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables (for Azure OpenAI):
```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
```

## Usage

### Streamlit Web Interface (Recommended)

Run the Streamlit app for a user-friendly interface:

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

### Command Line Interface

For programmatic usage:

```bash
python app.py
```

## Debugging

### Built-in Debug Mode

The Streamlit app includes a built-in debug mode:

1. **Enable Debug Mode**: Check the "Enable Debug Mode" checkbox in the sidebar
2. **View Debug Logs**: Click "View Debug Logs" to see detailed execution information
3. **Error Inspection**: Detailed error information is automatically displayed in debug mode
4. **Session State**: Inspect the current session state for troubleshooting

### Debug Script

Use the dedicated debug script to test individual components:

```bash
# Run comprehensive tests
python debug_streamlit.py

# Test specific components
python debug_streamlit.py imports    # Test imports
python debug_streamlit.py llm        # Test LLM connections
python debug_streamlit.py workflow   # Test workflow components
python debug_streamlit.py agents     # Test agent creation
python debug_streamlit.py env        # Test environment
```

### Common Debugging Techniques

1. **Console Logs**: Check the terminal where you ran `streamlit run` for error messages
2. **Browser Developer Tools**: Press F12 to inspect network requests and console errors
3. **Streamlit Cache**: Clear cache with `streamlit cache clear`
4. **Log Files**: Debug logs are saved to `streamlit_debug.log` and timestamped files

### Troubleshooting Common Issues

- **Import Errors**: Run `python debug_streamlit.py imports`
- **LLM Connection Issues**: Check API keys and run `python debug_streamlit.py llm`
- **Workflow Errors**: Enable debug mode in the Streamlit app for detailed error information
- **Performance Issues**: Check the debug logs for timing information

## Configuration

### Streamlit Interface Options

- **LLM Settings**: Choose between Azure OpenAI and Local Ollama
- **Workflow Settings**: Configure logging, retry attempts, and timeout
- **Advanced Options**: Return full workflow state for debugging

### Programmatic Configuration

```python
from workflows.main_graph import main_workflow, WorkflowConfig

config = WorkflowConfig(
    use_local_llm=False,
    enable_logging=True,
    timeout_seconds=120,
    retry_attempts=3
)

article = main_workflow("Your topic here", config)
```

## Project Structure

```
MARAGS/
├── agents/           # AI agents for research, writing, editing
├── llm/             # LLM client configurations
├── workflows/       # LangGraph workflow definitions
├── streamlit_app.py # Streamlit web interface
├── app.py          # Command line interface
└── requirements.txt # Python dependencies
```

## Workflow Stages

1. **Research**: Gather comprehensive information about the topic
2. **Write**: Create an initial draft based on research
3. **Edit**: Polish and finalize the article

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]
