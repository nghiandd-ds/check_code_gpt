import streamlit as st
import openai
from openai import OpenAI
import numpy as np
import pandas as pd
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_LEFT, TA_CENTER

st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Call out OPENAI
def decoding(encryted_key, password):
    password = [eval(i) for i in password.split('-')]
    key = [i for i in encryted_key]
    combine_key = pd.DataFrame({
        'index' : password,
        'encryted_key': key
    }).sort_values('index')
    return ''.join(combine_key['encryted_key'])

openai_api_key = decoding('FSeeODhu-tBjpc9j-cM0iJtRRo3rkona7nXEHKk9sWk3bCPI63TrnTlB', '35-21-17-37-41-42-56-47-8-54-16-7-4-10-50-18-3-38-28-55-11-36-45-13-9-19-44-25-39-6-53-43-27-12-40-20-24-14-34-15-1-26-2-30-33-49-46-22-51-23-29-5-48-52-32-31')
client = OpenAI(api_key=openai_api_key)

def ask(client, mess):
    #### QUERY CHATGPT ####
    
    # Create OpenAI agent
    Coder = client.beta.assistants.create(
              name="Check code Assistant",
              instructions="""You are an expert in coding and specialize in python and relevent packages. You have 2 jobs:
                  1. Explain the code for non-coder employees and managers.
                  2. Make comments on code as following best practice and coding standard so junior developer could learn from it.
                """,
              model="gpt-4o-mini-2024-07-18", tools=[{"type": "code_interpreter"}]).id
    
    # Create thread
    my_thread = client.beta.threads.create(
      messages=[
        {
            "role": "user",
            "content": [
                            {"type": "text", "text": mess}
            ],
        }
      ]
    )
    
    # Run
    my_run = client.beta.threads.runs.create(
        thread_id = my_thread.id,
        assistant_id = Coder,
    )
    
    text = []
    while my_run.status in ["queued", "in_progress"]:
        keep_retrieving_run = client.beta.threads.runs.retrieve(
            thread_id=my_thread.id,
            run_id=my_run.id
        )
        print(f"Run status: {keep_retrieving_run.status}")
    
        if keep_retrieving_run.status == "completed":
            print("\n")
    
            all_messages = client.beta.threads.messages.list(
                thread_id=my_thread.id
            )
    
            print("------------------------------------------------------------ \n")
            # print in reverse order => first answer go first
            for txt in all_messages.data[::-1]:
                if txt.role == 'assistant':
                    text.append(txt.content[0].text.value)
            print("------------------------------------------------------------ \n")
            break
        elif keep_retrieving_run.status == "queued" or keep_retrieving_run.status == "in_progress":
            pass
        else:
            print(f"Run status: {keep_retrieving_run.status}")
            break
    client.beta.threads.delete(my_thread.id)
    client.beta.assistants.delete(Coder)
    return text


Message = "Given the following code:"

Question = '''
Question: Explain the code by the format:
1. Code purpose
2. Code breakdown:
- Input
- Output
- Explain the code by table |code | explaination
'''

st.markdown("""
    <style>
    .container {
        display: flex;
        flex-direction: row;
    }

    .fixed-column {
        width: 33%;
        position: fixed;
        height: 100vh;
        background-color: #f4f4f4;
        padding: 10px;
    }

    .scrollable-column {
        margin-left: 33%; /* Offset by the width of the fixed column */
        padding: 10px;
        width: calc(100% - 33%);
    }

    /* Style for the specific button */
    .stButton > button[kind="secondary"] {
        position: fixed;
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        cursor: pointer;
    }
    .stButton > button[kind="secondary"]:hover {
        background-color: #45a049;
    }

    /* Style for the specific text area */
    .custom-text-area textarea {
        position: fixed;
        width: 33%;
    }
    </style>
""", unsafe_allow_html=True)

col_1, col_2 = st.columns([1, 2])

with col_1:
    st.markdown('<div class="custom-text-area">', unsafe_allow_html=True)
    # Add Streamlit components to the fixed column
    st.markdown('<div class="custom-text-area">', unsafe_allow_html=True)
    text = st.text_area("Your text area")
    st.markdown('</div>', unsafe_allow_html=True)
    
    explain_button =  st.button("Custom Button", key="custom_button", type="secondary")

with col_2:
    # Continue the HTML structure for the scrollable column
    st.markdown("""
            </div>
            <div class="scrollable-column">
                <h3>Scrollable Column</h3>
    """, unsafe_allow_html=True)
    
    # Add content to the scrollable column using st.markdown
    if text and explain_button:
        for i in range(1, 101):
            st.markdown(f"<p class='scrollable-column'>Scrollable content line {i}</p>", unsafe_allow_html=True)
    
    # Close the HTML tags
    st.markdown("""
            </div>
    """, unsafe_allow_html=True)


















