import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# 1. Page Configuration
st.set_page_config(
    page_title="MediGuide AI", 
    page_icon="🩺", 
    layout="centered"
)

# 2. Initialize Session State Variables
if "api_authenticated" not in st.session_state:
    st.session_state["api_authenticated"] = False
if "api_key" not in st.session_state:
    st.session_state["api_key"] = ""
if "messages" not in st.session_state:
    st.session_state["messages"] = []


# 3. Lock Screen: Ask for API Key First
if not st.session_state["api_authenticated"]:
    st.title("🔐 MediGuide AI - Access Portal")
    st.write("Please enter your OpenAI API Key to unlock the medical assistant.")

    # API Key Input Form
    api_key_input = st.text_input("OpenAI API Key", type="password")

    if st.button("Unlock Assistant"):
        key = api_key_input.strip()
        if key:
            with st.spinner("Validating API key..."):
                try:
                    # Test the key with a minimal completion request
                    test_model = ChatOpenAI(
                        model_name="gpt-4o-mini",
                        openai_api_key=key,
                        max_tokens=1,
                        max_retries=0
                    )
                    test_model.invoke("test")
                    
                    # Key is valid: Save state and allow entry
                    st.session_state["api_key"] = key
                    st.session_state["api_authenticated"] = True
                    st.rerun()

                except Exception as e:
                    # Key is invalid or call failed: Show error message
                    st.error("❌ Invalid API Key or authentication failed. Access denied.")
        else:
            st.error("Please enter a valid API key to proceed.")

    # Stop execution here so the app doesn't load until unlocked
    st.stop()

# ==========================================
# 4. MAIN INTERFACE (Loaded after unlock)
# ==========================================
st.title("🩺 MediGuide AI")
st.caption("An interactive medical information assistant for symptom analysis, health questions, and triage guidance.")

# Medical Disclaimer Banner
st.warning(
    "**Disclaimer:** MediGuide AI is strictly for health and medical information. "
    "It is not a substitute for professional medical advice, diagnosis, or treatment."
)

# Strict System Prompt with Guardrails against irrelevant topics
system_prompt = (
    "You are MediGuide AI, a specialized medical and healthcare assistant. "
    "STRICT TOPIC GUARDRAIL: You are strictly restricted to discussing human health, medicine, symptoms, wellness, nutrition, anatomy, and healthcare. "
    "If the user asks ANY question that is irrelevant to medical, health, or clinical topics (such as coding, general knowledge, math, pop culture, sports, financial advice, or general conversation), "
    "you MUST decline to answer politely using this exact response or similar: "
    "'I am specialized exclusively as a medical guide. I cannot answer non-medical or off-topic questions. Please ask a health- or symptom-related question.'"
    "\n\nFor valid medical queries, follow these guidelines:"
    "\n1. Emergency Triage First: If severe red-flag symptoms are mentioned, advise emergency medical help immediately."
    "\n2. Structured Assessment: Outline potential causes, follow-up questions, self-care measures, and red flags."
    "\n3. Tone: Professional, compassionate, and non-alarmist."
    "\n4. Disclaimer: Remind the user that this response is for educational purposes only."
)

# Ensure System Message is tracked in session history
if not any(isinstance(x, SystemMessage) for x in st.session_state["messages"]):
    st.session_state["messages"].append(SystemMessage(content=system_prompt))

# Display prior chat messages (skipping raw system message)
for msg in st.session_state["messages"][1:]:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.markdown(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.markdown(msg.content)

# 5. Bottom Center Chat Input
if user_prompt := st.chat_input("Describe your symptoms or ask a health question..."):
    
    # Append user input to history and display it
    st.session_state["messages"].append(HumanMessage(content=user_prompt))
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Initialize Chat model with the user-provided API key
    try:
        chat_model = ChatOpenAI(
            model_name="gpt-4o-mini",
            temperature=0.0,  # Zero temperature for strict instruction following
            openai_api_key=st.session_state["api_key"]
        )

        # Generate AI response inside a spinner
        with st.chat_message("assistant"):
            with st.spinner("Reviewing request..."):
                response = chat_model.invoke(st.session_state["messages"])
                st.markdown(response.content)

                # Save AI response to message history
                st.session_state["messages"].append(AIMessage(content=response.content))

    except Exception as e:
        st.error(f"An error occurred while communicating with the OpenAI API: {e}")
