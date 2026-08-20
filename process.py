import os
import json
from datetime import datetime
from PIL import Image
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

st.set_page_config(page_title="QC Invoice Scanner", page_icon="📱", layout="centered")

st.title("📱 QC Invoice Scanner")
st.write("Phone se direct Photo khinchein ya Gallery se select karke Google Sheet mein bhejain.")

@st.cache_resource
def get_gsheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gs_client = gspread.authorize(creds)
    return gs_client.open("fress inword qc").sheet1

gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

# Option Selection: Camera ya Gallery
option = st.radio("Choose Input Method:", ("📷 Direct Camera", "📁 Gallery File Upload"))

image = None

if option == "📷 Direct Camera":
    camera_file = st.camera_input("Take a photo")
    if camera_file:
        image = Image.open(camera_file)
else:
    uploaded_file = st.file_uploader("Choose file", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)

if image is not None:
    if st.button("🚀 Process & Save to Sheets", type="primary"):
        with st.spinner("Processing image..."):
            try:
                prompt = """
                Extract all lines from this handwritten QC sheet into a JSON ARRAY of objects.
                Each item object should have these keys:
                {"DATE": "YYYY-MM-DD", "INVOICE_NUM": "", "BATCH_NUM": "", "EN_NUM": "", "ALTER_QTY": "", "GOOD_QTY": "", "SHORT_QTY": ""}
                
                If specific headers like DATE or INVOICE_NUM are not written, extract whatever codes/numbers you see into EN_NUM or BATCH_NUM and put quantities into GOOD_QTY.
                Return ONLY raw JSON list, no markdown formatting or codeblocks.
                """
                
                response = gemini_client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt, image]
                )
                
                clean_text = response.text.strip().replace("```json", "").replace("```", "")
                parsed_data = json.loads(clean_text)
                
                items = parsed_data if isinstance(parsed_data, list) else [parsed_data]
                
                sheet = get_gsheet()
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                rows_to_add = []
                for item in items:
                    rows_to_add.append([
                        timestamp,
                        item.get("DATE", ""),
                        item.get("INVOICE_NUM", ""),
                        item.get("BATCH_NUM", ""),
                        item.get("EN_NUM", ""),
                        item.get("ALTER_QTY", ""),
                        item.get("GOOD_QTY", ""),
                        item.get("SHORT_QTY", "")
                    ])
                
                next_row = len(sheet.col_values(1)) + 1
                sheet.insert_rows(rows_to_add, row=next_row)
                
                st.success(f"✅ Data added directly under Row {next_row}!")
                st.json(items)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
