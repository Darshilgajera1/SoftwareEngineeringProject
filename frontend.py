import json
import logging
import os
import random
import re
import smtplib
import string
import sys
from datetime import datetime, timedelta
from email.mime.text import MIMEText

import firebase_admin
import requests
import streamlit as st
import streamlit.components.v1 as components
from firebase_admin import credentials, auth, firestore
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain_community.chat_models import ChatOpenAI
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.callbacks import StreamingStdOutCallbackHandler
from langchain_core.tools import Tool
from streamlit_option_menu import option_menu

import util
from main import MainAgentWithTools
from prompt import TOOL_MAKER_PROMPT
from tools import (
    verify_and_install_library,
    query_available_modules,
    paged_web_browser,
)

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

db = firestore.client()

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
    response = requests.post(rest_api_url, params={"key": st.session_state['Firebase_API_key']},
                             headers={"Content-Type": "application/json"}, data=payload)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Failed to sign in: {response.json().get('error', {}).get('message', 'Unknown error')}")
        return None


def register_user(name_sign_up: str, email_sign_up: str, username_sign_up: str, password_sign_up: str) -> bool:
    user = auth.create_user(display_name=name_sign_up, email=email_sign_up, password=password_sign_up,
                            uid=username_sign_up)
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
                st.session_state['user_email'] = username.strip().lower()
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

        if register_button:
            if check_name(name_sign_up) and check_email(email_sign_up) and check_username(
                    username_sign_up) and check_uniq_username(username_sign_up) and check_uniq_email(email_sign_up):
                register_user(name_sign_up, email_sign_up, username_sign_up, password_sign_up)
                st.success("Registration Successful!")
            else:
                if not check_name(name_sign_up):
                    st.error("Invalid name. Please enter a valid name.")
                elif not check_email(email_sign_up):
                    st.error("Invalid email. Please enter a valid email.")
                elif not check_username(username_sign_up):
                    st.error("Invalid username. Please enter a valid username.")
                elif not check_uniq_username(username_sign_up):
                    st.error("Username already taken. Please choose a different username.")
                elif not check_uniq_email(email_sign_up):
                    st.error("Email already registered. Please use a different email.")


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
        email_reset_passwd = st.text_input("Email", value=st.session_state.get('reset_email', ''),
                                           placeholder='Please enter your email')
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
                    "margin": "0px",
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
        st.session_state['page'] = 'Home'

    # Set a custom title with branding
    st.title(":blue_heart: Welcome to **PoolofTools** :toolbox:")

    # Add a hero section with a friendly introduction
    st.markdown(
        """
        <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);">
        <h2 style="text-align: center; color: #007acc;">Empowering AI Agents to Build and Share Tools</h2>
        <p style="text-align: center; color: #333;">
        Imagine a world where AI agents autonomously create, share, and utilize tools to make your life easier.
        <strong>PoolofTools (PoT)</strong> is here to transform your vision into reality by enabling
        Large Language Model (LLM) agents to collaborate and innovate together. 🌟
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Add sections with creative icons and layouts
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        ### :star: **Why Choose PoolofTools?**
    
        - **🚀 Automated Tool Creation**: Agents autonomously create new tools for unique tasks if no suitable ones exist.
        - **🤝 Collaborative Environment**: Share and access tools created by others, fostering a thriving ecosystem of innovation.
        - **⚡ Efficient Problem Solving**: Leverage existing tools to minimize redundancy and maximize productivity.
        - **📄 Smart Document Analysis**: Analyze complex documents and uncover insights with tools like **PdfBot**.
    
        Get started today and experience the future of task automation!
        """,
        unsafe_allow_html=True,
    )

    # Add a testimonial or user story section
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="background-color: #e6f7ff; padding: 20px; border-radius: 10px; box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);">
        <h3 style="text-align: center; color: #0056b3;">What Our Users Say</h3>
        <blockquote style="text-align: center; font-style: italic; color: #555;">
        "PoolofTools has revolutionized how I handle complex tasks. With its collaborative ecosystem, my productivity
        has skyrocketed, and I’ve been able to tackle projects faster than ever before!" - <strong>Fenil</strong>
        </blockquote>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="text-align: center;"> Made with ❤️ by the PoolofTools Team.</div>
        <div style="text-align: center; font-size: 16px; color: #666;">
        <strong>Connect with us:</strong> <br>
        <a href="https://www.linkedin.com" target="_blank" style="margin: 0 10px; text-decoration: none;">
        <img src="https://img.icons8.com/ios-filled/50/0077b5/linkedin.png" title="LinkedIn" alt="LinkedIn" width="40" height="40">
        </a>
        <a href="https://twitter.com" target="_blank" style="margin: 0 10px; text-decoration: none;">
        <img src="https://img.icons8.com/ios-filled/50/1DA1F2/twitter.png" title="Twitter" alt="Twitter" width="40" height="40">
        </a>
        <a href="https://github.com" target="_blank" style="margin: 0 10px;">
        <img src="https://img.icons8.com/ios-filled/50/333333/github.png" title="GitHub" alt="GitHub" width="40" height="40">
        </a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def interaction_page():
    # Reset the submitted state when the page loads
    if 'submitted' in st.session_state:
        st.session_state['submitted'] = False

    # Page Title
    st.markdown("<h1>🤖 Interact with the Pool of Tools</h1>", unsafe_allow_html=True)

    # Horizontal Divider
    st.markdown("<hr>", unsafe_allow_html=True)

    # Centered input prompt with larger text and padding for better visual appearance
    st.markdown("<h3 style='text-align: center;'>📝 What's your task for the Pool of Tools?</h3>",
                unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.25, 1.5, 0.25])  # Adjust columns for better centering and full-width input
    with col2:
        with st.form("User Input Form"):
            prompt = st.text_input(
                "Enter your prompt:",
                placeholder="E.g., Analyze this document or generate a financial report...",
                help="Provide a specific prompt to get the best results.",
                key="prompt_input"
            )

            submit_button = st.form_submit_button(label="🚀 Submit")

            if submit_button:
                st.session_state['prompt'] = prompt
                st.session_state['submitted'] = True

        if st.session_state.get('submitted', False):
            prompt = st.session_state['prompt']

            # Pass the file to the tool making agent for further processing
            file_path = os.path.join("PoolOfTools", st.session_state['user_email'])

            # Ensure the directory exists
            os.makedirs(file_path, exist_ok=True)

            # Pass the file to the tool-making agent for further processing
            tool_making_agent.receive("HumanUser", f"{prompt}. Store the created tool in directory: {file_path}")
            response = tool_making_agent.send()

            with st.spinner("🤖 Processing your request..."):
                st.success(f"✅ Response for your prompt: '{prompt}'")

            st.markdown(f"📄 **Output:** {response}")

    # Additional styling and spacing for better appearance
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Footer
    st.markdown("<h4>Powered by Pool of Tools</h4>", unsafe_allow_html=True)


def display_tools(user_uid):
    """
    Display tools available in the PoolofTools folder for the authenticated user,
    based on their user-specific subfolder.

    :param user_uid: The UID of the authenticated user.
    """
    # Path to the user's specific folder inside PoolofTools
    user_tools_folder = os.path.join('./PoolofTools', user_uid)

    # Define a placeholder for displaying HTML content
    display_box = st.empty()

    # Function to remove JavaScript from HTML content
    def remove_javascript(html_content):
        # Remove <script> tags and any JavaScript inside them
        clean_html = re.sub(r'<script.?>.?</script>', '', html_content, flags=re.DOTALL)
        return clean_html

    try:
        # Check if the user's folder exists
        if os.path.exists(user_tools_folder):
            # Get all HTML files in the user's folder
            html_files = [f for f in os.listdir(user_tools_folder) if f.endswith('.html')]

            if html_files:
                st.write(f"### Tools available for user: {st.session_state['user_name']}")
                logging.info(f"HTML files found for user '{user_uid}': {html_files}")

                # Display the content at the top first
                display_box.empty()  # Clear the display box

                # You can display the first HTML file content as a preview above buttons
                with open(os.path.join(user_tools_folder, html_files[0]), "r") as file:
                    html_content = file.read()
                    # Remove JavaScript from HTML content
                    clean_html = remove_javascript(html_content)
                    # Display the HTML content inside the display_box
                    display_box.markdown(
                        f"""
                        <div style="border: 2px solid #ccc; padding: 10px; border-radius: 5px;">
                            {clean_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Create columns for buttons
                cols = st.columns(3)
                for i, tool in enumerate(html_files):
                    # Construct the full path to the tool
                    tool_path = os.path.join(user_tools_folder, tool)

                    # Create a button to load and display the HTML content
                    tool_name = os.path.splitext(tool)[0].replace('_', " ").title()  # Get the tool name without extension
                    col = cols[i % 3]
                    with col:
                        if st.button(f"Run {tool_name}"):
                            # Read the HTML content
                            with open(tool_path, "r") as file:
                                html_content = file.read()

                            # Remove JavaScript from the HTML content
                            clean_html = remove_javascript(html_content)

                            # Clear previous content and show new HTML
                            display_box.empty()  # Clear the display box
                            display_box.markdown(
                                f"""
                                <div style="border: 2px solid #ccc; padding: 10px; border-radius: 5px;">
                                    {clean_html}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

            else:
                st.write("No HTML files found in your tools folder.")
                logging.info(f"No HTML files found in the tools folder for user '{user_uid}'.")
        else:
            st.markdown(
                """
                <div style="padding: 10px; border-radius: 5px; background-color: #f8d7da; color: #842029; border: 1px solid #f5c2c7; font-family: Arial, sans-serif;">
                    <strong>🚨 No tools have been created by you yet.</strong><br>
                </div>
                """,
                unsafe_allow_html=True
            )
            logging.info(f"Tools folder does not exist for user '{user_uid}'.")
    except Exception as e:
        st.error(f"Error displaying tools: {e}")
        logging.error(f"Error displaying tools for user UID '{user_uid}': {e}")


def upload_file_names_to_firestore(folder_path, user_uid):
    """
    Store only file names in Firestore under the user's UID, with detailed logging.

    :param folder_path: Path to the local folder containing files.
    :param user_uid: The authenticated user's UID.
    """
    try:
        logging.info(f"Starting to upload file names from folder: {folder_path} for user UID: {user_uid}")

        # Firestore reference for the user's document
        user_doc_ref = db.collection('users').document(user_uid)

        # Store file names from the folder
        file_names = []
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):  # Ensure it's a file
                # Save file name in Firestore
                file_metadata = {
                    'filename': filename,
                    'timestamp': firestore.SERVER_TIMESTAMP
                }
                user_doc_ref.collection('files').add(file_metadata)
                file_names.append(filename)
                logging.info(f"Stored file name '{filename}' in Firestore for user '{user_uid}'.")

        logging.info("All file names successfully stored in Firestore!")
        return file_names

    except Exception as e:
        logging.error(f"An error occurred while uploading file names: {e}")
        raise


def main():
    """
    Main function to manage user login, navigation, and file uploads.
    """
    logging.info("Initializing application...")

    # Initialize session state variables if not already present
    if 'log_in' not in st.session_state:
        st.session_state.log_in = False
        logging.info("User session initialized with logged-out state.")
    if 'page' not in st.session_state:
        st.session_state['page'] = "Home"

    # Display login UI if the user is not logged in
    if not st.session_state.log_in:
        build_login_ui()

    # Post-login logic
    if st.session_state.log_in:
        logging.info(f"User '{st.session_state.get('user_email', 'Unknown')}' logged in.")

        with st.sidebar:
            # Sidebar navigation menu
            choose = option_menu(
                "Menu",
                ["Home", "Interaction", "Tools"],
                icons=['house', 'robot', 'tools'],
                menu_icon="cast",
                default_index=0
            )
            logging.info(f"User selected menu option: {choose}")

            st.session_state['page'] = choose
            user_email = st.session_state['user_email']
            # Logout button
            if st.button("Logout"):
                st.session_state.log_in = False
                st.session_state['uploaded_files'] = False  # Reset the upload flag
                logging.info("User logged out.")
                logout_widget()

        # Render the corresponding page based on the selected menu option
        if st.session_state['page'] == 'Home':
            logging.info("Rendering 'Home' page.")
            home()
        elif st.session_state['page'] == 'Interaction':
            logging.info("Rendering 'Interaction' page.")
            interaction_page()
        elif st.session_state['page'] == 'Tools':
            logging.info("Rendering 'Tools' page.")
            display_tools(user_email)


# Set the page flags
def set_login():
    st.session_state['log_in'] = True


def set_home_page():
    st.session_state['page'] = 'Home'


def set_interaction_page():
    st.session_state['page'] = 'Interaction'


def set_account_page():
    st.session_state['page'] = 'account'


def clear_prompt_input():
    st.session_state['prompt_input'] = ""


if __name__ == "__main__":
    main()
