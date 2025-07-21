from langchain_tavily import TavilySearch

from tools.tool_secrets import PROD_TAVILY_API_KEY


def get_search_tools():
    tavily_search_tool = _get_tavily_search_tool()
    tools = [tavily_search_tool]
    return tools

def _get_tavily_search_tool():
    return TavilySearch(
        max_results=10,
        tavily_api_key=PROD_TAVILY_API_KEY,
        description="Search the web for current information about topics. Use this to gather comprehensive research data, recent developments, statistics, and factual information. Provide specific search queries to get the most relevant results."
    )
