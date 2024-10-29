import streamlit as st
import re
import json
import requests
from streamlit_option_menu import option_menu
import firebase_admin
from firebase_admin import credentials, auth
import os
from dotenv import load_dotenv
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

load_dotenv()

if not firebase_admin._apps:
    cred = credentials.Certificate(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))
    firebase_admin.initialize_app(cred)

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
    payload = json.dumps({"email": user_name, "password": password, "return_secure_token": return_secure_token})
    rest_api_url = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
    response = requests.post(rest_api_url, params={"key": st.session_state['Firebase_API_key']}, data=payload)
    if response:
        return response.json()
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
        valid_name = check_name(name_sign_up=name_sign_up)

        email_sign_up = st.text_input("Email *", placeholder='user@gmail.com')
        valid_email = check_email(email_sign_up=email_sign_up)
        uniq_email = check_uniq_email(email_sign_up=email_sign_up)

        username_sign_up = st.text_input("Username *", placeholder='test1234')
        valid_username = check_username(username_sign_up=username_sign_up)
        uniq_username = check_uniq_username(username_sign_up=username_sign_up)

        password_sign_up = st.text_input("Password *", placeholder='Create a strong password', type='password')

        st.markdown("###")
        sign_up_submit_button = st.form_submit_button(label='Register')

        if sign_up_submit_button:
            if not valid_name:
                st.error("Please enter a valid name")
            elif not valid_email:
                st.error("Please enter a valid email address")
            elif not uniq_email:
                st.error("Email already exists!")
            elif not valid_username:
                st.error("Please enter a valid username")
            elif not uniq_username:
                st.error(f'Sorry, username {username_sign_up} already exists!')

            if valid_name and valid_email and uniq_email and valid_username and uniq_username:
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

def navbar() -> None:
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


def navbar1() -> None:
    main_navbar = st.empty()
    with main_navbar:
        selected = option_menu(
            menu_title=None,
            default_index=0,
            options=['Profile', 'Change Password'],
            icons=['person-circle', 'arrow-repeat'],
            orientation="horizontal",
            styles={
                "container": {"padding": "0!important", "background-color": "#333333"},
                "icon": {"color": "white", "font-size": "18px"},
                "nav-link": {
                    "font-size": "18px", 
                    "text-align": "left", 
                    "margin": "0px", 
                    "color": "white", 
                    "--hover-color": "#444444"
                },
                "nav-link-selected": {"background-color": "black"},
            }
        )
        return selected


def build_login_ui():
    if st.session_state.get('log_in', False) == False:
        selected = navbar()

        if selected == 'Login':
            login_page()
        st.rerun
        
        if selected == 'Create Account':
            sign_up_widget()

        if selected == 'Forgot Password':
            forgot_password()

        if selected == 'Reset Password' and st.session_state.get('reset_code_sent', False):
            st.session_state['reset_code_sent']
            reset_password()

        return st.session_state['log_in']
    else:
        selected = navbar1()

        if selected == 'Profile':
            logout_widget()

        if selected == 'Change Password':
            change_password()


# from tools.setup import db, auth
# import streamlit as st
# from tools.home import home

# def register_user(email, password, username):
#     try:
#         # Create a user with Firebase Authentication
#         user = auth.create_user(
#             email=email,
#             password=password
#         )
#         print(f"Successfully created new user: {user.uid}")

#         # Store additional user data in Firestore
#         user_data = {
#             'username': username,
#             'email': email,
#             'uid': user.uid
#         }
#         db.collection('users').document(user.uid).set(user_data)
#         print(f"User data saved for {username}")
#         return True
#     except Exception as e:
#         print(f"Error creating user: {e}")
#         return False

# # Function to verify a user's login
# def verify_user(email, password):
#     try:
#         # Fetch user details (Firebase Admin SDK doesn't handle login directly)
#         user = auth.get_user_by_email(email)
#         print(f"Successfully fetched user: {user.uid}")
#         return True, user
#     except Exception as e:
#         print(f"Error fetching user: {e}")
#         return False, None

# def login_page():
#     st.title("Pool of Tools (POT)")

#     # Create a simple selectbox to switch between login and register
#     option = st.selectbox("Choose an option", ("Login", "Register"))

#     if option == "Register":
#         st.subheader("Register a New Account")

#         # Input fields for registration
#         email = st.text_input("Email")
#         username = st.text_input("Username")
#         password = st.text_input("Password", type="password")

#         if st.button("Register"):
#             # Register user
#             if email and username and password:
#                 success = register_user(email, password, username)
#                 if success:
#                     st.success(f"User '{username}' registered successfully!")
#                 else:
#                     st.error("Error registering user.")
#             else:
#                 st.error("Please fill out all fields.")

#     elif option == "Login":
#         st.subheader("Login to Your Account")

#         # Input fields for login
#         email = st.text_input("Email")
#         password = st.text_input("Password", type="password")

#         if st.button("Login"):
#             # Verify user
#             if email and password:
#                 success, user = verify_user(email, password)
#                 if success:
                    
#                     username = user.email.split("@")[0]
#                     print("-username",username)
#                     st.session_state['logged_in'] = True
#                     st.session_state['username'] = username
#                     st.success(f"User '{user.email}' logged in successfully!")
#                     st.rerun()
#                 else:
#                     st.error("Invalid email or password.")
#             else:
#                 st.error("Please fill out all fields.")

# def logout():
#     st.session_state['logged_in'] = False
#     st.session_state['username'] = None
#     st.experimental_rerun()

# if 'logged_in' not in st.session_state:
#     st.session_state['logged_in'] = False

# if 'username' not in st.session_state:
#     st.session_state['username'] = None

# if not st.session_state['logged_in']:
#     login_page()
# else:
#     home()