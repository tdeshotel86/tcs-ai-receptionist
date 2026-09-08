import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="Total Care Squad - AI Receptionist", page_icon="🤖")
st.title("Total Care Squad")
st.subheader("Virtual IT Receptionist & Intake")

# Load API key from Streamlit Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.warning("GEMINI_API_KEY secret not found. Please configure it in your Streamlit app settings.")
    st.stop()

genai.configure(api_key=api_key)

SYSTEM_INSTRUCTION = """
You are Nico, the virtual receptionist for Total Care Squad IT Support.
Your job is to greet clients, triage technical issues, and gather intake information for IT support consultations.

Intake requirements:
- Client Full Name
- Preferred Contact Info (Phone or Email)
- Detailed description of the IT issue
- Preferred appointment date and time

Maintain a professional, helpful, and concise tone.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest",
    system_instruction=SYSTEM_INSTRUCTION
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_session" not in st.session_state:
    st.session_state.chat_session = model.start_chat(history=[])

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User message input
if prompt := st.chat_input("How can Nico help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = st.session_state.chat_session.send_message(prompt)
    reply_text = response.text

    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)
