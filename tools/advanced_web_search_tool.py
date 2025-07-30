from langchain_tavily import TavilySearch
from tools.tool_secrets import PROD_TAVILY_API_KEY
from typing import List, Optional
from datetime import datetime


def get_search_tools():
    """Get optimized search tools for different use cases"""
    # Default tool for general viral content discovery
    tavily_search_tool = _get_tavily_search_tool()

    # Specialized tools for different trending content types
    viral_social_tool = _get_viral_search_tool("social")
    trending_news_tool = _get_viral_search_tool("news")
    tech_trends_tool = _get_viral_search_tool("tech")
    finance_trends_tool = _get_viral_search_tool("finance")
    celebrities_trends_tool = _get_viral_search_tool("celebrities")
    entertainment_trends_tool = _get_viral_search_tool("entertainment")

    tools = [tavily_search_tool, viral_social_tool, trending_news_tool, tech_trends_tool, finance_trends_tool,
             celebrities_trends_tool, entertainment_trends_tool]
    return tools


def _get_tavily_search_tool():
    """Optimized default search tool for viral and trending content"""
    return TavilySearch(
        max_results=10,  # Reduced from 20 for efficiency
        tavily_api_key=PROD_TAVILY_API_KEY,
        search_depth="advanced",  # Changed from basic for better context
        description="Search the web for viral and trending topics. Optimized for real-time discovery of trending content, viral stories, and emerging topics with time-sensitive filtering.",
        include_images=True,  # Visual content crucial for viral trends
        include_answer=True,  # Get direct answers for trending topics
        time_range="day",  # Focus on most recent viral content
        topic="general"  # Best for discovering diverse trending topics
    )


def _get_viral_search_tool(
        trend_focus: str = "general",
        max_results: int = 10,
        time_sensitivity: str = "day"
):
    """
    Specialized Tavily search tool for different types of viral content

    Args:
        trend_focus: "general", "news", "social", "tech", "finance"
        max_results: Number of results (5-15 recommended for efficiency)
        time_sensitivity: "day", "week", "month"
    """

    # Base configuration optimized for viral content
    config = {
        "max_results": max_results,
        "tavily_api_key": PROD_TAVILY_API_KEY,
        "search_depth": "advanced",
        "include_images": True,
        "include_answer": True,
        "time_range": time_sensitivity,
    }

    # Trend-specific optimizations
    trend_configs = {
        "social": {
            "include_domains": ["tiktok.com", "instagram.com", "youtube.com", "twitter.com", "reddit.com"],
            "description": "Discover viral social media trends, trending hashtags, and viral social content from major platforms"
        },
        "news": {
            "topic": "news",
            "time_range": "day",
            "description": "Find breaking news, viral news stories, and trending current events"
        },
        "tech": {
            "include_domains": ["techcrunch.com", "theverge.com", "reddit.com", "hackernews.com"],
            "description": "Track viral tech trends, product launches, and trending technology discussions"
        },
        "finance": {
            "topic": "finance",
            "include_domains": ["bloomberg.com", "reuters.com", "reddit.com"],
            "description": "Find trending financial news, viral market movements, and trending investment topics"
        },
        "celebrities": {
            "include_domains": ["tmz.com", "people.com", "eonline.com", "usmagazine.com", "extratv.com",
                                "instagram.com", "twitter.com", "reddit.com"],
            "time_range": "day",
            "description": "Track celebrity news, viral celebrity moments, trending celebrity gossip, and celebrity social media activity"
        },
        "entertainment": {
            "include_domains": ["variety.com", "hollywoodreporter.com", "deadline.com", "ew.com", "imdb.com",
                                "youtube.com", "netflix.com", "reddit.com"],
            "time_range": "day",
            "description": "Discover trending entertainment news, viral movie/TV content, music trends, streaming hits, and entertainment industry buzz"
        },
        "general": {
            "topic": "general",
            "description": "Search for viral content and trending topics across all categories"
        }
    }

    config.update(trend_configs.get(trend_focus, trend_configs["general"]))

    return TavilySearch(**config)


def enhance_viral_query(base_query: str) -> str:
    """Enhance queries specifically for viral content discovery"""
    viral_keywords = ["trending", "viral", "popular", "breaking", "hot"]
    current_year = str(datetime.now().year)

    # Add viral context if not present
    if not any(keyword in base_query.lower() for keyword in viral_keywords):
        enhanced_query = f"{base_query} trending viral {current_year}"
    else:
        enhanced_query = f"{base_query} {current_year}"

    return enhanced_query


def search_trending_batch(topics: List[str], trend_type: str = "general", time_filter: str = "day"):
    """Efficiently search multiple trending topics"""
    tavily_tool = _get_viral_search_tool(trend_type, time_sensitivity=time_filter)

    # Optimize queries for trending content
    results = []
    for topic in topics:
        enhanced_query = enhance_viral_query(topic)

        try:
            result = tavily_tool.search(query=enhanced_query)
            results.append({
                "topic": topic,
                "enhanced_query": enhanced_query,
                "results": result
            })
        except Exception as e:
            results.append({
                "topic": topic,
                "enhanced_query": enhanced_query,
                "error": str(e)
            })

    return results


# Alternative streamlined version if you prefer to keep it simple
def _get_optimized_tavily_search_tool():
    """Single optimized tool with all viral content enhancements"""
    return TavilySearch(
        max_results=10,
        tavily_api_key=PROD_TAVILY_API_KEY,
        search_depth="advanced",
        description="Search the web for viral and trending topics. Optimized for discovering trending content, viral stories, breaking news, and emerging topics with real-time filtering.",
        include_images=True,
        include_answer=True,
        time_range="day",
        topic="general"
    )
