import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from google.genai import types

st.set_page_config(page_title="Total Care Squad - AI Receptionist", page_icon="🤖")
st.title("Total Care Squad")
st.subheader("Virtual IT Receptionist & Intake")

# Load Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
email_sender = st.secrets.get("EMAIL_SENDER")
email_password = st.secrets.get("EMAIL_PASSWORD")
email_receiver = st.secrets.get("EMAIL_RECEIVER", "tdeshotel86@gmail.com")

if not api_key:
    st.error("GEMINI_API_KEY secret is missing.")
    st.stop()

# Email Dispatch Function
def dispatch_intake_email(client_name: str, contact_info: str, issue_description: str, appointment_time: str):
    """Dispatches intake details to the support team inbox."""
    if not email_sender or not email_password:
        return "Email dispatch skipped: sender credentials not configured in secrets."

    try:
        msg = MIMEMultipart()
        msg["From"] = email_sender
        msg["To"] = email_receiver
        msg["Subject"] = f"🔔 New IT Support Lead: {client_name}"

        body = f"""Total Care Squad - New Consultation Request

Client Name: {client_name}
Contact Information: {contact_info}
Issue Summary: {issue_description}
Requested Date/Time: {appointment_time}

---
Dispatched automatically by Virtual Receptionist (Nico).
"""
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)

        return "Intake notification sent successfully to technical support."
    except Exception as e:
        return f"Failed to send email notification: {str(e)}"

SYSTEM_INSTRUCTION = """
You are Nico, the virtual receptionist for Total Care Squad IT Support.
Your job is to greet clients, triage technical issues, and gather intake information for IT support consultations.

Intake requirements to collect:
1. Client Full Name
2. Preferred Contact Info (Phone or Email)
3. Detailed description of the IT issue
4. Preferred appointment date and time

When you have collected ALL 4 pieces of information, execute the dispatch_intake_email tool to send the notification to the team, and let the user know their consultation request has been routed to a technician.
"""

# Tool definition for Gemini
email_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="dispatch_intake_email",
            description="Sends an email notification with client intake details to technical support.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "client_name": types.Schema(type="STRING", description="Client's full name"),
                    "contact_info": types.Schema(type="STRING", description="Client phone number or email"),
                    "issue_description": types.Schema(type="STRING", description="Summary of the IT problem"),
                    "appointment_time": types.Schema(type="STRING", description="Requested consultation date and time"),
                },
                required=["client_name", "contact_info", "issue_description", "appointment_time"]
            )
        )
    ]
)

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Input
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

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=[email_tool],
                temperature=0.7,
            )
        )

        reply_text = ""

        # Check for function call
        if response.function_calls:
            for call in response.function_calls:
                if call.name == "dispatch_intake_email":
                    args = call.args
                    tool_result = dispatch_intake_email(
                        client_name=args.get("client_name", "Unknown"),
                        contact_info=args.get("contact_info", "Not provided"),
                        issue_description=args.get("issue_description", "General Inquiry"),
                        appointment_time=args.get("appointment_time", "Pending")
                    )
                    reply_text = f"Thank you, {args.get('client_name')}! Your details have been submitted to Total Care Squad. We will reach out to you shortly at {args.get('contact_info')}."
                    st.toast("📧 Intake email dispatched to support team!")
        else:
            reply_text = response.text or "How can I assist you with your IT issue?"

    except Exception as e:
        reply_text = f"Nico encountered a temporary error: {str(e)}"

    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)
