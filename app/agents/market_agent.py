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
class MarketAgentOutput(BaseModel):
    response: str = Field(description="The crop market price, pricing trends, and trading strategy.")
    confidence: float = Field(description="Confidence rating of this market insight between 0.0 and 1.0.")

# Setup MCP Toolset path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
mcp_server_path = os.path.join(current_dir, "mcp", "mcp_server.py")

market_agent_mcp = McpToolset(
    connection_params=StdioServerParameters(
        command=sys.executable,
        args=[mcp_server_path]
    ),
    tool_filter=["get_crop_market_price"]
)

market_agent = Agent(
    name="market_agent",
    description="Analyzes agricultural commodity prices and advises on selling or holding crops.",
    model=Gemini(
        model=config.model,
        retry_options=types.HttpRetryOptions(initial_delay=2, attempts=3),
    ),
    instruction=(
        "You are an agricultural market analyst.\n"
        "Your task is to analyze price trends for the crop requested by the farmer.\n"
        "Use the `get_crop_market_price` tool to check wholesale prices and pricing trends.\n"
        "Advise whether to sell now or store the crop, along with your pricing confidence rating."
    ),
    tools=[market_agent_mcp],
    output_schema=MarketAgentOutput,
)
