import streamlit as st
from datetime import datetime
from fpdf import FPDF
import io
import re
import os
import pandas as pd
from collections import Counter
import folium
from streamlit_folium import st_folium
from gemini_helper import get_gemini_response  # Only this function is used

# --- Remove emojis and non-latin1 characters for PDF ---
def remove_non_latin1(text):
    return re.sub(r'[^\x00-\xFF]', '', text)

# --- Generate PDF Report ---
def generate_chat_pdf(chat_history):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "HealthBot - Chat Report", ln=True, align="C")
    pdf.ln(10)

    for chat in chat_history:
        time = chat.get("time", "")
        user = remove_non_latin1(chat.get("user", ""))
        bot = remove_non_latin1(chat.get("bot", ""))

        pdf.set_text_color(33, 150, 243)
        pdf.multi_cell(0, 10, f"You ({time}): {user}")
        pdf.ln(1)

        pdf.set_text_color(76, 175, 80)
        pdf.multi_cell(0, 10, f"HealthBot: {bot}")
        pdf.ln(5)

    buffer = io.BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- Extract Summary ---
def extract_health_summary(chat_history):
    causes = []
    care_tips = []
    for chat in chat_history:
        bot_response = chat.get("bot", "")
        cause_match = re.findall(r"🩺 Possible Causes:\n(.*?)\n💡", bot_response, re.DOTALL)
        tip_match = re.findall(r"💡 Self-Care Tips:\n(.*?)\n🚨", bot_response, re.DOTALL)
        if cause_match:
            causes.extend(re.split(r'\n|- ', cause_match[0].strip()))
        if tip_match:
            care_tips.extend(re.split(r'\n|- ', tip_match[0].strip()))
    causes = [c.strip() for c in causes if c.strip()]
    care_tips = [t.strip() for t in care_tips if t.strip()]
    return Counter(causes), Counter(care_tips)

# --- Detect symptoms and emergencies ---
def detect_symptoms(text):
    symptoms = ["fever", "cough", "rash", "headache", "dizziness", "nausea", "fatigue"]
    return [s for s in symptoms if s in text.lower()]

def check_emergency_keywords(text):
    emergencies = ["chest pain", "difficulty breathing", "seizure", "stroke", "heart attack", "loss of consciousness"]
    return any(word in text.lower() for word in emergencies)

# --- Enhance prompt for Gemini ---
def get_health_prompt(query, symptoms=None):
    symptom_str = ", ".join(symptoms) if symptoms else "None"
    return f"""
You are a virtual healthcare assistant powered by Gemini AI.

The user says: "{query}"
Detected symptoms: {symptom_str}

Based on their input:
- Identify possible non-serious causes
- Suggest self-care tips
- Advise when to see a doctor
- Do NOT provide emergency care instructions
- Always remind the user this is not a substitute for professional medical advice

Format:
🩺 Possible Causes:
💡 Self-Care Tips:
🚨 When to See a Doctor:
"""

# --- Save chat to CSV ---
def save_chat_to_csv(chat_history, filename="chat_logs.csv"):
    df = pd.DataFrame(chat_history)
    df.to_csv(filename, index=False, mode='a', header=not os.path.exists(filename))

# --- Function to create hospital map ---
def create_hospital_map(center_lat, center_lon):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=13)
    # For demo, add some fixed hospital locations near Ernakulam
    hospitals = [
        {"name": "Lakeshore Hospital", "lat": 9.9816, "lon": 76.2977},
        {"name": "Aster Medcity", "lat": 9.9963, "lon": 76.3171},
        {"name": "Medical Trust Hospital", "lat": 9.9675, "lon": 76.3000},
        {"name": "Rajagiri Hospital", "lat": 10.0104, "lon": 76.3051}
    ]
    for hosp in hospitals:
        folium.Marker(
            location=[hosp["lat"], hosp["lon"]],
            popup=hosp["name"],
            icon=folium.Icon(color='red', icon='plus-sign')
        ).add_to(m)
    return m

# --- Streamlit config ---
st.set_page_config(page_title="\U0001fa7a SymptoMate", layout="centered")
st.title("\U0001fa7a SymptoMate - A Smart Healtcare Chatbot")
st.caption("Describe your symptoms or ask any health-related question.")

st.markdown("\u26a0\ufe0f **Disclaimer:** This chatbot provides general health information and is not a substitute for professional medical advice, diagnosis, or treatment.")

# --- Session state ---
st.session_state.setdefault("chat_history", [])
st.session_state.setdefault("voice_input", "")
st.session_state.setdefault("recording", False)
st.session_state.setdefault("emergency_mode", False)

# --- Sidebar controls ---
with st.sidebar:
    st.header("⚙️ Settings")

    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.session_state.emergency_mode = False
        st.rerun()

    if st.session_state.chat_history:
        pdf_data = generate_chat_pdf(st.session_state.chat_history)
        st.download_button("📄 Download PDF Report", data=pdf_data, file_name="SymptoMate_Report.pdf", mime="application/pdf")

    if st.button("📊 Generate Health Summary"):
        causes_count, tips_count = extract_health_summary(st.session_state.chat_history)
        if not causes_count and not tips_count:
            st.warning("No sufficient data to generate a health summary.")
        else:
            st.subheader("📋 Health Insights Summary")
            if causes_count:
                st.markdown("**🧪 Frequent Possible Causes:**")
                for cause, freq in causes_count.most_common():
                    st.markdown(f"- {cause} ({freq} times)")
            if tips_count:
                st.markdown("**💡 Frequent Self-Care Tips:**")
                for tip, freq in tips_count.most_common():
                    st.markdown(f"- {tip} ({freq} times)")

    st.markdown("---")
    st.subheader("🎙️ Voice Input")
    col1, col2, col3 = st.columns(3)

    with col1:
        if not st.session_state.recording:
            if st.button("▶️ Start"):
                st.session_state.recording = True
                st.rerun()

    with col2:
        if st.session_state.recording:
            if st.button("⏹️ Stop"):
                import speech_recognition as sr
                try:
                    r = sr.Recognizer()
                    with sr.Microphone() as source:
                        st.info("Listening...")
                        audio = r.listen(source, timeout=5)
                        st.session_state.voice_input = r.recognize_google(audio)
                        st.success("Voice captured successfully.")
                except Exception as e:
                    st.error(f"Speech recognition failed: {e}")
                st.session_state.recording = False
                st.rerun()

    with col3:
        if st.button("🔁 Retry"):
            st.session_state.voice_input = ""
            st.session_state.recording = False
            st.rerun()

# --- Emergency UI & Map ---
if st.session_state.emergency_mode:
    st.markdown("""
        <style>
        body { background-color: #300000 !important; }
        </style>
        <div style='padding: 16px; background: red; color: white; font-size: 20px; border-radius: 8px; margin-bottom: 10px;'>
            🚨 <b>Emergency Alert:</b> Please call 112 or your local emergency service immediately.
        </div>
    """, unsafe_allow_html=True)

    # Center map on Ernakulam, Kerala by default
    center_lat, center_lon = 9.9816, 76.2999
    hospital_map = create_hospital_map(center_lat, center_lon)
    st.subheader("🧭 Nearby Hospitals")
    st_folium(hospital_map, width=700, height=450)

# --- Chat display ---
st.markdown("<div class='chat-scroll'>", unsafe_allow_html=True)
for chat in st.session_state.chat_history:
    time = chat.get("time", "")
    st.markdown(f"""
        <div class='chat-bubble user'>
            <img src="https://img.icons8.com/fluency/32/user-male-circle.png" class='avatar'/>
            <div><b>You <small>({time})</small>:</b><br>{chat['user']}</div>
        </div>
        <div class='chat-bubble bot'>
            <img src="https://img.icons8.com/fluency/32/bot.png" class='avatar'/>
            <div><b>HealthBot:</b><br>{chat['bot']}</div>
        </div>
    """, unsafe_allow_html=True)
st.markdown("<div id='end'></div></div>", unsafe_allow_html=True)

# --- Input form ---
st.markdown("<div class='input-wrapper'>", unsafe_allow_html=True)
with st.form("chat_form", clear_on_submit=False):
    default_val = st.session_state.pop("voice_input", "")
    user_input = st.text_area("Your message", value=default_val, placeholder="Describe your symptoms...", height=80, label_visibility="collapsed")
    send = st.form_submit_button("Send")

    if send and user_input.strip():
        symptoms = detect_symptoms(user_input)
        is_emergency = check_emergency_keywords(user_input)

        if is_emergency:
            st.session_state.emergency_mode = True

        reply = ("🚨 These symptoms may require immediate medical attention. Please call emergency services."
                 if is_emergency else get_gemini_response(get_health_prompt(user_input, symptoms)))

        chat_entry = {
            "user": user_input.strip(),
            "bot": reply.strip(),
            "time": datetime.now().strftime("%I:%M %p")
        }
        st.session_state.chat_history.append(chat_entry)

        save_chat_to_csv([{
            "user": chat_entry["user"],
            "bot": chat_entry["bot"],
            "time": datetime.now().strftime("%Y-%m-%d %I:%M %p")
        }])

        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

# --- CSS Styling ---
st.markdown("""
<style>
.chat-scroll {
    max-height: 65vh;
    overflow-y: auto;
    padding: 10px;
    margin-bottom: 120px;
}
.chat-bubble {
    display: flex;
    gap: 10px;
    margin-bottom: 15px;
}
.chat-bubble.user > div {
    background-color: #2a2a2a;
    color: #ffffff;
    border-radius: 10px;
    padding: 12px;
}
.chat-bubble.bot > div {
    background-color: #1e4620;
    color: #d7ffd9;
    border-radius: 10px;
    padding: 12px;
}
.avatar {
    width: 32px;
    height: 32px;
    margin-top: 4px;
}
.input-wrapper {
    position: fixed;
    bottom: 10px;
    left: 1.5rem;
    right: 1.5rem;
    background-color: #0e1117;
    padding: 12px;
    border-radius: 10px;
    z-index: 999;
    box-shadow: 0 0 10px #00000060;
}
textarea {
    background-color: #1e1e1e !important;
    color: #ffffff !important;
    border: 1px solid #333;
    border-radius: 8px !important;
    font-size: 16px;
}
button[kind="primary"] {
    background-color: #00897b !important;
    color: white !important;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- Auto-scroll ---
st.markdown("""
<script>
const chatEnd = document.getElementById("end");
if (chatEnd) chatEnd.scrollIntoView({ behavior: "smooth" });
</script>
""", unsafe_allow_html=True)
