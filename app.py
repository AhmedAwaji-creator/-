import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import io
import streamlit.components.v1 as components
import json

# =========================================================
# 1. إعدادات قاعدة البيانات ونظام الجداول الكامل دون اختصار
# =========================================================
DB_NAME = 'awaji_emergency_full_system.db'
conn = sqlite3.connect(DB_NAME, check_same_thread=False)
c = conn.cursor()

def init_database():
    # جدول تعريف المواد الأساسي
    c.execute('''CREATE TABLE IF NOT EXISTS material_definitions (
                    item_code TEXT PRIMARY KEY, 
                    item_name TEXT, 
                    description TEXT, 
                    category TEXT)''')
    
    # جدول حركة وحسابات المخزون المتكاملة
    c.execute('''CREATE TABLE IF NOT EXISTS inventory (
                    item_code TEXT, 
                    qty INTEGER, 
                    warehouse TEXT, 
                    contractor TEXT, 
                    category TEXT)''')
    
    # جداول الثوابت والإعدادات العامة
    c.execute('''CREATE TABLE IF NOT EXISTS settings_warehouses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings_contractors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    red_limit REAL DEFAULT 5.0, 
                    yellow_limit REAL DEFAULT 10.0)''')
    
    # جدول مستخدمي النظام والصلاحيات الكاملة
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY, 
                    password TEXT, 
                    full_name TEXT, 
                    role TEXT)''')
    
    # جدول سجل العمليات التفصيلي لضمان الشفافية والأمان
    c.execute('''CREATE TABLE IF NOT EXISTS action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    log_type TEXT, 
                    item_code TEXT, 
                    qty INTEGER, 
                    details TEXT, 
                    user_name TEXT, 
                    timestamp TEXT, 
                    log_date TEXT)''')
    
    # جدول طلبات إعادة تعيين كلمات المرور للموظفين
    c.execute('''CREATE TABLE IF NOT EXISTS access_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    phone TEXT, 
                    status TEXT, 
                    request_time TEXT)''')
    
    # جدول أرشيف الفواتير المصدرة لتسهيل إعادة الاستخراج الميداني عند الخطأ والتعديل
    c.execute('''CREATE TABLE IF NOT EXISTS archived_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_type TEXT,
                    invoice_no TEXT,
                    warehouse_from TEXT,
                    warehouse_to TEXT,
                    contractor TEXT,
                    employee TEXT,
                    items_json TEXT,
                    html_content TEXT,
                    timestamp TEXT)''')
    
    # حساب مدير النظام الافتراضي الأستان أحمد سعيد عواجي
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?)", ("0501104283", "0000", "أحمد سعيد عواجي", "مدير نظام"))
    conn.commit()

init_database()

# =========================================================
# 2. وظيفة بناء وتوليد فاتورة الصرف (HTML) بدون هوامش بالطباعة
# =========================================================
def render_invoice_html(title, items_list, warehouse, contractor, employee, custom_inv_no=None):
    inv_no = custom_inv_no if custom_inv_no else datetime.now().strftime("%d%H%M")
    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""
    for item in items_list:
        rows += f"""
        <tr>
            <td style="border:1px solid #ddd; padding:10px; text-align:center; font-weight:bold;">{item['code']}</td>
            <td style="border:1px solid #ddd; padding:10px; text-align:right;">{item['name']}</td>
            <td style="border:1px solid #ddd; padding:10px; text-align:center; color:#004a99; font-weight:bold; font-size:16px;">{item['qty']}</td>
        </tr>
        """

    return f"""
    <style>
    @media print {{
        @page {{ size: auto; margin: 0mm; }}
        body {{ margin: 0mm; padding: 10mm; background: white; }}
        .no-print {{ display: none !important; }}
    }}
    </style>
    <div dir="rtl" style="font-family:'Tajawal', Arial, sans-serif; padding:30px; border:3px solid #004a99; border-radius:15px; background-color: white; max-width:900px; margin:auto;">
        <div style="display:flex; justify-content:between; align-items:center; margin-bottom:10px;">
            <div style="text-align:right; width:50%;">
                <h2 style="color:#004a99; margin:0; font-size:24px;">السعودية للطاقة</h2>
                <h3 style="color:#f9a825; margin:5px 0; font-size:20px;">نظام إدارة مواد الطوارئ</h3>
                <p style="font-size:14px; color:#555; margin:2px 0; font-weight:bold;">دائرة شرق منطقة جازان</p>
            </div>
            <div style="text-align:left; width:50%; font-size:14px; color:#333;">
                <p style="margin:2px 0;"><b>رقم الفاتورة:</b> <span style="color:red; font-weight:bold;">{inv_no}</span></p>
                <p style="margin:2px 0;"><b>التاريخ والوقت:</b> {dt_str}</p>
                <p style="margin:2px 0;"><b>الشخص المسؤول:</b> {employee}</p>
            </div>
        </div>
        
        <hr style="border:2px solid #004a99; margin-bottom:20px;">
        
        <h3 style="text-align:center; background:#004a99; color:white; padding:12px; border-radius:8px; font-size:20px; margin-bottom:25px;">{title}</h3>
        
        <div style="background:#f9f9f9; padding:15px; border-radius:8px; margin-bottom:25px; border:1px solid #eee; font-size:15px;">
            <table style="width:100%; border:none;">
                <tr>
                    <td><b>المستودع المعني:</b> {warehouse if warehouse else 'N/A'}</td>
                    <td><b>المقاول / الجهة المستلمة:</b> {contractor if contractor else 'N/A'}</td>
                </tr>
            </table>
        </div>
        
        <table style="width:100%; border-collapse:collapse; margin-top:15px; font-size:15px;">
            <thead>
                <tr style="background:#004a99; color:white;">
                    <th style="border:1px solid #004a99; padding:12px; width:25%;">كود المادة</th>
                    <th style="border:1px solid #004a99; padding:12px; width:55%; text-align:right;">وصف وصنف المادة</th>
                    <th style="border:1px solid #004a99; padding:12px; width:20%;">الكمية</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        
        <div style="margin-top:60px; display:flex; justify-content:space-between; text-align:center; font-size:15px;">
            <div style="width:45%;">
                <p><b>توقيع مسؤول المستودع</b></p>
                <br><br>
                <p>_______________________</p>
            </div>
            <div style="width:45%;">
                <p><b>توقيع المقاول / المستلم للمواد</b></p>
                <br><br>
                <p>_______________________</p>
            </div>
        </div>
        
        <div style="text-align:center; margin-top:40px;" class="no-print">
            <button onclick="window.print()" style="padding:12px 35px; background:#f9a825; color:white; border:none; border-radius:6px; font-size:16px; font-weight:bold; cursor:pointer; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">🖨️ اضغط هنا لطباعة الفاتورة</button>
        </div>
    </div>
    """
    # =========================================================
# 3. وظيفة بناء وتوليد فاتورة الارتجاع المنفصلة (HTML) بدون هوامش
# =========================================================
def render_return_invoice_html(title, items_list, warehouse, contractor, employee, custom_inv_no=None):
    inv_no = custom_inv_no if custom_inv_no else datetime.now().strftime("%d%H%M")
    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""
    for item in items_list:
        rows += f"""
        <tr>
            <td style="border:1px solid #ddd; padding:10px; text-align:center; font-weight:bold;">{item['code']}</td>
            <td style="border:1px solid #ddd; padding:10px; text-align:right;">{item['name']}</td>
            <td style="border:1px solid #ddd; padding:10px; text-align:center; color:#004a99; font-weight:bold; font-size:16px;">{item['qty']}</td>
        </tr>
        """

    return f"""
    <style>
    @media print {{
        @page {{ size: auto; margin: 0mm; }}
        body {{ margin: 0mm; padding: 10mm; background: white; }}
        .no-print {{ display: none !important; }}
    }}
    </style>
    <div dir="rtl" style="font-family:'Tajawal', Arial, sans-serif; padding:30px; border:3px solid #004a99; border-radius:15px; background-color: white; max-width:900px; margin:auto;">
        <div style="display:flex; justify-content:between; align-items:center; margin-bottom:10px;">
            <div style="text-align:right; width:50%;">
                <h2 style="color:#004a99; margin:0; font-size:24px;">السعودية للطاقة</h2>
                <h3 style="color:#f9a825; margin:5px 0; font-size:20px;">نظام إدارة مواد الطوارئ</h3>
                <p style="font-size:14px; color:#555; margin:2px 0; font-weight:bold;">دائرة شرق منطقة جازان</p>
            </div>
            <div style="text-align:left; width:50%; font-size:14px; color:#333;">
                <p style="margin:2px 0;"><b>رقم الفاتورة:</b> <span style="color:red; font-weight:bold;">{inv_no}</span></p>
                <p style="margin:2px 0;"><b>التاريخ والوقت:</b> {dt_str}</p>
                <p style="margin:2px 0;"><b>مسؤول المستودع المستلم:</b> {employee}</p>
            </div>
        </div>
        
        <hr style="border:2px solid #004a99; margin-bottom:20px;">
        
        <h3 style="text-align:center; background:#004a99; color:white; padding:12px; border-radius:8px; font-size:20px; margin-bottom:25px;">{title}</h3>
        
        <div style="background:#f9f9f9; padding:15px; border-radius:8px; margin-bottom:25px; border:1px solid #eee; font-size:15px;">
            <table style="width:100%; border:none;">
                <tr>
                    <td><b>المقاول المسلّم:</b> {contractor if contractor else 'N/A'}</td>
                    <td><b>المستودع المستلم:</b> {warehouse if warehouse else 'N/A'}</td>
                </tr>
            </table>
        </div>
        
        <table style="width:100%; border-collapse:collapse; margin-top:15px; font-size:15px;">
            <thead>
                <tr style="background:#004a99; color:white;">
                    <th style="border:1px solid #004a99; padding:12px; width:25%;">كود المادة</th>
                    <th style="border:1px solid #004a99; padding:12px; width:55%; text-align:right;">وصف وصنف المادة</th>
                    <th style="border:1px solid #004a99; padding:12px; width:20%;">الكمية</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        
        <div style="margin-top:60px; display:flex; justify-content:space-between; text-align:center; font-size:15px;">
            <div style="width:45%;">
                <p><b>توقيع مسؤول المستودع</b></p>
                <br><br>
                <p>_______________________</p>
            </div>
            <div style="width:45%;">
                <p><b>توقيع المقاول المسلّم للمواد</b></p>
                <br><br>
                <p>_______________________</p>
            </div>
        </div>
        
        <div style="text-align:center; margin-top:40px;" class="no-print">
            <button onclick="window.print()" style="padding:12px 35px; background:#f9a825; color:white; border:none; border-radius:6px; font-size:16px; font-weight:bold; cursor:pointer; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">🖨️ اضغط هنا لطباعة الفاتورة</button>
        </div>
    </div>
    """

# =========================================================
# 4. وظيفة بناء وتوليد فاتورة النقل بين المستودعات (HTML) بدون هوامش
# =========================================================
def render_transfer_invoice_html(title, items_list, wh_from, wh_to, employee, custom_inv_no=None):
    inv_no = custom_inv_no if custom_inv_no else datetime.now().strftime("%d%H%M")
    dt_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""
    for item in items_list:
        rows += f"""
        <tr>
            <td style="border:1px solid #ddd; padding:10px; text-align:center; font-weight:bold;">{item['code']}</td>
            <td style="border:1px solid #ddd; padding:10px; text-align:right;">{item['name']}</td>
            <td style="border:1px solid #ddd; padding:10px; text-align:center; color:#004a99; font-weight:bold; font-size:16px;">{item['qty']}</td>
        </tr>
        """

    return f"""
    <style>
    @media print {{
        @page {{ size: auto; margin: 0mm; }}
        body {{ margin: 0mm; padding: 10mm; background: white; }}
        .no-print {{ display: none !important; }}
    }}
    </style>
    <div dir="rtl" style="font-family:'Tajawal', Arial, sans-serif; padding:30px; border:3px solid #004a99; border-radius:15px; background-color: white; max-width:900px; margin:auto;">
        <div style="display:flex; justify-content:between; align-items:center; margin-bottom:10px;">
            <div style="text-align:right; width:50%;">
                <h2 style="color:#004a99; margin:0; font-size:24px;">السعودية للطاقة</h2>
                <h3 style="color:#f9a825; margin:5px 0; font-size:20px;">نظام إدارة مواد الطوارئ</h3>
                <p style="font-size:14px; color:#555; margin:2px 0; font-weight:bold;">دائرة شرق منطقة جازان</p>
            </div>
            <div style="text-align:left; width:50%; font-size:14px; color:#333;">
                <p style="margin:2px 0;"><b>رقم الفاتورة:</b> <span style="color:red; font-weight:bold;">{inv_no}</span></p>
                <p style="margin:2px 0;"><b>التاريخ والوقت:</b> {dt_str}</p>
                <p style="margin:2px 0;"><b>الشخص المسؤول:</b> {employee}</p>
            </div>
        </div>
        
        <hr style="border:2px solid #004a99; margin-bottom:20px;">
        
        <h3 style="text-align:center; background:#004a99; color:white; padding:12px; border-radius:8px; font-size:20px; margin-bottom:25px;">{title}</h3>
        
        <div style="background:#f9f9f9; padding:15px; border-radius:8px; margin-bottom:25px; border:1px solid #eee; font-size:15px;">
            <table style="width:100%; border:none;">
                <tr>
                    <td><b>المستودع المنقول منه:</b> {wh_from if wh_from else 'N/A'}</td>
                    <td><b>المستودع المنقول إليه:</b> {wh_to if wh_to else 'N/A'}</td>
                </tr>
            </table>
        </div>
        
        <table style="width:100%; border-collapse:collapse; margin-top:15px; font-size:15px;">
            <thead>
                <tr style="background:#004a99; color:white;">
                    <th style="border:1px solid #004a99; padding:12px; width:25%;">كود المادة</th>
                    <th style="border:1px solid #004a99; padding:12px; width:55%; text-align:right;">وصف وصنف المادة</th>
                    <th style="border:1px solid #004a99; padding:12px; width:20%;">الكمية</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        
        <div style="margin-top:60px; display:flex; justify-content:space-between; text-align:center; font-size:15px;">
            <div style="width:45%;">
                <p><b>توقيع مسؤول المستودع</b></p>
                <br><br>
                <p>_______________________</p>
            </div>
            <div style="width:45%;">
                <p><b>توقيع أمين المستودع المستلم</b></p>
                <br><br>
                <p>_______________________</p>
            </div>
        </div>
        
        <div style="text-align:center; margin-top:40px;" class="no-print">
            <button onclick="window.print()" style="padding:12px 35px; background:#f9a825; color:white; border:none; border-radius:6px; font-size:16px; font-weight:bold; cursor:pointer; box-shadow: 0px 4px 6px rgba(0,0,0,0.1);">🖨️ اضغط هنا لطباعة الفاتورة</button>
        </div>
    </div>
    """

# =========================================================
# 5. الوظائف البرمجية المساعدة (التسجيل والتصدير)
# =========================================================
def save_log(log_type, item_code, qty, details, user_name):
    now = datetime.now()
    log_date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO action_logs (log_type, item_code, qty, details, user_name, timestamp, log_date) 
                 VALUES (?,?,?,?,?,?,?)""", (log_type, item_code, qty, details, user_name, timestamp, log_date))
    conn.commit()

def archive_invoice(invoice_type, invoice_no, wh_from, wh_to, contractor, employee, items_json, html_content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO archived_invoices (invoice_type, invoice_no, warehouse_from, warehouse_to, contractor, employee, items_json, html_content, timestamp)
                 VALUES (?,?,?,?,?,?,?,?,?)""", (invoice_type, invoice_no, wh_from, wh_to, contractor, employee, items_json, html_content, timestamp))
    conn.commit()

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='التقرير المخرجات')
    return output.getvalue()

# =========================================================
# 6. واجهة المستخدم الرسومية وإعدادات الـ CSS البصرية الكاملة
# =========================================================
st.set_page_config(page_title="نظام إدارة مواد الطوارئ - دائرة شرق منطقة جازان", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Tajawal', sans-serif; direction: rtl; text-align: right; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; background-color: #004a99; color: white; height: 3em; font-size:15px; }
    .stButton>button:hover { background-color: #003366; border-color: #f9a825; }
    .main-title { color: #004a99; text-align: center; font-size: 28px; font-weight: bold; border-bottom: 3px solid #f9a825; padding-bottom: 12px; margin-bottom: 30px; }
    .sidebar-header { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #004a99; text-align: center; margin-bottom: 15px; color: #004a99; }
    .creator-info { font-size: 11px; text-align: center; color: #666; margin-top: 25px; border-top: 1px solid #ddd; padding-top: 12px; }
    .report-box { background-color: #f1f3f6; padding: 15px; border-radius: 10px; border-right: 6px solid #004a99; margin-bottom: 15px; }
    .operation-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0px 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .btn-danger>div>button { background-color: #d32f2f !important; color: white !important; }
    .btn-danger>div>button:hover { background-color: #b71c1c !important; }
    .btn-success>div>button { background-color: #2e7d32 !important; color: white !important; }
    .btn-success>div>button:hover { background-color: #1b5e20 !important; }
    @media print { .no-print { display: none !important; } }
    </style>
    """, unsafe_allow_html=True)

# استدعاء والتحقق من متغيرات الجلسة (Session State)
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'page' not in st.session_state: st.session_state.page = "inventory_status"

# متغيرات السلات المحدثة (الصرف، الارتجاع، النقل)
if 'cart' not in st.session_state: st.session_state.cart = []
if 'return_cart' not in st.session_state: st.session_state.return_cart = []
if 'transfer_cart' not in st.session_state: st.session_state.transfer_cart = []

# أزرار وحالات المراجعة المسبقة والتأكيد قبل الخصم والأرشفة
if 'review_out' not in st.session_state: st.session_state.review_out = False
if 'review_return' not in st.session_state: st.session_state.review_return = False
if 'review_transfer' not in st.session_state: st.session_state.review_transfer = False

if 'last_inv_html' not in st.session_state: st.session_state.last_inv_html = None
if 'last_ret_inv_html' not in st.session_state: st.session_state.last_ret_inv_html = None
if 'last_trans_inv_html' not in st.session_state: st.session_state.last_trans_inv_html = None
if 'view_archived_html' not in st.session_state: st.session_state.view_archived_html = {}

# مفاتيح التحكم لتصفير الحقول آلياً عند الضغط على زر الإضافة للسلة
if 'input_out_code' not in st.session_state: st.session_state.input_out_code = 0
if 'input_out_qty' not in st.session_state: st.session_state.input_out_qty = 0
if 'input_ret_code' not in st.session_state: st.session_state.input_ret_code = 0
if 'input_ret_qty' not in st.session_state: st.session_state.input_ret_qty = 0
if 'input_trans_code' not in st.session_state: st.session_state.input_trans_code = 0
if 'input_trans_qty' not in st.session_state: st.session_state.input_trans_qty = 0

# شاشة تسجيل الدخول الإلزامية لتأمين النظام
if not st.session_state.auth:
    st.markdown("<div class='main-title'>السعودية للطاقة<br>نظام إدارة مواد طوارئ دائرة شرق منطقة جازان</div>", unsafe_allow_html=True)
    _, col_login, _ = st.columns([1, 1.2, 1])
    
    with col_login:
        st.markdown("""
        <div style='text-align:center; margin-bottom:15px;'>
            <img src="https://img.icons8.com/color/96/shield-security.png" width="60">
        </div>
        """, unsafe_allow_html=True)
        st.subheader("🔐 بوابة تسجيل دخول المستخدمين")
        login_user = st.text_input("رقم الجوال الخاص بالموظف")
        login_pass = st.text_input("كلمة المرور السرية", type="password")
        
        if st.button("تسجيل الدخول إلى النظام"):
            res = pd.read_sql(f"SELECT * FROM users WHERE username='{login_user}' AND password='{login_pass}'", conn)
            if not res.empty:
                st.session_state.auth = True
                st.session_state.user_info = res.iloc[0]
                st.success("تم التحقق بنجاح، جاري الدخول...")
                st.rerun()
            else: 
                st.error("بيانات الدخول خاطئة، يرجى إعادة المحاولة والتحقق من كلمة المرور.")
        
        st.divider()
        if st.button("إرسال طلب إعادة تعيين كلمة المرور"):
            if login_user:
                c.execute("INSERT INTO access_requests (phone, status, request_time) VALUES (?,?,?)", 
                          (login_user, "معلق", datetime.now().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.success("تم إرسال طلب تصفير كلمة المرور لمدير النظام بنجاح.")
            else: 
                st.warning("يرجى إدخال رقم جوالك أولاً في حقل اسم المستخدم ليتم رفعه للنظام.")

# =========================================================
# 7. بيئة عمل النظام الرئيسية (القوائم والتبويبات الشاملة)
# =========================================================
else:
    u = st.session_state.user_info
    
    # بناء شريط التنقل الجانبي بالكامل بالمسميات الأصلية
    with st.sidebar:
        st.markdown(f"""
        <div class='sidebar-header'>
            <img src="https://img.icons8.com/color/96/electricity.png" width="55"><br>
            <b style='font-size:16px;'>نظام إدارة مواد الطوارئ</b><br>
            <span style='color:#f9a825; font-size:13px; font-weight:bold;'>دائرة شرق منطقة جازان</span><br>
            <hr style="margin:12px 0; border:1px solid #004a99;">
            <span style='font-size:13px; color:#555;'>👤 المسؤول: <b>{u['full_name']}</b></span><br>
            <span style='font-size:12px; background:#e1f5fe; color:#0288d1; padding:2px 8px; border-radius:10px;'>{u['role']}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # أزرار الاستعلامات والتقارير العامة
        if st.button("📊 رصيد المستودعات"): st.session_state.page = "inventory_status"
        if st.button("📑 تعريف مواد جديدة"): st.session_state.page = "item_defs"
        if st.button("⚠️ تنبيهات نقص مواد"): st.session_state.page = "alerts_page"
        
        st.divider()
        st.sidebar.markdown("<p style='text-align:center; font-weight:bold; color:#004a99; margin:0;'>📦 العمليات المخزنية الميدانية</p>", unsafe_allow_html=True)
        if st.button("📥 إضافة مواد إلى المستودع"): st.session_state.page = "stock_in"
        if st.button("🛒 صرف مواد للمقاول"): st.session_state.page = "stock_out"
        if st.button("🔄 ارجاع المواد"): st.session_state.page = "stock_return"
        if st.button("🚛 نقل مادة من مستودع إلى آخر"): st.session_state.page = "stock_transfer"
        
        st.divider()
        if st.button("🛠️ سجل العمليات التفصيلي"): st.session_state.page = "view_logs"
        
        # تبويبات خاصة بمدير النظام
        if u['role'] == "مدير نظام":
            st.divider()
            st.sidebar.markdown("<p style='text-align:center; font-weight:bold; color:#004a99; margin:0;'>⚙️ التحكم بالنظام</p>", unsafe_allow_html=True)
            if st.button("👥 إدارة حسابات الموظفين والطلبات"): st.session_state.page = "manage_staff"
            if st.button("🛠️ الثوابت والإعدادات العامة"): st.session_state.page = "global_settings"
        
        st.divider()
        if st.button("🚪 خروج من النظام"):
            st.session_state.auth = False
            st.session_state.user_info = None
            st.rerun()
            
        st.markdown(f"""
        <div class='creator-info'>
            تم تطويره بواسطة: أحمد سعيد عواجي<br>
            جميع الحقوق محفوظة لصيانة اعطال دائرة الشرق © 2026
        </div>
        """, unsafe_allow_html=True)

    # جلب قوائم الثوابت المسجلة لاستعمالها في حقول الإدخال والتحقق السريع
    list_warehouses = pd.read_sql("SELECT name FROM settings_warehouses", conn)['name'].tolist()
    list_contractors = pd.read_sql("SELECT name FROM settings_contractors", conn)['name'].tolist()
    list_categories = pd.read_sql("SELECT name FROM settings_categories", conn)['name'].tolist()

    # ---------------------------------------------------------
    # صفحة: رصيد المستودعات والبحث المتقدم
    # ---------------------------------------------------------
    if st.session_state.page == "inventory_status":
        st.markdown("<div class='main-title'>📊 المواد المتوفرة في المستودعات</div>", unsafe_allow_html=True)
        
        col_s1, col_s2 = st.columns([2, 1])
        search_txt = col_s1.text_input("🔍 ابحث فوراً بكتابة كود المادة أو اسم الصنف بدقة")
        cat_filter = col_s2.selectbox("تصفية بحسب الفئة وتصنيف المواد", ["عرض الكل"] + list_categories)
        
        query = """SELECT i.item_code as 'كود المادة', m.item_name as 'اسم الصنف والمادة التفصيلي', 
                   i.category as 'تصنيف الفئة', i.warehouse as 'موقع المستودع', SUM(i.qty) as 'الرصيد المتاح حالياً' 
                   FROM inventory i JOIN material_definitions m ON i.item_code = m.item_code 
                   WHERE i.warehouse != '' """
        
        if cat_filter != "عرض الكل": 
            query += f" AND i.category='{cat_filter}'"
        query += " GROUP BY i.item_code, i.warehouse HAVING SUM(i.qty) > 0"
        
        df_inventory = pd.read_sql(query, conn)
        
        if search_txt:
            df_inventory = df_inventory[df_inventory['اسم الصنف والمادة التفصيلي'].str.contains(search_txt, na=False) |
                                        df_inventory['كود المادة'].str.contains(search_txt, na=False)]
            
        if not df_inventory.empty:
            st.dataframe(df_inventory, use_container_width=True, hide_index=True)
            excel_view = to_excel(df_inventory)
            st.download_button("📥 تصدير رصيد المخزون الحالي المعروض إلى ملف Excel", excel_view, "جرد_المخزون.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("⚠️ لا توجد أي مواد أو أرصدة مخزنية مسجلة تحت شروط البحث المحددة حالياً.")

     # ---------------------------------------------------------
    # صفحة: تعريف مواد جديدة في كشاف النظام المحدثة (التعريف المتعدد)
    # ---------------------------------------------------------
    elif st.session_state.page == "item_defs":
        st.markdown("<div class='main-title'>📝 تعريف مواد غير مضافة في النظام</div>", unsafe_allow_html=True)
        if not list_categories:
            st.warning("⚠️ يرجى أولاً تدوين وتثبيت فئة أصناف واحدة على الأقل من لوحة الإعدادات العامة لربط المواد بها.")
        else:
            if "num_materials_rows" not in st.session_state:
                st.session_state.num_materials_rows = 3
            col_control1, col_control2 = st.columns([1, 4])
            with col_control1:
                new_rows_count = st.number_input("عدد المواد المراد تعريفها معاً:", min_value=1, max_value=20, value=st.session_state.num_materials_rows, step=1)
                if new_rows_count != st.session_state.num_materials_rows:
                    st.session_state.num_materials_rows = new_rows_count
                    st.rerun()
            st.write("---")
            with st.form("multi_material_define_form", clear_on_submit=True):
                inserted_data = []
                for i in range(st.session_state.num_materials_rows):
                    st.markdown(f"##### 📦 المادة رقم ({i+1}) :")
                    c1, c2, c3, c4 = st.columns([1.5, 2, 2.5, 1.5])
                    item_code_input = c1.text_input(f"كود المادة *", key=f"m_code_{i}").strip()
                    item_name_input = c2.text_input(f"اسم المادة *", key=f"m_name_{i}").strip()
                    item_desc_input = c3.text_input(f"الوصف الفني التفصيلي", key=f"m_desc_{i}").strip()
                    item_cat_input = c4.selectbox(f"الفئة التابعة لها *", list_categories, key=f"m_cat_{i}")
                    
                    if item_code_input and item_name_input:
                        inserted_data.append({
                            'code': item_code_input,
                            'name': item_name_input,
                            'desc': item_desc_input,
                            'cat': item_cat_input
                        })
                st.markdown("<p style='margin-bottom:15px;'></p>", unsafe_allow_html=True)
                st.write("---")
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                submit_multi = st.form_submit_button("🚀 حفظ واعتماد كافة المواد المدخلة دفعة واحدة")
                st.markdown("</div>", unsafe_allow_html=True)
                
                if submit_multi:
                    if not inserted_data:
                        st.error("⚠️ لم تقم بملء بيانات أي مادة! يرجى كتابة (كود المادة واسم المادة) على الأقل للأصناف المراد حفظها.")
                    else:
                        success_count = 0
                        skipped_codes = []
                        for mat in inserted_data:
                            check_exist = pd.read_sql(f"SELECT item_code FROM material_definitions WHERE item_code='{mat['code']}'", conn)
                            if check_exist.empty:
                                c.execute("INSERT INTO material_definitions (item_code, item_name, description, category) VALUES (?,?,?,?)",
                                          (mat['code'], mat['name'], mat['desc'], mat['cat']))
                                save_log("تعريف صنف جديد", mat['code'], 0, f"تعريف متعدد - الاسم: {mat['name']} | فئة: {mat['cat']}", u['full_name'])
                                success_count += 1
                            else:
                                skipped_codes.append(mat['code'])
                        conn.commit()
                        if success_count > 0:
                            st.success(f"🎉 تم بنجاح تعريف وحفظ ({success_count}) صنف جديد في كشاف النظام!")
                        if skipped_codes:
                            st.warning(f"⚠️ الأكواد التالية ({', '.join(skipped_codes)}) لم يتم حفظها لأنها معرفة ومسجلة في النظام مسبقاً!")
                        st.session_state.num_materials_rows = 3
                        st.rerun()
 
            st.divider()
            st.write("##### 📋 كشاف وصنف المواد المعرفة حالياً في المنظومة:")
 
            # ── شريط البحث السريع في الجدول ──
            search_mat = st.text_input("🔍 ابحث بكود أو اسم المادة لتسريع التعديل:", key="search_mat_table").strip()
 
            df_current_materials = pd.read_sql(
                "SELECT item_code, item_name, description, category FROM material_definitions ORDER BY item_code ASC", conn
            )
 
            if search_mat:
                df_current_materials = df_current_materials[
                    df_current_materials['item_code'].str.contains(search_mat, case=False, na=False) |
                    df_current_materials['item_name'].str.contains(search_mat, case=False, na=False)
                ]
 
            if df_current_materials.empty:
                st.info("ℹ️ لا توجد مواد أو أصناف معرفة في كشاف النظام تطابق البحث.")
            else:
                st.caption(f"📦 إجمالي المواد المعروضة: {len(df_current_materials)} صنف — اضغط على أي صنف لتعديله أو حذفه.")
 
                # رأس الجدول
                hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([1.2, 2, 2.5, 1.5, 1.2])
                hcol1.markdown("**كود المادة**")
                hcol2.markdown("**اسم المادة**")
                hcol3.markdown("**الوصف الفني**")
                hcol4.markdown("**الفئة**")
                hcol5.markdown("**الإجراءات**")
                st.markdown("<hr style='margin:4px 0 8px 0;'>", unsafe_allow_html=True)
 
                for idx, row in df_current_materials.iterrows():
                    orig_code = row['item_code']
                    row_key = f"mat_{orig_code}"
 
                    # تهيئة حالة التعديل لكل صف
                    if f"edit_mode_{row_key}" not in st.session_state:
                        st.session_state[f"edit_mode_{row_key}"] = False
 
                    col1, col2, col3, col4, col5 = st.columns([1.2, 2, 2.5, 1.5, 1.2])
 
                    if st.session_state[f"edit_mode_{row_key}"]:
                        # ── وضع التعديل ──
                        with st.form(f"edit_mat_form_{row_key}", clear_on_submit=False):
                            e1, e2, e3, e4 = st.columns([1.2, 2, 2.5, 1.5])
                            new_code = e1.text_input("الكود", value=row['item_code'], key=f"ec_{row_key}")
                            new_name = e2.text_input("الاسم", value=row['item_name'], key=f"en_{row_key}")
                            new_desc = e3.text_input("الوصف", value=row['description'] if row['description'] else "", key=f"ed_{row_key}")
                            cat_idx = list_categories.index(row['category']) if row['category'] in list_categories else 0
                            new_cat = e4.selectbox("الفئة", list_categories, index=cat_idx, key=f"ecat_{row_key}")
 
                            btn_save, btn_cancel = st.columns([1, 1])
                            save_clicked = btn_save.form_submit_button("💾 حفظ")
                            cancel_clicked = btn_cancel.form_submit_button("❌ إلغاء")
 
                            if save_clicked:
                                new_code = new_code.strip()
                                new_name = new_name.strip()
                                if not new_code or not new_name:
                                    st.error("⚠️ الكود والاسم حقول إلزامية.")
                                else:
                                    # التحقق من تكرار الكود عند تغييره
                                    if new_code != orig_code:
                                        dup = pd.read_sql(f"SELECT item_code FROM material_definitions WHERE item_code='{new_code}'", conn)
                                        if not dup.empty:
                                            st.error(f"❌ الكود ({new_code}) مستخدم لمادة أخرى!")
                                            st.stop()
 
                                    c.execute(
                                        "UPDATE material_definitions SET item_code=?, item_name=?, description=?, category=? WHERE item_code=?",
                                        (new_code, new_name, new_desc.strip(), new_cat, orig_code)
                                    )
                                    # تحديث الكود في جداول المخزون والسجلات إن تغيّر
                                    if new_code != orig_code:
                                        c.execute("UPDATE inventory SET item_code=? WHERE item_code=?", (new_code, orig_code))
                                        c.execute("UPDATE action_logs SET item_code=? WHERE item_code=?", (new_code, orig_code))
 
                                    save_log("تعديل بيانات مادة", new_code, 0,
                                             f"تعديل المادة [{orig_code}] → كود: {new_code} | اسم: {new_name} | فئة: {new_cat}",
                                             u['full_name'])
                                    conn.commit()
                                    st.session_state[f"edit_mode_{row_key}"] = False
                                    st.success(f"✅ تم تحديث بيانات المادة [{new_name}] بنجاح!")
                                    st.rerun()
 
                            if cancel_clicked:
                                st.session_state[f"edit_mode_{row_key}"] = False
                                st.rerun()
 
                    else:
                        # ── وضع العرض العادي ──
                        col1.write(row['item_code'])
                        col2.write(row['item_name'])
                        col3.write(row['description'] if row['description'] else "—")
                        col4.write(row['category'])
 
                        with col5:
                            btn_e, btn_d = st.columns([1, 1])
                            if btn_e.button("✏️", key=f"edit_btn_{row_key}", help="تعديل بيانات المادة"):
                                st.session_state[f"edit_mode_{row_key}"] = True
                                st.rerun()
 
                            if btn_d.button("🗑️", key=f"del_btn_{row_key}", help="حذف المادة نهائياً"):
                                st.session_state[f"confirm_del_{row_key}"] = True
 
                        # رسالة تأكيد الحذف
                        if st.session_state.get(f"confirm_del_{row_key}", False):
                            st.warning(f"⚠️ هل أنت متأكد من حذف المادة **{row['item_name']}** ({orig_code}) نهائياً؟ لا يمكن التراجع عن هذا الإجراء.")
                            conf1, conf2 = st.columns([1, 1])
                            if conf1.button("✅ نعم، احذف نهائياً", key=f"yes_del_{row_key}"):
                                c.execute("DELETE FROM material_definitions WHERE item_code=?", (orig_code,))
                                save_log("حذف مادة", orig_code, 0,
                                         f"تم حذف المادة [{row['item_name']}] من كشاف النظام نهائياً",
                                         u['full_name'])
                                conn.commit()
                                st.session_state[f"confirm_del_{row_key}"] = False
                                st.success(f"✅ تم حذف المادة ({orig_code}) بنجاح.")
                                st.rerun()
                            if conf2.button("🚫 لا، إلغاء الحذف", key=f"no_del_{row_key}"):
                                st.session_state[f"confirm_del_{row_key}"] = False
                                st.rerun()
 
                    st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
                # ---------------------------------------------------------
    # صفحة: تنبيهات مستويات الخطر وقوائم الطلب السريع والآلي
    # ---------------------------------------------------------
    elif st.session_state.page == "alerts_page":
        st.markdown("<div class='main-title'>⚠️ تقرير المواد التي اقتربت نهايتها من المخزون</div>", unsafe_allow_html=True)
        st.write("### 📋 استخراج مسودات ومستندات نقص المواد")
        col_filter1, col_filter2 = st.columns([2, 1])
        status_filter = col_filter1.selectbox("اختر مستوى فرز المواد لإنشاء ملف الطلبيات الميدانية:", ["عرض كافة النواقص (الحرج والتنبيه)", "🔴 نقص حاد وحرج جداً (الأحمر)", "🟡 تخطي حد التنبيه الآمن (الأصفر)"])
        
        df_alert_data = pd.read_sql("""
            SELECT i.item_code as 'كود المادة', m.item_name as 'اسم المادة والصنف', i.category as 'الفئة الأساسية', i.warehouse as 'المستودع المستضيف', SUM(i.qty) as 'الرصيد الحالي بالمخزن', cat.red_limit, cat.yellow_limit
            FROM inventory i JOIN material_definitions m ON i.item_code = m.item_code JOIN settings_categories cat ON i.category = cat.name
            WHERE i.warehouse != '' GROUP BY i.item_code, i.warehouse
        """, conn)
        
        if not df_alert_data.empty:
            def get_status_label(row):
                qty = row['الرصيد الحالي بالمخزن']
                red = row['red_limit']
                yellow = row['yellow_limit']
                if qty <= red: return "🔴 نقص حاد"
                elif qty <= yellow: return "🟡 تنبيه"
                else: return "🟢 آمن ومستقر"
                
            df_alert_data['وضعية حالة المخزون'] = df_alert_data.apply(get_status_label, axis=1)
            if status_filter == "🔴 نقص حاد وحرج جداً (الأحمر)":
                df_to_export = df_alert_data[df_alert_data['وضعية حالة المخزون'] == "🔴 نقص حاد"]
            elif status_filter == "🟡 تخطي حد التنبيه الآمن (الأصفر)":
                df_to_export = df_alert_data[df_alert_data['وضعية حالة المخزون'] == "🟡 تنبيه"]
            else:
                df_to_export = df_alert_data[df_alert_data['وضعية حالة المخزون'] != "🟢 آمن ومستقر"]
                
            if not df_to_export.empty:
                st.info(f"📋 إجمالي عدد المواد والأصناف التي تتطلب التدخل وإعادة التعبئة حالياً: {len(df_to_export)} صنف.")
                excel_data = to_excel(df_to_export[['كود المادة', 'اسم المادة والصنف', 'الفئة الأساسية', 'المستودع المستضيف', 'الرصيد الحالي بالمخزن', 'وضعية حالة المخزون']])
                st.download_button(label=f"📥 تحميل مسودة مستند طلب المواد المحددة بصيغة Excel ({status_filter})", data=excel_data, file_name=f"مسودة_طلب_مواد_{status_filter}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                st.dataframe(df_to_export[['كود المادة', 'اسم المادة والصنف', 'الفئة الأساسية', 'المستودع المستضيف', 'الرصيد الحالي بالمخزن', 'وضعية حالة المخزون']], use_container_width=True, hide_index=True)
            else:
                st.success("✅ جميع أرصدة مستودعات الطوارئ الميدانية آمنة وضمن المستويات المستقرة المطلوبة.")
        else:
            st.success("✅ المنظومة لا تحتوي على أي نواقص أو حركات مخزنية حرجة حالياً.")

    # ---------------------------------------------------------
    # صفحة: شحن وإدخال المواد للمستودعات
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_in":
        st.markdown("<div class='main-title'>📥 شحن وتغذية مستودعات الطوارئ الميدانية</div>", unsafe_allow_html=True)
        if not list_warehouses:
            st.warning("⚠️ يرجى أولاً الذهاب للوحة التحكم العامة وتعريف مستودع ميداني واحد على الأقل.")
        else:
            with st.form("stock_in_form", clear_on_submit=True):
                st.write("##### 📝 تعبئة نموذج الشحن الوارد:")
                c_in1, c_in2, c_in3 = st.columns([1.5, 3, 1.5])
                in_code = c_in1.text_input("كود المادة المراد شحنها *").strip()
                in_wh = c_in2.selectbox("المستودع الميداني المستهدف بالشحن *", list_warehouses)
                in_qty = c_in3.number_input("الكمية المدخلة الواردة *", min_value=1, value=10, step=1)
                
                if st.form_submit_button("💾 اعتماد وتثبيت الكمية الواردة بالمخزن"):
                    if in_code and in_wh and in_qty > 0:
                        mat_res = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{in_code}'", conn)
                        if mat_res.empty:
                            st.error(f"❌ خطأ: كود المادة ({in_code}) غير معرف مسبقاً بالنظام! يرجى تعريفه أولاً من تبويب [تعريف مواد جديدة].")
                        else:
                            item_name = mat_res.iloc[0]['item_name']
                            item_cat = mat_res.iloc[0]['category']
                            
                            c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                      (in_code, in_qty, in_wh, "", item_cat))
                            save_log("شحن وإدخل مخزني", in_code, in_qty, f"شحن كمية ({in_qty}) من صنف [{item_name}] إلى المستودع [{in_wh}]", u['full_name'])
                            conn.commit()
                            st.success(f"✅ تم بنجاح قيد وشحن المادة [{item_name}] بالكمية (+{in_qty}) في مستودع {in_wh}.")
                    else:
                        st.error("⚠️ يرجى التأكد من كتابة كود المادة وتحديد كافة البيانات بشكل صحيح.")

    # ---------------------------------------------------------
    # صفحة: صرف مواد للمقاول (إصلاح محاذاة سلة الصرف)
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_out":
        st.markdown("<div class='main-title'>🛒 عمليات صرف ومواجهة حالات الطوارئ للمقاولين</div>", unsafe_allow_html=True)
        if not list_warehouses or not list_contractors:
            st.warning("⚠️ يرجى التأكد من تعريف المستودعات والمقاولين المعتمدين في لوحة الإعدادات أولاً.")
        else:
            col_out_h1, col_out_h2 = st.columns([1.5, 2])
            out_wh = col_out_h1.selectbox("📍 الصرف والسحب من مستودع طوارئ:", list_warehouses)
            out_contractor = col_out_h2.selectbox("🏗️ المقاول المعتمد المستلم للمواد:", list_contractors)
            
            st.write("---")
            col_out1, col_out2, col_out3 = st.columns([1.5, 2, 1])
            out_code = col_out1.text_input("كود المادة للصرف *", key=f"out_code_val_{st.session_state.input_out_code}").strip()
            out_qty = col_out2.number_input("الكمية المراد سحبها *", min_value=1, value=1, step=1, key=f"out_qty_val_{st.session_state.input_out_qty}")
            
            if col_out3.button("➕ إضافة الصنف للسلة"):
                if out_code and out_qty > 0:
                    mat_chk = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{out_code}'", conn)
                    if mat_chk.empty:
                        st.error("❌ كود المادة المدخل غير معرّف بالنظام!")
                    else:
                        item_name = mat_chk.iloc[0]['item_name']
                        item_cat = mat_chk.iloc[0]['category']
                        
                        avail_qty_res = pd.read_sql(f"SELECT SUM(qty) as total FROM inventory WHERE item_code='{out_code}' AND warehouse='{out_wh}'", conn)
                        avail_qty = avail_qty_res.iloc[0]['total'] if not avail_qty_res.empty and avail_qty_res.iloc[0]['total'] is not None else 0
                        
                        already_in_cart = sum(item['qty'] for item in st.session_state.cart if item['code'] == out_code)
                        if avail_qty < (out_qty + already_in_cart):
                            st.error(f"❌ رصيد غير كافٍ! المتاح في المستودع حالياً هو ({avail_qty}) فقط.")
                        else:
                            st.session_state.cart.append({'code': out_code, 'name': item_name, 'qty': out_qty, 'cat': item_cat})
                            st.session_state.input_out_code += 1
                            st.session_state.input_out_qty += 1
                            st.rerun()

            if st.session_state.cart:
                st.write("### 🛒 الأصناف الحالية في سلة الصرف المؤقتة:")
                df_cart = pd.DataFrame(st.session_state.cart)
                st.dataframe(df_cart[['code', 'name', 'qty']], use_container_width=True, hide_index=True)
                
                c_btn1, c_btn2 = st.columns([1, 1])
                if c_btn1.button("🗑️ تفريغ وإلغاء السلة بالكامل"):
                    st.session_state.cart = []
                    st.session_state.review_out = False
                    st.rerun()
                    
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                if c_btn2.button("🔍 مراجعة ومعاينة مستند الصرف الرسمي قبل الاعتماد"):
                    st.session_state.review_out = True
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.session_state.review_out:
                    st.write("---")
                    st.write("### 📄 المعاينة الحية المباشرة للفاتورة الصادرة:")
                    inv_no_preview = datetime.now().strftime("%d%H%M")
                    html_invoice = render_invoice_html("مستند صرف مواد طوارئ رسمي للمقاولين", st.session_state.cart, out_wh, out_contractor, u['full_name'], inv_no_preview)
                    components.html(html_invoice, height=480, scrolling=True)
                    
                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                    if st.button("🚀 تأكيد الخصم الفعلي والأرشفة النهائية للفاتورة"):
                        for item in st.session_state.cart:
                            c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                      (item['code'], -item['qty'], out_wh, out_contractor, item['cat']))
                            save_log("صرف مواد لمقاول", item['code'], item['qty'], f"صرف للمقاول [{out_contractor}] من مستودع [{out_wh}] برقم قيد {inv_no_preview}", u['full_name'])
                        
                        archive_invoice("صرف", inv_no_preview, out_wh, "", out_contractor, u['full_name'], json.dumps(st.session_state.cart), html_invoice)
                        conn.commit()
                        st.session_state.last_inv_html = html_invoice
                        st.session_state.cart = []
                        st.session_state.review_out = False
                        st.success(f"🎉 تم بنجاح خصم الرصيد وأرشفة مستند الصرف رقم ({inv_no_preview}) بنجاح كلي!")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
            
            if st.session_state.last_inv_html:
                st.divider()
                st.write("### 🖨️ آخر فاتورة صرف تم إنشاؤها بنجاح (جاهزة للطباعة الفورية):")
                components.html(st.session_state.last_inv_html, height=520, scrolling=True)

    # ---------------------------------------------------------
    # صفحة: ارتجاع فائض المواد من المقاولين
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_return":
        st.markdown("<div class='main-title'>🔄 ارتجاع وإدخال فائض ومسترجعات المواد الميدانية</div>", unsafe_allow_html=True)
        if not list_warehouses or not list_contractors:
            st.warning("⚠️ يرجى التأكد من تعريف المستودعات والمقاولين المعتمدين في لوحة الإعدادات أولاً.")
        else:
            col_ret_h1, col_ret_h2 = st.columns([2, 1.5])
            ret_contractor = col_ret_h1.selectbox("🏗️ المقاول المعتمد المسلّم للمواد:", list_contractors)
            ret_wh = col_ret_h2.selectbox("📍 إيداع وارتجاع إلى مستودع:", list_warehouses)
            
            st.write("---")
            col_ret1, col_ret2, col_ret3 = st.columns([1.5, 2, 1])
            ret_code = col_ret1.text_input("كود المادة للارتجاع *", key=f"ret_code_val_{st.session_state.input_ret_code}").strip()
            ret_qty = col_ret2.number_input("الكمية المرتجعة المودعة *", min_value=1, value=1, step=1, key=f"ret_qty_val_{st.session_state.input_ret_qty}")
            
            if col_ret3.button("➕ إضافة المرتجع للسلة"):
                if ret_code and ret_qty > 0:
                    mat_chk = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{ret_code}'", conn)
                    if mat_chk.empty:
                        st.error("❌ كود المادة المدخل غير معرّف بالنظام!")
                    else:
                        item_name = mat_chk.iloc[0]['item_name']
                        item_cat = mat_chk.iloc[0]['category']
                        st.session_state.return_cart.append({'code': ret_code, 'name': item_name, 'qty': ret_qty, 'cat': item_cat})
                        st.session_state.input_ret_code += 1
                        st.session_state.input_ret_qty += 1
                        st.rerun()
            
            if st.session_state.return_cart:
                st.write("### 🔄 الأصناف الحالية في سلة الارتجاع المؤقتة:")
                df_ret_cart = pd.DataFrame(st.session_state.return_cart)
                st.dataframe(df_ret_cart[['code', 'name', 'qty']], use_container_width=True, hide_index=True)
                
                c_r_btn1, c_r_btn2 = st.columns([1, 1])
                if c_r_btn1.button("🗑️ تفريغ وإلغاء سلة الارتجاع"):
                    st.session_state.return_cart = []
                    st.session_state.review_return = False
                    st.rerun()
                    
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                if c_r_btn2.button("🔍 مراجعة ومعاينة مستند الارتجاع الرسمي قبل الاعتماد"):
                    st.session_state.review_return = True
                st.markdown("</div>", unsafe_allow_html=True)
                
                if st.session_state.review_return:
                    st.write("---")
                    st.write("### 📄 المعاينة الحية المباشرة لفاتورة الارتجاع الإيداعية:")
                    ret_inv_no_preview = datetime.now().strftime("%d%H%M")
                    html_ret_invoice = render_return_invoice_html("مستند إيداع وارتجاع فائض مواد الطوارئ", st.session_state.return_cart, ret_wh, ret_contractor, u['full_name'], ret_inv_no_preview)
                    components.html(html_ret_invoice, height=480, scrolling=True)
                    
                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                    if st.button("🚀 تأكيد قيد الارتجاع وإدخال الكميات للمخزن وأرشفة الفاتورة"):
                        for item in st.session_state.return_cart:
                            c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                      (item['code'], item['qty'], ret_wh, ret_contractor, item['cat']))
                            save_log("ارتجاع فائض مواد", item['code'], item['qty'], f"ارتجاع وإيداع من المقاول [{ret_contractor}] في مستودع [{ret_wh}] برقم قيد {ret_inv_no_preview}", u['full_name'])
                        
                        archive_invoice("ارتجاع", ret_inv_no_preview, ret_wh, "", ret_contractor, u['full_name'], json.dumps(st.session_state.return_cart), html_ret_invoice)
                        conn.commit()
                        st.session_state.last_ret_inv_html = html_ret_invoice
                        st.session_state.return_cart = []
                        st.session_state.review_return = False
                        st.success(f"🎉 تم بنجاح قيد وإضافة الرصيد المرتجع وأرشفة المستند رقم ({ret_inv_no_preview}) بنجاح كلي!")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                    
            if st.session_state.last_ret_inv_html:
                st.divider()
                st.write("### 🖨️ آخر فاتورة ارتجاع تم إنشاؤها بنجاح (جاهزة للطباعة الفورية):")
                components.html(st.session_state.last_ret_inv_html, height=520, scrolling=True)

    # ---------------------------------------------------------
    # صفحة: نقل وتحويل مادة من مستودع لآخر (تحويل لوجستي بيني)
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_transfer":
        st.markdown("<div class='main-title'>🚛 نقل وتحويل المواد لوجستياً بين مستودعات الطوارئ الميدانية</div>", unsafe_allow_html=True)
        if not list_warehouses:
            st.warning("⚠️ يرجى أولاً التأكد من تعريف المستودعات في لوحة الإعدادات أولاً.")
        else:
            col_trans_h1, col_trans_h2 = st.columns([1, 1])
            trans_wh_from = col_trans_h1.selectbox("📍 من المستودع (المصدر المنقول منه):", list_warehouses)
            trans_wh_to = col_trans_h2.selectbox("📍 إلى المستودع (المستهدف بالتحويل والطلب المستلم):", list_warehouses)
            
            if trans_wh_from == trans_wh_to:
                st.error("❌ خطأ: لا يمكن اختيار نفس المستودع كمصدر ومستهدف للنقل اللوجستي البيني!")
            else:
                st.write("---")
                col_trans1, col_trans2, col_trans3 = st.columns([1.5, 2, 1])
                trans_code = col_trans1.text_input("كود المادة المراد نقلها *", key=f"trans_code_val_{st.session_state.input_trans_code}").strip()
                trans_qty = col_trans2.number_input("الكمية المنقولة المحولة *", min_value=1, value=1, step=1, key=f"trans_qty_val_{st.session_state.input_trans_qty}")
                
                if col_trans3.button("➕ إضافة مادة للتحويل"):
                    if trans_code and trans_qty > 0:
                        mat_chk = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{trans_code}'", conn)
                        if mat_chk.empty:
                            st.error("❌ كود المادة المدخل غير معرّف بالنظام!")
                        else:
                            item_name = mat_chk.iloc[0]['item_name']
                            item_cat = mat_chk.iloc[0]['category']
                            
                            avail_qty_res = pd.read_sql(f"SELECT SUM(qty) as total FROM inventory WHERE item_code='{trans_code}' AND warehouse='{trans_wh_from}'", conn)
                            avail_qty = avail_qty_res.iloc[0]['total'] if not avail_qty_res.empty and avail_qty_res.iloc[0]['total'] is not None else 0
                            
                            already_in_cart = sum(item['qty'] for item in st.session_state.transfer_cart if item['code'] == trans_code)
                            if avail_qty < (trans_qty + already_in_cart):
                                st.error(f"❌ رصيد غير كافٍ! المتاح في مستودع المصدر حالياً هو ({avail_qty}) فقط.")
                            else:
                                st.session_state.transfer_cart.append({'code': trans_code, 'name': item_name, 'qty': trans_qty, 'cat': item_cat})
                                st.session_state.input_trans_code += 1
                                st.session_state.input_trans_qty += 1
                                st.rerun()
                
                if st.session_state.transfer_cart:
                    st.write("### 🚛 الأصناف الحالية في سلة النقل والتحويل اللوجستي المؤقتة:")
                    df_trans_cart = pd.DataFrame(st.session_state.transfer_cart)
                    st.dataframe(df_trans_cart[['code', 'name', 'qty']], use_container_width=True, hide_index=True)
                    
                    c_t_btn1, c_t_btn2 = st.columns([1, 1])
                    if c_t_btn1.button("🗑️ تفريغ وإلغاء سلة التحويل"):
                        st.session_state.transfer_cart = []
                        st.session_state.review_transfer = False
                        st.rerun()
                        
                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                    if c_t_btn2.button("🔍 مراجعة ومعاينة مستند النقل البيني الرسمي قبل الاعتماد"):
                        st.session_state.review_transfer = True
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if st.session_state.review_transfer:
                        st.write("---")
                        st.write("### 📄 المعاينة الحية المباشرة لفاتورة النقل اللوجستي البيني:")
                        trans_inv_no_preview = datetime.now().strftime("%d%H%M")
                        html_trans_invoice = render_transfer_invoice_html("مستند نقل وتحويل مواد طوارئ بيني", st.session_state.transfer_cart, trans_wh_from, trans_wh_to, u['full_name'], trans_inv_no_preview)
                        components.html(html_trans_invoice, height=480, scrolling=True)
                        
                        st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                        if st.button("🚀 تأكيد عملية النقل والخصم والإيداع الفوري للمستودعات وأرشفة الفاتورة"):
                            for item in st.session_state.transfer_cart:
                                c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                          (item['code'], -item['qty'], trans_wh_from, "", item['cat']))
                                c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                          (item['code'], item['qty'], trans_wh_to, "", item['cat']))
                                save_log("تحويل ونقل بيني لوجستي", item['code'], item['qty'], f"نقل وتحويل من مستودع [{trans_wh_from}] إلى مستودع [{trans_wh_to}] برقم قيد {trans_inv_no_preview}", u['full_name'])
                            
                            archive_invoice("تحويل", trans_inv_no_preview, trans_wh_from, trans_wh_to, "", u['full_name'], json.dumps(st.session_state.transfer_cart), html_trans_invoice)
                            conn.commit()
                            st.session_state.last_trans_inv_html = html_trans_invoice
                            st.session_state.transfer_cart = []
                            st.session_state.review_transfer = False
                            st.success(f"🎉 تم بنجاح قيد وخصم وإيداع الأرصدة التبادلية وأرشفة المستند رقم ({trans_inv_no_preview}) بنجاح كلي!")
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                        
                if st.session_state.last_trans_inv_html:
                    st.divider()
                    st.write("### 🖨️ آخر فاتورة نقل لوجستي تم إنشاؤها بنجاح (جاهزة للطباعة الفورية):")
                    components.html(st.session_state.last_trans_inv_html, height=520, scrolling=True)

    # ---------------------------------------------------------
    # صفحة: سجل العمليات التفصيلي وأرشيف المستندات الذكي
    # ---------------------------------------------------------
    elif st.session_state.page == "view_logs":
        st.markdown("<div class='main-title'>🛠️ سجل العمليات التفصيلي وأرشيف فواتير النظام الأوتوماتيكي</div>", unsafe_allow_html=True)
        
        tab_logs_actions, tab_invoices_archive = st.tabs(["📋 سجل تتبع حركات الموظفين اليومية", "🗂️ مستودع الفواتير والمستندات المؤرشفة"])
        
        with tab_logs_actions:
            st.write("##### 🔍 البحث والفرز الفوري في سجل تتبع النظام الكلي")
            col_l1, col_l2 = st.columns([2, 1])
            search_log_txt = col_l1.text_input("ابحث بكتابة اسم الموظف، كود المادة، أو نوع العملية:")
            type_log_filter = col_l2.selectbox("تصفية بحسب نوع الحركة:", ["عرض الكل", "شحن وإدخل مخزني", "صرف مواد لمقاول", "ارتجاع فائض مواد", "تحويل ونقل بيني لوجستي", "تعريف صنف جديد"])
            
            log_query = "SELECT log_type as 'نوع العملية', item_code as 'كود المادة', qty as 'الكمية المعنية', details as 'التفاصيل والبيانات الكاملة', user_name as 'الموظف المسؤول', timestamp as 'التاريخ والوقت الفعلي' FROM action_logs WHERE 1=1"
            if type_log_filter != "عرض الكل":
                log_query += f" AND log_type='{type_log_filter}'"
            log_query += " ORDER BY id DESC"
            
            df_logs = pd.read_sql(log_query, conn)
            if search_log_txt:
                df_logs = df_logs[df_logs['التفاصيل والبيانات الكاملة'].str.contains(search_log_txt, na=False) | df_logs['الموظف المسؤول'].str.contains(search_log_txt, na=False) | df_logs['كود المادة'].str.contains(search_log_txt, na=False)]
                
            if not df_logs.empty:
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
                excel_logs = to_excel(df_logs)
                st.download_button("📥 تصدير السجل المعروض حالياً إلى ملف Excel مستقل", excel_logs, "سجل_العمليات_المخزنية.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.info("ℹ️ لا توجد قيوز أو عمليات مسجلة تطابق محددات البحث والفلاتر الحالية.")
                
        with tab_invoices_archive:
            st.write("##### 📄 أرشيف استرجاع وإعادة طباعة المستندات والفواتير الصادرة مسبقاً")
            
            col_arch1, col_arch2, col_arch3, col_arch4 = st.columns([1, 1, 1.2, 1.2])
            filter_arch_type = col_arch1.selectbox("نوع المستند المراد عرضه:", ["الكل", "صرف", "ارتجاع", "تحويل"])
            search_arch_no = col_arch2.text_input("ابحث برقم الفاتورة مباشرة:")
            search_arch_name = col_arch3.text_input("ابحث باسم المقاول أو الموظف منشئ الحركة:")
            search_arch_date = col_arch4.date_input("تصفية بحسب تاريخ إصدار الفاتورة:", value=None)
            
            arch_query = "SELECT id, invoice_type, invoice_no, warehouse_from, warehouse_to, contractor, employee, timestamp, html_content FROM archived_invoices WHERE 1=1"
            if filter_arch_type != "الكل":
                arch_query += f" AND invoice_type='{filter_arch_type}'"
            if search_arch_no:
                arch_query += f" AND invoice_no LIKE '%{search_arch_no.strip()}%'"
            if search_arch_date is not None:
                date_str_filter = search_arch_date.strftime("%Y-%m-%d")
                arch_query += f" AND timestamp LIKE '{date_str_filter}%'"
            arch_query += " ORDER BY id DESC"
            
            df_archived = pd.read_sql(arch_query, conn)
            
            if search_arch_name:
                df_archived = df_archived[df_archived['contractor'].str.contains(search_arch_name, na=False) | df_archived['employee'].str.contains(search_arch_name, na=False)]
                
            if not df_archived.empty:
                len_archived = len(df_archived)
                st.success(f"✅ تم العثور على ({len_archived}) مستند/فاتورة مطابقة لشروط البحث والفرز الزمني.")
                
                for index, row in df_archived.iterrows():
                    with st.container():
                        st.markdown(f"""
                        <div class='report-box'>
                            📄 <b>مستند {row['invoice_type']} رسمي برقم ( <span style='color:red;'>{row['invoice_no']}</span> )</b> | 📝 المسؤول عن الحركة: <b>{row['employee']}</b><br>
                            📅 تاريخ القيد والأرشفة الفعلي: {row['timestamp']} | 📍 المستودع المصدر: {row['warehouse_from'] if row['warehouse_from'] else 'N/A'} {f' ➡️ المستودع المستلم: {row["warehouse_to"]}' if row['warehouse_to'] else ''} {f' | 🏗️ المقاول المستلم: {row["contractor"]}' if row['contractor'] else ''}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        show_inv_btn = st.button(f"👁️ عرض ومعاينة وطباعة الفاتورة رقم {row['invoice_no']}", key=f"btn_arch_{row['id']}")
                        if show_inv_btn:
                            st.session_state.view_archived_html[row['invoice_no']] = not st.session_state.view_archived_html.get(row['invoice_no'], False)
                            
                        if st.session_state.view_archived_html.get(row['invoice_no'], False):
                            st.write("<p style='margin-top:10px;'></p>", unsafe_allow_html=True)
                            components.html(row['html_content'], height=520, scrolling=True)
                            st.write("---")
            else:
                st.info("ℹ️ لم يتم العثور على أي مستندات مؤرشفة تطابق الكلمات المفتاحية أو التاريخ المحدد حالياً.")

    # ---------------------------------------------------------
    # صفحة: لوحة إدارة حسابات الموظفين والتحكم بالصلاحيات العليا
    # ---------------------------------------------------------
    elif st.session_state.page == "manage_staff":
        st.markdown("<div class='main-title'>👥 إدارة حسابات الموظفين والتحكم بالصلاحيات العليا</div>", unsafe_allow_html=True)
        
        tab_requests_view, tab_add_new_emp = st.tabs(["📥 طلبات تصفير وتعديل كلمات المرور الواردة", "➕ إضافة وتعيين حساب موظف ميداني جديد"])
        
        with tab_requests_view:
            st.write("##### 📋 طلبات إعادة تعيين كلمات السر المعلقة والمرفوعة")
            df_reqs = pd.read_sql("SELECT id as 'رقم الطلب', phone as 'رقم جوال الموظف الطالب', status as 'حالة الطلب الحالي', request_time as 'توقيت رفع الطلب' FROM access_requests ORDER BY id DESC", conn)
            if not df_reqs.empty:
                st.dataframe(df_reqs, use_container_width=True, hide_index=True)
                
                st.write("---")
                st.write("🔑 **تحديث فوري وسريع لكلمة مرور الحسابات المعلقة:**")
                with st.form("reset_pwd_form", clear_on_submit=True):
                    col_p1, col_p2 = st.columns([1, 1])
                    phone_to_reset = col_p1.text_input("رقم جوال الموظف المراد تصفيره *").strip()
                    new_password_val = col_p2.text_input("كلمة السر الجديدة المقترحة *", type="password")
                    
                    if st.form_submit_button("💾 تحديث واعتماد كلمة المرور الجديدة الآن"):
                        if phone_to_reset and new_password_val:
                            check_usr = pd.read_sql(f"SELECT username FROM users WHERE username='{phone_to_reset}'", conn)
                            if check_usr.empty:
                                st.error("❌ عذراً رقم الجوال غير مسجل نهائياً كموظف في النظام لإجراء التصفير له.")
                            else:
                                c.execute("UPDATE users SET password=? WHERE username=?", (new_password_val, phone_to_reset))
                                c.execute("UPDATE access_requests SET status='تمت المعالجة والحل' WHERE phone=?", (phone_to_reset,))
                                save_log("تصفير كلمة سر حساب", phone_to_reset, 0, f"تعديل وتصفير الباسورد من قبل المدير العام", u['full_name'])
                                conn.commit()
                                st.success(f"✅ تم تحديث كلمة المرور للحساب رقم ({phone_to_reset}) بنجاح وإغلاق الطلبات المفتوحة.")
                                st.rerun()
                        else:
                            st.error("⚠️ يرجى تعبئة كافة الحقول المطلوبة.")
            else:
                st.success("✅ لا توجد أي طلبات إعادة تعيين معلقة أو واردة من الموظفين حالياً.")
                
        with tab_add_new_emp:
            st.write("##### ➕ تعيين حساب موظف تشغيلي جديد بنظام الطوارئ")
            with st.form("add_user_form", clear_on_submit=True):
                c_u1, c_u2, c_u3, c_u4 = st.columns([1.5, 2, 1.5, 1.5])
                new_username = c_u1.text_input("رقم الجوال (اسم المستخدم) *").strip()
                new_fullname = c_u2.text_input("الاسم الثلاثي الكامل للموظف *").strip()
                new_password = c_u3.text_input("كلمة المرور الافتراضية *", type="password")
                new_role = c_u4.selectbox("مستوى الصلاحية الممنوحة *", ["موظف مستودع", "مدير نظام"])
                
                if st.form_submit_button("👥 إنشاء وتفعيل حساب الموظف فوراً"):
                    if new_username and new_fullname and new_password:
                        check_exist_user = pd.read_sql(f"SELECT username FROM users WHERE username='{new_username}'", conn)
                        if not check_exist_user.empty:
                            st.error(f"❌ خطأ: رقم الجوال ({new_username}) مسجل ومستخدم مسبقاً لموظف آخر بالمنظومة.")
                        else:
                            c.execute("INSERT INTO users (username, password, full_name, role) VALUES (?,?,?,?)",
                                      (new_username, new_password, new_fullname, new_role))
                            save_log("إنشاء حساب موظف", new_username, 0, f"تفعيل حساب موظف جديد باسم: {new_fullname} وبصلاحية: {new_role}", u['full_name'])
                            conn.commit()
                            st.success(f"✅ تم تعيين وتفعيل صلاحيات الموظف الجديد [{new_fullname}] بنجاح بالنظام.")
                            st.rerun()
                    else:
                        st.error("⚠️ جميع الحقول التي تحمل علامة (*) إلزامية لإنشاء الحساب البرمجي بنجاح.")
                        
            st.divider()
            st.write("##### 👥 إدارة وتعديل الموظفين المقيدين حالياً بالنظام:")
            
            df_all_users = pd.read_sql("SELECT username, full_name, password, role FROM users", conn)
            
            if not df_all_users.empty:
                for idx, r_usr in df_all_users.iterrows():
                    usr_key = r_usr['username']
                    with st.expander(f"👤 {r_usr['full_name']} (حساب: {usr_key})"):
                        with st.form(f"edit_user_form_{usr_key}"):
                            col_e1, col_e2, col_e3, col_e4 = st.columns([1.5, 2, 1.5, 1.5])
                            
                            updated_username = col_e1.text_input("رقم الجوال (اسم المستخدم)", value=r_usr['username'])
                            updated_name = col_e2.text_input("الاسم التفصيلي الكامل", value=r_usr['full_name'])
                            updated_pass = col_e3.text_input("كلمة السر", value=r_usr['password'])
                            updated_role = col_e4.selectbox("الصلاحية الممنوحة", ["موظف مستودع", "مدير نظام"], index=0 if r_usr['role'] == "موظف مستودع" else 1)
                            
                            c_user_act1, c_user_act2 = st.columns([1, 1])
                            
                            st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                            if c_user_act1.form_submit_button("🗑️ حذف الحساب نهائياً"):
                                if usr_key == u['username']:
                                    st.error("❌ لا يمكنك حذف حسابك الحالي الذي تسجل الدخول به!")
                                else:
                                    c.execute("DELETE FROM users WHERE username=?", (usr_key,))
                                    save_log("حذف حساب موظف", usr_key, 0, f"تم حذف حساب الموظف [{r_usr['full_name']}] كلياً من قبل الإدارة", u['full_name'])
                                    conn.commit()
                                    st.success("✅ تم حذف حساب الموظف بنجاح.")
                                    st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                            
                            if c_user_act2.form_submit_button("💾 حفظ وتحديث البيانات"):
                                if not updated_username or not updated_name or not updated_pass:
                                    st.error("⚠️ يرجى عدم ترك الحقول فارغة أثناء التعديل.")
                                else:
                                    if updated_username != usr_key:
                                        check_dup = pd.read_sql(f"SELECT username FROM users WHERE username='{updated_username}'", conn)
                                        if not check_dup.empty:
                                            st.error("❌ رقم الجوال الجديد مكتوب ومستخدم لحساب موظف آخر بالفعل.")
                                            st.stop()
                                            
                                    c.execute("UPDATE users SET username=?, full_name=?, password=?, role=? WHERE username=?",
                                              (updated_username.strip(), updated_name.strip(), updated_pass.strip(), updated_role, usr_key))
                                    save_log("تعديل بيانات حساب", updated_username, 0, f"تعديل بيانات الموظف القديمة إلى الاسم: {updated_name} والصلاحية: {updated_role}", u['full_name'])
                                    conn.commit()
                                    
                                    if usr_key == u['username']:
                                        res_self = pd.read_sql(f"SELECT * FROM users WHERE username='{updated_username.strip()}'", conn)
                                        if not res_self.empty:
                                            st.session_state.user_info = res_self.iloc[0]
                                            
                                    st.success("✅ تم تحديث بيانات الموظف بنجاح كلي.")
                                    st.rerun()

    # ---------------------------------------------------------
    # صفحة: الثوابت العامة والإعدادات التشغيلية
    # ---------------------------------------------------------
    elif st.session_state.page == "global_settings":
        st.markdown("<div class='main-title'>🛠️ الثوابت والإعدادات التشغيلية العامة للمنظومة</div>", unsafe_allow_html=True)
        
        set_col1, set_col2, set_col3 = st.columns([1, 1, 1.2])
        
        with set_col1:
            st.markdown("### 🏢 إدارة مستودعات الطوارئ")
            df_wh = pd.read_sql("SELECT * FROM settings_warehouses", conn)
            if not df_wh.empty:
                for idx, r_wh in df_wh.iterrows():
                    c_w_1, c_w_2 = st.columns([3, 1])
                    c_w_1.write(f"📍 {r_wh['name']}")
                    if c_w_2.button("🗑️", key=f"del_wh_{r_wh['id']}"):
                        c.execute("DELETE FROM settings_warehouses WHERE id=?", (r_wh['id'],))
                        conn.commit()
                        st.rerun()
            else:
                st.info("ℹ️ لا توجد مستودعات طوارئ معرّفة.")
                
            with st.form("add_wh_form", clear_on_submit=True):
                new_wh = st.text_input("اسم المستودع الميداني الجديد")
                if st.form_submit_button("حفظ المستودع"):
                    if new_wh:
                        c.execute("INSERT INTO settings_warehouses (name) VALUES (?)", (new_wh.strip(),))
                        conn.commit()
                        st.rerun()
                        
        with set_col2:
            st.markdown("### 🏗️ المقاولين المعتمدين")
            df_con = pd.read_sql("SELECT * FROM settings_contractors", conn)
            if not df_con.empty:
                for idx, r_con in df_con.iterrows():
                    c_c_1, c_c_2 = st.columns([3, 1])
                    c_c_1.write(f"👷 {r_con['name']}")
                    if c_c_2.button("🗑️", key=f"del_con_{r_con['id']}"):
                        c.execute("DELETE FROM settings_contractors WHERE id=?", (r_con['id'],))
                        conn.commit()
                        st.rerun()
            else:
                st.info("ℹ️ لا يوجد مقاولين معتمدين حالياً.")
                
            with st.form("add_con_form", clear_on_submit=True):
                new_con = st.text_input("اسم المقاول / الشركة الجديد")
                if st.form_submit_button("حفظ المقاول"):
                    if new_con:
                        c.execute("INSERT INTO settings_contractors (name) VALUES (?)", (new_con.strip(),))
                        conn.commit()
                        st.rerun()
                        
        with set_col3:
            st.markdown("### 🏷️ فئات أصناف المواد وحدود الأمان")
            df_cat = pd.read_sql("SELECT * FROM settings_categories", conn)
            if not df_cat.empty:
                for idx, r_cat in df_cat.iterrows():
                    with st.expander(f"📦 {r_cat['name']}"):
                        cat_id = r_cat['id']
                        cat_old_name = r_cat['name']
                        
                        new_cat_name = st.text_input("تعديل الاسم", value=r_cat['name'], key=f"edit_name_cat_{cat_id}")
                        new_red = st.number_input("🔴 الحد الحرج", value=float(r_cat['red_limit']), key=f"edit_red_cat_{cat_id}")
                        new_yellow = st.number_input("🟡 حد التنبيه", value=float(r_cat['yellow_limit']), key=f"edit_yel_cat_{cat_id}")
                        
                        c_actions_cat1, c_actions_cat2 = st.columns([1, 1])
                        if c_actions_cat1.button("🗑️ حذف الفئة", key=f"del_cat_btn_{cat_id}"):
                            c.execute("DELETE FROM settings_categories WHERE id=?", (cat_id,))
                            conn.commit()
                            st.rerun()
                        if c_actions_cat2.button("💾 حفظ", key=f"save_cat_btn_{cat_id}"):
                            if new_cat_name:
                                c.execute("UPDATE settings_categories SET name=?, red_limit=?, yellow_limit=? WHERE id=?", 
                                          (new_cat_name.strip(), new_red, new_yellow, cat_id))
                                c.execute("UPDATE material_definitions SET category=? WHERE category=?", (new_cat_name.strip(), cat_old_name))
                                c.execute("UPDATE inventory SET category=? WHERE category=?", (new_cat_name.strip(), cat_old_name))
                                conn.commit()
                                st.success("✅ تم تحديث اسم الفئة ومستويات الخطر بنجاح.")
                                st.rerun()
            else:
                st.info("ℹ️ لا توجد فئات أصناف معرّفة.")
                
            st.divider()
            with st.form("add_cat_form", clear_on_submit=True):
                st.write("**➕ إضافة وتثبيت فئة أصناف رئيسية بالنظام**")
                new_cat = st.text_input("اسم تصنيف الفئة الجديد")
                c_red = st.number_input("حد الأمان الأدنى الحرج المقترح (🔴 الأحمر)", min_value=0.0, value=5.0, step=1.0)
                c_yellow = st.number_input("حد التنبيه والاقتراب المقترح (🟡 الأصفر)", min_value=0.0, value=10.0, step=1.0)
                
                if st.form_submit_button("تأكيد وحفظ الفئة الجديدة"):
                    if new_cat:
                        c.execute("INSERT INTO settings_categories (name, red_limit, yellow_limit) VALUES (?,?,?)", (new_cat.strip(), c_red, c_yellow))
                        conn.commit()
                        st.success(f"✅ تم إضافة الفئة الجديدة [{new_cat}] وتحديد حدود الأمان بنجاح.")
                        st.rerun()

# =========================================================
# 8. إغلاق اتصال قاعدة البيانات عند نهاية التنفيذ لضمان سلامة البيانات
# =========================================================
if 'conn' in locals() or 'conn' in globals():
    try:
        pass
    except NameError:
        pass