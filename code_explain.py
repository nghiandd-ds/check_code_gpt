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
                  2. Make notes and comments on code as following best practice and coding standards.
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
#######
# PDF function

pdfmetrics.registerFont(TTFont('Arial', "arial.ttf"))

def seprate_table(text, sep='|'):
    first_v = text.find(sep)
    last_v = text.rfind(sep)+1
    if first_v != -1 and last_v != 0:
        return [text[:first_v], text[first_v:last_v], text[last_v:]]
    else:
        return [text]

def split_code(code, sep = '|'):
    case_1 = f"){sep}("
    case_2 = f") {sep} ("
    code = code.replace(case_1, '_TOKEN_PLACE_HOLDER_1_')
    code = code.replace(case_2, '_TOKEN_PLACE_HOLDER_2_')
    a = code.split(sep)
    return [org.replace('_TOKEN_PLACE_HOLDER_1_', case_1).replace('_TOKEN_PLACE_HOLDER_2_', case_2) for org in a]

def process_table(text, doc, sep='|'):
    '''
    Code to make table form text with a type of separation between columns.
    Input: 
        - text: content to make table
        - sep: how to separate text for table columns
        - doc: the ouput document that table go to
    '''
    list_of_token = [t for t in split_code(text) if (t != '<br/>') and (t.strip() != '') and (t != '/n')]
    
    code_part = []
    code = []
    exp = []
    for i in range(0, len(list_of_token)//3):
        code_part.append(list_of_token[3*i])
        code.append(list_of_token[1 + 3*i])
        exp.append(list_of_token[2 + 3*i])

    # Font style
    header_style = ParagraphStyle(
            'HeaderStyle',
            fontName='Arial',
            fontSize=12,
            textColor=colors.whitesmoke,
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
    body_style = ParagraphStyle(
            'BodyStyle',
            fontName='Arial',
            fontSize=10,
            leading=10,
            alignment=TA_LEFT
        )
    
    # Create data for table
    formatted_data = [
            [Paragraph(cell, header_style) for cell in np.array([code_part, code, exp]).T.tolist()[0]]] + [
            [Paragraph(cell, body_style) for cell in row] for row in np.array([code_part, code, exp]).T.tolist()[1:]]
    
    # Create the table
    available_width = A4[0] - doc.leftMargin - doc.rightMargin    
    # Create the table with adjusted column widths
    col_widths = [available_width * 0.2, available_width * 0.3, available_width * 0.5]
    table = Table(formatted_data, colWidths=col_widths)
    # Add style to the table
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ])    
    table.setStyle(style)
    return table

def make_pdf(text):
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
    text_ = '<br/><br/>'.join([i.replace('\n', '<br/>').replace('<br>', '<br/>') for i in text])
    normal_style = ParagraphStyle(
            'NormalStyle',
            fontName='Arial',
            fontSize=10,
            leading=12
        )
    header_style = ParagraphStyle(
                'HeaderStyle',
                fontName='Arial',
                fontSize=20,
                alignment=TA_CENTER,
                spaceAfter=36)
    doc.title = "Code Quality Report"
    format_text = []
    align_text = seprate_table(text_, sep='|')
    if len(align_text) == 3:
        align_text =[Paragraph('Code Quality Report',  header_style),
                    Paragraph(align_text[0], normal_style),
                    process_table(align_text[1], doc, sep='|'),
                    Paragraph(align_text[2], normal_style)]
    else:
        align_text = [Paragraph('Code Quality Report',  header_style), Paragraph(align_text[0], normal_style)]
    
    doc.build(align_text)
    buffer.seek(0)
    return buffer



#######
# ChatGPT query
Message = "Given the following code:"

explain_code_query = '''
Task: Explain the code by the format:
1. Code purpose
2. Code breakdown:
- Input
- Output
- Explain the code by table |code | explaination
'''


add_comments = '''
Task: Add comments to the code so it follow best practice and readable. Also add brief informations about usage if the code is a function in the code. Remember to add some tips on how to explain the code for non-coder.
'''

optimization = '''
Task: Optimize the code for better accuracy and performance. Only return the code and reason for optimization.
'''

col_1, col_2 = st.columns([1, 3])
st.markdown("""
<style>
    [data-testid="column"]:nth-of-type(1) {
        position: fixed;
        top: 5rx;
    }
    
    [data-testid="column"]:nth-of-type(2) {
        position: static;
        padding-left: 35%;
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
    user_input = st.text_area("Enter your code here", height=200)
    sub_col_1, sub_col_2, sub_col_3 = st.columns([1, 3, 1])
    with sub_col_1:
        explain_button =  st.button("Explain code")
    with sub_col_2:
        comment_button =  st.button("Add comments")    
    with sub_col_3:
        optimize_button =  st.button("Optimization")  
with col_2:
    # Add content to the scrollable column using st.markdown
    if user_input and explain_button:
        query_ = Message + "/n/n" + user_input  + "/n/n" + explain_code_query
        text = ask(client, query_)
        
        buffer = make_pdf(text)
        @st.experimental_fragment
        def download_file():
            st.download_button(
                    label="Download PDF",
                    data=buffer,
                    file_name="report.pdf",
                    mime="application/pdf"
                )
        download_file()    
        
        for t in text:
            st.markdown(t)
        st.stop()
        
    if user_input and comment_button:
        query_ = Message + "/n/n" + user_input  + "/n/n" + add_comments
        text = ask(client, query_)
        
        buffer = make_pdf(text)
        @st.experimental_fragment
        def download_file():
            st.download_button(
                    label="Download PDF",
                    data=buffer,
                    file_name="report.pdf",
                    mime="application/pdf"
                )
        download_file()  
        
        for t in text:
            st.markdown(t)
        st.stop()

    if user_input and optimize_button:
        query_ = Message + "/n/n" + user_input  + "/n/n" + optimization
        text = ask(client, query_)
        
        buffer = make_pdf(text)
        @st.experimental_fragment
        def download_file():
            st.download_button(
                    label="Download PDF",
                    data=buffer,
                    file_name="report.pdf",
                    mime="application/pdf"
                )
        download_file()
        
        for t in text:
            st.markdown(t)
        st.stop()
st.stop()














