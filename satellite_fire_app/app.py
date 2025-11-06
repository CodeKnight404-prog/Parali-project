import streamlit as st
import json
import os
import random
from datetime import datetime
import folium
from streamlit_folium import st_folium

# ---------------- Session State ----------------
if "has_detected_once" not in st.session_state:
    st.session_state["has_detected_once"] = False
if "last_district" not in st.session_state:
    st.session_state["last_district"] = None
if "last_confidence" not in st.session_state:
    st.session_state["last_confidence"] = None
if "last_aqi" not in st.session_state:
    st.session_state["last_aqi"] = None
if "last_timestamp" not in st.session_state:
    st.session_state["last_timestamp"] = None
if "last_fire_flag" not in st.session_state:
    st.session_state["last_fire_flag"] = None
if "show_history" not in st.session_state:
    st.session_state["show_history"] = False

# ---------------- Helpers ----------------
def ai_confidence(is_fire: bool) -> float:
    return round(random.uniform(0.86, 0.97), 2) if is_fire else round(random.uniform(0.15, 0.35), 2)

def get_fake_aqi(is_fire: bool) -> int:
    return random.randint(180, 350) if is_fire else random.randint(40, 120)

def log_alert(district, time_str, conf):
    with open("alerts_log.txt", "a") as f:
        f.write(f"{time_str} - Fire in {district} (confidence: {int(conf*100)}%)\n")

def log_emergency(district, time_str, conf, aqi):
    with open("emergency_log.txt", "a") as f:
        f.write(f"{time_str} - EMERGENCY sent for {district} | conf={int(conf*100)}% | AQI={aqi}\n")

def aqi_label(aqi_val: int) -> str:
    if aqi_val > 300: return "Severe"
    if aqi_val > 250: return "Hazardous"
    if aqi_val > 150: return "Moderate"
    if aqi_val > 100: return "Unhealthy (Sensitive)"
    return "Healthy"

# ---------------- Load Data ----------------
with open("data/punjab_fire_data.json") as f:
    fire_data = json.load(f)

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header("ℹ️ About")
    st.write("**Satellite-based Stubble Fire Detection** prototype")
    st.markdown(
        "- 🔥 District-wise detection\n"
        "- 🧠 AI confidence + simulated AQI\n"
        "- 🌍 Interactive GIS map\n"
        "- 🚨 Emergency alert logging"
    )
    st.divider()
    st.caption("Prototype for demo/education. Data is simulated.")

# ---------------- Main UI ----------------
st.title("🔥 Satellite-based Stubble Fire Detection System")
st.caption("GIS + AI dashboard for crop-residue burning (Punjab)")

districts = list(fire_data.keys())
selected = st.selectbox("Select District:", districts)
result = fire_data[selected]

# Update state when district changes
if st.session_state["last_district"] != selected:
    st.session_state["last_district"] = selected
    if st.session_state["has_detected_once"]:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["last_timestamp"] = now
        st.session_state["last_fire_flag"] = result["fire_detected"]
        st.session_state["last_confidence"] = ai_confidence(result["fire_detected"])
        st.session_state["last_aqi"] = get_fake_aqi(result["fire_detected"])

# ---------------- Top Summary ----------------
card_aqi = (
    st.session_state["last_aqi"]
    if st.session_state["last_aqi"] is not None
    else (280 if result["fire_detected"] else 85)
)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📍 District", selected)
with col2:
    st.metric("🔥 Fire Detected", "Yes" if result["fire_detected"] else "No")
with col3:
    st.metric("🌫️ Avg AQI (est.)", f"{card_aqi} ({aqi_label(card_aqi)})")

# ---------------- Actions ----------------
colA, colB, colC = st.columns(3)
with colA:
    if st.button("Check Fire Activity"):
        with st.spinner("Analyzing latest satellite pass…"):
            st.session_state["has_detected_once"] = True
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state["last_timestamp"] = now
            st.session_state["last_fire_flag"] = result["fire_detected"]
            st.session_state["last_confidence"] = ai_confidence(result["fire_detected"])
            st.session_state["last_aqi"] = get_fake_aqi(result["fire_detected"])
            log_alert(selected, now, st.session_state["last_confidence"])

with colB:
    if st.button("📜 View Alert History"):
        st.session_state["show_history"] = True

with colC:
    emergency_enabled = st.session_state["has_detected_once"]
    if st.button("🚨 Notify Authorities", disabled=not emergency_enabled):
        if emergency_enabled:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            conf = st.session_state["last_confidence"] or 0.90
            aqi_val = st.session_state["last_aqi"] or 260
            log_emergency(selected, now, conf, aqi_val)
            st.success("Emergency alert dispatched to district control room (demo).")
            st.balloons()

# ---------------- Detection & Details ----------------
if st.session_state["has_detected_once"]:
    conf = st.session_state["last_confidence"]
    aqi_val = st.session_state["last_aqi"]
    time_str = st.session_state["last_timestamp"]
    fire_flag = st.session_state["last_fire_flag"]

    st.metric("🧠 AI Confidence", f"{int(conf * 100)}%")
    st.write(f"⏱️ Last scan: {time_str}")
    st.write(f"🌫️ Estimated AQI: **{aqi_val}** — {aqi_label(aqi_val)}")

    if fire_flag:
        st.error(f"🔥 Fire detected in **{selected}**")
        st.write(f"📍 Coordinates: {result['lat']}, {result['lon']}")
        st.progress(int(conf * 100))

        m = folium.Map(location=[result["lat"], result["lon"]], zoom_start=8)
        folium.Marker(
            [result["lat"], result["lon"]],
            popup=f"🔥 Fire in {selected}",
            icon=folium.Icon(color="red"),
        ).add_to(m)
        st_folium(m, width=700, height=400)

        if os.path.exists("data/demo_fire.jpg"):
            st.image("data/demo_fire.jpg", caption="Infrared Hotspot (Demo)", width=420)
    else:
        st.success(f"✅ No fire detected in **{selected}**")
        if os.path.exists("data/punjab_map.jpg"):
            st.image("data/punjab_map.jpg", caption="No Active Hotspots (Demo)", width=420)

# ---------------- Logs Viewer ----------------
if st.session_state["show_history"]:
    st.subheader("🧾 Alert History")
    if os.path.exists("alerts_log.txt"):
        with open("alerts_log.txt", "r") as f:
            logs = f.read().strip()
        st.code(logs or "No alerts logged yet.", language="text")
    else:
        st.info("No alert log yet. Run a detection first.")
