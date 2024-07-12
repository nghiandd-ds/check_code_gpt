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

text = 'THIS IS A TEST'
def create_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, text)
    c.save()
    buffer.seek(0)
    return buffer

if st.button("Generate PDF"):
    pdf = create_pdf()
    st.download_button(
        label="Download PDF",
        data=pdf,
        file_name="example.pdf",
        mime="application/pdf"
    )





