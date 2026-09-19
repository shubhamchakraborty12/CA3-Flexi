# 🌾 AgriSense AI - Weather-Based Farming Advisory Agent

An intelligent, GUI-based **Weather-Based Farming Advisory Agent** built with **Gradio**, powered by **Groq AI** (`openai/gpt-oss-120b`), **Tavily Web Search API**, and real-time meteorological data from **Open-Meteo API**.

---

## 🌟 Features

- 🌤️ **Live Meteorological & Weather Forecast Integration**:
  - Global Geocoding for any farm location/city.
  - Real-time weather parameters: Temperature, Humidity, Wind Speed, Precipitation Probability.
  - 7-day weather forecast breakdown.
  - Agricultural Hazard Metrics: Irrigation Necessity Index, Pesticide Spraying Safety Window, Fungal & Insect Pest Risk, Frost & Heat Stress Warnings.

- 🧠 **Groq AI Agronomist Agent**:
  - High-speed AI inference using active Groq models (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`, `groq/compound`).
  - Tailored recommendations considering specific Crop Type, Soil Type, and Growth Stage.

- 🔎 **Tavily Web Search Integration**:
  - Live ground-truth search for real-time agricultural news, localized crop disease outbreaks, market price trends, and state extension advisories.

- 💻 **Interactive Gradio Dashboard**:
  - **Tab 1: 🌾 Advisory & Chat Assistant** — Interactive AI chat with live weather card, preset consultation questions, and crop profile setup.
  - **Tab 2: 📊 Weather & Risk Dashboard** — Meteorological metrics and 7-day forecast table.
  - **Tab 3: 🔎 Tavily Agri-Search Engine** — Dedicated search portal for agricultural web queries.
  - **Tab 4: ⚙️ Settings & API Config** — Input, test, and save Groq & Tavily API keys to `.env`.

---

## 📁 Project Structure

```
.
├── app.py                # Main Gradio GUI Application & Event Handlers
├── agent.py              # Groq AI & Tavily Search Integration Pipeline
├── weather_service.py    # Open-Meteo Geocoding, Forecast & Agricultural Risk Calculators
├── .env.example          # Sample API Key configuration template
├── README.md             # Project documentation
```

---

## 🚀 Quick Setup & Installation

### 1. Install Prerequisites
Ensure Python 3.10+ is installed. Install required packages:

```bash
pip install gradio groq tavily-python pandas requests python-dotenv
```

### 2. Configure API Keys
Copy `.env.example` to `.env` or enter your keys directly in the GUI **Settings** tab:

```env
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly-...
```

- Get free Groq API key: [https://console.groq.com](https://console.groq.com)
- Get free Tavily API key: [https://tavily.com](https://tavily.com)

### 3. Launch the Application

```bash
python app.py
```

Open your browser and navigate to `http://127.0.0.1:7860`.

---

## 🧪 Testing & Verification

1. **Weather Fetch Test**: Type `Punjab, India` or `Des Moines, Iowa` and click **Fetch Live Weather Data**. Verify temperature, humidity, rain chance, and risk gauges appear.
2. **AI Advisory Chat**: Ask `"Is today safe for applying pesticide?"` or click preset buttons.
3. **Tavily Search**: Enable web search toggle to get real-time online search insights embedded in the AI's advice.
