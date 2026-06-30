import re
import json
import logging
from google.adk.workflow import node
from google.adk.agents.context import Context
from google.genai import types

# Set up logging for audit logging
logger = logging.getLogger("agripilot.security")

@node(name="security_checkpoint")
async def security_checkpoint(ctx: Context, node_input: str) -> str:
    """Security Checkpoint agent that validates and sanitizes input queries."""
    audit_log = {
        "session_id": ctx.session.id,
        "node": "security_checkpoint",
        "action": "input_validation",
    }
    
    # 1. PII Scrubbing: Redact latitude/longitude coordinates to protect farmer privacy
    scrubbed_input = node_input
    coord_patterns = [
        r"\b\d{1,3}\.\d+°?\s*[NS]?\s*,\s*\d{1,3}\.\d+°?\s*[EW]?\b",
        r"\b(latitude|longitude|lat|lon|coords?)\b\s*:\s*\d{1,3}\.\d+",
    ]
    for pattern in coord_patterns:
        scrubbed_input = re.sub(pattern, "[LOCATION_REDACTED]", scrubbed_input, flags=re.IGNORECASE)
        
    # 2. Prompt Injection Detection
    injection_keywords = ["ignore instructions", "ignore previous", "system prompt", "bypass", "override instructions"]
    injection_detected = False
    for kw in injection_keywords:
        if kw in node_input.lower():
            injection_detected = True
            break
            
    # 3. Domain-specific safety: Block banned chemicals (DDT, Paraquat, Endosulfan)
    banned_chemical_detected = False
    banned_chemicals = ["paraquat", "ddt", "endosulfan"]
    for chem in banned_chemicals:
        if chem in node_input.lower():
            banned_chemical_detected = True
            break
            
    if injection_detected:
        audit_log.update({
            "status": "REJECTED",
            "reason": "Prompt injection detected",
            "severity": "CRITICAL"
        })
        logger.warning(json.dumps(audit_log))
        ctx.route = "security_event"
        return "Prompt injection detected."
        
    if banned_chemical_detected:
        audit_log.update({
            "status": "REJECTED",
            "reason": "Banned chemical query",
            "severity": "WARNING"
        })
        logger.warning(json.dumps(audit_log))
        ctx.route = "security_event"
        return "Banned chemical detected."
        
    audit_log.update({
        "status": "APPROVED",
        "severity": "INFO",
        "scrubbed": scrubbed_input != node_input
    })
    logger.info(json.dumps(audit_log))
    
    ctx.state["clean_query"] = scrubbed_input
    ctx.route = "orchestrator"
    return scrubbed_input

@node(name="security_event")
async def security_event(ctx: Context, node_input: str) -> str:
    """Fallback node returned when security_checkpoint fails."""
    return (
        "Security Alert: Your query has been flagged by AgriPilot's security system. "
        "We cannot fulfill this request because it either violates prompt policies "
        "or references banned/restricted agricultural substances."
    )
