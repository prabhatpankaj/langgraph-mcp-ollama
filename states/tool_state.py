from typing import TypedDict, Optional, List, Dict

class ToolGraphState(TypedDict):
    input_text: str
    page_url: Optional[str]
    element_selector: Optional[str]
    extraction_target: Optional[str]
    page_title: Optional[str]
    click_result: Optional[str]
    console_logs: Optional[List[Dict]]
    network_requests: Optional[List[Dict]]
    final_answer: Optional[str]
    wants_browser_open: Optional[bool]
    wants_click_action: Optional[bool]
    wants_console_logs: Optional[bool]
    wants_network_logs: Optional[bool]
