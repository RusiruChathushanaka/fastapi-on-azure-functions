import os
import azure.functions as func
import fastapi
from openai import OpenAI
from pydantic import BaseModel
from typing import List

app = fastapi.FastAPI()

_openai_client: OpenAI | None = None

def get_openai_client() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
        api_key = os.environ["AZURE_OPENAI_API_KEY"]
        _openai_client = OpenAI(base_url=endpoint, api_key=api_key)
    return _openai_client


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]


class ChatResponse(BaseModel):
    role: str
    content: str


@app.get("/sample")
async def index():
    return {
        "info": "Try /hello/Shivani for parameterized route.",
    }


@app.get("/hello/{name}")
async def get_name(name: str):
    return {
        "name": name,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-5.4-nano")
    client = get_openai_client()

    completion = client.chat.completions.create(
        model=deployment,
        messages=[{"role": m.role, "content": m.content} for m in request.messages],
    )

    message = completion.choices[0].message
    return ChatResponse(role=message.role, content=message.content)
