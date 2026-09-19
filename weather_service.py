import requests
from typing import Dict, Any, Tuple, Optional

# Weather Code Mapping based on WMO Weather interpretation codes (WW)
WEATHER_CODES = {
    0: ("☀️ Clear Sky", "Optimal sunlight for photosynthesis."),
    1: ("🌤️ Mainly Clear", "Favorable conditions for field work."),
    2: ("⛅ Partly Cloudy", "Good balance of sun and shade."),
    3: ("☁️ Overcast", "Limited direct sunlight, monitor crop transpiration."),
    45: ("🌫️ Fog", "High moisture content in surface air. Watch for fungal pathogens."),
    48: ("🌫️ Depositing Rime Fog", "High surface humidity with freezing fog risk."),
    51: ("🌦️ Light Drizzle", "Slight moisture boost, low erosion risk."),
    53: ("🌦️ Moderate Drizzle", "Slight rain benefit, hold off on immediate spraying."),
    55: ("🌧️ Dense Drizzle", "Moist leaves, hold off on pesticide applications."),
    61: ("🌧️ Slight Rain", "Good natural irrigation for shallow crops."),
    63: ("🌧️ Moderate Rain", "Beneficial soil moisture recharge."),
    65: ("⛈️ Heavy Rain", "High run-off and erosion risk. Delay field machinery operations."),
    71: ("🌨️ Slight Snow", "Cold protection needed for frost-sensitive plants."),
    73: ("🌨️ Moderate Snow", "Snow blanket covers ground."),
    75: ("🌨️ Heavy Snow", "Severe cold cover, risk of frost damage."),
    80: ("🌧️ Rain Showers", "Intermittent rainfall, plan outdoor tasks carefully."),
    81: ("🌧️ Moderate Rain Showers", "Field mudding risk."),
    82: ("⛈️ Violent Rain Showers", "High deluge risk. Risk of waterlogging."),
    95: ("🌩️ Thunderstorm", "Avoid open fields. High lightning and wind hazard."),
    96: ("🌩️ Thunderstorm with Slight Hail", "Risk of leaf tearing and fruit drop."),
    99: ("🌩️ Thunderstorm with Heavy Hail", "Severe crop damage risk. Prepare protective netting if possible.")
}

def get_coordinates(location_name: str) -> Optional[Tuple[float, float, str, str]]:
    """
    Geocodes a location string using Open-Meteo Geocoding API.
    Returns (latitude, longitude, formatted_name, country).
    """
    try:
        url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {"name": location_name, "count": 1, "language": "en", "format": "json"}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get("results"):
            res = data["results"][0]
            lat = res["latitude"]
            lon = res["longitude"]
            name = res.get("name", location_name)
            country = res.get("country", "")
            admin1 = res.get("admin1", "")
            display_name = f"{name}{', ' + admin1 if admin1 else ''}{', ' + country if country else ''}"
            return lat, lon, display_name, country
        return None
    except Exception as e:
        print(f"Geocoding error: {e}")
        return None

def fetch_weather_data(lat: float, lon: float) -> Optional[Dict[str, Any]]:
    """
    Fetches current weather and 7-day forecast from Open-Meteo API.
    """
    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current": [
                "temperature_2m", "relative_humidity_2m", "apparent_temperature",
                "is_day", "precipitation", "rain", "showers", "weather_code",
                "cloud_cover", "surface_pressure", "wind_speed_10m", "wind_direction_10m"
            ],
            "daily": [
                "weather_code", "temperature_2m_max", "temperature_2m_min",
                "precipitation_sum", "rain_sum", "precipitation_probability_max",
                "wind_speed_10m_max"
            ],
            "timezone": "auto"
        }
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"Weather API error: {e}")
        return None

def compute_agri_risks(current: Dict[str, Any], daily: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculates agricultural indicators based on meteorological variables.
    """
    temp = current.get("temperature_2m", 20)
    humidity = current.get("relative_humidity_2m", 50)
    wind_speed = current.get("wind_speed_10m", 0)
    precip_prob = daily.get("precipitation_probability_max", [0])[0] if daily.get("precipitation_probability_max") else 0
    precip_sum = current.get("precipitation", 0)
    
    # 1. Irrigation Need Index (0 - 100%)
    # High temp + Low humidity + Low rain = High irrigation need
    irrigation_score = 50
    if temp > 30:
        irrigation_score += 25
    elif temp > 25:
        irrigation_score += 10
    
    if humidity < 40:
        irrigation_score += 25
    elif humidity < 60:
        irrigation_score += 10
        
    if precip_prob > 50 or precip_sum > 2.0:
        irrigation_score -= 40
    elif precip_prob > 20:
        irrigation_score -= 15
        
    irrigation_score = max(0, min(100, irrigation_score))
    
    if irrigation_score > 70:
        irrigation_status = "🔴 High Need (Irrigate Recommended)"
    elif irrigation_score > 40:
        irrigation_status = "🟡 Moderate Need (Monitor Soil)"
    else:
        irrigation_status = "🟢 Low Need (Sufficient Moisture / Rain Likely)"

    # 2. Chemical / Pesticide Spraying Safety Window
    # Wind > 20 km/h creates drift, Rain prob > 40% washes away chemicals
    if wind_speed > 20:
        spray_status = "❌ Unsafe (High Wind Drift > 20 km/h)"
        spray_badge = "Danger"
    elif precip_prob > 40:
        spray_status = "⚠️ Caution (High Rain Risk > 40%)"
        spray_badge = "Warning"
    elif humidity > 85:
        spray_status = "⚠️ Caution (Very High Humidity > 85%)"
        spray_badge = "Warning"
    else:
        spray_status = "✅ Favorable Spraying Window"
        spray_badge = "Success"

    # 3. Fungal / Pest Risk Index
    # Warm temperatures (20-30C) combined with high humidity (>75%) trigger fungal spores
    if 18 <= temp <= 32 and humidity >= 75:
        pest_risk = "🔴 High Risk (Warm & Humid - Fungal/Blight Threat)"
    elif humidity >= 65:
        pest_risk = "🟡 Moderate Risk (Watch for Rust/Aphids)"
    else:
        pest_risk = "🟢 Low Risk (Dry / Unfavorable for Spores)"

    # 4. Thermal Hazards (Frost & Heat Stress)
    temp_min_today = daily.get("temperature_2m_min", [temp])[0] if daily.get("temperature_2m_min") else temp
    temp_max_today = daily.get("temperature_2m_max", [temp])[0] if daily.get("temperature_2m_max") else temp

    thermal_hazards = []
    if temp_min_today <= 3.0:
        thermal_hazards.append("❄️ FROST ALERT: Cover sensitive saplings / run frost prevention.")
    if temp_max_today >= 36.0:
        thermal_hazards.append("🔥 HEAT STRESS ALERT: High heat evapotranspiration. Ensure hydration.")
    if wind_speed >= 35.0:
        thermal_hazards.append("💨 GALE/HIGH WIND WARNING: Secure greenhouse structures.")
    
    if not thermal_hazards:
        thermal_hazards.append("✅ No extreme temperature or wind hazards detected.")

    return {
        "irrigation_score": irrigation_score,
        "irrigation_status": irrigation_status,
        "spray_status": spray_status,
        "spray_badge": spray_badge,
        "pest_risk": pest_risk,
        "thermal_hazards": thermal_hazards
    }

def get_full_weather_report(location_query: str) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Main function to get formatted weather information for a location.
    Returns (success_flag, display_message, data_dict).
    """
    coords = get_coordinates(location_query)
    if not coords:
        return False, f"Could not find coordinates for location: '{location_query}'. Please check spelling.", {}

    lat, lon, display_name, country = coords
    raw_data = fetch_weather_data(lat, lon)
    if not raw_data:
        return False, f"Failed to retrieve weather data from Open-Meteo for {display_name}.", {}

    current = raw_data.get("current", {})
    daily = raw_data.get("daily", {})

    wcode = current.get("weather_code", 0)
    weather_desc, weather_advice = WEATHER_CODES.get(wcode, ("🌈 Variable Conditions", "Monitor local microclimate."))

    risks = compute_agri_risks(current, daily)

    # Format 7-Day Forecast Table
    forecast_days = []
    daily_dates = daily.get("time", [])
    max_temps = daily.get("temperature_2m_max", [])
    min_temps = daily.get("temperature_2m_min", [])
    precip_probs = daily.get("precipitation_probability_max", [])
    precip_sums = daily.get("precipitation_sum", [])
    wcodes = daily.get("weather_code", [])

    for i in range(min(len(daily_dates), 7)):
        date = daily_dates[i]
        t_max = max_temps[i] if i < len(max_temps) else "N/A"
        t_min = min_temps[i] if i < len(min_temps) else "N/A"
        p_prob = precip_probs[i] if i < len(precip_probs) else 0
        p_sum = precip_sums[i] if i < len(precip_sums) else 0
        code = wcodes[i] if i < len(wcodes) else 0
        desc, _ = WEATHER_CODES.get(code, ("Variable", ""))
        
        forecast_days.append({
            "Date": date,
            "Condition": desc,
            "Max Temp (°C)": f"{t_max}°C",
            "Min Temp (°C)": f"{t_min}°C",
            "Rain Prob (%)": f"{p_prob}%",
            "Rain (mm)": f"{p_sum} mm"
        })

    report_data = {
        "location": display_name,
        "lat": lat,
        "lon": lon,
        "temp": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind_speed": current.get("wind_speed_10m"),
        "weather_condition": weather_desc,
        "weather_advice": weather_advice,
        "precipitation_today": current.get("precipitation", 0),
        "rain_probability": precip_probs[0] if precip_probs else 0,
        "agri_risks": risks,
        "forecast": forecast_days
    }

    summary_text = (
        f"📍 Location: {display_name}\n"
        f"🌡️ Temperature: {report_data['temp']}°C (Feels like: {report_data['feels_like']}°C)\n"
        f"💧 Humidity: {report_data['humidity']}%\n"
        f"💨 Wind Speed: {report_data['wind_speed']} km/h\n"
        f"🌤️ Condition: {weather_desc}\n"
        f"🌧️ Rain Risk Today: {report_data['rain_probability']}%\n"
        f"💧 Irrigation Status: {risks['irrigation_status']}\n"
        f"🚜 Pesticide Spraying: {risks['spray_status']}\n"
        f"🦠 Pest & Fungal Risk: {risks['pest_risk']}"
    )

    return True, summary_text, report_data
