import streamlit as st

# Custom CSS for better UI and wider layout
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


def interaction_page():
    # Page Title
    st.markdown("<h1>🤖 Interact with the Pool of Tools</h1>", unsafe_allow_html=True)

    # Horizontal Divider
    st.markdown("<hr>", unsafe_allow_html=True)

    # Centered input prompt with larger text and padding for better visual appearance
    st.markdown("<h3 style='text-align: center;'>📝 What's your task for the Pool of Tools?</h3>", unsafe_allow_html=True)

    # Input prompt centered in a column
    col1, col2, col3 = st.columns([0.25, 1, 0.25])  # Adjust columns for better centering and full-width input
    with col2:
        prompt = st.text_input(
            "Enter your prompt:",
            placeholder="E.g., Analyze this document or generate a financial report...",
            help="Provide a specific prompt to get the best results.",
        )

    st.markdown("<br>", unsafe_allow_html=True)  # Adds some space after input

    # Always display Submit and Go Back buttons
    col1, col2, col3 = st.columns([0.25, 1, 0.25])  # Adjust column widths for centering buttons
    with col2:
        # Submit Button
        submit_button = st.button("🚀 Submit", key="submit")
        if submit_button:
            if prompt:  # Ensure the prompt is not empty
                st.write(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>:",result)
                print(">>>>>>>>>>>>>>>>>",result)
                # Display a spinner while processing the request
                with st.spinner("🤖 Processing your request..."):
                    result = process_request(prompt)  # Call the function with the prompt
                    # Display the result after processing
                    st.success(f"✅ Response for your prompt: {result}")
                    st.write(f"Response: {result}")
            else:
                st.error("❌ Please enter a valid prompt before submitting.")

        # Go Back Button
        go_back_button = st.button("⬅️ Go Back", key="go_back")
        if go_back_button:
            st.session_state['page'] = 'home'

    # Additional styling and spacing for better appearance
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Footer
    st.markdown("<h4>Powered by Pool of Tools</h4>", unsafe_allow_html=True)

def process_request(prompt):
    st.write(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>:",result)
    print(">>>>>>>>>>>>>>>>>",result)
    # This is a placeholder for the actual logic of processing the prompt
    # Replace this with the actual code that handles the prompt
    return f"Processed result for: {prompt}"  # Example response

def home():
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
        get_started_button = st.button("Let's get started!")
        if get_started_button:
            interaction_page()
            st.session_state['page'] = 'interaction'