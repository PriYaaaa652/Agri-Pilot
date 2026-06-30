import os
import json

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_memory.json")

def load_profile(session_id: str) -> dict:
    """Loads session profile from JSON file."""
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get(session_id, {})
    except Exception:
        return {}

def save_profile(session_id: str, data: dict) -> None:
    """Saves session profile to JSON file."""
    all_data = {}
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                all_data = json.load(f)
        except Exception:
            all_data = {}
    all_data[session_id] = data
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(all_data, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def prefill_query_with_memory(session_id: str, current_query: str) -> tuple[str, dict]:
    """Prefills user query with stored crop and district context, updating the profile."""
    profile = load_profile(session_id)
    
    # Heuristic parsing for district
    districts = ["dhaka", "rajshahi", "sylhet", "chittagong"]
    for d in districts:
        if d in current_query.lower():
            profile["district"] = d.capitalize()
            
    # Heuristic parsing for crop type
    crops = ["rice", "wheat", "tomato", "tomatoes", "potato", "potatoes", "blueberry", "blueberries"]
    for c in crops:
        if c in current_query.lower():
            norm_crop = c
            if c in ["tomato", "tomatoes"]:
                norm_crop = "Tomatoes"
            elif c in ["potato", "potatoes"]:
                norm_crop = "Potatoes"
            elif c in ["blueberry", "blueberries"]:
                norm_crop = "Blueberries"
            else:
                norm_crop = c.capitalize()
            profile["crop_type"] = norm_crop

    if "language_preference" not in profile:
        profile["language_preference"] = "Bangla"
    if "last_query_summary" not in profile:
        profile["last_query_summary"] = ""

    # Prefill the query with context if available
    context_parts = []
    if "crop_type" in profile:
        context_parts.append(f"Crop: {profile['crop_type']}")
    if "district" in profile:
        context_parts.append(f"Location: {profile['district']}")
        
    prefilled_query = current_query
    if context_parts:
        context_str = ", ".join(context_parts)
        prefilled_query = f"[Session Context: {context_str}] {current_query}"
        
    save_profile(session_id, profile)
    return prefilled_query, profile
