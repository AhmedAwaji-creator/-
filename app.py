import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import time

# --- 1. الإعدادات وقاعدة البيانات ---
# ملاحظة: عند التشغيل على السحاب، يفضل استخدام قاعدة بيانات دائمة أو ملف محلي كما هو هنا
SYSTEM_CATEGORIES = ["محولات هوائية", "وحدات حلقية", "كابلات", "موصلات", "ترمينيشن", "جونت"]
CONTRACTORS_LIST = [f"مقاول {i}" for i in range(1, 14)]

conn = sqlite3.connect('warehouse_cloud_v1.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS material_definitions 
             (item_code TEXT PRIMARY KEY, item_name TEXT, category TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS inventory 
             (item_code TEXT, qty INTEGER, warehouse TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS logs 
             (emp_name TEXT, action TEXT, details TEXT, qty INTEGER, contractor TEXT, timestamp TEXT)''')
conn.commit()

# --- 2. وظائف النظام ---
def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    return output.getvalue()

# --- 3. تصميم الواجهة (دعم النسخ والجوال) ---
st.set_page_config(page_title="نظام أحمد عواجي للمستودعات", layout="wide")

st.markdown("""
    <style>
    /* جعل النصوص قابلة للنسخ في كل مكان */
    * {
        user-select: text !important;
        -webkit-user-select: text !important;
    }
    /* تحسين شكل الأزرار للجوال */
    .stButton > button {
        width: 100%;
        height: 50px;
        font-size: 18px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. نظام تسجيل الدخول ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 دخول النظام (أحمد عواجي)")
    with st.container():
        user_input = st.text_input("اسم المستخدم (رقم الهوية)")
        pwd_input = st.text_input("كلمة المرور", type="password")
        if st.button("تسجيل الدخول"):
            if user_input == "1102193511" and pwd_input == "0000":
                st.session_state.logged_in = True
                st.session_state.full_name = "أحمد سعيد محمد عواجي"
                st.success("مرحباً بك.. جاري فتح النظام")
                st.rerun()
            else:
                st.error("بيانات الدخول غير صحيحة")
else:
    # القائمة الجانبية
    with st.sidebar:
        st.header(f"👤 {st.session_state.full_name}")
        menu = ["🏠 الأقسام الرئيسية", "⚙️ إدارة المستودع", "🛒 طلب صرف مواد", "🔄 الإرجاع", "📜 سجل الرقابة", "📥 سحب تقرير"]
        choice = st.selectbox("انتقل إلى:", menu)
        if st.button("🚪 خروج"):
            st.session_state.logged_in = False
            st.rerun()

    # --- تنفيذ الأقسام ---
    if choice == "🏠 الأقسام الرئيسية":
        st.title("📂 جرد المخزون")
        cat_choice = st.selectbox("اختر القسم:", ["الكل"] + SYSTEM_CATEGORIES)
        
        query = '''SELECT d.item_code as "كود المادة", d.item_name as "اسم المادة", SUM(i.qty) as "الكمية" 
                   FROM material_definitions d LEFT JOIN inventory i ON d.item_code = i.item_code'''
        if cat_choice != "الكل":
            query += f" WHERE d.category = '{cat_choice}'"
        query += " GROUP BY d.item_code"
        
        df = pd.read_sql(query, conn)
        # استخدام st.dataframe يسمح بنسخ القيم مباشرة
        st.write("تلميح: يمكنك نسخ أي كود مادة مباشرة من الجدول أدناه:")
        st.dataframe(df, use_container_width=True)

    elif choice == "⚙️ إدارة المستودع":
        st.header("⚙️ الإدارة")
        tab1, tab2 = st.tabs(["تعريف مادة", "تغذية مخزون"])
        with tab1:
            ic = st.text_input("كود المادة الجديد")
            iname = st.text_input("اسم المادة الجديد")
            icat = st.selectbox("القسم", SYSTEM_CATEGORIES)
            if st.button("حفظ المادة"):
                c.execute("INSERT OR IGNORE INTO material_definitions VALUES (?,?,?)", (ic, iname, icat))
                conn.commit()
                st.success("تم الحفظ")
        with tab2:
            sc = st.text_input("ادخل كود المادة الموجودة")
            sq = st.number_input("الكمية المضافة", min_value=1)
            sw = st.selectbox("المستودع", ["أ", "ب", "ج"])
            if st.button("إضافة للمخزن"):
                c.execute("INSERT INTO inventory VALUES (?,?,?)", (sc, sq, sw))
                conn.commit()
                st.success("تمت التغذية")

    elif choice == "🛒 طلب صرف مواد":
        st.header("🛒 صرف مواد")
        col1, col2 = st.columns(2)
        ic_in = col1.text_input("كود المادة للصرف")
        qty_in = col2.number_input("الكمية", min_value=1)
        cont_in = st.selectbox("المقاول", CONTRACTORS_LIST)
        
        if st.button("إضافة وتنفيذ الصرف فوراً"):
            # التحقق من المتوفر
            check_inv = pd.read_sql(f"SELECT SUM(qty) as total FROM inventory WHERE item_code='{ic_in}'", conn)
            available = check_inv['total'].iloc[0] or 0
            if available >= qty_in:
                c.execute("INSERT INTO logs VALUES (?,?,?,?,?,?)", 
                          (st.session_state.full_name, "صرف", f"صرف مادة {ic_in}", qty_in, cont_in, datetime.now().strftime("%Y-%m-%d %H:%M")))
                c.execute("UPDATE inventory SET qty = qty - ? WHERE item_code = ? AND rowid IN (SELECT rowid FROM inventory WHERE item_code = ? LIMIT 1)", (qty_in, ic_in, ic_in))
                conn.commit()
                st.success(f"تم صرف {qty_in} للمقاول {cont_in}")
            else:
                st.error(f"الكمية غير كافية! المتوفر فقط: {available}")

    elif choice == "📥 سحب تقرير":
        st.title("📥 تقارير Excel")
        target_cont = st.selectbox("اختر المقاول لاستخراج تقريره:", ["الكل"] + CONTRACTORS_LIST)
        rep_query = "SELECT timestamp as 'التاريخ', details as 'المادة', qty as 'الكمية', contractor as 'المقاول' FROM logs WHERE action='صرف'"
        if target_cont != "الكل":
            rep_query += f" AND contractor='{target_cont}'"
        
        df_rep = pd.read_sql(rep_query, conn)
        st.table(df_rep) # الجدول بصيغة بسيطة تسهل النسخ اليدوي أيضاً
        if not df_rep.empty:
            st.download_button("📥 تحميل ملف Excel", data=to_excel(df_rep), file_name="warehouse_report.xlsx")