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

Message = "Given the following code:"

Question = '''
Question: Explain the code by the format:
1. Code purpose
2. Code breakdown:
- Input
- Output
- Explain the code by table |code | explaination
'''


# Create two columns, the first one will be used for the input text
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("""<div class="fixed-side">
    <h1>Code explainer</h1>
    <p><i>LLM can make mistakes. Check important info.</i></p>
    """, 
                unsafe_allow_html=True)
    st.write("Code explainer")
    st.markdown("LLM can make mistakes. Check important info.")
    user_input = st.text_area("Enter your code here:", height=270)
    submit_button = st.button('Explain code')
    
    st.markdown('</div>', unsafe_allow_html=True)

# Custom CSS to freeze the left column
st.markdown(
    """
    <style>
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        position: sticky;
        top: 3rem;
        align-self: start;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# You can use col2 for any other content you'd like to place on the right side
with col2:
    st.write("")
    # Define the button and check if it has been clicked
    if submit_button and user_input:
        mess = Message + "/n/n" + user_input  + "/n/n" + Question
        print(mess)
        #### QUERY CHATGPT ####
        
        # Create OpenAI agent
        Coder = client.beta.assistants.create(
                  name="Check code Assistant",
                  instructions="You are an expert in coding and specialize in python and relevent packages. Your job is to read and understand codes of junior-level employees and then, explain it briefly and correctly to manager who is trained as a data scientist but not specialized in coding",
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
        for t in text:
            print(t)
            st.markdown(t)
    st.stop()
    client.beta.threads.delete(my_thread.id)
    client.beta.assistants.delete(Coder)
             
    #        return text

    














