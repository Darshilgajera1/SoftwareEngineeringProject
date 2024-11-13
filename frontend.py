import streamlit as st
from streamlit_option_menu import option_menu
import sys
import os

from test import tool_making_agent

# Add the parent directory to sys.path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import MainAgentWithTools
    from langchain.callbacks import StreamingStdOutCallbackHandler
    from langchain_community.chat_models import ChatOpenAI
    from tools.toolRegistration import tool_registration_tool
    from tools.queryTool import tool_query_tool
    from tools.browsingTool import paged_web_browser
    from langchain.tools import Tool
    from langchain.agents.agent_toolkits import FileManagementToolkit
    from langchain.utilities import GoogleSearchAPIWrapper
    from prompt import TOOL_MAKER_PROMPT
    import util
except ImportError as e:
    st.error(f"Failed to import required modules: {str(e)}")
    st.stop()

st.markdown("""
    <style>
    /* Expand the entire page width and center the content */
    .main {
        max-width: 1200px;
        margin: 0 auto;
        padding: 10px;
    }

    /* Center align the title */
    h1 {
        text-align: center;
        color: #2E86C1;
    }

    /* Style the prompt input box */
    .stTextInput > div > input {
        font-size: 18px;
        padding: 15px;
        border-radius: 10px;
        border: 2px solid #3498DB;
        background-color: #F0F8FF;
        width: 100%; /* Full-width input box */
    }

    /* Customize the Submit and Go Back buttons */
    div.stButton > button:first-child {
        background-color: #3498DB;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 18px;
        margin-top: 10px;
        margin-bottom: 20px;
        width: 100%; /* Full-width button */
        transition: background-color 0.3s ease;
    }

    /* Button hover effect */
    div.stButton > button:first-child:hover {
        background-color: #1F618D;
        color: white;
    }

    /* Customize Go Back button */
    div.stButton > button:nth-child(2) {
        background-color: #E74C3C;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 18px;
        margin-top: 10px;
        margin-bottom: 20px;
        width: 100%; /* Full-width button */
        transition: background-color 0.3s ease;
    }

    /* Go Back button hover effect */
    div.stButton > button:nth-child(2):hover {
        background-color: #C0392B;
        color: white;
    }

    /* Style for the footer */
    h4 {
        text-align: center;
        color: gray;
    }

    </style>
    """, unsafe_allow_html=True)

def home():
    if 'page' not in st.session_state:
        st.session_state['page'] = 'home'

    st.title("Welcome to :red[PoolofTools]")
    st.markdown("""
    PoT (Pool of Tools) is an innovative platform designed to empower Large Language Model (LLM) agents with the ability to create and utilize tools autonomously. The platform acts as a dynamic repository, or "pot," where agents can store, share, and access tools that they have created or that others have made available.
    
    ### Key Features:
    
    - Automated Tool Creation: When given a task by a human user, an agent will first search the "pot" for an existing tool that can complete the task. If no suitable tool is found, the agent will autonomously create a new tool tailored to the task at hand.
    - Collaborative Environment: Tools created by one agent are made accessible to other agents, fostering a collaborative ecosystem where agents can learn from and build upon each other's work.
    - Efficient Task Resolution: By leveraging existing tools in the pot, agents can quickly and efficiently solve user problems, reducing redundancy and maximizing resource utilization.
        Imagine having the power to effortlessly analyze complex documents, uncover insights, and receive instant 
        responses to your queries, all from one centralized location. **PdfBot** does exactly that by harnessing 
        the latest advancements in natural language processing and machine learning.
    
    Get started now and experienced the future of Autonomous agent in your regular task
    """)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.button("Let's get started!", key='get_started', on_click=set_interaction_page)


def interaction_page():

    # Page Title
    st.markdown("<h1>🤖 Interact with the Pool of Tools</h1>", unsafe_allow_html=True)

    # Horizontal Divider
    st.markdown("<hr>", unsafe_allow_html=True)

    # Centered input prompt with larger text and padding for better visual appearance
    st.markdown("<h3 style='text-align: center;'>📝 What's your task for the Pool of Tools?</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.25, 1.5, 0.25])  # Adjust columns for better centering and full-width input
    with col2:
        # Better-looking text input with a larger font size and full-width style
        prompt = st.text_input(
            "Enter your prompt:",
            placeholder="E.g., Analyze this document or generate a financial report...",
            help="Provide a specific prompt to get the best results.",
            key="prompt_input"
        )

    st.markdown("<br>", unsafe_allow_html=True)  # Adds some space after input

    # Align Submit and Go Back buttons in a row, adding custom button styles
    col1, col2, col3 = st.columns([0.25, 1.5, 0.25])  # Adjust column widths for centering buttons

    with col2:
        # Submit Button
        submit_button = st.button("🚀 Submit", key="submit")
        # Reset Button
        st.button("🔄 Reset", key="reset", on_click=clear_prompt_input)
        if submit_button:
            if prompt:
                # Simulate processing time for better UX
                tool_making_agent.receive("HumanUser", prompt)
                tool_making_agent.send()
                with st.spinner("🤖 Processing your request..."):
                    st.success(f"✅ Response for your prompt: '{prompt}'")
            else:
                st.error("❌ Please enter a valid prompt before submitting.")


        # Go Back Button
        st.button("⬅️ Go Back", key="go_back", on_click=set_home_page)

    # Additional styling and spacing for better appearance
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Footer
    st.markdown("<h4>Powered by Pool of Tools</h4>", unsafe_allow_html=True)


def main():
    # Initialize session state for login and chat interface
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'page' not in st.session_state:
        st.session_state['page'] = "home"

    # Load secrets
    util.load_secrets()

    # If not logged in, show only login page
    if not st.session_state.logged_in:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", on_click=set_login):
            # login_result = login.login(username, password)
            login_result = True
            if login_result:
                st.session_state.page = "home"
                st.success(f"Logged in as {username}")
                st.rerun()
            else:
                st.error("Login failed. Please check your credentials.")
        return

    with st.sidebar:
        choose = option_menu("Menu", ["Home", "My Account"],
                             icons=['house', 'account'],
                             menu_icon="cast", default_index=0)

    if choose == 'home' or st.session_state['page'] == 'home':
        home()
    elif st.session_state['page'] == 'interaction_page':
        interaction_page()

    elif choose == "My Account":
        st.title("My Account")
        st.write("Welcome to your account page.")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# Set the page flags
def set_login():
    st.session_state['logged_in'] = True

def set_home_page():
    st.session_state['page'] = 'home'

def set_interaction_page():
    st.session_state['page'] = 'interaction_page'

def clear_prompt_input():
    st.session_state['prompt_input'] = ""

if __name__ == "__main__":
    main()