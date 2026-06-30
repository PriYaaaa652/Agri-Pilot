from typing import Any
import json
from pydantic import BaseModel
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from google.adk.workflow import node
from google.adk.agents.context import Context
from app.config import config

translator_agent = Agent(
    name="translator_agent",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(initial_delay=2, attempts=3),
    ),
    instruction=(
        "You are an expert agricultural translator specialized in translating technical English reports into fluent, conversational Bangla.\n"
        "Your task is to take the structured JSON report and translate ONLY the human-readable values "
        "(specifically inside 'diagnosis', 'weather', 'market', 'decision_summary', and 'action_plan') into Bangla. "
        "Leave keys, confidence numbers, and numerical values untranslated. Keep the JSON layout clean.\n"
        "Output ONLY the translated Bangla text."
    )
)

@node(name="bangla_translation", rerun_on_resume=True)
async def bangla_translation(ctx: Context, node_input: Any) -> str:
    """Translation node that takes the English JSON report and outputs both English JSON and Bangla translation."""
    if isinstance(node_input, BaseModel):
        english_json_str = node_input.model_dump_json(indent=4)
    elif isinstance(node_input, dict):
        english_json_str = json.dumps(node_input, indent=4, ensure_ascii=False)
    else:
        english_json_str = str(node_input)
        
    # Query translator agent to get natural Bangla text
    bangla_report = await ctx.run_node(translator_agent, node_input=english_json_str)
    
    final_output = (
        "=== ENGLISH STRUCTURED JSON ===\n"
        f"{english_json_str}\n\n"
        "=== বাংলায় পরামর্শ (কৃষকের জন্য) ===\n"
        f"{bangla_report}"
    )
    return final_output
