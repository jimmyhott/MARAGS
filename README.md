# MARAGS - Multi-Agent Research and Article Generation System

A comprehensive AI-powered article generation system that uses a three-stage workflow: Research → Write → Edit. Built with LangGraph for workflow orchestration and Streamlit for the user interface.

## Features

- **Three-Stage AI Workflow**: Research → Write → Edit with specialized agents
- **Multiple Editor Styles**: General, Emotional, Hilarious, and Critical
- **Image Generation**: AI-generated images to accompany articles
- **Web Search Integration**: Real-time information gathering via Tavily
- **Azure OpenAI Integration**: Powered by GPT-4o for high-quality content
- **Streamlit UI**: User-friendly web interface with real-time progress tracking
- **Debug Mode**: Comprehensive debugging and logging capabilities
- **Configurable Workflow**: Customizable settings for different use cases

## Project Structure

```
MARAGS/
├── agents/                    # AI agents for research, writing, editing
│   ├── base_agent.py         # Base class for all agents
│   ├── researcher.py         # Research agent for information gathering
│   ├── writer.py             # Writing agent for article creation
│   └── editor.py             # Editing agent for content refinement
├── llm/                      # LLM client configurations
│   ├── azure_llm_client.py  # Azure OpenAI client
│   ├── azure_llm_wrapper.py # Azure LLM wrapper
│   ├── azure_secrets.py     # Azure API configuration
│   └── local_llm_client.py  # Local Ollama client
├── tools/                    # External tool integrations
│   ├── image_generation_tool.py # DALL-E 3 image generation
│   ├── web_search_tool.py   # Tavily web search
│   └── tool_secrets.py      # Tool API keys
├── workflows/                # LangGraph workflow definitions
│   ├── main_graph.py        # Main workflow orchestration
│   ├── state.py             # Workflow state management
│   └── constant.py          # Workflow constants
├── prompts/                  # Agent prompt templates
│   ├── researcher.txt        # Research agent prompts
│   ├── writer.txt           # Writing agent prompts
│   ├── editor.txt           # General editor prompts
│   ├── editor_emotional.txt # Emotional style prompts
│   ├── editor_hilarious.txt # Hilarious style prompts
│   ├── editor_critical.txt  # Critical style prompts
│   ├── editor_cantonese.txt # Cantonese style prompts
│   └── image_generation_instruction.txt # Image generation prompts
├── streamlit_app.py         # Main Streamlit web interface
├── app.py                   # Command-line interface
├── debug_streamlit.py       # Debug script for troubleshooting
├── utils.py                 # Utility functions
└── requirements.txt         # Python dependencies
```

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd MARAGS
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up environment variables** (for Azure OpenAI):
```bash
export AZURE_OPENAI_API_KEY="your-api-key"
export AZURE_OPENAI_ENDPOINT="your-endpoint"
export AZURE_DALL_E_3_API_KEY="your-dalle-api-key"
export AZURE_DALL_E_3_ENDPOINT="your-dalle-endpoint"
export PROD_TAVILY_API_KEY="your-tavily-api-key"
```

## Usage

### Streamlit Web Interface (Recommended)

Run the Streamlit app for a user-friendly interface:

```bash
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

**Features in the Streamlit interface:**
- Topic input with word count specification
- Editor style selection (General, Emotional, Hilarious, Critical)
- Image generation toggle
- Real-time progress tracking
- Debug mode with detailed logging
- Workflow visualization
- Session state inspection

### Command Line Interface

For programmatic usage:

```bash
python app.py
```

### Programmatic Usage

```python
from workflows.main_graph import main_workflow, WorkflowConfig

config = WorkflowConfig(
    enable_logging=True,
    timeout_seconds=120,
    retry_attempts=3,
    editor_style="General",
    enable_image_generation=True
)

article = main_workflow("Your topic here", 1000, config)
```

## Workflow Stages

### 1. Research Stage
- **Agent**: `ResearcherLlm`
- **Function**: Gathers comprehensive information about the topic
- **Tools**: Web search via Tavily
- **Output**: Research summary

### 2. Writing Stage
- **Agent**: `WriterLlm`
- **Function**: Creates initial article draft based on research
- **Input**: Research summary and topic
- **Output**: Article draft

### 3. Editing Stage
- **Agent**: `EditorLlm`
- **Function**: Refines and polishes the article
- **Tools**: Image generation (optional)
- **Output**: Final edited article with images

## Editor Styles

- **General**: Standard professional editing
- **Emotional**: Empathetic and emotionally engaging content
- **Hilarious**: Humorous and entertaining style
- **Critical**: Analytical and critical perspective
- **Cantonese**: Cantonese language style

## Debugging

### Built-in Debug Mode

The Streamlit app includes comprehensive debugging:

1. **Enable Debug Mode**: Check the "Enable Debug Mode" checkbox
2. **View Debug Logs**: Click "View Debug Logs" for detailed execution info
3. **Error Inspection**: Automatic error display in debug mode
4. **Session State**: Inspect current session state for troubleshooting

### Debug Script

Use the dedicated debug script for component testing:

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

### Troubleshooting

- **Import Errors**: Run `python debug_streamlit.py imports`
- **LLM Connection Issues**: Check API keys and run `python debug_streamlit.py llm`
- **Workflow Errors**: Enable debug mode in Streamlit for detailed error info
- **Performance Issues**: Check debug logs for timing information

## Configuration

### Environment Variables

Required for full functionality:
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API key
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI endpoint
- `AZURE_DALL_E_3_API_KEY`: DALL-E 3 API key (for image generation)
- `AZURE_DALL_E_3_ENDPOINT`: DALL-E 3 endpoint
- `PROD_TAVILY_API_KEY`: Tavily search API key

### Workflow Configuration

```python
@dataclass
class WorkflowConfig:
    enable_logging: bool = True
    timeout_seconds: Optional[int] = None
    retry_attempts: int = 3
    editor_style: str = "General"
    enable_image_generation: bool = True
```

## Dependencies

- **streamlit**: Web interface
- **langgraph**: Workflow orchestration
- **langchain**: LLM integration
- **langchain-openai**: OpenAI integration
- **langchain-ollama**: Local LLM support
- **openai**: OpenAI API client
- **requests**: HTTP requests
- **pydantic**: Data validation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]
