import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

import os

BACKEND_API_URL = os.getenv("BACKEND_API_URL")
API_CHAT_URL = f"{BACKEND_API_URL}/chat"
API_PATIENTS_URL = f"{BACKEND_API_URL}/patients"

st.set_page_config(page_title="Zero-Trust Clinical EHR", layout="centered")
st.title("🏥 Enterprise EHR Chat")
st.caption("Protected by Presidio Zero-Trust & NeMo Guardrails")


@st.cache_data(ttl=300)
def fetch_patient_list():

    try:
        response = requests.get(API_PATIENTS_URL)

        if response.status_code == 200:
            data = response.json() 
            return data.get("patients", ["No patients found"])

    except:
        return ["Database Connection Error"]

    return ["Unknown Error"]


patient_list = fetch_patient_list()

patient_id = st.sidebar.selectbox("Select Patient File (Type to search)", patient_list)
st.sidebar.info(f"🔒 Database explicitly locked to Patient: {patient_id}")


# --- CHAT MEMORY ---

if "messages" not in st.session_state:
    st.session_state.messages = []



for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])



# --- CHAT INPUT & API CALL ---
if prompt := st.chat_input(f"Ask about patient {patient_id}'s history..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    payload = {
        "patient_id": patient_id,
        "messages": st.session_state.messages
    }

    with st.spinner("Analyzing securely..."):
        try:
            response = requests.post(API_CHAT_URL, json=payload)
            response.raise_for_status()
            bot_reply = response.json().get("llm_response")
            
            # Enforce Output Disclaimer
            bot_reply += "\n\n*⚠️ AI generated summary. Do not use for diagnostic purposes.*"
            
        except requests.exceptions.RequestException as e:
            bot_reply = f"❌ API Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})
    st.chat_message("assistant").write(bot_reply)



# := walrus operator