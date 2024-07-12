import streamlit as st
from openai import OpenAI
import numpy as np
import pandas as pd
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

st.write("""
# Check code
""")
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

st.text("Processing")    
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
promt = """
      Using the attached file, your manager have given you two jobs. 
      First is task 1, you have to answer in a form she have given to you information about the attached code. 
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
          
        Second is task 2, you have to explain all of the code so manager could follow as a formated table. 
        The format of the table are given:
            1. Each row of the table are each part of the code. Rows must cover all of the code, from the first line to the last line.
            2. There are 3 columns in the table as follow:
                    - First column: code's part.
                    - Second column: The code content in the part in first column. This columns must be exact copy code from attached file.
                    - Third column: Explaination of the code in second column.
        Your explaination must cover all of the code and explainations should be added side-by-side to the code so manager could understand.
        
        You must write a report that contain answers for all of manager's questions. Both jobs have to be delivered at the same time. 

        """

# Create thread
my_thread = client.beta.threads.create()

# add message
my_thread_message = client.beta.threads.messages.create(
  thread_id=my_thread.id,
  role = "user",
  content = promt,
  attachments = [{ "file_id": gpt_file, "tools": [{"type": "code_interpreter"}]}]
)

# Run
my_run = client.beta.threads.runs.create(
    thread_id = my_thread.id,
    assistant_id = Coder,
    max_prompt_tokens = 10000,
    max_completion_tokens = 16000,
    instructions="""
    Only return the final report to the manager. Especially do not give her un-finsihed product.
            """
)

text = ''
while my_run.status in ["queued", "in_progress"]:
    keep_retrieving_run = client.beta.threads.runs.retrieve(
        thread_id=my_thread.id,
        run_id=my_run.id
    )
    #print(f"Run status: {keep_retrieving_run.status}")

    if keep_retrieving_run.status == "completed":
        print("\n")

        all_messages = client.beta.threads.messages.list(
            thread_id=my_thread.id
        )

        print("------------------------------------------------------------ \n")
        # print in reverse order => first answer go first
        for txt in all_messages.data[::-1]:
            if txt.role == 'assistant':
                st.text(txt.content[0].text.value)
                text = text + (txt.content[0].text.value) + "\n"
        print("------------------------------------------------------------ \n")
        break
    elif keep_retrieving_run.status == "queued" or keep_retrieving_run.status == "in_progress":
        pass
    else:
        print(f"Run status: {keep_retrieving_run.status}")
        break

def create_pdf():
    buffer = BytesIO(text)
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, text)
    c.save()
    buffer.seek(0)
    return buffer

if st.button("Generate PDF"):
    pdf = create_pdf(text)
    st.download_button(
        label="Download PDF",
        data=pdf,
        file_name="example.pdf",
        mime="application/pdf"
    )





