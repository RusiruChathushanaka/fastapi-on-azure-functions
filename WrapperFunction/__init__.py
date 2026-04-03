import os
import azure.functions as func
import fastapi
from openai import OpenAI
from pydantic import BaseModel, model_validator
from typing import List, Literal, Optional

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
    role: Literal["system", "assistant", "user", "tool", "developer"]
    content: str


class ChatRequest(BaseModel):
    messages: Optional[List[ChatMessage]] = None
    message: Optional[str] = None
    system_prompt: Optional[str] = None

    @model_validator(mode="after")
    def check_at_least_one(self) -> "ChatRequest":
        if not self.messages and not self.message:
            raise ValueError("Provide either 'message' (string) or 'messages' (list of role/content objects).")
        return self


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

    if request.message:
        messages = [{"role": "user", "content": request.message}]
    else:
        messages = [{"role": m.role, "content": m.content} for m in request.messages]

    if request.system_prompt:
        messages.insert(0, {"role": "system", "content": request.system_prompt})

    completion = client.chat.completions.create(
        model=deployment,
        messages=messages,
    )

    message = completion.choices[0].message
    return ChatResponse(role=message.role, content=message.content)

