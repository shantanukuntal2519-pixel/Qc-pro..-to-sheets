import os
import json
from datetime import datetime
from PIL import Image
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# Page Configuration
st.set_page_config(page_title="Delhivery Smart QC Workstation", page_icon="📦", layout="wide")

# Custom CSS for Delhivery Branding
st.markdown("""
    <style>
    .main-header {
        background-color: #000000;
        padding: 15px;
        border-radius: 8px;
        color: white;
        margin-bottom: 20px;
    }
    .main-title {
        color: #E31E24;
        font-weight: bold;
        font-size: 28px;
        margin: 0;
    }
    .sub-title {
        color: #FFFFFF;
        font-size: 16px;
        margin: 0;
    }
    .status-card {
        background-color: #F8F9FA;
        padding: 12px;
        border-left: 4px solid #E31E24;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# Top Banner Header
st.markdown("""
    <div class="main-header">
        <div class="main-title">DELHIVERY</div>
        <div class="sub-title">SMART QC WORKSTATION</div>
        <small>Auto Invoice Image Extractor & Google Sheets Sync Engine</small>
    </div>
""", unsafe_allow_html=True)

# Operator Status Bar
st.markdown("""
    <div class="status-card">
        <b>Active Operator:</b> Shantanu | QC Station Operator <br>
        <small>System automatically compresses invoice images, extracts barcode metadata, and appends rows directly to the target Google Spreadsheet in real-time.</small>
    </div>
""", unsafe_allow_html=True)

@st.cache_resource
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gs_client = gspread.authorize(creds)
    return gs_client.open("fress inword qc").sheet1

@st.cache_resource
def get_gemini():
    return genai.Client(api_key=os.environ["GEMINI_API_KEY"])

gemini_client = get_gemini()
sheet = get_gsheet()

# Form Inputs Layout
st.subheader("1. ORDER PHOTO CAPTURE & UPLOAD")

col1, col2 = st.columns(2)

with col1:
    target_tab = st.selectbox("Target Google Sheet Tab", ["Daily_QC_Orders_2026", "Form_Responses"])
    inspection_cat = st.selectbox("Inspection Category", ["Inbound Package QC", "Outbound Package QC", "Return Order QC"])

with col2:
    uploaded_file = st.file_uploader("Upload Order / Invoice Photo", type=["jpg", "jpeg", "png"], help="Drag & drop order photo here, or browse from local storage")

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    image.thumbnail((1024, 1024))
    
    st.image(image, caption="Uploaded Invoice Photo", use_container_width=True)
    
    if st.button("PROCESS & SYNC TO GOOGLE SHEET", type="primary"):
        with st.spinner("Extracting data & syncing with Google Sheet..."):
            try:
                prompt = """
                Extract all lines into JSON ARRAY:
                [{"DATE": "", "INVOICE_NUM": "", "BATCH_NUM": "", "EN_NUM": "", "ALTER_QTY": "", "GOOD_QTY": "", "SHORT_QTY": ""}]
                Return ONLY raw JSON, no markdown.
                """
                
                response = gemini_client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt, image]
                )
                
                clean_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
                parsed_data = json.loads(clean_text)
                items = parsed_data if isinstance(parsed_data, list) else [parsed_data]
                
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                rows_to_add = [
                    [
                        timestamp,
                        item.get("DATE", ""),
                        item.get("INVOICE_NUM", ""),
                        item.get("BATCH_NUM", ""),
                        item.get("EN_NUM", ""),
                        item.get("ALTER_QTY", ""),
                        item.get("GOOD_QTY", ""),
                        item.get("SHORT_QTY", "")
                    ]
                    for item in items
                ]
                
                next_row = len(sheet.col_values(1)) + 1
                sheet.insert_rows(rows_to_add, row=next_row)
                
                st.success(f"✅ Successfully extracted and synced {len(rows_to_add)} rows to Google Sheet!")
                st.json(items)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
