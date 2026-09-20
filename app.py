import os
import pandas as pd
import gradio as gr
from dotenv import load_dotenv

from weather_service import get_full_weather_report
from agent import (
    generate_farming_advisory,
    search_agricultural_info,
    validate_groq_api_key,
    validate_tavily_api_key,
    get_groq_key,
    get_tavily_key
)

load_dotenv()

# Global state memory for weather report object
current_weather_state = {}

# Custom CSS for modern emerald / dark agricultural theme
CUSTOM_CSS = """
/* AgriSense Modern Aesthetic */
.container {
    max-width: 1200px;
    margin: 0 auto;
}
.header-box {
    background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%);
    color: white;
    padding: 24px;
    border-radius: 16px;
    margin-bottom: 20px;
    box-shadow: 0 10px 25px -5px rgba(5, 150, 105, 0.3);
    text-align: center;
}
.header-box h1 {
    font-size: 2.2rem;
    font-weight: 800;
    margin-bottom: 6px;
    letter-spacing: -0.5px;
    color: #ffffff !important;
}
.header-box p {
    font-size: 1.05rem;
    opacity: 0.95;
    margin: 0;
    color: #e6f4ea !important;
}
.weather-card {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}
.metric-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-right: 8px;
    margin-bottom: 8px;
}
.badge-success { background-color: #065f46; color: #a7f3d0; }
.badge-warning { background-color: #854d0e; color: #fef08a; }
.badge-danger { background-color: #991b1b; color: #fecaca; }

.quick-btn button {
    background-color: #1f2937 !important;
    border: 1px solid #374151 !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
    font-size: 0.9rem !important;
    transition: all 0.2s ease;
}
.quick-btn button:hover {
    background-color: #059669 !important;
    color: white !important;
    border-color: #10b981 !important;
}
"""

def fetch_and_render_weather(location_query: str):
    """
    Fetches weather data and generates both HTML summary card and structured dataframe.
    """
    global current_weather_state
    if not location_query or not location_query.strip():
        return (
            "<div style='padding:15px; background:#1f2937; border-radius:10px; color:#f3f4f6;'>"
            "⚠️ Please enter a valid location (e.g., 'Punjab, India' or 'Iowa, USA').</div>",
            pd.DataFrame(),
            "⚠️ Location query was empty."
        )

    success, msg, data = get_full_weather_report(location_query)
    if not success:
        current_weather_state = {}
        return (
            f"<div style='padding:15px; background:#7f1d1d; border-radius:10px; color:#fecaca;'>❌ {msg}</div>",
            pd.DataFrame(),
            msg
        )

    current_weather_state = data
    risks = data.get("agri_risks", {})
    
    # Render rich HTML card
    html_card = f"""
    <div style="background: linear-gradient(135deg, #111827 0%, #1f2937 100%); border: 1px solid #059669; border-radius: 14px; padding: 20px; color: white; margin-bottom: 12px;">
        <div style="display: flex; justify-subspace: space-between; align-items: center; border-bottom: 1px solid #374151; padding-bottom: 12px; margin-bottom: 12px;">
            <div>
                <h3 style="margin: 0; color: #34d399; font-size: 1.4rem;">📍 {data['location']}</h3>
                <span style="font-size: 0.9rem; color: #9ca3af;">{data['weather_condition']} — {data['weather_advice']}</span>
            </div>
            <div style="text-align: right;">
                <span style="font-size: 2.2rem; font-weight: 800; color: #f3f4f6;">{data['temp']}°C</span>
                <div style="font-size: 0.8rem; color: #9ca3af;">Feels like: {data['feels_like']}°C</div>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 14px;">
            <div style="background: #1f2937; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 0.8rem; color: #9ca3af;">Humidity</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #60a5fa;">💧 {data['humidity']}%</div>
            </div>
            <div style="background: #1f2937; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 0.8rem; color: #9ca3af;">Wind Speed</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #f59e0b;">💨 {data['wind_speed']} km/h</div>
            </div>
            <div style="background: #1f2937; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 0.8rem; color: #9ca3af;">Rain Chance</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #38bdf8;">🌧️ {data['rain_probability']}%</div>
            </div>
            <div style="background: #1f2937; padding: 10px; border-radius: 8px; text-align: center;">
                <div style="font-size: 0.8rem; color: #9ca3af;">Irrigation Index</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #a7f3d0;">{risks.get('irrigation_score')}%</div>
            </div>
        </div>

        <div style="border-top: 1px dashed #374151; padding-top: 10px; font-size: 0.9rem;">
            <div style="margin-bottom: 6px;">💧 <b>Irrigation Recommendation:</b> {risks.get('irrigation_status')}</div>
            <div style="margin-bottom: 6px;">🚜 <b>Chemical Spraying Window:</b> {risks.get('spray_status')}</div>
            <div style="margin-bottom: 6px;">🦠 <b>Pest & Fungal Risk:</b> {risks.get('pest_risk')}</div>
            <div>⚠️ <b>Hazards:</b> {', '.join(risks.get('thermal_hazards', []))}</div>
        </div>
    </div>
    """

    df_forecast = pd.DataFrame(data.get("forecast", []))
    status_summary = f"Successfully fetched weather for {data['location']}."
    return html_card, df_forecast, status_summary


def handle_user_chat(
    user_message: str,
    history: list,
    location_input: str,
    crop_type: str,
    soil_type: str,
    growth_stage: str,
    use_tavily: bool,
    model_name: str,
    groq_key_input: str,
    tavily_key_input: str
):
    """
    Handles streaming chat output for the advisory chatbot.
    """
    global current_weather_state
    
    if not user_message or not user_message.strip():
        yield history, ""
        return

    # Automatically fetch weather if location input provided but state is empty
    if not current_weather_state and location_input:
        get_full_weather_report(location_input)

    crop_info = {
        "crop": crop_type,
        "soil": soil_type,
        "stage": growth_stage
    }

    # Format history for agent pipeline
    chat_history_list = []
    if history:
        for item in history:
            if isinstance(item, dict):
                chat_history_list.append(item)
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                chat_history_list.append({"role": "user", "content": item[0]})
                chat_history_list.append({"role": "assistant", "content": item[1]})

    # Append user question and empty assistant placeholder to UI history
    new_history = history.copy() if history else []
    new_history.append({"role": "user", "content": user_message})
    new_history.append({"role": "assistant", "content": ""})

    # Stream agent response
    generator = generate_farming_advisory(
        user_query=user_message,
        chat_history=chat_history_list,
        weather_info=current_weather_state,
        crop_info=crop_info,
        groq_key=groq_key_input,
        tavily_key=tavily_key_input,
        model_name=model_name,
        use_tavily_search=use_tavily
    )

    for partial_resp in generator:
        new_history[-1] = {"role": "assistant", "content": partial_resp}
        yield new_history, ""


def save_env_keys(groq_k: str, tavily_k: str):
    """Saves API keys to local .env file."""
    try:
        content = f"GROQ_API_KEY={groq_k.strip()}\nTAVILY_API_KEY={tavily_k.strip()}\n"
        with open(".env", "w") as f:
            f.write(content)
        return "✅ Saved API Keys successfully to `.env` file!"
    except Exception as e:
        return f"❌ Failed to write `.env` file: {str(e)}"


def execute_tavily_direct_search(query: str, tavily_k: str):
    """Executes search for Tab 3."""
    if not query or not query.strip():
        return "Please enter a search query."
    success, md_result, _ = search_agricultural_info(query, tavily_key=tavily_k)
    return md_result


# Build Gradio Blocks Application
with gr.Blocks(title="AgriSense AI - Weather-Based Farming Advisory Agent") as demo:
    
    # Application Header
    gr.HTML("""
    <div class="header-box">
        <h1>🌾 AgriSense AI</h1>
        <p>Weather-Based Farming Advisory & Climate-Smart Agricultural Intelligence Agent</p>
    </div>
    """)

    # Main Tabs
    with gr.Tabs():
        
        # TAB 1: ADVISORY & CHAT ASSISTANT
        with gr.TabItem("🌾 Advisory & Chat Assistant"):
            with gr.Row():
                # Left Panel: Weather & Crop Inputs
                with gr.Column(scale=4):
                    gr.Markdown("### 🌤️ Weather & Location Setup")
                    location_input = gr.Textbox(
                        label="Farm Location / City",
                        placeholder="e.g., Punjab, India or Des Moines, Iowa",
                        value="Punjab, India"
                    )
                    fetch_weather_btn = gr.Button("🌦️ Fetch Live Weather Data", variant="primary")
                    
                    weather_card_html = gr.HTML(
                        value="<div style='padding:15px; background:#1f2937; border-radius:10px; color:#9ca3af;'>Click 'Fetch Live Weather Data' to load local meteorological insights.</div>"
                    )

                    gr.Markdown("### 🌱 Crop & Soil Profile")
                    crop_type_input = gr.Dropdown(
                        choices=["Wheat", "Rice / Paddy", "Corn / Maize", "Cotton", "Tomato", "Potato", "Soybean", "Sugarcane", "Citrus", "General Crop"],
                        value="Wheat",
                        label="Crop Type"
                    )
                    soil_type_input = gr.Dropdown(
                        choices=["Alluvial / Loam", "Clay Soil", "Sandy Loam", "Black Soil (Regur)", "Red / Laterite Soil"],
                        value="Alluvial / Loam",
                        label="Soil Type"
                    )
                    growth_stage_input = gr.Dropdown(
                        choices=["Germination & Seedling", "Vegetative Growth", "Flowering & Pollination", "Fruit/Grain Formation", "Harvesting Stage"],
                        value="Vegetative Growth",
                        label="Current Growth Stage"
                    )

                    gr.Markdown("### ⚙️ Agent Controls")
                    use_tavily_chk = gr.Checkbox(label="🔍 Enable Tavily Web Search for real-time news & disease info", value=True)
                    model_selector = gr.Dropdown(
                        choices=["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b", "groq/compound"],
                        value="openai/gpt-oss-120b",
                        label="Groq AI Model"
                    )

                # Right Panel: Interactive Chatbot
                with gr.Column(scale=6):
                    gr.Markdown("### 💬 Ask AgriSense AI Agronomist")
                    
                    chatbot = gr.Chatbot(
                        label="Farming Advisory Conversation",
                        height=480
                    )
                    
                    user_msg_input = gr.Textbox(
                        label="Ask a Question",
                        placeholder="e.g., Is it safe to apply fertilizer today given the humidity and rain chance?",
                        lines=2
                    )

                    with gr.Row():
                        submit_btn = gr.Button("🚀 Send Question", variant="primary")
                        clear_btn = gr.Button("🗑️ Clear Chat")

                    gr.Markdown("#### 💡 Quick Consultation Questions:")
                    with gr.Row(elem_classes="quick-btn"):
                        q1_btn = gr.Button("💧 Is today safe for irrigation?")
                        q2_btn = gr.Button("🧪 Can I spray pesticide / fertilizer today?")
                    with gr.Row(elem_classes="quick-btn"):
                        q3_btn = gr.Button("🐛 What pest hazards exist for current humidity?")
                        q4_btn = gr.Button("📅 Give 7-day crop care schedule")

        # TAB 2: WEATHER & RISK DASHBOARD
        with gr.TabItem("📊 Weather & Risk Dashboard"):
            gr.Markdown("## 📊 Meteorological & Agricultural Risk Analysis")
            with gr.Row():
                dash_location_btn = gr.Button("🔄 Refresh Dashboard Data", variant="secondary")
            
            dashboard_status = gr.Markdown("Status: Ready")
            forecast_table = gr.Dataframe(label="7-Day Detailed Weather Forecast")

        # TAB 3: TAVILY AGRI-SEARCH ENGINE
        with gr.TabItem("🔎 Tavily Agri-Search Engine"):
            gr.Markdown("## 🔎 Real-Time Agricultural Web Search")
            gr.Markdown("Search for recent crop diseases, market prices, extension advisories, or government farming schemes using **Tavily Search API**.")
            
            with gr.Row():
                tavily_query_box = gr.Textbox(
                    label="Agricultural Search Query",
                    placeholder="e.g. Wheat rust disease outbreak management guidelines 2026",
                    scale=4
                )
                tavily_search_btn = gr.Button("🔎 Search Web", variant="primary", scale=1)

            tavily_output_md = gr.Markdown("Search results will appear here...")

        # TAB 4: SETTINGS & API CONFIG
        with gr.TabItem("⚙️ Settings & API Config"):
            gr.Markdown("## ⚙️ API Configuration & Key Management")
            gr.Markdown(
                "Provide your **Groq** and **Tavily** API keys below. "
                "Keys are automatically read from your environment `.env` file if present."
            )
            
            initial_groq_key = get_groq_key()
            initial_tavily_key = get_tavily_key()

            with gr.Row():
                groq_key_field = gr.Textbox(
                    label="Groq API Key",
                    placeholder="gsk_...",
                    value=initial_groq_key,
                    type="password",
                    scale=3
                )
                test_groq_btn = gr.Button("🧪 Test Groq Key", scale=1)

            groq_status_output = gr.Markdown(value="Key not tested yet." if not initial_groq_key else "Key loaded from environment.")

            with gr.Row():
                tavily_key_field = gr.Textbox(
                    label="Tavily API Key",
                    placeholder="tvly-...",
                    value=initial_tavily_key,
                    type="password",
                    scale=3
                )
                test_tavily_btn = gr.Button("🧪 Test Tavily Key", scale=1)

            tavily_status_output = gr.Markdown(value="Key not tested yet." if not initial_tavily_key else "Key loaded from environment.")

            save_keys_btn = gr.Button("💾 Save Keys to `.env` File", variant="primary")
            save_status_output = gr.Markdown()

    # --- EVENT BINDINGS & HANDLERS ---
    
    # 1. Weather Fetch Binding
    fetch_weather_btn.click(
        fn=fetch_and_render_weather,
        inputs=[location_input],
        outputs=[weather_card_html, forecast_table, dashboard_status]
    )

    dash_location_btn.click(
        fn=fetch_and_render_weather,
        inputs=[location_input],
        outputs=[weather_card_html, forecast_table, dashboard_status]
    )

    # 2. Chat Submit Handler
    submit_btn.click(
        fn=handle_user_chat,
        inputs=[
            user_msg_input, chatbot, location_input, crop_type_input,
            soil_type_input, growth_stage_input, use_tavily_chk,
            model_selector, groq_key_field, tavily_key_field
        ],
        outputs=[chatbot, user_msg_input]
    )

    user_msg_input.submit(
        fn=handle_user_chat,
        inputs=[
            user_msg_input, chatbot, location_input, crop_type_input,
            soil_type_input, growth_stage_input, use_tavily_chk,
            model_selector, groq_key_field, tavily_key_field
        ],
        outputs=[chatbot, user_msg_input]
    )

    clear_btn.click(lambda: [], None, chatbot)

    # 3. Quick Consultation Questions Handler
    def handle_q1(hist, loc, crop, soil, stage, tav, model, g_key, t_key):
        yield from handle_user_chat("Is today safe for irrigation given current weather?", hist, loc, crop, soil, stage, tav, model, g_key, t_key)

    def handle_q2(hist, loc, crop, soil, stage, tav, model, g_key, t_key):
        yield from handle_user_chat("Can I apply pesticide or fertilizer today? Check wind and rain window.", hist, loc, crop, soil, stage, tav, model, g_key, t_key)

    def handle_q3(hist, loc, crop, soil, stage, tav, model, g_key, t_key):
        yield from handle_user_chat("What fungal or insect pest risks exist for current humidity and temp?", hist, loc, crop, soil, stage, tav, model, g_key, t_key)

    def handle_q4(hist, loc, crop, soil, stage, tav, model, g_key, t_key):
        yield from handle_user_chat("Provide a 7-day farm operation plan based on upcoming forecast.", hist, loc, crop, soil, stage, tav, model, g_key, t_key)

    q1_btn.click(
        fn=handle_q1,
        inputs=[chatbot, location_input, crop_type_input, soil_type_input, growth_stage_input, use_tavily_chk, model_selector, groq_key_field, tavily_key_field],
        outputs=[chatbot, user_msg_input]
    )

    q2_btn.click(
        fn=handle_q2,
        inputs=[chatbot, location_input, crop_type_input, soil_type_input, growth_stage_input, use_tavily_chk, model_selector, groq_key_field, tavily_key_field],
        outputs=[chatbot, user_msg_input]
    )

    q3_btn.click(
        fn=handle_q3,
        inputs=[chatbot, location_input, crop_type_input, soil_type_input, growth_stage_input, use_tavily_chk, model_selector, groq_key_field, tavily_key_field],
        outputs=[chatbot, user_msg_input]
    )

    q4_btn.click(
        fn=handle_q4,
        inputs=[chatbot, location_input, crop_type_input, soil_type_input, growth_stage_input, use_tavily_chk, model_selector, groq_key_field, tavily_key_field],
        outputs=[chatbot, user_msg_input]
    )

    # 4. Tab 3 Tavily Direct Search Handler
    tavily_search_btn.click(
        fn=execute_tavily_direct_search,
        inputs=[tavily_query_box, tavily_key_field],
        outputs=[tavily_output_md]
    )

    # 5. Settings Handler
    test_groq_btn.click(
        fn=lambda key: validate_groq_api_key(key)[1],
        inputs=[groq_key_field],
        outputs=[groq_status_output]
    )

    test_tavily_btn.click(
        fn=lambda key: validate_tavily_api_key(key)[1],
        inputs=[tavily_key_field],
        outputs=[tavily_status_output]
    )

    save_keys_btn.click(
        fn=save_env_keys,
        inputs=[groq_key_field, tavily_key_field],
        outputs=[save_status_output]
    )

if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("PORT", "7860")),
        share=False,
        css=CUSTOM_CSS
    )
    