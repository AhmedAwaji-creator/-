import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io

# --- 1. إعدادات قاعدة البيانات ---
DB_NAME = 'emergency_system_v200.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_db():
    c.execute('''CREATE TABLE IF NOT EXISTS material_definitions 
                 (item_code TEXT PRIMARY KEY, item_name TEXT, description TEXT, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS inventory 
                 (item_code TEXT, qty INTEGER, warehouse TEXT, contractor TEXT, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings_warehouses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings_contractors (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, full_name TEXT, role TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS return_requests 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, item_code TEXT, qty INTEGER, contractor TEXT, 
                  warehouse TEXT, requester TEXT, status TEXT, date TEXT, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS password_resets 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, phone TEXT, status TEXT, request_time TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS action_logs 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, log_type TEXT, item_code TEXT, qty INTEGER, 
                  details TEXT, user_name TEXT, timestamp TEXT)''')
    
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?)", ("0501104283", "0000", "أحمد عواجي", "مدير نظام"))
    c.execute("INSERT OR IGNORE INTO app_settings VALUES ('logo_url', 'https://cdn.discordapp.com/attachments/1175245476472299581/1504041627310620723/image.png')")
    conn.commit()

init_db()

# --- 2. وظائف مساعدة ---
def add_log(l_type, i_code, qty, details, u_name):
    c.execute("INSERT INTO action_logs (log_type, item_code, qty, details, user_name, timestamp) VALUES (?,?,?,?,?,?)",
              (l_type, i_code, qty, details, u_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()

def get_logo():
    res = pd.read_sql("SELECT value FROM app_settings WHERE key='logo_url'", conn)
    return res.iloc[0]['value'] if not res.empty else ""

# --- 3. التنسيق الجمالي CSS ---
st.set_page_config(page_title="نظام طوارئ شرق جازان", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] { direction: rtl; text-align: right; }
    [data-testid="stSidebar"] { right: 0; left: auto !important; background-color: #fcfcfc; border-left: 1px solid #eeeeee; }
    .centered-sidebar-content { text-align: center; width: 100%; margin-bottom: 20px; }
    .user-info-text { font-size: 1.1rem; color: #1e3d59; font-weight: bold; margin-top: 5px; }
    .role-info-text { font-size: 0.9rem; color: #555; margin-bottom: 10px; }
    .signature-text { font-size: 0.8rem; color: #888; font-style: italic; margin-bottom: 15px; }
    .sidebar-title { color: #1e3d59; font-weight: bold; font-size: 1.1rem; margin-bottom: 2px; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #1e3d59; color: white; height: 3.2em; margin-bottom: 5px; }
    .stButton>button:hover { background-color: #2b5d8a; color: #ffc13b; }
    .logo-container { display: flex; justify-content: center; margin-bottom: 10px; }
    .logo-img { width: 100px; border-radius: 10px; object-fit: contain; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. إدارة الجلسة ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'active_page' not in st.session_state: st.session_state.active_page = "inventory"
if 'forgot_pw' not in st.session_state: st.session_state.forgot_pw = False

# --- 5. نظام الدخول ---
if not st.session_state.logged_in:
    _, col_mid, _ = st.columns([1, 1.2, 1])
    with col_mid:
        if not st.session_state.forgot_pw:
            st.title("🔐 دخول النظام")
            u_id = st.text_input("رقم الجوال")
            u_pw = st.text_input("كلمة المرور", type="password")
            if st.button("تسجيل الدخول"):
                res = pd.read_sql(f"SELECT * FROM users WHERE username='{u_id}' AND password='{u_pw}'", conn)
                if not res.empty:
                    st.session_state.logged_in, st.session_state.user = True, res.iloc[0]
                    st.rerun()
                else: st.error("❌ بيانات الدخول خاطئة")
            if st.button("نسيت كلمة المرور؟"): st.session_state.forgot_pw = True; st.rerun()
        else:
            st.title("🔑 طلب استعادة الحساب")
            f_phone = st.text_input("رقم الجوال المسجل")
            if st.button("إرسال طلب"):
                c.execute("INSERT INTO password_resets (phone, status, request_time) VALUES (?,?,?)", (f_phone, "معلق", datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit(); st.success("🚀 تم إرسال طلبك للمدير")
            if st.button("عودة"): st.session_state.forgot_pw = False; st.rerun()
else:
    user = st.session_state.user
    role = user['role']
    pending_returns = pd.read_sql("SELECT COUNT(*) as t FROM return_requests WHERE status='معلق'", conn).iloc[0]['t']
    pending_resets = pd.read_sql("SELECT COUNT(*) as t FROM password_resets WHERE status='معلق'", conn).iloc[0]['t']

    with st.sidebar:
        logo_url = get_logo()
        if logo_url: st.markdown(f'<div class="logo-container"><img src="{logo_url}" class="logo-img"></div>', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="centered-sidebar-content">
                <div class='sidebar-title'>نظام مواد طوارئ شرق جازان</div>
                <div class='signature-text'>إنشاء بواسطة أحمد عواجي</div>
                <div class="user-info-text">الموظف: {user["full_name"]}</div>
                <div class="role-info-text">نظام الصلاحية: {role}</div>
            </div>
        """, unsafe_allow_html=True)
        st.divider()
        if st.button("📦 المستودع"): st.session_state.active_page = "inventory"
        if st.button("🛒 صرف مواد للمقاول"): st.session_state.active_page = "order"
        
        if role in ["مدير نظام", "مسؤول مستودع"]:
            if st.button("📥 تغذية المستودع"): st.session_state.active_page = "add_stock"
            if st.button("🚛 نقل بين المستودعات"): st.session_state.active_page = "transfer"
            if st.button("🔄 إرجاع مباشر"): st.session_state.active_page = "direct_return"
            if st.button("📑 تعريف الأصناف"): st.session_state.active_page = "manage_items"
            lbl_r = f"✅ قبول الإرجاعات [{pending_returns}]" if pending_returns > 0 else "✅ قبول الإرجاعات"
            if st.button(lbl_r): st.session_state.active_page = "approve_returns"
            if st.button("📜 سجل العمليات"): st.session_state.active_page = "logs"
            
        if role == "موجه بلاغات":
            if st.button("📝 طلب إرجاع مواد"): st.session_state.active_page = "request_return"
            
        if role == "مدير نظام":
            st.divider()
            if st.button("🛠️ إعدادات النظام"): st.session_state.active_page = "settings"
            lbl_p = f"🔑 طلبات كلمة المرور [{pending_resets}]" if pending_resets > 0 else "🔑 طلبات كلمة المرور"
            if st.button(lbl_p): st.session_state.active_page = "manage_resets"
            
        st.divider()
        if st.button("🚪 تسجيل الخروج"): st.session_state.logged_in = False; st.rerun()

    list_whs = pd.read_sql("SELECT name FROM settings_warehouses", conn)['name'].tolist()
    list_conts = pd.read_sql("SELECT name FROM settings_contractors", conn)['name'].tolist()
    list_cats = pd.read_sql("SELECT name FROM settings_categories", conn)['name'].tolist()
    page = st.session_state.active_page

    # --- 6. الصفحات ---

    if page == "inventory":
        st.title("📦 خانة رصيد المستودع")
        tab_code, tab_cat = st.tabs(["🔍 بحث بكود المادة", "🏷️ بحث بالتصنيف"])
        query_base = """SELECT i.category as 'التصنيف', i.item_code as 'الكود', m.item_name as 'المادة', 
                        i.warehouse as 'المستودع', i.contractor as 'المقاول', SUM(i.qty) as 'الكمية' 
                        FROM inventory i LEFT JOIN material_definitions m ON i.item_code = m.item_code
                        GROUP BY i.item_code, i.warehouse, i.contractor HAVING SUM(i.qty) > 0"""
        df_all = pd.read_sql(query_base, conn)

        with tab_code:
            search_code = st.text_input("أدخل كود المادة يدوياً")
            if search_code:
                df_code = df_all[df_all['الكود'].astype(str) == search_code]
                if not df_code.empty: st.table(df_code[['المستودع', 'الكمية', 'التصنيف']])
                else: st.warning("⚠️ هذه المادة غير متوفرة حالياً.")
        with tab_cat:
            search_cat = st.selectbox("اختر التصنيف المخصص", [""] + list_cats)
            if search_cat != "": st.dataframe(df_all[df_all['التصنيف'] == search_cat], use_container_width=True)

    elif page == "manage_items":
        st.title("📑 تعريف الأصناف")
        tab_s, tab_m = st.tabs(["🆕 تعريف مادة مفردة", "🔢 تعريف متعدد (جدول)"])
        
        with tab_s:
            with st.form("single_item"):
                c1, c2 = st.columns(2)
                ni_code = c1.text_input("كود المادة")
                ni_name = c2.text_input("اسم المادة")
                ni_desc = st.text_area("وصف المادة")
                ni_cat = st.selectbox("تصنيف المادة", list_cats)
                if st.form_submit_button("تعريف المادة"):
                    if ni_code and ni_name:
                        c.execute("INSERT OR REPLACE INTO material_definitions VALUES (?,?,?,?)", (ni_code, ni_name, ni_desc, ni_cat))
                        conn.commit(); st.success(f"✅ تم تعريف {ni_name}")
                    else: st.error("الكود والاسم مطلوبان")
        
        with tab_m:
            st.info("استخدم الجدول أدناه لتعريف عدة مواد في وقت واحد.")
            df_m = pd.read_sql("SELECT item_code as 'الكود', item_name as 'الاسم', description as 'الوصف', category as 'التصنيف' FROM material_definitions", conn)
            edited_m = st.data_editor(df_m, num_rows="dynamic", use_container_width=True)
            if st.button("حفظ جميع التغييرات"):
                c.execute("DELETE FROM material_definitions")
                for _, r in edited_m.iterrows():
                    if r['الكود']: c.execute("INSERT INTO material_definitions VALUES (?,?,?,?)", (str(r['الكود']), str(r['الاسم']), str(r['الوصف']), str(r['التصنيف'])))
                conn.commit(); st.success("✅ تم تحديث قاعدة بيانات الأصناف")

    elif page == "settings":
        st.title("🛠️ إعدادات النظام")
        t_users, t_whs, t_conts, t_cats, t_logo = st.tabs(["👥 الموظفين", "🏠 المستودعات", "🏗️ المقاولين", "🏷️ الفئات", "🖼️ الشعار"])
        
        with t_users:
            st.subheader("إدارة الموظفين (تحكم كامل)")
            all_u = pd.read_sql("SELECT * FROM users", conn)
            sel_u_name = st.selectbox("اختر موظف لتعديله أو اختر 'إضافة جديد'", ["إضافة جديد"] + all_u['full_name'].tolist())
            
            with st.form("u_manage"):
                if sel_u_name == "إضافة جديد":
                    v_user, v_pass, v_name, v_role = "", "", "", "مسؤول مستودع"
                else:
                    curr = all_u[all_u['full_name'] == sel_u_name].iloc[0]
                    v_user, v_pass, v_name, v_role = curr['username'], curr['password'], curr['full_name'], curr['role']
                
                new_u = st.text_input("رقم الجوال", v_user)
                new_p = st.text_input("كلمة السر", v_pass)
                new_n = st.text_input("الاسم الكامل", v_name)
                new_r = st.selectbox("الصلاحية", ["مدير نظام", "مسؤول مستودع", "موجه بلاغات"], index=["مدير نظام", "مسؤول مستودع", "موجه بلاغات"].index(v_role))
                
                if st.form_submit_button("حفظ بيانات الموظف"):
                    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?)", (new_u, new_p, new_n, new_r))
                    conn.commit(); st.success("✅ تم الحفظ"); st.rerun()
            
            if sel_u_name != "إضافة جديد" and v_user != "0501104283":
                if st.button("🗑️ حذف هذا الموظف"):
                    c.execute("DELETE FROM users WHERE username=?", (v_user,))
                    conn.commit(); st.success("تم الحذف"); st.rerun()

        with t_whs:
            nw = st.text_input("اسم المستودع")
            if st.button("حفظ المستودع"):
                c.execute("INSERT INTO settings_warehouses (name) VALUES (?)", (nw,)); conn.commit(); st.rerun()
            st.dataframe(pd.read_sql("SELECT name FROM settings_warehouses", conn))
        with t_conts:
            nc = st.text_input("اسم المقاول")
            if st.button("حفظ المقاول"):
                c.execute("INSERT INTO settings_contractors (name) VALUES (?)", (nc,)); conn.commit(); st.rerun()
            st.dataframe(pd.read_sql("SELECT name FROM settings_contractors", conn))
        with t_cats:
            nca = st.text_input("اسم الفئة")
            if st.button("حفظ الفئة"):
                c.execute("INSERT INTO settings_categories (name) VALUES (?)", (nca,)); conn.commit(); st.rerun()
            st.dataframe(pd.read_sql("SELECT name FROM settings_categories", conn))
        with t_logo:
            nl = st.text_input("رابط الشعار", get_logo())
            if st.button("تحديث الشعار"):
                c.execute("UPDATE app_settings SET value=? WHERE key='logo_url'", (nl,)); conn.commit(); st.rerun()

    elif page == "order":
        st.title("🛒 صرف مواد للمقاول")
        with st.form("o_f"):
            c1, c2 = st.columns(2)
            it_code = c1.text_input("كود المادة")
            it_qty = c2.number_input("الكمية", 1)
            wh_f = c1.selectbox("من مستودع", list_whs)
            co_t = c2.selectbox("إلى المقاول", list_conts)
            if st.form_submit_button("تأكيد الصرف"):
                check_def = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{it_code}'", conn)
                if check_def.empty: st.error("⚠️ المادة غير معرفة!")
                else:
                    check_inv = pd.read_sql(f"SELECT SUM(qty) as total FROM inventory WHERE item_code='{it_code}' AND warehouse='{wh_f}'", conn)
                    avail = check_inv.iloc[0]['total'] if not check_inv.empty and check_inv.iloc[0]['total'] else 0
                    if avail < it_qty: st.error(f"⚠️ غير متوفر. المتاح: {avail}")
                    else:
                        cat = check_def.iloc[0]['category']
                        c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (it_code, -it_qty, wh_f, '', cat))
                        c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (it_code, it_qty, '', co_t, cat))
                        add_log("صرف مواد", it_code, it_qty, f"من {wh_f} إلى {co_t}", user['full_name'])
                        conn.commit(); st.success("✅ تم الصرف")

    elif page == "direct_return":
        st.title("🔄 إرجاع مواد مباشر")
        with st.form("dr_f"):
            c1, c2 = st.columns(2)
            it_c, it_q = c1.text_input("كود المادة"), c2.number_input("الكمية", 1)
            cont_f, wh_t = c1.selectbox("من المقاول", list_conts), c2.selectbox("إلى المستودع", list_whs)
            it_cat = st.selectbox("تصنيف المادة", list_cats)
            if st.form_submit_button("تأكيد الإرجاع المباشر"):
                c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (it_c, -it_q, '', cont_f, it_cat))
                c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (it_c, it_q, wh_t, '', it_cat))
                add_log("إرجاع مواد", it_c, it_q, f"مباشر من {cont_f} إلى {wh_t}", user['full_name'])
                conn.commit(); st.success("✅ تم الإرجاع")

    elif page == "approve_returns":
        st.title("✅ قبول إرجاع المواد")
        reqs = pd.read_sql("SELECT * FROM return_requests WHERE status='معلق'", conn)
        if reqs.empty: st.info("🔔 لا توجد طلبات معلقة.")
        else:
            for _, r in reqs.iterrows():
                with st.expander(f"طلب من {r['contractor']} - كود {r['item_code']} ({r['qty']})"):
                    if st.button("قبول الاستلام", key=f"acc_{r['id']}"):
                        c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (r['item_code'], -r['qty'], '', r['contractor'], r['category']))
                        c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (r['item_code'], r['qty'], r['warehouse'], '', r['category']))
                        c.execute("UPDATE return_requests SET status='مقبول' WHERE id=?", (r['id'],))
                        add_log("إرجاع مواد", r['item_code'], r['qty'], f"قبول طلب إرجاع من {r['contractor']}", user['full_name'])
                        conn.commit(); st.rerun()

    elif page == "add_stock":
        st.title("📥 تغذية المستودع")
        with st.form("add_s"):
            c1, c2 = st.columns(2)
            ac = c1.text_input("كود المادة")
            aq = c2.number_input("الكمية المضافة", 1)
            aw = c1.selectbox("المستودع المستهدف", list_whs)
            # إضافة خيار التصنيف المطلوب
            acat = c2.selectbox("تصنيف المادة", list_cats) 
            
            if st.form_submit_button("تغذية الرصيد"):
                if ac:
                    c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (ac, aq, aw, '', acat))
                    add_log("تغذية مستودع", ac, aq, f"إضافة إلى {aw} تحت تصنيف {acat}", user['full_name'])
                    conn.commit(); st.success(f"✅ تمت إضافة {aq} من المادة {ac} إلى {aw}")
                else:
                    st.error("⚠️ يرجى إدخال كود المادة")

    elif page == "transfer":
        st.title("🚛 نقل مواد")
        with st.form("tr_f"):
            tc, tq = st.text_input("كود المادة"), st.number_input("الكمية", 1)
            tf, tt = st.selectbox("من", list_whs, key="f"), st.selectbox("إلى", list_whs, key="t")
            if st.form_submit_button("تأكيد النقل"):
                c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (tc, -tq, tf, '', "عام"))
                c.execute("INSERT INTO inventory VALUES (?,?,?,?,?)", (tc, tq, tt, '', "عام"))
                add_log("نقل مواد", tc, tq, f"من {tf} إلى {tt}", user['full_name'])
                conn.commit(); st.success("✅ تم النقل")

    elif page == "request_return":
        st.title("📝 طلب إرجاع مواد")
        with st.form("req_f"):
            rc, rq = st.text_input("كود المادة"), st.number_input("الكمية", 1)
            rf, rt = st.selectbox("من المقاول", list_conts), st.selectbox("إلى المستودع", list_whs)
            r_cat = st.selectbox("الفئة", list_cats)
            if st.form_submit_button("إرسال الطلب"):
                c.execute("INSERT INTO return_requests (item_code, qty, contractor, warehouse, requester, status, date, category) VALUES (?,?,?,?,?,?,?,?)",
                          (rc, rq, rf, rt, user['full_name'], "معلق", datetime.now().strftime("%Y-%m-%d"), r_cat))
                conn.commit(); st.success("🚀 تم إرسال الطلب")

    elif page == "logs":
        st.title("📜 سجل العمليات")
        df_l = pd.read_sql("SELECT log_type, item_code, qty, details, user_name, timestamp FROM action_logs ORDER BY id DESC", conn)
        st.dataframe(df_l, use_container_width=True)

    elif page == "manage_resets":
        st.title("🔑 طلبات استعادة الحساب")
        resets = pd.read_sql("SELECT * FROM password_resets WHERE status='معلق'", conn)
        if resets.empty: st.info("🔔 لا توجد طلبات معلقة حالياً.")
        for _, r in resets.iterrows():
            if st.button(f"اعتماد معالجة {r['phone']}", key=f"res_{r['id']}"):
                c.execute("UPDATE password_resets SET status='تم' WHERE id=?", (r['id'],))
                conn.commit(); st.rerun()