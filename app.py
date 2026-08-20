import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from PIL import Image
import json
from datetime import datetime

# Page Title
st.set_page_config(page_title="QC Image to Sheet", page_icon="📋")
st.title("📷 QC Data Extractor to Google Sheet")

# 1. Credentials Setup
try:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("fress inword qc").sheet1

    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    st.success("System Ready!")
except Exception as e:
    st.error(f"Setup Error: {e}")

# 2. Image Uploading & Processing
uploaded_file = st.file_uploader("Upload QC Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Photo", use_column_width=True)
    
    if st.button("Process & Save to Sheet"):
        with st.spinner("Extracting Data..."):
            try:
                prompt = """
                Extract data from image into JSON:
                {
                    "DATE": "YYYY-MM-DD",
                    "INVOICE_NUM": "text",
                    "BATCH_NUM": "text",
                    "EN_NUM": "text",
                    "ALTER_QTY": "text",
                    "GOOD_QTY": "text",
                    "SHORT_QTY": "text"
                }
                Return ONLY raw JSON, no markdown formatting.
                """
                response = model.generate_content([prompt, image])
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                data = json.loads(clean_text)
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row = [
                    timestamp,
                    data.get("DATE", ""),
                    data.get("INVOICE_NUM", ""),
                    data.get("BATCH_NUM", ""),
                    data.get("EN_NUM", ""),
                    data.get("ALTER_QTY", ""),
                    data.get("GOOD_QTY", ""),
                    data.get("SHORT_QTY", "")
                ]
                
                sheet.append_row(row)
                st.success("Data successfully saved to Google Sheet!")
                st.json(data)
            except Exception as e:
                st.error(f"Error: {e}")
