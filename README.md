# 🩺 SymptoMate - A Smart HealthCare Chatbot

**SymptoMate** is a smart virtual healthcare assistant built using **Streamlit** and powered by **Gemini AI**. It provides symptom checking, self-care guidance, emergency detection, and inline maps to nearby hospitals — all in a clean, interactive interface.

---

## 🚀 Features

- 🤖 AI-powered chat (Gemini)
- 🎙️ Voice input
- 📄 PDF export of chat history (without Unicode issues)
- 📊 Health summary of causes & tips
- 🚨 Emergency detection
- 🧭 Inline hospital map using `folium` + `streamlit_folium`
- 📁 CSV logging of chat history

---

## 🛠️ Tech Stack

- `Streamlit` for UI
- `Gemini` (via helper module) for AI responses
- `SpeechRecognition` for voice input
- `fpdf` for PDF generation
- `folium` & `streamlit_folium` for interactive maps
- `pandas` for data loggin

---

## 📦 Installation

1. **Clone the repo:**

```bash
git clone https://github.com/your-username/healthbot-streamlit.git
cd healthbot-streamlit
