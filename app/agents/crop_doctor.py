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
class CropDoctorOutput(BaseModel):
    response: str = Field(description="The crop diagnosis and soil nutrition recommendation.")
    confidence: float = Field(description="Confidence rating of this crop advice between 0.0 and 1.0.")

# Setup MCP Toolset path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mcp_server_path = os.path.join(current_dir, "mcp", "mcp_server.py")

crop_doctor_mcp = McpToolset(
    connection_params=StdioServerParameters(
        command=sys.executable,
        args=[mcp_server_path]
    ),
    tool_filter=["get_soil_info"]
)

crop_doctor = Agent(
    name="crop_doctor",
    description="Diagnoses crop health and soil characteristics using soil databases.",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(initial_delay=2, attempts=3),
    ),
    instruction=(
        "You are an expert crop doctor and agronomist.\n"
        "Analyze the crop symptoms, pests, and soil type.\n"
        "Use the `get_soil_info` tool to get recommended parameters and nutritional advice.\n"
        "State your response and estimate your confidence level based on soil data compatibility."
    ),
    tools=[crop_doctor_mcp],
    output_schema=CropDoctorOutput,
)
