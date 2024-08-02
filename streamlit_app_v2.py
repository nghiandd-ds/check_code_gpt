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

st.write("""
# Check code
""")
st.markdown("LLM can make mistakes. Check important info.")

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


# upload file by streamlit
uploaded_file = st.file_uploader("Upload code")
if not uploaded_file:
    st.stop()  

    

  
# Connect to Openai API
client = OpenAI(api_key=openai_api_key)


# Upload file to OpenAI and take ID
gpt_file = client.files.create(
    file=uploaded_file,
    purpose='assistants').id


# Create agent
Coder = client.beta.assistants.create(
  name="Check code Assistant",
  instructions="You are an expert in coding and specialize in python and relevent packages. Your job is to read and understand codes of junior-level employees and then, explain it briefly and correctly to manager who is trained as a data scientist but not specialized in coding",
  model="gpt-3.5-turbo-0125", tools=[{"type": "code_interpreter"}]).id

# ChatGPT promt
promt_1 = """
        "Task Code Information". Using attached file to answer in a form she have given to you information about the attached code. 
        In case code have no information about that you are asked, please let the answer as ''. 
        The form as follow. You must keep the format of this form:
          01. Code's name:
          02. Code maker:
          03. Created date:
          04. Code's version:
          05. Log changes:
          06. Active status:
          07. System requirements:
          08. Code's objectives:
          09. Code's application:
          10. Code's input:
          11. Code's output:
          12. References:
          13. Code checker:
          14. Notes:
        Never return a table for this task.
"""

promt_2 = """
    "Task Code explaination". You have to explain all of the code so manager could follow as a formated table. 
        The format of the table are given:
            1. Each row of the table are each parts/functions of the code. Rows must cover all of the code to the last line.
            2. There are 3 columns in the table as follow:
                    - First column: code's part.
                    - Second column: The code content in the part in first column. This columns must be exact copy code from attached file.
                    - Third column: Explaination of the code in second column.
        Your explaination must cover all of the code and explainations should be added side-by-side to the code so manager could understand.
"""

# Create thread
my_thread = client.beta.threads.create(
  messages=[
    {
        "role": "user",
        "content": [
                        {"type": "text", "text": promt_1}, 
                        {"type": "text", "text": promt_2}, 
        ],
        "attachments": [
                {
                  "file_id": gpt_file,
                  "tools": [{"type": "code_interpreter"}]
                }
        ]
    }
  ]
)

# Run
my_run = client.beta.threads.runs.create(
    thread_id = my_thread.id,
    assistant_id = Coder,
    max_prompt_tokens = 10000,
    max_completion_tokens = 16000,
    instructions="""
            Only return the final report to the manager. Especially do not give her un-finsihed product. Use '|' notation to separate columns in table. And do not 
            """
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
         
client.files.delete(gpt_file)
client.beta.assistants.delete(Coder)
client.beta.threads.delete(my_thread.id)
del openai_api_key      

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



