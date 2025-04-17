from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils import format_agent_response
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI()

model = ChatOllama(model="llama3.2")

# Pydantic schema for request body
class QueryRequest(BaseModel):
    query: str

async def process_query(message: str):
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
        agent = create_react_agent(model, client.get_tools())
        res = await agent.ainvoke({"messages": message})
        return format_agent_response(res)

@app.post("/query")
async def handle_post_query(request: QueryRequest):
    response = await process_query(request.query)
    return JSONResponse(content=response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
