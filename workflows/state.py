from typing import TypedDict, Annotated, Optional

from langgraph.graph import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]
    topic: str  # ✅ Flows from user → researcher → writer
    research_summary: Optional[str]  # ✅ Flows from researcher → writer
    article_draft: Optional[str]  # ✅ Flows from writer → editor
    edited_article: Optional[str]  # ✅ Final output from editor