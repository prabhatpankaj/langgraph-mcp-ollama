import json
from langgraph.graph import StateGraph, END
from states.tool_state import ToolGraphState

def build_tool_graph(model, tools):
    graph = StateGraph(ToolGraphState)

    async def llm_parser(state):
        prompt = (
            "You are a helpful assistant that extracts structured inputs for browser automation using Playwright.\n"
            "From the user query, extract:\n"
            "- `page_url`: full URL to open\n"
            "- `element_selector`: the visible text to click, if any\n"
            "- `extraction_target`: the kind of data to extract from the page after the click (e.g., 'car names', 'car specs', 'brand names')\n"
            "- `wants_console_logs`: true if user asks for browser logs\n"
            "- `wants_network_logs`: true if user wants network activity\n\n"
            "Respond in JSON only, like:\n"
            '{\n'
            '  "page_url": "https://example.com",\n'
            '  "element_selector": "View all 5 and below seater",\n'
            '  "extraction_target": "car names",\n'
            '  "wants_console_logs": false,\n'
            '  "wants_network_logs": false\n'
            '}\n\n'
            f"User query:\n{state['input_text']}"
        )

        response = await model.ainvoke(prompt)

        try:
            parsed = json.loads(response.content)
        except Exception:
            parsed = {}

        page_url = parsed.get("page_url", "").strip()
        element_selector = parsed.get("element_selector", "").strip()
        raw_target = parsed.get("extraction_target", "")
        if isinstance(raw_target, list):
            extraction_target = ", ".join(map(str, raw_target)).strip().lower()
        elif isinstance(raw_target, str):
            extraction_target = raw_target.strip().lower()
        else:
            extraction_target = ""

        # Optional fallback
        if not extraction_target and "car" in state["input_text"].lower():
            extraction_target = "car names and specs"

        return {
            "page_url": page_url,
            "element_selector": element_selector,
            "extraction_target": extraction_target,
            "wants_browser_open": bool(page_url),
            "wants_click_action": bool(page_url and element_selector),
            "wants_console_logs": parsed.get("wants_console_logs", False),
            "wants_network_logs": parsed.get("wants_network_logs", False),
        }

    def prep_inputs(state):
        return state

    async def get_page_title(state):
        tool = tools["open_page_and_get_title"]
        result = await tool.ainvoke({"url": state["page_url"]})
        return {"page_title": result}

    async def click_element(state):
        tool = tools["click_element_and_get_text"]
        selector = state["element_selector"]
        if selector.startswith("text="):
            selector = selector.replace("text=", "").strip()

        result = await tool.ainvoke({
            "url": state["page_url"],
            "selector": selector,
            "extraction_target": state.get("extraction_target", "")
        })
        return {"click_result": result}

    async def get_console_logs(state):
        tool = tools["get_console_logs"]
        result = await tool.ainvoke({"last_n": 5})
        return {"console_logs": result}

    async def get_network_requests(state):
        tool = tools["get_network_requests"]
        result = await tool.ainvoke({"last_n": 5})
        return {"network_requests": result}

    def combine_results(state):
        parts = []

        if state.get("page_title"):
            parts.append(f"Page title is: {state['page_title']}")

        if state.get("click_result"):
            try:
                data = json.loads(state["click_result"])
                extracted = data.get("extracted", [])
                if isinstance(extracted, list):
                    parts.append("Extracted Data:\n" + "\n".join(f"- {item}" for item in extracted))
                else:
                    parts.append(f"Extracted Result:\n{extracted}")
            except Exception:
                parts.append(f"Click result content:\n{state['click_result'][:300]}...")

        if state.get("console_logs"):
            logs = "\n".join(log["text"] for log in state["console_logs"])
            parts.append(f"Console Logs:\n{logs}")

        if state.get("network_requests"):
            reqs = "\n".join(req["url"] for req in state["network_requests"])
            parts.append(f"Network Requests:\n{reqs}")

        return {
            "final_answer": "\n\n".join(parts)
        }

    def end_node(state):
        return state

    def tool_router(state):
        next_nodes = []
        if state.get("wants_browser_open"):
            next_nodes.append("get_page_title")
        if state.get("wants_click_action"):
            next_nodes.append("click_element")
        if state.get("wants_console_logs"):
            next_nodes.append("get_console_logs")
        if state.get("wants_network_logs"):
            next_nodes.append("get_network_requests")

        print("[🧭 tool_router] Routing to:", next_nodes or ["combine_results"])
        return next_nodes or ["combine_results"]

    # Register
    graph.add_node("llm_parser", llm_parser)
    graph.add_node("prep_inputs", prep_inputs)
    graph.add_node("get_page_title", get_page_title)
    graph.add_node("click_element", click_element)
    graph.add_node("get_console_logs", get_console_logs)
    graph.add_node("get_network_requests", get_network_requests)
    graph.add_node("combine_results", combine_results)
    graph.add_node("end", end_node)

    graph.set_entry_point("llm_parser")
    graph.add_edge("llm_parser", "prep_inputs")
    graph.add_conditional_edges("prep_inputs", tool_router)
    graph.add_edge("get_page_title", "combine_results")
    graph.add_edge("click_element", "combine_results")
    graph.add_edge("get_console_logs", "combine_results")
    graph.add_edge("get_network_requests", "combine_results")
    graph.add_edge("combine_results", "end")
    graph.set_finish_point("end")
    return graph.compile()
