import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="Total Care Squad - AI Receptionist", page_icon="🤖")
st.title("Total Care Squad")
st.subheader("Virtual IT Receptionist & Intake")

# Retrieve secret
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY secret is not set in Streamlit settings.")
    st.stop()

# Initialize Google GenAI client
client = genai.Client(api_key=api_key)

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

# Initialize session history
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat" not in st.session_state:
    st.session_state.chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        )
    )

# Render conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt input
if prompt := st.chat_input("How can Nico help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response
    response = st.session_state.chat.send_message(prompt)
    reply_text = response.text

    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)
