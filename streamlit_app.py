import streamlit as st
from openai import OpenAI
import numpy as np
import pandas as pd
import os
#from pathlib import Path

st.write("""
# Check code
""")

def decoding(encryted_key, password):
    password = [eval(i) for i in password.split('-')]
    key = [i for i in encryted_key]
    combine_key = pd.DataFrame({
        'index' : password,
        'encryted_key': key
    }).sort_values('index')
    return ''.join(combine_key['encryted_key'])

#with st.sidebar:
#    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")

openai_api_key = decoding('FSeeODhu-tBjpc9j-cM0iJtRRo3rkona7nXEHKk9sWk3bCPI63TrnTlB', '35-21-17-37-41-42-56-47-8-54-16-7-4-10-50-18-3-38-28-55-11-36-45-13-9-19-44-25-39-6-53-43-27-12-40-20-24-14-34-15-1-26-2-30-33-49-46-22-51-23-29-5-48-52-32-31')

#if not openai_api_key:
#    st.info("Please add your OpenAI API key to continue.")
#    st.stop()
    
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
  instructions="You are an expert in coding and specialize in python and relevent packages. \
                Your job is to read and understand codes of junior-level employees and then, explain it briefly and correctly to \
                manager who is trained as a data scientist but not specialized in coding",
  model="gpt-3.5-turbo-0125", tools=[{"type": "code_interpreter"}]).id

# ChatGPT promt
promt = """
      Using the attached file, your manager have given you two jobs. 
      First is task 1, you have to answer in a form she have given to you information about the code. In case code have no information about that you are asked, 
      please let the answer as blank.
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
          
        Second is task 2, you have add to the report explaination all of the code so manager could follow as a formated table for pdf file. The format of the table are given:
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
    instructions="""The final report must meet the following requirements:
            1. All tasks are reported in PDF file.
            2. Task 2 have to be present a table in the pdf file.
            3. Only return the final report."""
)

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

        st.text("------------------------------------------------------------ \n")

        #print(f"User: {my_thread_message.content[0].text.value}")
        # print in reverse order => first answer go first
        for txt in all_messages.data[::-1]:
            if txt.role == 'assistant':
                st.text(body=txt.content[0].text.value)
                try:
                    download_id=txt.attachments[0].file_id
                    file_data = client.files.content(download_id)
                    st.download_button(
                        label="Download data as CSV",
                        data=file_data
                    )
                except:
                    next
        st.text("------------------------------------------------------------ \n")
        break
    elif keep_retrieving_run.status == "queued" or keep_retrieving_run.status == "in_progress":
        pass
    else:
        print(f"Run status: {keep_retrieving_run.status}")
        break
# Delete file and agent
#client.files.delete(gpt_file)
#client.beta.assistants.delete(Coder)
#client.beta.threads.delete(my_thread.id)
del openai_api_key

