# =========================
# LOAD ENV
# =========================
from dotenv import load_dotenv
load_dotenv()

import os
import re
import pandas as pd

# =========================
# GEMINI CLIENT
# =========================
from google import genai

client = genai.Client(api_key=os.getenv("AIzaSyA1Y2LDIR1OSXqcBN42ta2oltEbPq-6MdY"))

# =========================
# GOOGLE SHEET
# =========================
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "credentials.json", scope
)

gs_client = gspread.authorize(creds)

sheet = gs_client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1Lsdco6nRDpUyQ0QeDMRsW00qjlR1S9wK02Siq4VQoec/edit"
).sheet1

data = sheet.get_all_records()
df = pd.DataFrame(data)

print("👉 Columns:", df.columns)

# =========================
# PARSE DATA (CHUẨN HƠN)
# =========================
def parse_row(row):
    text = str(row.get("raw_text", "")).lower()

    def find(pattern):
        match = re.search(pattern, text)
        return int(match.group(1)) if match else None

    return {
        "price_usd": row.get("Giá thuê USD"),
        "bedrooms": row.get("Phòng Ngủ"),
        "furniture": row.get("Nội thất"),
        "area": find(r"(\d+)\s*m2"),
        "has_pool": "hồ bơi" in text or "pool" in text,
        "has_garden": "sân vườn" in text or "garden" in text,
        "location": row.get("Tên Đường"),
        "raw": text
    }

df_parsed = pd.DataFrame([parse_row(r) for _, r in df.iterrows()])

# =========================
# BUILD TEXT CHO AI
# =========================
def build_text(row):
    return f"""
    Villa tại {row['location']},
    {row['bedrooms']} phòng ngủ,
    giá {row['price_usd']} USD,
    diện tích {row['area']} m2,
    nội thất {row['furniture']},
    {'có hồ bơi' if row['has_pool'] else 'không hồ bơi'},
    {'có sân vườn' if row['has_garden'] else 'không sân vườn'}
    """

df_parsed["ai_text"] = df_parsed.apply(build_text, axis=1)

# =========================
# AI MATCH (CORE)
# =========================
def ai_match(query, df_data):
    data_sample = df_data.head(50)  # tránh quá dài

    prompt = f"""
    Bạn là chuyên gia môi giới villa cao cấp.

    Danh sách villa:
    {data_sample.to_dict(orient="records")}

    Yêu cầu khách:
    {query}

    Hãy chọn ra 5 căn phù hợp nhất.

    Trả về JSON dạng:
    [
        {{"index": 0, "reason": "..."}},
        ...
    ]
    """

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text

# =========================
# TEST
# =========================
query = "khách Hàn, cần villa 4-6 phòng ngủ, có hồ bơi, ngân sách 4000-6000 usd"

result = ai_match(query, df_parsed)

print("\n🔥 KẾT QUẢ MATCH:\n")
print(result)