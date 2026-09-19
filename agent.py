import os
from typing import Dict, Any, List, Tuple, Generator
from dotenv import load_dotenv

load_dotenv()

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None


def get_groq_key(custom_key: str = "") -> str:
    """Returns the custom key if provided, else falls back to environment variable."""
    return custom_key.strip() if custom_key.strip() else os.getenv("GROQ_API_KEY", "").strip()


def get_tavily_key(custom_key: str = "") -> str:
    """Returns the custom key if provided, else falls back to environment variable."""
    return custom_key.strip() if custom_key.strip() else os.getenv("TAVILY_API_KEY", "").strip()


def validate_groq_api_key(api_key: str) -> Tuple[bool, str]:
    """Tests if the Groq API key is valid."""
    key = get_groq_key(api_key)
    if not key:
        return False, "No Groq API Key provided or found in environment."
    
    if Groq is None:
        return False, "The `groq` python library is not installed."
        
    try:
        client = Groq(api_key=key)
        # Test a minimal completion query
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Ping"}],
            max_tokens=5
        )
        return True, "✅ Groq API Key is valid and working!"
    except Exception as e:
        return False, f"❌ Groq API Key Error: {str(e)}"


def validate_tavily_api_key(api_key: str) -> Tuple[bool, str]:
    """Tests if the Tavily API key is valid."""
    key = get_tavily_key(api_key)
    if not key:
        return False, "No Tavily API Key provided or found in environment."
        
    if TavilyClient is None:
        return False, "The `tavily-python` library is not installed."

    try:
        client = TavilyClient(api_key=key)
        res = client.search(query="crop farming news", max_results=1)
        return True, "✅ Tavily API Key is valid and working!"
    except Exception as e:
        return False, f"❌ Tavily API Key Error: {str(e)}"


def search_agricultural_info(query: str, tavily_key: str = "") -> Tuple[bool, str, List[Dict[str, Any]]]:
    """
    Executes a web search via Tavily for agricultural news/queries.
    Returns (success_flag, formatted_markdown, list_of_raw_results).
    """
    key = get_tavily_key(tavily_key)
    if not key:
        return False, "⚠️ Tavily API Key is missing. Enter your key in the **Settings** tab to enable web search.", []

    if TavilyClient is None:
        return False, "⚠️ Tavily Python package is not available.", []

    try:
        client = TavilyClient(api_key=key)
        response = client.search(query=f"farming agriculture advice {query}", search_depth="advanced", max_results=4)
        results = response.get("results", [])
        
        if not results:
            return True, "No specific web search results found for this query.", []

        formatted_md = "### 🔎 Real-Time Agricultural Web Search Insights (via Tavily)\n\n"
        for i, res in enumerate(results, 1):
            title = res.get("title", "No Title")
            url = res.get("url", "#")
            content = res.get("content", "No content snippet.")
            formatted_md += f"**{i}. [{title}]({url})**\n> {content}\n\n"
            
        return True, formatted_md, results
    except Exception as e:
        return False, f"⚠️ Tavily Search error: {str(e)}", []


def generate_farming_advisory(
    user_query: str,
    chat_history: List[Dict[str, str]],
    weather_info: Dict[str, Any],
    crop_info: Dict[str, str],
    groq_key: str = "",
    tavily_key: str = "",
    model_name: str = "openai/gpt-oss-120b",
    use_tavily_search: bool = True
) -> Generator[str, None, None]:
    """
    Core Advisory Agent pipeline.
    Combines Weather + Crop Context + Tavily Search (optional) + Groq LLM.
    Streams back the generated markdown advisory.
    """
    key = get_groq_key(groq_key)
    if not key:
        yield "⚠️ **Groq API Key Required**: Please provide a valid Groq API Key in the **Settings & API Config** tab to receive AI recommendations."
        return

    if Groq is None:
        yield "⚠️ **Library Error**: The `groq` library is not installed in the python environment."
        return

    # 1. Optionally trigger Tavily Search if enabled
    tavily_insights = ""
    if use_tavily_search:
        search_query = f"{crop_info.get('crop', 'crop')} {user_query}"
        success, search_md, _ = search_agricultural_info(search_query, tavily_key)
        if success and "Insights" in search_md:
            tavily_insights = search_md

    # 2. Construct System Prompt
    system_prompt = (
        "You are 'AgriSense AI', an expert Senior Agronomist, Climate-Smart Farming Consultant, "
        "and Plant Pathology Specialist. Your goal is to provide precise, scientifically sound, "
        "and actionable farming advice based on real-time weather data, soil conditions, and crop growth stage.\n\n"
        "GUIDELINES FOR YOUR RESPONSES:\n"
        "1. **Weather Integration**: Directly reference current weather metrics (temperature, humidity, wind, rain probability) to explain your recommendations.\n"
        "2. **Specific Action Plan**: Provide clear step-by-step guidance on Irrigation, Fertilizer application, Pesticide/Fungicide spraying windows, and Thermal/Cold risk mitigation.\n"
        "3. **Structured & Readable**: Use bolding, bullet points, headers, and relevant agricultural emojis (🌾, 💧, 🚜, 🐛, 🌤️, ⚠️).\n"
        "4. **Safety & Sustainability**: Recommend eco-friendly, IPM (Integrated Pest Management) practices where applicable.\n"
        "5. **Concise yet Comprehensive**: Be clear, direct, and pragmatic so farmers and farm managers can immediately take action."
    )

    # 3. Format Context
    weather_summary_text = "No location weather selected yet."
    if weather_info:
        risks = weather_info.get("agri_risks", {})
        weather_summary_text = (
            f"Location: {weather_info.get('location', 'Unknown')}\n"
            f"Current Temp: {weather_info.get('temp')}°C (Feels like: {weather_info.get('feels_like')}°C)\n"
            f"Humidity: {weather_info.get('humidity')}%\n"
            f"Wind Speed: {weather_info.get('wind_speed')} km/h\n"
            f"Condition: {weather_info.get('weather_condition')}\n"
            f"Rain Probability Today: {weather_info.get('rain_probability')}%\n"
            f"Irrigation Status: {risks.get('irrigation_status', 'N/A')}\n"
            f"Spraying Safety: {risks.get('spray_status', 'N/A')}\n"
            f"Pest/Fungal Risk: {risks.get('pest_risk', 'N/A')}\n"
            f"Hazards: {', '.join(risks.get('thermal_hazards', []))}"
        )

    crop_context_text = (
        f"Crop Type: {crop_info.get('crop', 'General Crops')}\n"
        f"Soil Type: {crop_info.get('soil', 'Loam / General')}\n"
        f"Growth Stage: {crop_info.get('stage', 'Vegetative / Growth')}"
    )

    context_prompt = (
        f"=== CURRENT LIVE METEOROLOGICAL DATA ===\n{weather_summary_text}\n\n"
        f"=== FARM / CROP PROFILE ===\n{crop_context_text}\n\n"
    )
    
    if tavily_insights:
        context_prompt += f"=== REAL-TIME WEB SEARCH INSIGHTS (TAVILY) ===\n{tavily_insights}\n\n"

    # Assemble messages
    messages = [{"role": "system", "content": system_prompt}]
    
    # Append limited chat history for context continuity
    for msg in chat_history[-6:]:
        role = "user" if msg.get("role") == "user" or msg.get("from") == "user" else "assistant"
        content = msg.get("content", "") or msg.get("text", "")
        if content:
            messages.append({"role": role, "content": content})

    # Combine context with user's new query
    final_user_content = f"{context_prompt}=== FARMER / USER QUESTION ===\n{user_query}"
    messages.append({"role": "user", "content": final_user_content})

    try:
        client = Groq(api_key=key)
        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.6,
            max_tokens=1500,
            stream=True
        )

        full_response = ""
        for chunk in completion:
            content = chunk.choices[0].delta.content or ""
            full_response += content
            yield full_response

    except Exception as e:
        yield f"❌ **Error communicating with Groq AI**: {str(e)}\n\nPlease check your API key and model selection."
