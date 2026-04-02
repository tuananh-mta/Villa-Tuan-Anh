import streamlit as st
import pandas as pd
import re
import datetime
import gspread
from google.oauth2.service_account import Credentials

# =============================
# 1. CẤU HÌNH GIAO DIỆN
# =============================
st.set_page_config(page_title="Villa CRM PRO", layout="wide")
st.title("🏡 Giỏ Hàng Villa Tuấn Anh")

# =============================
# 2. TẢI DỮ LIỆU (TTL 10 PHÚT)
# =============================
@st.cache_data(ttl=600)
def load_data():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key("1lxWjikL1b_wg0NW9zjsnEXK9DY3FgtHXKrbwHn7Rs4o")
        worksheet = sheet.worksheet("Đang trống")
        data = worksheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
        return pd.DataFrame()

if st.sidebar.button("🔄 Cập nhật dữ liệu mới"):
    st.cache_data.clear()
    st.rerun()

df_raw = load_data()
if df_raw.empty:
    st.stop()

# =============================
# 3. MAPPING CỘT & CLEANING
# =============================
df = df_raw.copy()
COL_TYPE = df.columns[1]      # Cột B: Loại hình
COL_PRICE = df.columns[3]     # Cột D: Giá
COL_STATUS_G = df.columns[6]  # Cột G: Ngày trống
COL_BED = df.columns[7]       # Cột H: PN
COL_FURNI_I = df.columns[8]   # Cột I: Nội thất
COL_AREA = df.columns[10]     # Cột K: Diện tích
COL_STREET = df.columns[12]   # Cột M: Tên đường
COL_ADDRESS = df.columns[13]  # Cột N: Địa chỉ
COL_IMAGE_O = df.columns[14]  # Cột O: Hình ảnh

def clean_num(x):
    if pd.isna(x) or x == "": return None
    nums = re.findall(r"\d+", str(x).replace(".", "").replace(",", ""))
    return int(nums[0]) if nums else None

def process_status_logic(x):
    val = str(x).strip().lower()
    if val in ["#n/a", "nan", "", "null"]: return None, None
    if "đang trống" in val: return "✅ Đang trống", ""
    if re.search(r"\d", val): return "⏳ Sắp trống", str(x).strip()
    return "✅ Đang trống", ""

def process_furni(x):
    val = str(x).strip().lower()
    if "full" in val: return "Full NT"
    if "knt" in val: return "KNT"
    if "ntcb" in val: return "NTCB"
    return "Khác"

# Thực thi xử lý dữ liệu
df["price"] = df[COL_PRICE].apply(clean_num)
df["bed"] = df[COL_BED].apply(clean_num)
df["area"] = df[COL_AREA].apply(clean_num)
status_results = df[COL_STATUS_G].apply(process_status_logic)
df["status_label"] = [item[0] for item in status_results]
df["status_date"] = [item[1] for item in status_results]
df["furniture"] = df[COL_FURNI_I].apply(process_furni)

# Loại bỏ dòng không có trạng thái trống hợp lệ
df = df.dropna(subset=["status_label"])

# =============================
# 3. MAPPING CỘT & CLEANING (Đã fix lỗi dòng 85)
# =============================

# ... (Giữ nguyên phần code phía trên) ...

# Loại bỏ dòng không có trạng thái trống hợp lệ
df = df.dropna(subset=["status_label"])

# --- ĐOẠN SỬA LỖI TẠI ĐÂY ---
def create_search_string(row):
    # Chuyển tất cả các cột trong hàng thành chuỗi, loại bỏ NaN, nối lại bằng dấu cách
    return " ".join(row.fillna("").astype(str)).lower()

# Tạo một Series tạm để tìm kiếm mà không làm thay đổi kiểu dữ liệu các cột gốc của df
search_series = df.apply(create_search_string, axis=1)

df["pool"] = search_series.str.contains("hồ bơi|bể bơi", na=False)
df["garden"] = search_series.str.contains("sân vườn", na=False)
# ----------------------------

# =============================
# =============================
# 4. BỘ LỌC (SIDEBAR & SEARCH)
# =============================
st.sidebar.header("🔍 Bộ lọc tìm kiếm")

# --- MỚI: Thêm ô tìm kiếm địa chỉ/tên đường ---
search_query = st.sidebar.text_input("📍 Tìm địa chỉ, tên đường...", placeholder="Ví dụ: Võ Nguyên Giáp")

# Các bộ lọc cũ giữ nguyên
st_filter = st.sidebar.selectbox("Ngày trống", ["Tất cả", "✅ Đang trống", "⏳ Sắp trống"])
type_filter = st.sidebar.selectbox("Loại hình", ["Tất cả", "Villa", "House", "Airbnb", "MB", "Office"])
price_range = st.sidebar.slider("Khoảng giá (USD)", 0, int(df["price"].max() or 5000), (0, int(df["price"].max() or 5000)))
bed_filter = st.sidebar.selectbox("Phòng ngủ", ["Tất cả", "2+", "3+", "4+", "5+", "6+"])
furni_filter = st.sidebar.selectbox("Nội thất", ["Tất cả", "Full NT", "KNT", "NTCB"])

# THỰC HIỆN LỌC
f = df.copy()

# 1. Lọc theo từ khóa địa chỉ (MỚI)
if search_query:
    # Tìm kiếm trong cả cột Tên đường và Địa chỉ cụ thể
    # case=False để không phân biệt hoa thường
    condition = (
        f[COL_STREET].astype(str).str.contains(search_query, case=False, na=False) | 
        f[COL_ADDRESS].astype(str).str.contains(search_query, case=False, na=False)
    )
    f = f[condition]

# 2. Lọc theo các tiêu chí khác (Giữ nguyên logic cũ của bạn)
if st_filter != "Tất cả": 
    f = f[f["status_label"] == st_filter]

if type_filter != "Tất cả": 
    f = f[f[COL_TYPE].astype(str).str.contains(type_filter, case=False, na=False)]

f = f[(f["price"] >= price_range[0]) & (f["price"] <= price_range[1])]

if bed_filter != "Tất cả":
    f = f[f["bed"] >= int(bed_filter.replace("+", ""))]

if furni_filter != "Tất cả": 
    f = f[f["furniture"] == furni_filter]

if st.sidebar.checkbox("🏊 Hồ bơi"): f = f[f["pool"] == True]
if st.sidebar.checkbox("🌿 Sân vườn"): f = f[f["garden"] == True]

# =============================
# 5. HIỂN THỊ KẾT QUẢ
# =============================
st.markdown(f"🔍 Tìm thấy **{len(f)}** căn phù hợp")

for i, row in f.head(50).iterrows():
    # Hiển thị địa chỉ cụ thể (Mặc định quyền cao nhất)
    display_name = row[COL_ADDRESS]
    price_val = f"{int(row['price']):,}".replace(",", ".") + " USD" if pd.notna(row['price']) else "Liên hệ"
    
    status_display = row["status_label"]
    if row["status_label"] == "⏳ Sắp trống" and row["status_date"]:
        status_display = f"{row['status_label']} ({row['status_date']})"

    copy_text = f"""🏡 {display_name} 💰 Giá: {price_val}
🛏 {int(row['bed']) if pd.notna(row['bed']) else 'N/A'} PN | 📐 {int(row['area']) if pd.notna(row['area']) else 'N/A'} m2
🪑 Nội thất: {row['furniture']}
📌 Ngày trống: {status_display}
{"🏊 Hồ bơi" if row['pool'] else ""} {"🌿 Sân vườn" if row['garden'] else ""}""".strip()

    with st.container():
        st.subheader(f"🏠 {display_name}")
        
        # XỬ LÝ ALBUM ẢNH (Giữ nguyên logic Phiên bản 6)
        raw_img_links = str(row[COL_IMAGE_O]).strip()
        if raw_img_links and raw_img_links.lower() != "nan":
            list_links = [link.strip() for link in raw_img_links.split(",") if link.strip().startswith("http")]
            
            if len(list_links) > 1:
                tabs = st.tabs([f"Ảnh {idx+1}" for idx in range(len(list_links))])
                for idx, link in enumerate(list_links):
                    with tabs[idx]:
                        st.image(link, use_container_width=True)
            elif len(list_links) == 1:
                st.image(list_links[0], use_container_width=True)
        
        # Khung copy (Hoạt động tốt trên mobile)
        st.code(copy_text, language="text")
        st.divider()
