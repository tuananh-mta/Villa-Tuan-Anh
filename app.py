import streamlit as st
import pandas as pd
import re
import datetime
import gspread
from google.oauth2.service_account import Credentials

# =============================
# 1. CẤU HÌNH GIAO DIỆN & STYLE TAILWIND (NEXT.JS)
# =============================
st.set_page_config(
    page_title="Giỏ Hàng Villa Tuấn Anh",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="collapsed" # Mặc định thu gọn sidebar để xem trên Mobile đẹp hơn
)

# Nhúng CSS tùy biến cao cấp mô phỏng bdsttt.vercel.app
custom_css = """
<style>
/* Ẩn các thành phần mặc định của Streamlit để tạo cảm giác Web thật */
#MainMenu, header, footer {visibility: hidden;}
.stAppDeployButton {display:none;}
div[data-testid="stToolbar"] {display: none;}
.block-container {padding-top: 0rem; padding-bottom: 3rem;}

/* Cấu hình màu nền Dark Mode sâu (Zinc 950) */
.stApp {
    background-color: #09090b !important;
}

/* Khung viền và bo góc cho các Container/Card sản phẩm */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 1rem !important;
    padding: 1rem !important;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1) !important;
    transition: transform 0.2s, border-color 0.2s;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: #f97316 !important;
}

/* Tùy biến ô Input và Selectbox */
.stTextInput input, .stSelectbox div[data-baseweb="select"] {
    background-color: #09090b !important;
    border: 1px solid #27272a !important;
    border-radius: 0.5rem !important;
    color: #fafafa !important;
}
.stTextInput input:focus {
    border-color: #f97316 !important;
    box-shadow: 0 0 0 1px #f97316 !important;
}

/* Thiết kế phần Header cố định (Sticky Navigation) */
.custom-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: 60px;
    background-color: rgba(9, 9, 9, 0.8);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid #27272a;
    z-index: 999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
}
.header-title {
    font-size: 1.125rem;
    font-weight: 700;
    color: #fafafa;
}

/* Thiết kế phần Profile Banner (Hero Section màu cam chuyển sắc) */
.hero-profile {
    background: linear-gradient(135deg, #f97316 0%, #fdba74 100%);
    border-radius: 1rem;
    padding: 2.5rem 1.5rem;
    margin-top: 80px;
    margin-bottom: 2rem;
    color: #09090b;
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
}
.profile-avatar {
    width: 90px;
    height: 90px;
    border-radius: 50%;
    border: 4px solid #ffffff;
    object-fit: cover;
    margin-bottom: 0.75rem;
}
.profile-name {
    font-size: 1.5rem;
    font-weight: 800;
    margin: 0;
    color: #09090b;
}
.profile-tag {
    font-size: 0.875rem;
    font-weight: 500;
    opacity: 0.9;
    margin-top: 0.25rem;
}

/* Nút bấm gọi điện / Zalo nhanh */
.cta-container {
    display: flex;
    gap: 0.75rem;
    margin-top: 1.25rem;
}
.cta-button {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem 1.25rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
    text-decoration: none;
    background-color: #09090b;
    color: #ffffff !important;
}

/* Custom cho các Badge / Tag thông tin */
.badge-price {
    font-size: 1.125rem;
    font-weight: 700;
    color: #f97316;
    margin-bottom: 0.5rem;
}
</style>
"""
st.html(custom_css)

# Hiển thị Header cố định
st.html('''
<div class="custom-header">
    <div class="header-title">🏢 BĐS Trong Tầm Tay</div>
    <div style="color: #a1a1aa; font-size: 0.875rem;">Alliance Real Estate 🌙</div>
</div>
''')

# Hiển thị Banner Profile của Tuấn Anh
st.html('''
<div class="hero-profile">
    <img src="https://res.cloudinary.com/dbv796w60/image/upload/v1711181775/avatar_linh.jpg" class="profile-avatar" alt="Avatar">
    <div class="profile-name">Tuấn Anh Villa</div>
    <div class="profile-tag">Chuyên gia Môi giới & Marketing Biệt thự / Villa Quận 2</div>
    <div class="cta-container">
        <a href="tel:0909108814" class="cta-button">📞 Gọi ngay</a>
        <a href="https://zalo.me/0909108814" class="cta-button" style="background-color: #0068ff;">💬 Liên hệ Zalo</a>
    </div>
</div>
''')


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

df_raw = load_data()
if df_raw.empty:
    st.stop()


# =============================
# 3. MAPPING CỘT & CLEANING (Giữ nguyên logic gốc của bạn)
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

df = df.dropna(subset=["status_label"])

combined_text = df.astype(str).apply(lambda x: ' '.join(x), axis=1).str.lower()
df["pool"] = combined_text.str.contains("hồ bơi|bể bơi", na=False)
df["garden"] = combined_text.str.contains("sân vườn", na=False)


# =============================
# 4. BỘ LỌC HIỆN ĐẠI (ĐƯA RA TRANG CHÍNH THAY VÌ SIDEBAR)
# =============================
st.markdown("### 🔍 Bộ lọc tìm kiếm nâng cao")

# Chia thanh tìm kiếm và bộ lọc thành các cột thông minh trên trang chính
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    search_address = st.text_input("📍 Tìm kiếm theo tên đường hoặc địa chỉ...", placeholder="Ví dụ: Thảo Điền, Đường số 10...")
with c2:
    st_filter = st.selectbox("📅 Trạng thái trống", ["Tất cả", "✅ Đang trống", "⏳ Sắp trống"])
with c3:
    type_filter = st.selectbox("🏢 Loại hình", ["Tất cả", "Villa", "House", "Airbnb", "MB", "Office"])

c4, c5, c6 = st.columns([2, 1, 1])
with c4:
    price_range = st.slider("💰 Khoảng giá (USD)", 0, int(df["price"].max() or 5000), (0, int(df["price"].max() or 5000)))
with c5:
    bed_filter = st.selectbox("🛏 Phòng ngủ", ["Tất cả", "2+", "3+", "4+", "5+", "6+"])
with c6:
    furni_filter = st.selectbox("🪑 Nội thất", ["Tất cả", "Full NT", "KNT", "NTCB"])

# Cột checkbox phụ
cc1, cc2, cc3 = st.columns([1, 1, 4])
with cc1:
    filter_pool = st.checkbox("🏊 Có hồ bơi")
with cc2:
    filter_garden = st.checkbox("🌿 Có sân vườn")
with cc3:
    if st.button("🔄 Làm mới dữ liệu"):
        st.cache_data.clear()
        st.rerun()

# --- TIẾN HÀNH LỌC DỮ LIỆU ---
f = df.copy()

if search_address:
    f = f[f[COL_ADDRESS].astype(str).str.contains(search_address, case=False, na=False) | 
          f[COL_STREET].astype(str).str.contains(search_address, case=False, na=False)]

if st_filter != "Tất cả": 
    f = f[f["status_label"] == st_filter]

if type_filter != "Tất cả": 
    f = f[f[COL_TYPE].astype(str).str.contains(type_filter, case=False, na=False)]

f = f[(f["price"] >= price_range[0]) & (f["price"] <= price_range[1])]

if bed_filter != "Tất cả":
    f = f[f["bed"] >= int(bed_filter.replace("+", ""))]

if furni_filter != "Tất cả": 
    f = f[f["furniture"] == furni_filter]

if filter_pool: f = f[f["pool"] == True]
if filter_garden: f = f[f["garden"] == True]


# =============================
# 5. HIỂN THỊ KẾT QUẢ DẠNG Ô LƯỚI (GRID LAYOUT)
# =============================
st.markdown(f"### 📋 Kết quả tìm kiếm ({len(f)} căn phù hợp)")

# Chia danh sách thành lưới 2 cột giống giao diện bdsttt.vercel.app
grid_columns = st.columns(2)

for index, (i, row) in enumerate(f.head(50).iterrows()):
    display_name = row[COL_ADDRESS]
    price_val = f"{int(row['price']):,}".replace(",", ".") + " USD" if pd.notna(row['price']) else "Liên hệ"
    
    status_display = row["status_label"]
    if row["status_label"] == "⏳ Sắp trống" and row["status_date"]:
        status_display = f"{row['status_label']} ({row['status_date']})"

    copy_text = f"""🏡 {display_name} 💰 Giá: {price_val}
🛏 {int(row['bed']) if pd.notna(row['bed']) else 'N/A'} PN | 📐 {int(row['area']) if pd.notna(row['area']) else 'N/A'} m2
🪑 Nội thất: {row['furniture']}
📌 Trạng thái: {status_display}
{"🏊 Hồ bơi" if row['pool'] else ""} {"🌿 Sân vườn" if row['garden'] else ""}""".strip()

    # Chọn cột luân phiên (Cột 0 hoặc Cột 1) để rải đều Card sản phẩm
    with grid_columns[index % 2]:
        with st.container(border=True): # Tạo viền và màu nền Zinc-900 thông qua CSS
            
            # 1. Hiển thị hình ảnh dạng Slider/Tab gọn gàng
            raw_img_links = str(row[COL_IMAGE_O]).strip()
            if raw_img_links and raw_img_links.lower() != "nan":
                list_links = [link.strip() for link in raw_img_links.split(",") if link.strip().startswith("http")]
                
                if len(list_links) > 1:
                    tabs = st.tabs([f"📸 Ảnh {idx+1}" for idx in range(len(list_links))])
                    for idx, link in enumerate(list_links):
                        with tabs[idx]:
                            st.image(link, use_container_width=True)
                elif len(list_links) == 1:
                    st.image(list_links[0], use_container_width=True)
            else:
                # Ảnh mặc định nếu căn hộ không có ảnh
                st.image("https://images.unsplash.com/photo-1600596542815-ffad4c1539a9", use_container_width=True)
            
            # 2. Thông tin chi tiết sản phẩm
            st.markdown(f"#### 🏠 {display_name}")
            st.html(f'<div class="badge-price">💰 {price_val} / tháng</div>')
            
            # Sắp xếp các thông số kỹ thuật dạng cột nhỏ bên trong Card
            info_c1, info_c2 = st.columns(2)
            with info_c1:
                st.markdown(f"📐 **Diện tích:** {int(row['area']) if pd.notna(row['area']) else 'N/A'} m²")
                st.markdown(f"🛏 **Phòng ngủ:** {int(row['bed']) if pd.notna(row['bed']) else 'N/A'} PN")
                st.markdown(f"🪑 **Nội thất:** {row['furniture']}")
            with info_c2:
                st.markdown(f"📅 **Trạng thái:** {status_display}")
                st.markdown(f"🏊 **Hồ bơi:** {'Có' if row['pool'] else 'Không'}")
                st.markdown(f"🌿 **Sân vườn:** {'Có' if row['garden'] else 'Không'}")
            
            # 3. Khung Copy nhanh cho Môi giới gửi khách hàng
            st.code(copy_text, language="text")
            
            # Nút CTA riêng cho từng căn biệt thự kết nối nhanh
            st.link_button("💬 Gửi yêu cầu tư vấn căn này", f"https://zalo.me/0909108814", use_container_width=True)
