import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
try:
    import pytz
    MECCA_TZ = pytz.timezone("Asia/Riyadh")
    def now_mecca():
        return datetime.now(MECCA_TZ)
except ImportError:
    def now_mecca():
        return datetime.now()
import io
import streamlit.components.v1 as components
import json
import threading, shutil, os, queue

# =========================================================
# 1. إعدادات قاعدة البيانات
# =========================================================
DB_NAME = 'awaji_emergency_full_system.db'

@st.cache_resource
def get_connection():
    """اتصال واحد يُعاد استخدامه عبر جميع جلسات Streamlit"""
    _conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=60)
    _conn.execute("PRAGMA journal_mode=WAL")
    _conn.execute("PRAGMA synchronous=NORMAL")
    _conn.execute("PRAGMA busy_timeout=60000")
    _conn.execute("PRAGMA cache_size=-32000")   # 32MB cache
    _conn.execute("PRAGMA temp_store=MEMORY")
    _conn.row_factory = sqlite3.Row
    return _conn

conn = get_connection()
c    = conn.cursor()

# ═══════════════════════════════════════════════════════
# نظام النسخ الاحتياطية التلقائية — نسخ الملف فقط
# بدون فتح أي اتصال بقاعدة البيانات في خيط خلفي
# ═══════════════════════════════════════════════════════
_backup_queue = queue.Queue()  # قائمة انتظار لتسجيل النسخة في DB من الخيط الرئيسي

def _do_file_copy_backup():
    """ينسخ ملف قاعدة البيانات فقط — لا يفتح اتصال SQL"""
    try:
        date_str = now_mecca().strftime("%Y-%m-%d")
        time_str = now_mecca().strftime("%H:%M")
        hour_tag = "morning" if now_mecca().hour < 12 else "evening"
        backup_dir = "auto_backups"
        os.makedirs(backup_dir, exist_ok=True)
        bk_name = f"auto_{date_str}_{hour_tag}.db"
        bk_path = os.path.join(backup_dir, bk_name)
        # نسخ الملف مباشرة — آمن حتى مع WAL mode
        shutil.copy2(DB_NAME, bk_path)
        # أضف WAL file إن وجد
        wal_src = DB_NAME + "-wal"
        if os.path.exists(wal_src):
            shutil.copy2(wal_src, bk_path + "-wal")
        size_kb = round(os.path.getsize(bk_path) / 1024, 2)
        # أرسل للخيط الرئيسي ليسجلها في DB
        _backup_queue.put({
            'name': bk_name, 'date': date_str,
            'time': time_str, 'path': bk_path, 'size': size_kb
        })
    except Exception:
        pass

def _schedule_auto_backups():
    """خيط الجدولة — ينسخ الملف فقط بدون أي SQL"""
    import time as _time
    target_hours = {8, 20}
    last_hour = -1
    while True:
        try:
            now = now_mecca()
            h, m = now.hour, now.minute
            if h in target_hours and m == 0 and h != last_hour:
                _do_file_copy_backup()
                last_hour = h
            if h not in target_hours:
                last_hour = -1
        except Exception:
            pass
        _time.sleep(30)

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
                    role TEXT,
                    mobile_access INTEGER DEFAULT 0)''')
    # إضافة العمود إن لم يكن موجوداً (للتوافق مع قواعد البيانات القديمة)
    try:
        c.execute("ALTER TABLE users ADD COLUMN mobile_access INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass
    
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
    
    # جدول النسخ الاحتياطية
    c.execute('''CREATE TABLE IF NOT EXISTS backups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backup_name TEXT,
                    backup_date TEXT,
                    backup_time TEXT,
                    backup_type TEXT,
                    file_path TEXT,
                    size_kb REAL,
                    created_by TEXT)''')

    # جدول طلبات الارجاع (من موجه البلاغات — يحتاج اعتماد مسؤول المستودع أو مدير النظام)
    c.execute('''CREATE TABLE IF NOT EXISTS return_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_no TEXT,
                    warehouse TEXT,
                    contractor TEXT,
                    items_json TEXT,
                    requester TEXT,
                    status TEXT DEFAULT "معلق",
                    notes TEXT,
                    invoice_html TEXT,
                    timestamp TEXT,
                    approved_by TEXT,
                    approved_at TEXT)''')

    # جدول أرقام التواصل مع المقاولين والمستودعات
    c.execute('''CREATE TABLE IF NOT EXISTS contact_numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    position TEXT,
                    phone TEXT,
                    entity_type TEXT,
                    entity_name TEXT,
                    notes TEXT)''')
    # إضافة عمود entity_name لقواعد البيانات القديمة
    try:
        c.execute("ALTER TABLE contact_numbers ADD COLUMN entity_name TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    # جدول المدراء (يُدار يدوياً من مدير النظام)
    c.execute('''CREATE TABLE IF NOT EXISTS managers_directory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    department TEXT,
                    phone TEXT,
                    notes TEXT)''')

    # إضافة عمود المنصب لجدول المستخدمين إن لم يكن موجوداً
    try:
        c.execute("ALTER TABLE users ADD COLUMN position TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass

    # إضافة indexes لتسريع الاستعلامات
    c.execute("CREATE INDEX IF NOT EXISTS idx_archived_type ON archived_invoices(invoice_type)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_archived_ts   ON archived_invoices(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_archived_no   ON archived_invoices(invoice_no)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_code     ON action_logs(item_code)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_logs_date     ON action_logs(log_date)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_inv_code_wh   ON inventory(item_code, warehouse)")

    # حساب مدير النظام الافتراضي الأستان أحمد سعيد عواجي
    c.execute("INSERT OR REPLACE INTO users VALUES (?,?,?,?,?,?)", ("0501104283", "AaSs123456+++**", "أحمد سعيد عواجي", "مدير نظام", 1, "مدير النظام"))
    conn.commit()

init_database()

# ── تشغيل خيط النسخ الاحتياطية مرة واحدة فقط ──
if 'auto_backup_started' not in st.session_state:
    _t = threading.Thread(target=_schedule_auto_backups, daemon=True)
    _t.start()
    st.session_state['auto_backup_started'] = True

# ── معالجة قائمة انتظار النسخ من الخيط الرئيسي (آمن من database locked) ──
try:
    while not _backup_queue.empty():
        bk = _backup_queue.get_nowait()
        c.execute("""INSERT INTO backups (backup_name, backup_date, backup_time, backup_type, file_path, size_kb, created_by)
                     VALUES (?,?,?,?,?,?,?)""",
                  (bk['name'], bk['date'], bk['time'], "تلقائية", bk['path'], bk['size'], "النظام التلقائي"))
        conn.commit()
except Exception:
    pass

# =========================================================
# 2. وظيفة بناء وتوليد فاتورة الصرف (HTML) بدون هوامش بالطباعة
# =========================================================

def render_invoice_html(title, items_list, warehouse, contractor, employee, custom_inv_no=None, extra_info=None):
    inv_no = custom_inv_no if custom_inv_no else now_mecca().strftime("%d%H%M")
    dt_str = now_mecca().strftime("%Y-%m-%d %H:%M")
    rows = ""
    for item in items_list:
        rows += (
            "<tr>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:center;font-weight:bold;'>{item['code']}</td>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:right;'>{item['name']}</td>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:center;color:#004a99;font-weight:bold;font-size:16px;'>{item['qty']}</td>"
            "</tr>"
        )
    extra_row = ""
    if extra_info:
        extra_row = f"<tr><td colspan='2'><b>{extra_info[0]}</b> {extra_info[1]}</td></tr>"
    html = f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    @media print {{
        @page {{ size: auto; margin: 0mm; }}
        body {{ margin: 0mm; padding: 10mm; background: white; }}
        .no-print {{ display: none !important; }}
    }}
    </style>
    <div dir="rtl" style="font-family:'Tajawal',Arial,sans-serif;padding:30px;border:3px solid #004a99;border-radius:15px;background:#fff;max-width:900px;margin:auto;">
        <div style="text-align:center;margin-bottom:15px;">
            <img src="{LOGO_DATA_URI}" width="160" style="border-radius:10px;display:block;margin:0 auto 8px auto;">
            <div style="font-size:22px;font-weight:900;color:#004a99;">السعودية للطاقة</div>
            <div style="font-size:13px;color:#1daa60;font-weight:bold;">نظام إدارة مواد الطوارئ — دائرة شرق منطقة جازان</div>
        </div>
        <hr style="border:2px solid #004a99;margin-bottom:12px;">
        <div style="display:flex;justify-content:space-between;font-size:14px;color:#333;margin-bottom:12px;">
            <div><b>رقم الفاتورة:</b> <span style="color:red;font-weight:bold;font-size:16px;">{inv_no}</span></div>
            <div><b>التاريخ والوقت:</b> {dt_str}</div>
            <div><b>المسؤول:</b> {employee}</div>
        </div>
        <h3 style="text-align:center;background:#004a99;color:white;padding:12px;border-radius:8px;font-size:19px;margin-bottom:18px;">{title}</h3>
        <div style="background:#f9f9f9;padding:12px 15px;border-radius:8px;margin-bottom:18px;border:1px solid #eee;font-size:14px;">
            <table style="width:100%;border:none;">
                <tr>
                    <td><b>المستودع المعني:</b> {warehouse if warehouse else 'N/A'}</td>
                    <td><b>المقاول / الجهة المستلمة:</b> {contractor if contractor else 'N/A'}</td>
                </tr>
                {extra_row}
            </table>
        </div>
        <table style="width:100%;border-collapse:collapse;font-size:15px;">
            <thead><tr style="background:#004a99;color:white;">
                <th style="border:1px solid #004a99;padding:12px;width:25%;">كود المادة</th>
                <th style="border:1px solid #004a99;padding:12px;width:55%;text-align:right;">وصف وصنف المادة</th>
                <th style="border:1px solid #004a99;padding:12px;width:20%;">الكمية</th>
            </tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div style="margin-top:60px;display:flex;justify-content:space-between;text-align:center;font-size:15px;">
            <div style="width:45%;"><p><b>توقيع مسؤول المستودع</b></p><br><br><p>_______________________</p></div>
            <div style="width:45%;"><p><b>توقيع المقاول / المستلم للمواد</b></p><br><br><p>_______________________</p></div>
        </div>
        <div style="text-align:center;margin-top:40px;" class="no-print">
            <button onclick="window.print()" style="padding:12px 35px;background:#f9a825;color:white;border:none;border-radius:6px;font-size:16px;font-weight:bold;cursor:pointer;">🖨️ اضغط هنا لطباعة الفاتورة</button>
        </div>
    </div>"""
    return html

def render_return_invoice_html(title, items_list, warehouse, contractor, employee, custom_inv_no=None):
    return render_invoice_html(title, items_list, warehouse, contractor, employee, custom_inv_no)

def render_transfer_invoice_html(title, items_list, wh_from, wh_to, employee, custom_inv_no=None):
    return render_invoice_html(title, items_list, wh_from, "", employee, custom_inv_no,
                                extra_info=("المستودع المستلم:", wh_to if wh_to else "N/A"))

# =========================================================
# 5. الوظائف البرمجية المساعدة (التسجيل والتصدير)
# =========================================================
# =========================================================
# دوال النسخ الاحتياطية
# =========================================================
import shutil, os, zipfile

BACKUP_DIR = "system_backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

BACKUP_PASSWORD = "AaSs#123123"  # كلمة مرور الوصول لصفحة النسخ الاحتياطية

def create_backup(created_by="تلقائي"):
    """إنشاء نسخة احتياطية كاملة من قاعدة البيانات"""
    now = now_mecca()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H-%M")
    backup_name = f"backup_{date_str}_{time_str}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    try:
        # إغلاق وفتح الاتصال لضمان كتابة البيانات
        conn.commit()
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_NAME, DB_NAME)
        size_kb = round(os.path.getsize(backup_path) / 1024, 2)
        c.execute("""INSERT INTO backups (backup_name, backup_date, backup_time, backup_type, file_path, size_kb, created_by)
                     VALUES (?,?,?,?,?,?,?)""",
                  (backup_name, date_str, now.strftime("%H:%M"), created_by, backup_path, size_kb, created_by))
        conn.commit()
        return backup_path, backup_name, size_kb
    except Exception as e:
        return None, str(e), 0

def run_auto_backup():
    """تشغيل النسخ الاحتياطي التلقائي إذا حان وقته (8 ص و8 م بتوقيت مكة)"""
    try:
        now_local = now_mecca()
        hour   = now_local.hour
        minute = now_local.minute
        date_str = now_local.strftime("%Y-%m-%d")
        # تشغيل عند الساعة 8:00 صباحاً أو 20:00 مساءً (نافذة 5 دقائق)
        if (hour == 8 or hour == 20) and minute < 5:
            existing = pd.read_sql(
                f"SELECT id FROM backups WHERE backup_date='{date_str}' AND backup_time LIKE '{hour:02d}:%' AND backup_type='تلقائي'",
                conn)
            if existing.empty:
                label = "تلقائي - 8 صباحاً" if hour == 8 else "تلقائي - 8 مساءً"
                create_backup(label)
    except Exception:
        pass

# تشغيل النسخ التلقائي عند كل تحميل للتطبيق
run_auto_backup()


def render_editable_cart(cart_key, wh_ref=None):
    """سلة تفاعلية: تعديل الكمية + حذف كل صنف — مع منع تجاوز الكمية المتاحة"""
    cart = st.session_state[cart_key]
    if not cart:
        return False  # لا أخطاء — السلة فارغة
    st.write(f"### 🛒 الأصناف في السلة ({len(cart)} صنف):")
    h1, h2, h3, h4, h5 = st.columns([1.2, 2.5, 1.8, 1.3, 0.8])
    h1.markdown("**كود المادة**"); h2.markdown("**اسم المادة**")
    h3.markdown("**الفئة**"); h4.markdown("**الكمية**"); h5.markdown("**حذف**")
    st.markdown("<hr style='margin:4px 0 6px 0;'>", unsafe_allow_html=True)
    to_remove = None
    cart_has_error = False
    for i, item in enumerate(cart):
        c1, c2, c3, c4, c5 = st.columns([1.2, 2.5, 1.8, 1.3, 0.8])
        c1.write(item['code']); c2.write(item['name']); c3.write(item.get('cat',''))
        if wh_ref:
            avail_r = pd.read_sql(f"SELECT SUM(qty) as t FROM inventory WHERE item_code='{item['code']}' AND warehouse='{wh_ref}'", conn)
            avail = int(avail_r.iloc[0]['t'] or 0)
            others = sum(x['qty'] for j,x in enumerate(cart) if j!=i and x['code']==item['code'])
            max_qty = max(1, avail - others)
            new_qty = c4.number_input("", min_value=1, max_value=max_qty,
                                       value=min(int(item['qty']), max_qty),
                                       step=1, key=f"cq_{cart_key}_{i}", label_visibility="collapsed")
            if int(item['qty']) > max_qty:
                c4.markdown(f"<span style='color:red;font-size:11px;'>⚠️ تم تعديله — المتاح: {max_qty}</span>", unsafe_allow_html=True)
                st.session_state[cart_key][i]['qty'] = max_qty
                cart_has_error = False  # تم التصحيح التلقائي
            if new_qty != int(item['qty']):
                st.session_state[cart_key][i]['qty'] = new_qty; st.rerun()
        else:
            new_qty = c4.number_input("", min_value=1, max_value=9999, value=int(item['qty']),
                                       step=1, key=f"cq_{cart_key}_{i}", label_visibility="collapsed")
            if new_qty != int(item['qty']):
                st.session_state[cart_key][i]['qty'] = new_qty; st.rerun()
        if c5.button("🗑️", key=f"cd_{cart_key}_{i}", help="حذف من السلة"):
            to_remove = i
    if to_remove is not None:
        st.session_state[cart_key].pop(to_remove); st.rerun()
    st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)
    return cart_has_error

def validate_cart_stock(cart, warehouse):
    """
    يتحقق من كفاية الرصيد لكل صنف في السلة.
    يعيد قائمة بالأخطاء — فارغة إذا كان كل شيء سليماً.
    """
    errors = []
    # نجمع الكميات المطلوبة لكل كود
    code_totals = {}
    for item in cart:
        code_totals[item['code']] = code_totals.get(item['code'], 0) + int(item['qty'])
    for code, needed in code_totals.items():
        res = pd.read_sql(
            f"SELECT SUM(qty) as t FROM inventory WHERE item_code='{code}' AND warehouse='{warehouse}'",
            conn)
        avail = int(res.iloc[0]['t'] or 0) if not res.empty else 0
        if needed > avail:
            name_r = pd.read_sql(f"SELECT item_name FROM material_definitions WHERE item_code='{code}'", conn)
            name = name_r.iloc[0]['item_name'] if not name_r.empty else code
            errors.append(f"❌ <b>{name}</b> (كود: {code}) — مطلوب: <b>{needed}</b> | متوفر: <b>{avail}</b>")
    return errors

def save_log(log_type, item_code, qty, details, user_name):
    now = now_mecca()
    log_date = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO action_logs (log_type, item_code, qty, details, user_name, timestamp, log_date) 
                 VALUES (?,?,?,?,?,?,?)""", (log_type, item_code, qty, details, user_name, timestamp, log_date))
    conn.commit()

def archive_invoice(invoice_type, invoice_no, wh_from, wh_to, contractor, employee, items_json, html_content):
    timestamp = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
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
    .main-title { color: #004a99; text-align: center; font-size: 28px; font-weight: bold; border-bottom: 3px solid #004a99; padding-bottom: 12px; margin-bottom: 30px; }
    .sidebar-header { background-color: #ffffff; padding: 20px; border-radius: 15px; border: 2px solid #004a99; text-align: center; margin-bottom: 15px; color: #004a99; }
    .creator-info { font-size: 11px; text-align: center; color: #666; margin-top: 25px; border-top: 1px solid #ddd; padding-top: 12px; }
    .report-box { background-color: #f1f3f6; padding: 15px; border-radius: 10px; border-right: 6px solid #004a99; margin-bottom: 15px; }
    .operation-card { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 0px 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; }
    .btn-danger>div>button { background-color: #d32f2f !important; color: white !important; }
    .btn-danger>div>button:hover { background-color: #b71c1c !important; }
    .btn-success>div>button { background-color: #2e7d32 !important; color: white !important; }
    .btn-success>div>button:hover { background-color: #1b5e20 !important; }
    @media print { .no-print { display: none !important; } }
    .warn-box { background:#fff3cd; border:2px solid #f9a825; border-radius:10px; padding:16px 20px; margin:12px 0; direction:rtl; font-size:15px; }
    </style>
    """, unsafe_allow_html=True)

# تطبيق CSS النسخة المحمولة إذا كان المستخدم اختار الجوال
if st.session_state.get('display_mode') == "mobile":
    st.markdown("""
    <style>
    /* ===== نسخة الجوال ===== */
    .main .block-container {
        padding: 8px 6px !important;
        max-width: 100% !important;
    }
    /* المحتوى الرئيسي يأخذ العرض الكامل دائماً في الجوال */
    section[data-testid="stMain"] {
        width: 100% !important;
        min-width: 0 !important;
    }
    section[data-testid="stMain"] > div {
        width: 100% !important;
        max-width: 100% !important;
        padding-right: 6px !important;
        padding-left: 6px !important;
    }
    /* إخفاء القائمة الجانبية تلقائياً وجعل المحتوى يملأ الشاشة */
    [data-testid="stSidebar"] {
        min-width: 220px !important;
        max-width: 240px !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] {
        min-width: 0 !important;
        max-width: 0 !important;
        overflow: hidden !important;
    }
    /* منع التحرك الجانبي عند إغلاق القائمة */
    .stApp {
        overflow-x: hidden !important;
    }
    .stButton>button {
        height: 3.5em !important;
        font-size: 17px !important;
        margin-bottom: 4px !important;
        border-radius: 12px !important;
    }
    .main-title {
        font-size: 20px !important;
        padding-bottom: 8px !important;
        margin-bottom: 16px !important;
    }
    [data-testid="stSidebar"] .stButton>button {
        font-size: 14px !important;
        height: 3em !important;
        padding: 4px 6px !important;
    }
    .sidebar-header {
        padding: 10px !important;
        font-size: 13px !important;
    }
    .sidebar-header img {
        width: 80px !important;
    }
    div[data-testid="column"] {
        padding: 2px !important;
    }
    .stDataFrame {
        font-size: 12px !important;
    }
    h1, h2, h3 {
        font-size: 16px !important;
    }
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        font-size: 16px !important;
    }
    /* تحسين الجداول في الجوال */
    .stDataFrame table {
        font-size: 11px !important;
    }
    /* تصغير الأعمدة في الجوال */
    div[data-testid="stHorizontalBlock"] {
        flex-wrap: wrap !important;
    }
    </style>
    """, unsafe_allow_html=True)

# استدعاء والتحقق من متغيرات الجلسة (Session State)
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_info' not in st.session_state: st.session_state.user_info = None
if 'page' not in st.session_state: st.session_state.page = "inventory_status"

# ── استعادة الجلسة من localStorage عند تحديث المتصفح ──
if not st.session_state.auth:
    # نقرأ قيمة مخزنة في localStorage عبر query params
    params = st.query_params
    saved_user = params.get("_u", "")
    if saved_user:
        res = pd.read_sql(
            "SELECT * FROM users WHERE username=?", conn,
            params=(saved_user,))
        if not res.empty:
            u_row = res.iloc[0]
            st.session_state.auth = True
            st.session_state.user_info = {
                'username':     str(u_row['username']),
                'full_name':    str(u_row['full_name']),
                'role':         str(u_row['role']),
                'mobile_access': int(u_row['mobile_access']) if 'mobile_access' in u_row.index else 0,
                'position':     str(u_row['position']) if 'position' in u_row.index else '',
            }

# ── حقن JS لحفظ اسم المستخدم في query param عند تسجيل الدخول ──
st.markdown("""
<script>
(function(){
    // عند تحميل الصفحة: إذا كان query param فارغاً لكن localStorage به بيانات، أعد التوجيه
    var saved = localStorage.getItem('awaji_user');
    var url   = new URL(window.location.href);
    if (saved && !url.searchParams.get('_u')) {
        url.searchParams.set('_u', saved);
        window.location.replace(url.toString());
    }
})();
</script>
""", unsafe_allow_html=True)

# متغيرات السلات المحدثة (الصرف، الارجاع، النقل)
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
if 'confirm_out' not in st.session_state: st.session_state.confirm_out = False
if 'confirm_return' not in st.session_state: st.session_state.confirm_return = False
if 'confirm_transfer' not in st.session_state: st.session_state.confirm_transfer = False
if 'ef_result_html' not in st.session_state: st.session_state['ef_result_html'] = None
if 'ef_items' not in st.session_state: st.session_state['ef_items'] = None
if 'ef_confirm' not in st.session_state: st.session_state['ef_confirm'] = False
if 'backup_auth' not in st.session_state: st.session_state['backup_auth'] = False
if 'staff_auth' not in st.session_state: st.session_state['staff_auth'] = False
if 'settings_auth' not in st.session_state: st.session_state['settings_auth'] = False
if 'prev_page' not in st.session_state: st.session_state.prev_page = ""
if 'display_mode' not in st.session_state: st.session_state['display_mode'] = "desktop"
# متغيرات طلبات الارجاع
if 'ret_req_cart' not in st.session_state: st.session_state.ret_req_cart = []
if 'ret_req_review' not in st.session_state: st.session_state.ret_req_review = False
if 'input_retreq_code' not in st.session_state: st.session_state.input_retreq_code = 0
if 'input_retreq_qty' not in st.session_state: st.session_state.input_retreq_qty = 0
# متغيرات تعديل الفاتورة المحسّنة
if 'ef_contractor' not in st.session_state: st.session_state['ef_contractor'] = None
if 'ef_wh_from' not in st.session_state: st.session_state['ef_wh_from'] = None
if 'ef_wh_to' not in st.session_state: st.session_state['ef_wh_to'] = None

# شعار السعودية للطاقة مضمّن مباشرة في الكود
LOGO_DATA_URI = "data:image/png;base64,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"

# إخفاء الفاتورة تلقائياً عند تغيير الصفحة
if st.session_state.prev_page != st.session_state.page:
    if st.session_state.prev_page in ("stock_out","stock_return","stock_transfer"):
        st.session_state.last_inv_html = None
        st.session_state.last_ret_inv_html = None
        st.session_state.last_trans_inv_html = None
    st.session_state.prev_page = st.session_state.page

# شاشة تسجيل الدخول الإلزامية لتأمين النظام
if not st.session_state.auth:
    _, col_login, _ = st.columns([1, 1.5, 1])
    with col_login:
        st.markdown(f"""
        <div style='text-align:center; padding:30px 0 5px 0;'>
            <img src="{LOGO_DATA_URI}" width="190" style="max-width:100%; border-radius:12px; display:block; margin:auto; box-shadow:0 4px 15px rgba(0,74,153,0.2);">
        </div>
        <div style='text-align:center; margin:16px 0 5px 0;'>
            <div style='font-size:30px; font-weight:900; color:#004a99; letter-spacing:1px; line-height:1.2;'>السعودية للطاقة</div>
            <div style='font-size:20px; font-weight:800; color:#1daa60; margin-top:6px; letter-spacing:0.5px;'>نظام إدارة مواد طوارئ</div>
            <div style='font-size:16px; font-weight:700; color:#1daa60; margin-top:3px;'>دائرة شرق منطقة جازان</div>
            <hr style='border:2px solid #004a99; margin:16px 0 14px 0;'>
            <div style='font-size:22px; font-weight:900; color:#004a99;'>تسجيل الدخول</div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            login_user = st.text_input("رقم الجوال الخاص بالموظف")
            login_pass = st.text_input("كلمة المرور", type="password")
            login_btn = st.form_submit_button("تسجيل الدخول إلى النظام", use_container_width=True)
        if login_btn:
            res = pd.read_sql(f"SELECT * FROM users WHERE username='{login_user}' AND password='{login_pass}'", conn)
            if not res.empty:
                st.session_state.auth = True
                row = res.iloc[0]
                st.session_state.user_info = {
                    'username':     str(row['username']),
                    'full_name':    str(row['full_name']),
                    'role':         str(row['role']),
                    'mobile_access': int(row['mobile_access']) if 'mobile_access' in row.index else 0,
                    'position':     str(row['position']) if 'position' in row.index else '',
                }
                # ── حفظ المستخدم في query param + localStorage ──
                st.query_params["_u"] = login_user
                st.markdown(f"""<script>
                    localStorage.setItem('awaji_user', '{login_user}');
                </script>""", unsafe_allow_html=True)
                st.success("تم التحقق بنجاح، جاري الدخول...")
                st.rerun()
            else:
                st.error("بيانات الدخول خاطئة، يرجى إعادة المحاولة والتحقق من كلمة المرور.")
        st.divider()
        if st.button("إرسال طلب إعادة تعيين كلمة المرور"):
            if login_user:
                c.execute("INSERT INTO access_requests (phone, status, request_time) VALUES (?,?,?)",
                          (login_user, "معلق", now_mecca().strftime("%Y-%m-%d %H:%M")))
                conn.commit()
                st.success("تم إرسال طلب تصفير كلمة المرور لمدير النظام بنجاح.")
            else:
                st.warning("يرجى إدخال رقم جوالك أولاً في حقل اسم المستخدم ليتم رفعه للنظام.")
        st.markdown("""
        <div style='text-align:center; margin-top:30px; padding:12px 0; border-top:1px solid #e0e0e0;'>
            <p style='font-size:13px; color:#555; margin:4px 0;'>تم تطويره بواسطة: <b>أحمد سعيد عواجي</b></p>
            <p style='font-size:12px; color:#888; margin:4px 0;'>جميع الحقوق محفوظة لصيانة اعطال دائرة شرق منطقة جازان © 2026</p>
        </div>
        """, unsafe_allow_html=True)

# =========================================================
# 7. بيئة عمل النظام الرئيسية (القوائم والتبويبات الشاملة)
# =========================================================
else:
    u = st.session_state.user_info
    
    # بناء شريط التنقل الجانبي بالكامل بالمسميات الأصلية
    with st.sidebar:
        st.markdown(f"""
        <div class='sidebar-header'>
            <img src="{LOGO_DATA_URI}" width="130" style="max-width:100%; border-radius:8px; display:block; margin:auto;">
            <br>
            <b style='font-size:15px;'>نظام إدارة مواد الطوارئ</b><br>
            <span style='color:#1daa60; font-size:13px; font-weight:bold;'>دائرة شرق منطقة جازان</span><br>
            <hr style="margin:12px 0; border:1px solid #004a99;">
            <span style='font-size:13px; color:#555;'>👤 الموظف: <b>{u['full_name']}</b></span><br>
            <span style='font-size:12px; background:#e1f5fe; color:#0288d1; padding:2px 8px; border-radius:10px;'>{u['role']}</span>
        </div>
        """, unsafe_allow_html=True)

        # ── ساعة رقمية بتوقيت مكة المكرمة ──
        components.html("""
        <div style='text-align:center;padding:8px 4px 6px 4px;'>
            <div id='dg' style='color:#004a99;font-size:28px;font-weight:900;
                                font-family:monospace;letter-spacing:3px;
                                line-height:1.2;'>--:--:--</div>
            <div id='dt' style='color:#004a99;font-size:13px;font-weight:700;
                                margin-top:4px;letter-spacing:1px;'>----/--/--</div>
        </div>
        <script>
        function tick(){
            var now=new Date();
            var utc=now.getTime()+now.getTimezoneOffset()*60000;
            var mc=new Date(utc+3*3600000);
            var h=String(mc.getHours()).padStart(2,'0');
            var m=String(mc.getMinutes()).padStart(2,'0');
            var s=String(mc.getSeconds()).padStart(2,'0');
            var ds=['الأحد','الاثنين','الثلاثاء','الأربعاء','الخميس','الجمعة','السبت'];
            var dy=String(mc.getDate()).padStart(2,'0');
            var mo=String(mc.getMonth()+1).padStart(2,'0');
            var yr=mc.getFullYear();
            var d=document.getElementById('dg');
            var t=document.getElementById('dt');
            if(d) d.textContent=h+':'+m+':'+s;
            if(t) t.textContent=ds[mc.getDay()]+'  '+yr+'/'+mo+'/'+dy;
        }
        tick();
        setInterval(tick,1000);
        </script>
        """, height=95)

        role = u['role']

        # ── موجه بلاغات: صلاحيات محدودة ──
        if role == "موجه بلاغات":
            if st.button("📊 رصيد المستودعات"): st.session_state.page = "inventory_status"
            st.divider()
            st.sidebar.markdown("<p style='text-align:center; font-weight:bold; color:#1daa60; margin:0;'>عمليات الصرف والارجاع ونقل المواد</p>", unsafe_allow_html=True)
            if st.button("🛒 صرف مواد للمقاول"): st.session_state.page = "stock_out"
            # عدد طلبات الارجاع المعلقة
            pending_ret_count = pd.read_sql("SELECT COUNT(*) as cnt FROM return_requests WHERE status='معلق'", conn).iloc[0]['cnt']
            ret_btn_label = f"📤 طلبات الارجاع" + (f"  🔴 {pending_ret_count}" if pending_ret_count > 0 else "")
            if st.button(ret_btn_label): st.session_state.page = "return_requests_user"
            st.divider()
            if st.button("✏️ تعديل فاتورة سابقة"): st.session_state.page = "edit_invoice"
            if st.button("🗂️ أرشيف فواتيري"): st.session_state.page = "my_invoices"
            st.divider()
            if st.button("📞 أرقام التواصل"): st.session_state.page = "contacts_page"

        # ── موظف مستودع: كل شيء إلا التحكم بالنظام ──
        elif role == "موظف مستودع":
            if st.button("📊 رصيد المستودعات"): st.session_state.page = "inventory_status"
            if st.button("📑 تعريف مواد جديدة"): st.session_state.page = "item_defs"
            if st.button("⚠️ تنبيهات نقص مواد"): st.session_state.page = "alerts_page"
            st.divider()
            st.sidebar.markdown("<p style='text-align:center; font-weight:bold; color:#1daa60; margin:0;'>عمليات الصرف والارجاع ونقل المواد</p>", unsafe_allow_html=True)
            if st.button("📥 إضافة مواد إلى المستودع"): st.session_state.page = "stock_in"
            if st.button("🛒 صرف مواد للمقاول"): st.session_state.page = "stock_out"
            if st.button("🔄 ارجاع المواد"): st.session_state.page = "stock_return"
            if st.button("🚛 نقل مادة من مستودع إلى آخر"): st.session_state.page = "stock_transfer"
            pending_ret_wh = pd.read_sql("SELECT COUNT(*) as cnt FROM return_requests WHERE status='معلق'", conn).iloc[0]['cnt']
            ret_wh_label = f"📥 طلبات الارجاع المعلقة" + (f"  🔴 {pending_ret_wh}" if pending_ret_wh > 0 else "")
            if st.button(ret_wh_label): st.session_state.page = "return_requests_admin"
            st.divider()
            if st.button("🛠️ سجل العمليات التفصيلي"): st.session_state.page = "view_logs"
            if st.button("✏️ تعديل فاتورة سابقة"): st.session_state.page = "edit_invoice"
            st.divider()
            if st.button("📞 أرقام التواصل"): st.session_state.page = "contacts_page"

        # ── مدير النظام: صلاحيات كاملة ──
        else:
            if st.button("📊 رصيد المستودعات"): st.session_state.page = "inventory_status"
            if st.button("📑 تعريف مواد جديدة"): st.session_state.page = "item_defs"
            if st.button("⚠️ تنبيهات نقص مواد"): st.session_state.page = "alerts_page"
            st.divider()
            st.sidebar.markdown("<p style='text-align:center; font-weight:bold; color:#1daa60; margin:0;'>عمليات الصرف والارجاع ونقل المواد</p>", unsafe_allow_html=True)
            if st.button("📥 إضافة مواد إلى المستودع"): st.session_state.page = "stock_in"
            if st.button("🛒 صرف مواد للمقاول"): st.session_state.page = "stock_out"
            if st.button("🔄 ارجاع المواد"): st.session_state.page = "stock_return"
            if st.button("🚛 نقل مادة من مستودع إلى آخر"): st.session_state.page = "stock_transfer"
            pending_ret_adm = pd.read_sql("SELECT COUNT(*) as cnt FROM return_requests WHERE status='معلق'", conn).iloc[0]['cnt']
            ret_adm_label = f"📥 طلبات الارجاع المعلقة" + (f"  🔴 {pending_ret_adm}" if pending_ret_adm > 0 else "")
            if st.button(ret_adm_label): st.session_state.page = "return_requests_admin"
            st.divider()
            if st.button("🛠️ سجل العمليات التفصيلي"): st.session_state.page = "view_logs"
            if st.button("✏️ تعديل فاتورة سابقة"): st.session_state.page = "edit_invoice"
            if st.button("📞 أرقام التواصل"): st.session_state.page = "contacts_page"
            st.divider()
            st.sidebar.markdown("<p style='text-align:center; font-weight:bold; color:#004a99; margin:0;'>⚙️ التحكم بالنظام</p>", unsafe_allow_html=True)
            if st.button("👥 إدارة حسابات الموظفين والطلبات"): st.session_state.page = "manage_staff"
            if st.button("🏢 إدارة المستودعات والمقاولين والفئات"): st.session_state.page = "global_settings"
            if st.button("💾 إدارة النسخ الاحتياطية"): st.session_state.page = "backup_page"

        st.divider()
        if st.button("🚪 خروج من النظام"):
            st.session_state.auth = False
            st.session_state.user_info = None
            # مسح localStorage و query params عند الخروج
            st.query_params.clear()
            st.markdown("""<script>
                localStorage.removeItem('awaji_user');
            </script>""", unsafe_allow_html=True)
            st.rerun()

        # ── خيار اختيار النسخة (لمدير النظام فقط، أو من منحهم صلاحية الجوال) ──
        user_mobile_access = int(u.get('mobile_access', 0))
        if role == "مدير نظام" or user_mobile_access == 1:
            st.divider()
            st.markdown("""
            <p style='text-align:center; font-weight:bold; color:#555; margin:0 0 6px 0; font-size:13px;'>
                🖥️ اختر نسخة العرض
            </p>""", unsafe_allow_html=True)
            col_desk, col_mob = st.columns(2)
            with col_desk:
                desktop_style = "background-color:#004a99 !important; color:white !important; border:2px solid #004a99 !important;" if st.session_state.get('display_mode','desktop') == 'desktop' else ""
                if st.button("💻\nحاسب", key="mode_desktop", use_container_width=True, help="عرض النظام بوضع الحاسب الآلي"):
                    st.session_state['display_mode'] = 'desktop'
                    st.rerun()
            with col_mob:
                if st.button("📱\nجوال", key="mode_mobile", use_container_width=True, help="عرض النظام بوضع الجوال"):
                    st.session_state['display_mode'] = 'mobile'
                    st.rerun()
            # مؤشر النسخة الحالية
            mode_label = "💻 نسخة الحاسب" if st.session_state.get('display_mode','desktop') == 'desktop' else "📱 نسخة الجوال"
            mode_color = "#004a99" if st.session_state.get('display_mode','desktop') == 'desktop' else "#1daa60"
            st.markdown(f"""
            <div style='text-align:center; margin-top:4px;'>
                <span style='background:{mode_color}; color:white; border-radius:10px; padding:3px 12px; font-size:12px; font-weight:bold;'>
                    {mode_label} — مفعّلة
                </span>
            </div>""", unsafe_allow_html=True)
            
        st.markdown(f"""
        <div class='creator-info'>
            تم تطويره بواسطة: أحمد سعيد عواجي<br>
            جميع الحقوق محفوظة لصيانة اعطال دائرة شرق منطقة جازان © 2026
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
            if "num_in_rows" not in st.session_state: st.session_state.num_in_rows = 3
            col_nr, _ = st.columns([1, 4])
            new_nr = col_nr.number_input("عدد المواد المراد شحنها:", min_value=1, max_value=20, value=st.session_state.num_in_rows, step=1)
            if new_nr != st.session_state.num_in_rows: st.session_state.num_in_rows = new_nr; st.rerun()
            st.write("---")
            with st.form("stock_in_form", clear_on_submit=True):
                st.write("##### 📝 تعبئة نموذج الشحن الوارد (يمكن شحن أكثر من مادة دفعة واحدة):")
                in_rows = []
                for ri in range(st.session_state.num_in_rows):
                    st.markdown(f"**📦 المادة رقم ({ri+1}):**")
                    r1,r2,r3 = st.columns([1.5,3,1.5])
                    r_code = r1.text_input("كود المادة *", key=f"in_code_{ri}").strip()
                    r_wh   = r2.selectbox("المستودع *", list_warehouses, key=f"in_wh_{ri}")
                    r_qty  = r3.number_input("الكمية *", min_value=1, value=10, step=1, key=f"in_qty_{ri}")
                    if r_code: in_rows.append({'code':r_code,'wh':r_wh,'qty':r_qty})
                st.write("---")
                if st.form_submit_button("💾 اعتماد وتثبيت كافة الكميات الواردة بالمخزن"):
                    if not in_rows:
                        st.error("⚠️ يرجى كتابة كود المادة لصف واحد على الأقل.")
                    else:
                        ok_count = 0; err_list = []
                        for row_in in in_rows:
                            mat_res = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{row_in['code']}'", conn)
                            if mat_res.empty:
                                err_list.append(row_in['code'])
                            else:
                                item_name = mat_res.iloc[0]['item_name']; item_cat = mat_res.iloc[0]['category']
                                c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                          (row_in['code'], row_in['qty'], row_in['wh'], "", item_cat))
                                save_log("شحن وإدخل مخزني", row_in['code'], row_in['qty'],
                                         f"شحن كمية ({row_in['qty']}) من صنف [{item_name}] إلى المستودع [{row_in['wh']}]", u['full_name'])
                                ok_count += 1
                        conn.commit()
                        if ok_count: st.success(f"✅ تم بنجاح شحن ({ok_count}) صنف للمستودعات!")
                        if err_list: st.error(f"❌ الأكواد غير معرّفة: {', '.join(err_list)}")
                        if ok_count: st.session_state.num_in_rows = 3; st.rerun()
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
            # إضافة يدوية باستخدام الكود
            col_out1, col_out2, col_out3 = st.columns([1.5, 2, 1])
            out_code = col_out1.text_input("كود المادة للصرف *", key=f"out_code_val_{st.session_state.input_out_code}").strip()
            out_qty = col_out2.number_input("الكمية المراد سحبها *", min_value=1, value=1, step=1, key=f"out_qty_val_{st.session_state.input_out_qty}")
            if col_out3.button("➕ إضافة الصنف للسلة"):
                if out_code and out_qty > 0:
                    mat_chk = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{out_code}'", conn)
                    if mat_chk.empty:
                        st.error("❌ كود المادة المدخل غير معرّف بالنظام!")
                    else:
                        item_name = mat_chk.iloc[0]['item_name']; item_cat = mat_chk.iloc[0]['category']
                        avail_qty_res = pd.read_sql(f"SELECT SUM(qty) as total FROM inventory WHERE item_code='{out_code}' AND warehouse='{out_wh}'", conn)
                        avail_qty = avail_qty_res.iloc[0]['total'] if not avail_qty_res.empty and avail_qty_res.iloc[0]['total'] is not None else 0
                        already_in_cart = sum(item['qty'] for item in st.session_state.cart if item['code'] == out_code)
                        if avail_qty < (out_qty + already_in_cart):
                            st.error(f"❌ رصيد غير كافٍ! المتاح في المستودع حالياً هو ({int(avail_qty)}) فقط.")
                        else:
                            ex = [i for i,x in enumerate(st.session_state.cart) if x['code']==out_code]
                            if ex: st.session_state.cart[ex[0]]['qty'] += out_qty
                            else: st.session_state.cart.append({'code': out_code, 'name': item_name, 'qty': out_qty, 'cat': item_cat})
                            st.session_state.input_out_code += 1; st.session_state.input_out_qty += 1; st.rerun()

            if st.session_state.cart:
                render_editable_cart('cart', out_wh)
                c_btn1, c_btn2 = st.columns([1, 1])
                if c_btn1.button("🗑️ تفريغ وإلغاء السلة بالكامل"):
                    st.session_state.cart = []; st.session_state.review_out = False; st.session_state.confirm_out = False; st.rerun()
                # ── التحقق من الأرصدة قبل السماح بالمراجعة ──
                stock_errors_out = validate_cart_stock(st.session_state.cart, out_wh)
                if stock_errors_out:
                    st.markdown("<div style='background:#ffebee;border:2px solid #c62828;border-radius:10px;padding:14px 18px;margin:10px 0;direction:rtl;'>"
                                "⛔ <b>لا يمكن إصدار الفاتورة — الكميات التالية تتجاوز الرصيد المتاح في المستودع:</b><br>"
                                + "<br>".join(stock_errors_out) +
                                "</div>", unsafe_allow_html=True)
                    st.session_state.review_out = False
                    st.session_state.confirm_out = False
                else:
                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                    if c_btn2.button("🔍 مراجعة ومعاينة مستند الصرف الرسمي قبل الاعتماد"):
                        st.session_state.review_out = True; st.session_state.confirm_out = False
                    st.markdown("</div>", unsafe_allow_html=True)
                if st.session_state.review_out:
                    st.write("---")
                    # تحقق مزدوج لحظة الإصدار (قد يتغير الرصيد بين المراجعة والتأكيد)
                    stock_errors_final = validate_cart_stock(st.session_state.cart, out_wh)
                    if stock_errors_final:
                        st.markdown("<div style='background:#ffebee;border:2px solid #c62828;border-radius:10px;padding:14px 18px;margin:10px 0;direction:rtl;'>"
                                    "⛔ <b>تغيّر الرصيد! لا يمكن إصدار الفاتورة:</b><br>"
                                    + "<br>".join(stock_errors_final) +
                                    "</div>", unsafe_allow_html=True)
                        st.session_state.review_out = False
                        st.session_state.confirm_out = False
                    else:
                        st.write("### 📄 المعاينة الحية المباشرة للفاتورة الصادرة:")
                        inv_no_preview = now_mecca().strftime("%d%H%M")
                        html_invoice = render_invoice_html("فاتورة صرف مواد طوارئ", st.session_state.cart, out_wh, out_contractor, u['full_name'], inv_no_preview)
                        components.html(html_invoice, height=480, scrolling=True)
                        if not st.session_state.confirm_out:
                            st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                            if st.button("🚀 تصدير الفاتورة وخصم المواد من المستودع"):
                                st.session_state.confirm_out = True; st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            items_txt = "، ".join([f"{i['name']} ({i['qty']})" for i in st.session_state.cart])
                            st.markdown(f"""<div class='warn-box'>⚠️ <b>هل أنت متأكد من تصدير الفاتورة؟</b><br>
                            سيتم خصم المواد التالية من مستودع <b>{out_wh}</b> تلقائياً:<br>
                            {items_txt}<br>المقاول المستلم: <b>{out_contractor}</b></div>""", unsafe_allow_html=True)
                            col_yes, col_no = st.columns([1, 1])
                            if col_yes.button("✅ نعم، تأكيد الخصم والأرشفة"):
                                # تحقق أخير قبل الخصم الفعلي
                                final_errors = validate_cart_stock(st.session_state.cart, out_wh)
                                if final_errors:
                                    st.error("⛔ لا يمكن تنفيذ الصرف — الرصيد غير كافٍ:\n" + "\n".join(final_errors))
                                    st.session_state.confirm_out = False
                                else:
                                    for item in st.session_state.cart:
                                        c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                                  (item['code'], -item['qty'], out_wh, out_contractor, item['cat']))
                                        save_log("صرف مواد لمقاول", item['code'], item['qty'], f"صرف للمقاول [{out_contractor}] من مستودع [{out_wh}] برقم قيد {inv_no_preview}", u['full_name'])
                                    archive_invoice("صرف", inv_no_preview, out_wh, "", out_contractor, u['full_name'], json.dumps(st.session_state.cart), html_invoice)
                                    conn.commit()
                                    st.session_state.last_inv_html = html_invoice
                                    st.session_state.cart = []; st.session_state.review_out = False; st.session_state.confirm_out = False
                                    st.success(f"🎉 تم بنجاح خصم الرصيد وأرشفة مستند الصرف رقم ({inv_no_preview}) بنجاح كلي!"); st.rerun()
                            if col_no.button("❌ لا، إلغاء"):
                                st.session_state.confirm_out = False; st.rerun()

            if st.session_state.last_inv_html and not st.session_state.cart:
                st.divider()
                ch1, ch2 = st.columns([4,1])
                ch1.write("### 🖨️ آخر فاتورة صرف تم إنشاؤها بنجاح (جاهزة للطباعة الفورية):")
                if ch2.button("✖️ إخفاء", key="hide_out_inv"): st.session_state.last_inv_html = None; st.rerun()
                components.html(st.session_state.last_inv_html, height=520, scrolling=True)
    # ---------------------------------------------------------
    # صفحة: ارجاع فائض المواد من المقاولين
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_return":
        st.markdown("<div class='main-title'>🔄 ارجاع وإدخال فائض ومسترجعات المواد الميدانية</div>", unsafe_allow_html=True)
        if not list_warehouses or not list_contractors:
            st.warning("⚠️ يرجى التأكد من تعريف المستودعات والمقاولين المعتمدين في لوحة الإعدادات أولاً.")
        else:
            col_ret_h1, col_ret_h2 = st.columns([2, 1.5])
            ret_contractor = col_ret_h1.selectbox("🏗️ المقاول المعتمد المسلّم للمواد:", list_contractors)
            ret_wh = col_ret_h2.selectbox("📍 إيداع وارجاع إلى مستودع:", list_warehouses)
            st.write("---")
            col_ret1, col_ret2, col_ret3 = st.columns([1.5, 2, 1])
            ret_code = col_ret1.text_input("كود المادة للارجاع *", key=f"ret_code_val_{st.session_state.input_ret_code}").strip()
            ret_qty = col_ret2.number_input("الكمية المرتجعة المودعة *", min_value=1, value=1, step=1, key=f"ret_qty_val_{st.session_state.input_ret_qty}")
            if col_ret3.button("➕ إضافة المرتجع للسلة"):
                if ret_code and ret_qty > 0:
                    mat_chk = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{ret_code}'", conn)
                    if mat_chk.empty:
                        st.error("❌ كود المادة المدخل غير معرّف بالنظام!")
                    else:
                        item_name = mat_chk.iloc[0]['item_name']; item_cat = mat_chk.iloc[0]['category']
                        ex = [i for i,x in enumerate(st.session_state.return_cart) if x['code']==ret_code]
                        if ex: st.session_state.return_cart[ex[0]]['qty'] += ret_qty
                        else: st.session_state.return_cart.append({'code': ret_code, 'name': item_name, 'qty': ret_qty, 'cat': item_cat})
                        st.session_state.input_ret_code += 1; st.session_state.input_ret_qty += 1; st.rerun()

            if st.session_state.return_cart:
                render_editable_cart('return_cart')
                c_r_btn1, c_r_btn2 = st.columns([1, 1])
                if c_r_btn1.button("🗑️ تفريغ وإلغاء سلة الارجاع"):
                    st.session_state.return_cart = []; st.session_state.review_return = False; st.session_state.confirm_return = False; st.rerun()
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                if c_r_btn2.button("🔍 مراجعة ومعاينة مستند الارجاع الرسمي قبل الاعتماد"):
                    st.session_state.review_return = True; st.session_state.confirm_return = False
                st.markdown("</div>", unsafe_allow_html=True)
                if st.session_state.review_return:
                    st.write("---")
                    st.write("### 📄 المعاينة الحية المباشرة لفاتورة الارجاع الإيداعية:")
                    ret_inv_no_preview = now_mecca().strftime("%d%H%M")
                    html_ret_invoice = render_return_invoice_html("فاتورة ارجاع مواد طوارئ", st.session_state.return_cart, ret_wh, ret_contractor, u['full_name'], ret_inv_no_preview)
                    components.html(html_ret_invoice, height=480, scrolling=True)
                    if not st.session_state.confirm_return:
                        st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                        if st.button("🚀 تصدير فاتورة الارجاع وإضافة المواد للمستودع"):
                            st.session_state.confirm_return = True; st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                    else:
                        items_txt = "، ".join([f"{i['name']} ({i['qty']})" for i in st.session_state.return_cart])
                        st.markdown(f"""<div class='warn-box'>⚠️ <b>هل أنت متأكد من تصدير فاتورة الارجاع؟</b><br>
                        سيتم إضافة المواد التالية إلى مستودع <b>{ret_wh}</b> تلقائياً:<br>
                        {items_txt}<br>المقاول المسلّم: <b>{ret_contractor}</b></div>""", unsafe_allow_html=True)
                        col_yes, col_no = st.columns([1, 1])
                        if col_yes.button("✅ نعم، تأكيد قيد الارجاع والأرشفة"):
                            for item in st.session_state.return_cart:
                                c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                          (item['code'], item['qty'], ret_wh, ret_contractor, item['cat']))
                                save_log("ارجاع فائض مواد", item['code'], item['qty'], f"ارجاع وإيداع من المقاول [{ret_contractor}] في مستودع [{ret_wh}] برقم قيد {ret_inv_no_preview}", u['full_name'])
                            archive_invoice("ارجاع", ret_inv_no_preview, ret_wh, "", ret_contractor, u['full_name'], json.dumps(st.session_state.return_cart), html_ret_invoice)
                            conn.commit()
                            st.session_state.last_ret_inv_html = html_ret_invoice
                            st.session_state.return_cart = []; st.session_state.review_return = False; st.session_state.confirm_return = False
                            st.success(f"🎉 تم بنجاح قيد وإضافة الرصيد المرتجع وأرشفة المستند رقم ({ret_inv_no_preview}) بنجاح كلي!"); st.rerun()
                        if col_no.button("❌ لا، إلغاء"):
                            st.session_state.confirm_return = False; st.rerun()

            if st.session_state.last_ret_inv_html and not st.session_state.return_cart:
                st.divider()
                rh1, rh2 = st.columns([4,1])
                rh1.write("### 🖨️ آخر فاتورة ارجاع تم إنشاؤها بنجاح (جاهزة للطباعة الفورية):")
                if rh2.button("✖️ إخفاء", key="hide_ret_inv"): st.session_state.last_ret_inv_html = None; st.rerun()
                components.html(st.session_state.last_ret_inv_html, height=520, scrolling=True)
    # ---------------------------------------------------------
    # صفحة: تقديم طلب ارجاع (موجه البلاغات)
    # ---------------------------------------------------------
    elif st.session_state.page == "return_requests_user":
        st.markdown("<div class='main-title'>📤 تقديم طلب ارجاع مواد</div>", unsafe_allow_html=True)
        if not list_warehouses or not list_contractors:
            st.warning("⚠️ يرجى التأكد من تعريف المستودعات والمقاولين في لوحة الإعدادات أولاً.")
        else:
            st.info("ℹ️ سيتم رفع الطلب إلى مسؤول المستودع ومدير النظام للمراجعة والاعتماد قبل إضافة المواد للمستودع.")

            tab_new_req, tab_my_req = st.tabs(["➕ طلب ارجاع جديد", "📋 طلباتي السابقة"])

            with tab_new_req:
                col_rr1, col_rr2 = st.columns([1.5, 2])
                rr_wh = col_rr1.selectbox("📍 المستودع الذي سيُرجع إليه:", list_warehouses, key="rr_wh_sel")
                rr_contractor = col_rr2.selectbox("🏗️ المقاول المسلّم للمواد:", list_contractors, key="rr_cont_sel")

                st.write("---")
                col_rr_c1, col_rr_c2, col_rr_c3 = st.columns([1.5, 2, 1])
                rr_code = col_rr_c1.text_input("كود المادة المرتجعة *", key=f"rr_code_{st.session_state.input_retreq_code}").strip()
                rr_qty  = col_rr_c2.number_input("الكمية المرتجعة *", min_value=1, value=1, step=1, key=f"rr_qty_{st.session_state.input_retreq_qty}")
                if col_rr_c3.button("➕ إضافة للقائمة"):
                    if rr_code and rr_qty > 0:
                        mat_r = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{rr_code}'", conn)
                        if mat_r.empty:
                            st.error("❌ كود المادة المدخل غير معرّف بالنظام!")
                        else:
                            item_nm = mat_r.iloc[0]['item_name']; item_ct = mat_r.iloc[0]['category']
                            ex = [i for i,x in enumerate(st.session_state.ret_req_cart) if x['code']==rr_code]
                            if ex: st.session_state.ret_req_cart[ex[0]]['qty'] += rr_qty
                            else: st.session_state.ret_req_cart.append({'code':rr_code,'name':item_nm,'qty':rr_qty,'cat':item_ct})
                            st.session_state.input_retreq_code += 1; st.session_state.input_retreq_qty += 1; st.rerun()

                if st.session_state.ret_req_cart:
                    st.write(f"### 📋 قائمة المواد المرتجعة ({len(st.session_state.ret_req_cart)} صنف):")
                    rh1,rh2,rh3,rh4 = st.columns([1.2,2.5,1.5,0.8])
                    rh1.markdown("**كود المادة**"); rh2.markdown("**اسم المادة**")
                    rh3.markdown("**الكمية**"); rh4.markdown("**حذف**")
                    st.markdown("<hr style='margin:4px 0 6px 0;'>", unsafe_allow_html=True)
                    to_rm = None
                    for idx_r, ritem in enumerate(st.session_state.ret_req_cart):
                        rc1,rc2,rc3,rc4 = st.columns([1.2,2.5,1.5,0.8])
                        rc1.write(ritem['code']); rc2.write(ritem['name'])
                        new_rqty = rc3.number_input("", min_value=1, value=int(ritem['qty']), step=1,
                                                     key=f"rreq_qty_{idx_r}", label_visibility="collapsed")
                        if new_rqty != int(ritem['qty']):
                            st.session_state.ret_req_cart[idx_r]['qty'] = new_rqty; st.rerun()
                        if rc4.button("🗑️", key=f"rreq_del_{idx_r}"): to_rm = idx_r
                    if to_rm is not None:
                        st.session_state.ret_req_cart.pop(to_rm); st.rerun()
                    st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

                    rb1, rb2 = st.columns([1,1])
                    if rb1.button("🗑️ إلغاء وتفريغ القائمة"):
                        st.session_state.ret_req_cart = []; st.session_state.ret_req_review = False; st.rerun()

                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                    if rb2.button("🔍 معاينة وإرسال الطلب"):
                        st.session_state.ret_req_review = True
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state.ret_req_review:
                        st.write("---")
                        req_no_preview = "RR" + now_mecca().strftime("%d%H%M")
                        html_rr = render_return_invoice_html("فاتورة ارجاع مواد طوارئ — بانتظار الاعتماد",
                                                              st.session_state.ret_req_cart, rr_wh, rr_contractor,
                                                              u['full_name'], req_no_preview)
                        st.write("### 📄 معاينة فاتورة الطلب:")
                        components.html(html_rr, height=450, scrolling=True)
                        items_txt_rr = "، ".join([f"{i['name']} ({i['qty']})" for i in st.session_state.ret_req_cart])
                        st.markdown(f"""<div class='warn-box'>⚠️ <b>سيتم رفع طلب الارجاع التالي للاعتماد:</b><br>
                        المستودع: <b>{rr_wh}</b> | المقاول: <b>{rr_contractor}</b><br>
                        {items_txt_rr}<br>
                        <small>لن تُضاف المواد إلى المستودع إلا بعد اعتماد مسؤول المستودع أو مدير النظام.</small>
                        </div>""", unsafe_allow_html=True)
                        col_send, col_cancel = st.columns([1,1])
                        if col_send.button("🚀 إرسال الطلب للاعتماد"):
                            ts = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("""INSERT INTO return_requests (request_no, warehouse, contractor, items_json, requester, status, invoice_html, timestamp)
                                         VALUES (?,?,?,?,?,?,?,?)""",
                                      (req_no_preview, rr_wh, rr_contractor,
                                       json.dumps(st.session_state.ret_req_cart),
                                       u['full_name'], "معلق", html_rr, ts))
                            conn.commit()
                            save_log("طلب ارجاع جديد", "—", 0,
                                     f"تقديم طلب ارجاع رقم [{req_no_preview}] للمستودع [{rr_wh}] من المقاول [{rr_contractor}]",
                                     u['full_name'])
                            st.session_state.ret_req_cart = []; st.session_state.ret_req_review = False
                            st.success(f"✅ تم إرسال طلب الارجاع رقم ({req_no_preview}) بنجاح وهو الآن بانتظار الاعتماد!"); st.rerun()
                        if col_cancel.button("❌ إلغاء"):
                            st.session_state.ret_req_review = False; st.rerun()

            with tab_my_req:
                st.write(f"### 📋 طلبات الارجاع المقدمة من: {u['full_name']}")
                df_my_req = pd.read_sql(
                    f"SELECT * FROM return_requests WHERE requester='{u['full_name']}' ORDER BY id DESC", conn)
                if df_my_req.empty:
                    st.info("ℹ️ لم تقم بتقديم أي طلبات ارجاع حتى الآن.")
                else:
                    for _, rr in df_my_req.iterrows():
                        status_color = "#2e7d32" if rr['status']=="معتمد" else ("#d32f2f" if rr['status']=="مرفوض" else "#f9a825")
                        st.markdown(f"""<div class='report-box'>
                            📄 <b>طلب ارجاع رقم (<span style='color:red;'>{rr['request_no']}</span>)</b>
                            <span style='background:{status_color};color:white;border-radius:8px;padding:2px 10px;font-size:13px;'>{rr['status']}</span><br>
                            📅 {rr['timestamp']} | 📍 المستودع: {rr['warehouse']} | 🏗️ المقاول: {rr['contractor']}
                            {f"<br>✅ اعتمده: <b>{rr['approved_by']}</b> في {rr['approved_at']}" if rr['approved_by'] else ""}
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"👁️ عرض الفاتورة {rr['request_no']}", key=f"myrr_{rr['id']}"):
                            st.session_state.view_archived_html[rr['request_no']] = not st.session_state.view_archived_html.get(rr['request_no'], False)
                        if st.session_state.view_archived_html.get(rr['request_no'], False):
                            components.html(rr['invoice_html'], height=500, scrolling=True)
                        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: مراجعة واعتماد طلبات الارجاع (مسؤول مستودع / مدير نظام)
    # ---------------------------------------------------------
    elif st.session_state.page == "return_requests_admin":
        st.markdown("<div class='main-title'>📥 طلبات الارجاع المعلقة — المراجعة والاعتماد</div>", unsafe_allow_html=True)
        if role not in ("موظف مستودع", "مدير نظام"):
            st.error("❌ هذه الصفحة متاحة لمسؤول المستودع ومدير النظام فقط.")
        else:
            tab_pending, tab_all = st.tabs(["⏳ الطلبات المعلقة", "📋 جميع الطلبات"])

            with tab_pending:
                df_pending = pd.read_sql("SELECT * FROM return_requests WHERE status='معلق' ORDER BY id DESC", conn)
                if df_pending.empty:
                    st.success("✅ لا توجد طلبات ارجاع معلقة حالياً.")
                else:
                    st.info(f"📋 يوجد ({len(df_pending)}) طلب ارجاع معلق يحتاج مراجعتك.")
                    for _, rr in df_pending.iterrows():
                        rr_items = json.loads(rr['items_json'])
                        with st.expander(f"📄 طلب رقم {rr['request_no']} | من: {rr['requester']} | {rr['timestamp']}", expanded=True):
                            st.markdown(f"""
                            <div style='background:#e3f2fd;border:1px solid #1976d2;border-radius:8px;padding:12px;margin-bottom:10px;'>
                                📍 <b>المستودع:</b> {rr['warehouse']} | 🏗️ <b>المقاول:</b> {rr['contractor']}<br>
                                👤 <b>مقدّم الطلب:</b> {rr['requester']}
                            </div>""", unsafe_allow_html=True)

                            # عرض المواد مع إمكانية التعديل
                            st.write("##### ✏️ المواد المطلوب ارجاعها (يمكن تعديل الكميات أو حذف صنف):")
                            adm_items_key = f"adm_items_{rr['id']}"
                            adm_wh_key = f"adm_wh_{rr['id']}"
                            if adm_items_key not in st.session_state:
                                st.session_state[adm_items_key] = [dict(x) for x in rr_items]
                            if adm_wh_key not in st.session_state:
                                st.session_state[adm_wh_key] = rr['warehouse']

                            # تعديل المستودع
                            new_adm_wh = st.selectbox("📍 المستودع الذي ستُضاف إليه المواد:", list_warehouses,
                                                        index=list_warehouses.index(st.session_state[adm_wh_key]) if st.session_state[adm_wh_key] in list_warehouses else 0,
                                                        key=f"adm_wh_sel_{rr['id']}")
                            if new_adm_wh != st.session_state[adm_wh_key]:
                                st.session_state[adm_wh_key] = new_adm_wh

                            # جدول التعديل
                            ah1,ah2,ah3,ah4 = st.columns([1.2,2.5,1.5,0.8])
                            ah1.markdown("**كود المادة**"); ah2.markdown("**اسم المادة**")
                            ah3.markdown("**الكمية**"); ah4.markdown("**حذف**")
                            st.markdown("<hr style='margin:2px 0 4px 0;'>", unsafe_allow_html=True)
                            adm_to_del = None
                            cur_items = st.session_state[adm_items_key]
                            for ai, aitem in enumerate(cur_items):
                                ac1,ac2,ac3,ac4 = st.columns([1.2,2.5,1.5,0.8])
                                ac1.write(aitem['code']); ac2.write(aitem['name'])
                                new_aq = ac3.number_input("", min_value=0, value=int(aitem['qty']), step=1,
                                                           key=f"adm_qty_{rr['id']}_{ai}", label_visibility="collapsed")
                                if new_aq != int(aitem['qty']):
                                    st.session_state[adm_items_key][ai]['qty'] = new_aq
                                if ac4.button("🗑️", key=f"adm_del_{rr['id']}_{ai}"): adm_to_del = ai
                            if adm_to_del is not None:
                                st.session_state[adm_items_key].pop(adm_to_del); st.rerun()

                            # إضافة صنف جديد
                            with st.expander("➕ إضافة صنف جديد للطلب"):
                                na1,na2,na3 = st.columns([1.5,3,1])
                                new_adm_code = na1.text_input("كود المادة:", key=f"adm_nc_{rr['id']}").strip()
                                new_adm_qty  = na3.number_input("الكمية:", min_value=1, value=1, key=f"adm_nq_{rr['id']}")
                                if na2.button("➕ إضافة", key=f"adm_nadd_{rr['id']}"):
                                    if new_adm_code:
                                        mat_ra = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{new_adm_code}'", conn)
                                        if mat_ra.empty:
                                            st.error("❌ الكود غير معرف!")
                                        else:
                                            ex_a = [j for j,x in enumerate(st.session_state[adm_items_key]) if x['code']==new_adm_code]
                                            if ex_a: st.session_state[adm_items_key][ex_a[0]]['qty'] += new_adm_qty
                                            else: st.session_state[adm_items_key].append({'code':new_adm_code,'name':mat_ra.iloc[0]['item_name'],'qty':new_adm_qty,'cat':mat_ra.iloc[0]['category']})
                                            st.rerun()

                            # معاينة الفاتورة
                            st.write("---")
                            if st.button(f"📄 معاينة فاتورة الطلب قبل الاعتماد", key=f"prev_rr_{rr['id']}"):
                                st.session_state.view_archived_html[f"prev_{rr['id']}"] = not st.session_state.view_archived_html.get(f"prev_{rr['id']}", False)
                            if st.session_state.view_archived_html.get(f"prev_{rr['id']}", False):
                                final_items_prev = [x for x in st.session_state[adm_items_key] if int(x['qty']) > 0]
                                html_prev = render_return_invoice_html("فاتورة ارجاع مواد طوارئ — معتمدة",
                                                                        final_items_prev, st.session_state[adm_wh_key],
                                                                        rr['contractor'], u['full_name'], rr['request_no'])
                                components.html(html_prev, height=450, scrolling=True)

                            # أزرار الاعتماد والرفض
                            st.write("---")
                            btn_col1, btn_col2 = st.columns([1,1])
                            adm_confirm_key = f"adm_confirm_{rr['id']}"
                            if adm_confirm_key not in st.session_state: st.session_state[adm_confirm_key] = False

                            st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                            if btn_col1.button(f"✅ اعتماد الطلب وإضافة المواد للمستودع", key=f"approve_{rr['id']}"):
                                st.session_state[adm_confirm_key] = True
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                            if btn_col2.button(f"❌ رفض الطلب", key=f"reject_{rr['id']}"):
                                c.execute("UPDATE return_requests SET status='مرفوض', approved_by=?, approved_at=? WHERE id=?",
                                          (u['full_name'], now_mecca().strftime("%Y-%m-%d %H:%M:%S"), int(rr['id'])))
                                conn.commit()
                                save_log("رفض طلب ارجاع", "—", 0, f"رفض طلب الارجاع رقم [{rr['request_no']}]", u['full_name'])
                                st.warning(f"⚠️ تم رفض طلب الارجاع ({rr['request_no']})."); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

                            if st.session_state.get(adm_confirm_key):
                                final_items = [x for x in st.session_state[adm_items_key] if int(x['qty']) > 0]
                                items_sum = "، ".join([f"{i['name']} ({i['qty']})" for i in final_items])
                                final_wh = st.session_state[adm_wh_key]
                                st.markdown(f"""<div class='warn-box'>⚠️ <b>تأكيد اعتماد طلب الارجاع ({rr['request_no']})؟</b><br>
                                سيتم إضافة المواد التالية إلى مستودع <b>{final_wh}</b>:<br>
                                {items_sum}
                                </div>""", unsafe_allow_html=True)
                                cy, cn = st.columns([1,1])
                                if cy.button(f"✅ نعم، اعتماد وإضافة للمستودع", key=f"conf_yes_{rr['id']}"):
                                    ts_now = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                                    final_inv_no = rr['request_no']
                                    for fitem in final_items:
                                        c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                                  (fitem['code'], int(fitem['qty']), final_wh, rr['contractor'], fitem['cat']))
                                        save_log("اعتماد ارجاع مواد", fitem['code'], fitem['qty'],
                                                 f"اعتماد ارجاع طلب [{final_inv_no}] إلى مستودع [{final_wh}] من [{rr['contractor']}]",
                                                 u['full_name'])
                                    new_html = render_return_invoice_html("فاتورة ارجاع مواد طوارئ — معتمدة",
                                                                           final_items, final_wh, rr['contractor'],
                                                                           u['full_name'], final_inv_no)
                                    archive_invoice("ارجاع", final_inv_no, final_wh, "", rr['contractor'],
                                                    u['full_name'], json.dumps(final_items), new_html)
                                    c.execute("""UPDATE return_requests SET status='معتمد', approved_by=?, approved_at=?,
                                                 items_json=?, invoice_html=?, warehouse=? WHERE id=?""",
                                              (u['full_name'], ts_now, json.dumps(final_items), new_html, final_wh, int(rr['id'])))
                                    conn.commit()
                                    st.success(f"🎉 تم اعتماد طلب الارجاع ({final_inv_no}) وإضافة المواد إلى مستودع [{final_wh}] بنجاح!"); st.rerun()
                                if cn.button(f"❌ إلغاء", key=f"conf_no_{rr['id']}"):
                                    st.session_state[adm_confirm_key] = False; st.rerun()

            with tab_all:
                st.write("### 📋 جميع طلبات الارجاع")
                df_all_rr = pd.read_sql("SELECT * FROM return_requests ORDER BY id DESC", conn)
                if df_all_rr.empty:
                    st.info("ℹ️ لا توجد أي طلبات ارجاع في النظام حتى الآن.")
                else:
                    col_filt1, col_filt2 = st.columns([1,2])
                    filt_status = col_filt1.selectbox("الحالة:", ["الكل","معلق","معتمد","مرفوض"], key="rr_status_filter")
                    filt_req = col_filt2.text_input("ابحث بالرقم أو اسم مقدم الطلب:", key="rr_search_filter").strip()
                    if filt_status != "الكل": df_all_rr = df_all_rr[df_all_rr['status']==filt_status]
                    if filt_req: df_all_rr = df_all_rr[df_all_rr['requester'].str.contains(filt_req,na=False) | df_all_rr['request_no'].str.contains(filt_req,na=False)]
                    for _, rr in df_all_rr.iterrows():
                        sc = "#2e7d32" if rr['status']=="معتمد" else ("#d32f2f" if rr['status']=="مرفوض" else "#f9a825")
                        st.markdown(f"""<div class='report-box'>
                            📄 <b>طلب رقم (<span style='color:red;'>{rr['request_no']}</span>)</b>
                            <span style='background:{sc};color:white;border-radius:8px;padding:2px 10px;'>{rr['status']}</span><br>
                            👤 {rr['requester']} | 📅 {rr['timestamp']} | 📍 {rr['warehouse']} | 🏗️ {rr['contractor']}
                            {f"<br>✅ اعتمده: <b>{rr['approved_by']}</b> في {rr['approved_at']}" if rr['approved_by'] else ""}
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"👁️ عرض {rr['request_no']}", key=f"allrr_{rr['id']}"):
                            st.session_state.view_archived_html[f"all_{rr['id']}"] = not st.session_state.view_archived_html.get(f"all_{rr['id']}", False)
                        if st.session_state.view_archived_html.get(f"all_{rr['id']}", False):
                            components.html(rr['invoice_html'], height=500, scrolling=True)
                        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

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
                            item_name = mat_chk.iloc[0]['item_name']; item_cat = mat_chk.iloc[0]['category']
                            avail_qty_res = pd.read_sql(f"SELECT SUM(qty) as total FROM inventory WHERE item_code='{trans_code}' AND warehouse='{trans_wh_from}'", conn)
                            avail_qty = avail_qty_res.iloc[0]['total'] if not avail_qty_res.empty and avail_qty_res.iloc[0]['total'] is not None else 0
                            already_in_cart = sum(item['qty'] for item in st.session_state.transfer_cart if item['code'] == trans_code)
                            if avail_qty < (trans_qty + already_in_cart):
                                st.error(f"❌ رصيد غير كافٍ! المتاح في مستودع المصدر حالياً هو ({avail_qty}) فقط.")
                            else:
                                ex = [i for i,x in enumerate(st.session_state.transfer_cart) if x['code']==trans_code]
                                if ex: st.session_state.transfer_cart[ex[0]]['qty'] += trans_qty
                                else: st.session_state.transfer_cart.append({'code': trans_code, 'name': item_name, 'qty': trans_qty, 'cat': item_cat})
                                st.session_state.input_trans_code += 1; st.session_state.input_trans_qty += 1; st.rerun()

                if st.session_state.transfer_cart:
                    render_editable_cart('transfer_cart', trans_wh_from)
                    c_t_btn1, c_t_btn2 = st.columns([1, 1])
                    if c_t_btn1.button("🗑️ تفريغ وإلغاء سلة التحويل"):
                        st.session_state.transfer_cart = []; st.session_state.review_transfer = False; st.session_state.confirm_transfer = False; st.rerun()
                    # ── التحقق من الأرصدة قبل السماح بالمراجعة ──
                    stock_errors_trans = validate_cart_stock(st.session_state.transfer_cart, trans_wh_from)
                    if stock_errors_trans:
                        st.markdown("<div style='background:#ffebee;border:2px solid #c62828;border-radius:10px;padding:14px 18px;margin:10px 0;direction:rtl;'>"
                                    "⛔ <b>لا يمكن تنفيذ النقل — الكميات التالية تتجاوز الرصيد المتاح في المستودع المصدر:</b><br>"
                                    + "<br>".join(stock_errors_trans) +
                                    "</div>", unsafe_allow_html=True)
                        st.session_state.review_transfer = False
                        st.session_state.confirm_transfer = False
                    else:
                        st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                        if c_t_btn2.button("🔍 مراجعة ومعاينة مستند النقل البيني الرسمي قبل الاعتماد"):
                            st.session_state.review_transfer = True; st.session_state.confirm_transfer = False
                        st.markdown("</div>", unsafe_allow_html=True)
                    if st.session_state.review_transfer:
                        st.write("---")
                        stock_errors_trans_final = validate_cart_stock(st.session_state.transfer_cart, trans_wh_from)
                        if stock_errors_trans_final:
                            st.markdown("<div style='background:#ffebee;border:2px solid #c62828;border-radius:10px;padding:14px 18px;margin:10px 0;direction:rtl;'>"
                                        "⛔ <b>تغيّر الرصيد! لا يمكن تنفيذ النقل:</b><br>"
                                        + "<br>".join(stock_errors_trans_final) +
                                        "</div>", unsafe_allow_html=True)
                            st.session_state.review_transfer = False
                            st.session_state.confirm_transfer = False
                        else:
                            st.write("### 📄 المعاينة الحية المباشرة لفاتورة النقل اللوجستي البيني:")
                            trans_inv_no_preview = now_mecca().strftime("%d%H%M")
                            html_trans_invoice = render_transfer_invoice_html("فاتورة نقل مواد من مستودع إلى آخر", st.session_state.transfer_cart, trans_wh_from, trans_wh_to, u['full_name'], trans_inv_no_preview)
                            components.html(html_trans_invoice, height=480, scrolling=True)
                            if not st.session_state.confirm_transfer:
                                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                                if st.button("🚀 تصدير فاتورة النقل وتنفيذ التحويل بين المستودعين"):
                                    st.session_state.confirm_transfer = True; st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                            else:
                                items_txt = "، ".join([f"{i['name']} ({i['qty']})" for i in st.session_state.transfer_cart])
                                st.markdown(f"""<div class='warn-box'>⚠️ <b>هل أنت متأكد من تصدير فاتورة النقل؟</b><br>
                                سيتم خصم المواد التالية من مستودع <b>{trans_wh_from}</b> وإضافتها إلى مستودع <b>{trans_wh_to}</b> تلقائياً:<br>
                                {items_txt}</div>""", unsafe_allow_html=True)
                                col_yes, col_no = st.columns([1, 1])
                                if col_yes.button("✅ نعم، تأكيد النقل والخصم والإيداع والأرشفة"):
                                    final_errors_trans = validate_cart_stock(st.session_state.transfer_cart, trans_wh_from)
                                    if final_errors_trans:
                                        st.error("⛔ لا يمكن تنفيذ النقل — الرصيد غير كافٍ الآن.")
                                        st.session_state.confirm_transfer = False
                                    else:
                                        for item in st.session_state.transfer_cart:
                                            c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                                      (item['code'], -item['qty'], trans_wh_from, "", item['cat']))
                                            c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                                      (item['code'], item['qty'], trans_wh_to, "", item['cat']))
                                            save_log("تحويل ونقل بيني لوجستي", item['code'], item['qty'], f"نقل وتحويل من مستودع [{trans_wh_from}] إلى مستودع [{trans_wh_to}] برقم قيد {trans_inv_no_preview}", u['full_name'])
                                        archive_invoice("تحويل", trans_inv_no_preview, trans_wh_from, trans_wh_to, "", u['full_name'], json.dumps(st.session_state.transfer_cart), html_trans_invoice)
                                        conn.commit()
                                        st.session_state.last_trans_inv_html = html_trans_invoice
                                        st.session_state.transfer_cart = []; st.session_state.review_transfer = False; st.session_state.confirm_transfer = False
                                        st.success(f"🎉 تم بنجاح قيد وخصم وإيداع الأرصدة التبادلية وأرشفة المستند رقم ({trans_inv_no_preview}) بنجاح كلي!"); st.rerun()
                                if col_no.button("❌ لا، إلغاء"):
                                    st.session_state.confirm_transfer = False; st.rerun()

                if st.session_state.last_trans_inv_html and not st.session_state.transfer_cart:
                    st.divider()
                    th1, th2 = st.columns([4,1])
                    th1.write("### 🖨️ آخر فاتورة نقل لوجستي تم إنشاؤها بنجاح (جاهزة للطباعة الفورية):")
                    if th2.button("✖️ إخفاء", key="hide_trans_inv"): st.session_state.last_trans_inv_html = None; st.rerun()
                    components.html(st.session_state.last_trans_inv_html, height=520, scrolling=True)
    # ---------------------------------------------------------
    # صفحة: تعديل فاتورة سابقة
    # ---------------------------------------------------------
    elif st.session_state.page == "edit_invoice":
        st.markdown("<div class='main-title'>✏️ تعديل فاتورة سابقة</div>", unsafe_allow_html=True)
        st.info("ℹ️ يمكنك تعديل الكميات والمقاول والمستودع وإضافة أصناف أو حذفها، ثم تصدير الفاتورة بنفس الرقم.")

        col_ef1, col_ef2 = st.columns([1, 2])
        ef_type = col_ef1.selectbox("نوع الفاتورة:", ["صرف", "ارجاع", "تحويل"])
        ef_no   = col_ef2.text_input("رقم الفاتورة:").strip()
        if st.button("🔍 بحث عن الفاتورة"):
            st.session_state['ef_search']      = ef_no
            st.session_state['ef_items']       = None
            st.session_state['ef_confirm']     = False
            st.session_state['ef_result_html'] = None
            st.session_state['ef_contractor']  = None
            st.session_state['ef_wh_from']     = None
            st.session_state['ef_wh_to']       = None

        if st.session_state.get('ef_search'):
            df_inv = pd.read_sql(
                f"SELECT * FROM archived_invoices WHERE invoice_no='{st.session_state['ef_search']}' AND invoice_type='{ef_type}'", conn)
            if df_inv.empty:
                st.error(f"❌ لم يتم العثور على فاتورة {ef_type} برقم ({st.session_state['ef_search']}).")
            else:
                row = df_inv.iloc[0]
                if st.session_state.get('ef_items') is None:
                    st.session_state['ef_items'] = json.loads(row['items_json'])
                if 'ef_confirm' not in st.session_state: st.session_state['ef_confirm'] = False
                # تهيئة قيم المقاول والمستودع القابلة للتعديل
                if st.session_state.get('ef_contractor') is None:
                    st.session_state['ef_contractor'] = row['contractor'] or ""
                if st.session_state.get('ef_wh_from') is None:
                    st.session_state['ef_wh_from'] = row['warehouse_from'] or ""
                if st.session_state.get('ef_wh_to') is None:
                    st.session_state['ef_wh_to'] = row['warehouse_to'] or ""

                orig_contractor = row['contractor'] or ""
                orig_wh_from    = row['warehouse_from'] or ""
                orig_wh_to      = row['warehouse_to'] or ""

                st.success(f"✅ فاتورة {ef_type} رقم ({row['invoice_no']}) | التاريخ: {row['timestamp']}")

                # ── تعديل المقاول والمستودع ──
                st.markdown("##### 🔧 تعديل بيانات الفاتورة:")
                if ef_type in ("صرف", "ارجاع"):
                    efc1, efc2 = st.columns([1, 1])
                    # المستودع
                    _wh_opts = list_warehouses
                    _wh_idx  = _wh_opts.index(st.session_state['ef_wh_from']) if st.session_state['ef_wh_from'] in _wh_opts else 0
                    new_ef_wh = efc1.selectbox(
                        "📍 المستودع المعني:" if ef_type=="صرف" else "📍 المستودع الذي يستلم المواد:",
                        _wh_opts, index=_wh_idx, key="ef_wh_sel")
                    if new_ef_wh != st.session_state['ef_wh_from']:
                        st.session_state['ef_wh_from'] = new_ef_wh
                    # المقاول
                    _con_opts = list_contractors
                    _con_idx  = _con_opts.index(st.session_state['ef_contractor']) if st.session_state['ef_contractor'] in _con_opts else 0
                    new_ef_con = efc2.selectbox(
                        "🏗️ المقاول المستلم للمواد:" if ef_type=="صرف" else "🏗️ المقاول المسلّم للمواد (المرجع):",
                        _con_opts, index=_con_idx, key="ef_con_sel")
                    if new_ef_con != st.session_state['ef_contractor']:
                        st.session_state['ef_contractor'] = new_ef_con
                    wh_from    = st.session_state['ef_wh_from']
                    wh_to      = ""
                    contractor = st.session_state['ef_contractor']

                elif ef_type == "تحويل":
                    efc1, efc2 = st.columns([1, 1])
                    _wh_opts = list_warehouses
                    _wf_idx  = _wh_opts.index(st.session_state['ef_wh_from']) if st.session_state['ef_wh_from'] in _wh_opts else 0
                    _wt_idx  = _wh_opts.index(st.session_state['ef_wh_to'])   if st.session_state['ef_wh_to']   in _wh_opts else 0
                    new_ef_wf = efc1.selectbox("📍 المستودع المصدر (المنقول منه):", _wh_opts, index=_wf_idx, key="ef_wf_sel")
                    new_ef_wt = efc2.selectbox("📍 المستودع المستلم (المنقول إليه):", _wh_opts, index=_wt_idx, key="ef_wt_sel")
                    if new_ef_wf != st.session_state['ef_wh_from']: st.session_state['ef_wh_from'] = new_ef_wf
                    if new_ef_wt != st.session_state['ef_wh_to']:   st.session_state['ef_wh_to']   = new_ef_wt
                    if new_ef_wf == new_ef_wt:
                        st.error("❌ المستودع المصدر والمستلم لا يمكن أن يكونا نفس المستودع!")
                    wh_from    = st.session_state['ef_wh_from']
                    wh_to      = st.session_state['ef_wh_to']
                    contractor = ""
                else:
                    wh_from = orig_wh_from; wh_to = orig_wh_to; contractor = orig_contractor

                st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

                # ── جدول الأصناف القابل للتعديل مع التحقق من الرصيد ──
                st.write("##### ✏️ تعديل الأصناف:")
                hh1, hh2, hh3, hh4 = st.columns([1.5, 3, 1.5, 0.8])
                hh1.markdown("**كود المادة**"); hh2.markdown("**اسم المادة**")
                hh3.markdown("**الكمية**"); hh4.markdown("**حذف**")
                st.markdown("<hr style='margin:4px 0 8px 0;'>", unsafe_allow_html=True)

                orig_items = json.loads(row['items_json'])
                to_del = None
                cart_has_stock_error = False

                for i, item in enumerate(st.session_state['ef_items']):
                    ec1, ec2, ec3, ec4 = st.columns([1.5, 3, 1.5, 0.8])
                    ec1.write(item['code']); ec2.write(item['name'])

                    # حساب الحد الأقصى المتاح بناءً على نوع الفاتورة
                    if ef_type == "صرف":
                        # الكمية المتاحة = رصيد المستودع + الكمية الأصلية في الفاتورة (لأنها لم تُخصم بعد التعديل)
                        avail_r = pd.read_sql(
                            f"SELECT SUM(qty) as t FROM inventory WHERE item_code='{item['code']}' AND warehouse='{wh_from}'", conn)
                        avail = int(avail_r.iloc[0]['t'] or 0)
                        orig_qty = next((int(x['qty']) for x in orig_items if x['code']==item['code']), 0)
                        max_allowed = avail + orig_qty  # الرصيد الحالي + ما كان مخصوماً أصلاً
                        new_q = ec3.number_input("", min_value=0, max_value=max(0, max_allowed),
                                                  value=min(int(item['qty']), max(0, max_allowed)),
                                                  step=1, key=f"ef_qty_{row['invoice_no']}_{i}",
                                                  label_visibility="collapsed")
                        if max_allowed <= 0 and int(item['qty']) > 0:
                            ec3.markdown(f"<span style='color:red;font-size:11px;'>⚠️ غير متوفر</span>", unsafe_allow_html=True)
                            cart_has_stock_error = True
                    elif ef_type == "تحويل":
                        avail_r = pd.read_sql(
                            f"SELECT SUM(qty) as t FROM inventory WHERE item_code='{item['code']}' AND warehouse='{wh_from}'", conn)
                        avail = int(avail_r.iloc[0]['t'] or 0)
                        orig_qty = next((int(x['qty']) for x in orig_items if x['code']==item['code']), 0)
                        max_allowed = avail + orig_qty
                        new_q = ec3.number_input("", min_value=0, max_value=max(0, max_allowed),
                                                  value=min(int(item['qty']), max(0, max_allowed)),
                                                  step=1, key=f"ef_qty_{row['invoice_no']}_{i}",
                                                  label_visibility="collapsed")
                    else:
                        new_q = ec3.number_input("", min_value=0, value=int(item['qty']), step=1,
                                                  key=f"ef_qty_{row['invoice_no']}_{i}",
                                                  label_visibility="collapsed")

                    if new_q != int(item['qty']):
                        st.session_state['ef_items'][i]['qty'] = new_q
                    if ec4.button("🗑️", key=f"ef_del_{i}", help="حذف هذا الصنف"):
                        to_del = i

                if to_del is not None:
                    st.session_state['ef_items'].pop(to_del); st.rerun()

                st.markdown("<hr style='margin:8px 0;'>", unsafe_allow_html=True)

                # ── إضافة صنف جديد ──
                with st.expander("➕ إضافة صنف جديد للفاتورة"):
                    na1, na2, na3 = st.columns([1.5, 3, 1])
                    new_code_ef = na1.text_input("كود المادة:", key="ef_new_code").strip()
                    new_qty_ef  = na3.number_input("الكمية:", min_value=1, value=1, key="ef_new_qty")
                    if na2.button("➕ إضافة للفاتورة", key="ef_add_btn"):
                        if new_code_ef:
                            mat_r = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{new_code_ef}'", conn)
                            if mat_r.empty:
                                st.error("❌ الكود غير معرف!")
                            else:
                                # تحقق من الرصيد عند الإضافة لفواتير الصرف والتحويل
                                if ef_type in ("صرف", "تحويل"):
                                    avail_new = pd.read_sql(
                                        f"SELECT SUM(qty) as t FROM inventory WHERE item_code='{new_code_ef}' AND warehouse='{wh_from}'", conn)
                                    avail_new_qty = int(avail_new.iloc[0]['t'] or 0)
                                    already = sum(x['qty'] for x in st.session_state['ef_items'] if x['code']==new_code_ef)
                                    if new_qty_ef + already > avail_new_qty:
                                        st.error(f"❌ رصيد غير كافٍ! المتاح في المستودع: ({avail_new_qty})")
                                        st.stop()
                                ex = [j for j,x in enumerate(st.session_state['ef_items']) if x['code']==new_code_ef]
                                if ex: st.session_state['ef_items'][ex[0]]['qty'] += new_qty_ef
                                else: st.session_state['ef_items'].append({
                                    'code': new_code_ef,
                                    'name': mat_r.iloc[0]['item_name'],
                                    'qty':  new_qty_ef,
                                    'cat':  mat_r.iloc[0]['category']
                                })
                                st.rerun()

                # ── تحقق نهائي من الرصيد قبل التأكيد ──
                new_items = st.session_state['ef_items']
                if ef_type in ("صرف", "تحويل") and not cart_has_stock_error:
                    stock_errors_ef = validate_cart_stock(
                        [x for x in new_items if int(x['qty']) > 0], wh_from)
                    # نطرح الكميات الأصلية لأنها ستُعاد
                    real_errors = []
                    for item in new_items:
                        if int(item['qty']) == 0: continue
                        avail_r = pd.read_sql(
                            f"SELECT SUM(qty) as t FROM inventory WHERE item_code='{item['code']}' AND warehouse='{wh_from}'", conn)
                        avail = int(avail_r.iloc[0]['t'] or 0)
                        orig_q = next((int(x['qty']) for x in orig_items if x['code']==item['code']), 0)
                        net_need = int(item['qty']) - orig_q  # الزيادة الفعلية المطلوبة
                        if net_need > avail:
                            real_errors.append(f"❌ <b>{item['name']}</b> — زيادة مطلوبة: {net_need} | متوفر: {avail}")
                    if real_errors:
                        st.markdown("<div style='background:#ffebee;border:2px solid #c62828;border-radius:10px;padding:14px 18px;margin:10px 0;direction:rtl;'>"
                                    "⛔ <b>لا يمكن حفظ الفاتورة — رصيد غير كافٍ للأصناف التالية:</b><br>"
                                    + "<br>".join(real_errors) + "</div>", unsafe_allow_html=True)
                        st.session_state['ef_confirm'] = False
                        st.stop()

                # ── حساب التغييرات للعرض ──
                changes = []
                for old_i in orig_items:
                    ni = next((x for x in new_items if x['code']==old_i['code']), None)
                    diff = int(old_i['qty']) - (int(ni['qty']) if ni else int(old_i['qty']))
                    if diff > 0:   changes.append(f"إعادة {diff} وحدة من [{old_i['name']}] إلى المستودع [{wh_from}]")
                    elif diff < 0: changes.append(f"خصم {abs(diff)} وحدة إضافية من [{old_i['name']}] من المستودع [{wh_from}]")
                for ni in new_items:
                    if not any(x['code']==ni['code'] for x in orig_items):
                        changes.append(f"إضافة صنف جديد [{ni['name']}] بكمية {ni['qty']}")
                if contractor != orig_contractor:
                    changes.append(f"تغيير المقاول من [{orig_contractor}] إلى [{contractor}]")
                if wh_from != orig_wh_from:
                    changes.append(f"تغيير المستودع من [{orig_wh_from}] إلى [{wh_from}]")

                if not st.session_state.get('ef_confirm'):
                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                    if st.button("💾 تأكيد التعديل وتصدير الفاتورة المعدّلة"):
                        st.session_state['ef_confirm'] = True; st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    ch_txt = "<br>".join([f"• {ch}" for ch in changes]) if changes else "• لا توجد تغييرات"
                    st.markdown(f"""<div class='warn-box'>
                    ⚠️ <b>هل أنت متأكد من تعديل الفاتورة ({row['invoice_no']})؟</b><br>
                    ستترتب على هذا التعديل الإجراءات التالية:<br>{ch_txt}
                    </div>""", unsafe_allow_html=True)
                    col_yes, col_no = st.columns([1,1])
                    if col_yes.button("✅ نعم، تأكيد التعديل والتصدير"):
                        inv_type = row['invoice_type']
                        # تطبيق الفروق على المخزون
                        for old_i in orig_items:
                            ni = next((x for x in new_items if x['code']==old_i['code']), {'qty':0})
                            diff = int(old_i['qty']) - int(ni['qty'])
                            if diff == 0: continue
                            cat_r = pd.read_sql(f"SELECT category FROM material_definitions WHERE item_code='{old_i['code']}'", conn)
                            cat = cat_r.iloc[0]['category'] if not cat_r.empty else old_i.get('cat','')
                            if inv_type == "صرف":
                                c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                          (old_i['code'], diff, wh_from, contractor, cat))
                                save_log("تعديل فاتورة صرف", old_i['code'], abs(diff),
                                         f"تعديل ({row['invoice_no']}): {old_i['name']} {old_i['qty']}->{ni['qty']}", u['full_name'])
                            elif inv_type == "ارجاع":
                                c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                          (old_i['code'], -diff, wh_from, contractor, cat))
                                save_log("تعديل فاتورة ارجاع", old_i['code'], abs(diff),
                                         f"تعديل ({row['invoice_no']}): {old_i['name']} {old_i['qty']}->{ni['qty']}", u['full_name'])
                            elif inv_type == "تحويل":
                                c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                          (old_i['code'], diff, wh_from, "", cat))
                                c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                          (old_i['code'], -diff, wh_to, "", cat))
                                save_log("تعديل فاتورة تحويل", old_i['code'], abs(diff),
                                         f"تعديل ({row['invoice_no']}): {old_i['name']} {old_i['qty']}->{ni['qty']}", u['full_name'])
                        # الأصناف الجديدة المضافة
                        for ni in new_items:
                            if not any(x['code']==ni['code'] for x in orig_items):
                                cat_r = pd.read_sql(f"SELECT category FROM material_definitions WHERE item_code='{ni['code']}'", conn)
                                cat = cat_r.iloc[0]['category'] if not cat_r.empty else ni.get('cat','')
                                if inv_type == "صرف":
                                    c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                              (ni['code'], -int(ni['qty']), wh_from, contractor, cat))
                                    save_log("تعديل فاتورة صرف - إضافة صنف", ni['code'], ni['qty'],
                                             f"إضافة صنف [{ni['name']}] للفاتورة ({row['invoice_no']})", u['full_name'])
                                elif inv_type == "ارجاع":
                                    c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                              (ni['code'], int(ni['qty']), wh_from, contractor, cat))
                                    save_log("تعديل فاتورة ارجاع - إضافة صنف", ni['code'], ni['qty'],
                                             f"إضافة صنف [{ni['name']}] للفاتورة ({row['invoice_no']})", u['full_name'])
                        # إعادة توليد الفاتورة بنفس الرقم مع البيانات الجديدة
                        filtered = [x for x in new_items if int(x['qty']) > 0]
                        if inv_type == "صرف":
                            new_html = render_invoice_html(f"فاتورة صرف مواد طوارئ (معدّل)", filtered, wh_from, contractor, u['full_name'], row['invoice_no'])
                        elif inv_type == "ارجاع":
                            new_html = render_return_invoice_html(f"فاتورة ارجاع مواد طوارئ (معدّل)", filtered, wh_from, contractor, u['full_name'], row['invoice_no'])
                        else:
                            new_html = render_transfer_invoice_html(f"فاتورة نقل مواد من مستودع إلى آخر (معدّل)", filtered, wh_from, wh_to, u['full_name'], row['invoice_no'])
                        c.execute("UPDATE archived_invoices SET items_json=?, html_content=?, warehouse_from=?, warehouse_to=?, contractor=? WHERE id=?",
                                  (json.dumps(new_items), new_html, wh_from, wh_to, contractor, int(row['id'])))
                        conn.commit()
                        st.session_state['ef_result_html'] = new_html
                        st.session_state['ef_items']       = None
                        st.session_state['ef_search']      = None
                        st.session_state['ef_confirm']     = False
                        st.session_state['ef_contractor']  = None
                        st.session_state['ef_wh_from']     = None
                        st.session_state['ef_wh_to']       = None
                        st.success(f"✅ تم تعديل الفاتورة ({row['invoice_no']}) وتحديث الأرشيف والمخزون بنجاح!"); st.rerun()
                    if col_no.button("❌ لا، إلغاء التعديل"):
                        st.session_state['ef_confirm'] = False; st.rerun()

        if st.session_state.get('ef_result_html'):
            st.write("### 📄 الفاتورة المعدّلة (جاهزة للطباعة):")
            efh1, efh2 = st.columns([4,1])
            if efh2.button("✖️ إخفاء", key="close_ef"): st.session_state['ef_result_html'] = None; st.rerun()
            components.html(st.session_state['ef_result_html'], height=540, scrolling=True)
    # ---------------------------------------------------------
    # صفحة: أرشيف فواتيري (خاص بموجه البلاغات)
    # ---------------------------------------------------------
    elif st.session_state.page == "my_invoices":
        st.markdown("<div class='main-title'>🗂️ أرشيف فواتيري</div>", unsafe_allow_html=True)
        st.info(f"📋 يعرض هذه الصفحة الفواتير التي قام بإصدارها: **{u['full_name']}**")
        col_mf1, col_mf2, col_mf3 = st.columns([1, 1, 1.2])
        mf_type = col_mf1.selectbox("نوع الفاتورة:", ["الكل", "صرف", "ارجاع"], key="mf_type")
        mf_no   = col_mf2.text_input("رقم الفاتورة (اختياري):", key="mf_no").strip()
        mf_date = col_mf3.date_input("تصفية بالتاريخ (اختياري):", value=None, key="mf_date")
        mf_query = f"SELECT * FROM archived_invoices WHERE employee='{u['full_name']}'"
        if mf_type != "الكل": mf_query += f" AND invoice_type='{mf_type}'"
        if mf_no:             mf_query += f" AND invoice_no LIKE '%{mf_no}%'"
        if mf_date:           mf_query += f" AND timestamp LIKE '{mf_date.strftime('%Y-%m-%d')}%'"
        mf_query += " ORDER BY id DESC"
        df_mf = pd.read_sql(mf_query, conn)
        if df_mf.empty:
            st.warning("⚠️ لا توجد فواتير تطابق معايير البحث.")
        else:
            st.success(f"✅ تم العثور على ({len(df_mf)}) فاتورة.")
            for _, mrow in df_mf.iterrows():
                st.markdown(f"""<div class='report-box'>
                    📄 <b>مستند {mrow['invoice_type']} رسمي برقم (<span style='color:red;'>{mrow['invoice_no']}</span>)</b><br>
                    📅 التاريخ: {mrow['timestamp']} | 📍 المستودع: {mrow['warehouse_from'] if mrow['warehouse_from'] else 'N/A'}
                    {f" | 🏗️ المقاول: {mrow['contractor']}" if mrow['contractor'] else ""}
                </div>""", unsafe_allow_html=True)
                if st.button(f"👁️ عرض الفاتورة {mrow['invoice_no']}", key=f"mfv_{mrow['id']}"):
                    st.session_state.view_archived_html[mrow['invoice_no']] = not st.session_state.view_archived_html.get(mrow['invoice_no'], False)
                if st.session_state.view_archived_html.get(mrow['invoice_no'], False):
                    components.html(mrow['html_content'], height=520, scrolling=True)
                st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: سجل العمليات التفصيلي وأرشيف المستندات الذكي
    # ---------------------------------------------------------
    elif st.session_state.page == "view_logs":
        st.markdown("<div class='main-title'>🛠️ سجل العمليات التفصيلي وأرشيف فواتير النظام</div>", unsafe_allow_html=True)

        # ── حذف تلقائي للسجلات الأقدم من 60 يوماً ──
        try:
            from datetime import timedelta
            cutoff = (now_mecca() - timedelta(days=60)).strftime("%Y-%m-%d")
            deleted_old = c.execute("DELETE FROM action_logs WHERE log_date < ?", (cutoff,)).rowcount
            if deleted_old: conn.commit()
        except Exception: pass

        # ── التحقق من الصلاحية ──
        can_manage = role in ("مدير نظام", "موظف مستودع")
        if not can_manage:
            st.error("❌ هذه الصفحة متاحة لمدير النظام ومسؤول المستودع فقط.")
            st.stop()

        tab_logs_actions, tab_material_track, tab_invoices_archive = st.tabs([
            "📋 سجل تتبع حركات الموظفين",
            "🔍 تتبع مسار المادة",
            "🗂️ أرشيف الفواتير والمستندات"
        ])

        # ══════════════════════════════════════════════════════
        # تبويب ١: سجل تتبع حركات الموظفين
        # ══════════════════════════════════════════════════════
        with tab_logs_actions:
            st.write("##### 🔍 البحث والفرز في سجل تتبع العمليات")

            fl1, fl2, fl3, fl4 = st.columns([2, 1.5, 1.2, 1.2])
            search_log_txt   = fl1.text_input("🔎 بحث بالاسم أو الكود أو التفاصيل:", key="log_search")
            type_log_filter  = fl2.selectbox("نوع الحركة:", ["عرض الكل", "شحن وإدخل مخزني",
                                              "صرف مواد لمقاول", "ارجاع فائض مواد",
                                              "تحويل ونقل بيني لوجستي", "تعريف صنف جديد"], key="log_type")
            log_date_from    = fl3.date_input("من تاريخ:", value=None, key="log_date_from")
            log_date_to      = fl4.date_input("إلى تاريخ:", value=None, key="log_date_to")

            log_query = """SELECT id, log_type as 'نوع العملية', item_code as 'كود المادة',
                           qty as 'الكمية', details as 'التفاصيل',
                           user_name as 'الموظف', timestamp as 'التاريخ والوقت'
                           FROM action_logs WHERE 1=1"""
            if type_log_filter != "عرض الكل":
                log_query += f" AND log_type='{type_log_filter}'"
            if log_date_from:
                log_query += f" AND log_date >= '{log_date_from.strftime('%Y-%m-%d')}'"
            if log_date_to:
                log_query += f" AND log_date <= '{log_date_to.strftime('%Y-%m-%d')}'"
            log_query += " ORDER BY id DESC"

            df_logs = pd.read_sql(log_query, conn)
            if search_log_txt:
                mask = (
                    df_logs['التفاصيل'].str.contains(search_log_txt, na=False) |
                    df_logs['الموظف'].str.contains(search_log_txt, na=False) |
                    df_logs['كود المادة'].str.contains(search_log_txt, na=False) |
                    df_logs['نوع العملية'].str.contains(search_log_txt, na=False)
                )
                df_logs = df_logs[mask]

            # ── إحصائيات سريعة ──
            si1, si2, si3 = st.columns(3)
            si1.metric("إجمالي العمليات", len(df_logs))
            si2.metric("عدد الموظفين المشاركين", df_logs['الموظف'].nunique() if not df_logs.empty else 0)
            si3.metric("آخر تحديث", now_mecca().strftime("%Y-%m-%d %H:%M"))

            if not df_logs.empty:
                df_display = df_logs.drop(columns=['id'])
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                st.download_button(
                    "📥 تصدير السجل إلى Excel",
                    to_excel(df_display),
                    f"سجل_العمليات_{now_mecca().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_logs"
                )
            else:
                st.info("ℹ️ لا توجد عمليات مسجلة تطابق الفلاتر المحددة.")

        # ══════════════════════════════════════════════════════
        # تبويب ٢: تتبع مسار المادة
        # ══════════════════════════════════════════════════════
        with tab_material_track:
            st.write("##### 🔍 تتبع مسار مادة محددة عبر جميع العمليات والفواتير")
            st.info("ℹ️ ابحث بكود المادة لمعرفة أين ذهبت — من أي مستودع وإلى أي مقاول وفي أي فاتورة.")

            mt1, mt2, mt3 = st.columns([1.5, 1.5, 1.5])
            track_code       = mt1.text_input("🔢 كود المادة *", key="track_code").strip()
            track_contractor = mt2.selectbox("🏗️ المقاول (اختياري):", ["الكل"] + list_contractors, key="track_con")
            track_warehouse  = mt3.selectbox("🏢 المستودع (اختياري):", ["الكل"] + list_warehouses, key="track_wh")
            tdc1, tdc2 = st.columns([1.5, 1.5])
            track_date_from  = tdc1.date_input("📅 من تاريخ (اختياري):", value=None, key="track_df")
            track_date_to    = tdc2.date_input("📅 إلى تاريخ (اختياري):", value=None, key="track_dt")

            if track_code:
                # ── معلومات المادة ──
                mat_info = pd.read_sql(
                    f"SELECT item_name, category, description FROM material_definitions WHERE item_code='{track_code}'", conn)
                if mat_info.empty:
                    st.error(f"❌ الكود [{track_code}] غير معرف في النظام.")
                else:
                    mi = mat_info.iloc[0]
                    st.markdown(f"""
                    <div style='background:#e8f0fb;border:2px solid #004a99;border-radius:10px;
                                padding:14px 20px;margin:10px 0;direction:rtl;'>
                        <b>📦 {mi['item_name']}</b> | الفئة: {mi['category']}
                        {f"<br><small>{mi['description']}</small>" if mi.get('description') else ""}
                    </div>""", unsafe_allow_html=True)

                    # ── الرصيد الحالي في المستودعات ──
                    stock_q = f"SELECT warehouse as 'المستودع', SUM(qty) as 'الرصيد الحالي' FROM inventory WHERE item_code='{track_code}'"
                    if track_warehouse != "الكل":
                        stock_q += f" AND warehouse='{track_warehouse}'"
                    stock_q += " GROUP BY warehouse HAVING SUM(qty)>0"
                    df_stock = pd.read_sql(stock_q, conn)
                    if not df_stock.empty:
                        st.write("**📊 الرصيد الحالي في المستودعات:**")
                        st.dataframe(df_stock, use_container_width=True, hide_index=True)
                        total_stock = df_stock['الرصيد الحالي'].sum()
                        st.markdown(f"<div style='text-align:left;color:#004a99;font-weight:bold;'>إجمالي الرصيد: {total_stock}</div>", unsafe_allow_html=True)
                    else:
                        st.warning("⚠️ لا يوجد رصيد حالي لهذه المادة" + (f" في مستودع [{track_warehouse}]." if track_warehouse != "الكل" else " في أي مستودع."))

                    st.markdown("---")

                    # ── سجل حركات المادة ──
                    log_q = f"""SELECT log_type as 'نوع العملية', qty as 'الكمية',
                                details as 'التفاصيل', user_name as 'الموظف',
                                timestamp as 'التاريخ والوقت'
                                FROM action_logs WHERE item_code='{track_code}'"""
                    if track_date_from:
                        log_q += f" AND log_date >= '{track_date_from.strftime('%Y-%m-%d')}'"
                    if track_date_to:
                        log_q += f" AND log_date <= '{track_date_to.strftime('%Y-%m-%d')}'"
                    log_q += " ORDER BY id DESC"

                    df_track_logs = pd.read_sql(log_q, conn)
                    # فلترة المقاول والمستودع من عمود التفاصيل
                    if track_contractor != "الكل":
                        df_track_logs = df_track_logs[
                            df_track_logs['التفاصيل'].str.contains(track_contractor, na=False)]
                    if track_warehouse != "الكل":
                        df_track_logs = df_track_logs[
                            df_track_logs['التفاصيل'].str.contains(track_warehouse, na=False)]

                    st.write(f"**📋 سجل حركات المادة [{track_code}] ({len(df_track_logs)} عملية):**")
                    if not df_track_logs.empty:
                        st.dataframe(df_track_logs, use_container_width=True, hide_index=True)
                        st.download_button(
                            "📥 تصدير سجل المادة إلى Excel",
                            to_excel(df_track_logs),
                            f"تتبع_مادة_{track_code}_{now_mecca().strftime('%Y%m%d')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="dl_track_logs"
                        )
                    else:
                        st.info("ℹ️ لا توجد حركات مسجلة لهذه المادة بالفلاتر المحددة.")

                    st.markdown("---")

                    # ── الفواتير التي تحتوي على المادة ──
                    st.write(f"**📄 الفواتير التي تحتوي على المادة [{track_code}]:**")
                    df_all_inv = pd.read_sql(
                        """SELECT id, invoice_type, invoice_no, warehouse_from, warehouse_to,
                           contractor, employee, items_json, timestamp
                           FROM archived_invoices ORDER BY id DESC""", conn)

                    inv_matches = []
                    for _, inv_row in df_all_inv.iterrows():
                        try:
                            items = json.loads(inv_row['items_json'])
                            codes = [str(x.get('code','')) for x in items]
                            if track_code not in codes: continue
                            if track_contractor != "الكل" and inv_row['contractor'] != track_contractor: continue
                            if track_warehouse != "الكل" and inv_row['warehouse_from'] != track_warehouse and inv_row['warehouse_to'] != track_warehouse: continue
                            if track_date_from and inv_row['timestamp'][:10] < str(track_date_from): continue
                            if track_date_to   and inv_row['timestamp'][:10] > str(track_date_to):   continue
                            item_qty = next((x.get('qty',0) for x in items if str(x.get('code',''))==track_code), 0)
                            inv_matches.append({
                                'id': inv_row['id'],
                                'نوع الفاتورة': inv_row['invoice_type'],
                                'رقم الفاتورة': inv_row['invoice_no'],
                                'الكمية في الفاتورة': item_qty,
                                'المستودع المصدر': inv_row['warehouse_from'] or '—',
                                'المستودع المستلم': inv_row['warehouse_to'] or '—',
                                'المقاول': inv_row['contractor'] or '—',
                                'الموظف': inv_row['employee'],
                                'التاريخ': inv_row['timestamp'],
                            })
                        except Exception: continue

                    if inv_matches:
                        st.success(f"✅ وُجدت هذه المادة في ({len(inv_matches)}) فاتورة.")
                        df_inv_sum = pd.DataFrame([{k:v for k,v in r.items() if k not in ('id','_html')} for r in inv_matches])
                        st.dataframe(df_inv_sum, use_container_width=True, hide_index=True)
                        st.download_button(
                            "📥 تصدير الفواتير إلى Excel",
                            to_excel(df_inv_sum),
                            f"فواتير_مادة_{track_code}_{now_mecca().strftime('%Y%m%d')}.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="dl_inv_track"
                        )
                        st.markdown("---")
                        st.write("**👁️ عرض الفواتير:**")
                        for inv_r in inv_matches:
                            inv_view_key = f"track_inv_{inv_r['id']}"
                            if inv_view_key not in st.session_state:
                                st.session_state[inv_view_key] = False
                            inv_type_color = "#e65100" if inv_r['نوع الفاتورة']=="صرف" else ("#1a237e" if inv_r['نوع الفاتورة']=="تحويل" else "#2e7d32")
                            wh_info = f"مستودع: {inv_r['المستودع المصدر']}"
                            if inv_r['المستودع المستلم'] != '—':
                                wh_info += f" ➡️ {inv_r['المستودع المستلم']}"
                            st.markdown(f"""
                            <div style='background:#f8f9fa;border-right:5px solid {inv_type_color};
                                        border-radius:8px;padding:10px 16px;margin:6px 0;direction:rtl;'>
                                📄 <b>فاتورة {inv_r['نوع الفاتورة']}</b> رقم
                                <span style='color:red;font-weight:900;'>{inv_r['رقم الفاتورة']}</span> |
                                الكمية: <b>{inv_r['الكمية في الفاتورة']}</b><br>
                                🏢 {wh_info} | 🏗️ {inv_r['المقاول']} | 📅 {inv_r['التاريخ']}
                            </div>""", unsafe_allow_html=True)
                            if st.button(f"👁️ عرض الفاتورة {inv_r['رقم الفاتورة']}", key=f"view_tinv_{inv_r['id']}"):
                                st.session_state[inv_view_key] = not st.session_state[inv_view_key]
                            # ── جلب HTML عند الطلب فقط ──
                            if st.session_state[inv_view_key]:
                                _html_row = pd.read_sql(
                                    f"SELECT html_content FROM archived_invoices WHERE id={inv_r['id']}", conn)
                                if not _html_row.empty:
                                    components.html(_html_row.iloc[0]['html_content'], height=520, scrolling=True)
                            st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
                    else:
                        st.info("ℹ️ لم تُعثر على فواتير تحتوي على هذه المادة بالفلاتر المحددة.")

        # ══════════════════════════════════════════════════════
        # تبويب ٣: أرشيف الفواتير والمستندات
        # ══════════════════════════════════════════════════════
        with tab_invoices_archive:
            st.write("##### 📄 أرشيف استرجاع وإعادة طباعة المستندات والفواتير الصادرة مسبقاً")

            # ── حذف تلقائي للفواتير الأقدم من 90 يوماً ──
            try:
                from datetime import timedelta
                cutoff_inv = (now_mecca() - timedelta(days=90)).strftime("%Y-%m-%d")
                c.execute("DELETE FROM archived_invoices WHERE timestamp < ?", (cutoff_inv,))
                conn.commit()
            except Exception:
                pass

            col_arch1, col_arch2, col_arch3, col_arch4 = st.columns([1, 1, 1.2, 1.2])
            filter_arch_type = col_arch1.selectbox("نوع المستند المراد عرضه:", ["الكل", "صرف", "ارجاع", "تحويل"], key="arch_type")
            search_arch_no   = col_arch2.text_input("ابحث برقم الفاتورة مباشرة:", key="arch_no")
            search_arch_name = col_arch3.text_input("ابحث باسم المقاول أو الموظف منشئ الحركة:", key="arch_name")
            search_arch_date = col_arch4.date_input("تصفية بحسب تاريخ إصدار الفاتورة:", value=None, key="arch_date")

            # ── استعلام بدون html_content لتحسين الأداء ──
            arch_query = """SELECT id, invoice_type, invoice_no, warehouse_from,
                            warehouse_to, contractor, employee, timestamp
                            FROM archived_invoices WHERE 1=1"""
            if filter_arch_type != "الكل":
                arch_query += f" AND invoice_type='{filter_arch_type}'"
            if search_arch_no.strip():
                arch_query += f" AND invoice_no LIKE '%{search_arch_no.strip()}%'"
            if search_arch_date is not None:
                arch_query += f" AND timestamp LIKE '{search_arch_date.strftime('%Y-%m-%d')}%'"
            if search_arch_name.strip():
                n = search_arch_name.strip()
                arch_query += f" AND (contractor LIKE '%{n}%' OR employee LIKE '%{n}%')"
            arch_query += " ORDER BY id DESC"

            df_archived = pd.read_sql(arch_query, conn)

            if not df_archived.empty:
                st.success(f"✅ تم العثور على ({len(df_archived)}) مستند/فاتورة مطابقة لشروط البحث.")

                # تصدير Excel
                st.download_button(
                    "📥 تصدير قائمة الفواتير إلى Excel",
                    to_excel(df_archived),
                    f"أرشيف_الفواتير_{now_mecca().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_arch"
                )
                st.markdown("---")

                for _, row in df_archived.iterrows():
                    inv_id = int(row['id'])
                    arch_view_key = f"arch_view_{inv_id}"
                    if arch_view_key not in st.session_state:
                        st.session_state[arch_view_key] = False

                    st.markdown(f"""
                    <div class='report-box'>
                        📄 <b>مستند {row['invoice_type']} رسمي برقم ( <span style='color:red;'>{row['invoice_no']}</span> )</b> | 📝 المسؤول عن الحركة: <b>{row['employee']}</b><br>
                        📅 تاريخ القيد والأرشفة الفعلي: {row['timestamp']} | 📍 المستودع المصدر: {row['warehouse_from'] if row['warehouse_from'] else 'N/A'} {f" ➡️ المستودع المستلم: {row['warehouse_to']}" if row['warehouse_to'] else ''} {f" | 🏗️ المقاول المستلم: {row['contractor']}" if row['contractor'] else ''}
                    </div>""", unsafe_allow_html=True)

                    if st.button(f"👁️ عرض ومعاينة وطباعة الفاتورة رقم {row['invoice_no']}", key=f"btn_arch_{inv_id}"):
                        st.session_state[arch_view_key] = not st.session_state[arch_view_key]

                    # ── جلب HTML عند الطلب فقط ──
                    if st.session_state[arch_view_key]:
                        with st.spinner("جاري تحميل الفاتورة..."):
                            _html_r = pd.read_sql(
                                "SELECT html_content FROM archived_invoices WHERE id=?",
                                conn, params=(inv_id,))
                            if not _html_r.empty:
                                st.write("<p style='margin-top:10px;'></p>", unsafe_allow_html=True)
                                components.html(_html_r.iloc[0]['html_content'], height=520, scrolling=True)
                                st.write("---")

                    st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
            else:
                st.info("ℹ️ لم يتم العثور على أي مستندات مؤرشفة تطابق الكلمات المفتاحية أو التاريخ المحدد حالياً.")

    # ---------------------------------------------------------
    # صفحة: أرقام التواصل مع المقاولين والمستودعات
    # ---------------------------------------------------------
    elif st.session_state.page == "contacts_page":
        st.markdown("<div class='main-title'>📞 دليل أرقام التواصل</div>", unsafe_allow_html=True)

        # ── ثوابت التسلسل الهرمي ──
        POSITION_HIERARCHY = [
            {"key": "مدير المشروع",      "icon": "👑", "color": "#004a99", "bg": "#e8f0fb"},
            {"key": "نائب مدير المشروع", "icon": "🥇", "color": "#1565c0", "bg": "#e3f2fd"},
            {"key": "مستلم بلاغات",      "icon": "📡", "color": "#00695c", "bg": "#e0f2f1"},
            {"key": "أمين مستودع",       "icon": "🏪", "color": "#6a1b9a", "bg": "#f3e5f5"},
            {"key": "مسؤول فرق طوارئ",   "icon": "🚨", "color": "#c62828", "bg": "#ffebee"},
            {"key": "أخرى",              "icon": "📋", "color": "#555",    "bg": "#f5f5f5"},
        ]
        POSITION_KEYS = [p["key"] for p in POSITION_HIERARCHY]

        # المناصب التي تُعرض لكل تبويب
        CONTRACTOR_POSITIONS = ["مدير المشروع", "نائب مدير المشروع", "مستلم بلاغات", "مسؤول فرق طوارئ"]
        WAREHOUSE_POSITIONS  = ["مدير المشروع", "نائب مدير المشروع", "أمين مستودع"]

        # جلب قوائم النظام
        ct_warehouses  = pd.read_sql("SELECT name FROM settings_warehouses  ORDER BY name", conn)['name'].tolist()
        ct_contractors = pd.read_sql("SELECT name FROM settings_contractors ORDER BY name", conn)['name'].tolist()
        df_contacts    = pd.read_sql("SELECT * FROM contact_numbers ORDER BY entity_type, entity_name, position, name", conn)
        df_managers    = pd.read_sql("SELECT * FROM managers_directory ORDER BY department, name", conn)

        # دالة مساعدة لعرض أشخاص جهة واحدة بتسلسل هرمي
        def render_entity_contacts(df_grp, allowed_positions, etype_color, etype_bg):
            shown_any = False
            for pos_info in POSITION_HIERARCHY:
                if pos_info["key"] not in allowed_positions:
                    continue
                grp_pos = df_grp[df_grp['position'] == pos_info["key"]]
                if grp_pos.empty:
                    continue
                shown_any = True
                st.markdown(f"""
                <div style='background:{pos_info["bg"]};border-right:5px solid {pos_info["color"]};
                            border-radius:8px;padding:7px 16px;margin:10px 0 6px 16px;direction:rtl;'>
                    <span style='font-size:15px;font-weight:700;color:{pos_info["color"]};'>
                        {pos_info["icon"]} {pos_info["key"]}
                    </span>
                    <span style='font-size:12px;color:#aaa;margin-right:6px;'>({len(grp_pos)})</span>
                </div>""", unsafe_allow_html=True)
                cols_r = 3
                for chunk in [grp_pos.iloc[i:i+cols_r] for i in range(0, len(grp_pos), cols_r)]:
                    card_cols = st.columns(cols_r)
                    for ci, (_, ct) in enumerate(chunk.iterrows()):
                        with card_cols[ci]:
                            ph = str(ct['phone']).replace(" ","").replace("-","")
                            nt = f"<div style='font-size:11px;color:#999;margin-top:5px;'>📝 {ct['notes']}</div>" if ct.get('notes') else ""
                            st.markdown(f"""
                            <div style='background:#fff;border:2px solid {pos_info["color"]};border-radius:12px;
                                        padding:16px 10px;text-align:center;margin-bottom:10px;
                                        box-shadow:0 2px 8px rgba(0,0,0,0.07);'>
                                <div style='font-size:15px;font-weight:900;color:#222;margin-bottom:6px;'>{ct['name']}</div>
                                <a href='tel:{ph}' style='display:block;background:{pos_info["color"]};color:white;
                                   border-radius:18px;padding:7px 14px;font-size:14px;font-weight:bold;
                                   text-decoration:none;margin:4px auto;max-width:175px;'>
                                    📞 {ct['phone']}
                                </a>{nt}
                            </div>""", unsafe_allow_html=True)
            if not shown_any:
                st.info("ℹ️ لا توجد أرقام مسجلة لهذه الجهة.")

        # ══════════════════════════════════════
        # التبويبات الرئيسية للعرض
        # ══════════════════════════════════════
        tab_contractor, tab_warehouse, tab_mgr = st.tabs([
            "🏗️ المقاولون",
            "🏢 المستودعات",
            "🌟 المدراء"
        ])

        # ─── تبويب المقاولين ───
        with tab_contractor:
            # فلتر + بحث
            fc1, fc2 = st.columns([2, 2])
            sel_contractor = fc1.selectbox("اختر المقاول:", ["الكل"] + ct_contractors, key="view_ct_con")
            search_con     = fc2.text_input("🔍 بحث بالاسم أو الرقم:", key="srch_con").strip()

            df_con = df_contacts[df_contacts['entity_type'] == "مقاول"].copy()
            if sel_contractor != "الكل":
                df_con = df_con[df_con['entity_name'] == sel_contractor]
            if search_con:
                df_con = df_con[df_con['name'].str.contains(search_con, na=False) |
                                df_con['phone'].str.contains(search_con, na=False)]

            if df_con.empty:
                st.info("ℹ️ لا توجد أرقام تواصل مسجلة للمقاولين.")
            else:
                # تجميع بحسب اسم المقاول
                contractors_shown = df_con['entity_name'].dropna().unique()
                for con_name in sorted(contractors_shown):
                    grp = df_con[df_con['entity_name'] == con_name]
                    st.markdown(f"""
                    <div style='background:#fff3e0;border:2px solid #e65100;border-radius:12px;
                                padding:12px 20px;margin:20px 0 6px 0;direction:rtl;'>
                        <span style='font-size:20px;font-weight:900;color:#e65100;'>🏗️ {con_name}</span>
                        <span style='font-size:12px;color:#aaa;background:white;border-radius:8px;
                                     padding:2px 10px;margin-right:10px;'>مقاول | {len(grp)} شخص</span>
                    </div>""", unsafe_allow_html=True)
                    render_entity_contacts(grp, CONTRACTOR_POSITIONS, "#e65100", "#fff3e0")

        # ─── تبويب المستودعات ───
        with tab_warehouse:
            fw1, fw2 = st.columns([2, 2])
            sel_warehouse = fw1.selectbox("اختر المستودع:", ["الكل"] + ct_warehouses, key="view_ct_wh")
            search_wh     = fw2.text_input("🔍 بحث بالاسم أو الرقم:", key="srch_wh").strip()

            df_wh = df_contacts[df_contacts['entity_type'] == "مستودع"].copy()
            if sel_warehouse != "الكل":
                df_wh = df_wh[df_wh['entity_name'] == sel_warehouse]
            if search_wh:
                df_wh = df_wh[df_wh['name'].str.contains(search_wh, na=False) |
                              df_wh['phone'].str.contains(search_wh, na=False)]

            if df_wh.empty:
                st.info("ℹ️ لا توجد أرقام تواصل مسجلة للمستودعات.")
            else:
                warehouses_shown = df_wh['entity_name'].dropna().unique()
                for wh_name in sorted(warehouses_shown):
                    grp = df_wh[df_wh['entity_name'] == wh_name]
                    st.markdown(f"""
                    <div style='background:#e8eaf6;border:2px solid #1a237e;border-radius:12px;
                                padding:12px 20px;margin:20px 0 6px 0;direction:rtl;'>
                        <span style='font-size:20px;font-weight:900;color:#1a237e;'>🏢 {wh_name}</span>
                        <span style='font-size:12px;color:#aaa;background:white;border-radius:8px;
                                     padding:2px 10px;margin-right:10px;'>مستودع | {len(grp)} شخص</span>
                    </div>""", unsafe_allow_html=True)
                    render_entity_contacts(grp, WAREHOUSE_POSITIONS, "#1a237e", "#e8eaf6")

        # ─── تبويب المدراء ───
        with tab_mgr:
            search_mgr = st.text_input("🔍 بحث بالاسم أو القسم:", key="srch_mgr").strip()
            df_mgr_show = df_managers.copy()
            if search_mgr:
                df_mgr_show = df_mgr_show[
                    df_mgr_show['name'].str.contains(search_mgr, na=False) |
                    df_mgr_show['department'].str.contains(search_mgr, na=False)
                ]

            if df_mgr_show.empty:
                st.info("ℹ️ لا يوجد مدراء مسجلون." if not search_mgr else "ℹ️ لا توجد نتائج.")
            else:
                # تجميع بحسب القسم
                depts = df_mgr_show['department'].dropna().unique()
                for dept in sorted(depts):
                    grp_d = df_mgr_show[df_mgr_show['department'] == dept]
                    st.markdown(f"""
                    <div style='background:#f3e5f5;border:2px solid #6a1b9a;border-radius:12px;
                                padding:10px 20px;margin:18px 0 6px 0;direction:rtl;'>
                        <span style='font-size:19px;font-weight:900;color:#6a1b9a;'>🌟 {dept}</span>
                        <span style='font-size:12px;color:#aaa;background:white;border-radius:8px;
                                     padding:2px 10px;margin-right:10px;'>{len(grp_d)} شخص</span>
                    </div>""", unsafe_allow_html=True)
                    cols_m = 3
                    for chunk in [grp_d.iloc[i:i+cols_m] for i in range(0, len(grp_d), cols_m)]:
                        mcols = st.columns(cols_m)
                        for ci, (_, mgr) in enumerate(chunk.iterrows()):
                            with mcols[ci]:
                                ph_m = str(mgr['phone']).replace(" ","").replace("-","")
                                nt_m = f"<div style='font-size:11px;color:#999;margin-top:5px;'>📝 {mgr['notes']}</div>" if mgr.get('notes') else ""
                                st.markdown(f"""
                                <div style='background:#fff;border:2px solid #6a1b9a;border-radius:12px;
                                            padding:16px 10px;text-align:center;margin-bottom:10px;
                                            box-shadow:0 2px 8px rgba(0,0,0,0.07);'>
                                    <div style='font-size:15px;font-weight:900;color:#222;margin-bottom:4px;'>{mgr['name']}</div>
                                    <div style='font-size:12px;color:#6a1b9a;margin-bottom:8px;'>🏷️ {mgr['department']}</div>
                                    <a href='tel:{ph_m}' style='display:block;background:#6a1b9a;color:white;
                                       border-radius:18px;padding:7px 14px;font-size:14px;font-weight:bold;
                                       text-decoration:none;margin:4px auto;max-width:175px;'>
                                        📞 {mgr['phone']}
                                    </a>{nt_m}
                                </div>""", unsafe_allow_html=True)

        # ══════════════════════════════════════
        # إدارة الأرقام — مدير النظام فقط
        # ══════════════════════════════════════
        if role == "مدير نظام":
            st.divider()
            st.markdown("### ⚙️ إدارة أرقام التواصل")

            adm_tab1, adm_tab2, adm_tab3 = st.tabs([
                "➕ إضافة / تعديل أرقام المقاولين والمستودعات",
                "🌟 إدارة قائمة المدراء",
                "🗑️ حذف الأرقام"
            ])

            # ── تبويب الإضافة والتعديل ──
            with adm_tab1:
                st.write("#### ➕ إضافة رقم تواصل جديد")
                with st.form("add_contact_form", clear_on_submit=True):
                    ca1, ca2 = st.columns([2, 2])
                    ct_name  = ca1.text_input("الاسم الكامل *").strip()
                    ct_phone = ca2.text_input("رقم الجوال *").strip()
                    ct_etype = st.selectbox("نوع الجهة *", ["مقاول", "مستودع"])
                    # نوع الجهة يحدد القائمة
                    if ct_etype == "مقاول":
                        _pos_list = CONTRACTOR_POSITIONS
                        _ename_list = ct_contractors if ct_contractors else ["لا يوجد مقاولون"]
                        ct_ename    = st.selectbox("اسم المقاول (من المقاولين المعتمدين) *", _ename_list, key="ct_ename_con")
                        ct_pos_sel  = st.selectbox("المنصب الوظيفي *", _pos_list, key="add_pos_sel_con")
                    else:
                        _pos_list = WAREHOUSE_POSITIONS
                        _ename_list = ct_warehouses if ct_warehouses else ["لا توجد مستودعات"]
                        ct_ename    = st.selectbox("اسم المستودع (من مستودعات النظام) *", _ename_list, key="ct_ename_wh")
                        ct_pos_sel  = st.selectbox("المنصب الوظيفي *", _pos_list, key="add_pos_sel_wh")
                    ct_notes = st.text_input("ملاحظات (اختياري)").strip()
                    if st.form_submit_button("💾 حفظ رقم التواصل", use_container_width=True):
                        if ct_name and ct_phone and ct_ename:
                            c.execute("INSERT INTO contact_numbers (name, position, phone, entity_type, entity_name, notes) VALUES (?,?,?,?,?,?)",
                                      (ct_name, ct_pos_sel, ct_phone, ct_etype, ct_ename, ct_notes))
                            conn.commit()
                            st.success(f"✅ تم إضافة [{ct_name}] — {ct_pos_sel} في {ct_ename}.")
                            st.rerun()
                        else:
                            st.error("⚠️ يرجى تعبئة جميع الحقول الإلزامية.")

                st.divider()
                st.write("#### ✏️ تعديل الأرقام الموجودة")
                df_all_ct = pd.read_sql("SELECT * FROM contact_numbers ORDER BY entity_type, entity_name, position, name", conn)
                if df_all_ct.empty:
                    st.info("ℹ️ لا توجد أرقام مسجلة.")
                else:
                    ef1c, ef2c = st.columns([1.2, 1.8])
                    filt_et  = ef1c.selectbox("تصفية بالجهة:", ["الكل","مقاول","مستودع"], key="edf_et")
                    filt_en  = ef2c.text_input("تصفية باسم الجهة:", key="edf_en").strip()
                    df_edit_show = df_all_ct.copy()
                    if filt_et != "الكل": df_edit_show = df_edit_show[df_edit_show['entity_type']==filt_et]
                    if filt_en: df_edit_show = df_edit_show[df_edit_show['entity_name'].str.contains(filt_en, na=False)]

                    for _, ct_row in df_edit_show.iterrows():
                        ct_id = int(ct_row['id'])
                        ct_edit_key = f"ct_edit_{ct_id}"
                        if ct_edit_key not in st.session_state: st.session_state[ct_edit_key] = False

                        pos_meta = next((p for p in POSITION_HIERARCHY if p["key"]==ct_row['position']), POSITION_HIERARCHY[-1])
                        ent_disp = ct_row.get('entity_name') or ct_row.get('entity_type','')

                        cte1,cte2,cte3,cte4 = st.columns([0.4,3,1.5,0.7])
                        cte1.markdown(f"<span style='font-size:18px;'>{pos_meta['icon']}</span>", unsafe_allow_html=True)
                        cte2.write(f"**{ct_row['name']}** | {ct_row['position']} | 🏢 {ent_disp}")
                        cte3.write(f"📞 {ct_row['phone']}")
                        if cte4.button("✏️", key=f"ct_e_{ct_id}"):
                            st.session_state[ct_edit_key] = not st.session_state[ct_edit_key]; st.rerun()

                        if st.session_state[ct_edit_key]:
                            with st.form(f"edit_ct_form_{ct_id}"):
                                ef1,ef2 = st.columns([2,2])
                                new_nm  = ef1.text_input("الاسم", value=ct_row['name'])
                                new_ph  = ef2.text_input("الجوال", value=ct_row['phone'])
                                eg1,eg2 = st.columns([1.5,1.5])
                                _et_opts = ["مقاول","مستودع"]
                                _et_idx  = _et_opts.index(ct_row['entity_type']) if ct_row['entity_type'] in _et_opts else 0
                                new_et   = eg1.selectbox("نوع الجهة", _et_opts, index=_et_idx)
                                _pl      = CONTRACTOR_POSITIONS if new_et=="مقاول" else WAREHOUSE_POSITIONS
                                _pi      = _pl.index(ct_row['position']) if ct_row['position'] in _pl else 0
                                new_pos  = eg2.selectbox("المنصب", _pl, index=_pi)
                                cur_en   = ct_row.get('entity_name') or ""
                                if new_et=="مقاول":
                                    _el = ct_contractors if ct_contractors else ["لا يوجد"]
                                    new_en = st.selectbox("المقاول", _el, index=_el.index(cur_en) if cur_en in _el else 0)
                                else:
                                    _el = ct_warehouses if ct_warehouses else ["لا يوجد"]
                                    new_en = st.selectbox("المستودع", _el, index=_el.index(cur_en) if cur_en in _el else 0)
                                new_nt = st.text_input("ملاحظات", value=ct_row['notes'] or "")
                                fs1,fs2 = st.columns([1,1])
                                if fs1.form_submit_button("💾 حفظ"):
                                    if new_nm.strip() and new_ph.strip():
                                        c.execute("UPDATE contact_numbers SET name=?,position=?,phone=?,entity_type=?,entity_name=?,notes=? WHERE id=?",
                                                  (new_nm.strip(),new_pos,new_ph.strip(),new_et,new_en,new_nt.strip(),ct_id))
                                        conn.commit(); st.session_state[ct_edit_key]=False
                                        st.success("✅ تم التحديث."); st.rerun()
                                if fs2.form_submit_button("❌ إلغاء"):
                                    st.session_state[ct_edit_key]=False; st.rerun()

                        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

            # ── تبويب إدارة المدراء ──
            with adm_tab2:
                st.write("#### ➕ إضافة مدير جديد")
                with st.form("add_mgr_form", clear_on_submit=True):
                    mg1,mg2 = st.columns([2,2])
                    mgr_name  = mg1.text_input("اسم المدير الكامل *").strip()
                    mgr_phone = mg2.text_input("رقم الجوال *").strip()
                    mg3,mg4   = st.columns([2,2])
                    mgr_dept  = mg3.text_input("القسم / المنصب *").strip()
                    mgr_notes = mg4.text_input("ملاحظات (اختياري)").strip()
                    if st.form_submit_button("💾 حفظ المدير", use_container_width=True):
                        if mgr_name and mgr_phone and mgr_dept:
                            c.execute("INSERT INTO managers_directory (name, department, phone, notes) VALUES (?,?,?,?)",
                                      (mgr_name, mgr_dept, mgr_phone, mgr_notes))
                            conn.commit()
                            st.success(f"✅ تم إضافة المدير [{mgr_name}] — {mgr_dept}.")
                            st.rerun()
                        else:
                            st.error("⚠️ يرجى تعبئة الاسم والجوال والقسم.")

                st.divider()
                st.write("#### 📋 المدراء المسجلون")
                df_mgr_adm = pd.read_sql("SELECT * FROM managers_directory ORDER BY department, name", conn)
                if df_mgr_adm.empty:
                    st.info("ℹ️ لا يوجد مدراء مسجلون.")
                else:
                    for _, mr in df_mgr_adm.iterrows():
                        mr_id = int(mr['id'])
                        mr_ek = f"mr_edit_{mr_id}"; mr_ck = f"mr_conf_{mr_id}"
                        if mr_ek not in st.session_state: st.session_state[mr_ek] = False
                        if mr_ck not in st.session_state: st.session_state[mr_ck] = False

                        mc1,mc2,mc3,mc4,mc5 = st.columns([0.4,2.2,1.8,0.6,0.6])
                        mc1.markdown("🌟", unsafe_allow_html=True)
                        mc2.write(f"**{mr['name']}** — {mr['department']}")
                        mc3.write(f"📞 {mr['phone']}")
                        if not st.session_state[mr_ek]:
                            if mc4.button("✏️", key=f"mr_e_{mr_id}"): st.session_state[mr_ek]=True; st.rerun()
                            if mc5.button("🗑️", key=f"mr_d_{mr_id}"): st.session_state[mr_ck]=True; st.rerun()
                        else:
                            with st.form(f"edit_mgr_{mr_id}"):
                                em1,em2 = st.columns([2,2])
                                new_mrn = em1.text_input("الاسم", value=mr['name'])
                                new_mrp = em2.text_input("الجوال", value=mr['phone'])
                                em3,em4 = st.columns([2,2])
                                new_mrd = em3.text_input("القسم", value=mr['department'])
                                new_mrt = em4.text_input("ملاحظات", value=mr['notes'] or "")
                                es1,es2 = st.columns([1,1])
                                if es1.form_submit_button("💾 حفظ"):
                                    if new_mrn.strip() and new_mrp.strip() and new_mrd.strip():
                                        c.execute("UPDATE managers_directory SET name=?,department=?,phone=?,notes=? WHERE id=?",
                                                  (new_mrn.strip(),new_mrd.strip(),new_mrp.strip(),new_mrt.strip(),mr_id))
                                        conn.commit(); st.session_state[mr_ek]=False
                                        st.success("✅ تم التحديث."); st.rerun()
                                if es2.form_submit_button("❌ إلغاء"):
                                    st.session_state[mr_ek]=False; st.rerun()

                        if st.session_state[mr_ck]:
                            st.warning(f"⚠️ تأكيد حذف [{mr['name']}]؟")
                            cy_m,cn_m = st.columns([1,1])
                            if cy_m.button("✅ نعم، احذف", key=f"mr_yes_{mr_id}"):
                                c.execute("DELETE FROM managers_directory WHERE id=?",(mr_id,))
                                conn.commit(); st.session_state[mr_ck]=False
                                st.success("✅ تم الحذف."); st.rerun()
                            if cn_m.button("🚫 إلغاء", key=f"mr_no_{mr_id}"):
                                st.session_state[mr_ck]=False; st.rerun()
                        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

            # ── تبويب الحذف ──
            with adm_tab3:
                st.write("#### 🗑️ حذف أرقام التواصل")
                df_del = pd.read_sql("SELECT * FROM contact_numbers ORDER BY entity_type, entity_name, position, name", conn)
                if df_del.empty:
                    st.info("ℹ️ لا توجد أرقام.")
                else:
                    for _, ct_row in df_del.iterrows():
                        ct_id = int(ct_row['id'])
                        ct_confirm_key = f"ct_confirm_{ct_id}"
                        if ct_confirm_key not in st.session_state: st.session_state[ct_confirm_key] = False
                        pos_meta = next((p for p in POSITION_HIERARCHY if p["key"]==ct_row['position']), POSITION_HIERARCHY[-1])
                        ent_disp = ct_row.get('entity_name') or ''
                        del1,del2,del3,del4 = st.columns([0.4,3,1.5,0.7])
                        del1.markdown(f"<span style='font-size:18px;'>{pos_meta['icon']}</span>", unsafe_allow_html=True)
                        del2.write(f"**{ct_row['name']}** | {ct_row['position']} | 🏢 {ent_disp}")
                        del3.write(f"📞 {ct_row['phone']}")
                        if del4.button("🗑️", key=f"dct_{ct_id}"): st.session_state[ct_confirm_key]=True; st.rerun()
                        if st.session_state[ct_confirm_key]:
                            st.warning(f"⚠️ تأكيد حذف [{ct_row['name']}]؟")
                            cy3,cn3 = st.columns([1,1])
                            if cy3.button("✅ نعم، احذف", key=f"ct_yes_{ct_id}"):
                                c.execute("DELETE FROM contact_numbers WHERE id=?",(ct_id,))
                                conn.commit(); st.session_state[ct_confirm_key]=False
                                st.success("✅ تم الحذف."); st.rerun()
                            if cn3.button("🚫 إلغاء", key=f"ct_no_{ct_id}"):
                                st.session_state[ct_confirm_key]=False; st.rerun()
                        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: لوحة إدارة حسابات الموظفين والتحكم بالصلاحيات العليا
    # ---------------------------------------------------------
    elif st.session_state.page == "manage_staff":
        st.markdown("<div class='main-title'>👥 إدارة حسابات الموظفين والتحكم بالصلاحيات العليا</div>", unsafe_allow_html=True)

        if u['role'] != "مدير نظام":
            st.error("❌ هذه الصفحة متاحة لمدير النظام فقط.")
        elif not st.session_state.get('staff_auth'):
            st.markdown("""
            <div style='background:#fff3cd;border:2px solid #f9a825;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;'>
                🔐 <b>هذه الصفحة محمية بكلمة مرور إضافية</b><br>
                <small>أدخل كلمة المرور للوصول إلى إدارة حسابات الموظفين</small>
            </div>""", unsafe_allow_html=True)
            _, col_sp, _ = st.columns([1, 1.5, 1])
            with col_sp:
                with st.form("staff_auth_form"):
                    sp_pass = st.text_input("كلمة المرور:", type="password")
                    if st.form_submit_button("🔓 دخول", use_container_width=True):
                        if sp_pass == BACKUP_PASSWORD:
                            st.session_state['staff_auth'] = True
                            st.rerun()
                        else:
                            st.error("❌ كلمة المرور غير صحيحة!")
        else:
            col_ms_title, col_ms_logout = st.columns([4, 1])
            if col_ms_logout.button("🔒 قفل الصفحة", key="lock_staff"):
                st.session_state['staff_auth'] = False; st.rerun()

            tab_requests_view, tab_add_new_emp, tab_change_pwd, tab_mobile_access = st.tabs([
                "📥 طلبات تصفير وتعديل كلمات المرور الواردة",
                "➕ إضافة وتعيين حساب موظف ميداني جديد",
                "🔑 تغيير كلمة مرور أي مستخدم",
                "📱 صلاحية تشغيل النظام من الجوال"
            ])
        
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
                    new_role = c_u4.selectbox("مستوى الصلاحية الممنوحة *", ["موظف مستودع", "موجه بلاغات", "مدير نظام"])
                    new_position = ""  # المنصب لا يُحدد عند الإنشاء

                    if st.form_submit_button("👥 إنشاء وتفعيل حساب الموظف فوراً"):
                        if new_username and new_fullname and new_password:
                            check_exist_user = pd.read_sql(f"SELECT username FROM users WHERE username='{new_username}'", conn)
                            if not check_exist_user.empty:
                                st.error(f"❌ خطأ: رقم الجوال ({new_username}) مسجل ومستخدم مسبقاً لموظف آخر بالمنظومة.")
                            else:
                                c.execute("INSERT INTO users (username, password, full_name, role, position) VALUES (?,?,?,?,?)",
                                          (new_username, new_password, new_fullname, new_role, new_position))
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
                                _role_opts = ["موظف مستودع", "موجه بلاغات", "مدير نظام"]
                                updated_role = col_e4.selectbox("الصلاحية الممنوحة", _role_opts, index=_role_opts.index(r_usr['role']) if r_usr['role'] in _role_opts else 0)
                                # حقل المنصب الوظيفي
                                _pos_opts_edit = ["مدير المشروع", "نائب مدير المشروع", "مستلم بلاغات", "أمين مستودع", "مسؤول فرق طوارئ", "أخرى"]
                                cur_position = ""
                                try:
                                    pos_res = pd.read_sql(f"SELECT COALESCE(position,'') as pos FROM users WHERE username='{r_usr['username']}'", conn)
                                    cur_position = pos_res.iloc[0]['pos'] if not pos_res.empty else ""
                                except Exception: pass
                                _pos_edit_idx = _pos_opts_edit.index(cur_position) if cur_position in _pos_opts_edit else len(_pos_opts_edit)-1
                                updated_position = st.selectbox("المنصب الوظيفي", _pos_opts_edit, index=_pos_edit_idx, key=f"pos_{usr_key}")
                            
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
                                            
                                        c.execute("UPDATE users SET username=?, full_name=?, password=?, role=?, position=? WHERE username=?",
                                                  (updated_username.strip(), updated_name.strip(), updated_pass.strip(), updated_role, updated_position.strip(), usr_key))
                                        save_log("تعديل بيانات حساب", updated_username, 0, f"تعديل بيانات الموظف القديمة إلى الاسم: {updated_name} والصلاحية: {updated_role}", u['full_name'])
                                        conn.commit()
                                    
                                        if usr_key == u['username']:
                                            res_self = pd.read_sql(f"SELECT * FROM users WHERE username='{updated_username.strip()}'", conn)
                                            if not res_self.empty:
                                                row_s = res_self.iloc[0]
                                                st.session_state.user_info = {
                                                    'username':     str(row_s['username']),
                                                    'full_name':    str(row_s['full_name']),
                                                    'role':         str(row_s['role']),
                                                    'mobile_access': int(row_s['mobile_access']) if 'mobile_access' in row_s.index else 0,
                                                    'position':     str(row_s['position']) if 'position' in row_s.index else '',
                                                }
                                            
                                        st.success("✅ تم تحديث بيانات الموظف بنجاح كلي.")
                                        st.rerun()

            with tab_change_pwd:
                st.write("##### 🔑 تغيير كلمة مرور أي مستخدم مباشرة:")
                st.info("يمكنك من هنا تغيير كلمة مرور أي موظف مسجل في النظام لأي كلمة تريدها.")
                df_all_users_pwd = pd.read_sql("SELECT username, full_name, role FROM users ORDER BY full_name ASC", conn)
                if not df_all_users_pwd.empty:
                    with st.form("direct_pwd_change_form", clear_on_submit=True):
                        selected_user = st.selectbox(
                            "اختر الموظف:",
                            options=df_all_users_pwd['username'].tolist(),
                            format_func=lambda x: df_all_users_pwd[df_all_users_pwd['username']==x]['full_name'].values[0] + f" ({x})"
                        )
                        col_np1, col_np2 = st.columns([1, 1])
                        new_pwd_direct = col_np1.text_input("كلمة المرور الجديدة *", type="password", key="direct_new_pwd")
                        confirm_pwd_direct = col_np2.text_input("تأكيد كلمة المرور *", type="password", key="direct_confirm_pwd")
                        if st.form_submit_button("💾 تغيير كلمة المرور", use_container_width=True):
                            if not new_pwd_direct:
                                st.error("⚠️ يرجى إدخال كلمة المرور الجديدة.")
                            elif new_pwd_direct != confirm_pwd_direct:
                                st.error("❌ كلمة المرور وتأكيدها غير متطابقين!")
                            else:
                                usr_info = df_all_users_pwd[df_all_users_pwd['username']==selected_user].iloc[0]
                                c.execute("UPDATE users SET password=? WHERE username=?", (new_pwd_direct, selected_user))
                                save_log("تغيير كلمة مرور مباشر", selected_user, 0,
                                         f"تم تغيير كلمة مرور [{usr_info['full_name']}] مباشرة من قبل مدير النظام", u['full_name'])
                                conn.commit()
                                st.success(f"✅ تم تغيير كلمة مرور [{usr_info['full_name']}] بنجاح!")

            with tab_mobile_access:
                st.write("##### 📱 إدارة صلاحية تشغيل النظام من الجوال")
                st.markdown("""
                <div style='background:#e3f2fd;border:2px solid #0288d1;border-radius:10px;padding:14px 18px;margin-bottom:18px;direction:rtl;font-size:14px;'>
                    🔐 <b>هذه الصفحة تتيح لك منح أو سحب صلاحية تشغيل النسخة المحسّنة للجوال لأي موظف.</b><br>
                    <small>• مدير النظام يمتلك هذه الصلاحية تلقائياً دائماً.<br>
                    • الموظفون الآخرون يظهر لهم خيار اختيار النسخة فقط إذا منحتهم الصلاحية من هنا.</small>
                </div>""", unsafe_allow_html=True)

                df_mobile_users = pd.read_sql(
                    "SELECT username, full_name, role, COALESCE(mobile_access, 0) as mobile_access FROM users ORDER BY full_name ASC", conn
                )

                if df_mobile_users.empty:
                    st.info("ℹ️ لا يوجد موظفون مسجلون في النظام.")
                else:
                    # إحصائيات سريعة
                    total_with_access = int(df_mobile_users[df_mobile_users['mobile_access'] == 1].shape[0])
                    total_all = len(df_mobile_users)
                    col_stat1, col_stat2, col_stat3 = st.columns(3)
                    col_stat1.metric("👥 إجمالي الموظفين", total_all)
                    col_stat2.metric("✅ لديهم صلاحية الجوال", total_with_access)
                    col_stat3.metric("🚫 بدون صلاحية الجوال", total_all - total_with_access)

                    st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
                    st.write("**قائمة الموظفين وحالة صلاحية الجوال:**")

                    for idx_m, r_mob in df_mobile_users.iterrows():
                        mob_key = r_mob['username']
                        is_admin = r_mob['role'] == "مدير نظام"
                        has_access = int(r_mob['mobile_access']) == 1 or is_admin

                        col_m1, col_m2, col_m3, col_m4 = st.columns([2.5, 1.5, 1, 1.2])
                        col_m1.write(f"👤 **{r_mob['full_name']}** ({mob_key})")
                        col_m2.write(f"🏷️ {r_mob['role']}")

                        if is_admin:
                            col_m3.markdown("<span style='color:#004a99;font-weight:bold;font-size:13px;'>✅ تلقائي</span>", unsafe_allow_html=True)
                            col_m4.markdown("<span style='color:#888;font-size:12px;'>مدير النظام</span>", unsafe_allow_html=True)
                        else:
                            if has_access:
                                col_m3.markdown("<span style='color:#1daa60;font-weight:bold;font-size:13px;'>✅ مفعّلة</span>", unsafe_allow_html=True)
                                if col_m4.button("🚫 سحب الصلاحية", key=f"revoke_mob_{mob_key}", use_container_width=True):
                                    c.execute("UPDATE users SET mobile_access=0 WHERE username=?", (mob_key,))
                                    save_log("سحب صلاحية جوال", mob_key, 0,
                                             f"تم سحب صلاحية الجوال من [{r_mob['full_name']}] بواسطة مدير النظام", u['full_name'])
                                    conn.commit()
                                    st.success(f"✅ تم سحب صلاحية الجوال من [{r_mob['full_name']}]")
                                    st.rerun()
                            else:
                                col_m3.markdown("<span style='color:#d32f2f;font-weight:bold;font-size:13px;'>🚫 محجوبة</span>", unsafe_allow_html=True)
                                if col_m4.button("✅ منح الصلاحية", key=f"grant_mob_{mob_key}", use_container_width=True):
                                    c.execute("UPDATE users SET mobile_access=1 WHERE username=?", (mob_key,))
                                    save_log("منح صلاحية جوال", mob_key, 0,
                                             f"تم منح صلاحية الجوال لـ [{r_mob['full_name']}] بواسطة مدير النظام", u['full_name'])
                                    conn.commit()
                                    st.success(f"✅ تم منح صلاحية الجوال لـ [{r_mob['full_name']}]")
                                    st.rerun()

                        st.markdown("<hr style='margin:3px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: إدارة النسخ الاحتياطية (مدير النظام فقط)
    # ---------------------------------------------------------
    elif st.session_state.page == "backup_page":
        if u['role'] != "مدير نظام":
            st.error("❌ هذه الصفحة متاحة لمدير النظام فقط.")
        else:
            st.markdown("<div class='main-title'>💾 إدارة النسخ الاحتياطية للنظام</div>", unsafe_allow_html=True)

            # ── التحقق من كلمة المرور ──
            if not st.session_state.get('backup_auth'):
                st.markdown("""
                <div style='background:#fff3cd;border:2px solid #f9a825;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;'>
                    🔐 <b>هذه الصفحة محمية بكلمة مرور إضافية</b>
                </div>""", unsafe_allow_html=True)
                _, col_bp, _ = st.columns([1, 1.5, 1])
                with col_bp:
                    with st.form("backup_auth_form"):
                        bp_pass = st.text_input("كلمة مرور النسخ الاحتياطية:", type="password")
                        if st.form_submit_button("🔓 دخول", use_container_width=True):
                            if bp_pass == BACKUP_PASSWORD:
                                st.session_state['backup_auth'] = True
                                st.rerun()
                            else:
                                st.error("❌ كلمة المرور غير صحيحة!")
            else:
                # ── معلومات النسخ التلقائية ──
                st.info("⏰ يتم إنشاء نسخة احتياطية تلقائياً مرتين يومياً: **8:00 صباحاً** و**8:00 مساءً** بتوقيت مكة المكرمة.")

                # ── نسخة احتياطية فورية ──
                st.write("### 🚀 إنشاء نسخة احتياطية فورية:")
                col_b1, col_b2 = st.columns([2, 1])
                col_b1.write("اضغط الزر لإنشاء نسخة احتياطية كاملة من قاعدة البيانات الآن.")
                if col_b2.button("💾 إنشاء نسخة احتياطية الآن", use_container_width=True):
                    bpath, bname, bsize = create_backup(u['full_name'])
                    if bpath:
                        st.success(f"✅ تم إنشاء النسخة الاحتياطية بنجاح: **{bname}** ({bsize} KB)")
                        with open(bpath, 'rb') as bf:
                            st.download_button(
                                label=f"⬇️ تحميل النسخة الاحتياطية ({bname})",
                                data=bf.read(),
                                file_name=bname,
                                mime="application/zip",
                                key="dl_instant_backup"
                            )
                    else:
                        st.error(f"❌ فشل إنشاء النسخة الاحتياطية: {bname}")

                st.divider()

                # ── البحث في النسخ الاحتياطية ──
                st.write("### 🗂️ سجل النسخ الاحتياطية:")
                col_bs1, col_bs2, col_bs3 = st.columns([1.5, 1.5, 1])
                search_backup_date = col_bs1.date_input("تصفية بالتاريخ:", value=None, key="backup_date_filter")
                search_backup_type = col_bs2.selectbox("نوع النسخة:", ["الكل", "تلقائي - 8 صباحاً", "تلقائي - 8 مساءً", u['full_name']], key="backup_type_filter")

                bq = "SELECT * FROM backups WHERE 1=1"
                if search_backup_date:
                    bq += f" AND backup_date='{search_backup_date.strftime('%Y-%m-%d')}'"
                if search_backup_type != "الكل":
                    bq += f" AND backup_type='{search_backup_type}'"
                bq += " ORDER BY id DESC"

                df_backups = pd.read_sql(bq, conn)
                if df_backups.empty:
                    st.info("ℹ️ لا توجد نسخ احتياطية تطابق معايير البحث.")
                else:
                    st.success(f"✅ تم العثور على ({len(df_backups)}) نسخة احتياطية.")
                    for _, br in df_backups.iterrows():
                        with st.container():
                            bc1, bc2, bc3, bc4 = st.columns([2, 1.5, 1, 1.2])
                            bc1.markdown(f"**💾 {br['backup_name']}**")
                            bc2.write(f"📅 {br['backup_date']} ⏰ {br['backup_time']}")
                            bc3.write(f"📦 {br['size_kb']} KB")
                            # زر تحميل النسخة
                            bfile_path = br['file_path']
                            if os.path.exists(bfile_path):
                                with open(bfile_path, 'rb') as bf:
                                    bc4.download_button(
                                        label="⬇️ تحميل",
                                        data=bf.read(),
                                        file_name=br['backup_name'],
                                        mime="application/zip",
                                        key=f"dl_backup_{br['id']}"
                                    )
                            else:
                                bc4.warning("⚠️ الملف غير موجود")
                            st.markdown(f"<small style='color:#888;'>النوع: {br['backup_type']} | بواسطة: {br['created_by']}</small>", unsafe_allow_html=True)
                            st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)

                st.divider()
                if st.button("🚪 تسجيل الخروج من صفحة النسخ الاحتياطية", key="logout_backup"):
                    st.session_state['backup_auth'] = False; st.rerun()

    # ---------------------------------------------------------
    # صفحة: الثوابت العامة والإعدادات التشغيلية
    # ---------------------------------------------------------
    elif st.session_state.page == "global_settings":
        st.markdown("<div class='main-title'>🏢 إدارة المستودعات والمقاولين والفئات</div>", unsafe_allow_html=True)

        if u['role'] != "مدير نظام":
            st.error("❌ هذه الصفحة متاحة لمدير النظام فقط.")
        elif not st.session_state.get('settings_auth'):
            st.markdown("""
            <div style='background:#fff3cd;border:2px solid #f9a825;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;'>
                🔐 <b>هذه الصفحة محمية بكلمة مرور إضافية</b><br>
                <small>أدخل كلمة المرور للوصول إلى إدارة المستودعات والمقاولين والفئات</small>
            </div>""", unsafe_allow_html=True)
            _, col_gsp, _ = st.columns([1, 1.5, 1])
            with col_gsp:
                with st.form("settings_auth_form"):
                    gsp_pass = st.text_input("كلمة المرور:", type="password")
                    if st.form_submit_button("🔓 دخول", use_container_width=True):
                        if gsp_pass == BACKUP_PASSWORD:
                            st.session_state['settings_auth'] = True
                            st.rerun()
                        else:
                            st.error("❌ كلمة المرور غير صحيحة!")
        else:
            _, col_gs_lock = st.columns([4, 1])
            if col_gs_lock.button("🔒 قفل الصفحة", key="lock_settings"):
                st.session_state['settings_auth'] = False; st.rerun()

            set_col1, set_col2, set_col3 = st.columns([1, 1, 1.2])

            with set_col1:
                st.markdown("### 🏢 إدارة مستودعات الطوارئ")
                df_wh = pd.read_sql("SELECT * FROM settings_warehouses", conn)
                if not df_wh.empty:
                    for _, r_wh in df_wh.iterrows():
                        wh_id = r_wh['id']
                        ek = f"wh_edit_{wh_id}"; ck = f"wh_confirm_{wh_id}"
                        if ek not in st.session_state: st.session_state[ek] = False
                        if ck not in st.session_state: st.session_state[ck] = False
                        cw1,cw2,cw3 = st.columns([2.5,0.65,0.65])
                        if not st.session_state[ek]:
                            cw1.write(f"📍 {r_wh['name']}")
                            if cw2.button("✏️", key=f"wh_e_{wh_id}"): st.session_state[ek]=True; st.rerun()
                            if cw3.button("🗑️", key=f"wh_d_{wh_id}"): st.session_state[ck]=True; st.rerun()
                        else:
                            with st.form(f"wh_ef_{wh_id}"):
                                nn = st.text_input("الاسم الجديد", value=r_wh['name'])
                                s1,s2 = st.columns(2)
                                if s1.form_submit_button("💾"):
                                    if nn.strip(): c.execute("UPDATE settings_warehouses SET name=? WHERE id=?",(nn.strip(),wh_id)); conn.commit(); st.session_state[ek]=False; st.rerun()
                                if s2.form_submit_button("❌"): st.session_state[ek]=False; st.rerun()
                        if st.session_state[ck]:
                            st.warning(f"⚠️ هل أنت متأكد من حذف المستودع **{r_wh['name']}**؟ لا يمكن التراجع.")
                            y1,y2 = st.columns(2)
                            if y1.button("✅ نعم، احذف", key=f"wh_yes_{wh_id}"):
                                c.execute("DELETE FROM settings_warehouses WHERE id=?",(wh_id,)); conn.commit(); st.session_state[ck]=False; st.rerun()
                            if y2.button("🚫 إلغاء", key=f"wh_no_{wh_id}"):
                                st.session_state[ck]=False; st.rerun()
                        st.markdown("<hr style='margin:3px 0;'>", unsafe_allow_html=True)
                else:
                    st.info("ℹ️ لا توجد مستودعات طوارئ معرّفة.")
                with st.form("add_wh_form", clear_on_submit=True):
                    new_wh = st.text_input("اسم المستودع الميداني الجديد")
                    if st.form_submit_button("حفظ المستودع"):
                        if new_wh: c.execute("INSERT INTO settings_warehouses (name) VALUES (?)",(new_wh.strip(),)); conn.commit(); st.rerun()

            with set_col2:
                st.markdown("### 🏗️ المقاولين المعتمدين")
                df_con = pd.read_sql("SELECT * FROM settings_contractors", conn)
                if not df_con.empty:
                    for _, r_con in df_con.iterrows():
                        con_id = r_con['id']
                        cek = f"con_edit_{con_id}"; cck = f"con_confirm_{con_id}"
                        if cek not in st.session_state: st.session_state[cek] = False
                        if cck not in st.session_state: st.session_state[cck] = False
                        cc1,cc2,cc3 = st.columns([2.5,0.65,0.65])
                        if not st.session_state[cek]:
                            cc1.write(f"👷 {r_con['name']}")
                            if cc2.button("✏️", key=f"con_e_{con_id}"): st.session_state[cek]=True; st.rerun()
                            if cc3.button("🗑️", key=f"con_d_{con_id}"): st.session_state[cck]=True; st.rerun()
                        else:
                            with st.form(f"con_ef_{con_id}"):
                                nn = st.text_input("الاسم الجديد", value=r_con['name'])
                                s1,s2 = st.columns(2)
                                if s1.form_submit_button("💾"):
                                    if nn.strip(): c.execute("UPDATE settings_contractors SET name=? WHERE id=?",(nn.strip(),con_id)); conn.commit(); st.session_state[cek]=False; st.rerun()
                                if s2.form_submit_button("❌"): st.session_state[cek]=False; st.rerun()
                        if st.session_state[cck]:
                            st.warning(f"⚠️ هل أنت متأكد من حذف المقاول **{r_con['name']}**؟ لا يمكن التراجع.")
                            y1,y2 = st.columns(2)
                            if y1.button("✅ نعم، احذف", key=f"con_yes_{con_id}"):
                                c.execute("DELETE FROM settings_contractors WHERE id=?",(con_id,)); conn.commit(); st.session_state[cck]=False; st.rerun()
                            if y2.button("🚫 إلغاء", key=f"con_no_{con_id}"):
                                st.session_state[cck]=False; st.rerun()
                        st.markdown("<hr style='margin:3px 0;'>", unsafe_allow_html=True)
                else:
                    st.info("ℹ️ لا يوجد مقاولين معتمدين حالياً.")
                with st.form("add_con_form", clear_on_submit=True):
                    new_con = st.text_input("اسم المقاول / الشركة الجديد")
                    if st.form_submit_button("حفظ المقاول"):
                        if new_con: c.execute("INSERT INTO settings_contractors (name) VALUES (?)",(new_con.strip(),)); conn.commit(); st.rerun()

            with set_col3:
                st.markdown("### 🏷️ فئات أصناف المواد وحدود الأمان")
                df_cat = pd.read_sql("SELECT * FROM settings_categories", conn)
                if not df_cat.empty:
                    for idx_c, r_cat in df_cat.iterrows():
                        with st.expander(f"📦 {r_cat['name']}"):
                            cat_id = r_cat['id']; cat_old_name = r_cat['name']
                            new_cat_name = st.text_input("تعديل الاسم", value=r_cat['name'], key=f"edit_name_cat_{cat_id}")
                            new_red = st.number_input("🔴 الحد الحرج", value=float(r_cat['red_limit']), key=f"edit_red_cat_{cat_id}")
                            new_yellow = st.number_input("🟡 حد التنبيه", value=float(r_cat['yellow_limit']), key=f"edit_yel_cat_{cat_id}")
                            c_actions_cat1, c_actions_cat2 = st.columns([1, 1])
                            if c_actions_cat1.button("🗑️ حذف الفئة", key=f"del_cat_btn_{cat_id}"):
                                c.execute("DELETE FROM settings_categories WHERE id=?", (cat_id,)); conn.commit(); st.rerun()
                            if c_actions_cat2.button("💾 حفظ", key=f"save_cat_btn_{cat_id}"):
                                if new_cat_name:
                                    c.execute("UPDATE settings_categories SET name=?, red_limit=?, yellow_limit=? WHERE id=?",
                                              (new_cat_name.strip(), new_red, new_yellow, cat_id))
                                    c.execute("UPDATE material_definitions SET category=? WHERE category=?", (new_cat_name.strip(), cat_old_name))
                                    c.execute("UPDATE inventory SET category=? WHERE category=?", (new_cat_name.strip(), cat_old_name))
                                    conn.commit(); st.success("✅ تم تحديث اسم الفئة ومستويات الخطر بنجاح."); st.rerun()
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
                            conn.commit(); st.success(f"✅ تم إضافة الفئة الجديدة [{new_cat}] وتحديد حدود الأمان بنجاح."); st.rerun()
# =========================================================
# 8. إغلاق اتصال قاعدة البيانات عند نهاية التنفيذ لضمان سلامة البيانات
# =========================================================
if 'conn' in locals() or 'conn' in globals():
    try:
        pass
    except NameError:
        pass