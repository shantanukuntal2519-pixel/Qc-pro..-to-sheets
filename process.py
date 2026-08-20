import os
import json
import time
import base64
from datetime import datetime
from PIL import Image
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

st.set_page_config(page_title="Delhivery Smart QC Workstation", page_icon="📦", layout="centered")

# Custom CSS for UI Matching
st.markdown("""
    <style>
    .stApp { background-color: #F2F5F9; }
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 720px; }
    .qc-card { background-color: #FFFFFF; border-radius: 16px; padding: 24px; box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05); border: 1px solid #E6ECF1; margin-bottom: 20px; }
    .header-container { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #EEF2F5; padding-bottom: 16px; margin-bottom: 20px; }
    .brand-title { color: #D3122A; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; display: inline-block; margin-right: 8px; }
    .badge-tag { background-color: #0A192F; color: #FFFFFF; font-size: 10px; font-weight: 700; padding: 4px 8px; border-radius: 12px; letter-spacing: 0.5px; vertical-align: middle; }
    .sub-tagline { color: #6B7C93; font-size: 12px; margin-top: 2px; }
    .operator-chip { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 25px; padding: 6px 14px 6px 8px; display: flex; align-items: center; gap: 10px; }
    .avatar-circle { background-color: #D3122A; color: white; font-weight: bold; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; }
    .operator-name { font-weight: 700; font-size: 13px; color: #1E293B; line-height: 1.1; }
    .operator-role { font-size: 11px; color: #64748B; }
    .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
    .section-title { font-weight: 800; font-size: 16px; color: #0F172A; }
    .status-ready { color: #16A34A; font-weight: 600; font-size: 13px; }
    div.stButton > button:first-child { background-color: #C20E23 !important; color: white !important; font-weight: 700 !important; font-size: 15px !important; border-radius: 8px !important; height: 48px !important; width: 100% !important; border: none !important; box-shadow: 0 4px 12px rgba(194, 14, 35, 0.25) !important; }
    </style>
""", unsafe_allow_html=True)

# Google Sheets Setup
@st.cache_resource
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gs_client = gspread.authorize(creds)
    return gs_client.open("fress inword qc").sheet1

sheet = get_gsheet()

# Base64 Encoded API Keys Array
RAW_KEYS = [
    "QVEuQWI4Uk42S0RIUE1NaXc0VjdleEJGcmVOYkZxejdxdFR1R25TS1pVc0UtdF9rNWpPOXc=",
    "QVEuQWI4Uk42S3VDRlNLUi1qUTA3TXdqSHhRazNxTUhqN2dOOC1JbE9OaW5uUDJzQ0YyMUE=",
    "QVEuQWI4Uk42SldFcWZqN1pvMFlMcEFTU0dsZVc1NWNyZGo4aGpsWnJ6ek8zX2RsRVJSZHc=",
    "QVEuQWI4Uk42SWYyZjhmUFdqczdXMWtPdzBncEVGR1VTREprZnFEYS13UGlVYmJaOVd3UQ==",
    "QVEuQWI4Uk42TGNfLW80RlVndWY0dndYcGJ6cGY3RGVqRGVwMWs5T1BfSmRSNDJMcVVZM3c=",
    "QVEuQWI4Uk42SURWdUdpRWF6TGFteG5jTVlaTVNnUXBuMGctQmxnQ3ZEcHZKeC12OFhVdHc=",
    "QVEuQWI4Uk42TFF4Mk5GcDBNNzg1ZlRSSGdTOG5Oa2NVNERoa2RnTC1xazNIbzFPVVVVZw=="
]

API_KEYS = [base64.b64decode(k).decode('utf-8') for k in RAW_KEYS]

# Header HTML
st.markdown("""
<div class="qc-card">
    <div class="header-container">
        <div>
            <div>
                <span class="brand-title">DELHIVERY</span>
                <span class="badge-tag">SMART QC WORKSTATION</span>
            </div>
            <div class="sub-tagline">Auto Invoice Image Extractor & Google Sheets Sync Engine</div>
        </div>
        <div class="operator-chip">
            <div class="avatar-circle">S</div>
            <div>
                <div class="operator-name">Shantanu</div>
                <div class="operator-role">QC Station Operator</div>
            </div>
        </div>
    </div>
    <div class="section-header">
        <div class="section-title">1. ORDER PHOTO CAPTURE & UPLOAD</div>
        <div class="status-ready">● Ready for Scan</div>
    </div>
</div>
""", unsafe_allow_html=True)

uploaded_file = st.file_uploader("Upload Order / Invoice Photo", type=["jpg", "jpeg", "png"])

col1, col2 = st.columns(2)
with col1:
    target_tab = st.selectbox("Target Google Sheet Tab", ["Daily_QC_Orders_2026", "Form_Responses"])
with col2:
    inspection_cat = st.selectbox("Inspection Category", ["Inbound Package QC", "Outbound Package QC", "Return Order QC"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    image.thumbnail((1024, 1024))
    st.image(image, caption="Uploaded Photo Preview", use_container_width=True)
    
    if st.button("⚡ PROCESS & SYNC TO GOOGLE SHEET"):
        with st.spinner("Processing image & Syncing to Google Sheet..."):
            prompt = """
            Extract all lines into JSON ARRAY:
            [{"DATE": "", "INVOICE_NUM": "", "BATCH_NUM": "", "EN_NUM": "", "ALTER_QTY": "", "GOOD_QTY": "", "SHORT_QTY": ""}]
            Return ONLY raw JSON, no markdown.
            """
            
            res_text = None
            last_err = None
            used_key_index = None

            # Rotation Mechanism for Enterprise Keys
            for idx, key in enumerate(API_KEYS):
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content([prompt, image])
                    res_text = res.text
                    used_key_index = idx + 1
                    break
                except Exception as err:
                    last_err = err
                    continue

            if res_text:
                try:
                    clean_text = res_text.strip().removeprefix("```json").removesuffix("```").strip()
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
                    
                    st.success(f"✅ Successfully extracted and synced {len(rows_to_add)} rows using Key #{used_key_index}!")
                    st.json(items)
                except Exception as parse_err:
                    st.error(f"❌ JSON Parsing Error: {parse_err}")
            else:
                st.error(f"❌ Processing Error: {last_err}")
