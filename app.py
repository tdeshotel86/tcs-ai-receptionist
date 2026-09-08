import streamlit as st
from google import genai
from google.genai import types
from google.genai.errors import APIError

st.set_page_config(page_title="Total Care Squad - AI Receptionist", page_icon="🤖")
st.title("Total Care Squad")
st.subheader("Virtual IT Receptionist & Intake")

# Load API key from Streamlit Cloud Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY secret is not set in Streamlit settings.")
    st.stop()

SYSTEM_INSTRUCTION = """
You are Nico, the virtual receptionist for Total Care Squad IT Support.
Your job is to greet clients, triage technical issues, and gather intake information for IT support consultations.

Intake requirements to collect:
1. Client Full Name
2. Preferred Contact Info (Phone or Email)
3. Detailed description of the IT issue
4. Preferred appointment date and time

Maintain a professional, helpful, and concise tone.
"""

# Initialize message history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User prompt
if prompt := st.chat_input("How can Nico help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = genai.Client(api_key=api_key)

    contents = []
    for m in st.session_state.messages:
        role = "user" if m["role"] == "user" else "model"
        contents.append(
            types.Content(
                role=role,
                parts=[types.Part.from_text(text=m["content"])]
            )
        )

    # Fallback model cascade to beat 503 capacity spikes
    models_to_try = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-2.0-flash"]
    reply_text = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.7,
                )
            )
            reply_text = response.text
            if reply_text:
                break
        except APIError as e:
            if "503" in str(e) or "404" in str(e):
                continue
            else:
                st.error(f"API Error: {e}")
                break

    if not reply_text:
        reply_text = "Nico is experiencing heavy call volume. Please send your message again in a moment."

    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)
