import streamlit as st
from streamlit_option_menu import option_menu
st.set_page_config(page_title="PoolofTools", page_icon=":material/picture_as_pdf:")
from langchain.callbacks import StreamingStdOutCallbackHandler
from langchain_community.chat_models import ChatOpenAI, ChatOllama
# from langchain_ollama import OllamaLLM
from prompt import TOOL_MAKER_PROMPT
from main import MainAgentWithTools

import util
from langchain.tools import Tool
from langchain.agents.agent_toolkits import FileManagementToolkit

from langchain.utilities import GoogleSearchAPIWrapper

from tools.toolRegistration import tool_registration_tool, query_available_modules
from tools.queryTool import tool_query_tool
from tools.browsingTool import paged_web_browser
from tools.liabraryInstallation import verify_and_install_library
from tools import login
from tools.home import home


util.load_secrets()

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
<<<<<<< HEAD
# tool_making_agent.receive("HumanUser", "can you please a create an tool that can create an bounding box around title(headers) of the image")

# tool_making_agent.send()

if 'log_in' not in st.session_state:
    st.session_state['log_in'] = False
=======
tool_making_agent.receive("HumanUser", "create an tool which can convert pdf into images")
>>>>>>> 9ee291dd07920efb160000191c4b3fd75fa73982

class PdfBot:
    def run():
        with st.sidebar:
            app = option_menu(
                menu_title='PoolofTools',
                options=['Home', 'My Tools', 'My Account'],
                icons=['house-fill', 'chat-left-text-fill', 'files', 'person-circle'],
                menu_icon='filetype-pdf',
                default_index=0,
                styles={
                    "container": {"padding": "0!important", "background-color": "#333333"},
                    "menu-icon": {"color": "white", "font-size":"34px"},
                    "menu-title": {"font-size":"34px", "text-align": "center", "font-weight":"bold", "color": "white"},
                    "icon": {"color": "white", "font-size": "22px"},
                    "nav-link": {"font-size": "18px", "text-align": "left", "margin":"0px", "--hover-color": "#444444", "color": "white"},
                    "nav-link-selected": {"background-color": "black"},
                    "title": {"font-size":"24px", "color": "white"}
                }
            )

<<<<<<< HEAD
        # Navigation logic
        if app == "Home":
            home()
        elif app == "My Tools":
            pass
        elif app == 'My Account':
            login.account()

    run()
=======
# # Set session state for login status if not already set
# if 'logged_in' not in st.session_state:
#     st.session_state['logged_in'] = False  # Default to False if not logged in

# # Function to handle user login or redirect to the home page
# def handle_login():
#     print("st.session_state['logged_in']",st.session_state['logged_in'])
#     if not st.session_state['logged_in']:
#         login.login_page()  # This function should handle login and set st.session_state['logged_in'] = True
#     else:
#         home()  # This function should display the home page once logged in

# # Run the login/home page logic
# handle_login()

# class PdfBot:
#     def run():
#         with st.sidebar:
#             app = option_menu(
#                 menu_title='PoolofTools',
#                 options=['Home', 'My Tools', 'My Account'],
#                 icons=['house-fill', 'chat-left-text-fill', 'files', 'person-circle'],
#                 menu_icon='filetype-pdf',
#                 default_index=0,
#                 styles={
#                     "container": {"padding": "0!important", "background-color": "#333333"},
#                     "menu-icon": {"color": "white", "font-size":"34px"},
#                     "menu-title": {"font-size":"34px", "text-align": "center", "font-weight":"bold", "color": "white"},
#                     "icon": {"color": "white", "font-size": "22px"},
#                     "nav-link": {"font-size": "18px", "text-align": "left", "margin":"0px", "--hover-color": "#444444", "color": "white"},
#                     "nav-link-selected": {"background-color": "black"},
#                     "title": {"font-size":"24px", "color": "white"}
#                 }
#             )

#         # Navigation logic
#         if app == "Home":
#             home()
#         elif app == "My Tools":
#             pass
#         elif app == 'My Account':
#             login.account()

#     run()
>>>>>>> 9ee291dd07920efb160000191c4b3fd75fa73982
