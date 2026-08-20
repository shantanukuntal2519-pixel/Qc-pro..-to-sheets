import os
import json
import glob
from datetime import datetime
from PIL import Image
# Purana (isey hata dein):
# import google.generativeai as genai

# Naya (ye likhein):
from google import genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Credentials Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(os.environ["GOOGLE_CREDENTIALS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("fress inword qc").sheet1

gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
# Search images everywhere in repo
image_files = glob.glob('*.[jJ][pP][gG]') + glob.glob('*.[pP][nN][gG]') + glob.glob('*.[jJ][pP][eE][gG]') + glob.glob('*WhatsApp*')

for img_path in image_files:
    try:
        image = Image.open(img_path)
        prompt = """
        Extract data into JSON format:
        {"DATE": "YYYY-MM-DD", "INVOICE_NUM": "", "BATCH_NUM": "", "EN_NUM": "", "ALTER_QTY": "", "GOOD_QTY": "", "SHORT_QTY": ""}
        Return ONLY raw JSON, no markdown codeblocks.
        """
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )
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
        print(f"Successfully processed: {img_path}")
    except Exception as e:
        print(f"Error processing {img_path}: {e}")
