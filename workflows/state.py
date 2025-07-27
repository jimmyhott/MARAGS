from typing import TypedDict, Annotated, Optional, List, Dict, Any

from langgraph.graph import add_messages


class State(TypedDict):
    topic: str  # ✅ Flows from user → researcher → writer
    word_count: int
    messages: Annotated[list, add_messages]
    research_summary: Optional[str]  # ✅ Flows from researcher → writer
    article_draft: Optional[str]  # ✅ Flows from writer → editor
    edited_article: Optional[str]  # ✅ Final output from editor
    generated_images: Optional[List[Dict[str, Any]]]  # Generated images
