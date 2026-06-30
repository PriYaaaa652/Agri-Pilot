import os
import sys
from pydantic import BaseModel, Field
from google.adk.agents import Agent
from google.adk.models import Gemini
from google.genai import types
from google.adk.tools import McpToolset
from mcp import StdioServerParameters
from app.config import config

# Output Schema
class WeatherAgentOutput(BaseModel):
    response: str = Field(description="The local weather forecast and agricultural action warnings.")
    confidence: float = Field(description="Confidence rating of this weather forecast between 0.0 and 1.0.")

# Setup MCP Toolset path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mcp_server_path = os.path.join(current_dir, "mcp", "mcp_server.py")

weather_agent_mcp = McpToolset(
    connection_params=StdioServerParameters(
        command=sys.executable,
        args=[mcp_server_path]
    ),
    tool_filter=["get_weather_alert"]
)

weather_agent = Agent(
    name="weather_agent",
    description="Fetches and analyzes local agricultural weather alerts and schedules.",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(initial_delay=2, attempts=3),
    ),
    instruction=(
        "You are an agricultural weather assistant.\n"
        "Your task is to fetch weather warnings and forecasts for the farmer's location.\n"
        "Use the `get_weather_alert` tool to check for active safety alerts (e.g. heatwaves, flash floods, storms).\n"
        "Formulate your response and estimate your confidence level based on current alert warnings."
    ),
    tools=[weather_agent_mcp],
    output_schema=WeatherAgentOutput,
)
