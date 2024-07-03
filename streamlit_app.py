import streamlit as st
from openai import OpenAI
import numpy as np
import pandas as pd
import os
#from pathlib import Path

st.write("""
# Check code
""")

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")



if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.")
    st.stop()
    
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

# Create agent if not exist
if "Check code Assistant" in ([i.name for i in client.beta.assistants.list().data]) == True:
    Coder = "asst_HqchrsdI82apAEzoXU2KGygS"
Coder = client.beta.assistants.create(
  name="Check code Assistant",
  instructions="You are an expert in coding and specialize in python and relevent packages. \
                Your job is to read and understand codes of junior-level employees and then, explain it briefly and correctly to \
                manager who is trained as a data scientist but not specialized in coding",
  model="gpt-3.5-turbo-0125").id

# ChatGPT promt
promt = """
      Using the attached file, your manager have given you two jobs. 
      First, answer in a form she have given to you information about the code. In case code have no information about that you are asked, 
      please answer that 'not given' or 'no information'.
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
        Second, you have to make a table that separate the main code and explain it side-by-side so manager could follow. 
        The table should have at least the copy of the code that explained and explaination.

        You must write a report that contain answers for all of manager's questions.
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
    instructions="Please only return the final report."
)

while my_run.status in ["queued", "in_progress"]:
    keep_retrieving_run = client.beta.threads.runs.retrieve(
        thread_id=my_thread.id,
        run_id=my_run.id
    )
    #print(f"Run status: {keep_retrieving_run.status}")

    if keep_retrieving_run.status == "completed":
        print("\n")

        # Step 7: Retrieve the Messages added by the Assistant to the Thread
        all_messages = client.beta.threads.messages.list(
            thread_id=my_thread.id
        )

        st.text("------------------------------------------------------------ \n")

        #print(f"User: {my_thread_message.content[0].text.value}")
        st.text(body=all_messages.data[0].content[0].text.value)
        st.text("------------------------------------------------------------ \n")
        break
    elif keep_retrieving_run.status == "queued" or keep_retrieving_run.status == "in_progress":
        pass
    else:
        print(f"Run status: {keep_retrieving_run.status}")
        break
