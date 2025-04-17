def format_agent_response(res):
    tool_outputs = {}
    final_answer = None

    for msg in res["messages"]:
        if msg.__class__.__name__ == "ToolMessage":
            tool_outputs[msg.name] = msg.content
        elif msg.__class__.__name__ == "AIMessage":
            if msg.content.strip():
                final_answer = msg.content

    return {
        "final_answer": final_answer,
        "tool_outputs": tool_outputs
    }
