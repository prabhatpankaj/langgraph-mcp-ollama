# app.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient
from tool_graph import build_tool_graph
from states.tool_state import ToolGraphState

app = FastAPI()
model = ChatOllama(model="llama3.2")

class QueryRequest(BaseModel):
    query: str

@app.post("/tools")
async def run_tools(request: QueryRequest):
    async with MultiServerMCPClient({
        "strings": {
            "command": "python",
            "args": ["tools/string_tools_server.py"],
            "transport": "stdio",
        },
        "datetime": {
            "command": "python",
            "args": ["tools/datetime_tools_server.py"],
            "transport": "stdio",
        }
    }) as client:
        tools = {t.name: t for t in client.get_tools()}
        graph = build_tool_graph(model, tools)
        result = await graph.ainvoke({"input_text": request.query})
        return JSONResponse(content=result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)