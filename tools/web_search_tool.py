from langchain.tools import BaseTool
from typing import Optional, Type

class WebSearchTool(BaseTool):

    name = "web_search"
    description = (
        "Useful for when you need to answer questions by searching the web. "
        "Input should be a search query."
    )

    def __init__(self, search_client, **kwargs):
        """
        search_client: An object with a .search(query: str) -> str method.
        """
        super().__init__(**kwargs)
        self.search_client = search_client

    def _run(self, query: str) -> str:
        """
        Run a web search for the given query and return the results as a string.
        """
        try:
            results = self.search_client.search(query)
            return results
        except Exception as e:
            return f"Web search failed: {e}"

    async def _arun(self, query: str) -> str:
        """
        Asynchronous version of web search.
        """
        try:
            if hasattr(self.search_client, "asearch"):
                results = await self.search_client.asearch(query)
            else:
                # Fallback to sync if async not available
                results = self.search_client.search(query)
            return results
        except Exception as e:
            return f"Web search failed: {e}"
