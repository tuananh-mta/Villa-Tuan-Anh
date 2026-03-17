# =========================
# IMPORT
# =========================
import re
import pandas as pd
from google import genai

# =========================
# CONFIG API
# =========================
client = genai.Client(api_key="YOUR_GEMINI_API_KEY")

# =========================
# LOAD DATA GOOGLE SHEET
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

df = pd.DataFrame(sheet.get_all_records())

print("👉 Columns:", df.columns)

# =========================
# CLEAN + PARSE
# =========================
def clean_price(val):
    try:
        return float(str(val).replace(",", "").strip())
    except:
        return None

def clean_bedroom(val):
    try:
        return int(val)
    except:
        return None

def parse_pool_garden(text):
    text = str(text).lower()
    return (
        "hồ bơi" in text or "pool" in text,
        "sân vườn" in text or "garden" in text
    )

rows = []

for _, row in df.iterrows():
    pool, garden = parse_pool_garden(row.get("Hồ Bơi\nSân vườn", ""))

    rows.append({
        "price_usd": clean_price(row.get("Giá thuê USD")),
        "bedrooms": clean_bedroom(row.get("Phòng Ngủ")),
        "location": str(row.get("Tên Đường")),
        "has_pool": pool,
        "has_garden": garden,
        "raw": str(row.get("raw_text"))
    })

df_parsed = pd.DataFrame(rows)

# =========================
# RULE FILTER
# =========================
def extract_budget(query):
    nums = re.findall(r"\d+", query)
    nums = [int(n) for n in nums]

    if len(nums) >= 2:
        return min(nums), max(nums)
    elif len(nums) == 1:
        return nums[0] - 1000, nums[0] + 1000
    return None, None

def rule_filter(query, df):
    query = query.lower()
    min_price, max_price = extract_budget(query)

    results = []

    for i, row in df.iterrows():
        score = 0

        if "hồ bơi" in query and row["has_pool"]:
            score += 3

        if "sân vườn" in query and row["has_garden"]:
            score += 3

        if row["bedrooms"]:
            if "4" in query and row["bedrooms"] >= 4:
                score += 2

        if row["price_usd"] and min_price and max_price:
            if min_price <= row["price_usd"] <= max_price:
                score += 4

        results.append((i, score))

    results.sort(key=lambda x: x[1], reverse=True)

    # 👉 chỉ lấy top 10 để đưa vào AI
    return results[:10]

# =========================
# AI RE-RANK
# =========================
def ai_rerank(query, df, candidates):
    text_block = ""

    for idx, score in candidates:
        row = df.iloc[idx]
        text_block += f"""
ID: {idx}
Location: {row['location']}
Price: {row['price_usd']} USD
Bedrooms: {row['bedrooms']}
Pool: {row['has_pool']}
Garden: {row['has_garden']}
Description: {row['raw']}
---
"""

    prompt = f"""
Bạn là chuyên gia môi giới bất động sản.

Khách hàng yêu cầu:
"{query}"

Danh sách nhà:
{text_block}

👉 Hãy chọn ra TOP 3 phù hợp nhất.
Chỉ trả về ID, cách nhau bằng dấu phẩy.
Ví dụ: 5,2,9
"""

    response = client.models.generate_content(
        model="gemini-1.5-flash",  # nếu lỗi thì đổi: gemini-1.5-pro
        contents=prompt
    )

    text = response.text.strip()

    try:
        ids = [int(x) for x in re.findall(r"\d+", text)]
        return ids
    except:
        return []

# =========================
# MAIN SEARCH
# =========================
def hybrid_search(query, df):
    candidates = rule_filter(query, df)

    try:
        best_ids = ai_rerank(query, df, candidates)
    except Exception as e:
        print("⚠️ AI lỗi → fallback rule:", e)
        best_ids = [idx for idx, _ in candidates[:3]]

    return best_ids

# =========================
# TEST
# =========================
query = "villa 4-6 phòng ngủ, có hồ bơi, sân vườn, giá 4000-6000 usd"

results = hybrid_search(query, df_parsed)

print("\n🔥 FINAL RESULT:\n")

for idx in results:
    row = df_parsed.iloc[idx]

    print("🏡 Villa:")
    print("📍 Khu:", row["location"])
    print("💰 Giá:", row["price_usd"], "USD")
    print("🛏 Phòng ngủ:", row["bedrooms"])
    print("🏊 Hồ bơi:", row["has_pool"])
    print("🌿 Sân vườn:", row["has_garden"])
    print("-" * 50)