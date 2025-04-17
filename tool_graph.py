import json
from langgraph.graph import StateGraph, END
from states.tool_state import ToolGraphState
from utils import clean_extracted_text, extract_date_fallback, extract_text_to_reverse

def build_tool_graph(model, tools):
    graph = StateGraph(ToolGraphState)

    # === Step 1: Parse user intent using LLM ===
    async def llm_parser(state):
        prompt = (
            "You are a helpful assistant that extracts inputs for tools.\n"
            "From the following user query, extract:\n"
            "- `text_to_reverse`: the string inside single or double quotes that should be reversed\n"
            "- `target_date`: the date mentioned for countdown in YYYY-MM-DD format\n\n"
            f"User query:\n{state['input_text']}\n\n"
            "Respond ONLY in JSON format like this:\n"
            '{\n  "text_to_reverse": "LangGraph rocks!",\n  "target_date": "2025-12-31" }\n\n'
            "Do not guess. If no date is found, leave it blank. If multiple dates, pick the most relevant one for countdown."
        )

        response = await model.ainvoke(prompt)

        try:
            parsed = json.loads(response.content)
        except Exception:
            parsed = {}

        # Fallbacks
        raw_text = parsed.get("text_to_reverse") or extract_text_to_reverse(state["input_text"])
        raw_date = parsed.get("target_date") or extract_date_fallback(state["input_text"])

        return {
            "text_to_reverse": clean_extracted_text(raw_text) if raw_text else "",
            "target_date": raw_date,
            "wants_reversal": bool(raw_text),
            "wants_countdown": bool(raw_date),
            "wants_datetime": any(
                x in state["input_text"].lower()
                for x in ["current date", "current time", "what time is it", "now"]
            ),
        }

    # === Step 2: Prep (barrier node) ===
    def prep_inputs(state):
        return state

    # === Step 3: Reverse string ===
    async def reverse_string(state):
        tool = tools["reverse_string"]
        result = await tool.ainvoke({"text": state["text_to_reverse"]})
        return {"reversed_text": result}

    # === Step 4: Days until target date ===
    async def days_until(state):
        tool = tools["days_until"]
        result = await tool.ainvoke({"date_str": state["target_date"]})
        return {"days_remaining": result}

    # === Step 5: Current datetime ===
    async def current_datetime(state):
        tool = tools["current_datetime"]
        result = await tool.ainvoke({})
        return {"current_time": result}

    # === Step 6: Combine final results ===
    def combine_results(state):
        parts = []

        if state.get("reversed_text"):
            parts.append(f"The reversed string is: {state['reversed_text']}")

        if state.get("days_remaining") is not None:
            date_label = state.get("target_date", "the date")
            parts.append(f"Days until {date_label}: {state['days_remaining']}")

        if state.get("current_time"):
            parts.append(f"Current date/time is: {state['current_time']}")

        return {
            "final_answer": "\n\n".join(parts)
        }

    # === Step 7: End node ===
    def end_node(state):
        return state

    # === Router based on extracted intent flags ===
    def tool_router(state):
        next_nodes = []
        if state.get("wants_reversal"):
            next_nodes.append("reverse_string")
        if state.get("wants_countdown"):
            next_nodes.append("days_until")
        if state.get("wants_datetime"):
            next_nodes.append("current_datetime")

        print("[🧭 tool_router] Routing to:", next_nodes or ["combine_results"])
        return next_nodes or ["combine_results"]

    # === Register Graph Nodes ===
    graph.add_node("llm_parser", llm_parser)
    graph.add_node("prep_inputs", prep_inputs)
    graph.add_node("reverse_string", reverse_string)
    graph.add_node("days_until", days_until)
    graph.add_node("current_datetime", current_datetime)
    graph.add_node("combine_results", combine_results)
    graph.add_node("end", end_node)

    # === Define Graph Flow ===
    graph.set_entry_point("llm_parser")
    graph.add_edge("llm_parser", "prep_inputs")
    graph.add_conditional_edges("prep_inputs", tool_router)

    graph.add_edge("reverse_string", "combine_results")
    graph.add_edge("days_until", "combine_results")
    graph.add_edge("current_datetime", "combine_results")
    graph.add_edge("combine_results", "end")

    graph.set_finish_point("end")
    return graph.compile()
