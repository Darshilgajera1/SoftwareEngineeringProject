import streamlit as st
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_core.tools import Tool
from streamlit_option_menu import option_menu
import sys
import os
import re
import json
import requests
import firebase_admin
from firebase_admin import credentials, auth
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

import util
from main import MainAgentWithTools
from prompt import TOOL_MAKER_PROMPT
from tools import verify_and_install_library, tool_query_tool, tool_registration_tool, query_available_modules, \
    paged_web_browser

util.load_secrets()

# Add the parent directory to sys.path to import from other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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

# Define system prompts for our agent
system_prompt_scribe = TOOL_MAKER_PROMPT

# initialize file management tools
file_tools = FileManagementToolkit(
    selected_tools=["read_file", "write_file", "list_directory", "copy_file", "move_file", "file_delete"]
).get_tools()


# initialie search API
search = GoogleSearchAPIWrapper()

def top10_results(query):
    return search.results(query, 10)

GoogleSearchTool = Tool(
    name="Google Search",
    description="Search Google for recent results.",
    func=top10_results,
)

tools = [GoogleSearchTool,
         tool_query_tool,
         tool_registration_tool,
         query_available_modules,
         paged_web_browser,
         verify_and_install_library,
         ] + file_tools

# Initialize our agents with their respective roles and system prompts
tool_making_agent = MainAgentWithTools(name="ToolCreator",
                                       system_message=system_prompt_scribe,
                                       model=ChatOpenAI(
                                       model_name='gpt-4o-mini',
                                       streaming=True,
                                       temperature=0.0,
                                       callbacks=[StreamingStdOutCallbackHandler()]),
                                       tools=tools)

if not firebase_admin._apps:
    print("###########################   Initializing Firebase Admin SDK...")
    cred = credentials.Certificate(os.getenv("FIREBASE_CREDENTIALS_PATH"))
    firebase_admin.initialize_app(cred, {
        'projectId': os.getenv("GOOGLE_CLOUD_PROJECT"),
    })

reset_codes = {}

def generate_reset_code(email):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    expiry_time = datetime.now() + timedelta(minutes=10)
    reset_codes[email] = {'code': code, 'expiry': expiry_time}
    return code

def send_email(recipient, subject, body):
    sender = os.getenv("EMAIL")
    password = os.getenv("EMAIL_PASSWORD")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender, password)
            server.sendmail(sender, recipient, msg.as_string())
        st.success("Email sent successfully")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def send_reset_code_email(email):
    code = generate_reset_code(email)
    send_email(email, "Your Password Reset Code", f"Your reset code is: {code}")

def account():
    st.title('Welcome' + st.session_state.get('user_name', ''))
    build_login_ui()

def check_name(name_sign_up: str) -> bool:
    name_regex = (r'^[A-Za-z_][A-Za-z0-9_]*')
    return bool(re.search(name_regex, name_sign_up))

def check_email(email_sign_up: str) -> bool:
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    return bool(re.fullmatch(regex, email_sign_up))

def check_username(username_sign_up: str) -> bool:
    regex = re.compile(r'^[a-zA-Z0-9_.-]+$')
    return bool(re.match(regex, username_sign_up))

def check_uniq_email(email_sign_up: str) -> bool:
    all_users = auth.list_users().users
    return not any(user.email == email_sign_up for user in all_users)

def check_uniq_username(username_sign_up: str) -> bool:
    all_users = auth.list_users().users
    return not any(user.uid == username_sign_up for user in all_users)

def sign_in_with_email_and_password(user_name: str, password: str, return_secure_token=True) -> dict:
    st.session_state['Firebase_API_key'] = os.getenv("FIREBASE_WEB_API")
    payload = json.dumps({"email": user_name, "password": password, "returnSecureToken": return_secure_token})
    rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    response = requests.post(rest_api_url, params={"key": st.session_state['Firebase_API_key']}, headers={"Content-Type": "application/json"}, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to sign in: {response.json().get('error', {}).get('message', 'Unknown error')}")
        return None

def register_user(name_sign_up: str, email_sign_up: str, username_sign_up: str, password_sign_up: str) -> bool:
    user = auth.create_user(display_name=name_sign_up, email=email_sign_up, password=password_sign_up, uid=username_sign_up)
    return bool(user.uid)

def login_page() -> None:
    with st.form("Login form"):
        username = st.text_input("Email", placeholder='Your email')
        password = st.text_input("Password", placeholder='Your password', type='password')

        st.markdown("###")
        login_submit_button = st.form_submit_button(label='Login')

        if login_submit_button:
            user_val = sign_in_with_email_and_password(username, password)
            if user_val is not None:
                st.session_state['log_in'] = True
                st.session_state['user_name'] = user_val['displayName']
                st.session_state['user_email'] = username
                st.success('Login Successful!!')
                st.rerun()
            else:
                st.error('Please enter valid Email and Password')

def sign_up_widget() -> None:
    with st.form("Sign Up Form"):
        name_sign_up = st.text_input("Name *", placeholder='test')
        email_sign_up = st.text_input("Email *", placeholder='user@gmail.com')
        username_sign_up = st.text_input("Username *", placeholder='test1234')
        password_sign_up = st.text_input("Password *", placeholder='Create a strong password', type='password')

        st.markdown("###")
        register_button = st.form_submit_button(label='Register')

        # valid_name = check_name(name_sign_up=name_sign_up)
        # valid_email = check_email(email_sign_up=email_sign_up)
        # uniq_email = check_uniq_email(email_sign_up=email_sign_up)
        # valid_username = check_username(username_sign_up=username_sign_up)
        # uniq_username = check_uniq_username(username_sign_up=username_sign_up)

        if register_button:
            # if not valid_name:
            #     st.error("Please enter a valid name")
            # elif not valid_email:
            #     st.error("Please enter a valid email address")
            # elif not uniq_email:
            #     st.error("Email already exists!")
            # elif not valid_username:
            #     st.error("Please enter a valid username")
            # elif not uniq_username:
            #     st.error(f'Sorry, username {username_sign_up} already exists!')
            #
            # if valid_name and valid_email and uniq_email and valid_username and uniq_username:
            register_user(name_sign_up, email_sign_up, username_sign_up, password_sign_up)
            st.success("Registration Successful!")

def logout_widget() -> None:
    if st.session_state['log_in']:
        logout_btn = st.button("Logout")
        if logout_btn:
            st.session_state['log_out'] = True
            st.session_state['log_in'] = False
            st.session_state['user_name'] = ''
            st.session_state['user_email'] = ""
            st.rerun()

def forgot_password() -> None:
    with st.form("Forgot Password Form"):
        email_forgot_passwd = st.text_input("Email", placeholder='Please enter your email')

        st.markdown("###")
        forgot_passwd_submit_button = st.form_submit_button(label='Get Password')

        if forgot_passwd_submit_button:
            try:
                user = auth.get_user_by_email(email_forgot_passwd)
                send_reset_code_email(email_forgot_passwd)
                st.session_state['reset_email'] = email_forgot_passwd
                st.session_state['reset_code_sent'] = True
                st.success("Secure Password Sent Successfully!")
            except firebase_admin.exceptions.FirebaseError:
                st.error("Email ID not registered with us!")

def reset_password() -> None:
    with st.form("Reset Password Form"):
        email_reset_passwd = st.text_input("Email", value=st.session_state.get('reset_email', ''), placeholder='Please enter your email')
        reset_code = st.text_input("Reset Code", placeholder='Enter the code sent to your email')

        new_password = st.text_input("New Password", placeholder='Enter your new password', type='password')

        st.markdown("###")
        reset_passwd_submit_button = st.form_submit_button(label='Reset Password')

        if reset_passwd_submit_button:
            if email_reset_passwd in reset_codes:
                stored_code = reset_codes[email_reset_passwd]
                if stored_code['code'] == reset_code and datetime.now() < stored_code['expiry']:
                    user = auth.get_user_by_email(email_reset_passwd)
                    auth.update_user(user.uid, password=new_password)

                    del reset_codes[email_reset_passwd]

                    st.success("Password has been reset. You can now log in with your new password.")
                else:
                    st.error("Invalid or expired reset code.")
            else:
                st.error("No reset code found for this email.")

def change_password() -> None:
    with st.form("Change Password Form"):
        current_password = st.text_input("Current Password", type='password', placeholder='Enter your current password')
        new_password = st.text_input("New Password", type='password', placeholder='Enter your new password')

        st.markdown("###")
        change_password_submit_button = st.form_submit_button(label='Change Password')

        if change_password_submit_button:
            user_email = st.session_state['user_email']
            user_val = sign_in_with_email_and_password(user_email, current_password)

            if user_val is not None:
                try:
                    user = auth.get_user_by_email(user_email)
                    auth.update_user(user.uid, password=new_password)
                    st.success("Password has been changed successfully.")
                except firebase_admin.exceptions.FirebaseError as e:
                    st.error(f"Error updating password: {e}")
            else:
                st.error("Current password is incorrect.")

def navbar() -> str:
    main_navbar = st.empty()
    with main_navbar:
        selected = option_menu(
            menu_title=None,
            default_index=0,
            options=['Login', 'Create Account', 'Forgot Password', 'Reset Password'],
            icons=['key', 'person-plus', 'question', 'key'],
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#333333"},  # Dark background for navbar
                "icon": {"color": "white", "font-size": "18px"},  # White icons for better visibility
                "nav-link": {
                    "font-size": "18px",
                    "text-align": "left",
                    "margin":"0px",
                    "color": "white",  # White text
                    "--hover-color": "#444444"  # Darker hover color
                },
                "nav-link-selected": {"background-color": "black"},  # Selected link background
            }
        )
        return selected

def build_login_ui():
    if not st.session_state.get('log_in', False):
        selected = navbar()

        if selected == 'Login':
            login_page()

        if selected == 'Create Account':
            sign_up_widget()

        if selected == 'Forgot Password':
            forgot_password()

        if selected == 'Reset Password' and st.session_state.get('reset_code_sent', False):
            st.session_state['reset_code_sent'] = False
            reset_password()

        return st.session_state['log_in']

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
    # Reset the submitted state when the page loads
    if 'submitted' in st.session_state:
        st.session_state['submitted'] = False

    # Page Title
    st.markdown("<h1>🤖 Interact with the Pool of Tools</h1>", unsafe_allow_html=True)

    # Horizontal Divider
    st.markdown("<hr>", unsafe_allow_html=True)

    # Centered input prompt with larger text and padding for better visual appearance
    st.markdown("<h3 style='text-align: center;'>📝 What's your task for the Pool of Tools?</h3>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.25, 1.5, 0.25])  # Adjust columns for better centering and full-width input
    with col2:
        file_name = ""
        with st.form("User Input Form"):
            prompt = st.text_input(
                "Enter your prompt:",
                placeholder="E.g., Analyze this document or generate a financial report...",
                help="Provide a specific prompt to get the best results.",
                key="prompt_input"
            )

            st.markdown("<h3 style='text-align: center;'>📁 Upload your files</h3>", unsafe_allow_html=True)
            uploaded_file = st.file_uploader("Choose an image, video, or PDF file (optional)", type=["jpg", "jpeg", "png", "mp4", "pdf"])

            submit_button = st.form_submit_button(label="🚀 Submit")

            if submit_button:
                st.session_state['prompt'] = prompt
                st.session_state['uploaded_file'] = uploaded_file
                st.session_state['submitted'] = True

        if st.session_state.get('submitted', False):
            prompt = st.session_state['prompt']
            uploaded_file = st.session_state['uploaded_file']
            file_name = uploaded_file.name if uploaded_file else ""

            # Process uploaded files
            if uploaded_file is not None:
                file_name = uploaded_file.name
                file_path = os.path.join("inputs", file_name)

                # Save the file to the inputs directory
                try:
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                except Exception as e:
                    st.error(f"An error occurred: {e}")

                st.success(f"File {file_name} saved to inputs directory.")

            # Pass the file to the tool making agent for further processing
            tool_making_agent.receive("HumanUser", f"{prompt}.Process this file: {file_name}")
            response = tool_making_agent.send()

            with st.spinner("🤖 Processing your request..."):
                st.success(f"✅ Response for your prompt: '{prompt}'")

            st.success(f"Output for {file_name} saved to outputs directory.")
            st.markdown(f"📄 **Output:** {response}")

    # Additional styling and spacing for better appearance
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Footer
    st.markdown("<h4>Powered by Pool of Tools</h4>", unsafe_allow_html=True)


def main():
    if 'log_in' not in st.session_state:
        st.session_state.log_in = False
    if 'page' not in st.session_state:
        st.session_state['page'] = "home"

    if not st.session_state.log_in:
        build_login_ui()

    # Navigation logic for logged-in users
    if st.session_state.log_in:
        with st.sidebar:
            choose = option_menu("Menu", ["Home", "Interaction"],
                                 icons=['house', 'robot'],
                                 menu_icon="cast", default_index=0)

            if st.button("Logout"):
                st.session_state.log_in = False
                st.experimental_rerun()

        if st.session_state['page'] == 'home':
            home()
        elif st.session_state['page'] == 'interaction_page':
            interaction_page()

# Set the page flags
def set_login():
    st.session_state['log_in'] = True

def set_home_page():
    st.session_state['page'] = 'home'

def set_interaction_page():
    st.session_state['page'] = 'interaction_page'

def set_account_page():
    st.session_state['page'] = 'account'

def clear_prompt_input():
    st.session_state['prompt_input'] = ""

if __name__ == "__main__":
    main()