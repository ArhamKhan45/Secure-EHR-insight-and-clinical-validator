# Import required libraries
import os
import streamlit as st
import requests
from dotenv import load_dotenv


# Load environment variables from .env
load_dotenv()

BACKEND_API_URL = os.getenv("BACKEND_API_URL")

# API endpoints
API_CHAT_URL = f"{BACKEND_API_URL}/chat"
API_PATIENTS_URL = f"{BACKEND_API_URL}/patients"


# Configure Streamlit page
st.set_page_config(
    page_title="Zero-Trust Clinical EHR",
    layout="centered"
)

st.title("🏥 Enterprise EHR Chat")
st.caption("Protected by Presidio Zero-Trust & NeMo Guardrails")


# Fetch patient IDs from the backend API
@st.cache_data(ttl=300)
def fetch_patient_list():
    try:
        response = requests.get(API_PATIENTS_URL)

        if response.status_code == 200:
            data = response.json()

            # Get patient list from API response
            return data.get("patients", ["No patients found"])

    except requests.exceptions.RequestException:
        return ["Database Connection Error"]

    return ["Unknown Error"]


# Load available patients
patient_list = fetch_patient_list()

# Allow the user to select a patient
patient_id = st.sidebar.selectbox(
    "Select Patient File (Type to search)",
    patient_list
)


st.sidebar.info(
    f"🔒 Database explicitly locked to Patient: {patient_id}"
)

st.sidebar.markdown(
    """
    <style>
    .developer-sidebar {
        position: fixed;
        bottom: 20px;
        left: 20px;
        width: 250px;
    }

    .developer-sidebar a {
        color: white !important;
        text-decoration: none;
        font-weight: 600;
    }

    .developer-sidebar a:hover {
        color: white !important;
        text-decoration: underline;
    }
    </style>

    <div class="developer-sidebar">
        <a
            href="https://arhamullahkhan.vercel.app/"
            target="_blank"
            rel="noopener noreferrer"
        >
            👨‍💻 Arham Ullah Khan — Developer
        </a>
    </div>
    """,
    unsafe_allow_html=True
)


# --- CHAT MEMORY ---

# Create chat history if it doesn't already exist
if "messages" not in st.session_state:
    st.session_state.messages = []


# Display previous messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


# --- CHAT INPUT & API CALL ---

# := assigns the input to prompt and checks if it has a value
if prompt := st.chat_input(
    f"Ask about patient {patient_id}'s history..."
):

    # Save user's message in Streamlit session
    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    # Display user's message immediately
    st.chat_message("user").write(prompt)

    # Prepare request payload for FastAPI
    payload = {
        "patient_id": patient_id,
        "messages": st.session_state.messages
    }

    # Show loading indicator while API processes the request
    with st.spinner("Analyzing securely..."):
        try:
            response = requests.post(
                API_CHAT_URL,
                json=payload
            )

            # Raise an exception if API returns 4xx or 5xx
            response.raise_for_status()

            # Extract LLM response from JSON
            bot_reply = response.json().get(
                "llm_response",
                "No response received."
            )

            # Enforce output disclaimer
            bot_reply += (
                "\n\n"
                "⚠️ AI generated summary. "
                "Do not use for diagnostic purposes."
            )

        except requests.exceptions.RequestException as e:
            bot_reply = f"❌ API Error: {e}"

    # Save assistant response in chat history
    st.session_state.messages.append(
        {"role": "assistant", "content": bot_reply}
    )

    # Display assistant response
    st.chat_message("assistant").write(bot_reply)