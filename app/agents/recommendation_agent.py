from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from app.config import config

# Sub-components of the structured recommendation
class ValueConfidence(BaseModel):
    value: str = Field(description="The analysis text from the specialized sub-agent.")
    confidence: float = Field(description="The certainty rating between 0.0 and 1.0.")

class ActionPlan(BaseModel):
    today: str = Field(description="Recommended tasks for today.")
    tomorrow: str = Field(description="Recommended tasks for tomorrow.")
    after_rain: str = Field(description="Recommended tasks after the next rainfall.")

# Main Structured Output Schema for Recommendation Agent
class RecommendationAgentOutput(BaseModel):
    diagnosis: ValueConfidence = Field(description="Crop health diagnosis and soil recommendation with confidence.")
    weather: ValueConfidence = Field(description="Weather forecast details and warnings with confidence.")
    market: ValueConfidence = Field(description="Crop pricing trends and sales suggestions with confidence.")
    decision_summary: list[str] = Field(description="Chronological key decision rationales explaining recommended actions.")
    action_plan: ActionPlan = Field(description="Concrete action plan timeline.")
    overall_confidence: float = Field(description="Synthesized confidence value calculated from all inputs.")

recommendation_agent = Agent(
    name="recommendation_agent",
    description="Compiles and structures reports into a strict structured agricultural recommendation JSON.",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(initial_delay=2, attempts=3),
    ),
    instruction=(
        "You are the master recommendation compiler.\n"
        "Your task is to synthesize the crop diagnosis, weather alerts, and market pricing inputs "
        "into a structured recommendation schema.\n"
        "Analyze the inputs and fill in the structured fields. Genuinely copy/derive the confidence scores "
        "from the sub-agent responses.\n"
        "Never fabricate a confidence value. Only use confidence scores actually returned by the crop_doctor, "
        "weather_agent, and market_agent sub-agent outputs. If a sub-agent's confidence is missing, use 0.0 and "
        "note this in decision_summary rather than guessing a number.\n"
        "If the review status notes that chemical fertilizer/pesticides were REJECTED, you MUST rewrite the "
        "recommendations to suggest only organic substitutes (e.g. compost, bio-pesticides) in the diagnosis, "
        "decision_summary, and action_plan."
    ),
    output_schema=RecommendationAgentOutput,
)
