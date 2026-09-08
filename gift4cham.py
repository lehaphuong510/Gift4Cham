import streamlit as st
import pandas as pd
import re
import os
import io
from streamlit_gsheets import GSheetsConnection

# ================= 1. CẤU HÌNH TRANG & GIAO DIỆN =================
st.set_page_config(page_title="GIFT FOR DONOR", page_icon="🎁", layout="centered")

# MÀU ĐỎ ĐÔ #8B0000
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #333333; }
    h1, h2, h3, h4, .stTabs [data-baseweb="tab"] p { color: #8B0000 !important; font-weight: bold; }
    
    /* Nút primary giữ màu Vàng F4C430 */
    button[kind="primary"] { background-color: #F4C430 !important; color: #8B0000 !important; font-weight: bold !important; border: none; width: 100%; border-radius: 8px;}
    button[kind="primary"]:hover { background-color: #8B0000 !important; color: #FFFFFF !important; border: none; }
    
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, .stSelectbox>div>div>div { background-color: #F8F9FA; color: #333333; border: 1px solid #8B0000; border-radius: 5px; }
    .stTabs [aria-selected="true"] { border-bottom-color: #8B0000 !important; }
    
    .section-title { background: linear-gradient(90deg, #8B0000 0%, #F4C430 100%); color: white; padding: 12px 15px; border-radius: 8px 8px 0 0; font-size: 16px; font-weight: bold; margin-top: 25px; text-transform: uppercase; }
    .info-box { background-color: #FAFAFA; border: 1px solid #E0E6ED; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .gift-card { background-color: #FFF9E6; border-left: 5px solid #8B0000; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    
    .custom-table { width: 100%; border-collapse: separate; border-spacing: 0; margin-bottom: 20px; border: 1px solid #E0E6ED; border-top: none; border-radius: 0 0 8px 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); overflow: hidden; }
    .custom-table thead tr { background-color: #5E0000; } 
    .custom-table th { color: white; padding: 12px 14px; text-align: center; font-size: 15px; border: none; }
    .custom-table th:first-child { text-align: left; }
    .custom-table td { padding: 14px; border-bottom: 1px solid #EEEEEE; border-right: 1px solid #EEEEEE; text-align: center; font-weight: bold; }
    .custom-table td:first-child { text-align: left; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #8B0000; margin-bottom: 10px;'>🎁 GIFT FOR DONOR</h1>", unsafe_allow_html=True)

# Hiển thị thông báo thành công sau khi rerun
if st.session_state.get('show_success', False):
    st.snow()
    st.toast("🌱 Khởi đầu mới! Chốt đơn thành công! 🌿", icon="🌱")
    st.success(st.session_state.get('success_msg', '🌱 Bạn đã cập nhật thông tin thành công rồi nha ❤️'))
    st.session_state['show_success'] = False

# Nút Refresh
col_rf1, col_rf2 = st.columns([1, 3])
with col_rf1:
    if st.button("🔄 Cập nhật dữ liệu"):
        st.cache_data.clear()
        st.rerun()

url = "https://docs.google.com/spreadsheets/d/1CDcmsv_O0vgvLjAiSEEamAqR8vEXiCSJYjKJnQ3jHkM/edit?usp=sharing"
ADMIN_PASSWORD = "0519"

LOCK_FILE = "lock_form.txt"
def is_form_locked(): return os.path.exists(LOCK_FILE)
def set_form_lock(locked):
    if locked:
        with open(LOCK_FILE, "w") as f: f.write("locked")
    else:
        if os.path.exists(LOCK_FILE): os.remove(LOCK_FILE)

GIFT_COLS = ['Keyring 9M', 'Bandana', 'Sticker', 'Standee acrylic', 'Vòng tay Xiếm xỏ', 
             'Quạt Liên tâm', 'Card pola', 'Card xịt nước', 'Bông dặm phấn', 'Dù nóng bỏng', 
             'Thảm xiếm may', 'Áo RM']

DICT_GIFT_LABEL = {
    'Keyring 9M': 'K9', 'Bandana': 'Ban', 'Sticker': 'Sti', 'Standee acrylic': 'SA', 
    'Vòng tay Xiếm xỏ': 'Vota', 'Quạt Liên tâm': 'Quali', 'Card pola': 'Capo', 
    'Card xịt nước': 'Caxi', 'Bông dặm phấn': 'Boda', 'Dù nóng bỏng': 'Du', 
    'Thảm xiếm may': 'Thảm', 'Áo RM': 'Áo'
}

@st.cache_data(ttl=60)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_app = conn.read(spreadsheet=url, worksheet="Data App")
    df_app.columns = df_app.columns.str.strip()
    
    df_dvhc = conn.read(spreadsheet=url, worksheet="Data_DVHC")
    df_dvhc.columns = df_dvhc.columns.str.strip()
    
    def fix_sdt(x):
        s = str(x).replace('.0', '').replace("'", "").strip()
        if s.lower() in ['nan', 'none', '<na>', 'nat', '']: 
            return ""
        if s.isdigit() and not s.startswith('0'): 
            return '0' + s
        return s
        
    for col in ['SDT', 'Checked SDT']:
        if col in df_app.columns:
            df_app[col] = df_app[col].apply(fix_sdt)
            
    return df_app, df_dvhc

try:
    df_app, df_dvhc = load_data()
    # Lấy danh sách Hành chính
    danh_sach_tinh_goc = df_dvhc['Tỉnh thành'].dropna().unique().tolist()
    danh_sach_tinh_goc = [str(t).strip() for t in danh_sach_tinh_goc if str(t).strip() != '']
    
    dict_phuong_xa = {}
    for tinh in danh_sach_tinh_goc:
        phuong = df_dvhc[df_dvhc['Tỉnh thành'] == tinh]['Phường xã'].dropna().unique().tolist()
        dict_phuong_xa[tinh] = [str(p).strip() for p in phuong if str(p).strip() != '']
except Exception as e:
    st.error("Đang có lỗi kết nối dữ liệu. Vui lòng thử lại sau!")
    st.stop()

# Hàm so khớp dropdown siêu an toàn
def find_index_safe(options_list, val):
    val_clean = str(val).strip().lower()
    if not val_clean or val_clean in ['nan', 'none', '']: return 0
    for i, opt in enumerate(options_list):
        if str(opt).strip().lower() == val_clean:
            return i
    return 0

tab1, tab2 = st.tabs(["🔍 XÁC NHẬN ĐƠN HÀNG", "🔒 ADMIN"])

# ================= TAB 1: USER CONFIRM =================
with tab1:
    st.markdown("### Nhập SĐT để kiểm tra phần quà của bạn")
    
    if 'search_key' not in st.session_state:
        st.session_state['search_key'] = 0
        
    phone_input = st.text_input("Nhập số điện thoại của bạn:", key=f"phone_query_{st.session_state['search_key']}", placeholder="Ví dụ: 0901234567")
    
    if st.button("KIỂM TRA 🚀", type="primary"):
        if phone_input:
            clean_input = phone_input.strip().lstrip('0')
            df_app['Phone_Compare'] = df_app['SDT'].astype(str).str.lstrip('0')
            user_orders = df_app[df_app['Phone_Compare'] == clean_input].copy()
            
            if not user_orders.empty:
                st.session_state['verified_phone'] = clean_input 
                st.rerun()
            else:
                st.warning("Không tìm thấy thông tin nào với SĐT này. Bạn kiểm tra lại nhé!")
        else:
            st.warning("Bạn chưa nhập số điện thoại kìa!")

    if 'verified_phone' in st.session_state:
        clean_input = st.session_state['verified_phone']
        df_app['Phone_Compare'] = df_app['SDT'].astype(str).str.lstrip('0')
        user_orders = df_app[df_app['Phone_Compare'] == clean_input].copy()
        row_first = user_orders.iloc[0]
        
        tt_xacnhan = str(row_first.get('Trạng thái xác nhận', '')).strip()
        nickname = str(row_first.get('Họ tên', '')).replace('nan', '').strip() or "BẠN"
        
        is_locked = is_form_locked()
        
        # Lời chào
        if tt_xacnhan in ["Đã xác nhận", "Đã cập nhật"]:
            st.success(f"🎉 Chào {nickname.upper()} ơi, bạn đã {tt_xacnhan.lower()} thông tin thành công rồi nha, dưới đây là kết quả cuối cùng của bạn!")
        else:
            st.info(f"👋 Chào {nickname.upper()} ơi, bạn kiểm tra lại thông tin nhận quà của mình nha!")
            
        if is_locked:
            st.error("🔒 ĐÃ HẾT THỜI GIAN CẬP NHẬT THÔNG TIN. Thông tin bên dưới là dữ liệu đã được hệ thống chốt sổ.")

        # ================= 1. THÔNG TIN VẬN CHUYỂN =================
        st.markdown("<div class='section-title'>🚚 THÔNG TIN VẬN CHUYỂN</div>", unsafe_allow_html=True)
        mvd = str(row_first.get('Mã vận đơn', '')).replace('nan', '').strip()
        phien = str(row_first.get('Phiên lấy hàng', '')).replace('nan', '').strip()
        
        if mvd == "":
            st.info("📦 Tụi mình sẽ sớm cập nhật Thông tin vận chuyển ngay sau khi book đơn nha ❤️")
        else:
            html_ship_top = f"<div class='info-box' style='background-color: #F0F8FF; border-left: 5px solid #8B0000; padding-bottom: 5px; margin-bottom: 0px; border-bottom: none; border-radius: 8px 8px 0 0;'>"
            html_ship_top += f"<div style='margin-bottom: 0px;'><b>Mã vận đơn:</b> <span style='font-size: 13px; color: #555; font-style: italic;'>(Bấm biểu tượng cuối ô để Copy nha)</span></div></div>"
            st.markdown(html_ship_top, unsafe_allow_html=True)
            st.code(mvd, language="plaintext")
            
            html_ship_bot = f"<div class='info-box' style='background-color: #F0F8FF; border-left: 5px solid #8B0000; padding-top: 10px; margin-top: -15px; border-top: none; border-radius: 0 0 8px 8px;'>"
            html_ship_bot += f"<div style='margin-bottom: 8px;'><b>Đơn vị vận chuyển:</b> <span style='color: #8B0000; font-weight: bold;'>GHTK</span></div>"
            html_ship_bot += f"<div style='margin-bottom: 8px;'><b>Ngày shipper lấy hàng:</b> <span style='color: #8B0000; font-weight: bold;'>{phien}</span></div>"
            html_ship_bot += f"<div style='margin-bottom: 8px;'><b>Link để tracking:</b> <a href='https://i.ghtk.vn/' target='_blank' style='color: #0066CC; text-decoration: none; font-weight: bold;'>Bấm vào đây để tra cứu hành trình nha 🚀</a></div>"
            html_ship_bot += "<hr style='border: 0.5px dashed #ccc; margin: 15px 0 10px 0;'>"
            html_ship_bot += "<div style='font-size: 14px; font-style: italic; color: #555;'>Nếu mọi người có gì cần hỗ trợ cứ liên hệ với mình qua Zalo 0903199825 - Lê Phương nha 😍</div></div>"
            st.markdown(html_ship_bot, unsafe_allow_html=True)

        # ================= 2. THÔNG TIN GIAO HÀNG =================
        st.markdown("<div class='section-title'>📍 THÔNG TIN GIAO HÀNG</div>", unsafe_allow_html=True)
        st.markdown("<p style='background-color: #FFF3CD; padding: 10px; border-radius: 5px; font-weight: bold; color: #856404;'>⚠️ Mọi người dò thiệt kỹ phần địa chỉ có đúng với SAU SÁP NHẬP chưa nha, phần nào chưa đúng mọi người nhớ chọn lại. Sau khi chọn lại mọi người NHỚ TICK VÀO Ô XÁC NHẬN nhé.</p>", unsafe_allow_html=True)
        
        def get_val(r, col_name):
            if col_name in r.index:
                return str(r[col_name]).replace('nan', '').strip()
            for idx_name in r.index:
                if col_name.replace(" ", "") == str(idx_name).replace(" ", ""):
                    return str(r[idx_name]).replace('nan', '').strip()
            return ""

        goc_sdt = str(row_first.get('SDT', '')).replace('.0','')
        goc_dc = get_val(row_first, 'Địa chỉ mới')
        goc_tinh = get_val(row_first, 'Tỉnh/Thành mới')
        goc_px = get_val(row_first, 'Phường/Xã mới')
        
        if tt_xacnhan in ["Đã xác nhận", "Đã cập nhật"]:
            val_sdt = str(row_first.get('Checked SDT', goc_sdt)).replace('nan', '').strip()
            val_dc = get_val(row_first, 'Checked Địa chỉ') or goc_dc
            val_tinh = get_val(row_first, 'Check Tỉnh thành') or goc_tinh
            val_px = get_val(row_first, 'Checked Phường xã') or goc_px
        else:
            val_sdt, val_dc, val_tinh, val_px = goc_sdt, goc_dc, goc_tinh, goc_px

        if not is_locked:
            input_sdt = st.text_input("SĐT:", value=val_sdt)
            input_dc = st.text_input("Địa chỉ (Số nhà + Tên đường):", value=val_dc, placeholder="Vui lòng điền địa chỉ...")
            
            options_tinh = [" Vui lòng chọn..."] + danh_sach_tinh_goc
            idx_tinh = find_index_safe(options_tinh, val_tinh)
            input_tinh = st.selectbox("Tỉnh/ Thành:", options=options_tinh, index=idx_tinh)
            
            if input_tinh == " Vui lòng chọn...":
                options_px = [" Vui lòng chọn..."]
            else:
                options_px = [" Vui lòng chọn..."] + dict_phuong_xa.get(input_tinh, [])
                
            idx_px = find_index_safe(options_px, val_px)
            input_px = st.selectbox("Phường/ Xã:", options=options_px, index=idx_px)
            
            st.markdown("<div style='background-color: #F8D7DA; color: #721C24; padding: 10px; border-radius: 5px; font-weight: bold; border: 1px solid #F5C6CB; margin-top: 15px; margin-bottom: 5px; text-align: center;'>👇 BẠN VUI LÒNG TICK VÀO Ô BÊN DƯỚI SAU KHI ĐÃ KIỂM TRA KỸ CÀNG NHA</div>", unsafe_allow_html=True)
            is_correct = st.checkbox("TÔI ĐÃ KIỂM TRA KỸ THÔNG TIN GIAO HÀNG", value=False)
        else:
            st.markdown(f"<div class='info-box'><b>SĐT:</b> {val_sdt}<br><b>Địa chỉ:</b> {val_dc if val_dc else '<i>Chưa có</i>'}<br><b>Phường/ Xã:</b> {val_px if val_px else '<i>Chưa có</i>'}<br><b>Tỉnh/ Thành:</b> {val_tinh if val_tinh else '<i>Chưa có</i>'}</div>", unsafe_allow_html=True)
            input_sdt, input_dc, input_tinh, input_px = val_sdt, val_dc, val_tinh, val_px
            is_correct = True

        # ================= 3. THÔNG TIN GIFT =================
        st.markdown("<div class='section-title'>🎁 THÔNG TIN GIFT</div>", unsafe_allow_html=True)
        
        for idx_order, order_row in user_orders.iterrows():
            proj_raw = str(order_row.get('Project tham gia', '')).replace('nan', '').strip()
            proj_display = f"<b><span style='color: #8B0000;'>{proj_raw.upper()}</span></b>" if proj_raw else ""
            
            tien_vote_raw = str(order_row.get('Số tiền/ Số vote', '')).replace('nan', '').strip()
            if tien_vote_raw.endswith('.0'):
                tien_vote_raw = tien_vote_raw[:-2]
                
            tien_vote_display = tien_vote_raw
            if tien_vote_raw.isdigit():
                val_num = int(tien_vote_raw)
                if val_num > 1000:
                    tien_vote_display = f"{val_num:,.0f} VNĐ"
                else:
                    tien_vote_display = f"{val_num} vote"
            
            gift_list = []
            for col_g in GIFT_COLS:
                val_g = str(order_row.get(col_g, '')).strip().lower()
                if val_g == 'x':
                    gift_list.append(col_g)
            
            str_gifts = "<br>".join([f"• <b><span style='color:#8B0000;'>{g}</span></b>" for g in gift_list]) if gift_list else "<span style='color:#888;'>Không có quà cứng</span>"
            
            card_html = f"""
            <div class='gift-card'>
                <div style='margin-bottom: 5px;'><b>Project bạn đã tham gia:</b> {proj_display}</div>
                <div style='margin-bottom: 5px;'><b>Số tiền/ số vote bạn đã đóng góp:</b> <span style='color: #E74C3C; font-weight: bold;'>{tien_vote_display}</span></div>
                <div style='margin-top: 10px; border-top: 1px dashed #ccc; padding-top: 10px;'>
                    <b>Quà gửi tặng bạn:</b><br>{str_gifts}
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)

        # ================= 4. LƯU Ý THÊM =================
        st.markdown("<div class='section-title'>📝 LƯU Ý THÊM</div>", unsafe_allow_html=True)
        note_goc = str(row_first.get('Note', '')).replace('nan', '')
        if not is_locked:
            input_note = st.text_area("Bạn có muốn nhắn nhủ gì cho mình không?", value=note_goc)
        else:
            st.write(note_goc if note_goc else "Không có lưu ý.")
            input_note = note_goc

        # ================= NÚT CHỐT ĐƠN =================
        if not is_locked:
            if st.button("🚀 XÁC NHẬN / CẬP NHẬT THÔNG TIN", type="primary"):
                if input_tinh == " Vui lòng chọn..." or input_px == " Vui lòng chọn..." or input_dc.strip() == "":
                    st.error("⚠️ Bạn vui lòng điền và chọn đầy đủ thông tin Tỉnh thành, Phường xã và Địa chỉ nhé!")
                elif not is_correct:
                    st.error("⚠️ BẠN CHƯA TICK XÁC NHẬN THÔNG TIN GIAO HÀNG. Vui lòng tick vào ô xác nhận trước khi lưu nhé!")
                else:
                    with st.spinner("Đang lưu thông tin vào hệ thống..."):
                        ss_sdt = (input_sdt.strip() == goc_sdt)
                        ss_dc = (input_dc.strip() == goc_dc)
                        ss_px = (input_px.strip() == goc_px)
                        ss_tinh = (input_tinh.strip() == goc_tinh)
                        
                        tt_moi = "Đã xác nhận" if (ss_sdt and ss_dc and ss_px and ss_tinh) else "Đã cập nhật"
                        
                        conn_update = st.connection("gsheets", type=GSheetsConnection)
                        df_source = conn_update.read(spreadsheet=url, worksheet="Source")
                        df_source.columns = df_source.columns.str.strip()
                        
                        def clean_phone_for_gsheets(x):
                            s = str(x).replace('.0', '').replace("'", "").strip()
                            if s.lower() in ['nan', 'none', '<na>', 'nat', '']: return ""
                            if s.isdigit() and not s.startswith('0'): return '0' + s
                            return s
                            
                        cols_to_update = ['Checked SDT', 'Checked Địa chỉ', 'Checked Phường xã', 'Check Tỉnh thành', 'Note', 'Trạng thái xác nhận']
                        for c in cols_to_update:
                            if c not in df_source.columns:
                                df_source[c] = ""
                            df_source[c] = df_source[c].astype(object)
                            
                        if 'SDT' in df_source.columns:
                            df_source['SDT'] = df_source['SDT'].astype(object).apply(clean_phone_for_gsheets)
                        if 'Checked SDT' in df_source.columns:
                            df_source['Checked SDT'] = df_source['Checked SDT'].astype(object).apply(clean_phone_for_gsheets)

                        df_source['Temp_Phone'] = df_source['SDT'].astype(str).apply(lambda x: x.replace("'", "").lstrip('0'))
                        
                        for s_idx in df_source.index:
                            if df_source.at[s_idx, 'Temp_Phone'] == clean_input:
                                df_source.at[s_idx, 'Checked SDT'] = input_sdt.strip()
                                df_source.at[s_idx, 'Checked Địa chỉ'] = input_dc.strip()
                                df_source.at[s_idx, 'Checked Phường xã'] = input_px.strip()
                                df_source.at[s_idx, 'Check Tỉnh thành'] = input_tinh.strip()
                                df_source.at[s_idx, 'Note'] = input_note.strip()
                                df_source.at[s_idx, 'Trạng thái xác nhận'] = tt_moi
                        
                        df_source = df_source.drop(columns=['Temp_Phone'])
                        
                        conn_update.update(spreadsheet=url, worksheet="Source", data=df_source)
                        st.cache_data.clear() 
                        
                        st.session_state['show_success'] = True
                        if tt_moi == "Đã xác nhận":
                            st.session_state['success_msg'] = "🌱 Bạn đã xác nhận thông tin thành công rồi nha ❤️"
                        else:
                            st.session_state['success_msg'] = "🌱 Bạn đã cập nhật thông tin thành công rồi nha ❤️"
                            
                        st.session_state['search_key'] += 1
                        del st.session_state['verified_phone']
                        
                        st.rerun()


# ================= TAB 2: ADMIN CONFIRM =================
with tab2:
    st.markdown("### 🔒 CỔNG QUẢN TRỊ NỘI BỘ")
    pass_admin = st.text_input("Nhập mật khẩu Admin:", type="password")
    
    if pass_admin == ADMIN_PASSWORD:
        st.success("Đăng nhập thành công!")
        
        is_locked = is_form_locked()
        toggle_lock = st.toggle("🔒 KHÓA CẬP NHẬT (Không cho Fan sửa data nữa)", value=is_locked)
        if toggle_lock != is_locked:
            set_form_lock(toggle_lock)
            st.rerun()
        st.divider()

        # ================= TIẾN ĐỘ XÁC NHẬN =================
        df_unique_phones = df_app.drop_duplicates(subset=['SDT']).copy()
        total_orders = len(df_unique_phones)
        c_xacnhan = len(df_unique_phones[df_unique_phones['Trạng thái xác nhận'].astype(str).str.strip() == 'Đã xác nhận'])
        c_capnhat = len(df_unique_phones[df_unique_phones['Trạng thái xác nhận'].astype(str).str.strip() == 'Đã cập nhật'])
        c_chuaxacnhan = total_orders - c_xacnhan - c_capnhat
        
        st.markdown("#### 📦 TIẾN ĐỘ XÁC NHẬN THÔNG TIN TỔNG (Tính theo Số Điện Thoại)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📦 Tổng SĐT", total_orders)
        col2.metric("👌 Chỉ Xác Nhận", c_xacnhan)
        col3.metric("✍️ Có Cập Nhật", c_capnhat)
        col4.metric("⏳ Đang chờ", c_chuaxacnhan)

        st.divider()

        # ================= THỐNG KÊ QUÀ TẶNG =================
        st.markdown("#### 🎁 THỐNG KÊ TỔNG SỐ LƯỢNG QUÀ")
        
        gift_counts = {}
        for p in GIFT_COLS:
            # FIX: Bọc str(x) để chống lỗi AttributeError y như khúc xuất Excel
            count = df_app[p].apply(lambda x: 1 if str(x).strip().lower() == 'x' else 0).sum()
            gift_counts[p] = count
            
        cols_gift = st.columns(2)
        
        html_tk1 = "<table class='custom-table'><thead><tr><th>Loại Quà</th><th>Số lượng</th></tr></thead><tbody>"
        html_tk2 = "<table class='custom-table'><thead><tr><th>Loại Quà</th><th>Số lượng</th></tr></thead><tbody>"
        
        half = len(GIFT_COLS) // 2
        for i, p in enumerate(GIFT_COLS):
            val = gift_counts[p]
            row_html = f"<tr><td>{p}</td><td><span style='color: #8B0000; font-weight: bold;'>{val}</span></td></tr>"
            if i < half:
                html_tk1 += row_html
            else:
                html_tk2 += row_html
                
        html_tk1 += "</tbody></table>"
        html_tk2 += "</tbody></table>"
        
        cols_gift[0].markdown(html_tk1, unsafe_allow_html=True)
        cols_gift[1].markdown(html_tk2, unsafe_allow_html=True)

        st.divider()
        
        # ================= GỘP ĐƠN & XUẤT EXCEL GHTK =================
        st.markdown("### 🖨️ XUẤT FILE EXCEL GHTK & LABEL (TỰ ĐỘNG GỘP ĐƠN)")
        
        df_export_raw = df_app.copy()
        if 'Mã vận đơn' not in df_export_raw.columns:
            df_export_raw['Mã vận đơn'] = ""
            
        map_cols = [('Checked SDT', 'SDT'), ('Checked Địa chỉ', 'Địa chỉ mới'), 
                    ('Checked Phường xã', 'Phường/Xã mới'), ('Check Tỉnh thành', 'Tỉnh/Thành mới')]
                    
        for c_new, c_old in map_cols:
            actual_new = next((col for col in df_export_raw.columns if c_new.replace(" ", "") == col.replace(" ", "")), None)
            actual_old = next((col for col in df_export_raw.columns if c_old.replace(" ", "") == col.replace(" ", "")), None)
            
            if actual_new and actual_old:
                df_export_raw[actual_old] = df_export_raw[actual_new].replace(['', 'nan', 'None'], pd.NA).fillna(df_export_raw[actual_old])
        
        def gop_diachi_admin(r):
            actual_dc = next((col for col in r.index if "địachỉmới" in str(col).lower().replace(" ", "")), None)
            actual_px = next((col for col in r.index if "phường/xãmới" in str(col).lower().replace(" ", "")), None)
            actual_tt = next((col for col in r.index if "tỉnh/thànhmới" in str(col).lower().replace(" ", "")), None)
            
            dc = str(r[actual_dc]).replace('nan', '').strip() if actual_dc else ""
            px = str(r[actual_px]).replace('nan', '').strip() if actual_px else ""
            tt = str(r[actual_tt]).replace('nan', '').strip() if actual_tt else ""
            
            return ", ".join([x for x in [dc, px, tt] if x])
            
        df_export_raw['Full_Address'] = df_export_raw.apply(gop_diachi_admin, axis=1)
        
        for p in GIFT_COLS:
            df_export_raw[p] = df_export_raw[p].apply(lambda x: 1 if str(x).strip().lower() == 'x' else 0)
        
        agg_dict = {'Họ tên': 'first', 'Full_Address': 'first', 'Mã vận đơn': 'first'}
        for p in GIFT_COLS: agg_dict[p] = 'sum'
        
        df_grouped = df_export_raw.groupby('SDT', as_index=False).agg(agg_dict)
        
        if st.button("Tải File Excel GHTK"):
            df_ghtk = pd.DataFrame()
            df_ghtk['Mã ĐH riêng'] = ""
            df_ghtk['Tên khách hàng'] = df_grouped['Họ tên']
            df_ghtk['SĐT'] = df_grouped['SDT'].astype(str)
            df_ghtk['Địa chỉ chi tiết'] = df_grouped['Full_Address']
            
            def lay_ten_sp(row):
                sp_list = [DICT_GIFT_LABEL[p] for p in GIFT_COLS if row[p] > 0]
                return "Văn phòng phẩm: " + ", ".join(sp_list) if sp_list else "Văn phòng phẩm"
                
            df_ghtk['Tên sản phẩm'] = df_grouped.apply(lay_ten_sp, axis=1)
            df_ghtk['Số lượng'] = 1
            df_ghtk['KL (kg) KT (cm)'] = "5 x 5 x1 | 0.1"
            df_ghtk['Giá trị hàng'] = 1
            df_ghtk['Tiền CoD'] = 0
            df_ghtk['Dịch vụ gia tăng'] = ""
            df_ghtk['Hình thức lấy hàng'] = ""
            df_ghtk['Phiên lấy hàng'] = ""
            df_ghtk['Dịch vụ & Hình thức VC'] = ""
            df_ghtk['Trả ship'] = "Người gửi trả cước"

            output_excel = io.BytesIO()
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df_ghtk.to_excel(writer, index=False, sheet_name='GHTK')
            st.download_button(label="📥 TẢI FILE EXCEL GHTK", data=output_excel.getvalue(), file_name="GHTK_Export.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            
        st.write("")
        
        if st.button("Tạo File In Label (Dán Decal)"):
            html_content = """
            <html><head><meta charset="utf-8">
            <style>
                @page { size: A4 portrait; margin: 10mm; }
                body { font-family: Arial, sans-serif; background-color: #e0e0e0; margin: 0; padding: 20px; }
                .page-a4 { width: 210mm; background-color: white; padding: 10mm; margin: 0 auto; box-shadow: 0 0 10px rgba(0,0,0,0.2); box-sizing: border-box; }
                .grid-container { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; }
                .label-box { width: 100%; min-height: 55mm; background: #fff; border: 1px dashed #000; padding: 6px; border-radius: 4px; box-sizing: border-box; page-break-inside: avoid; }
                .title { font-size: 14px; font-weight: bold; color: #333; border-bottom: 1px solid #ccc; padding-bottom: 2px; margin-bottom: 4px; }
                .info { font-size: 13px; margin-bottom: 2px; line-height: 1.5; }
                .products { font-size: 11px; }
                @media print { body { background-color: white; padding: 0; } .page-a4 { width: 100%; box-shadow: none; padding: 0; margin: 0; } }
            </style></head><body>
            <div class="page-a4"><div class="grid-container">
            """
            
            col1_gifts = GIFT_COLS[0:4]
            col2_gifts = GIFT_COLS[4:8]
            col3_gifts = GIFT_COLS[8:12]
            
            def render_gift_col(row, gift_list):
                html = "<div style='flex: 1;'>"
                for g in gift_list:
                    c = row.get(g, 0)
                    short_n = DICT_GIFT_LABEL[g]
                    if c > 0: html += f"<div style='margin-bottom: 4px;'><span style='color: red;'>✔</span> <b style='color: red;'>{c}x {short_n}</b></div>"
                    else: html += f"<div style='margin-bottom: 4px;'>▢ <span style='font-weight:normal; color:#555;'>{short_n}</span></div>"
                html += "</div>"
                return html

            for _, row in df_grouped.iterrows():
                mvd = str(row.get('Mã vận đơn', '')).replace('nan', '').strip()
                ten = str(row.get('Họ tên', '')).replace('nan', '')
                sdt = str(row.get('SDT', '')).replace('.0', '').replace("'", "")
                diachi = str(row.get('Full_Address', '')).replace('nan', '')
                
                h_c1 = render_gift_col(row, col1_gifts)
                h_c2 = render_gift_col(row, col2_gifts)
                h_c3 = render_gift_col(row, col3_gifts)

                html_content += f"""
                    <div class="label-box">
                        <div class="title">📦 MÃ VĐ: {mvd}</div>
                        <div class="info">👤 <b>{ten}</b> | 📞 {sdt}</div>
                        <div class="info">🏠 {diachi}</div>
                        <div class="products" style="display: flex; justify-content: space-between; margin-top: 5px; font-size: 14px;">
                            {h_c1}{h_c2}{h_c3}
                        </div>
                    </div>
                """
            html_content += "</div></div></body></html>"
            
            st.download_button(label="📥 TẢI FILE IN LABLE (.html)", data=html_content, file_name="Label_Gift.html", mime="text/html")

        st.divider()
        st.markdown("### 💌 LỜI NHẮN NHỦ TỪ FAN")
        df_notes = df_app[df_app['Note'].astype(str).str.strip().replace(['nan', 'None', ''], pd.NA).notna()]
        df_notes = df_notes[df_notes['Note'].astype(str).str.strip() != '']
        
        if not df_notes.empty:
            st.write(f"🥰 Đang có **{len(df_notes)}** lời nhắn siêu dễ thương từ các bạn Fan nè:")
            cols = st.columns(2)
            for idx, (_, row) in enumerate(df_notes.iterrows()):
                note = str(row['Note']).strip()
                sdt = str(row.get('SDT', '')).replace('.0', '').replace("'", "")
                name = str(row.get('Họ tên', '')).replace('nan', '').strip() or "Fan Giấu Tên"
                
                card_html = f"<div style='background-color: #FFF9E6; border-left: 5px solid #8B0000; padding: 15px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>"
                card_html += f"<div style='font-size: 13px; font-weight: bold; color: #8B0000; margin-bottom: 8px;'>👤 {name} <span style='color: #666; font-weight: normal;'>({sdt})</span></div>"
                card_html += f"<div style='font-size: 14px; color: #333; font-style: italic; line-height: 1.5;'>\"{note}\"</div></div>"
                cols[idx % 2].markdown(card_html, unsafe_allow_html=True)
        else:
            st.info("Hiện tại chưa có bạn nào để lại lời nhắn.")
            
    elif pass_admin != "":
        st.error("Sai mật khẩu!")
