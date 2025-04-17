from typing import TypedDict, Optional

class ToolGraphState(TypedDict):
    input_text: str
    text_to_reverse: Optional[str]
    target_date: Optional[str]
    reversed_text: Optional[str]
    days_remaining: Optional[int]
    current_time: Optional[str]
    final_answer: Optional[str]
    wants_reversal: Optional[bool]
    wants_countdown: Optional[bool]
    wants_datetime: Optional[bool]
