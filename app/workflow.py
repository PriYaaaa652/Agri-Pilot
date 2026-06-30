import logging
from typing import Any

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.tools import AgentTool
from google.adk.workflow import Workflow, Edge, START, node
from google.adk.events import Event, RequestInput
from google.adk.agents.context import Context

from app.config import config
from app.memory.session_memory import prefill_query_with_memory
from app.agents.security_agent import security_checkpoint, security_event
from app.agents.crop_doctor import crop_doctor
from app.agents.weather_agent import weather_agent
from app.agents.market_agent import market_agent
from app.agents.recommendation_agent import recommendation_agent
from app.skills.bangla_translation import bangla_translation

# Setup Orchestrator Agent with AgentTool delegation
crop_doctor_tool = AgentTool(agent=crop_doctor)
weather_agent_tool = AgentTool(agent=weather_agent)
market_agent_tool = AgentTool(agent=market_agent)

orchestrator = Agent(
    name="orchestrator",
    description="Orchestrates agricultural query analysis by delegating to specialized agents.",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(initial_delay=2, attempts=3),
    ),
    instruction=(
        "You are the AgriPilot Orchestrator.\n"
        "Your task is to analyze the user's query and query the specialized crop_doctor, weather_agent, and market_agent.\n"
        "Always call all relevant tools in parallel or sequence based on the context. "
        "Each tool will return a structured JSON response with a confidence score. "
        "Summarize their outputs and confidence scores into a single combined draft report."
    ),
    tools=[crop_doctor_tool, weather_agent_tool, market_agent_tool],
)

# Workflow Function Nodes

@node(name="memory_load_node")
async def memory_load_node(ctx: Context, node_input: str) -> str:
    """Memory loader node that reads session profile and injects stored context."""
    session_id = ctx.session.id
    prefilled_query, profile = prefill_query_with_memory(session_id, node_input)
    ctx.state["profile"] = profile
    return prefilled_query


@node(name="orchestrator_node", rerun_on_resume=True)
async def orchestrator_node(ctx: Context, node_input: str) -> str:
    """Orchestrator node executing the orchestrator agent and storing the draft plan."""
    draft_plan = await ctx.run_node(orchestrator, node_input=node_input)
    ctx.state["draft_plan"] = draft_plan
    return draft_plan


@node(name="human_review")
async def human_review(ctx: Context, node_input: str) -> Any:
    """Human Review node that intercepts chemical recommendations and triggers farmer confirmation."""
    draft_plan = ctx.state.get("draft_plan", "")
    
    # Check if a chemical treatment or pesticide is recommended
    requires_approval = False
    keywords = ["chemical fertilizer", "chemical nitrogen", "urea", "pesticide", "chemical n-p-k"]
    for kw in keywords:
        if kw in draft_plan.lower():
            requires_approval = True
            break
            
    if requires_approval:
        approval_id = "chemical_approval"
        if approval_id in ctx.resume_inputs:
            user_response = ctx.resume_inputs[approval_id]
            approved = False
            if isinstance(user_response, dict):
                approved = user_response.get("approved", False)
            elif isinstance(user_response, bool):
                approved = user_response
            elif isinstance(user_response, str):
                approved = "yes" in user_response.lower() or "approve" in user_response.lower()
                
            ctx.state["human_approved"] = approved
            if approved:
                ctx.state["human_review_status"] = "Approved by Farmer: Proceeding with recommendation."
            else:
                ctx.state["human_review_status"] = "Rejected by Farmer: Recommending organic alternatives instead."
            return ctx.state["human_review_status"]
        else:
            return RequestInput(
                interrupt_id=approval_id,
                message=(
                    "AgriPilot Alert: A chemical treatment was recommended in the draft plan. "
                    "Do you approve the use of chemical fertilizers/pesticides? (Type 'yes' to approve, or 'no' to reject)"
                )
            )
            
    ctx.state["human_review_status"] = "Auto-Approved: No restricted chemicals detected."
    return ctx.state["human_review_status"]


@node(name="recommendation_node", rerun_on_resume=True)
async def recommendation_node(ctx: Context, node_input: str) -> Any:
    """Recommendation node compiling final structured JSON output from inputs."""
    clean_query = ctx.state.get("clean_query", "")
    draft_plan = ctx.state.get("draft_plan", "")
    human_status = ctx.state.get("human_review_status", "")
    
    prompt = (
        f"Original Request: {clean_query}\n"
        f"Initial Draft Plan: {draft_plan}\n"
        f"Review Status: {human_status}\n\n"
        f"Compile the final structured AgriPilot Agricultural Report. "
        f"Ensure all fields in the output schema are filled. If the review status notes that chemical fertilizer/pesticides "
        f"were rejected, make sure you recommend ONLY organic alternatives in the fields."
    )
    return await ctx.run_node(recommendation_agent, node_input=prompt)


@node(name="memory_save_node")
async def memory_save_node(ctx: Context, node_input: Any) -> Any:
    """Persists updated session profile (including last_query_summary) 
    after the recommendation is generated."""
    from app.memory.session_memory import save_profile
    from pydantic import BaseModel
    session_id = ctx.session.id
    profile = ctx.state.get("profile", {})
    # Derive a short summary from the recommendation output for next-turn context
    if isinstance(node_input, BaseModel):
        summary_source = node_input.model_dump()
    elif isinstance(node_input, dict):
        summary_source = node_input
    else:
        summary_source = {}
    decision_summary = summary_source.get("decision_summary", [])
    profile["last_query_summary"] = " ".join(decision_summary[:2]) if decision_summary else ""
    save_profile(session_id, profile)
    return node_input  # pass the recommendation through unchanged


# 4. Workflow Graph definition
root_agent = Workflow(
    name="agripilot_workflow",
    edges=[
        Edge(from_node=START, to_node=memory_load_node),
        Edge(from_node=memory_load_node, to_node=security_checkpoint),
        Edge(from_node=security_checkpoint, to_node=orchestrator_node, route="orchestrator"),
        Edge(from_node=security_checkpoint, to_node=security_event, route="security_event"),
        Edge(from_node=orchestrator_node, to_node=human_review),
        Edge(from_node=human_review, to_node=recommendation_node),
        Edge(from_node=recommendation_node, to_node=memory_save_node),
        Edge(from_node=memory_save_node, to_node=bangla_translation),
    ]
)

app = App(
    root_agent=root_agent,
    name="app",
)
