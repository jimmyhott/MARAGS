import logging
from langchain_core.tools import Tool
from langchain_tavily import TavilySearch

from tools.tool_secrets import PROD_TAVILY_API_KEY

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_search_tools():
    """Get all search tools including specialized ones for gossip and trending topics"""
    tools = [
        _get_basic_search_tool(),
        _get_gossip_search_tool(),
        _get_trending_topics_tool(),
        _get_viral_content_tool(),
        _get_social_buzz_tool()
    ]
    tools.append(_get_hot_topics_meta_tool(tools))  # Pass tools for reuse
    return tools


def _get_basic_search_tool():
    """Standard web search tool"""
    base_tool = TavilySearch(
        max_results=10,
        tavily_api_key=PROD_TAVILY_API_KEY,
        time_range="week",
        description="Search the web for current information about topics. Use this to gather comprehensive research data, recent developments, statistics, and factual information. Provide specific search queries to get the most relevant results."
    )

    def basic_search(query: str) -> dict:
        """Search for general information and recent developments"""
        try:
            results = base_tool.invoke({"query": f"{query} latest 2025"})
            if isinstance(results, list):
                formatted_results = [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")} for r in results]
            else:
                formatted_results = [{"content": str(results)}]
            return {"query": query, "results": formatted_results}
        except Exception as e:
            logger.error(f"Error with basic search query '{query}': {str(e)}")
            return {"query": query, "results": [], "message": "No results found."}

    return Tool(
        name="search_general_information",
        description="Search for general information, recent developments, and factual data across the web. Ideal for research and statistics.",
        func=basic_search
    )


def _get_gossip_search_tool():
    """Specialized tool for finding gossip and celebrity news"""
    base_tool = TavilySearch(
        max_results=15,
        tavily_api_key=PROD_TAVILY_API_KEY,
        include_domains=[
            "tmz.com",
            "pagesix.com",
            "eonline.com",
            "people.com",
            "usmagazine.com",
            "justjared.com",
            "dailymail.co.uk",
            "thesun.co.uk",
            "popsugar.com",
            "etonline.com",
            "radaronline.com",
            "perezhilton.com"
        ],
        time_range="week",
        search_depth="advanced"
    )

    def gossip_search(query: str) -> dict:
        """Search for gossip, celebrity news, and entertainment buzz"""
        enhanced_queries = [
            f"{query} scandal drama latest",
            f"{query} gossip rumors controversy",
            f"{query} breaking news exclusive",
            f"{query} shocking revelation leaked"
        ]

        all_results = []
        for enhanced_query in enhanced_queries[:2]:  # Limit to 2 to avoid rate limits
            try:
                results = base_tool.invoke({"query": enhanced_query})
                if isinstance(results, list):
                    formatted_results = [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")} for r in results]
                    all_results.extend([{"query": enhanced_query, "content": r} for r in formatted_results])
            except Exception as e:
                logger.error(f"Error with gossip query '{enhanced_query}': {str(e)}")
                continue

        return {"query": query, "results": all_results} if all_results else {"query": query, "results": [], "message": "No gossip found for this query."}

    return Tool(
        name="search_gossip_and_celebrity_news",
        description="Search for the latest celebrity gossip, entertainment news, scandals, and drama from major entertainment sources.",
        func=gossip_search
    )


def _get_trending_topics_tool():
    """Tool for finding what's trending and heated online"""
    base_tool = TavilySearch(
        max_results=20,
        tavily_api_key=PROD_TAVILY_API_KEY,
        time_range="week",
        include_domains=["news.google.com", "trends.google.com", "mashable.com", "vox.com", "cnn.com", "bbc.com"],
        search_depth="advanced"
    )

    def trending_search(query: str) -> dict:
        """Search for trending and heated topics"""
        trending_queries = [
            f"{query} trending viral last 7 days 2025",
            f"{query} heated debate controversy",
            f"{query} everyone talking about",
            f"{query} gone viral trending now",
            f"{query} social media buzz"
        ]

        all_results = []
        for trending_query in trending_queries[:3]:
            try:
                results = base_tool.invoke({"query": trending_query})
                if isinstance(results, list):
                    formatted_results = [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")} for r in results]
                    all_results.extend([{"query": trending_query, "content": r} for r in formatted_results])
            except Exception as e:
                logger.error(f"Error with trending query '{trending_query}': {str(e)}")
                continue

        return {"query": query, "results": all_results} if all_results else {"query": query, "results": [], "message": "No trending topics found."}

    return Tool(
        name="search_trending_heated_topics",
        description="Find what's currently trending, going viral, or causing heated debates online across news and trend aggregators.",
        func=trending_search
    )


def _get_viral_content_tool():
    """Tool specifically for viral content and internet phenomena"""
    base_tool = TavilySearch(
        max_results=15,
        tavily_api_key=PROD_TAVILY_API_KEY,
        time_range="week",
        include_domains=["buzzfeed.com", "knowyourmeme.com", "mashable.com", "popculture.com", "vox.com"],
        search_depth="advanced"
    )

    def viral_search(query: str) -> dict:
        """Search for viral videos, memes, and internet phenomena"""
        viral_queries = [
            f"{query} viral video meme",
            f"{query} internet breaking challenge",
            f"{query} everyone obsessed with",
            f"why is {query} trending"
        ]

        all_results = []
        for vq in viral_queries[:2]:
            try:
                results = base_tool.invoke({"query": vq})
                if isinstance(results, list):
                    formatted_results = [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")} for r in results]
                    all_results.extend([{"query": vq, "content": r} for r in formatted_results])
            except Exception as e:
                logger.error(f"Error with viral query '{vq}': {str(e)}")
                continue

        return {"query": query, "results": all_results} if all_results else {"query": query, "results": [], "message": "No viral content found."}

    return Tool(
        name="search_viral_content",
        description="Search for viral videos, memes, internet challenges, and trending content from aggregators and pop culture sites.",
        func=viral_search
    )


def _get_social_buzz_tool():
    """Tool for social media buzz and public opinion"""
    base_tool = TavilySearch(
        max_results=15,
        tavily_api_key=PROD_TAVILY_API_KEY,
        time_range="week",
        include_domains=["reddit.com", "mashable.com", "vox.com", "theguardian.com", "buzzfeed.com"],
        search_depth="advanced"
    )

    def social_buzz_search(query: str) -> dict:
        """Search for social media reactions and public discourse"""
        buzz_queries = [
            f"{query} social media reaction",
            f"{query} reddit discussion thread",
            f"{query} public opinion controversy",
            f"{query} hashtag movement",
            f"{query} online debate buzz"
        ]

        all_results = []
        for bq in buzz_queries[:3]:
            try:
                results = base_tool.invoke({"query": bq})
                if isinstance(results, list):
                    formatted_results = [{"title": r.get("title", ""), "url": r.get("url", ""), "content": r.get("content", "")} for r in results]
                    all_results.extend([{"query": bq, "content": r} for r in formatted_results])
            except Exception as e:
                logger.error(f"Error with social buzz query '{bq}': {str(e)}")
                continue

        return {"query": query, "results": all_results} if all_results else {"query": query, "results": [], "message": "No social buzz found."}

    return Tool(
        name="search_social_media_buzz",
        description="Search for social media reactions, public discourse, hashtag movements, and online discussions to understand public sentiment.",
        func=social_buzz_search
    )


def _get_hot_topics_meta_tool(tools):
    """Meta tool that uses all gossip and trending tools"""
    def search_all_hot_topics(query: str) -> dict:
        """Comprehensive search for all gossip, trending, and viral content"""
        all_results = []
        for tool in tools:
            try:
                result = tool.func(query)
                if result.get("results"):
                    all_results.append({"tool": tool.name, "results": result["results"]})
            except Exception as e:
                logger.error(f"Error with tool '{tool.name}' for query '{query}': {str(e)}")
                continue

        return {"query": query, "results": all_results} if all_results else {"query": query, "results": [], "message": "No hot topics found."}

    return Tool(
        name="search_all_hot_topics",
        description="Comprehensive search across all gossip, trending, viral, and social buzz sources for the complete picture of what's hot online.",
        func=search_all_hot_topics
    )