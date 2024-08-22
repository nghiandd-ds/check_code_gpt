import streamlit as st
import openai
from openai import OpenAI
import numpy as np
import pandas as pd
import os
from io import BytesIO
import markdown2
import markdown
import pdfkit

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

def ask(client, mess, model="gpt-4o-mini-2024-07-18"):
    #### QUERY CHATGPT ####
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": mess}])
    text = []

    # print in reverse order => first answer go first
    for txt in response.choices[::-1]:
            text.append(txt.message.content)
    return text
    
#######
# PDF function
def convert_markdown_to_pdf(markdown_text):

    buffer = BytesIO()
    styles = getSampleStyleSheet()

    
    html_content = "<html><body>"
    html_content += markdown.markdown(markdown_text)
    html_content += "</body></html>"
    
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    doc.title = "Report"
    # Generate PDF from the combined HTML using BytesIO
    doc.build(Paragraph(html_content))
    buffer.seek(0)
    
    return buffer

    
#######
# ChatGPT query
Message = """
As an expert in coding and specialize in python and relevent packages, you have 2 jobs:
    1. Explain the code for non-coder employees and managers.
    2. Make notes and comments on code as following best practice and coding standards.
Given the following code:
"""

explain_code_query = '''
Task: Explain the code by the format:
1. Code purpose
2. Code breakdown:
- Input
- Output
- Explain the code by table |code | explaination
'''


add_comments = '''
Task: Add comments to the code so it follow best practice and readable. Remember to format and indent the code. 
Also add brief informations about usage if there are functions in the code.
'''

optimization = '''
Task: Optimize the code for better accuracy and performance. Only return the code and reason for optimization.
'''

logic_code = '''
Task: Check if the code is suitable for the intented purpose/logic that given below. Only give brief answer and short reason on how the code is or is not.
Make sure to highlight the result suitable or not.
'''
col_1, col_2 = st.columns([1, 2.5])
st.markdown("""
<style>
    [data-testid="column"]:nth-of-type(1) {
        position: fixed;
        top: 0.5rx;
    }
    
    [data-testid="column"]:nth-of-type(2) {
        position: static;
        padding-left: 38%;
        top: 50rx;
    }
</style>
""", unsafe_allow_html=True)

with col_1:
    # Add Streamlit components to the fixed column
    st.markdown("""
    <h1>Code explainer</h1>
        <p><i>LLM can make mistakes. Check important info.</i></p>
    """, unsafe_allow_html=True)
        
    user_input = st.text_area("Enter your code here", height=200, key='user_input')
    
    sub_col_3, sub_col_4 = st.columns(2)
    with sub_col_3:
        explain_button =  st.button("Explain code")
        comment_button =  st.button("Add comments")    
        
    with sub_col_4:
        optimize_button =  st.button("Optimization")  
        logic_button = st.button("Check logic")
with col_2:
    # Add content to the scrollable column using st.markdown
    if user_input and explain_button:
        query_ = Message + "/n/n" + user_input  + "/n/n" + explain_code_query
        text = ask(client, query_)
        st.markdown('/n/n'.join(text))
        st.stop()
        
    if user_input and comment_button:
        query_ = Message + "/n/n" + user_input  + "/n/n" + add_comments
        text = ask(client, query_)
        st.markdown('/n/n'.join(text))
        st.stop()
        
    if user_input and optimize_button:
        query_ = Message + "/n/n" + user_input  + "/n/n" + optimization
        text = ask(client, query_)
        st.markdown('/n/n'.join(text))
        st.stop()
        
    if 'submit_logic_clicked' not in st.session_state:
        st.session_state.submit_logic_clicked = False
    
    if user_input and logic_button:
        st.markdown("#IMPORTANT: This is a alpha version. Some of the intented function might not work!")
        @st.experimental_fragment
        def logic_checker():
            code_purpose = st.text_area("Describe code's purpose/logic", height=150, key="code_purpose")
            st.markdown(st.session_state.user_input)
            @st.experimental_fragment
            def check_button():
                if st.button("Check") and code_purpose:
                    query_ = Message + "/n/n" + st.session_state.user_input + "/n/n" + logic_code + '/n/n' + "Purpose/Logic: " +  st.session_state.code_purpose
                    st.markdown(query_)
                    text = ask(client, query_)
                    st.markdown('/n/n'.join(text))
                    st.stop()
            check_button()  
        logic_checker()
        st.stop()
st.stop()














