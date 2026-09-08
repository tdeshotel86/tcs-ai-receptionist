import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google import genai
from google.genai import types
from google.genai.errors import APIError

st.set_page_config(page_title="Total Care Squad - AI Intake", page_icon="🛡️")
st.title("Total Care Squad")
st.subheader("Virtual Receptionist & Multi-Service Intake")

# Load Secrets
api_key = st.secrets.get("GEMINI_API_KEY")
email_sender = st.secrets.get("EMAIL_SENDER")
email_password = st.secrets.get("EMAIL_PASSWORD")
email_receiver = st.secrets.get("EMAIL_RECEIVER", "tdeshotel86@gmail.com")

if not api_key:
    st.error("GEMINI_API_KEY secret is missing.")
    st.stop()

# Email Dispatcher
def dispatch_service_ticket(
    service_track: str,
    client_name: str,
    contact_info: str,
    company_or_property: str,
    specific_details: str,
    timeline_or_urgency: str,
    preferred_schedule: str
):
    """Sends structured service form data directly to the support inbox."""
    if not email_sender or not email_password:
        return "Email dispatch skipped: credentials missing in secrets."

    try:
        msg = MIMEMultipart()
        msg["From"] = email_sender
        msg["To"] = email_receiver
        msg["Subject"] = f"📋 [{service_track.upper()}] Intake: {client_name}"

        body = f"""TOTAL CARE SQUAD - SERVICE REQUEST DISPATCH
============================================================
SERVICE TRACK: {service_track.upper()}

CLIENT INFORMATION:
- Requester Name: {client_name}
- Contact Details: {contact_info}
- Company / Property / Site: {company_or_property or 'Residential / Individual'}

PROJECT / INCIDENT SCOPE:
{specific_details}

TIMELINE / PRIORITY:
- Urgency / Delivery Target: {timeline_or_urgency}
- Preferred Consultation Time: {preferred_schedule}
============================================================
Processed autonomously by Virtual Receptionist (Nico).
"""
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_sender, email_password)
            server.send_message(msg)

        return "Ticket dispatched successfully."
    except Exception as e:
        return f"Dispatch failed: {str(e)}"

# System Prompts & Service Routing
SYSTEM_INSTRUCTION = """
You are Nico, the virtual intake specialist for Total Care Squad.
You handle onboarding and intake for 5 core service offerings:
1. Cybersecurity Services (Network audits, firewall hardening, compliance, threat mitigation, employee training)
2. Surveillance Installation (CCTV, IP camera deployment, NVR/DVR storage, residential or commercial site setup)
3. Custom Website Request (New build, redesign, portfolio/business presence, integrations, target launch date)
4. IT Troubleshooting Request (Hardware failures, operating system crashes, local network/Wi-Fi drops, printer outages)
5. AI Receptionist Installation (Custom conversational voice/web agents, automated booking, API tool integrations)

Workflow:
- Greet the client and identify which of the 5 services they need. If they already stated their problem, immediately match it to the correct service.
- Ask questions 1 to 2 at a time to complete that specific service's form:
  * Client Full Name & Preferred Contact (Email or Phone)
  * Property/Business Type (Commercial or Residential)
  * Core Requirements / Symptoms / Scope of Work
  * Urgency or Target Delivery Date
  * Preferred consultation date and time
- When all necessary items are collected, execute the `dispatch_service_ticket` tool.
- Confirm submission with a polite summary.
"""

service_tool = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="dispatch_service_ticket",
            description="Logs and emails the completed service intake form to Total Care Squad dispatch.",
            parameters=types.Schema(
                type="OBJECT",
                properties={
                    "service_track": types.Schema(type="STRING", description="Cybersecurity, Surveillance Installation, Custom Website, IT Troubleshooting, or AI Receptionist"),
                    "client_name": types.Schema(type="STRING", description="Full name of requester"),
                    "contact_info": types.Schema(type="STRING", description="Phone number and/or email address"),
                    "company_or_property": types.Schema(type="STRING", description="Commercial company name or residential address"),
                    "specific_details": types.Schema(type="STRING", description="Comprehensive scope, technical specs, or problem summary"),
                    "timeline_or_urgency": types.Schema(type="STRING", description="Critical/High/Routine or targeted launch deadline"),
                    "preferred_schedule": types.Schema(type="STRING", description="Preferred date/time for consultation"),
                },
                required=[
                    "service_track",
                    "client_name",
                    "contact_info",
                    "specific_details",
                    "timeline_or_urgency",
                    "preferred_schedule"
                ]
            )
        )
    ]
)

# Chat State
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User Chat Input
if prompt := st.chat_input("Tell Nico which service you need assistance with..."):
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

    # Priority order of available models
    models_to_try = ["gemini-2.5-flash", "gemini-3.6-flash", "gemini-2.0-flash"]
    response = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    tools=[service_tool],
                    temperature=0.6,
                )
            )
            if response:
                break
        except APIError as e:
            if "503" in str(e) or "404" in str(e):
                continue
            else:
                break

    reply_text = ""
    if response and response.function_calls:
        for call in response.function_calls:
            if call.name == "dispatch_service_ticket":
                args = call.args
                dispatch_service_ticket(
                    service_track=args.get("service_track", "General"),
                    client_name=args.get("client_name", "Unknown"),
                    contact_info=args.get("contact_info", "Not provided"),
                    company_or_property=args.get("company_or_property", "Individual"),
                    specific_details=args.get("specific_details", "None provided"),
                    timeline_or_urgency=args.get("timeline_or_urgency", "Standard"),
                    preferred_schedule=args.get("preferred_schedule", "TBD")
                )
                reply_text = (
                    f"Thank you, **{args.get('client_name')}**! Your **{args.get('service_track')}** request "
                    f"has been submitted to the Total Care Squad team. We will review your project requirements "
                    f"and contact you shortly at **{args.get('contact_info')}**."
                )
                st.toast(f"📥 {args.get('service_track')} ticket emailed to dispatch!")
    elif response and response.text:
        reply_text = response.text
    else:
        reply_text = "Nico is currently handling high server demand. Please re-enter your message in a few seconds."

    st.session_state.messages.append({"role": "assistant", "content": reply_text})
    with st.chat_message("assistant"):
        st.markdown(reply_text)
