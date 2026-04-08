import json

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import config
from .creator import create_skill_streaming
from .providers import get_provider
from .skills import SkillLoader

app = FastAPI(title="CelebrAgents")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

skill_loader = SkillLoader()


@app.get("/api/skills")
def list_skills():
    return skill_loader.list_skills()


@app.post("/api/skills/reload")
def reload_skills():
    skill_loader.reload()
    return {"ok": True, "count": len(skill_loader.list_skills())}


@app.get("/api/providers")
def list_providers():
    return {
        "current": config.LLM_PROVIDER,
        "available": ["openai", "anthropic", "google"],
    }


@app.post("/api/chat")
async def chat(request: Request):
    body = await request.json()
    skill_id: str = body["skill_id"]
    messages: list[dict] = body["messages"]
    provider_name: str = body.get("provider", config.LLM_PROVIDER)

    skill = skill_loader.get_skill(skill_id)
    if skill is None:
        return {"error": f"Skill '{skill_id}' not found"}

    provider = get_provider(provider_name)

    async def generate():
        try:
            async for chunk in provider.stream_chat(skill.system_prompt, messages):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/api/skills/create")
async def create_skill(request: Request):
    body = await request.json()
    person_name: str = body["person_name"]
    extra_context: str = body.get("extra_context", "")
    provider_name: str = body.get("provider", config.LLM_PROVIDER)

    provider = get_provider(provider_name)

    async def generate():
        try:
            async for chunk in create_skill_streaming(
                provider, person_name, extra_context
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/skills/{skill_id}/assets/{filename}")
async def skill_asset(skill_id: str, filename: str):
    skills_dir = Path(__file__).parent / "skills" / skill_id / "assets"
    file_path = (skills_dir / filename).resolve()
    if not file_path.is_relative_to(skills_dir.resolve()) or not file_path.is_file():
        return {"error": "Not found"}
    return FileResponse(file_path)

frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
