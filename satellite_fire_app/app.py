import streamlit as st
import json
import os
import random
from datetime import datetime
import folium
from streamlit_folium import st_folium

# ---- Session Setup ----
if "has_detected_once" not in st.session_state:
    st.session_state["has_detected_once"] = False
if "last_district" not in st.session_state:
    st.session_state["last_district"] = None
if "last_confidence" not in st.session_state:
    st.session_state["last_confidence"] = None
if "last_aqi" not in st.session_state:
    st.session_state["last_aqi"] = None
if "show_history" not in st.session_state:
    st.session_state["show_history"] = False

# ---- Fake AI confidence scorer ----
def ai_confidence(is_fire: bool) -> float:
    return round(random.uniform(0.86, 0.97), 2) if is_fire else round(random.uniform(0.15, 0.35), 2)

# ---- Fake AQI generator ----
def get_fake_aqi(is_fire: bool) -> int:
    return random.randint(180, 350) if is_fire else random.randint(40, 120)

# ---- Log alerts ----
def log_alert(district, time, conf):
    with open("alerts_log.txt", "a") as f:
        f.write(f"{time} - Fire in {district} (confidence: {conf * 100:.0f}%)\n")

# ---- Load fire data ----
with open("data/punjab_fire_data.json") as f:
    fire_data = json.load(f)

# ---- UI ----
st.title("🔥 Satellite-based Stubble Fire Detection System")
st.caption("A GIS + AI prototype for monitoring crop residue burning in Punjab")

districts = list(fire_data.keys())
selected = st.selectbox("Select District:", districts)

result = fire_data[selected]

# Auto update confidence and AQI when district changes
if st.session_state["last_district"] != selected:
    st.session_state["last_district"] = selected
    if st.session_state["has_detected_once"]:
        st.session_state["last_confidence"] = ai_confidence(result["fire_detected"])
        st.session_state["last_aqi"] = get_fake_aqi(result["fire_detected"])

# ---- Button Block ----
colA, colB = st.columns(2)
with colA:
    if st.button("Check Fire Activity"):
        st.session_state["has_detected_once"] = True

        # Real time timestamp update
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result["timestamp"] = now

        # Recalculate confidence & aqi
        st.session_state["last_confidence"] = ai_confidence(result["fire_detected"])
        st.session_state["last_aqi"] = get_fake_aqi(result["fire_detected"])

        log_alert(selected, now, st.session_state["last_confidence"])
with colB:
    if st.button("📜 View Alert History"):
        st.session_state["show_history"] = True

# ---- Show confidence & AQI only after first activation ----
if st.session_state["has_detected_once"]:
    st.metric("AI Confidence", f"{int(st.session_state['last_confidence'] * 100)}%")
    aqi_val = st.session_state["last_aqi"]
    aqi_status = "Hazardous" if aqi_val > 250 else "Moderate" if aqi_val > 150 else "Healthy"
    st.write(f"🌫️ Estimated AQI: {aqi_val} — {aqi_status}")

# ---- Fire detection block ----
if st.session_state["has_detected_once"]:
    if result["fire_detected"]:
        st.error(f"🔥 Fire detected in **{selected}**")
        st.write(f"🕒 Time: {result['timestamp']} | 📍 {result['location']}")
        st.progress(int(st.session_state["last_confidence"] * 100))

        m = folium.Map(location=[result["lat"], result["lon"]], zoom_start=8)
        folium.Marker(
            [result["lat"], result["lon"]],
            popup=f"🔥 Fire in {selected}",
            icon=folium.Icon(color="red")
        ).add_to(m)
        st_folium(m, width=700, height=400)

        if os.path.exists("data/demo_fire.jpg"):
            st.image("data/demo_fire.jpg", caption="🔥 Hotspot Detected (Demo)", width=420)

        st.success("🚨 Alert queued to authority dashboard (demo)")
    else:
        st.success(f"✅ No fire detected in **{selected}**")
        st.write(f"🕒 Last scan: {result['timestamp']}")

        if os.path.exists("data/punjab_map.jpg"):
            st.image("data/punjab_map.jpg", caption="🟩 No active hotspots (Demo)", width=420)

# ---- Alert history block ----
if st.session_state["show_history"]:
    if os.path.exists("alerts_log.txt"):
        with open("alerts_log.txt", "r") as f:
            logs = f.read().strip()
        st.code(logs or "No alerts logged yet.", language="text")
    else:
        st.info("No alert log yet. Run a detection first.")
