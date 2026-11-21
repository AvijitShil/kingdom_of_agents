"""
OpenAI-Compatible FastAPI Server for Gemma 4 E4B on Intel Arc A380 (GPU.1)
Powered by OpenVINO GenAI VLMPipeline
"""

import os
import sys
import time
import uuid
import argparse
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import openvino_genai as ov_genai

DEFAULT_MODEL_DIR = os.path.expanduser(r"~\.cache\models\gemma-4-E4B-it-int4-ov")
DEFAULT_DEVICE = "GPU.1"  # Intel Arc A380 dGPU

app = FastAPI(title="Gemma 4 E4B OpenVINO GenAI Server", version="1.0.0")

pipeline = None
model_device = DEFAULT_DEVICE
model_dir_path = DEFAULT_MODEL_DIR


class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "gemma-4-e4b"
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=512, ge=1, le=4096)
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
    stream: Optional[bool] = False


class ChatChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str


class UsageInfo(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatChoice]
    usage: UsageInfo


def format_gemma_chat(messages: List[Message]) -> str:
    """Format standard OpenAI messages to Gemma turn structure."""
    prompt = ""
    for msg in messages:
        role = msg.role.lower()
        if role in ["system", "user"]:
            prompt += f"<start_of_turn>user\n{msg.content}<end_of_turn>\n"
        elif role in ["assistant", "model"]:
            prompt += f"<start_of_turn>model\n{msg.content}<end_of_turn>\n"
    prompt += "<start_of_turn>model\n"
    return prompt


@app.on_event("startup")
def load_model():
    global pipeline
    print(f"[*] Initializing OpenVINO VLMPipeline from {model_dir_path} on device {model_device}...")
    try:
        pipeline = ov_genai.VLMPipeline(model_dir_path, model_device)
        print(f"[+] Gemma 4 E4B successfully compiled and loaded on {model_device}!")
    except Exception as e:
        print(f"[-] Error loading VLMPipeline on {model_device}: {e}")
        print("[!] Attempting fallback or deferred init...")


@app.get("/health")
def health():
    return {
        "status": "healthy" if pipeline is not None else "degraded",
        "device": model_device,
        "model_dir": model_dir_path,
        "loaded": pipeline is not None
    }


@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "gemma-4-e4b",
                "object": "model",
                "created": int(time.time()),
                "owned_by": "openvino-intel-arc",
                "permission": [],
                "root": "gemma-4-e4b",
                "parent": None
            }
        ]
    }


@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
def create_chat_completion(request: ChatCompletionRequest):
    global pipeline
    if pipeline is None:
        try:
            print(f"[*] Lazy-loading VLMPipeline on {model_device}...")
            pipeline = ov_genai.VLMPipeline(model_dir_path, model_device)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model not initialized: {e}")

    prompt = format_gemma_chat(request.messages)

    config = ov_genai.GenerationConfig()
    config.max_new_tokens = request.max_tokens or 512
    config.temperature = request.temperature if request.temperature is not None else 0.7
    config.top_p = request.top_p if request.top_p is not None else 0.9

    start_time = time.time()
    try:
        raw_output = pipeline.generate(prompt, generation_config=config)
        response_text = str(raw_output).strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Inference error: {e}")

    duration = time.time() - start_time
    # Approximate token counts
    prompt_tokens = len(prompt.split())
    completion_tokens = len(response_text.split())
    total_tokens = prompt_tokens + completion_tokens

    return ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=request.model,
        choices=[
            ChatChoice(
                index=0,
                message=Message(role="assistant", content=response_text),
                finish_reason="stop"
            )
        ],
        usage=UsageInfo(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens
        )
    )


def start_server(host: str = "127.0.0.1", port: int = 8000, device: str = DEFAULT_DEVICE, model_dir: str = DEFAULT_MODEL_DIR):
    global model_device, model_dir_path
    model_device = device
    model_dir_path = model_dir
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="OpenVINO Gemma 4 E4B Server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--model-dir", default=DEFAULT_MODEL_DIR)
    args = parser.parse_args()

    start_server(host=args.host, port=args.port, device=args.device, model_dir=args.model_dir)
