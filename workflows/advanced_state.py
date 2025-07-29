from typing import TypedDict, Annotated, List

from langgraph.graph import add_messages


class AdvancedState(TypedDict):
    topic: str
    messages: Annotated[list, add_messages]
    trending_topics: List[dict]
