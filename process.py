import os
import json
from datetime import datetime
from PIL import Image
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

# Page Configuration
st.set_page_config(page_title="QC Invoice Scanner", page_icon="📱", layout="centered")

st.title("📱 QC Invoice Scanner")
st.write("Phone ya PC se image upload karein aur Google Sheets mein auto-process karein.")

# Google Sheets Setup
@st.cache_resource
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gs_client = gspread.authorize(creds)
    return gs_client.open("fress inword qc").sheet1

# Gemini Client Setup
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# File Uploader UI for Phone/Browser
uploaded_file = st.file_uploader("Image Select ya Camera se Capture Karein", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    st.image(image, caption="Uploaded Image", use_container_width=True)
    
    if st.button("🚀 Process & Save to Sheets", type="primary"):
        with st.spinner("Handwritten data ko read karke Google Sheets mein bhej rahe hain..."):
            try:
                prompt = """
                Extract data from this handwritten list into JSON format:
                {"DATE": "YYYY-MM-DD", "INVOICE_NUM": "", "BATCH_NUM": "", "EN_NUM": "", "ALTER_QTY": "", "GOOD_QTY": "", "SHORT_QTY": ""}
                Return ONLY raw JSON, no markdown codeblocks.
                """
                
                response = gemini_client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt, image]
                )
                
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                data = json.loads(clean_text)
                
                sheet = get_gsheet()
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
                st.success("✅ Google Sheet mein Data successfully add ho gaya hai!")
                st.json(data)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
