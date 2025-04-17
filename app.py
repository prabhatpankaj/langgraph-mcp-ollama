from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils import format_agent_response

app = FastAPI()
model = ChatOllama(model="llama3.2")

class QueryRequest(BaseModel):
    query: str

async def process_query(query: str):
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
        tools = client.get_tools()

        # ✅ Use ReAct-style agent from LangGraph
        agent = create_react_agent(model, tools)

        # Run the agent directly
        result = await agent.ainvoke({"messages": query})
        return format_agent_response(result)

@app.post("/query")
async def handle_post_query(request: QueryRequest):
    response = await process_query(request.query)
    return JSONResponse(content=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
