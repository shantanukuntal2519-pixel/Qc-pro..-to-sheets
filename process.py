import os
import json
from datetime import datetime
from PIL import Image
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

st.set_page_config(page_title="QC Invoice Scanner", page_icon="⚡", layout="centered")

st.title("⚡ Fast QC Scanner")

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

uploaded_file = st.file_uploader("Upload Image or Capture Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    image = Image.open(uploaded_file)
    
    # Speed Optimization: Image Resize (Gemini fast process karega)
    image.thumbnail((1024, 1024))
    st.image(image, caption="Selected Image", use_container_width=True)
    
    if st.button("🚀 Process & Save Fast", type="primary"):
        with st.spinner("Processing..."):
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
                
                # Fast row position calculation
                next_row = len(sheet.col_values(1)) + 1
                sheet.insert_rows(rows_to_add, row=next_row)
                
                st.success(f"⚡ Done in seconds! Added {len(rows_to_add)} rows.")
                st.json(items)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
