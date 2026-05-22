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

    # جدول صلاحيات المستودعات لأمين مستودع المقاول
    c.execute('''CREATE TABLE IF NOT EXISTS contractor_warehouse_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    warehouse TEXT,
                    UNIQUE(username, warehouse))''')

    # جدول الفواتير الموقعة والمرفقة من أمين مستودع المقاول
    c.execute('''CREATE TABLE IF NOT EXISTS signed_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_no TEXT,
                    invoice_type TEXT,
                    original_invoice_id INTEGER,
                    signed_by TEXT,
                    signed_image_base64 TEXT,
                    signed_at TEXT,
                    deducted INTEGER DEFAULT 0,
                    status TEXT DEFAULT "بانتظار الاعتماد",
                    admin_notes TEXT DEFAULT "",
                    reviewed_by TEXT DEFAULT "",
                    reviewed_at TEXT DEFAULT "")''')
    # إضافة الأعمدة الناقصة إن لم تكن موجودة
    for _sc, _st in [
        ("invoice_no",          "TEXT DEFAULT ''"),
        ("invoice_type",        "TEXT DEFAULT ''"),
        ("original_invoice_id", "INTEGER DEFAULT 0"),
        ("signed_by",           "TEXT DEFAULT ''"),
        ("signed_image_base64", "TEXT DEFAULT ''"),
        ("signed_at",           "TEXT DEFAULT ''"),
        ("deducted",            "INTEGER DEFAULT 0"),
        ("status",              "TEXT DEFAULT 'بانتظار الاعتماد'"),
        ("admin_notes",         "TEXT DEFAULT ''"),
        ("reviewed_by",         "TEXT DEFAULT ''"),
        ("reviewed_at",         "TEXT DEFAULT ''"),
        ("boq",                 "TEXT DEFAULT ''"),
    ]:
        try:
            c.execute(f"ALTER TABLE signed_invoices ADD COLUMN {_sc} {_st}")
            conn.commit()
        except Exception:
            pass

    # جدول طلبات إلغاء الفواتير (من موجه البلاغات — يحتاج اعتماد)
    c.execute('''CREATE TABLE IF NOT EXISTS cancel_invoice_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_no TEXT,
                    invoice_no TEXT,
                    invoice_type TEXT,
                    warehouse_return TEXT,
                    contractor TEXT,
                    items_json TEXT,
                    cancel_reason TEXT,
                    requester TEXT,
                    status TEXT DEFAULT "معلق",
                    invoice_html TEXT,
                    timestamp TEXT,
                    approved_by TEXT,
                    approved_at TEXT)''')
    # إضافة الأعمدة الناقصة لقواعد البيانات القديمة
    for _ccol, _ctype in [
        ("request_no",      "TEXT DEFAULT ''"),
        ("invoice_no",      "TEXT DEFAULT ''"),
        ("invoice_type",    "TEXT DEFAULT ''"),
        ("warehouse_return","TEXT DEFAULT ''"),
        ("contractor",      "TEXT DEFAULT ''"),
        ("items_json",      "TEXT DEFAULT '[]'"),
        ("cancel_reason",   "TEXT DEFAULT ''"),
        ("boq",             "TEXT DEFAULT ''"),
        ("requester",       "TEXT DEFAULT ''"),
        ("status",          "TEXT DEFAULT 'معلق'"),
        ("invoice_html",    "TEXT DEFAULT ''"),
        ("timestamp",       "TEXT DEFAULT ''"),
        ("approved_by",     "TEXT DEFAULT ''"),
        ("approved_at",     "TEXT DEFAULT ''"),
    ]:
        try:
            c.execute(f"ALTER TABLE cancel_invoice_requests ADD COLUMN {_ccol} {_ctype}")
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
                    boq TEXT DEFAULT "",
                    timestamp TEXT)''')
    # إضافة عمود BOQ لقواعد البيانات القديمة
    try:
        c.execute("ALTER TABLE archived_invoices ADD COLUMN boq TEXT DEFAULT ''")
        conn.commit()
    except Exception:
        pass
    
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
                    return_reason TEXT DEFAULT "",
                    invoice_html TEXT,
                    timestamp TEXT,
                    approved_by TEXT,
                    approved_at TEXT)''')
    # إضافة الأعمدة الناقصة لقواعد البيانات القديمة (توافق مع الإصدارات السابقة)
    for _col, _type in [
        ("request_no",  "TEXT DEFAULT ''"),
        ("warehouse",   "TEXT DEFAULT ''"),
        ("contractor",  "TEXT DEFAULT ''"),
        ("items_json",  "TEXT DEFAULT '[]'"),
        ("requester",   "TEXT DEFAULT ''"),
        ("status",      "TEXT DEFAULT 'معلق'"),
        ("notes",       "TEXT DEFAULT ''"),
        ("return_reason","TEXT DEFAULT ''"),
        ("boq",         "TEXT DEFAULT ''"),
        ("invoice_html","TEXT DEFAULT ''"),
        ("timestamp",   "TEXT DEFAULT ''"),
        ("approved_by", "TEXT DEFAULT ''"),
        ("approved_at", "TEXT DEFAULT ''"),
    ]:
        try:
            c.execute(f"ALTER TABLE return_requests ADD COLUMN {_col} {_type}")
            conn.commit()
        except Exception:
            pass

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
                    notes TEXT,
                    sort_order INTEGER DEFAULT 0)''')
    # إضافة عمود الترتيب لقواعد البيانات القديمة
    try:
        c.execute("ALTER TABLE managers_directory ADD COLUMN sort_order INTEGER DEFAULT 0")
        conn.commit()
    except Exception:
        pass

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

def render_invoice_html(title, items_list, warehouse, contractor, employee, custom_inv_no=None, extra_info=None, boq=""):
    inv_no = custom_inv_no if custom_inv_no else now_mecca().strftime("%d%H%M")
    dt_str = now_mecca().strftime("%Y-%m-%d")
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
    boq_line = f"<div style='font-size:13px;color:#111111;font-weight:bold;margin-top:4px;'>BOQ الحالة: {boq}</div>" if boq else ""
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
            <div>
                <b>رقم الفاتورة:</b> <span style="color:red;font-weight:bold;font-size:16px;">{inv_no}</span>
                {boq_line}
            </div>
            <div><b>التاريخ:</b> {dt_str}</div>
            <div><b>المسؤول:</b> {employee}</div>
        </div>
        <h3 style="text-align:center;background:#004a99;color:white;padding:12px;border-radius:8px;font-size:19px;margin-bottom:18px;">{title}</h3>
        <div style="background:#f9f9f9;padding:12px 15px;border-radius:8px;margin-bottom:18px;border:1px solid #eee;font-size:14px;">
            <table style="width:100%;border:none;">
                <tr>
                    <td><b>مستودع الصرف:</b> {warehouse if warehouse else 'N/A'}</td>
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
            <div style="width:45%;"><p><b>توقيع أمين المستودع</b></p><br><br><p>_______________________</p></div>
            <div style="width:45%;"><p><b>توقيع المقاول / المستلم للمواد</b></p><br><br><p>_______________________</p></div>
        </div>
        <div style="text-align:center;margin-top:40px;" class="no-print">
            <button onclick="window.print()" style="padding:12px 35px;background:#f9a825;color:white;border:none;border-radius:6px;font-size:16px;font-weight:bold;cursor:pointer;">🖨️ اضغط هنا لطباعة الفاتورة</button>
        </div>
    </div>"""
    return html

def render_return_invoice_html(title, items_list, warehouse, contractor, employee, custom_inv_no=None, boq=""):
    """فاتورة الارجاع — مستودع مستلم + مقاول مسلم"""
    inv_no = custom_inv_no if custom_inv_no else now_mecca().strftime("%d%H%M")
    dt_str = now_mecca().strftime("%Y-%m-%d")
    rows = ""
    for item in items_list:
        rows += (
            "<tr>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:center;font-weight:bold;'>{item['code']}</td>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:right;'>{item['name']}</td>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:center;color:#004a99;font-weight:bold;font-size:16px;'>{item['qty']}</td>"
            "</tr>"
        )
    boq_line = f"<div style='font-size:13px;color:#111111;font-weight:bold;margin-top:4px;'>BOQ الحالة: {boq}</div>" if boq else ""
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
            <div>
                <b>رقم الفاتورة:</b> <span style="color:red;font-weight:bold;font-size:16px;">{inv_no}</span>
                {boq_line}
            </div>
            <div><b>التاريخ:</b> {dt_str}</div>
            <div><b>المسؤول:</b> {employee}</div>
        </div>
        <h3 style="text-align:center;background:#004a99;color:white;padding:12px;border-radius:8px;font-size:19px;margin-bottom:18px;">{title}</h3>
        <div style="background:#f9f9f9;padding:12px 15px;border-radius:8px;margin-bottom:18px;border:1px solid #eee;font-size:14px;">
            <table style="width:100%;border:none;">
                <tr>
                    <td><b>المستودع المستلم:</b> {warehouse if warehouse else 'N/A'}</td>
                    <td><b>المقاول المسلم للمادة:</b> {contractor if contractor else 'N/A'}</td>
                </tr>
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
            <div style="width:45%;"><p><b>توقيع أمين مستودع المستلم</b></p><br><br><p>_______________________</p></div>
            <div style="width:45%;"><p><b>المقاول المسلم للمادة</b></p><br><br><p>_______________________</p></div>
        </div>
        <div style="text-align:center;margin-top:40px;" class="no-print">
            <button onclick="window.print()" style="padding:12px 35px;background:#f9a825;color:white;border:none;border-radius:6px;font-size:16px;font-weight:bold;cursor:pointer;">🖨️ اضغط هنا لطباعة الفاتورة</button>
        </div>
    </div>"""
    return html

def render_transfer_invoice_html(title, items_list, wh_from, wh_to, employee, custom_inv_no=None):
    """فاتورة نقل المواد بين المستودعات — بدون مقاول"""
    inv_no = custom_inv_no if custom_inv_no else now_mecca().strftime("%d%H%M")
    dt_str = now_mecca().strftime("%Y-%m-%d")
    rows = ""
    for item in items_list:
        rows += (
            "<tr>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:center;font-weight:bold;'>{item['code']}</td>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:right;'>{item['name']}</td>"
            f"<td style='border:1px solid #ddd;padding:10px;text-align:center;color:#004a99;font-weight:bold;font-size:16px;'>{item['qty']}</td>"
            "</tr>"
        )
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
            <div><b>التاريخ:</b> {dt_str}</div>
            <div><b>المسؤول:</b> {employee}</div>
        </div>
        <h3 style="text-align:center;background:#004a99;color:white;padding:12px;border-radius:8px;font-size:19px;margin-bottom:18px;">{title}</h3>
        <div style="background:#f9f9f9;padding:12px 15px;border-radius:8px;margin-bottom:18px;border:1px solid #eee;font-size:14px;">
            <table style="width:100%;border:none;">
                <tr>
                    <td><b>المستودع المنقولة منه المواد:</b> {wh_from if wh_from else 'N/A'}</td>
                    <td><b>المستودع المستلم للمواد:</b> {wh_to if wh_to else 'N/A'}</td>
                </tr>
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
            <div style="width:45%;"><p><b>توقيع أمين مستودع المنقولة منه المواد</b></p><br><br><p>_______________________</p></div>
            <div style="width:45%;"><p><b>توقيع أمين المستودع المستلم للمواد</b></p><br><br><p>_______________________</p></div>
        </div>
        <div style="text-align:center;margin-top:40px;" class="no-print">
            <button onclick="window.print()" style="padding:12px 35px;background:#f9a825;color:white;border:none;border-radius:6px;font-size:16px;font-weight:bold;cursor:pointer;">🖨️ اضغط هنا لطباعة الفاتورة</button>
        </div>
    </div>"""
    return html

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

def archive_invoice(invoice_type, invoice_no, wh_from, wh_to, contractor, employee, items_json, html_content, boq=""):
    timestamp = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO archived_invoices (invoice_type, invoice_no, warehouse_from, warehouse_to, contractor, employee, items_json, html_content, boq, timestamp)
                 VALUES (?,?,?,?,?,?,?,?,?,?)""", (invoice_type, invoice_no, wh_from, wh_to, contractor, employee, items_json, html_content, boq, timestamp))
    conn.commit()

def to_excel(df):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='التقرير المخرجات')
    return output.getvalue()

# ── دالة رأس الصفحة الموحدة بهوية النظام ──
def page_header(icon, title, subtitle="", accent="#004a99"):
    st.markdown(f"""
    <div dir="rtl" style="
        background: linear-gradient(135deg, #0a1628 0%, #0d2347 60%, #0a1628 100%);
        border-radius: 14px; padding: 20px 28px; margin-bottom: 22px;
        border-right: 6px solid {accent};
        box-shadow: 0 4px 18px rgba(0,74,153,0.18);
        position: relative; overflow: hidden;
    ">
        <div style="position:absolute;top:0;left:0;right:0;bottom:0;
            background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,0.03) 50%,transparent 100%);
            pointer-events:none;"></div>
        <div style="font-size:32px; margin-bottom:4px;">{icon}</div>
        <div style="font-size:22px; font-weight:900; color:#e8f0ff; letter-spacing:0.5px;">{title}</div>
        {"<div style='font-size:13px;color:#8eaacc;margin-top:4px;'>" + subtitle + "</div>" if subtitle else ""}
        <div style="position:absolute;left:20px;top:50%;transform:translateY(-50%);
            font-size:60px;opacity:0.04;color:white;font-weight:900;">{icon}</div>
    </div>
    """, unsafe_allow_html=True)

# ── دالة بطاقة قسم داخلي (sub-section) ──
def section_card(label, color="#004a99"):
    st.markdown(f"""
    <div dir="rtl" style="
        background: linear-gradient(90deg, {color}18, {color}08);
        border-right: 4px solid {color};
        border-radius: 8px; padding: 8px 16px; margin: 14px 0 8px 0;
        font-weight: 800; font-size: 14px; color: {color};
        letter-spacing: 0.3px;
    ">{label}</div>
    """, unsafe_allow_html=True)

# ── دالة عرض السلة بتصميم موحد ──
def render_cart_table(cart, page_key, warehouse=None, conn=None):
    """يعرض محتوى السلة كجدول بتصميم الهوية"""
    if not cart:
        return
    rows = ""
    for i, item in enumerate(cart):
        avail_txt = ""
        if warehouse and conn is not None:
            try:
                avail = int(pd.read_sql(
                    f"SELECT COALESCE(SUM(qty),0) as t FROM inventory WHERE item_code='{item['code']}' AND warehouse='{warehouse}'",
                    conn).iloc[0]['t'])
                avail_txt = f"<span style='color:#888;font-size:11px;'> / {avail}</span>"
            except Exception:
                pass
        rows += f"""
        <tr>
            <td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;font-weight:900;color:#004a99;font-size:12px;'>{item['code']}</td>
            <td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;font-size:13px;'>{item['name']}</td>
            <td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;color:#666;font-size:12px;'>{item.get('cat','—')}</td>
            <td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;text-align:center;'>
                <span style='background:#004a99;color:white;border-radius:16px;padding:2px 12px;font-weight:900;font-size:13px;'>{item['qty']}{avail_txt}</span>
            </td>
        </tr>"""
    components.html(f"""
    <html><head><meta charset="utf-8">
    <style>
        body{{margin:0;padding:0;font-family:'Tajawal',Arial,sans-serif;direction:rtl;}}
        table{{width:100%;border-collapse:collapse;border-radius:10px;overflow:hidden;box-shadow:0 2px 10px rgba(0,74,153,0.1);}}
        thead tr{{background:linear-gradient(90deg,#004a99,#0066cc);color:white;}}
        thead th{{padding:9px 12px;text-align:right;font-weight:900;font-size:13px;}}
        tbody tr:nth-child(even){{background:#f7faff;}}
        tbody tr:hover{{background:#e8f0fe;}}
    </style></head><body>
    <table>
        <thead><tr>
            <th style="width:18%;">كود المادة</th>
            <th style="width:42%;">اسم المادة</th>
            <th style="width:22%;">الفئة</th>
            <th style="width:18%;text-align:center;">الكمية</th>
        </tr></thead>
        <tbody>{rows}</tbody>
    </table>
    </body></html>
    """, height=min(60 + len(cart)*42, 400), scrolling=len(cart) > 8)

# ── دالة جدول HTML عام — تُستخدم في كل أقسام النظام ──
def html_table(df, accent="#004a99", info_label=None, badge_col=None,
               badge_map=None, height=None, download_key=None, download_label=None, download_name=None):
    """
    تعرض أي DataFrame بتصميم الهوية الموحد.
    accent      : لون رأس الجدول
    info_label  : نص شريط المعلومات (None = لا يُعرض)
    badge_col   : اسم العمود الذي يُعرض كـ badge ملوّن
    badge_map   : dict { قيمة: (bg, fg) } لتلوين badge_col
    """
    if df is None or df.empty:
        return
    cols = df.columns.tolist()

    # بناء صفوف HTML
    rows_html = ""
    for _, row in df.iterrows():
        row_style = ""
        cells = ""
        for col in cols:
            val = str(row[col]) if row[col] is not None else "—"
            # هل هذا العمود badge؟
            if badge_col and col == badge_col and badge_map:
                bg, fg = badge_map.get(val, ("#78909c","white"))
                cell = f"""<td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;text-align:center;'>
                    <span style='background:{bg};color:{fg};border-radius:8px;padding:3px 10px;
                    font-size:12px;font-weight:bold;white-space:nowrap;'>{val}</span></td>"""
            # الأرقام تُعرض وسطاً
            elif val.lstrip('-').replace('.','',1).isdigit():
                num = int(float(val))
                if badge_col is None:  # رصيد عادي
                    if num <= 5:   nbg="#d32f2f"; nfg="white"
                    elif num <= 15: nbg="#f9a825"; nfg="#333"
                    else:           nbg="#004a99"; nfg="white"
                    cell = f"""<td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;text-align:center;'>
                        <span style='background:{nbg};color:{nfg};border-radius:16px;padding:2px 10px;font-weight:900;font-size:13px;'>{num}</span></td>"""
                else:
                    cell = f"<td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;text-align:center;font-weight:700;'>{val}</td>"
            else:
                cell = f"<td style='padding:8px 12px;border-bottom:1px solid #f0f4f8;font-size:13px;'>{val}</td>"
            cells += cell

        rows_html += f"<tr style='{row_style}'>{cells}</tr>\n"

    # بناء رؤوس الأعمدة
    headers = "".join(f"<th style='padding:10px 12px;text-align:right;font-weight:900;font-size:13px;letter-spacing:0.2px;'>{c}</th>" for c in cols)

    # شريط المعلومات
    info_bar = ""
    if info_label:
        info_bar = f"""<div style='display:flex;justify-content:space-between;align-items:center;
            padding:8px 14px;background:#f0f4ff;border-bottom:1px solid #dde6f5;
            font-size:13px;color:#555;direction:rtl;'>
            <span>{info_label} <b style="color:{accent};font-size:15px;">{len(df)}</b></span>
        </div>"""

    table_html = f"""<html><head><meta charset="utf-8">
    <style>
        body{{margin:0;padding:0;font-family:'Tajawal',Arial,sans-serif;direction:rtl;background:transparent;}}
        .wrap{{border-radius:12px;overflow:hidden;box-shadow:0 2px 14px rgba(0,74,153,0.10);border:1px solid #e8eef6;}}
        table{{width:100%;border-collapse:collapse;}}
        thead tr{{background:linear-gradient(90deg,{accent},{accent}cc);color:white;}}
        tbody tr:nth-child(even){{background:#f7faff;}}
        tbody tr:hover{{background:#e8f0fe;transition:background 0.15s;}}
    </style></head><body>
    {info_bar}
    <div class="wrap"><table>
        <thead><tr>{headers}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table></div>
    </body></html>"""

    tbl_h = height or min(90 + len(df) * 42, 560)
    components.html(table_html, height=tbl_h, scrolling=len(df) > 10)

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
    div[data-badge]::after {
        content: attr(data-badge); position: absolute; top: -6px; left: -6px;
        background: #d32f2f; color: white; border-radius: 50%; min-width: 20px; height: 20px;
        font-size: 11px; font-weight: 900; display: flex; align-items: center; justify-content: center;
        padding: 0 4px; box-shadow: 0 1px 4px rgba(0,0,0,0.3); z-index: 999; pointer-events: none; border: 2px solid white;
    }
    div[data-badge] { position: relative; display: inline-block; width: 100%; }
    .ret-btn-wrap { position: relative; display: block; width: 100%; }
    .ret-btn-wrap .ret-badge {
        position: absolute; top: 2px; left: 4px; background: #d32f2f; color: white;
        border-radius: 50%; min-width: 20px; height: 20px; font-size: 11px; font-weight: 900;
        display: flex; align-items: center; justify-content: center; padding: 0 3px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.35); z-index: 999; pointer-events: none;
        border: 2px solid white; line-height: 1;
    }

    /* ═══════════════════════════════════════════
       أقسام الشريط الجانبي — تصميم موحد أنيق
    ═══════════════════════════════════════════ */

    /* رأس القسم — موحد لجميع الأقسام */
    .sb-section-stock,
    .sb-section-requests,
    .sb-section-admin,
    .sb-section-emergency,
    .sb-section-invoices {
        background: linear-gradient(90deg, #0a1628 0%, #0d2347 50%, #0a1628 100%);
        color: #e8edf5;
        border-radius: 6px;
        padding: 6px 10px;
        text-align: center;
        margin: 10px 0 4px 0;
        font-weight: 800;
        font-size: 12px;
        letter-spacing: 1px;
        text-transform: uppercase;
        border-top: 2px solid #004a99;
        border-bottom: 1px solid rgba(0,74,153,0.3);
        position: relative;
        overflow: hidden;
    }
    .sb-section-stock::before,
    .sb-section-requests::before,
    .sb-section-admin::before,
    .sb-section-emergency::before,
    .sb-section-invoices::before {
        content: '';
        position: absolute; top: 0; left: -100%;
        width: 60%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.06), transparent);
        animation: sb-shine 3s infinite;
    }
    @keyframes sb-shine {
        0%   { left: -100%; }
        60%  { left: 150%;  }
        100% { left: 150%;  }
    }

    /* لون خاص لكل قسم على الخط العلوي */
    .sb-section-stock     { border-top-color: #f9a825; }
    .sb-section-requests  { border-top-color: #004a99; }
    .sb-section-admin     { border-top-color: #546e7a; }
    .sb-section-emergency { border-top-color: #c62828; }
    .sb-section-invoices  { border-top-color: #004a99; }

    /* أزرار الأقسام — أبيض نظيف بخط ملون على اليمين */
    .sb-btn-stock > div > button,
    .sb-btn-requests > div > button,
    .sb-btn-admin > div > button,
    .sb-btn-emergency > div > button,
    .sb-btn-invoices > div > button {
        background-color: white !important;
        border-radius: 7px !important;
        font-weight: bold !important;
        font-size: 14px !important;
        transition: all 0.2s ease !important;
    }
    .sb-btn-stock > div > button {
        color: #b45309 !important;
        border: 1px solid #e5e7eb !important;
        border-right: 3px solid #f9a825 !important;
    }
    .sb-btn-stock > div > button:hover {
        background-color: #fffbeb !important;
        border-right-color: #b45309 !important;
    }
    .sb-btn-requests > div > button {
        color: #004a99 !important;
        border: 1px solid #e5e7eb !important;
        border-right: 3px solid #004a99 !important;
    }
    .sb-btn-requests > div > button:hover {
        background-color: #eff6ff !important;
        border-right-color: #002f6c !important;
    }
    .sb-btn-admin > div > button {
        color: #1e293b !important;
        border: 1px solid #e5e7eb !important;
        border-right: 3px solid #546e7a !important;
        background-color: #f8fafc !important;
    }
    .sb-btn-admin > div > button:hover {
        background-color: #e2e8f0 !important;
    }
    .sb-btn-emergency > div > button {
        color: #991b1b !important;
        border: 1px solid #e5e7eb !important;
        border-right: 3px solid #c62828 !important;
    }
    .sb-btn-emergency > div > button:hover {
        background-color: #fff1f2 !important;
    }
    .sb-btn-invoices > div > button {
        color: #004a99 !important;
        border: 1px solid #e5e7eb !important;
        border-right: 3px solid #0288d1 !important;
    }
    .sb-btn-invoices > div > button:hover {
        background-color: #e0f2fe !important;
    }

    /* جدول المخزون المحسّن */
    .inv-table-wrap { border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,74,153,0.10); }
    .inv-row-header {
        background: linear-gradient(90deg, #004a99, #0066cc);
        color: white; font-weight: 900; font-size: 13px;
        padding: 10px 14px; display: flex; gap: 8px; direction: rtl;
    }
    .inv-row {
        display: flex; gap: 8px; padding: 9px 14px; direction: rtl;
        border-bottom: 1px solid #f0f4f8; font-size: 13px; align-items: center;
        transition: background 0.15s;
    }
    .inv-row:nth-child(even) { background: #f7faff; }
    .inv-row:hover { background: #e8f0fe; }
    .inv-qty-badge {
        display: inline-block; background: #004a99; color: white;
        border-radius: 20px; padding: 2px 12px; font-weight: 900; font-size: 13px;
        min-width: 40px; text-align: center;
    }
    .inv-qty-badge.low  { background: #d32f2f; }
    .inv-qty-badge.mid  { background: #f9a825; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# ── إصلاح مشكلة الشريط الجانبي لا يختفي بالكامل عند الإغلاق ──
st.markdown("""
<style>
/* عند إغلاق الشريط الجانبي: المحتوى يمتد لكامل العرض بدون فراغ */
[data-testid="stSidebar"][aria-expanded="false"] {
    width: 0px !important;
    min-width: 0px !important;
    overflow: hidden !important;
    visibility: hidden !important;
    padding: 0 !important;
    margin: 0 !important;
}
/* المحتوى الرئيسي يأخذ كامل العرض عند إغلاق السايدبار */
[data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stAppViewContainer"] > section[data-testid="stMain"],
section[data-testid="stMain"] {
    transition: margin-right 0.3s ease, width 0.3s ease;
}
/* إزالة الهامش الأيمن المتبقي عند إغلاق السايدبار */
@media (min-width: 768px) {
    [data-testid="stSidebar"][aria-expanded="false"] {
        width: 0rem !important;
        min-width: 0rem !important;
    }
    [data-testid="stSidebar"][aria-expanded="false"] + div {
        margin-right: 0 !important;
    }
}
/* زر فتح/إغلاق السايدبار - تحسين ظهوره */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}
</style>
""", unsafe_allow_html=True)

# التحقق من صلاحية الجوال: إعادة ضبط الوضع للحاسب إذا لم يكن للمستخدم صلاحية
if st.session_state.get('auth', False) and st.session_state.get('display_mode') == "mobile":
    _u_check = st.session_state.get('user_info')
    _has_mobile_perm = (_u_check and (
        _u_check.get('role') == "مدير نظام" or
        int(_u_check.get('mobile_access', 0)) == 1
    ))
    if not _has_mobile_perm:
        st.session_state['display_mode'] = "desktop"

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
if 'page' not in st.session_state: st.session_state.page = "inventory_status"; st.query_params["_pg"] = "inventory_status"

# ── استعادة الصفحة من query param عند التحديث ──
_qp_page = st.query_params.get("_pg", "")
if _qp_page and st.session_state.page == "inventory_status" and _qp_page != "inventory_status":
    st.session_state.page = _qp_page

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
if 'admin_pwd_auth' not in st.session_state: st.session_state['admin_pwd_auth'] = False
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
if 'stock_in_pending' not in st.session_state: st.session_state['stock_in_pending'] = None
if 'stock_in_confirm' not in st.session_state: st.session_state['stock_in_confirm'] = False
# متغيرات لتخزين رقم الفاتورة الأخيرة المنشأة للتوجيه
if 'last_created_inv_no' not in st.session_state: st.session_state['last_created_inv_no'] = None
if 'last_created_inv_type' not in st.session_state: st.session_state['last_created_inv_type'] = None
if 'last_ret_req_no' not in st.session_state: st.session_state['last_ret_req_no'] = None
if 'my_inv_show_latest' not in st.session_state: st.session_state['my_inv_show_latest'] = False
# متغيرات طلبات الغاء الفاتورة
if 'cancel_inv_no' not in st.session_state: st.session_state['cancel_inv_no'] = ""
if 'cancel_inv_type' not in st.session_state: st.session_state['cancel_inv_type'] = "صرف"
if 'cancel_inv_data' not in st.session_state: st.session_state['cancel_inv_data'] = None
if 'cancel_inv_confirm' not in st.session_state: st.session_state['cancel_inv_confirm'] = False
if 'last_cancel_req_no' not in st.session_state: st.session_state['last_cancel_req_no'] = None
if '_boq_override' not in st.session_state: st.session_state['_boq_override'] = None
if '_view_inv_no' not in st.session_state: st.session_state['_view_inv_no'] = None

# ── متغيرات انتهاء الجلسة (30 دقيقة) ──
import time as _time
_TIMEOUT_SECONDS = 30 * 60  # 30 دقيقة
if 'last_activity' not in st.session_state:
    st.session_state['last_activity'] = _time.time()
if 'session_expired' not in st.session_state:
    st.session_state['session_expired'] = False

# تحديث وقت آخر نشاط عند كل تفاعل (rerun)
if st.session_state.get('auth', False):
    _now = _time.time()
    _elapsed = _now - st.session_state.get('last_activity', _now)
    if _elapsed > _TIMEOUT_SECONDS:
        # انتهت الجلسة — تسجيل خروج تلقائي
        st.session_state.auth = False
        st.session_state.user_info = None
        st.session_state['session_expired'] = True
        st.session_state['last_activity'] = _time.time()
        # مسح قيمة _u من URL
        try: st.query_params.clear()
        except Exception: pass
        st.rerun()
    else:
        st.session_state['last_activity'] = _time.time()

# حقن JS لإعادة تحميل الصفحة تلقائياً كل 60 ثانية (لتشغيل فحص Python)
st.markdown("""
<script>
(function(){
    // إعادة تحميل كل 60 ثانية لتشغيل فحص انتهاء الجلسة في Python
    if (!window._autoReloadTimer) {
        window._autoReloadTimer = setInterval(function(){
            // إرسال rerun عبر تغيير param وهمي
            var url = new URL(window.location.href);
            url.searchParams.set('_t', Date.now());
            window.history.replaceState(null, '', url.toString());
            // إنهاء الـ interval بعد تحديث الـ URL لتشغيل Streamlit rerun
            clearInterval(window._autoReloadTimer);
            window._autoReloadTimer = null;
            window.dispatchEvent(new Event('streamlit:rerun'));
        }, 60000);
    }
})();
</script>
""", unsafe_allow_html=True)

# شعار السعودية للطاقة مضمّن مباشرة في الكود
LOGO_DATA_URI = "data:image/png;base64,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"

# ══════════════════════════════════════════════════════════════
# حجب الجوال — CSS media query + شاشة حجب مضمونة
# ══════════════════════════════════════════════════════════════
_current_user  = st.session_state.get('user_info')
_has_mobile_access = (
    _current_user and (
        _current_user.get('role') == "مدير نظام" or
        int(_current_user.get('mobile_access', 0)) == 1
    )
) if st.session_state.get('auth', False) else True

# إذا لم يكن للمستخدم صلاحية الجوال، نُخفي كل شيء على الشاشات الصغيرة
# ونعرض شاشة الحجب بدلاً منه
if not _has_mobile_access:
    st.markdown(f"""
<style>
/* ── على الجوال: إخفاء كل شيء ── */
@media (max-width: 768px) {{
    #root > div,
    [data-testid="stAppViewContainer"],
    [data-testid="stSidebar"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    section[data-testid="stMain"],
    .main, .block-container,
    header, footer {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    /* إظهار شاشة الحجب فقط */
    #mobile-block-screen {{
        display: flex !important;
    }}
}}
/* ── على الحاسب: إخفاء شاشة الحجب ── */
@media (min-width: 769px) {{
    #mobile-block-screen {{
        display: none !important;
    }}
}}
</style>
<div id="mobile-block-screen" dir="rtl" style="
    display: none;
    position: fixed; inset: 0; z-index: 2147483647;
    background: linear-gradient(160deg, #001a4d 0%, #003a8c 60%, #000d26 100%);
    flex-direction: column;
    align-items: center; justify-content: center;
    font-family: 'Tajawal', Arial, sans-serif;
    text-align: center; padding: 24px;
    box-sizing: border-box;
">
    <img src="{LOGO_DATA_URI}" width="110"
         style="border-radius:14px; margin-bottom:20px;
                box-shadow:0 6px 20px rgba(0,0,0,0.5);">
    <div style="font-size:22px; font-weight:900; color:#ffffff; margin-bottom:6px;">
        السعودية للطاقة
    </div>
    <div style="font-size:12px; color:#7baad4; margin-bottom:28px;">
        نظام إدارة مواد الطوارئ — دائرة شرق منطقة جازان
    </div>
    <div style="
        background: rgba(255,255,255,0.07);
        border: 1.5px solid rgba(255,80,80,0.45);
        border-radius: 18px; padding: 26px 22px;
        max-width: 320px; width: 100%;
    ">
        <div style="font-size:48px; margin-bottom:10px;">🚫</div>
        <div style="font-size:18px; font-weight:900; color:#ff7070; margin-bottom:10px;">
            غير مصرح بالوصول
        </div>
        <div style="font-size:14px; color:#c0d8f5; line-height:1.9; margin-bottom:18px;">
            هذا النظام <b style="color:#fff;">غير متاح على الجوال</b><br>
            لحسابك الحالي.<br>
            تواصل مع <b style="color:#7dd3fc;">مدير النظام</b><br>
            للحصول على الصلاحية.
        </div>
        <div style="font-size:12px; color:#4a7aaa; border-top:1px solid rgba(255,255,255,0.1);
                    padding-top:12px;">
            استخدم الحاسب للوصول إلى النظام
        </div>
    </div>
    <div style="margin-top:24px; font-size:11px; color:#3a6090;">
        جميع الحقوق محفوظة © 2026
    </div>
</div>
""", unsafe_allow_html=True)

# التحقق من صلاحية الجوال: إعادة ضبط الوضع للحاسب إذا لم يكن للمستخدم صلاحية
# إخفاء الفاتورة تلقائياً عند تغيير الصفحة
if st.session_state.prev_page != st.session_state.page:
    if st.session_state.prev_page in ("stock_out","stock_return","stock_transfer"):
        st.session_state.last_inv_html = None
        st.session_state.last_ret_inv_html = None
        st.session_state.last_trans_inv_html = None
    st.session_state.prev_page = st.session_state.page

# ── حقن JS عداد انتهاء الجلسة (تحذير عند 25 دقيقة، إعادة تحميل عند 30) ──
if st.session_state.get('auth', False):
    st.markdown("""
<script>
(function(){
    var TIMEOUT_MS  = 30 * 60 * 1000;   // 30 دقيقة
    var WARN_MS     = 25 * 60 * 1000;   // تحذير عند 25 دقيقة
    var lastActivity = Date.now();
    var warnShown    = false;
    var warnDiv      = null;

    function resetTimer() {
        lastActivity = Date.now();
        warnShown    = false;
        if (warnDiv) { warnDiv.remove(); warnDiv = null; }
    }

    // أحداث النشاط
    ['mousemove','mousedown','keydown','touchstart','scroll','click'].forEach(function(evt){
        document.addEventListener(evt, resetTimer, true);
    });

    function showWarning(secLeft) {
        if (!warnDiv) {
            warnDiv = document.createElement('div');
            warnDiv.id = '_session_warn';
            Object.assign(warnDiv.style, {
                position:'fixed', bottom:'24px', left:'50%',
                transform:'translateX(-50%)',
                background:'linear-gradient(135deg,#92400e,#b45309)',
                border:'1.5px solid rgba(251,191,36,0.6)',
                borderRadius:'14px', padding:'14px 22px',
                zIndex:'2147483647', direction:'rtl',
                fontFamily:'Tajawal,Arial,sans-serif',
                textAlign:'center', minWidth:'280px',
                boxShadow:'0 8px 24px rgba(0,0,0,0.4)',
                color:'#fef3c7', fontSize:'14px', fontWeight:'700',
            });
            document.body.appendChild(warnDiv);
        }
        var mins = Math.floor(secLeft/60);
        var secs = secLeft % 60;
        warnDiv.innerHTML =
            '<div style="font-size:22px;margin-bottom:6px;">⚠️</div>' +
            '<div style="font-size:15px;font-weight:900;color:#fde68a;margin-bottom:4px;">' +
                'تنبيه: سيتم تسجيل خروجك قريباً' +
            '</div>' +
            '<div style="font-size:13px;color:#fcd34d;">' +
                'المتبقي: <b>' + mins + ':' + (secs<10?'0':'') + secs + '</b>' +
            '</div>' +
            '<div style="font-size:12px;margin-top:6px;color:#fbbf24;">' +
                'تحرك أو اضغط لإبقاء الجلسة نشطة' +
            '</div>';
    }

    setInterval(function(){
        var elapsed = Date.now() - lastActivity;
        var remaining = TIMEOUT_MS - elapsed;

        if (elapsed >= TIMEOUT_MS) {
            // انتهت المدة — إعادة تحميل لتشغيل Python logout
            window.location.reload();
        } else if (elapsed >= WARN_MS) {
            showWarning(Math.ceil(remaining / 1000));
        } else {
            if (warnDiv) { warnDiv.remove(); warnDiv = null; }
            warnShown = false;
        }
    }, 1000);
})();
</script>
""", unsafe_allow_html=True)
if not st.session_state.auth:

    _qpu = st.query_params.get("_lu", "")
    _qpp = st.query_params.get("_lp", "")
    _qpr = st.query_params.get("_lr", "")
    _err = ""
    _rok = False

    if _qpu and _qpp:
        _res = pd.read_sql("SELECT * FROM users WHERE username=? AND password=?",
                           conn, params=(_qpu, _qpp))
        if not _res.empty:
            st.session_state.auth = True
            _row = _res.iloc[0]
            st.session_state.user_info = {
                "username":      str(_row["username"]),
                "full_name":     str(_row["full_name"]),
                "role":          str(_row["role"]),
                "mobile_access": int(_row["mobile_access"]) if "mobile_access" in _row.index else 0,
                "position":      str(_row["position"]) if "position" in _row.index else "",
            }
            st.query_params.clear()
            st.query_params["_u"] = _qpu
            st.rerun()
        else:
            _err = "بيانات الدخول خاطئة"
            st.query_params.clear()

    if _qpr:
        c.execute("INSERT INTO access_requests (phone,status,request_time) VALUES (?,?,?)",
                  (_qpr, "معلق", now_mecca().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        _rok = True
        st.query_params.clear()

    if st.session_state.get("session_expired"):
        _err = "انتهت الجلسة — سجّل الدخول مجدداً"
        st.session_state["session_expired"] = False

    _smsg  = _err or ("تم إرسال طلب تصفير كلمة المرور" if _rok else "")
    _sshow = "block" if _smsg else "none"
    _scls  = "err" if _err else "ok"
    # ── CSS: إخفاء عناصر Streamlit الزائدة ──
    st.markdown("""
<style>
[data-testid="stHeader"],[data-testid="stToolbar"],
[data-testid="stDecoration"],footer,header,#MainMenu {
    display:none !important;
}
section[data-testid="stSidebar"] { display:none !important; }
[data-testid="stAppViewContainer"]>.main>.block-container {
    padding:0 !important; max-width:100% !important;
}
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"]>.main,
.stApp { background:#020810 !important; }
</style>
""", unsafe_allow_html=True)

    _LOGO  = "/9j/4AAQSkZJRgABAQAAAQABAAD/4gHYSUNDX1BST0ZJTEUAAQEAAAHIAAAAAAQwAABtbnRyUkdCIFhZWiAH4AABAAEAAAAAAABhY3NwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAA9tYAAQAAAADTLQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAlkZXNjAAAA8AAAACRyWFlaAAABFAAAABRnWFlaAAABKAAAABRiWFlaAAABPAAAABR3dHB0AAABUAAAABRyVFJDAAABZAAAAChnVFJDAAABZAAAAChiVFJDAAABZAAAAChjcHJ0AAABjAAAADxtbHVjAAAAAAAAAAEAAAAMZW5VUwAAAAgAAAAcAHMAUgBHAEJYWVogAAAAAAAAb6IAADj1AAADkFhZWiAAAAAAAABimQAAt4UAABjaWFlaIAAAAAAAACSgAAAPhAAAts9YWVogAAAAAAAA9tYAAQAAAADTLXBhcmEAAAAAAAQAAAACZmYAAPKnAAANWQAAE9AAAApbAAAAAAAAAABtbHVjAAAAAAAAAAEAAAAMZW5VUwAAACAAAAAcAEcAbwBvAGcAbABlACAASQBuAGMALgAgADIAMAAxADb/2wBDAAUDBAQEAwUEBAQFBQUGBwwIBwcHBw8LCwkMEQ8SEhEPERETFhwXExQaFRERGCEYGh0dHx8fExciJCIeJBweHx7/2wBDAQUFBQcGBw4ICA4eFBEUHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh4eHh7/wAARCAFKAUoDASIAAhEBAxEB/8QAHQABAAEFAQEBAAAAAAAAAAAAAAYBAgQHCAMFCf/EAFMQAAEDAwIDAwcGCAkJCQEAAAABAgMEBREGIQcSMUFRYQgTNXFzgbEUIjKRodIVI0JSk5Sy0RYXJCdiY5KzwTNDRVZkcnSChBhEdYOFosLD0/D/xAAbAQEAAgMBAQAAAAAAAAAAAAAABAYDBQcBAv/EADcRAAICAQIDBgMHAwQDAAAAAAABAgMEBREGITESE0FRYXEikdEUFTKBobHBIyRTMzVDgkJSYv/aAAwDAQACEQMRAD8A7LAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABR3Qh1x9IVHtXfFSYu6EOuPpCo9q74qATIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFHdCHXH0hUe1d8VJi7oQ64+kKj2rvioBMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUd0IdcfSFR7V3xUmLuhDrj6QqPau+KgEyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABR3Qh1x9IVHtXfFSYu6EOuPpCo9q74qATIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFFUZAKKpai7Jup8fU+pLRpu3urbvWsp4+jE6uevc1OqqaM1pxuvdc+Sn05Ttt1P0SeVEfM7xx0b9pscHSsnOf9KPLz8DUahrWLgf6sufkup0TLMyJOaSRrGp2uXCGG++WhjuV92oWu7lnan+Jxld7zerrI59zu1bWK7r52dzkX3dPsPkOij6cif2S1U8Eykk52/JFbnxmm/gr5e53TT3GjqMLBWU8qL05JEX4KZSOVe04Lj5oJPOU8r4Xp0dGqtX60JJYuIOs7I5vyHUNarG/wCbnd51n1OyL+Bb0t6rE/dbfUz08YVt/wBStr2O0clUz3mk+DvF666q1FDYLvbads0kb3tqYHK1Pmpndq56+Cm6m779Cn5+BfgW91ctmWjCzasyvvKnyLwUQqRCYAAAUd0IdcfSFR7V3xUmLuhDrj6QqPau+KgEyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUtV3gAUd1IZxM13QaQt/ZUXCVPxFOi7r4r3IZnEXVtLpWyOqpESSpk+bTw53e79ydqnMN7uNdeLpPcbjMs1RMuXOXoidiInYidxutI0xZUu3Z+FfqVDiXiKOBHuKedj/Q8dSXq56iub7jdap887tmpn5kadzU7EPkK1N99zLe3uTY8ntb2IuTo2M4VRUYLZI5dK+dsnOb3bMR7Tyc0y3NweTk8DZ12mSMjFc083N3MlyHk5u5OrsM0ZE+8nLbixQ/8PN+ydZtOTvJ1T+dei9hN+ydYtOVcavfUf+qOm8Jv+yfuVQqUQqVMtIAABR3Qh1x9IVHtXfFSYu6EOuPpCo9q74qATIAAAAAAAoq7AFQQ/iZrqj0NbqasrKOoq/lMqxRsiVqYVGquVVewili48aWrqhsFxpq218y487K1Hxp61auUTxVCfTpeXfV31dbcfNGvt1TFpt7qyaUjbYMS31tNX0kdXR1EdRBI3mZJG5HNcneimT2ECW8XsyfGSkt0XAAHoAAAAAAAAAAAAAAAALVXcAq7oYF6uNLarbNX1kiRwwsVzlVTLV3zVwqoaO41apW53BbHRSZpKV2Zlau0knd6k+Jnx6O+mo+BpNe1iGl4jtf4uiXmyD641DV6mvktxqeZrM8sEWdo2dieteqnwHtzsqbqZTmb5PN7crlepdcaUa0ox6I4ZdlWZFjtse7ZhvYeLmmY9p4vabWq0+ozMR7Txc0y3tPJ7TYVWkiMjEe0se3cyHNPN7dzY12meMic+TumOK1F7Cb9k6tacq+T0mOKdF7Cb9k6qTqc14we+of9UdS4Qe+C/dlUKhAVctYAABR3Qh1x9IVHtXfFSYu6EOuPpCo9q74qATIAAAAABS13RcFylp4waS8rB2NPWbbP8td/dqc5yPRE3Q6J8rVcacsq/wC3O/u1ObZ5Njr3B/PTY+7/AHOYcRx31CXsiacMeI900RdG+ac+ptT3fyijc7bHa5nc77F7TrnTd6t+obNS3e1TtnpKhqPY5vVO9FTsVOiopwPK/KLvjBsTyf8AiY7Rmom2y5Tr+Aq+RElzukEi7JIncnYvhv2ELijh6ORB5NEdprqvNfU2WgapOiXc2P4X+h2VzJ3hFRVPKKRsrGvjcjmuTKKm6Khe36XVOhy8vie5eAAegAAAAAAAAAAAAsVd8F6ny9Q3iislrnuFdKkcUSZ8VXsRE7VU9UXJ7Ix22Rqg5zeyRHuJ+p0sNkdHA9EralFZCn5ve73fE5/c1znK5yqrlXKqvVV7z7mpbtVX67S3Ksy1X7Rx52jb2N//ALtPkvabOhqrkupwPibXnquY3F/BHkvqYb279Dxe3YzJGni5htqbTQwmYbmni5pmOYeL2mzptJMZGI9p4vaZbmnk9psqriRGRhuaeT27mW9p4vbubKq0kRkTXyfW44o0S/1E37J1Mhy9wATHE+j9hL+ydQlB4pl2s7f0R1fg174L92Xp0BRvQqVwtwAABR3Qh1x9IVHtXfFSYu6EOuPpCo9q74qATIAAAAABS0uUtTqePqDRvldLjTVk/wCOd/dqczVDzpfyvttNWP8A45/92pzHUuOvcH/7ZH3f7nN9fW+fL2RiVMndt3nz6ibGVMiqfsqnyaqTC9SzvZmHHr3OpvJh4rtltbdMX2fK0iI2CZ67pH2IvgmyZ7Mp7uj4ZWyNR7MK1UyiovVD8zNN32eyagprnTux5l3z2Z2exdnNX1odd6C19VUNBTTU7/ltsmY17GPdhWov5q9nqOb8Q8O/1Xdjrr4fQ31GsvAaryPwPo/L0N+cxVF2I1YtZWO7Na2OrbDMvWKb5rs/BfcSFkjVTZU9feUeymyt7TWzLRRl03x7Vck0emdypYhX3mMz7lwLfePeBui4KuC33lHKiIoG6K8w5vAx6iohhYss0rGMburnKiInvUgWr+LOnbNG+KhlS51abIyB3zGr/Sd0+rKkjHxL8mSjVHdkXJzaMaPatkkTe9Xeis9vlr7hOyCniTLnvXHuTvU0BqvVlXrS8rOjXw2mlevyaFer3fnu8fDsIpqrVV81ldY0rqheVXYhgZlI4/d3+J92jpY6SljgZ+SmM969qm3z8OGkULvHvbL9F9TkvGPFksiH2ajlF/qeT2J0weL2mY5Ow8XtTJoabjmkJGG9p4vaZjmoeD0Q2lNxKhIxHtPB7DNeiHg9ENpTcSISMR7Txe0zHoeL0NnVciTGRhvYeL27mW9Dyem5sqriRGRMeAiY4nUa/wBRL+ydPHMvAdP5y6Rf6mX9k6aKdxFLtZW/odd4Ke+A/dlzehUo3oVNEXAAAAo7oQ64+kKj2rvipMXdCHXH0hUe1d8VAJkAAAAAAUVCoAI9rPR+n9X0kFLqChWrip5Fkjakr4+VypjOWqnYpFH8DOGTvpaeev8A1s/3zZalMeBIrzMiqPZhNpejZGsxKLJdqcE37GsHcBeFjvpackX/AK+o++eL/J94Sv8ApaXev/qFQn/2G1VRRhT7+8cv/JL5s8WHQukF8jUjvJ14QL85dKSZ/wDEan/9D5eseH9o0da6RunKSWltrXKx0Tpny+bcq5RcvVVwu+2TdqoudkMK+W+G6Wqooahv4uZitXw8fWSMXVMiu2MpzbXq2yDqul1ZeNKtRSfVe5zm1ctRe8z6O9XaiRG0tyq4U/NbKuPqPG50U1vuE9FUNxLC9Wu26+KeC9TGL6oVXxTaTTOQdu7Gm4xbTRIWa21MxERLtIvrYxfihcuutUInpV36Jn3SNPejTFln6mJaXjSf+miStWzF/wAj+ZKJdf6pam11cn/lR/uMaTiHq1Ol3X9DH+4iss3UwpptyVDR8V/8a+R797Zv+V/Ml0vEjWDel4d+hj+6fPrOImsZWK119qGp3sa1i/YiEUmm6mJNL4kyrRsNc+7XyPXquY+TsfzPoXa9XK4uV1fcKqqX+tmc7/HB8iWbHqPOWU+joyx1OqdTUlnpsp552ZHp+QxN3O+o2bhRh0uxpKKMMI25Vqi222bP4DaEp7tRVF/u8L3QvVYqRuVbn85+31fWbX/i/wBN4wtJJ+ld+8+7ZbdTWq101upGJHBTxpHG1E6IiGcca1TOln5Mrp/l6LwOpYnDuDXTGNtcZSS5toiX8Xume2kk/TP/AHlF4d6XX/uUn6Z/7yW5K+8gL0JP3Hpy/wCGPyRD14caUXrQyfp3/vKLw20mvWgf+nf+8mOSmfUfSnJdD6+5NO/wx+SIavDTSK/6Of8Ap5PvFP4sdHr/AKNf+sSfeJmD6V1i8T37k0//AAx+SIWvC/Rq9bY79Yk+8Wrwt0Wv+i3L/wBTJ94m23eNu9D6+0Wr/wAmPubA/wAMfkiELwq0UvW1P/WZfvFv8VOh162l/wCtS/eJzsURWr0U9+1Xf+zPVpGB/ij8kRbT+gNL2G5suVrtzoapjVa16zyOwi9dlVUJU3oveE8C7cxTslY95PdkyjHqoj2aopL0DSoQHyZwAACjuhDrj6QqPau+Kkxd0IdcfSFR7V3xUAmQAAAAAAAAAAAAAABY9MoXlHJntDBrXi9p9JYG3ylZ8+JvLUInazsd7unqU1TLIiZxsdNVFPHPE6KVqPY9qtcipsqL2HPnEfTk+mrurWtctDMqup5PDtaq96fAuHDuepL7PY+fh9DnXFmjuMvtda5Pr9SOTTZ7TElmxvk85pk71MKabxLxXUUbbnses03Xcwppl33POaXxMSWXxJ1dR9bHpLL4mHLKWSSrlTFlfvglwgkZIw3LpJOu+PE6c8n7RLtO6e/DFwhRtyuDUcrXJ86KPqjfBV6r7jW3k/cPX6gurNR3aFyWukfmBjk2qJE+LWr9u3edORsREVE6HO+LtaVj+x0vkvxfT6l/4Y0dw/urV7fUNyiJncw7vcqG12+auuNRHTU0LVc+R64REM3lXvOafKT1LPW6rTT0cipR0LWve1F2klcmcr6k2Kro+my1LJVK5Lq35Isur6itPx3a1u/BEh1Tx8hindBpu0LUMRcJUVSqxrvU1N8etU9REKjjdrmSTmidbYU/N+S8yfapBtM2O5aivEVqtUHnamXKplcNa1OrlXsQ2tQ+T/dXxI6s1DSxSKm7IoHOx71VMl8uwdB0xKu9Jy9d2/0KPVma1qLc6W9vTkjDtnHrUkD2/hG1W+sZ+VyK6Jy+rqhs/h7xWser69lsjpaujuDmK5IpG8zVRE3w9NtvHBrC7cBdTU7HOt9zoK7HRj+aJy/FCzg3pq/ae4sUUV4tNTSL5iZEc5uWO+Z2OTZfrNZqOLoeRiztxWlJLdLf+GbDBytYoyIV5Cbi34r+TpVfWeNVUwU1M+oqJWRQsRXPe9cIiJ1VVPVVwnchzJx617UXy9z2G21Dm2qkfySqxcefkTrnvanYVbSdKt1K/uocl4vyRZ9V1OGn095Lm/BE31hx2tdFLJTaeolucjVx597uSL3drk+ogVZxx1vNKroFttO3salMr8e9VNfWa03C83GK32qkkqaqX6LGfaq9yeKm1LVwEv8AUQMkr7xQ0jlTeNkbpFT37IXyzTdC0uKjkbOXru38kUiGfrGoycqd9vTkjHtPHbVVPI38I0Fvro8/O5WLE7HhhVT60Nv8O+Jen9YIlNTvfR3BEy6knxzL3q1ejk9X1GjtZcH9Uado310L4bpSxoqyLTorXtTv5V6+41/R1VRR1MVZSTvhqIXo+ORi4VqofFmg6VqlLswns15fyjJXrOp6dco5XNev8M7qauVLyFcH9XJq/ScVZLypWwr5qqan56J1TwXqTQ5zkY88e2VU1zXI6DjXwyKo2w6MqAgMJnAAAKO6EOuPpCo9q74qTF3Qh1x9IVHtXfFQCZAAAAAAAAAAAAAAABQAAfI1JZaG/W2a3V8XPE/oqLuxU6ORexUPrlMJnofUZShJSi9mj4srjZFxmt0zlniBpO66UrVbUtWajeuIaprV5XJ3L+a7w+rJDZZdztC4UVLX0klLWU8U8MjcPZI1HNVPUam1bwQtdc909hrpLa92/mJE85H7u1PtL5pPFdaioZa2fn9Tn2qcJWKTnivdeRz7LL4mLLKbLuXBDXEL1SD8HVadisqOX9pELKHgXrepeiVUlsomZ3c+dXqiepqLn60LZHiDTFHtd6v5+RoY6Dn9rbumaulkVenQ2Rwi4WXDVlQy53WOSksjVzlUw+p/ot7m97vqNp6J4IacskkdXeJn3mrZujZGcsLV7+T8r3qpteKNkbGxxsa1rdkREwiIVXWuMlZF04XL/wCvoWnSuFnGSsyvl9Twt1HTW+ihoqOFkFPCxGRxsTCNanREMppVETuKohz9tt7su8YqK2RRehyNx1t0lv4nXTznNipc2oY5Uwio5Oz1KmDrpTX3Fvh7T63tzXxyMprpTIvyeZU2VF6sd/RX7FN9w7qUNPzFOz8L5M0fEOnzzsXs1/iT3OfOFGrYtHasbc6mndNSSxrDMjPpNRVRUVO/dE2On9N600xqCFklsvNHK5yf5NZEbIn/ACrhTkzU+k9Q6bqXw3e2TwNau0yN5onJ3o5Nj4najkxnsVC86loWJrMvtFVmz9OaKXp2tZOkp0zhy8nyZ3c1Wu6fX3leVM5RDjKwa21VYXMfbb7Vxsb0ikeska+HK7O3qwb34T8WqbVE7LPeY2UV1cn4pzF/FT+rPR3gUzUuF8vBi7F8UV4r6Fu0/iTFzJKuS7Mn5/UmXEu8LYdD3W5NdyyR07kjX+muzftU41VznLl6q5yrlVXtXO6nU/lFuc3hfWNZ0fLEjl8OZFOWMJhUxnJauB6YrFnZ4t7fIrfF90pZUYPol+5035Oemae16MZeZIWrWXH56vVN0jTZqJ8febSRERFwi7nEdPf79BA2GC+3WGNiYayOtka1qdyIjsIXrqPUadNR3n9fl+8RM7hDKy8id0rVzfqSMHijHxKI1RrfL2+Z2w9rXIqOblFToqHIvGmxwWHiFXU1KzzdPNiojYibN5uqJ4ZyfB/hJqT/AFjvP6/L94wq2rq62bz9dWVFVLjl85PK6R2O7LlVcGx0Dh3I0vIdkrE4tbbEDWtdp1GpQjW00+ptjyXbpJT6srrW534uqpvOcv8ASYvX6lOkW5VNzlTydGvdxRpVai8raaZXf2TqpE7ipcX1xhqTa8UmWjhScpYCT8Gy5CpRv+JUrBZwAACjuhDrj6QqPau+Kkxd0IdcfSFR7V3xUAmQAAAAAAAAAAAAAAAAAAAAKKmxbyrkvAPGty1UXPRRguB4elmFz0Kom/QuB6AAACh5uciIuT1U0fxO4n33R3EWa3wQ09bb/Mxv8xInK5qqi5Vrk6e/JNwdPuz7HVSt5bbkLOzqsKtWW9N9jc8sUc7Fa9jXovVrkRUUi1+4baMvSPWqsNKyV26ywJ5p+e/LcZ9+SJ2bjtpWqY1LlSV9uk7cxpKz629nuJA3i7w+c3m/hDE3bOFhkz+ySPsGpYk/hhJP03/ghvO03Kj8U4teu38mmOL3CyTSFMl2ttQ+qtjno17ZP8pCq9MqnVPHsNbUtRNS1EdVA9Y5oXpIx7V3RyLlFNzca+Kdpv8AY32DTyyzsmeiz1LmKxvKm+Gou65XBpVGueqMYmVVcNRO1Tp2hTy7cF/bVz59eu3qc81iGNXmf2j5enn6HUmulm1VwLmq2NRZpqGOpVqb5VuHKifUpy0m6JvjPadn6Kta0OiLbaqqNMto2RysXvVu6fact8UdJT6R1VUUT2L8ilVZKOTGzmZ+j629DQ8I59ULbcXfq20bnibDslVVkteGzNpcGtFaC1Vo2GsrbLHLXwqsVUvyiVF5k7cI7bKE3ThBw8VMpp9n6xN985y4d6xuejLutbRfjaeTDaimc7DZE789jvE3/YuNWia6ma+srJbbMv0o6iJy4XwVqKimt13TtTx8iU6nKUG91s3y9Cdoubpt1EYXKKkvPbmZ38UHD3/V9n6xL98p/FDw8Trp9n6xL98trOMOgKeNXNvaTuT8mKCRVX60QhmpOPtG1jorBZ5p35+bLVu5Gp48qfOX7DV4+JrGQ9oqf5tr9zZX5OjUreXZ/LZmytMaB0npu4LX2S1MpalzFZzpK93zV8HOVCUoip0QgPA/Ut11XpiW6XeWJ861L2tSOPla1E7ET9+VNgGqzYXV3Srue8lyfibfBlTOmM6VtFhAARSYAAAUd0IdcfSFR7V3xUmLuhDrj6QqPau+KgEyAAAAAAAAAAGQABkZAAGRkAAAAADIAAyUAKgAAAZGQApoTjjw31PfNUSX6zwQ1cLomsWJsvLIitTfZcIvuU32WOJ2n6jdp93fVdfUgahgVZ1XdWdDiW56b1FbZFjr7HcqdUX8qncqfWiYPm+ZlR3L5mXm7uRc/Ud1cjVxzIi+ClPk8Oc+Zj/soW2vjq5L46k37lWnwZBv4LeXscVWfS+pLtKkVusdxnVe1IFa3+0uEN08J+DktruEN81QsL54V54KNi8zWuTo569qp3JsbtVjU2a1ETuxsVwnYmPUa3UuLMvMg64pRT8uvzNhgcL42LNWTbk18iqMRUPh6z0radVWd9uu0HnGZ5o3ouHxO/OavYp95OhR/QrNdk6pKcHs0WSyqFsXCa3TOWNY8G9VWSWSW2Q/hijTdqw7Sonizv8AVk1/V2240T1ZWW+rp1bsqSQObj60O5cbdnqLVijenz42u9aZLficaZVUVG2Kl69GVPJ4Qx7JdqqTj+pwxDS1M7uWnpZ5VXsjic74ISSwcPNZXpzUpLBVMY7/ADtQnmmJ/a3+w7DbBE36MUaepqFWtx2GW/jjIktq60n77/QxU8G1J/1LG17bEN4O6SrNH6WS2V9RBPO6V0rlhzytz2ZXqTcsam5eU7IvnkWytn1fUt+PRCitVw6IAAwmYAAAo7oQ64+kKj2rvipMXdCHXH0hUe1d8VAJkAAAAAAAM7AFknTuIddtd0Nu1g7TclvuEkyUb6rz0ceWKjWq7lTtVcJ9eEJhM5Gs5nLhE3z3GsddcXNK2RlTTUNUtwuDWOa1KZiPYx2Nsu2bsuNkUl4eNPIn2YQcvYg52TGiHac1El2hdTU+rtPRXmkpKmlje9zPN1DcOy31bKnqPg3XWmoaS73+kg0bX1MNtp/O00yKuKt2U2TbxVdsrsuxj8HtV3G88Pqq/XuSKWanmlysUaMTlY1F6J61IXZabiRxDoptUUmqFstI+RyUVLGqo3DVxvjs7FVcrlF26E6vAUbbFbsoxe3Nvr5cuprrdRlKqt1buUlvy26G49N3Opuem6W6V9vlt080XnJKaT6Ua77b+owdDawtesaOqqrUypYymmWF/no0avN3phV2Itwb1ZdL/aLva78qPudpe6GWRET56fOTfG2ctVM9ux8vyXs/wfvWyekF+B8W4Cqruc1zi1tt02Zkp1B22UqL5ST35c90Tqm1rap9cz6PYyq/CEMXnXOWP8XjlR2y564VOwlTeiZU0jQTwU3lNXmeokZFFHb+Zz3uRGtRImZVVXohIqvjXoWnrlpkq6udEXHnoqZzo19S9qeo+bdMtk4qiDe8U349T7x9TrUZO+aW0ml4dDZjumxGL/q+2WbU1r0/VsqVqrnnzLo2Zam+PnLnbqfXsd6tt7tsNwtdVHVU0yZY9i7eOe5TV3FNf569DZTtd+20xYWKrrnXYuif6Lcz52U66VZW+rX6s2NrHUFDpewTXm4NmdTQ4RyRN5nbrjZNjMsVygvFopbpS86Q1MaSMR6YciL3oQnyhV/mruX+9H+2h9/hjleH9jTp/I4/gJ40Fhq/xcmv03EMmbzHT4dlMkuexSN6+1XTaQsrLnVUlVVRumbEjKduXZcvUkm2dyK611vpfS0eLxcGNmVMtp4288rv+VOieK4IuPXKyxRUe16Ik5NirrcnJR9WeWn9bUd41bV6dhoK+GelgbOsk0StaqOwuO9Oqe/JLmeCKaf4b8SK7WHEqqo6ZFis6UyviikiakiOTG6uTPebJ1HqK0aapYai81SU8c8qRRryq7Ll6JsSs3CsouVXY2bS5dSLg5kLqnY5bpPr0Ps9hXYimvtb2fR1tpq+5JUPjqZOSJsLEVVXGVXdU7CzRXEHTGrHLFaq5flLW8ywTMWOTHeiL1T1EdYd7r73sPs+ZIeZQrO67S7XkS5Qh8fVGpbNpu2rX3mtjpYc4bzbucvc1E3VSO6X4q6M1DcmW+iuL46mReWNlRC6Lzi9zVXZV8D2GJfZB2Rg3FeO3ITzKK5quU0m/DcnDk3yU7D4GvNU0GkrDJea6OaWJjmxoyFEVznOXZNzWLeM+papqz23h/Wz0ib8+ZFyngqR4+rJmxdMyMmPbrXLzbS/cw5Op4+NPsTfP0TZu7IT6SdxBOGfES3a0dNS/JZaC40/zpKaRcrjvRdsp3phFQmrayl+VLTJURLPjPm0enMierqRrsa2ibhZHZokUZNV0FOD3TMnBRTwkrqSKVkMtTEyST6DHPRHO9Sdp8TW2rLVpSjp6q6JUebqJmws81HzLzL0z4HzCqdklGK5syTthBOTfQ+1W1DKWlmqJM8kTFe7CZXCJn/A+BpbWNr1FpuW/wBCypbSRK9HJIzlf81N8Jk+nfXtl07WSN6LSvVM9ytU1ZwN24NXDKflVHwJuPiwsx5WS6ppfPc1+TlzrvjCPRpv5GxtC6ptur7W652xtQ2FsjolSZnK7KddtyRGrPJmT+b1Vx1q5f8AA2mYc2mNGROuPRMk4F0r8eNkurAAIpLAAAKO6EOuPpCo9q74qTF3Qh1x9IVHtXfFQCZAAAAAAKW9hcUxseMGqfKXutxt2i6eno5ZIYa2q8zVSMznzfKq4z2IuD4FPNwl01oqolt1Xb6ytkpHNZI5EkqXvVqp0xlm69mMG5r9ZrdfLZJbbrSsqqWVPnRv+xc9UXxQhtr4O6Gt9xZXMtssz43I5jJ53PY1U6Ly9uPHJvcTOx4Yyqsck09/h2+L39jQZuBkWZDshs01tz8PYifk7XGzfxcVNnr6+lhkdUSNljkma1eVzWpnfvwuD5dvtettFpPRaV1fp6os6PdJE2rqWKrEXwXovfhd+uCWX3gbo+5XKWsjWtokkcrlihe3zaKvXlRUXCeGcGB/2f8ASnOjvl9zxnK7x5X/ANpOWZguydnbe03u4uO/8kCWFnKuNfYW8eSkpbfwfK8nOWrra/WFdUOZLLUPYr5IvoPeqyKqt8Fzn1KhkeTXdLbRWm9U9XX00Evy5XckkrWqrcYzuvTJtTSGlrRpWzttdop1ih5uZ7nLzPkcvVzl7VIZqfgppK93aa5ZraSSd6ySMge3kVy9VRFRcd+xHs1DFyrbVY3GMtttlv8Ah5dCRXp2Ti11SglKUd9935mvNQWSk1vxnvLo7zBSWhnmmVVSk7W8+GIisblcOVVTxTY2Q+w8KLRYHwzU9gWmYzEkskjJJFTG682Vdn1Hx18n/Sq4Ra+6Kid7mfdPWj4B6QinR8tTc5WtXPJ5xjUX14bkk35mHZGEVfJRiktlHbp679SNRg5cHKUqYuUm3u35/kfB8nO+WyjuGoLelwjgoFmSaiZUyo1ytyreqr1xy5PXijf7O/jLpGZlfA+KjX+USNkRWR8z0xlc4Tp7iZ6n4RaQvdFRU6UklClEzkiWmVEXlXqjuZF5vX1MS08EtF0NFUwSRVVW6oj835yWVMxp3swiIi9N9+h8LO0+V8smTlu01tsvLbff9TI8HPVEcZRjsmnvv677bHh5QF8s83DWtpoLlSyzTSRtjjZM1zlXmReiL3ITHhpG+PQVka9FRy0Ua49bUVCFWzgPo6krmVEktwqWMdnzL5Gox2/RcNRVTwNrQxMiibHG1GsaiI1qJhEROmDW5t2PHGjj0Ny5tttbfkbPCoyJZMr70ly22T3/ADPn6jqaqisVfWUcXnaiGne+Jn5zkTY0Hwkdw/rKep1BrS6UlTepJnPe24O+Yidcoi7O/wAOmDo5zEc3C7opALtwf0NX3CSufbpIHyO5nsgmcxirnP0U6e7A07LppqnXY3Htbc115eHsfOpYV11sLK0n2d+T6e5rzQ+ptPVPHmuuFHPBS26SlWCBzkSNiq1E78YzhcH2vKJvFtrLXZaCjraeoqH3Fj2sikR/zUTquF26p1Pu624W6HqbEyWWjmoIrdA5UdSLhVYm6o5FRebp1XfxNf6JtvCi23Cw3WN94qpK+ocykZUwpyRyNVEy9ETsVUxuvqNtHIw7bI5UO1vBbbbb77LzNTKnKpg8WfZ2k999/N9NjdtxbYJ6aClviWyTkYipFWebXG2MojjSnF6h0xpy+2a+aOnpILotWiup6ORHMVE/K5WrtvhMJ1ybI19wrses70y7XGqrIpmwpCiRK3GEVVzui96nhpHg7pHT1zjuUbamsqIV5ovlDmqxi9io1qImfWQsHJxsaPeOyTez3jtyfo3v/BOzcbKyX3arSS22lvz/AGIZxTfRV/GGw0eqn+YsfyVr2o5yoxzlVc83cnNhM9xTjhYtHUWlIrrp9ltprhBPHyrRyNy5ue1GruqLhc9UJzxPptAXqop7Fquvhoq7k87TSK/zT2tXZeV6phf91fqNI8RNL6Gs7aek0peJrrdZ5msSON7JGNRe9Wp9LOERMm00ucL3Sm5R7K6JfC157/uarUa5Ud60oy7T6780/Lb9jdWsG2zVnDFbbNdaBayWkjkYr6ln+WRqKnb1yR/hbxNstFoVtLqO4Mpqy2/iFYq8z5Wp9HlROq9nuLbfwB03JRQyVVXcmTujasrUdHhrlTdPo959Kn4EaOjgfHLPdJHuTCPWoRFZ4oiJj6yIrNLjVKmdkmt91tHbbz8fEl91qUrI3QrSe23N9f0Ph8Jqylu/EO965qJaa20c7Vhp4ZZmNe/plyoq5TZE96mNR6lsjPKMqrgtxg+SSU/yZJ+dPN8/Kmyu6dcpk+27yf8ASjlVzq+6KvblzF/+J9+1cIdG0Fkq7YtLNVNq2oks00mZEx05VRERuPBD7uzdO7c5qUnvHspbdF8+Z5Vhah2Ix7KWz7T59X8iC8V9RWVeL2mKplwhkholb8pkjejmx5dtlU+0y/KN1DZ6q0WelpbhT1EqVrZ3JFIj+ViJ1XC7Eo03wY0dZ5pZVhqa5ZGOjRtU9HNaiphcIiImfE8LZwP0ZRXJapzKyqjRV5aeaVFjTPfhEVfep5Xm6bXOqW8v6a8lz3/PkezwtRnCxbR+N79en1JDc9S2BNGzzrdqHkdRLjFQ1VX5ndnJDOB7XN4MVyuaqIq1CovenKez+Aej1qXStqbmyNXZ82krdk7s8uTY1Bp622/Tv4CoYfk9GkSxNaxd0RU3XPaviQLcjEqp7umTl2pJvdbbbE2rGy7be8uiltFrk999yC+TNvw8z/tkvxQ2mR3QOlqLSFl/BNvmnlh846TmmVFdl3qRCRGvzro3ZE7I9GzZ4FMqceNcuqAAIhMAAAKO6EOuPpCo9q74qTF3Qh1x9IVHtXfFQCZAAAAAAAAAAAApgpsXAbAt2CoXAAswhXCY6lwPAWqmxTqXgAt9ZXoVB6CmShcADyla17Fa5qOauyoqZRTGjt1AxIWpQ0rUgXMKNiaiRr3t22X1GcMBNrxPlxT6nnunYilMbJueowD3Yies9C6a1a6N95t3nZo28rJmSOje1vXGU6pnsUxNJcM9I6arW19Bb1fVs+hLUSLIrP8AdzsnuJvgYJCzMhV90pvs+W/IjSwqJWd44rteZY3t2K4LgRyUW4K4Kg82BTHiUVC4DYFuPArgqBsCmEyVAPQAAAAAAUd0IdcfSFR7V3xUmLuhDrj6QqPau+KgEyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABR3Qh1x9IVHtXfFSYu6EOuPpCo9q74qATIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAFHdCHXH0hUe1d8VJi7oQ64+kKj2rvioBMgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAUd0IdcfSFR7V3xUmLuhDrj6QqPau+KgEyAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABR3Qh1x9IVHtXfFSYu6EOuPpCo9q74qAf/9k="

    components.html(f"""<!DOCTYPE html>
<html dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:100%;height:100vh;overflow:hidden;font-family:Tajawal,sans-serif;direction:rtl;background:#020810;}}
canvas{{position:fixed;inset:0;width:100%;height:100%;z-index:0;}}
#ui{{position:fixed;inset:0;z-index:10;display:flex;align-items:center;justify-content:center;padding:20px;pointer-events:none;}}
#card{{
    pointer-events:all;
    width:min(408px,93vw);
    background:rgba(3,10,28,0.90);
    backdrop-filter:blur(22px);-webkit-backdrop-filter:blur(22px);
    border:1px solid rgba(0,140,255,0.20);border-radius:22px;
    padding:28px 26px 20px;
    box-shadow:0 0 50px rgba(0,70,180,0.20),inset 0 1px 0 rgba(255,255,255,0.04);
    text-align:center;
}}
img.logo{{width:82px;height:82px;border-radius:11px;object-fit:cover;display:block;margin:0 auto 10px;box-shadow:0 0 16px rgba(0,140,255,0.40);}}
.t1{{font-size:20px;font-weight:900;color:#ddeeff;letter-spacing:.4px;margin-bottom:2px;}}
.t2{{font-size:13px;font-weight:700;color:#1dda70;margin-bottom:1px;}}
.t3{{font-size:11px;color:#4a7a9a;}}
.sep{{height:1.5px;margin:13px 0 12px;background:linear-gradient(90deg,transparent,rgba(0,140,255,.5) 30%,rgba(29,218,112,.4) 70%,transparent);}}
.lbl{{display:block;font-size:11.5px;font-weight:700;color:#6898c0;text-align:right;margin-bottom:3px;}}
.inp{{
    width:100%;padding:9px 11px;margin-bottom:10px;
    background:rgba(255,255,255,0.07);
    border:1px solid rgba(0,130,255,0.25);
    border-radius:9px;color:#ddeeff;
    font-size:14px;font-family:Tajawal,sans-serif;direction:rtl;outline:none;
    transition:border-color .15s,box-shadow .15s;
}}
.inp:focus{{border-color:rgba(0,160,255,.60);box-shadow:0 0 0 2.5px rgba(0,100,255,.14);background:rgba(255,255,255,.10);}}
.btn{{width:100%;padding:10px;border:none;border-radius:10px;font-size:14px;font-weight:900;font-family:Tajawal,sans-serif;cursor:pointer;transition:all .16s;}}
.bm{{background:linear-gradient(90deg,#004a99,#006adf);color:#fff;box-shadow:0 4px 14px rgba(0,90,220,.30);margin-bottom:7px;}}
.bm:hover{{background:linear-gradient(90deg,#003580,#0055bb);transform:translateY(-1px);}}
.bs{{background:rgba(255,255,255,.05);border:1px solid rgba(0,120,255,.18);color:#6898c0;font-size:12.5px;}}
.bs:hover{{background:rgba(0,70,170,.20);color:#aaccee;border-color:rgba(0,150,255,.32);}}
#st{{display:none;margin:5px 0 3px;padding:7px 10px;border-radius:8px;font-size:12.5px;font-weight:700;}}
.err{{background:rgba(220,40,40,.14);border:1px solid rgba(220,70,70,.28);color:#ff8888;}}
.ok{{background:rgba(29,200,100,.11);border:1px solid rgba(29,200,100,.26);color:#1dda70;}}
.ft{{margin-top:13px;padding-top:10px;border-top:1px solid rgba(0,140,255,0.18);font-size:12px;color:#7aaac8;letter-spacing:0.3px;}}
</style></head><body>
<canvas id="c"></canvas>
<div id="ui"><div id="card">
  <img class="logo" src="data:image/png;base64,{_LOGO}" alt="logo">
  <div class="t1">السعودية للطاقة</div>
  <div class="t2">نظام إدارة مواد طوارئ</div>
  <div class="t3" style="font-size:12px;font-weight:700;color:#c8e0f4;margin-top:2px;">دائرة شرق منطقة جازان</div>
  <div class="sep"></div>
  <div id="st" class="{_scls}" style="display:{_sshow}">{_smsg}</div>
  <label class="lbl">📱 رقم الجوال</label>
  <input class="inp" id="usr" type="text" placeholder="أدخل رقم جوالك..." autocomplete="username">
  <label class="lbl">🔑 كلمة المرور</label>
  <input class="inp" id="pwd" type="password" placeholder="••••••••" autocomplete="current-password"
         onkeydown="if(event.key==='Enter')login()">
  <button class="btn bm" onclick="login()">تسجيل الدخول</button>
  <button class="btn bs" onclick="reset()">📩 إرسال طلب إعادة تعيين كلمة المرور</button>
  <div class="ft">
    <span style="color:#a0c8e8;font-weight:700;">تطوير:</span>
    <span style="color:#c8e0f4;font-weight:700;"> أحمد سعيد عواجي</span>
    <br>
    <span style="color:#5a8aaa;">جميع الحقوق محفوظة لصيانة أعطال دائرة شرق منطقة جازان © 2026</span>
  </div>
</div></div>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
let W,H,t=0;
function rsz(){{W=cv.width=innerWidth;H=cv.height=innerHeight;}}
addEventListener('resize',rsz);rsz();
const LS=[
  [.18,.07,1.4,.80, 0,180,255,2.5,.90],
  [.27,.05,1.8,1.10, 0,220,255,1.5,.72],
  [.37,.08,1.2,.70,29,200,150,2.0,.85],
  [.47,.06,2.0,1.30, 0,160,255,1.8,.75],
  [.55,.04,2.4,1.50,29,230,160,1.2,.65],
  [.63,.09,1.0,.60, 0,200,255,3.0,.95],
  [.72,.05,1.6,1.00,29,170, 96,1.5,.70],
  [.14,.04,2.2,1.80, 0,140,220,1.0,.55],
  [.82,.06,1.3,.90, 0,180,255,1.8,.60],
];
const PS=Array.from({{length:90}},()=>({{x:Math.random(),y:Math.random(),
  vx:(Math.random()-.5)*.0003,vy:(Math.random()-.5)*.0002,
  r:Math.random()*1.4+.3,a:Math.random()*.32+.08,ph:Math.random()*6.28}}));
function bg(){{
  const g=ctx.createRadialGradient(W*.5,H*.38,0,W*.5,H*.38,W*.72);
  g.addColorStop(0,'#001842');g.addColorStop(.5,'#000c22');g.addColorStop(1,'#020810');
  ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
}}
function wy(yf,af,fr,sp,x){{
  const n=x/W,p=t*sp,amp=H*af,y0=H*yf;
  return y0+amp*(Math.sin(fr*6.28*n+p)+.35*Math.sin(fr*10.68*n+p*1.3)+.15*Math.sin(fr*19.47*n+p*.7));
}}
function line(yf,af,fr,sp,r,g,b,lw,op){{
  [3.5,2,1].forEach((m,i)=>{{
    ctx.beginPath();ctx.moveTo(0,wy(yf,af,fr,sp,0));
    for(let x=4;x<=W;x+=4)ctx.lineTo(x,wy(yf,af,fr,sp,x));
    ctx.strokeStyle=`rgba(${{r}},${{g}},${{b}},${{op*(i*.055+.042)}})`;
    ctx.lineWidth=lw*m*2.2;ctx.lineCap='round';ctx.stroke();
  }});
  const gr=ctx.createLinearGradient(0,0,W,0);
  gr.addColorStop(0,`rgba(${{r}},${{g}},${{b}},0)`);
  gr.addColorStop(.07,`rgba(${{r}},${{g}},${{b}},${{op}})`);
  gr.addColorStop(.93,`rgba(${{r}},${{g}},${{b}},${{op}})`);
  gr.addColorStop(1,`rgba(${{r}},${{g}},${{b}},0)`);
  ctx.beginPath();ctx.moveTo(0,wy(yf,af,fr,sp,0));
  for(let x=4;x<=W;x+=4)ctx.lineTo(x,wy(yf,af,fr,sp,x));
  ctx.strokeStyle=gr;ctx.lineWidth=lw;ctx.stroke();
  for(let n=.07;n<.95;n+=.14+Math.sin(t*.4+n*9)*.025){{
    const x=n*W,sy=wy(yf,af,fr,sp,x),v=(Math.sin(t*2.5+n*18)+1)/2;
    if(v>.58){{
      const sz=v*4,sg=ctx.createRadialGradient(x,sy,0,x,sy,sz*4);
      sg.addColorStop(0,`rgba(255,255,255,${{v*.88}})`);
      sg.addColorStop(.4,`rgba(${{r}},${{g}},${{b}},${{v*.52}})`);
      sg.addColorStop(1,'rgba(0,0,0,0)');
      ctx.beginPath();ctx.arc(x,sy,sz*4,0,6.28);ctx.fillStyle=sg;ctx.fill();
    }}
  }}
}}
function pts(){{
  PS.forEach(p=>{{
    p.x+=p.vx;p.y+=p.vy;
    if(p.x<0)p.x=1;if(p.x>1)p.x=0;
    if(p.y<0)p.y=1;if(p.y>1)p.y=0;
    const pl=(Math.sin(t*1.4+p.ph)+1)/2;
    ctx.beginPath();ctx.arc(p.x*W,p.y*H,p.r,0,6.28);
    ctx.fillStyle=`rgba(80,160,255,${{p.a*(.25+pl*.75)}})`;ctx.fill();
  }});
}}
(function fr(){{t+=.018;bg();pts();ctx.globalCompositeOperation='screen';LS.forEach(l=>line(...l));ctx.globalCompositeOperation='source-over';requestAnimationFrame(fr);}})();
function base(){{
  try{{
    var u=parent.location.href||window.location.href;
    return u.split('?')[0];
  }}catch(e){{
    return window.location.href.split('?')[0];
  }}
}}
function login(){{
  var u=document.getElementById('usr').value.trim();
  var p=document.getElementById('pwd').value;
  if(!u||!p){{show('أدخل رقم الجوال وكلمة المرور',1);return;}}
  var url=base()+'?_lu='+encodeURIComponent(u)+'&_lp='+encodeURIComponent(p);
  try{{parent.location.href=url;}}catch(e){{window.location.href=url;}}
}}
function reset(){{
  var u=document.getElementById('usr').value.trim();
  if(!u){{show('أدخل رقم جوالك',1);return;}}
  var url=base()+'?_lr='+encodeURIComponent(u);
  try{{parent.location.href=url;}}catch(e){{window.location.href=url;}}
}}
function show(m,e){{const s=document.getElementById('st');s.textContent=m;s.className=e?'err':'ok';s.style.display='block';}}
document.getElementById('usr').focus();

// تكبير الـ iframe من الداخل عبر parent
try {{
  const iframes = parent.document.querySelectorAll('iframe');
  iframes.forEach(f => {{
    if (f.contentWindow === window) {{
      f.style.cssText = 'width:100vw!important;height:100vh!important;position:fixed!important;top:0!important;left:0!important;border:none!important;z-index:9999!important;margin:0!important;';
      f.parentElement.style.cssText = 'overflow:visible!important;position:static!important;';
    }}
  }});
  const style = parent.document.createElement('style');
  style.textContent = '[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],footer,header,#MainMenu,section[data-testid="stSidebar"]{{display:none!important;}} [data-testid="stAppViewContainer"]>.main>.block-container{{padding:0!important;max-width:100%!important;}} .stApp{{background:#020810!important;}}';
  parent.document.head.appendChild(style);
}} catch(e) {{}}
</script></body></html>""", height=750, scrolling=False)


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
            <span style='font-size:13px; color:#555;'>الموظف:<b>{u['full_name']}</b></span><br>
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
            if st.button("📊 رصيد المستودعات"): st.session_state.page = "inventory_status"; st.query_params["_pg"] = "inventory_status"
            st.divider()
            st.sidebar.markdown("<p style='text-align:center; font-weight:bold; color:#004a99; margin:0;'>عمليات الصرف والارجاع ونقل المواد</p>", unsafe_allow_html=True)
            if st.button("🛒 صرف مواد للمقاول"): st.session_state.page = "stock_out"; st.query_params["_pg"] = "stock_out"
            # عدد طلبات الارجاع المعلقة
            pending_ret_count = int(pd.read_sql("SELECT COUNT(*) as cnt FROM return_requests WHERE status='معلق'", conn).iloc[0]['cnt'])
            if pending_ret_count > 0:
                st.markdown(
                    f"<div class='ret-btn-wrap'><span class='ret-badge'>{pending_ret_count}</span></div>",
                    unsafe_allow_html=True)
            if st.button("📤 طلبات الارجاع", key="ret_btn_user"): st.session_state.page = "return_requests_user"; st.query_params["_pg"] = "return_requests_user"
            # طلبات الغاء الفواتير
            pending_cancel_count_user = int(pd.read_sql("SELECT COUNT(*) as cnt FROM cancel_invoice_requests WHERE status='معلق'", conn).iloc[0]['cnt'])
            if pending_cancel_count_user > 0:
                st.markdown(
                    f"<div class='ret-btn-wrap'><span class='ret-badge'>{pending_cancel_count_user}</span></div>",
                    unsafe_allow_html=True)
            if st.button("🚫 طلب إلغاء فاتورة", key="cancel_inv_btn_user"): st.session_state.page = "cancel_invoice_user"; st.query_params["_pg"] = "cancel_invoice_user"
            st.divider()
            if st.button("✏️ تعديل فاتورة سابقة"): st.session_state.page = "edit_invoice"; st.query_params["_pg"] = "edit_invoice"
            if st.button("🗂️ أرشيف فواتيري"): st.session_state.page = "my_invoices"; st.query_params["_pg"] = "my_invoices"
            st.divider()
            if st.button("📞 أرقام التواصل"): st.session_state.page = "contacts_page"; st.query_params["_pg"] = "contacts_page"

        # ── موظف مستودع: كل شيء إلا التحكم بالنظام ──
        elif role in ("موظف مستودع", "أمين مستودع"):
            if st.button("📊 رصيد المستودعات", key="sb_inv_wh"): st.session_state.page = "inventory_status"; st.query_params["_pg"] = "inventory_status"
            if st.button("📑 تعريف مواد جديدة", key="sb_defs_wh"): st.session_state.page = "item_defs"; st.query_params["_pg"] = "item_defs"
            if st.button("⚠️ تنبيهات نقص مواد", key="sb_alerts_wh"): st.session_state.page = "alerts_page"; st.query_params["_pg"] = "alerts_page"

            # ═══ قسم: الصرف وتغذية المستودع ═══
            st.divider()
            st.sidebar.markdown("<div class='sb-section-stock'>📦 الصرف وتغذية المستودع</div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-btn-stock'>", unsafe_allow_html=True)
            if st.button("📥 إضافة مواد إلى المستودع", key="sb_stockin_wh"): st.session_state.page = "stock_in"; st.query_params["_pg"] = "stock_in"
            if st.button("🛒 صرف مواد للمقاول", key="sb_stockout_wh"): st.session_state.page = "stock_out"; st.query_params["_pg"] = "stock_out"
            if st.button("🚛 نقل مادة من مستودع إلى آخر", key="sb_transfer_wh"): st.session_state.page = "stock_transfer"; st.query_params["_pg"] = "stock_transfer"
            st.markdown("</div>", unsafe_allow_html=True)

            # ═══ قسم: الطلبات ═══
            st.divider()
            st.sidebar.markdown("<div class='sb-section-requests'>📋 الطلبات</div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-btn-requests'>", unsafe_allow_html=True)

            pending_ret_wh = int(pd.read_sql("SELECT COUNT(*) as cnt FROM return_requests WHERE status='معلق'", conn).iloc[0]['cnt'])
            if pending_ret_wh > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{pending_ret_wh}</span></div>", unsafe_allow_html=True)
            if st.button("🔄 طلبات الارجاع", key="sb_ret_wh"): st.session_state.page = "return_requests_admin"; st.query_params["_pg"] = "return_requests_admin"

            pending_cancel_wh = int(pd.read_sql("SELECT COUNT(*) as cnt FROM cancel_invoice_requests WHERE status='معلق'", conn).iloc[0]['cnt'])
            if pending_cancel_wh > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{pending_cancel_wh}</span></div>", unsafe_allow_html=True)
            if st.button("🚫 طلبات إلغاء الفواتير", key="sb_cancel_wh"): st.session_state.page = "cancel_invoice_admin"; st.query_params["_pg"] = "cancel_invoice_admin"

            try:
                _pend_signed_wh = int(pd.read_sql("SELECT COUNT(*) as cnt FROM signed_invoices WHERE status='بانتظار الاعتماد'", conn).iloc[0]['cnt'])
            except Exception:
                _pend_signed_wh = 0
            if _pend_signed_wh > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{_pend_signed_wh}</span></div>", unsafe_allow_html=True)
            if st.button("✍️ اعتماد فواتير المقاول", key="sb_approve_wh"): st.session_state.page = "approve_signed_invoices"; st.query_params["_pg"] = "approve_signed_invoices"
            st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            if st.button("🛠️ سجل العمليات التفصيلي", key="sb_logs_wh"): st.session_state.page = "view_logs"; st.query_params["_pg"] = "view_logs"
            if st.button("✏️ تعديل فاتورة سابقة", key="sb_edit_wh"): st.session_state.page = "edit_invoice"; st.query_params["_pg"] = "edit_invoice"

            # ═══ قسم: الفواتير ═══
            st.divider()
            st.sidebar.markdown("<div class='sb-section-invoices'>📑 قسم الفواتير</div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-btn-invoices'>", unsafe_allow_html=True)
            if st.button("📋 قسم BOQ", key="sb_boq_wh"): st.session_state.page = "boq_section"; st.query_params["_pg"] = "boq_section"
            st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            if st.button("📞 أرقام التواصل", key="sb_contacts_wh"): st.session_state.page = "contacts_page"; st.query_params["_pg"] = "contacts_page"

        # ── أمين مستودع المقاول: صلاحيات محدودة ──
        elif role == "أمين مستودع المقاول":
            # المستودعات المصرح له برؤيتها
            _cwp = pd.read_sql(
                "SELECT warehouse FROM contractor_warehouse_permissions WHERE username=?",
                conn, params=(u['username'],))
            _allowed_wh = _cwp['warehouse'].tolist()

            # حساب الفواتير المعلقة (لم تُرفق بعد أو مُعادة) لكل نوع
            def _pending_count(inv_type):
                try:
                    _total = int(pd.read_sql(
                        f"SELECT COUNT(*) as cnt FROM archived_invoices WHERE invoice_type='{inv_type}'", conn
                    ).iloc[0]['cnt'])
                    _done = int(pd.read_sql(
                        f"SELECT COUNT(*) as cnt FROM signed_invoices WHERE invoice_type='{inv_type}' AND status IN ('معتمد','بانتظار الاعتماد')", conn
                    ).iloc[0]['cnt'])
                    return max(0, _total - _done)
                except Exception:
                    return 0

            def _returned_count(inv_type):
                try:
                    return int(pd.read_sql(
                        f"SELECT COUNT(*) as cnt FROM signed_invoices WHERE invoice_type='{inv_type}' AND status='مُعادة'", conn
                    ).iloc[0]['cnt'])
                except Exception:
                    return 0

            _pend_dispatch  = _pending_count("صرف")   + _returned_count("صرف")
            _pend_return    = _pending_count("ارجاع") + _returned_count("ارجاع")
            _pend_transfer  = _pending_count("نقل")   + _returned_count("نقل")
            _pend_total     = _pend_dispatch + _pend_return + _pend_transfer

            if st.button("📊 رصيد المستودعات"): st.session_state.page = "contractor_inventory"; st.query_params["_pg"] = "contractor_inventory"

            # بطاقة إجمالي المعلقة
            if _pend_total > 0:
                st.markdown(f"""
                <div style='background:#fff3cd;border:2px solid #f9a825;border-radius:10px;
                    padding:10px 14px;text-align:center;margin:6px 0;direction:rtl;'>
                    ⏳ <b style='color:#e65100;font-size:16px;'>{_pend_total}</b>
                    <span style='font-size:13px;color:#555;'> فاتورة معلقة بانتظار توقيعك</span>
                </div>""", unsafe_allow_html=True)

            # ── فواتير تحتاج تعديل (مُعادة) ──
            try:
                _pend_returned_all = int(pd.read_sql("SELECT COUNT(*) as cnt FROM signed_invoices WHERE status='مُعادة'", conn).iloc[0]['cnt'])
            except Exception:
                _pend_returned_all = 0
            if _pend_returned_all > 0:
                st.divider()
                st.sidebar.markdown("<div class='sb-section-requests'>⚠️ فواتير تحتاج تعديل</div>", unsafe_allow_html=True)
                st.markdown("<div class='sb-btn-requests'>", unsafe_allow_html=True)
                st.markdown(
                    f"<div class='ret-btn-wrap'><span class='ret-badge'>{_pend_returned_all}</span></div>",
                    unsafe_allow_html=True)
                if st.button("🔴 فواتير مُعادة للتعديل", key="cwk_returned_inv"): st.session_state.page = "cwk_returned_invoices"; st.query_params["_pg"] = "cwk_returned_invoices"
                st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            st.sidebar.markdown("<div class='sb-section-emergency'>🚨 الطوارئ</div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-btn-emergency'>", unsafe_allow_html=True)
            if _pend_dispatch > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{_pend_dispatch}</span></div>", unsafe_allow_html=True)
            if st.button("🚨 طرف مواد طوارئ واردة", key="cwk_emg_dispatch"): st.session_state.page = "cwk_emg_dispatch"; st.query_params["_pg"] = "cwk_emg_dispatch"
            if _pend_return > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{_pend_return}</span></div>", unsafe_allow_html=True)
            if st.button("↩️ ارجاع مواد طوارئ واردة", key="cwk_emg_return"): st.session_state.page = "cwk_emg_return"; st.query_params["_pg"] = "cwk_emg_return"
            if _pend_transfer > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{_pend_transfer}</span></div>", unsafe_allow_html=True)
            if st.button("🔁 نقل مواد واردة", key="cwk_emg_transfer"): st.session_state.page = "cwk_emg_transfer"; st.query_params["_pg"] = "cwk_emg_transfer"
            st.markdown("</div>", unsafe_allow_html=True)

        # ── مدير النظام: صلاحيات كاملة ──
        else:
            _is_admin = (role == "مدير نظام")
            if st.button("📊 رصيد المستودعات", key="sb_inv_adm"): st.session_state.page = "inventory_status"; st.query_params["_pg"] = "inventory_status"
            if st.button("📑 تعريف مواد جديدة", key="sb_defs_adm"): st.session_state.page = "item_defs"; st.query_params["_pg"] = "item_defs"
            if st.button("⚠️ تنبيهات نقص مواد", key="sb_alerts_adm"): st.session_state.page = "alerts_page"; st.query_params["_pg"] = "alerts_page"

            # ═══ قسم: الصرف وتغذية المستودع ═══
            st.divider()
            st.sidebar.markdown("<div class='sb-section-stock'>📦 الصرف وتغذية المستودع</div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-btn-stock'>", unsafe_allow_html=True)
            if st.button("📥 إضافة مواد إلى المستودع", key="sb_stockin_adm"): st.session_state.page = "stock_in"; st.query_params["_pg"] = "stock_in"
            if st.button("🛒 صرف مواد للمقاول", key="sb_stockout_adm"): st.session_state.page = "stock_out"; st.query_params["_pg"] = "stock_out"
            if st.button("🚛 نقل مادة من مستودع إلى آخر", key="sb_transfer_adm"): st.session_state.page = "stock_transfer"; st.query_params["_pg"] = "stock_transfer"
            st.markdown("</div>", unsafe_allow_html=True)

            # ═══ قسم: الطلبات ═══
            st.divider()
            st.sidebar.markdown("<div class='sb-section-requests'>📋 الطلبات</div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-btn-requests'>", unsafe_allow_html=True)

            pending_ret_adm = int(pd.read_sql("SELECT COUNT(*) as cnt FROM return_requests WHERE status='معلق'", conn).iloc[0]['cnt'])
            if pending_ret_adm > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{pending_ret_adm}</span></div>", unsafe_allow_html=True)
            if st.button("🔄 طلبات الارجاع", key="sb_ret_adm"): st.session_state.page = "return_requests_admin"; st.query_params["_pg"] = "return_requests_admin"

            pending_cancel_adm = int(pd.read_sql("SELECT COUNT(*) as cnt FROM cancel_invoice_requests WHERE status='معلق'", conn).iloc[0]['cnt'])
            if pending_cancel_adm > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{pending_cancel_adm}</span></div>", unsafe_allow_html=True)
            if st.button("🚫 طلبات إلغاء الفواتير", key="sb_cancel_adm"): st.session_state.page = "cancel_invoice_admin"; st.query_params["_pg"] = "cancel_invoice_admin"

            try:
                _pend_signed_adm = int(pd.read_sql("SELECT COUNT(*) as cnt FROM signed_invoices WHERE status='بانتظار الاعتماد'", conn).iloc[0]['cnt'])
            except Exception:
                _pend_signed_adm = 0
            if _pend_signed_adm > 0:
                st.markdown(f"<div class='ret-btn-wrap'><span class='ret-badge'>{_pend_signed_adm}</span></div>", unsafe_allow_html=True)
            if st.button("✍️ اعتماد فواتير المقاول", key="sb_approve_adm"): st.session_state.page = "approve_signed_invoices"; st.query_params["_pg"] = "approve_signed_invoices"
            st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            if st.button("🛠️ سجل العمليات التفصيلي", key="sb_logs_adm"): st.session_state.page = "view_logs"; st.query_params["_pg"] = "view_logs"
            if st.button("✏️ تعديل فاتورة سابقة", key="sb_edit_adm"): st.session_state.page = "edit_invoice"; st.query_params["_pg"] = "edit_invoice"

            # ═══ قسم: الفواتير ═══
            st.divider()
            st.sidebar.markdown("<div class='sb-section-invoices'>📑 قسم الفواتير</div>", unsafe_allow_html=True)
            st.markdown("<div class='sb-btn-invoices'>", unsafe_allow_html=True)
            if st.button("📋 قسم BOQ", key="sb_boq_adm"): st.session_state.page = "boq_section"; st.query_params["_pg"] = "boq_section"
            if _is_admin:
                if st.button("🗑️ حذف فواتير", key="sb_delinv_adm"): st.session_state.page = "invoices_delete_perm"; st.query_params["_pg"] = "invoices_delete_perm"

            st.markdown("</div>", unsafe_allow_html=True)

            st.divider()
            if st.button("📞 أرقام التواصل", key="sb_contacts_adm"): st.session_state.page = "contacts_page"; st.query_params["_pg"] = "contacts_page"

            # ═══ قسم: التحكم بالنظام ═══
            if _is_admin:
                st.divider()
                st.sidebar.markdown("<div class='sb-section-admin'>⚙️ التحكم بالنظام</div>", unsafe_allow_html=True)
                st.markdown("<div class='sb-btn-admin'>", unsafe_allow_html=True)
                if st.button("👥 إدارة حسابات الموظفين والطلبات"): st.session_state.page = "manage_staff"; st.query_params["_pg"] = "manage_staff"
                if st.button("🏢 إدارة المستودعات والمقاولين والفئات"): st.session_state.page = "global_settings"; st.query_params["_pg"] = "global_settings"
                if st.button("💾 إدارة النسخ الاحتياطية"): st.session_state.page = "backup_page"; st.query_params["_pg"] = "backup_page"
                st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        if st.button("🚪 تسجيل الخروج "):
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
            # بناء HTML الجدول كاملاً مع CSS مضمّن
            rows_html = ""
            for _, row in df_inventory.iterrows():
                qty = int(row['الرصيد المتاح حالياً'])
                if qty <= 5:
                    badge_bg = "#d32f2f"; badge_color = "white"
                elif qty <= 15:
                    badge_bg = "#f9a825"; badge_color = "#333"
                else:
                    badge_bg = "#004a99"; badge_color = "white"
                row_bg = ""
                rows_html += f"""
                <tr>
                    <td style='font-weight:900;color:#004a99;font-size:12px;padding:9px 12px;border-bottom:1px solid #f0f4f8;'>{row['كود المادة']}</td>
                    <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;font-size:13px;'>{row['اسم الصنف والمادة التفصيلي']}</td>
                    <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;color:#555;font-size:12px;'>{row['تصنيف الفئة']}</td>
                    <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;font-size:12px;font-weight:bold;color:#333;'>📍 {row['موقع المستودع']}</td>
                    <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;text-align:center;'>
                        <span style='display:inline-block;background:{badge_bg};color:{badge_color};border-radius:20px;padding:3px 14px;font-weight:900;font-size:13px;min-width:36px;text-align:center;'>{qty}</span>
                    </td>
                </tr>"""

            table_height = min(80 + len(df_inventory) * 42, 600)
            components.html(f"""
            <html><head>
            <meta charset="utf-8">
            <style>
                body {{ margin:0; padding:0; font-family:'Tajawal',Arial,sans-serif; direction:rtl; }}
                .wrap {{ border-radius:12px; overflow:hidden; box-shadow:0 2px 14px rgba(0,74,153,0.12); border:1px solid #e8eef6; }}
                table {{ width:100%; border-collapse:collapse; }}
                thead tr {{ background:linear-gradient(90deg,#004a99,#0066cc); color:white; font-weight:900; font-size:13px; }}
                thead th {{ padding:11px 12px; text-align:right; font-weight:900; letter-spacing:0.3px; }}
                tbody tr:nth-child(even) {{ background:#f7faff; }}
                tbody tr:hover {{ background:#e8f0fe; transition:background 0.15s; }}
                .info-bar {{ display:flex; justify-content:space-between; align-items:center;
                             padding:8px 12px; background:#f0f4ff; border-bottom:1px solid #dde6f5;
                             font-size:13px; color:#555; direction:rtl; }}
                .legend {{ font-size:11px; color:#888; padding:6px 12px; text-align:right; background:#fafbff; }}
            </style>
            </head><body>
            <div class="info-bar">
                <span>📦 إجمالي الأصناف المعروضة: <b style="color:#004a99;font-size:15px;">{len(df_inventory)}</b></span>
                <span class="legend">🔴 حرج ≤5 &nbsp; 🟡 تنبيه ≤15 &nbsp; 🔵 آمن</span>
            </div>
            <div class="wrap">
                <table>
                    <thead>
                        <tr>
                            <th style="width:14%;">كود المادة</th>
                            <th style="width:38%;">اسم الصنف</th>
                            <th style="width:18%;">الفئة</th>
                            <th style="width:18%;">المستودع</th>
                            <th style="width:12%;text-align:center;">الرصيد</th>
                        </tr>
                    </thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            </body></html>
            """, height=table_height, scrolling=True)

            excel_view = to_excel(df_inventory)
            st.download_button("📥 تصدير رصيد المخزون إلى Excel", excel_view, "جرد_المخزون.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.warning("⚠️ لا توجد أي مواد أو أرصدة مخزنية مسجلة تحت شروط البحث المحددة حالياً.")

     # ---------------------------------------------------------
    # صفحة: تعريف مواد جديدة في كشاف النظام المحدثة (التعريف المتعدد)
    # ---------------------------------------------------------
    elif st.session_state.page == "item_defs":
        page_header("📑", "تعريف مواد جديدة في النظام", "إضافة وتعريف أصناف المواد وربطها بفئاتها", "#1daa60")
        if not list_categories:
            st.warning("⚠️ يرجى أولاً تدوين وتثبيت فئة أصناف واحدة على الأقل من لوحة الإعدادات العامة لربط المواد بها.")
        else:
            # ── قسم إضافة مواد جديدة ──
            section_card("➕ إضافة مواد جديدة دفعة واحدة", "#1daa60")
            if "num_materials_rows" not in st.session_state:
                st.session_state.num_materials_rows = 3
            col_control1, col_control2 = st.columns([1, 4])
            with col_control1:
                new_rows_count = st.number_input("عدد المواد:", min_value=1, max_value=20, value=st.session_state.num_materials_rows, step=1)
                if new_rows_count != st.session_state.num_materials_rows:
                    st.session_state.num_materials_rows = new_rows_count
                    st.rerun()
            with st.form("multi_material_define_form", clear_on_submit=True):
                inserted_data = []
                for i in range(st.session_state.num_materials_rows):
                    st.markdown(f"""<div style='background:#f0f4ff;border-right:3px solid #004a99;border-radius:6px;
                        padding:6px 14px;margin:6px 0 4px 0;font-weight:bold;color:#004a99;font-size:13px;'>
                        📦 المادة رقم ({i+1})</div>""", unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns([1.5, 2, 2.5, 1.5])
                    item_code_input = c1.text_input(f"كود المادة *", key=f"m_code_{i}").strip()
                    item_name_input = c2.text_input(f"اسم المادة *", key=f"m_name_{i}").strip()
                    item_desc_input = c3.text_input(f"الوصف الفني", key=f"m_desc_{i}").strip()
                    item_cat_input  = c4.selectbox(f"الفئة *", list_categories, key=f"m_cat_{i}")
                    if item_code_input and item_name_input:
                        inserted_data.append({'code': item_code_input, 'name': item_name_input,
                                              'desc': item_desc_input, 'cat': item_cat_input})
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                submit_multi = st.form_submit_button("🚀 حفظ واعتماد كافة المواد المدخلة", use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
                if submit_multi:
                    if not inserted_data:
                        st.error("⚠️ يرجى ملء بيانات مادة واحدة على الأقل.")
                    else:
                        success_count = 0; skipped_codes = []
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
                            st.success(f"🎉 تم تعريف وحفظ ({success_count}) صنف جديد!")
                        if skipped_codes:
                            st.warning(f"⚠️ الأكواد التالية موجودة مسبقاً: {', '.join(skipped_codes)}")
                        st.session_state.num_materials_rows = 3
                        st.rerun()

            # ── قسم المواد المعرّفة ──
            section_card("📋 المواد المعرّفة في النظام", "#004a99")
            search_mat = st.text_input("🔍 ابحث بكود أو اسم المادة:", key="search_mat_table").strip()
            df_current_materials = pd.read_sql(
                "SELECT item_code, item_name, description, category FROM material_definitions ORDER BY item_code ASC", conn)
            if search_mat:
                df_current_materials = df_current_materials[
                    df_current_materials['item_code'].str.contains(search_mat, case=False, na=False) |
                    df_current_materials['item_name'].str.contains(search_mat, case=False, na=False)]

            if df_current_materials.empty:
                st.info("ℹ️ لا توجد مواد تطابق البحث.")
            else:
                st.caption(f"📦 {len(df_current_materials)} صنف — اضغط ✏️ لتعديل أو 🗑️ لحذف")
                # ── رأس الجدول ──
                hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([1.2, 2, 2.5, 1.5, 1.2])
                for col, label in zip([hcol1,hcol2,hcol3,hcol4,hcol5],
                                      ["**كود المادة**","**الاسم**","**الوصف**","**الفئة**","**إجراء**"]):
                    col.markdown(label)
                st.markdown("<hr style='margin:4px 0 8px 0;border-color:#e0e8f0;'>", unsafe_allow_html=True)

                for idx, row in df_current_materials.iterrows():
                    orig_code = row['item_code']
                    row_key   = f"mat_{orig_code}"
                    if f"edit_mode_{row_key}" not in st.session_state:
                        st.session_state[f"edit_mode_{row_key}"] = False
                    col1, col2, col3, col4, col5 = st.columns([1.2, 2, 2.5, 1.5, 1.2])
                    if st.session_state[f"edit_mode_{row_key}"]:
                        with st.form(f"edit_mat_form_{row_key}", clear_on_submit=False):
                            e1, e2, e3, e4 = st.columns([1.2, 2, 2.5, 1.5])
                            new_code = e1.text_input("الكود", value=row['item_code'], key=f"ec_{row_key}")
                            new_name = e2.text_input("الاسم", value=row['item_name'], key=f"en_{row_key}")
                            new_desc = e3.text_input("الوصف", value=row['description'] if row['description'] else "", key=f"ed_{row_key}")
                            cat_idx  = list_categories.index(row['category']) if row['category'] in list_categories else 0
                            new_cat  = e4.selectbox("الفئة", list_categories, index=cat_idx, key=f"ecat_{row_key}")
                            btn_save, btn_cancel = st.columns([1, 1])
                            save_clicked   = btn_save.form_submit_button("💾 حفظ")
                            cancel_clicked = btn_cancel.form_submit_button("❌ إلغاء")
                            if save_clicked:
                                new_code = new_code.strip(); new_name = new_name.strip()
                                if not new_code or not new_name:
                                    st.error("⚠️ الكود والاسم إلزاميان.")
                                else:
                                    if new_code != orig_code:
                                        dup = pd.read_sql(f"SELECT item_code FROM material_definitions WHERE item_code='{new_code}'", conn)
                                        if not dup.empty:
                                            st.error(f"❌ الكود ({new_code}) مستخدم!"); st.stop()
                                    c.execute("UPDATE material_definitions SET item_code=?, item_name=?, description=?, category=? WHERE item_code=?",
                                              (new_code, new_name, new_desc.strip(), new_cat, orig_code))
                                    if new_code != orig_code:
                                        c.execute("UPDATE inventory SET item_code=? WHERE item_code=?", (new_code, orig_code))
                                        c.execute("UPDATE action_logs SET item_code=? WHERE item_code=?", (new_code, orig_code))
                                    save_log("تعديل بيانات مادة", new_code, 0,
                                             f"تعديل [{orig_code}] → {new_code} | {new_name}", u['full_name'])
                                    conn.commit()
                                    st.session_state[f"edit_mode_{row_key}"] = False
                                    st.success(f"✅ تم تحديث [{new_name}]"); st.rerun()
                            if cancel_clicked:
                                st.session_state[f"edit_mode_{row_key}"] = False; st.rerun()
                    else:
                        col1.write(row['item_code'])
                        col2.write(row['item_name'])
                        col3.write(row['description'] if row['description'] else "—")
                        col4.write(row['category'])
                        with col5:
                            btn_e, btn_d = st.columns([1, 1])
                            if btn_e.button("✏️", key=f"edit_btn_{row_key}", help="تعديل"):
                                st.session_state[f"edit_mode_{row_key}"] = True; st.rerun()
                            if btn_d.button("🗑️", key=f"del_btn_{row_key}", help="حذف"):
                                st.session_state[f"confirm_del_{row_key}"] = True
                    if st.session_state.get(f"confirm_del_{row_key}", False):
                        st.warning(f"⚠️ تأكيد حذف **{row['item_name']}** ({orig_code})؟")
                        conf1, conf2 = st.columns([1, 1])
                        if conf1.button("✅ نعم، احذف", key=f"yes_del_{row_key}"):
                            c.execute("DELETE FROM material_definitions WHERE item_code=?", (orig_code,))
                            save_log("حذف مادة", orig_code, 0, f"حذف [{row['item_name']}]", u['full_name'])
                            conn.commit()
                            st.session_state[f"confirm_del_{row_key}"] = False
                            st.success(f"✅ تم الحذف."); st.rerun()
                        if conf2.button("🚫 إلغاء", key=f"no_del_{row_key}"):
                            st.session_state[f"confirm_del_{row_key}"] = False; st.rerun()
                    st.markdown("<hr style='margin:3px 0;border-color:#f0f4f8;'>", unsafe_allow_html=True)

                # ---------------------------------------------------------
    # صفحة: تنبيهات مستويات الخطر وقوائم الطلب السريع والآلي
    # ---------------------------------------------------------
    elif st.session_state.page == "alerts_page":
        st.markdown("<div class='main-title'>⚠️ تقرير المواد التي اقتربت نهايتها من المخزون</div>", unsafe_allow_html=True)
        col_filter1, col_filter2 = st.columns([2, 1])
        status_filter = col_filter1.selectbox("اختر مستوى فرز المواد لإنشاء ملف بالمواد الحرجة :", ["عرض كافة النواقص (الحرج والتنبيه)", "🔴 نقص حاد وحرج جداً (الأحمر)", "🟡 تخطي حد التنبيه الآمن (الأصفر)"])

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
                # ── بناء جدول HTML بنفس تصميم جدول المخزون ──
                rows_html = ""
                for _, row in df_to_export.iterrows():
                    qty  = int(row['الرصيد الحالي بالمخزن'])
                    stat = str(row['وضعية حالة المخزون'])
                    if stat == "🔴 نقص حاد":
                        badge_bg = "#d32f2f"; badge_color = "white"
                        row_bg   = "background:#fff5f5;"
                    elif stat == "🟡 تنبيه":
                        badge_bg = "#f9a825"; badge_color = "#333"
                        row_bg   = "background:#fffde7;"
                    else:
                        badge_bg = "#2e7d32"; badge_color = "white"
                        row_bg   = ""

                    stat_badge_bg    = "#d32f2f" if "نقص" in stat else ("#f9a825" if "تنبيه" in stat else "#2e7d32")
                    stat_badge_color = "white" if "نقص" in stat else ("#333" if "تنبيه" in stat else "white")

                    rows_html += f"""
                    <tr style='{row_bg}'>
                        <td style='font-weight:900;color:#004a99;font-size:12px;padding:9px 12px;border-bottom:1px solid #f0f4f8;'>{row['كود المادة']}</td>
                        <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;font-size:13px;'>{row['اسم المادة والصنف']}</td>
                        <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;color:#555;font-size:12px;'>{row['الفئة الأساسية']}</td>
                        <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;font-size:12px;font-weight:bold;color:#333;'>📍 {row['المستودع المستضيف']}</td>
                        <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;text-align:center;'>
                            <span style='display:inline-block;background:{badge_bg};color:{badge_color};border-radius:20px;padding:3px 14px;font-weight:900;font-size:13px;min-width:36px;text-align:center;'>{qty}</span>
                        </td>
                        <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;text-align:center;'>
                            <span style='display:inline-block;background:{stat_badge_bg};color:{stat_badge_color};border-radius:8px;padding:3px 10px;font-size:12px;font-weight:bold;white-space:nowrap;'>{stat}</span>
                        </td>
                    </tr>"""

                table_height = min(80 + len(df_to_export) * 44, 600)
                components.html(f"""
                <html><head>
                <meta charset="utf-8">
                <style>
                    body {{ margin:0; padding:0; font-family:'Tajawal',Arial,sans-serif; direction:rtl; }}
                    .wrap {{ border-radius:12px; overflow:hidden; box-shadow:0 2px 14px rgba(0,74,153,0.12); border:1px solid #e8eef6; }}
                    table {{ width:100%; border-collapse:collapse; }}
                    thead tr {{ background:linear-gradient(90deg,#7f0000,#c62828); color:white; font-weight:900; font-size:13px; }}
                    thead th {{ padding:11px 12px; text-align:right; font-weight:900; letter-spacing:0.3px; }}
                    tbody tr:nth-child(even) {{ background:#fafafa; }}
                    tbody tr:hover {{ filter:brightness(0.96); transition:filter 0.15s; }}
                    .info-bar {{ display:flex; justify-content:space-between; align-items:center;
                                 padding:8px 12px; background:#fff8f0; border-bottom:1px solid #ffe0cc;
                                 font-size:13px; color:#555; direction:rtl; }}
                    .legend {{ font-size:11px; color:#888; }}
                </style>
                </head><body>
                <div class="info-bar">
                    <span>⚠️ الأصناف التي تحتاج تدخلاً: <b style="color:#c62828;font-size:15px;">{len(df_to_export)}</b> صنف</span>
                    <span class="legend">🔴 نقص حاد &nbsp; 🟡 تنبيه</span>
                </div>
                <div class="wrap">
                    <table>
                        <thead>
                            <tr>
                                <th style="width:13%;">كود المادة</th>
                                <th style="width:32%;">اسم المادة</th>
                                <th style="width:16%;">الفئة</th>
                                <th style="width:18%;">المستودع</th>
                                <th style="width:10%;text-align:center;">الرصيد</th>
                                <th style="width:11%;text-align:center;">الحالة</th>
                            </tr>
                        </thead>
                        <tbody>{rows_html}</tbody>
                    </table>
                </div>
                </body></html>
                """, height=table_height, scrolling=True)

                excel_data = to_excel(df_to_export[['كود المادة', 'اسم المادة والصنف', 'الفئة الأساسية', 'المستودع المستضيف', 'الرصيد الحالي بالمخزن', 'وضعية حالة المخزون']])
                st.download_button(label=f"📥 تحميل مسودة طلب المواد ({status_filter})", data=excel_data,
                                   file_name=f"مسودة_طلب_مواد.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.success("✅ جميع أرصدة مستودعات الطوارئ الميدانية آمنة وضمن المستويات المستقرة المطلوبة.")
        else:
            st.success("✅ المنظومة لا تحتوي على أي نواقص أو حركات مخزنية حرجة حالياً.")

    # ---------------------------------------------------------
    # صفحة: شحن وإدخال المواد للمستودعات
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_in":
        page_header("📥", "تغذية مستودعات الطوارئ", "إضافة وإدخال المواد إلى المستودعات الميدانية", "#1daa60")
        if not list_warehouses:
            st.warning("⚠️ يرجى أولاً الذهاب للوحة التحكم العامة وتعريف مستودع ميداني واحد على الأقل.")
        else:
            section_card("📦 بيانات المواد المراد إضافتها", "#1daa60")
            if "num_in_rows" not in st.session_state: st.session_state.num_in_rows = 3
            col_nr, _ = st.columns([1, 4])
            new_nr = col_nr.number_input("عدد المواد:", min_value=1, max_value=20, value=st.session_state.num_in_rows, step=1)
            if new_nr != st.session_state.num_in_rows: st.session_state.num_in_rows = new_nr; st.rerun()
            with st.form("stock_in_form", clear_on_submit=True):
                in_rows = []
                for ri in range(st.session_state.num_in_rows):
                    st.markdown(f"""<div style='background:#f0fff4;border-right:3px solid #1daa60;border-radius:6px;
                        padding:5px 14px;margin:6px 0 3px 0;font-weight:bold;color:#1daa60;font-size:13px;'>
                        📦 المادة رقم ({ri+1})</div>""", unsafe_allow_html=True)
                    r1,r2,r3 = st.columns([1.5,3,1.5])
                    r_code = r1.text_input("كود المادة *", key=f"in_code_{ri}").strip()
                    r_wh   = r2.selectbox("المستودع *", list_warehouses, key=f"in_wh_{ri}")
                    r_qty  = r3.number_input("الكمية *", min_value=1, value=10, step=1, key=f"in_qty_{ri}")
                    if r_code: in_rows.append({'code':r_code,'wh':r_wh,'qty':r_qty})
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                if st.form_submit_button("💾 اعتماد وتغذية الكميات", use_container_width=True):
                    if not in_rows:
                        st.error("⚠️ يرجى كتابة كود المادة لصف واحد على الأقل.")
                    else:
                        valid_rows = []; err_list = []
                        for row_in in in_rows:
                            mat_res = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{row_in['code']}'", conn)
                            if mat_res.empty:
                                err_list.append(row_in['code'])
                            else:
                                valid_rows.append({'code': row_in['code'], 'name': mat_res.iloc[0]['item_name'],
                                                   'wh': row_in['wh'], 'qty': row_in['qty'], 'cat': mat_res.iloc[0]['category']})
                        if err_list:
                            st.error(f"❌ الأكواد غير معرّفة: {', '.join(err_list)}")
                        if valid_rows:
                            st.session_state['stock_in_pending'] = valid_rows
                            st.session_state['stock_in_confirm'] = False
                            st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        # خارج الفورم: تأكيد التغذية
        if st.session_state.get('stock_in_pending'):
            pending_rows = st.session_state['stock_in_pending']
            st.write("---")
            section_card("✅ تأكيد إضافة المواد التالية للمستودع", "#1daa60")
            for rv in pending_rows:
                st.markdown(
                    f"<div style='background:#f0f7ff;border-right:4px solid #004a99;padding:8px 14px;margin:6px 0;border-radius:6px;direction:rtl;'>"
                    f"🏢 <b>المستودع:</b> {rv['wh']} &nbsp;|&nbsp; "
                    f"📦 <b>اسم المادة:</b> {rv['name']} &nbsp;|&nbsp; "
                    f"🔖 <b>الكود:</b> {rv['code']} &nbsp;|&nbsp; "
                    f"🔢 <b>الكمية:</b> {rv['qty']}</div>",
                    unsafe_allow_html=True)
            col_siy, col_sin = st.columns([1, 1])
            if col_siy.button("✅ نعم، تأكيد الإضافة للمستودع"):
                ok_count = 0
                for rv in pending_rows:
                    c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                              (rv['code'], rv['qty'], rv['wh'], "", rv['cat']))
                    save_log("تغذية مستودع", rv['code'], rv['qty'],
                             f"شحن كمية ({rv['qty']}) من صنف [{rv['name']}] إلى المستودع [{rv['wh']}]", u['full_name'])
                    ok_count += 1
                conn.commit()
                st.session_state['stock_in_pending'] = None
                st.session_state.num_in_rows = 3
                st.success(f"✅ تم بنجاح شحن ({ok_count}) صنف للمستودعات!")
                st.rerun()
            if col_sin.button("❌ إلغاء"):
                st.session_state['stock_in_pending'] = None
                st.rerun()
    # ---------------------------------------------------------
    # صفحة: صرف مواد للمقاول
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_out":
        page_header("🛒", "صرف مواد للمقاول", "إنشاء فاتورة صرف وتسليم المواد للمقاولين", "#f9a825")

        if not list_warehouses or not list_contractors:
            st.warning("⚠️ يرجى تعريف المستودعات والمقاولين في الإعدادات أولاً.")
        else:
            # ════════════════════════════════════════════
            # إذا تم إنشاء الفاتورة — إشعار النجاح
            # ════════════════════════════════════════════
            if st.session_state.last_created_inv_no and st.session_state.last_created_inv_type == "صرف" and not st.session_state.cart:
                st.markdown(f"""
                <div dir="rtl" style="background:linear-gradient(135deg,#e8f5e9,#f1f8e9);
                    border:2px solid #1daa60;border-radius:16px;padding:24px;text-align:center;
                    box-shadow:0 4px 16px rgba(29,170,96,0.15);margin:16px 0;">
                    <div style="font-size:42px;margin-bottom:8px;">✅</div>
                    <div style="font-size:19px;font-weight:900;color:#1b5e20;margin-bottom:6px;">تم إنشاء الفاتورة بنجاح</div>
                    <div style="font-size:14px;color:#2e7d32;margin-bottom:12px;">فاتورة صرف مواد طوارئ</div>
                    <div style="font-size:28px;font-weight:900;color:#c62828;background:rgba(198,40,40,0.08);
                                border-radius:8px;padding:6px 18px;display:inline-block;">
                        {st.session_state.last_created_inv_no}
                    </div>
                </div>""", unsafe_allow_html=True)
                _nc1, _nc2, _nc3 = st.columns([2, 2, 1])
                if _nc1.button("👁️ مشاهدة الفاتورة وطباعتها", key="preview_out_inv", use_container_width=True):
                    st.session_state["_view_inv_no"] = st.session_state.last_created_inv_no
                    st.session_state.page = "view_logs"
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()
                if _nc2.button("➕ إنشاء فاتورة صرف جديدة", key="new_out_inv", use_container_width=True):
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()
                if _nc3.button("✖️ إغلاق", key="dismiss_out_inv", use_container_width=True):
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()

            # ════════════════════════════════════════════
            # المرحلة ١: بيانات الفاتورة + إضافة المواد
            # ════════════════════════════════════════════
            elif not st.session_state.confirm_out:
                section_card("📋 بيانات الفاتورة", "#f9a825")
                c1, c2 = st.columns(2)
                out_wh         = c1.selectbox("📍 مستودع الصرف", list_warehouses, key="out_wh_sel")
                out_contractor = c2.selectbox("🏗️ المقاول المستلم", list_contractors, key="out_cont_sel")
                out_boq = st.text_input("📋 BOQ الحالة *", placeholder="BoQ/Zone2/2026/...", key="out_boq_val").strip()

                section_card("➕ إضافة مواد للسلة", "#f9a825")

                # ── إضافة مادة ──
                a1, a2, a3 = st.columns([2, 1.5, 1])
                out_code = a1.text_input("كود المادة", key=f"out_code_val_{st.session_state.input_out_code}", label_visibility="visible").strip()
                out_qty  = a2.number_input("الكمية", min_value=1, value=1, step=1, key=f"out_qty_val_{st.session_state.input_out_qty}")
                a3.markdown("<br>", unsafe_allow_html=True)
                if a3.button("➕ إضافة", use_container_width=True):
                    if out_code:
                        mat = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{out_code}'", conn)
                        if mat.empty:
                            st.error("❌ الكود غير معرّف في النظام")
                        else:
                            avail = int(pd.read_sql(f"SELECT COALESCE(SUM(qty),0) as t FROM inventory WHERE item_code='{out_code}' AND warehouse='{out_wh}'", conn).iloc[0]['t'])
                            already = sum(x["qty"] for x in st.session_state.cart if x["code"] == out_code)
                            if avail < (out_qty + already):
                                st.error(f"❌ الرصيد غير كافٍ — المتاح: {avail}")
                            else:
                                ex = [i for i,x in enumerate(st.session_state.cart) if x["code"] == out_code]
                                if ex: st.session_state.cart[ex[0]]["qty"] += out_qty
                                else:  st.session_state.cart.append({"code": out_code, "name": mat.iloc[0]["item_name"], "qty": out_qty, "cat": mat.iloc[0]["category"]})
                                st.session_state.input_out_code += 1; st.session_state.input_out_qty += 1; st.rerun()

                # ── عرض السلة ──
                if st.session_state.cart:
                    section_card("🛒 المواد في السلة", "#004a99")
                    # رأس الجدول
                    h1,h2,h3,h4,h5 = st.columns([1.5, 3, 1.5, 1.2, 0.6])
                    h1.markdown("**الكود**"); h2.markdown("**الاسم**"); h3.markdown("**الفئة**"); h4.markdown("**الكمية**"); h5.markdown("**حذف**")
                    _rm = None
                    for i, item in enumerate(st.session_state.cart):
                        c1,c2,c3,c4,c5 = st.columns([1.5, 3, 1.5, 1.2, 0.6])
                        avail_i = int(pd.read_sql(f"SELECT COALESCE(SUM(qty),0) as t FROM inventory WHERE item_code='{item['code']}' AND warehouse='{out_wh}'", conn).iloc[0]['t'])
                        c1.write(item["code"]); c2.write(item["name"]); c3.write(item.get("cat",""))
                        nq = c4.number_input("", min_value=1, max_value=max(1,avail_i), value=min(int(item["qty"]),max(1,avail_i)), step=1, key=f"oq_{i}", label_visibility="collapsed")
                        if nq != int(item["qty"]): st.session_state.cart[i]["qty"] = nq; st.rerun()
                        if c5.button("🗑️", key=f"od_{i}"): _rm = i
                    if _rm is not None: st.session_state.cart.pop(_rm); st.rerun()

                    st.divider()
                    # إجمالي + زر التصدير
                    tot = sum(x["qty"] for x in st.session_state.cart)
                    st.markdown(f"**الإجمالي:** {len(st.session_state.cart)} صنف — {tot} وحدة")
                    b1, b2 = st.columns([1, 3])
                    if b1.button("🗑️ تفريغ السلة"):
                        st.session_state.cart = []; st.rerun()
                    # التحقق من الأرصدة
                    errs = validate_cart_stock(st.session_state.cart, out_wh)
                    if errs:
                        st.error("⛔ " + " | ".join(errs))
                    elif not out_boq:
                        st.warning("⚠️ أدخل BOQ الحالة أولاً")
                    else:
                        st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                        if b2.button("🚀 تصدير الفاتورة", use_container_width=True):
                            st.session_state.confirm_out = True; st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

            # ════════════════════════════════════════════
            # المرحلة ٢: تأكيد التصدير
            # ════════════════════════════════════════════
            else:
                # استرجاع القيم من session (لأن widgets غير متاحة هنا)
                out_wh         = st.session_state.get("out_wh_sel", list_warehouses[0])
                out_contractor = st.session_state.get("out_cont_sel", list_contractors[0])
                _final_boq     = st.session_state.get("_boq_override") or st.session_state.get("out_boq_val", "")

                rows_html = "".join([
                    f"<tr><td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;'>{it['code']}</td>"
                    f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;'>{it['name']}</td>"
                    f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:700;color:#c62828;'>{it['qty']}</td></tr>"
                    for it in st.session_state.cart
                ])
                st.markdown(f"""
                <div dir="rtl" style="background:#fff8e1;border:2px solid #f9a825;border-radius:14px;
                    padding:22px 26px;box-shadow:0 2px 12px rgba(249,168,37,0.2);">
                    <div style="font-size:18px;font-weight:900;color:#e65100;margin-bottom:10px;">⚠️ تأكيد تصدير الفاتورة</div>
                    <div style="font-size:14px;color:#555;margin-bottom:14px;">
                        سيتم <b style="color:#c62828;">خصم المواد التالية</b> من مستودع
                        <b style="color:#004a99;">{out_wh}</b> وتسليمها للمقاول
                        <b style="color:#004a99;">{out_contractor}</b>
                    </div>
                    <table style="width:100%;border-collapse:collapse;font-size:14px;background:white;border-radius:8px;overflow:hidden;">
                        <tr style="background:#004a99;color:white;">
                            <th style="padding:9px 12px;text-align:right;">كود المادة</th>
                            <th style="padding:9px 12px;text-align:right;">اسم المادة</th>
                            <th style="padding:9px 12px;text-align:center;">الكمية</th>
                        </tr>
                        {rows_html}
                    </table>
                    <div style="margin-top:10px;font-size:13px;color:#666;">📋 BOQ: <b>{_final_boq}</b></div>
                </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                ya, na = st.columns(2)
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                if ya.button("✅ تأكيد وإصدار الفاتورة", use_container_width=True):
                    final_errs = validate_cart_stock(st.session_state.cart, out_wh)
                    if final_errs:
                        st.error("⛔ تغيّر الرصيد — " + " | ".join(final_errs))
                        st.session_state.confirm_out = False
                    else:
                        inv_no = now_mecca().strftime("%d%H%M")
                        html_inv = render_invoice_html("فاتورة صرف مواد طوارئ", st.session_state.cart, out_wh, out_contractor, u["full_name"], inv_no, boq=_final_boq)
                        # ملاحظة: الخصم من المخزون يتم بعد توقيع وإرفاق أمين مستودع المقاول
                        # لا يتم الخصم هنا — يتم عند رفع أمين مستودع المقاول للفاتورة الموقعة
                        archive_invoice("صرف", inv_no, out_wh, "", out_contractor, u["full_name"], json.dumps(st.session_state.cart), html_inv, _final_boq)
                        save_log("إنشاء فاتورة صرف (في انتظار توقيع أمين المستودع)", "-", 0,
                                 f"فاتورة صرف للمقاول [{out_contractor}] من [{out_wh}] | {inv_no} | BOQ:{_final_boq}", u["full_name"])
                        conn.commit()
                        st.session_state.last_inv_html = html_inv
                        st.session_state.last_created_inv_no = inv_no
                        st.session_state.last_created_inv_type = "صرف"
                        st.session_state.pop("_boq_override", None)
                        st.session_state.cart = []; st.session_state.confirm_out = False; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                if na.button("❌ إلغاء والرجوع للتعديل", use_container_width=True):
                    st.session_state.confirm_out = False; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: ارجاع مواد للمستودع
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_return":
        st.markdown("<div class='main-title'>🔄 ارجاع مواد للمستودع</div>", unsafe_allow_html=True)

        if not list_warehouses or not list_contractors:
            st.warning("⚠️ يرجى تعريف المستودعات والمقاولين في الإعدادات أولاً.")
        else:
            # ── إشعار النجاح ──
            if st.session_state.last_created_inv_no and st.session_state.last_created_inv_type == "ارجاع" and not st.session_state.return_cart:
                st.markdown(f"""
                <div dir="rtl" style="background:linear-gradient(135deg,#e8f5e9,#f1f8e9);
                    border:2px solid #1daa60;border-radius:16px;padding:24px;text-align:center;
                    box-shadow:0 4px 16px rgba(29,170,96,0.15);margin:16px 0;">
                    <div style="font-size:42px;margin-bottom:8px;">✅</div>
                    <div style="font-size:19px;font-weight:900;color:#1b5e20;margin-bottom:6px;">تم إنشاء الفاتورة بنجاح</div>
                    <div style="font-size:14px;color:#2e7d32;margin-bottom:12px;">فاتورة ارجاع مواد طوارئ</div>
                    <div style="font-size:28px;font-weight:900;color:#c62828;background:rgba(198,40,40,0.08);
                                border-radius:8px;padding:6px 18px;display:inline-block;">
                        {st.session_state.last_created_inv_no}
                    </div>
                </div>""", unsafe_allow_html=True)
                _rc1, _rc2, _rc3 = st.columns([2, 2, 1])
                if _rc1.button("👁️ مشاهدة الفاتورة وطباعتها", key="preview_ret_inv", use_container_width=True):
                    st.session_state["_view_inv_no"] = st.session_state.last_created_inv_no
                    st.session_state.page = "view_logs"
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()
                if _rc2.button("➕ إنشاء فاتورة ارجاع جديدة", key="new_ret_inv", use_container_width=True):
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()
                if _rc3.button("✖️ إغلاق", key="dismiss_ret_inv", use_container_width=True):
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()

            elif not st.session_state.confirm_return:
                # ── رأس الفاتورة ──
                c1, c2 = st.columns(2)
                ret_contractor = c1.selectbox("🏗️ المقاول المسلّم للمواد", list_contractors, key="ret_cont_sel")
                ret_wh         = c2.selectbox("📍 المستودع المستلم", list_warehouses, key="ret_wh_sel")
                ret_boq = st.text_input("📋 BOQ الحالة *", placeholder="BoQ/Zone2/2026/...", key="ret_boq_val").strip()

                section_card("➕ إضافة مواد للسلة", "#f9a825")

                # ── إضافة مادة ──
                a1, a2, a3 = st.columns([2, 1.5, 1])
                ret_code = a1.text_input("كود المادة", key=f"ret_code_val_{st.session_state.input_ret_code}").strip()
                ret_qty  = a2.number_input("الكمية", min_value=1, value=1, step=1, key=f"ret_qty_val_{st.session_state.input_ret_qty}")
                a3.markdown("<br>", unsafe_allow_html=True)
                if a3.button("➕ إضافة", use_container_width=True):
                    if ret_code:
                        mat = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{ret_code}'", conn)
                        if mat.empty:
                            st.error("❌ الكود غير معرّف في النظام")
                        else:
                            ex = [i for i,x in enumerate(st.session_state.return_cart) if x["code"] == ret_code]
                            if ex: st.session_state.return_cart[ex[0]]["qty"] += ret_qty
                            else:  st.session_state.return_cart.append({"code": ret_code, "name": mat.iloc[0]["item_name"], "qty": ret_qty, "cat": mat.iloc[0]["category"]})
                            st.session_state.input_ret_code += 1; st.session_state.input_ret_qty += 1; st.rerun()

                # ── عرض السلة ──
                if st.session_state.return_cart:
                    st.divider()
                    section_card("🛒 المواد في السلة", "#004a99")
                    h1,h2,h3,h4,h5 = st.columns([1.5, 3, 1.5, 1.2, 0.6])
                    h1.markdown("**الكود**"); h2.markdown("**الاسم**"); h3.markdown("**الفئة**"); h4.markdown("**الكمية**"); h5.markdown("**حذف**")
                    _rm = None
                    for i, item in enumerate(st.session_state.return_cart):
                        c1,c2,c3,c4,c5 = st.columns([1.5, 3, 1.5, 1.2, 0.6])
                        c1.write(item["code"]); c2.write(item["name"]); c3.write(item.get("cat",""))
                        nq = c4.number_input("", min_value=1, value=int(item["qty"]), step=1, key=f"rq_{i}", label_visibility="collapsed")
                        if nq != int(item["qty"]): st.session_state.return_cart[i]["qty"] = nq; st.rerun()
                        if c5.button("🗑️", key=f"rd_{i}"): _rm = i
                    if _rm is not None: st.session_state.return_cart.pop(_rm); st.rerun()

                    st.divider()
                    tot = sum(x["qty"] for x in st.session_state.return_cart)
                    st.markdown(f"**الإجمالي:** {len(st.session_state.return_cart)} صنف — {tot} وحدة")
                    b1, b2 = st.columns([1, 3])
                    if b1.button("🗑️ تفريغ السلة"):
                        st.session_state.return_cart = []; st.rerun()
                    if not ret_boq:
                        st.warning("⚠️ أدخل BOQ الحالة أولاً")
                    else:
                        st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                        if b2.button("🚀 تصدير فاتورة الارجاع", use_container_width=True):
                            st.session_state.confirm_return = True; st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

            else:
                # ── تأكيد الارجاع ──
                ret_contractor = st.session_state.get("ret_cont_sel", list_contractors[0])
                ret_wh         = st.session_state.get("ret_wh_sel", list_warehouses[0])
                ret_boq        = st.session_state.get("ret_boq_val", "")
                ret_inv_no_preview = now_mecca().strftime("%d%H%M")
                html_ret_invoice = render_return_invoice_html("فاتورة إرجاع مواد طوارئ", st.session_state.return_cart, ret_wh, ret_contractor, u["full_name"], ret_inv_no_preview, boq=ret_boq)

                rows_html = "".join([
                    f"<tr><td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;'>{it['code']}</td>"
                    f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;'>{it['name']}</td>"
                    f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:700;color:#2e7d32;'>{it['qty']}</td></tr>"
                    for it in st.session_state.return_cart
                ])
                st.markdown(f"""
                <div dir="rtl" style="background:#fff8e1;border:2px solid #f9a825;border-radius:14px;
                    padding:22px 26px;box-shadow:0 2px 12px rgba(249,168,37,0.2);">
                    <div style="font-size:18px;font-weight:900;color:#e65100;margin-bottom:10px;">⚠️ تأكيد تصدير فاتورة الارجاع</div>
                    <div style="font-size:14px;color:#555;margin-bottom:14px;">
                        سيتم <b style="color:#2e7d32;">إضافة المواد التالية</b> إلى مستودع
                        <b style="color:#004a99;">{ret_wh}</b> المسلّمة من المقاول
                        <b style="color:#004a99;">{ret_contractor}</b>
                    </div>
                    <table style="width:100%;border-collapse:collapse;font-size:14px;background:white;border-radius:8px;overflow:hidden;">
                        <tr style="background:#004a99;color:white;">
                            <th style="padding:9px 12px;text-align:right;">كود المادة</th>
                            <th style="padding:9px 12px;text-align:right;">اسم المادة</th>
                            <th style="padding:9px 12px;text-align:center;">الكمية</th>
                        </tr>
                        {rows_html}
                    </table>
                    <div style="margin-top:10px;font-size:13px;color:#666;">📋 BOQ: <b>{ret_boq}</b></div>
                </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                ya, na = st.columns(2)
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                if ya.button("✅ تأكيد وإصدار الفاتورة", use_container_width=True, key="ret_confirm_yes"):
                    inv_no = ret_inv_no_preview
                    # ملاحظة: الإضافة للمخزون تتم بعد توقيع وإرفاق أمين مستودع المقاول
                    archive_invoice("ارجاع", inv_no, ret_wh, "", ret_contractor, u["full_name"], json.dumps(st.session_state.return_cart), html_ret_invoice, ret_boq)
                    save_log("إنشاء فاتورة ارجاع (في انتظار توقيع أمين المستودع)", "-", 0,
                             f"ارجاع من [{ret_contractor}] إلى [{ret_wh}] | {inv_no} | BOQ:{ret_boq}", u["full_name"])
                    conn.commit()
                    st.session_state.last_ret_inv_html = html_ret_invoice
                    st.session_state.last_created_inv_no = inv_no
                    st.session_state.last_created_inv_type = "ارجاع"
                    st.session_state.return_cart = []; st.session_state.confirm_return = False; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                if na.button("❌ إلغاء والرجوع للتعديل", use_container_width=True, key="ret_confirm_no"):
                    st.session_state.confirm_return = False; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

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

                    # ── خانة سبب الارجاع الإجبارية ──
                    ret_reason_input = st.text_area(
                        "📝 سبب الارجاع * (إجباري)",
                        placeholder="يرجى كتابة سبب إرجاع المواد بوضوح...",
                        key="ret_reason_txt",
                        height=80
                    )
                    # ── خانة BOQ الإجبارية ──
                    ret_req_boq = st.text_input(
                        "📋 BOQ الحالة * (إجباري)",
                        placeholder="أدخل رقم أو وصف BOQ الحالة...",
                        key="ret_req_boq_val"
                    ).strip()

                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                    if rb2.button("🔍 معاينة وإرسال الطلب"):
                        if not ret_reason_input.strip():
                            st.error("❌ يرجى كتابة سبب الارجاع قبل المتابعة — هذا الحقل إجباري!")
                        elif not ret_req_boq:
                            st.error("❌ يرجى إدخال BOQ الحالة — هذا الحقل إجباري!")
                        else:
                            st.session_state.ret_req_review = True
                    st.markdown("</div>", unsafe_allow_html=True)

                    if st.session_state.ret_req_review:
                        st.write("---")
                        req_no_preview = "RR" + now_mecca().strftime("%d%H%M")
                        # استرجاع سبب الارجاع من session
                        _ret_reason = st.session_state.get('ret_reason_txt', '')
                        html_rr = render_return_invoice_html("فاتورة ارجاع مواد طوارئ — بانتظار الاعتماد",
                                                              st.session_state.ret_req_cart, rr_wh, rr_contractor,
                                                              u['full_name'], req_no_preview)
                        st.write("### 📄 معاينة فاتورة الطلب:")
                        components.html(html_rr, height=450, scrolling=True)
                        items_txt_rr = "، ".join([f"{i['name']} ({i['qty']})" for i in st.session_state.ret_req_cart])
                        st.markdown(f"""<div class='warn-box'>⚠️ <b>سيتم رفع طلب الارجاع التالي للاعتماد:</b><br>
                        المستودع: <b>{rr_wh}</b> | المقاول: <b>{rr_contractor}</b><br>
                        {items_txt_rr}<br>
                        <b>سبب الارجاع:</b> {_ret_reason}<br>
                        <small>لن تُضاف المواد إلى المستودع إلا بعد اعتماد مسؤول المستودع أو مدير النظام.</small>
                        </div>""", unsafe_allow_html=True)
                        col_send, col_cancel = st.columns([1,1])
                        if col_send.button("🚀 إرسال الطلب للاعتماد"):
                            ts = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                            c.execute("""INSERT INTO return_requests (request_no, warehouse, contractor, items_json, requester, status, return_reason, boq, invoice_html, timestamp)
                                         VALUES (?,?,?,?,?,?,?,?,?,?)""",
                                      (req_no_preview, rr_wh, rr_contractor,
                                       json.dumps(st.session_state.ret_req_cart),
                                       u['full_name'], "معلق", _ret_reason,
                                       st.session_state.get('ret_req_boq_val', ''),
                                       html_rr, ts))
                            conn.commit()
                            save_log("طلب ارجاع جديد", "—", 0,
                                     f"تقديم طلب ارجاع رقم [{req_no_preview}] للمستودع [{rr_wh}] من المقاول [{rr_contractor}] — السبب: {_ret_reason}",
                                     u['full_name'])
                            st.session_state.ret_req_cart = []; st.session_state.ret_req_review = False
                            st.session_state['last_ret_req_no'] = req_no_preview
                            st.rerun()
                        if col_cancel.button("❌ إلغاء"):
                            st.session_state.ret_req_review = False; st.rerun()

                if st.session_state.get('last_ret_req_no') and not st.session_state.ret_req_cart:
                    st.markdown(
                        f"<div style='background:#e8f5e9;border:2px solid #1daa60;border-radius:12px;padding:18px;text-align:center;direction:rtl;margin-top:16px;'>"
                        f"✅ <b>تم إرسال طلب الارجاع بنجاح — بانتظار الاعتماد</b><br>"
                        f"رقم الطلب: <span style='color:red;font-weight:900;font-size:18px;'>{st.session_state['last_ret_req_no']}</span><br>"
                        f"<small>لن تُضاف المواد إلى المستودع إلا بعد اعتماد مسؤول المستودع أو مدير النظام.</small>"
                        "</div>",
                        unsafe_allow_html=True)
                    if st.button("✖️ إغلاق الإشعار", key="close_ret_req_notif"):
                        st.session_state['last_ret_req_no'] = None; st.rerun()

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
        if role == "موجه بلاغات":
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
                                {f"<br>📝 <b>سبب الارجاع:</b> {rr['return_reason']}" if rr.get('return_reason') else ""}
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
                            {f"<br>📝 <b>سبب الارجاع:</b> {rr['return_reason']}" if rr.get('return_reason') else ""}
                            {f"<br>✅ اعتمده: <b>{rr['approved_by']}</b> في {rr['approved_at']}" if rr['approved_by'] else ""}
                        </div>""", unsafe_allow_html=True)
                        if st.button(f"👁️ عرض {rr['request_no']}", key=f"allrr_{rr['id']}"):
                            st.session_state.view_archived_html[f"all_{rr['id']}"] = not st.session_state.view_archived_html.get(f"all_{rr['id']}", False)
                        if st.session_state.view_archived_html.get(f"all_{rr['id']}", False):
                            components.html(rr['invoice_html'], height=500, scrolling=True)
                        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: نقل مواد بين المستودعات
    # ---------------------------------------------------------
    elif st.session_state.page == "stock_transfer":
        page_header("🚛", "نقل مواد بين المستودعات", "تحويل وإعادة توزيع المواد بين المستودعات الميدانية", "#0288d1")

        if not list_warehouses:
            st.warning("⚠️ يرجى تعريف المستودعات في الإعدادات أولاً.")
        else:
            # ── إشعار النجاح ──
            if st.session_state.last_created_inv_no and st.session_state.last_created_inv_type == "تحويل" and not st.session_state.transfer_cart:
                st.markdown(f"""
                <div dir="rtl" style="background:linear-gradient(135deg,#e8f5e9,#f1f8e9);
                    border:2px solid #1daa60;border-radius:16px;padding:24px;text-align:center;
                    box-shadow:0 4px 16px rgba(29,170,96,0.15);margin:16px 0;">
                    <div style="font-size:42px;margin-bottom:8px;">✅</div>
                    <div style="font-size:19px;font-weight:900;color:#1b5e20;margin-bottom:6px;">تم إنشاء الفاتورة بنجاح</div>
                    <div style="font-size:14px;color:#2e7d32;margin-bottom:12px;">فاتورة نقل مواد من مستودع إلى آخر</div>
                    <div style="font-size:28px;font-weight:900;color:#c62828;background:rgba(198,40,40,0.08);
                                border-radius:8px;padding:6px 18px;display:inline-block;">
                        {st.session_state.last_created_inv_no}
                    </div>
                </div>""", unsafe_allow_html=True)
                _tc1, _tc2, _tc3 = st.columns([2, 2, 1])
                if _tc1.button("👁️ مشاهدة الفاتورة وطباعتها", key="preview_trans_inv", use_container_width=True):
                    st.session_state["_view_inv_no"] = st.session_state.last_created_inv_no
                    st.session_state.page = "view_logs"
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()
                if _tc2.button("➕ إنشاء فاتورة نقل جديدة", key="new_trans_inv", use_container_width=True):
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()
                if _tc3.button("✖️ إغلاق", key="dismiss_trans_inv", use_container_width=True):
                    st.session_state.last_created_inv_no = None; st.session_state.last_created_inv_type = None; st.rerun()

            elif not st.session_state.confirm_transfer:
                section_card("📋 بيانات الفاتورة", "#0288d1")
                c1, c2 = st.columns(2)
                trans_wh_from = c1.selectbox("📤 من مستودع", list_warehouses, key="trans_from_sel")
                trans_wh_to   = c2.selectbox("📥 إلى مستودع", list_warehouses, key="trans_to_sel")
                if trans_wh_from == trans_wh_to:
                    st.error("❌ لا يمكن اختيار نفس المستودع كمصدر ومستهدف")
                else:
                    st.divider()
                    # ── إضافة مادة ──
                    a1, a2, a3 = st.columns([2, 1.5, 1])
                    trans_code = a1.text_input("كود المادة", key=f"trans_code_val_{st.session_state.input_trans_code}").strip()
                    trans_qty  = a2.number_input("الكمية", min_value=1, value=1, step=1, key=f"trans_qty_val_{st.session_state.input_trans_qty}")
                    a3.markdown("<br>", unsafe_allow_html=True)
                    if a3.button("➕ إضافة", use_container_width=True):
                        if trans_code:
                            mat = pd.read_sql(f"SELECT item_name, category FROM material_definitions WHERE item_code='{trans_code}'", conn)
                            if mat.empty:
                                st.error("❌ الكود غير معرّف في النظام")
                            else:
                                avail = int(pd.read_sql(f"SELECT COALESCE(SUM(qty),0) as t FROM inventory WHERE item_code='{trans_code}' AND warehouse='{trans_wh_from}'", conn).iloc[0]["t"])
                                already = sum(x["qty"] for x in st.session_state.transfer_cart if x["code"] == trans_code)
                                if avail < (trans_qty + already):
                                    st.error(f"❌ الرصيد غير كافٍ في المستودع المصدر — المتاح: {avail}")
                                else:
                                    ex = [i for i,x in enumerate(st.session_state.transfer_cart) if x["code"] == trans_code]
                                    if ex: st.session_state.transfer_cart[ex[0]]["qty"] += trans_qty
                                    else:  st.session_state.transfer_cart.append({"code": trans_code, "name": mat.iloc[0]["item_name"], "qty": trans_qty, "cat": mat.iloc[0]["category"]})
                                    st.session_state.input_trans_code += 1; st.session_state.input_trans_qty += 1; st.rerun()

                    # ── عرض السلة ──
                    if st.session_state.transfer_cart:
                        section_card("🚛 المواد في سلة النقل", "#004a99")
                        h1,h2,h3,h4,h5 = st.columns([1.5, 3, 1.5, 1.2, 0.6])
                        h1.markdown("**الكود**"); h2.markdown("**الاسم**"); h3.markdown("**الفئة**"); h4.markdown("**الكمية**"); h5.markdown("**حذف**")
                        _rm = None
                        for i, item in enumerate(st.session_state.transfer_cart):
                            c1,c2,c3,c4,c5 = st.columns([1.5, 3, 1.5, 1.2, 0.6])
                            avail_i = int(pd.read_sql(f"SELECT COALESCE(SUM(qty),0) as t FROM inventory WHERE item_code='{item['code']}' AND warehouse='{trans_wh_from}'", conn).iloc[0]["t"])
                            c1.write(item["code"]); c2.write(item["name"]); c3.write(item.get("cat",""))
                            nq = c4.number_input("", min_value=1, max_value=max(1,avail_i), value=min(int(item["qty"]),max(1,avail_i)), step=1, key=f"tq_{i}", label_visibility="collapsed")
                            if nq != int(item["qty"]): st.session_state.transfer_cart[i]["qty"] = nq; st.rerun()
                            if c5.button("🗑️", key=f"td_{i}"): _rm = i
                        if _rm is not None: st.session_state.transfer_cart.pop(_rm); st.rerun()

                        st.divider()
                        errs_t = validate_cart_stock(st.session_state.transfer_cart, trans_wh_from)
                        tot = sum(x["qty"] for x in st.session_state.transfer_cart)
                        st.markdown(f"**الإجمالي:** {len(st.session_state.transfer_cart)} صنف — {tot} وحدة")
                        b1, b2 = st.columns([1, 3])
                        if b1.button("🗑️ تفريغ السلة"):
                            st.session_state.transfer_cart = []; st.rerun()
                        if errs_t:
                            st.error("⛔ " + " | ".join(errs_t))
                        else:
                            st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                            if b2.button("🚀 تصدير فاتورة النقل", use_container_width=True):
                                st.session_state.confirm_transfer = True; st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

            else:
                # ── تأكيد النقل ──
                trans_wh_from = st.session_state.get("trans_from_sel", list_warehouses[0])
                trans_wh_to   = st.session_state.get("trans_to_sel", list_warehouses[-1] if len(list_warehouses) > 1 else list_warehouses[0])
                trans_inv_no_preview = now_mecca().strftime("%d%H%M")
                html_trans_invoice = render_transfer_invoice_html("فاتورة نقل مواد طوارئ من مستودع إلى آخر", st.session_state.transfer_cart, trans_wh_from, trans_wh_to, u["full_name"], trans_inv_no_preview)

                rows_html = "".join([
                    f"<tr><td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;'>{it['code']}</td>"
                    f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;'>{it['name']}</td>"
                    f"<td style='padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center;font-weight:700;color:#1565c0;'>{it['qty']}</td></tr>"
                    for it in st.session_state.transfer_cart
                ])
                st.markdown(f"""
                <div dir="rtl" style="background:#fff8e1;border:2px solid #f9a825;border-radius:14px;
                    padding:22px 26px;box-shadow:0 2px 12px rgba(249,168,37,0.2);">
                    <div style="font-size:18px;font-weight:900;color:#e65100;margin-bottom:10px;">⚠️ تأكيد تصدير فاتورة النقل</div>
                    <div style="font-size:14px;color:#555;margin-bottom:14px;">
                        سيتم <b style="color:#c62828;">خصم المواد</b> من مستودع
                        <b style="color:#c62828;">{trans_wh_from}</b>
                        و<b style="color:#2e7d32;">إضافتها</b> إلى مستودع
                        <b style="color:#2e7d32;">{trans_wh_to}</b>
                    </div>
                    <table style="width:100%;border-collapse:collapse;font-size:14px;background:white;border-radius:8px;overflow:hidden;">
                        <tr style="background:#004a99;color:white;">
                            <th style="padding:9px 12px;text-align:right;">كود المادة</th>
                            <th style="padding:9px 12px;text-align:right;">اسم المادة</th>
                            <th style="padding:9px 12px;text-align:center;">الكمية</th>
                        </tr>
                        {rows_html}
                    </table>
                </div>""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)
                ya, na = st.columns(2)
                st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                if ya.button("✅ تأكيد وإصدار الفاتورة", use_container_width=True, key="trans_confirm_yes"):
                    final_errs = validate_cart_stock(st.session_state.transfer_cart, trans_wh_from)
                    if final_errs:
                        st.error("⛔ تغيّر الرصيد — " + " | ".join(final_errs))
                        st.session_state.confirm_transfer = False
                    else:
                        # ملاحظة: الخصم والإضافة يتمان بعد توقيع وإرفاق أمين مستودع المقاول
                        archive_invoice("نقل", trans_inv_no_preview, trans_wh_from, trans_wh_to, "", u["full_name"], json.dumps(st.session_state.transfer_cart), html_trans_invoice)
                        save_log("إنشاء فاتورة نقل (في انتظار توقيع أمين المستودع)", "-", 0,
                                 f"نقل من [{trans_wh_from}] إلى [{trans_wh_to}] | {trans_inv_no_preview}", u["full_name"])
                        conn.commit()
                        st.session_state.last_trans_inv_html = html_trans_invoice
                        st.session_state.last_created_inv_no = trans_inv_no_preview
                        st.session_state.last_created_inv_type = "تحويل"
                        st.session_state.transfer_cart = []; st.session_state.confirm_transfer = False; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                if na.button("❌ إلغاء والرجوع للتعديل", use_container_width=True, key="trans_confirm_no"):
                    st.session_state.confirm_transfer = False; st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

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
                        "📍 مستودع الصرف:" if ef_type=="صرف" else "📍 المستودع الذي يستلم المواد:",
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
                        # التحقق من وجود تعديلات فعلية قبل الإصدار
                        has_changes = bool(changes)
                        if not has_changes:
                            st.warning("⚠️ لا يوجد تعديلات على الفاتورة. لم يتم إصدار فاتورة معدّلة.")
                        else:
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
    # صفحة: أرشيف فواتيري
    # ---------------------------------------------------------
    elif st.session_state.page == "my_invoices":
        st.markdown("<div class='main-title'>🗂️ أرشيف فواتيري</div>", unsafe_allow_html=True)
        st.info(f"📋 الفواتير التي قام بإصدارها: **{u['full_name']}**")

        # ── جلب آخر فاتورة لكل نوع من DB ──
        _inv_types = [("صرف", "#e65100", "🛒"), ("ارجاع", "#2e7d32", "🔄"), ("تحويل", "#1a237e", "🚛")]
        _latest_by_type = {}
        for _t, _c, _ic in _inv_types:
            _df_t = pd.read_sql(
                f"SELECT * FROM archived_invoices WHERE employee='{u['full_name']}'"
                f" AND invoice_type='{_t}' ORDER BY id DESC LIMIT 1", conn)
            if not _df_t.empty:
                _latest_by_type[_t] = (_df_t.iloc[0], _c, _ic)

        # ═══════════════════════════════════════════════════════
        # القسم الأول: آخر فاتورة تم إنشاؤها (حسب النوع)
        # ═══════════════════════════════════════════════════════
        if _latest_by_type:
            st.markdown("""
            <div style='display:flex;align-items:center;gap:10px;margin:12px 0 16px 0;direction:rtl;'>
                <div style='flex:1;height:3px;background:linear-gradient(to left,#004a99,transparent);border-radius:2px;'></div>
                <span style='background:#004a99;color:white;border-radius:20px;padding:6px 20px;
                             font-size:14px;font-weight:900;white-space:nowrap;letter-spacing:0.5px;
                             box-shadow:0 2px 8px rgba(0,74,153,0.3);'>🆕 آخر فاتورة تم إنشاؤها</span>
                <div style='flex:1;height:3px;background:linear-gradient(to right,#004a99,transparent);border-radius:2px;'></div>
            </div>""", unsafe_allow_html=True)

            # أزرار التبديل بين الأنواع
            _avail_types = list(_latest_by_type.keys())
            if 'latest_inv_type_sel' not in st.session_state or st.session_state['latest_inv_type_sel'] not in _avail_types:
                st.session_state['latest_inv_type_sel'] = _avail_types[0]

            _type_cols = st.columns(len(_avail_types))
            for _ci, _t in enumerate(_avail_types):
                _row, _clr, _ico = _latest_by_type[_t]
                _is_sel = st.session_state['latest_inv_type_sel'] == _t
                _btn_style = f"background:{_clr};" if _is_sel else ""
                if _type_cols[_ci].button(
                    f"{_ico} {_t}",
                    key=f"latest_type_btn_{_t}",
                    use_container_width=True,
                    type="primary" if _is_sel else "secondary"
                ):
                    st.session_state['latest_inv_type_sel'] = _t
                    st.rerun()

            # عرض آخر فاتورة للنوع المختار
            _sel_type = st.session_state['latest_inv_type_sel']
            if _sel_type in _latest_by_type:
                _lr, _inv_color, _inv_icon = _latest_by_type[_sel_type]
                _latest_id = int(_lr['id'])

                st.markdown(
                    f"<div style='background:#f9f9f9;border:2px solid {_inv_color};border-radius:10px;"
                    f"padding:12px 18px;margin:10px 0 12px 0;direction:rtl;'>"
                    f"{_inv_icon} <b>فاتورة <span style='color:{_inv_color};'>{_lr['invoice_type']}</span></b>"
                    f" — رقم: <span style='color:red;font-weight:900;font-size:17px;'>{_lr['invoice_no']}</span>"
                    f" &nbsp;|&nbsp; 📅 {str(_lr['timestamp'])[:10]}"
                    f"{f' &nbsp;|&nbsp; 📍 {_lr["warehouse_from"]}' if _lr['warehouse_from'] else ''}"
                    f"{f' &nbsp;|&nbsp; 🏗️ {_lr["contractor"]}' if _lr['contractor'] else ''}"
                    f"</div>",
                    unsafe_allow_html=True)

                _show_key = f"show_latest_inv_{_latest_id}"
                if _show_key not in st.session_state:
                    st.session_state[_show_key] = True

                if st.session_state[_show_key]:
                    components.html(_lr['html_content'], height=520, scrolling=True)
                    if st.button("🔒 إغلاق الفاتورة", key=f"close_latest_{_sel_type}", use_container_width=True):
                        st.session_state[_show_key] = False
                        st.rerun()
                else:
                    if st.button(f"👁️ عرض آخر فاتورة {_sel_type}", key=f"open_latest_{_sel_type}", use_container_width=True):
                        st.session_state[_show_key] = True
                        st.rerun()

        # ═══════════════════════════════════════════════════════
        # القسم الثاني: جميع الفواتير السابقة
        # ═══════════════════════════════════════════════════════
        st.markdown("""
        <div style='display:flex;align-items:center;gap:10px;margin:22px 0 16px 0;direction:rtl;'>
            <div style='flex:1;height:3px;background:linear-gradient(to left,#555,transparent);border-radius:2px;'></div>
            <span style='background:#555;color:white;border-radius:20px;padding:6px 20px;
                         font-size:14px;font-weight:900;white-space:nowrap;letter-spacing:0.5px;
                         box-shadow:0 2px 6px rgba(0,0,0,0.2);'>📋 جميع الفواتير السابقة</span>
            <div style='flex:1;height:3px;background:linear-gradient(to right,#555,transparent);border-radius:2px;'></div>
        </div>""", unsafe_allow_html=True)

        col_mf1, col_mf2, col_mf3 = st.columns([1, 1, 1.2])
        mf_type = col_mf1.selectbox("نوع الفاتورة:", ["الكل", "صرف", "ارجاع", "تحويل"], key="mf_type")
        mf_no   = col_mf2.text_input("رقم الفاتورة (اختياري):", key="mf_no").strip()
        mf_date = col_mf3.date_input("تصفية بالتاريخ (اختياري):", value=None, key="mf_date")

        mf_query = f"SELECT * FROM archived_invoices WHERE employee='{u['full_name']}'"
        # استبعاد آخر فاتورة لكل نوع من القائمة السابقة
        _excl_ids = [int(_latest_by_type[_t][0]['id']) for _t in _latest_by_type]
        if _excl_ids:
            mf_query += f" AND id NOT IN ({','.join(str(i) for i in _excl_ids)})"
        if mf_type != "الكل": mf_query += f" AND invoice_type='{mf_type}'"
        if mf_no:             mf_query += f" AND invoice_no LIKE '%{mf_no}%'"
        if mf_date:           mf_query += f" AND timestamp LIKE '{mf_date.strftime('%Y-%m-%d')}%'"
        mf_query += " ORDER BY id DESC"
        df_mf = pd.read_sql(mf_query, conn)

        if df_mf.empty:
            st.info("ℹ️ لا توجد فواتير سابقة أخرى.")
        else:
            st.caption(f"📦 إجمالي: {len(df_mf)} فاتورة")
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
        can_manage = role != "موجه بلاغات"
        if not can_manage:
            st.error("❌ هذه الصفحة متاحة لمدير النظام ومسؤول المستودع فقط.")
            st.stop()

        tab_logs_actions, tab_material_track, tab_invoices_archive, tab_cancel_invoices_mgr, tab_cancelled_invoices, tab_my_invoices_log = st.tabs([
            "📋 سجل تتبع حركات الموظفين",
            "🔍 تتبع مسار المادة",
            "🗂️ أرشيف الفواتير والمستندات",
            "🚫 إلغاء الفواتير",
            "📑 سجل الفواتير الملغية",
            "📄 فواتير منشأة بواسطتي"
        ])

        # ══════════════════════════════════════════════════════
        # تبويب ١: سجل تتبع حركات الموظفين
        # ══════════════════════════════════════════════════════
        with tab_logs_actions:
            section_card("🔍 البحث والفرز في سجل تتبع حركات الموظفين", "#1a3a5c")
            fl1, fl2 = st.columns([2, 2])
            fl3, fl4, fl5 = st.columns([1.5, 1.5, 1])

            # قائمة الموظفين
            _emp_list = pd.read_sql("SELECT DISTINCT user_name FROM action_logs ORDER BY user_name", conn)['user_name'].tolist()
            search_emp_name  = fl1.selectbox("👤 فلترة بالموظف:", ["الكل"] + _emp_list, key="log_emp_filter")
            search_log_txt   = fl2.text_input("🔎 بحث بالكود أو التفاصيل:", key="log_search")
            type_log_filter  = fl3.selectbox("نوع الحركة:", [
                "عرض الكل", "تغذية مستودع", "صرف", "ارجاع", "نقل", "اعتماد", "إلغاء"
            ], key="log_type")
            log_date_from    = fl4.date_input("📅 من تاريخ:", value=None, key="log_date_from")
            log_date_to      = fl5.date_input("📅 إلى تاريخ:", value=None, key="log_date_to")

            log_query = """SELECT id, log_type as 'نوع العملية', item_code as 'كود المادة',
                           qty as 'الكمية', details as 'التفاصيل',
                           user_name as 'الموظف', timestamp as 'التاريخ والوقت'
                           FROM action_logs WHERE 1=1"""
            if search_emp_name != "الكل":
                log_query += f" AND user_name='{search_emp_name}'"
            if type_log_filter != "عرض الكل":
                log_query += f" AND log_type LIKE '%{type_log_filter}%'"
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
                html_table(df_display, accent='#1a3a5c', info_label='📋 إجمالي العمليات المعروضة: ')
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
                        section_card("📊 الرصيد الحالي في المستودعات", "#004a99")
                        html_table(df_stock, accent='#004a99', info_label='📍 المستودعات: ')
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

                    section_card(f"📋 سجل حركات المادة [{track_code}]", "#1a3a5c")
                    if not df_track_logs.empty:
                        html_table(df_track_logs, accent='#1a3a5c', info_label='📋 الحركات المسجلة: ')
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
                    section_card(f"📄 الفواتير التي تحتوي على المادة [{track_code}]", "#004a99")
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
                        html_table(df_inv_sum, accent='#004a99', info_label='📄 الفواتير: ')
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

            # ── إذا جاء المستخدم من زر "مشاهدة الفاتورة" بعد التصدير ──
            _auto_inv_no = st.session_state.get('_view_inv_no', '') or ''
            if _auto_inv_no:
                st.success(f"✅ عرض الفاتورة رقم: **{_auto_inv_no}**")
                st.session_state['_view_inv_no'] = None

            # ── حذف تلقائي للفواتير الأقدم من 90 يوماً ──
            try:
                from datetime import timedelta
                cutoff_inv = (now_mecca() - timedelta(days=90)).strftime("%Y-%m-%d")
                c.execute("DELETE FROM archived_invoices WHERE timestamp < ?", (cutoff_inv,))
                conn.commit()
            except Exception:
                pass

            # ── فلاتر البحث المتقدمة ──
            _arch_col1, _arch_col2, _arch_col3 = st.columns([1, 1, 1])
            _arch_col4, _arch_col5, _arch_col6, _arch_col7 = st.columns([1, 1, 1, 1])

            filter_arch_type    = _arch_col1.selectbox("نوع المستند:", ["الكل", "صرف", "ارجاع", "تحويل"], key="arch_type")
            search_arch_no      = _arch_col2.text_input("ابحث برقم الفاتورة:", value=_auto_inv_no, key="arch_no")
            search_arch_boq     = _arch_col3.text_input("🔍 ابحث برقم BOQ:", key="arch_boq").strip()
            search_arch_date    = _arch_col4.date_input("من تاريخ:", value=None, key="arch_date")
            search_arch_date_to = _arch_col5.date_input("إلى تاريخ:", value=None, key="arch_date_to")

            # فلتر المقاول (لإظهار فواتير مقاول محدد)
            _contractors_arch = ["الكل"] + list_contractors
            filter_arch_contractor = _arch_col6.selectbox("🏗️ اختر مقاول:", _contractors_arch, key="arch_contractor")
            # فلتر نوع إصدار الفاتورة
            filter_arch_source = _arch_col7.selectbox("📦 نوع العرض:", ["الكل", "فواتير صرف المستودع", "فواتير تسليم المقاولين"], key="arch_source")

            # ── استعلام بدون html_content لتحسين الأداء ──
            arch_query = """SELECT id, invoice_type, invoice_no, warehouse_from,
                            warehouse_to, contractor, employee, boq, timestamp
                            FROM archived_invoices WHERE 1=1"""
            if filter_arch_type != "الكل":
                arch_query += f" AND invoice_type='{filter_arch_type}'"
            if search_arch_no.strip():
                arch_query += f" AND invoice_no LIKE '%{search_arch_no.strip()}%'"
            if search_arch_boq:
                arch_query += f" AND boq LIKE '%{search_arch_boq}%'"
            if search_arch_date is not None:
                arch_query += f" AND timestamp >= '{search_arch_date.strftime('%Y-%m-%d')}'"
            if search_arch_date_to is not None:
                arch_query += f" AND timestamp <= '{search_arch_date_to.strftime('%Y-%m-%d')} 23:59:59'"
            if filter_arch_contractor != "الكل":
                arch_query += f" AND contractor LIKE '%{filter_arch_contractor}%'"
            if filter_arch_source == "فواتير صرف المستودع":
                arch_query += " AND invoice_type IN ('صرف', 'تحويل')"
            elif filter_arch_source == "فواتير تسليم المقاولين":
                arch_query += " AND invoice_type = 'ارجاع'"
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
                        📅 تاريخ القيد والأرشفة الفعلي: {row['timestamp']} | 📍 المستودع المصدر: {row['warehouse_from'] if row['warehouse_from'] else 'N/A'} {f" ➡️ المستودع المستلم: {row['warehouse_to']}" if row['warehouse_to'] else ''} {f" | 🏗️ المقاول المستلم: {row['contractor']}" if row['contractor'] else ''}<br>
                        {f"📋 <b>BOQ الحالة:</b> <span style='color:#e65100;font-weight:bold;'>{row['boq']}</span>" if row.get('boq') else ''}
                    </div>""", unsafe_allow_html=True)

                    if st.button(f"👁️ عرض ومعاينة وطباعة الفاتورة رقم {row['invoice_no']}", key=f"btn_arch_{inv_id}"):
                        st.session_state[arch_view_key] = not st.session_state[arch_view_key]

                    # ── إلغاء الفاتورة مباشرة (مدير النظام / مسؤول المستودع) ──
                    if role in ("مدير نظام", "أمين مستودع", "موظف مستودع"):
                        direct_cancel_key = f"direct_cancel_{inv_id}"
                        direct_cancel_form_key = f"direct_cancel_form_{inv_id}"
                        if direct_cancel_key not in st.session_state: st.session_state[direct_cancel_key] = False
                        if st.session_state[direct_cancel_key]:
                            with st.container():
                                st.markdown(f"<div style='background:#fff3cd;border:2px solid #d32f2f;border-radius:10px;padding:14px;direction:rtl;margin:6px 0;'>", unsafe_allow_html=True)
                                st.markdown(f"**🚫 إلغاء الفاتورة رقم {row['invoice_no']}**")
                                dc_wh_opts = list_warehouses
                                dc_wh_default = row.get('warehouse_from','')
                                dc_wh_idx = dc_wh_opts.index(dc_wh_default) if dc_wh_default in dc_wh_opts else 0
                                dc_wh = st.selectbox("📍 المستودع الذي ستُرجع إليه المواد *",
                                                      dc_wh_opts, index=dc_wh_idx, key=f"dc_wh_{inv_id}")
                                dc_reason = st.text_area("📝 سبب الإلغاء * (إجباري)",
                                                          placeholder="اكتب سبب الإلغاء...",
                                                          key=f"dc_reason_{inv_id}", height=70)
                                dc_boq = st.text_input("📋 BOQ الحالة * (إجباري)",
                                                         placeholder="أدخل رقم أو وصف BOQ...",
                                                         key=f"dc_boq_{inv_id}").strip()
                                dc_confirm_key = f"dc_confirm_{inv_id}"
                                if dc_confirm_key not in st.session_state: st.session_state[dc_confirm_key] = False
                                dc_col1, dc_col2 = st.columns([1, 1])
                                if not st.session_state[dc_confirm_key]:
                                    st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                                    if dc_col1.button("🚫 تأكيد الإلغاء", key=f"dc_submit_{inv_id}"):
                                        if not dc_reason.strip():
                                            st.error("❌ سبب الإلغاء إجباري!")
                                        elif not dc_boq:
                                            st.error("❌ BOQ الحالة إجباري!")
                                        else:
                                            st.session_state[dc_confirm_key] = True; st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)
                                    if dc_col2.button("❌ إلغاء", key=f"dc_abort_{inv_id}"):
                                        st.session_state[direct_cancel_key] = False; st.rerun()
                                else:
                                    try:
                                        _dc_items = json.loads(pd.read_sql(f"SELECT items_json FROM archived_invoices WHERE id={inv_id}", conn).iloc[0]['items_json'])
                                    except Exception:
                                        _dc_items = []
                                    _dc_sum = "، ".join([f"{i.get('name','?')} ({i.get('qty',0)})" for i in _dc_items])
                                    st.markdown(f"""<div class='warn-box'>⚠️ <b>هل أنت متأكد من إلغاء الفاتورة ({row['invoice_no']})؟</b><br>
                                    سيتم ارجاع هذه المواد إلى مستودع <b>{dc_wh}</b>:<br>{_dc_sum}</div>""",
                                    unsafe_allow_html=True)
                                    dc_yes, dc_no = st.columns([1,1])
                                    if dc_yes.button("✅ نعم، إلغاء الفاتورة", key=f"dc_yes_{inv_id}"):
                                        ts_dc = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                                        req_dc = "CR" + now_mecca().strftime("%d%H%M%S")
                                        _dc_html_row = pd.read_sql(f"SELECT html_content FROM archived_invoices WHERE id={inv_id}", conn)
                                        _dc_html = _dc_html_row.iloc[0]['html_content'] if not _dc_html_row.empty else ""
                                        # إدخال طلب الإلغاء كمعتمد مباشرة
                                        c.execute("""INSERT INTO cancel_invoice_requests
                                                     (request_no, invoice_no, invoice_type, warehouse_return, contractor,
                                                      items_json, cancel_reason, boq, requester, status,
                                                      invoice_html, timestamp, approved_by, approved_at)
                                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                                  (req_dc, row['invoice_no'], row['invoice_type'],
                                                   dc_wh, row.get('contractor',''),
                                                   pd.read_sql(f"SELECT items_json FROM archived_invoices WHERE id={inv_id}", conn).iloc[0]['items_json'],
                                                   dc_reason, dc_boq, u['full_name'], "معتمد",
                                                   _dc_html, ts_dc, u['full_name'], ts_dc))
                                        # ارجاع المواد للمستودع
                                        for fitem in _dc_items:
                                            c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                                      (fitem.get('code',''), int(fitem.get('qty',0)), dc_wh,
                                                       row.get('contractor',''), fitem.get('cat','')))
                                            save_log("إلغاء فاتورة مباشر", fitem.get('code',''), int(fitem.get('qty',0)),
                                                     f"إلغاء الفاتورة [{row['invoice_no']}] وارجاع المواد لمستودع [{dc_wh}] — السبب: {dc_reason} | BOQ: {dc_boq}",
                                                     u['full_name'])
                                        conn.commit()
                                        st.session_state[direct_cancel_key] = False
                                        st.session_state[dc_confirm_key] = False
                                        st.success(f"✅ تم إلغاء الفاتورة ({row['invoice_no']}) وارجاع المواد لمستودع [{dc_wh}] بنجاح!")
                                        st.rerun()
                                    if dc_no.button("❌ إلغاء", key=f"dc_no_{inv_id}"):
                                        st.session_state[dc_confirm_key] = False; st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                        else:
                            st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                            if st.button(f"🚫 إلغاء الفاتورة {row['invoice_no']}", key=f"cancel_arch_{inv_id}"):
                                st.session_state[direct_cancel_key] = True; st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

                    # ── جلب HTML عند الطلب فقط ──
                    if st.session_state[arch_view_key]:
                        with st.spinner("جاري تحميل الفاتورة..."):
                            _html_r = pd.read_sql(
                                "SELECT html_content FROM archived_invoices WHERE id=?",
                                conn, params=(inv_id,))
                            if not _html_r.empty:
                                st.write("<p style='margin-top:10px;'></p>", unsafe_allow_html=True)
                                st.markdown("**📄 الفاتورة الأصلية:**")
                                components.html(_html_r.iloc[0]['html_content'], height=520, scrolling=True)

                            # ── عرض الفاتورة الموقعة من أمين مستودع المقاول ──
                            _signed_r = pd.read_sql(
                                "SELECT * FROM signed_invoices WHERE invoice_no=? AND invoice_type=?",
                                conn, params=(str(row['invoice_no']), str(row['invoice_type'])))
                            if not _signed_r.empty:
                                _sr = _signed_r.iloc[0]
                                _sr_status = str(_sr.get('status',''))
                                _sr_color  = {"معتمد":"#1daa60","مرفوض":"#d32f2f","مُعادة":"#e65100","بانتظار الاعتماد":"#0288d1"}.get(_sr_status,"#9e9e9e")
                                st.markdown("---")
                                st.markdown(f"""
                                <div style='background:#f8f9fa;border-right:5px solid {_sr_color};border-radius:8px;
                                    padding:10px 14px;direction:rtl;font-size:13px;margin:8px 0;'>
                                    <b>📎 الفاتورة الموقعة من أمين مستودع المقاول</b><br>
                                    <span style='background:{_sr_color};color:white;border-radius:6px;padding:1px 8px;font-size:11px;'>{_sr_status}</span><br>
                                    👤 <b>أرفقها:</b> {_sr['signed_by']} | 📅 {_sr['signed_at']}
                                    {f"<br>👤 <b>راجعها:</b> {_sr['reviewed_by']} | {_sr['reviewed_at']}" if str(_sr.get('reviewed_by','')).strip() else ""}
                                    {f"<br>💬 <b>الملاحظة:</b> {_sr['admin_notes']}" if str(_sr.get('admin_notes','')).strip() else ""}
                                </div>""", unsafe_allow_html=True)
                                _sb64 = _sr.get('signed_image_base64', '')
                                _imgk2 = f"arch_sig_img_{inv_id}"
                                if st.button("🖼️ عرض صورة الفاتورة الموقعة", key=f"arch_img_btn_{inv_id}"):
                                    st.session_state[_imgk2] = not st.session_state.get(_imgk2, False)
                                if st.session_state.get(_imgk2, False) and _sb64:
                                    st.markdown(
                                        f'<img src="data:image/jpeg;base64,{_sb64}" style="max-width:100%;border:2px solid {_sr_color};border-radius:8px;margin-top:8px;">',
                                        unsafe_allow_html=True)
                            else:
                                st.markdown("---")
                                st.info("⏳ لم يتم إرفاق الفاتورة الموقعة من أمين مستودع المقاول بعد.")
                                st.write("---")

                    st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)
            else:
                st.info("ℹ️ لم يتم العثور على أي مستندات مؤرشفة تطابق الكلمات المفتاحية أو التاريخ المحدد حالياً.")

        # ══════════════════════════════════════════════════════
        # تبويب ٤: إلغاء الفواتير — قسم منفصل كامل الصلاحية
        # ══════════════════════════════════════════════════════
        with tab_cancel_invoices_mgr:
            st.write("##### 🚫 إلغاء الفواتير — عرض جميع الفواتير مع إمكانية الإلغاء المباشر")
            st.info("ℹ️ اختر الفاتورة من القائمة، شاهد محتواها، ثم ألغِها مع اختيار المستودع وسبب الإلغاء. ستُرجع المواد تلقائياً بعد التأكيد.")

            # ── فلاتر البحث ──
            cm_c1, cm_c2, cm_c3, cm_c4 = st.columns([1, 1, 1.5, 1.2])
            cm_type_f   = cm_c1.selectbox("نوع الفاتورة:", ["الكل", "صرف", "ارجاع", "تحويل"], key="cm_type_f")
            cm_no_f     = cm_c2.text_input("رقم الفاتورة:", key="cm_no_f").strip()
            cm_boq_f    = cm_c3.text_input("🔍 BOQ الحالة:", key="cm_boq_f").strip()
            cm_date_f   = cm_c4.date_input("تصفية بالتاريخ:", value=None, key="cm_date_f")

            cm_query = """SELECT id, invoice_type, invoice_no, warehouse_from,
                          warehouse_to, contractor, employee, boq, timestamp
                          FROM archived_invoices WHERE 1=1"""
            if cm_type_f != "الكل":
                cm_query += f" AND invoice_type='{cm_type_f}'"
            if cm_no_f:
                cm_query += f" AND invoice_no LIKE '%{cm_no_f}%'"
            if cm_boq_f:
                cm_query += f" AND boq LIKE '%{cm_boq_f}%'"
            if cm_date_f:
                cm_query += f" AND timestamp >= '{cm_date_f.strftime('%Y-%m-%d')}'"
            cm_query += " ORDER BY id DESC"

            df_cm = pd.read_sql(cm_query, conn)

            if df_cm.empty:
                st.info("ℹ️ لا توجد فواتير تطابق الفلاتر المحددة.")
            else:
                st.success(f"✅ تم العثور على ({len(df_cm)}) فاتورة.")
                st.markdown("---")

                for _, cm_row in df_cm.iterrows():
                    cm_inv_id   = int(cm_row['id'])
                    cm_view_key = f"cm_view_{cm_inv_id}"
                    cm_form_key = f"cm_cancel_{cm_inv_id}"
                    cm_conf_key = f"cm_conf_{cm_inv_id}"
                    for _k in [cm_view_key, cm_form_key, cm_conf_key]:
                        if _k not in st.session_state:
                            st.session_state[_k] = False

                    # بطاقة الفاتورة
                    _type_color = "#e65100" if cm_row['invoice_type']=="صرف" else ("#2e7d32" if cm_row['invoice_type']=="ارجاع" else "#1a237e")
                    st.markdown(f"""
                    <div style='background:rgba(255,255,255,0.9);border-right:5px solid {_type_color};
                                border-radius:10px;padding:12px 16px;margin-bottom:6px;direction:rtl;'>
                        <b style='color:{_type_color};'>فاتورة {cm_row['invoice_type']}</b>
                        رقم <span style='color:red;font-weight:900;font-size:15px;'>{cm_row['invoice_no']}</span>
                        &nbsp;|&nbsp; 📅 {cm_row['timestamp']}<br>
                        📍 {cm_row['warehouse_from'] or 'N/A'}
                        {f" ➡️ {cm_row['warehouse_to']}" if cm_row['warehouse_to'] else ""}
                        {f" &nbsp;|&nbsp; 🏗️ {cm_row['contractor']}" if cm_row['contractor'] else ""}
                        &nbsp;|&nbsp; 👤 {cm_row['employee']}
                        {f"<br>📋 <b>BOQ:</b> <span style='color:#e65100;'>{cm_row['boq']}</span>" if cm_row.get('boq') else ""}
                    </div>""", unsafe_allow_html=True)

                    # أزرار: عرض الفاتورة + إلغاء
                    btn_col_v, btn_col_c = st.columns([1, 1])
                    if btn_col_v.button(f"👁️ عرض الفاتورة", key=f"cm_view_btn_{cm_inv_id}"):
                        st.session_state[cm_view_key] = not st.session_state[cm_view_key]
                        if st.session_state[cm_view_key]:
                            st.session_state[cm_form_key] = False

                    st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                    if btn_col_c.button(f"🚫 إلغاء الفاتورة", key=f"cm_cancel_btn_{cm_inv_id}"):
                        st.session_state[cm_form_key] = not st.session_state[cm_form_key]
                        if st.session_state[cm_form_key]:
                            st.session_state[cm_view_key] = False
                            st.session_state[cm_conf_key] = False
                    st.markdown("</div>", unsafe_allow_html=True)

                    # عرض الفاتورة
                    if st.session_state[cm_view_key]:
                        with st.spinner("جاري تحميل الفاتورة..."):
                            _cm_html = pd.read_sql(
                                "SELECT html_content FROM archived_invoices WHERE id=?",
                                conn, params=(cm_inv_id,))
                            if not _cm_html.empty:
                                components.html(_cm_html.iloc[0]['html_content'], height=520, scrolling=True)

                    # نموذج الإلغاء
                    if st.session_state[cm_form_key]:
                        with st.container():
                            st.markdown("""<div style='background:rgba(255,235,238,0.95);
                                border:2px solid #d32f2f;border-radius:12px;
                                padding:16px;margin:8px 0;direction:rtl;'>""",
                                unsafe_allow_html=True)
                            st.markdown(f"**🚫 إلغاء الفاتورة رقم {cm_row['invoice_no']}**")

                            # اختيار المستودع
                            _cm_wh_opts = list_warehouses
                            _cm_wh_def  = cm_row.get('warehouse_from', '')
                            _cm_wh_idx  = _cm_wh_opts.index(_cm_wh_def) if _cm_wh_def in _cm_wh_opts else 0
                            cm_sel_wh = st.selectbox(
                                "📍 المستودع الذي ستُرجع إليه المواد *",
                                _cm_wh_opts, index=_cm_wh_idx,
                                key=f"cm_wh_{cm_inv_id}")

                            cm_reason = st.text_area(
                                "📝 سبب الإلغاء * (إجباري)",
                                placeholder="اكتب سبب الإلغاء بوضوح...",
                                key=f"cm_reason_{cm_inv_id}", height=75)

                            cm_boq_inp = st.text_input(
                                "📋 BOQ الحالة * (إجباري)",
                                placeholder="أدخل رقم أو وصف BOQ...",
                                key=f"cm_boq_{cm_inv_id}").strip()

                            st.markdown("</div>", unsafe_allow_html=True)

                            if not st.session_state[cm_conf_key]:
                                _ca1, _ca2 = st.columns([1, 1])
                                st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                                if _ca1.button("⚠️ متابعة الإلغاء", key=f"cm_proceed_{cm_inv_id}"):
                                    if not cm_reason.strip():
                                        st.error("❌ سبب الإلغاء إجباري!")
                                    elif not cm_boq_inp:
                                        st.error("❌ BOQ الحالة إجباري!")
                                    else:
                                        st.session_state[cm_conf_key] = True
                                        st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)
                                if _ca2.button("❌ إلغاء", key=f"cm_abort_{cm_inv_id}"):
                                    st.session_state[cm_form_key] = False
                                    st.session_state[cm_conf_key] = False
                                    st.rerun()
                            else:
                                # جلب المواد للتأكيد
                                try:
                                    _cm_items_r = pd.read_sql(
                                        "SELECT items_json FROM archived_invoices WHERE id=?",
                                        conn, params=(cm_inv_id,))
                                    _cm_items = json.loads(_cm_items_r.iloc[0]['items_json']) if not _cm_items_r.empty else []
                                except Exception:
                                    _cm_items = []

                                _cm_sum = "، ".join([f"{i.get('name','?')} ({i.get('qty',0)})" for i in _cm_items])
                                _cm_wh_val  = st.session_state.get(f"cm_wh_{cm_inv_id}", cm_sel_wh)
                                _cm_rsn_val = st.session_state.get(f"cm_reason_{cm_inv_id}", cm_reason)
                                _cm_boq_val = st.session_state.get(f"cm_boq_{cm_inv_id}", cm_boq_inp)

                                st.markdown(f"""
                                <div class='warn-box'>
                                ⚠️ <b>هل أنت متأكد من إلغاء الفاتورة ({cm_row['invoice_no']})؟</b><br>
                                سيتم ارجاع المواد التالية إلى مستودع <b>{_cm_wh_val}</b>:<br>
                                {_cm_sum or "لا توجد مواد"}<br>
                                <b>سبب الإلغاء:</b> {_cm_rsn_val} | <b>BOQ:</b> {_cm_boq_val}
                                </div>""", unsafe_allow_html=True)

                                _cy, _cn = st.columns([1, 1])
                                st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                                if _cy.button("✅ نعم، تأكيد الإلغاء وإرجاع المواد", key=f"cm_yes_{cm_inv_id}"):
                                    ts_cm = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                                    req_cm = "CR" + now_mecca().strftime("%d%H%M%S")
                                    _cm_html_r = pd.read_sql(
                                        "SELECT html_content FROM archived_invoices WHERE id=?",
                                        conn, params=(cm_inv_id,))
                                    _cm_html_c = _cm_html_r.iloc[0]['html_content'] if not _cm_html_r.empty else ""
                                    _cm_items_json = pd.read_sql(
                                        "SELECT items_json FROM archived_invoices WHERE id=?",
                                        conn, params=(cm_inv_id,)).iloc[0]['items_json']

                                    # حفظ طلب الإلغاء كمعتمد
                                    c.execute("""INSERT INTO cancel_invoice_requests
                                                 (request_no, invoice_no, invoice_type, warehouse_return,
                                                  contractor, items_json, cancel_reason, boq, requester,
                                                  status, invoice_html, timestamp, approved_by, approved_at)
                                                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                                              (req_cm, cm_row['invoice_no'], cm_row['invoice_type'],
                                               _cm_wh_val, cm_row.get('contractor', ''),
                                               _cm_items_json, _cm_rsn_val, _cm_boq_val,
                                               u['full_name'], "معتمد", _cm_html_c,
                                               ts_cm, u['full_name'], ts_cm))

                                    # إرجاع المواد للمستودع
                                    for fitem in _cm_items:
                                        c.execute("""INSERT INTO inventory
                                                     (item_code, qty, warehouse, contractor, category)
                                                     VALUES (?,?,?,?,?)""",
                                                  (fitem.get('code', ''), int(fitem.get('qty', 0)),
                                                   _cm_wh_val, cm_row.get('contractor', ''),
                                                   fitem.get('cat', '')))
                                        save_log("إلغاء فاتورة",
                                                 fitem.get('code', ''),
                                                 int(fitem.get('qty', 0)),
                                                 f"إلغاء الفاتورة [{cm_row['invoice_no']}] وارجاع المواد "
                                                 f"لمستودع [{_cm_wh_val}] — السبب: {_cm_rsn_val} | BOQ: {_cm_boq_val}",
                                                 u['full_name'])
                                    conn.commit()

                                    # تصفير حالة هذه الفاتورة
                                    st.session_state[cm_form_key] = False
                                    st.session_state[cm_conf_key] = False
                                    st.session_state[cm_view_key] = False
                                    st.success(f"✅ تم إلغاء الفاتورة ({cm_row['invoice_no']}) وارجاع المواد لمستودع [{_cm_wh_val}] بنجاح!")
                                    st.rerun()
                                st.markdown("</div>", unsafe_allow_html=True)

                                if _cn.button("❌ رجوع", key=f"cm_no_{cm_inv_id}"):
                                    st.session_state[cm_conf_key] = False
                                    st.rerun()

                    st.markdown("<hr style='margin:6px 0;'>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════
        # تبويب ٥: سجل الفواتير الملغية
        # ══════════════════════════════════════════════════════
        with tab_cancelled_invoices:
            st.write("##### 🚫 أرشيف الفواتير الملغية — طلبات الإلغاء المعتمدة والمرفوضة والمعلقة")

            # ── فلاتر البحث ──
            ci_c1, ci_c2, ci_c3 = st.columns([1, 1.5, 1.2])
            ci_status_f   = ci_c1.selectbox("الحالة:", ["الكل", "معلق", "معتمد", "مرفوض"], key="ci_status_f")
            ci_search_req = ci_c2.text_input("ابحث برقم الطلب أو الفاتورة أو مقدم الطلب:", key="ci_search_req").strip()
            ci_date_f     = ci_c3.date_input("تصفية بالتاريخ:", value=None, key="ci_date_f")

            ci_query = "SELECT * FROM cancel_invoice_requests WHERE 1=1"
            if ci_status_f != "الكل":
                ci_query += f" AND status='{ci_status_f}'"
            if ci_search_req:
                ci_query += f" AND (request_no LIKE '%{ci_search_req}%' OR invoice_no LIKE '%{ci_search_req}%' OR requester LIKE '%{ci_search_req}%')"
            if ci_date_f:
                ci_query += f" AND timestamp LIKE '{ci_date_f.strftime('%Y-%m-%d')}%'"
            ci_query += " ORDER BY id DESC"

            df_cancelled = pd.read_sql(ci_query, conn)

            if df_cancelled.empty:
                st.info("ℹ️ لا توجد طلبات إلغاء فواتير تطابق الفلاتر المحددة.")
            else:
                st.success(f"✅ تم العثور على ({len(df_cancelled)}) طلب إلغاء.")
                st.markdown("---")

                for _, cr in df_cancelled.iterrows():
                    sc_ci = "#2e7d32" if cr['status']=="معتمد" else ("#d32f2f" if cr['status']=="مرفوض" else "#f9a825")
                    ci_view_key = f"ci_arch_view_{cr['id']}"
                    if ci_view_key not in st.session_state:
                        st.session_state[ci_view_key] = False

                    st.markdown(f"""
                    <div style='background:rgba(252,228,236,0.7);border-right:6px solid {sc_ci};
                                border-radius:10px;padding:14px 18px;margin-bottom:10px;direction:rtl;'>
                        🚫 <b>طلب إلغاء رقم (<span style='color:red;'>{cr['request_no']}</span>)</b>
                        <span style='background:{sc_ci};color:white;border-radius:8px;padding:2px 10px;font-size:13px;margin-right:8px;'>{cr['status']}</span><br>
                        📄 <b>رقم الفاتورة:</b> {cr['invoice_no']} ({cr['invoice_type']}) |
                        👤 <b>مقدم الطلب:</b> {cr['requester']}<br>
                        📍 <b>المستودع المُرجَع إليه:</b> {cr['warehouse_return']} |
                        🏗️ <b>المقاول:</b> {cr['contractor']}<br>
                        📝 <b>سبب الإلغاء:</b> {cr['cancel_reason']}<br>
                        📅 <b>تاريخ الطلب:</b> {cr['timestamp']}
                        {f"<br>✅ <b>اعتمده:</b> <span style='color:#2e7d32;font-weight:bold;'>{cr['approved_by']}</span> في {cr['approved_at']}" if cr.get('approved_by') else ""}
                    </div>""", unsafe_allow_html=True)

                    _ci_col1, _ci_col2 = st.columns([1, 1])
                    with _ci_col1:
                        if st.button(f"👁️ معاينة الفاتورة {cr['invoice_no']}", key=f"ci_preview_{cr['id']}"):
                            st.session_state[ci_view_key] = not st.session_state[ci_view_key]
                    with _ci_col2:
                        # زر إعادة الفاتورة (فقط للملغية المعتمدة)
                        if cr['status'] == "معتمد" and role == "مدير نظام":
                            _restore_key = f"confirm_restore_{cr['id']}"
                            if st.button(f"↩️ إعادة الفاتورة", key=f"restore_btn_{cr['id']}",
                                        help="إعادة هذه الفاتورة إلى الأرشيف كفاتورة فعّالة"):
                                st.session_state[_restore_key] = True
                            if st.session_state.get(_restore_key, False):
                                st.warning(f"⚠️ هل تريد إعادة الفاتورة ({cr['invoice_no']}) وإلغاء طلب الإلغاء؟")
                                _rc1, _rc2 = st.columns([1,1])
                                if _rc1.button("✅ نعم، أعِد الفاتورة", key=f"restore_yes_{cr['id']}"):
                                    c.execute("UPDATE cancel_invoice_requests SET status='مُعادة', approved_by=?, approved_at=? WHERE id=?",
                                              (u['full_name'], now_mecca().strftime("%Y-%m-%d %H:%M:%S"), int(cr['id'])))
                                    save_log("إعادة فاتورة ملغية", str(cr['invoice_no']), 0,
                                             f"تم إعادة الفاتورة [{cr['invoice_no']}] من حالة الإلغاء بواسطة {u['full_name']}", u['full_name'])
                                    conn.commit()
                                    st.session_state[_restore_key] = False
                                    st.success(f"✅ تمت إعادة الفاتورة ({cr['invoice_no']}) بنجاح.")
                                    st.rerun()
                                if _rc2.button("❌ لا، إلغاء", key=f"restore_no_{cr['id']}"):
                                    st.session_state[_restore_key] = False
                                    st.rerun()

                    if st.session_state[ci_view_key] and cr.get('invoice_html'):
                        components.html(cr['invoice_html'], height=500, scrolling=True)

                    st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════
        # تبويب ٦: فواتير منشأة بواسطتي
        # ══════════════════════════════════════════════════════
        with tab_my_invoices_log:
            st.write(f"##### 📄 الفواتير التي أنشأتها أنت: **{u['full_name']}**")

            # ── فلاتر البحث ──
            mi_c1, mi_c2, mi_c3, mi_c4 = st.columns([1, 1, 1.2, 1.2])
            mi_type_f = mi_c1.selectbox("نوع الفاتورة:", ["الكل", "صرف", "ارجاع", "تحويل"], key="mi_type_f_log")
            mi_no_f   = mi_c2.text_input("رقم الفاتورة:", key="mi_no_f_log").strip()
            mi_boq_f  = mi_c3.text_input("🔍 BOQ الحالة:", key="mi_boq_f_log").strip()
            mi_date_f = mi_c4.date_input("تصفية بالتاريخ:", value=None, key="mi_date_f_log")

            mi_query = """SELECT id, invoice_type, invoice_no, warehouse_from,
                          warehouse_to, contractor, employee, boq, timestamp
                          FROM archived_invoices WHERE employee=?"""
            mi_params = [u['full_name']]
            if mi_type_f != "الكل":
                mi_query += f" AND invoice_type='{mi_type_f}'"
            if mi_no_f:
                mi_query += f" AND invoice_no LIKE '%{mi_no_f}%'"
            if mi_boq_f:
                mi_query += f" AND boq LIKE '%{mi_boq_f}%'"
            if mi_date_f:
                mi_query += f" AND timestamp >= '{mi_date_f.strftime('%Y-%m-%d')}'"
            mi_query += " ORDER BY id DESC"

            df_mi = pd.read_sql(mi_query, conn, params=mi_params)

            if df_mi.empty:
                st.info("ℹ️ لا توجد فواتير منشأة بواسطتك تطابق الفلاتر المحددة.")
            else:
                st.success(f"✅ تم العثور على ({len(df_mi)}) فاتورة.")
                st.markdown("---")
                for _, mi_row in df_mi.iterrows():
                    mi_inv_id   = int(mi_row['id'])
                    mi_view_key = f"mi_log_view_{mi_inv_id}"
                    if mi_view_key not in st.session_state:
                        st.session_state[mi_view_key] = False

                    _tc = "#e65100" if mi_row['invoice_type']=="صرف" else ("#2e7d32" if mi_row['invoice_type']=="ارجاع" else "#1a237e")
                    st.markdown(f"""
                    <div class='report-box'>
                        📄 <b style='color:{_tc};'>فاتورة {mi_row['invoice_type']}</b>
                        رقم <span style='color:red;font-weight:900;'>{mi_row['invoice_no']}</span>
                        &nbsp;|&nbsp; 📅 {mi_row['timestamp']}<br>
                        📍 {mi_row['warehouse_from'] or 'N/A'}
                        {f" ➡️ {mi_row['warehouse_to']}" if mi_row['warehouse_to'] else ""}
                        {f" &nbsp;|&nbsp; 🏗️ {mi_row['contractor']}" if mi_row['contractor'] else ""}
                        {f"<br>📋 <b>BOQ:</b> <span style='color:#e65100;'>{mi_row['boq']}</span>" if mi_row.get('boq') else ""}
                    </div>""", unsafe_allow_html=True)

                    if st.button(f"👁️ معاينة الفاتورة {mi_row['invoice_no']}", key=f"mi_log_view_btn_{mi_inv_id}"):
                        st.session_state[mi_view_key] = not st.session_state[mi_view_key]

                    if st.session_state[mi_view_key]:
                        _mi_html = pd.read_sql(
                            "SELECT html_content FROM archived_invoices WHERE id=?",
                            conn, params=(mi_inv_id,))
                        if not _mi_html.empty:
                            components.html(_mi_html.iloc[0]['html_content'], height=520, scrolling=True)

                    st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: أرقام التواصل مع المقاولين والمستودعات
    # ---------------------------------------------------------
    elif st.session_state.page == "contacts_page":
        st.markdown("<div class='main-title'>📞 دليل أرقام التواصل</div>", unsafe_allow_html=True)

        # ── ثوابت التسلسل الهرمي ──
        POSITION_HIERARCHY = [
            {"key": "مدير المشروع",      "icon": "", "color": "#004a99", "bg": "#e8f0fb"},
            {"key": "نائب مدير المشروع", "icon": "", "color": "#1565c0", "bg": "#e3f2fd"},
            {"key": "مستلم بلاغات",      "icon": "", "color": "#00695c", "bg": "#e0f2f1"},
            {"key": "أمين مستودع",       "icon": "", "color": "#6a1b9a", "bg": "#f3e5f5"},
            {"key": "مسؤول فرق طوارئ",   "icon": "", "color": "#c62828", "bg": "#ffebee"},
            {"key": "أخرى",              "icon": "", "color": "#555",    "bg": "#f5f5f5"},
        ]
        POSITION_KEYS = [p["key"] for p in POSITION_HIERARCHY]

        # المناصب التي تُعرض لكل تبويب
        CONTRACTOR_POSITIONS = ["مدير المشروع", "نائب مدير المشروع", "مستلم بلاغات", "مسؤول فرق طوارئ"]
        WAREHOUSE_POSITIONS  = ["مدير المشروع", "نائب مدير المشروع", "أمين مستودع"]

        # جلب قوائم النظام
        ct_warehouses  = pd.read_sql("SELECT name FROM settings_warehouses  ORDER BY name", conn)['name'].tolist()
        ct_contractors = pd.read_sql("SELECT name FROM settings_contractors ORDER BY name", conn)['name'].tolist()
        df_contacts    = pd.read_sql("SELECT * FROM contact_numbers ORDER BY entity_type, entity_name, position, name", conn)
        df_managers    = pd.read_sql("SELECT * FROM managers_directory ORDER BY sort_order ASC, id ASC", conn)

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
                df_mgr_adm = pd.read_sql("SELECT * FROM managers_directory ORDER BY sort_order ASC, id ASC", conn)
                if df_mgr_adm.empty:
                    st.info("ℹ️ لا يوجد مدراء مسجلون.")
                else:
                    st.caption("🔼🔽 استخدم الأزرار لتغيير ترتيب ظهور المدير في القائمة")
                    for idx_mr, (_, mr) in enumerate(df_mgr_adm.iterrows()):
                        mr_id = int(mr['id'])
                        mr_ek = f"mr_edit_{mr_id}"; mr_ck = f"mr_conf_{mr_id}"
                        if mr_ek not in st.session_state: st.session_state[mr_ek] = False
                        if mr_ck not in st.session_state: st.session_state[mr_ck] = False

                        mc1,mc2,mc3,mc4,mc5,mc6,mc7 = st.columns([0.3,2.2,1.8,0.4,0.4,0.5,0.5])
                        mc1.markdown("🌟", unsafe_allow_html=True)
                        mc2.write(f"**{mr['name']}** — {mr['department']}")
                        mc3.write(f"📞 {mr['phone']}")
                        # أزرار الترتيب
                        # ── تحديث sort_order لكل صف بقيمة index الحالي (لضمان التسلسل) ──
                        if idx_mr > 0:
                            if mc4.button("🔼", key=f"mr_up_{mr_id}", help="تحريك لأعلى"):
                                prev_mr = df_mgr_adm.iloc[idx_mr - 1]
                                # إعادة تعيين sort_order لكل الصفوف أولاً لضمان التسلسل
                                for _ri, _rr in df_mgr_adm.iterrows():
                                    c.execute("UPDATE managers_directory SET sort_order=? WHERE id=?",
                                              (df_mgr_adm.index.get_loc(_ri), int(_rr['id'])))
                                # تبديل الصفين
                                c.execute("UPDATE managers_directory SET sort_order=? WHERE id=?", (idx_mr, int(prev_mr['id'])))
                                c.execute("UPDATE managers_directory SET sort_order=? WHERE id=?", (idx_mr - 1, mr_id))
                                conn.commit(); st.rerun()
                        if idx_mr < len(df_mgr_adm) - 1:
                            if mc5.button("🔽", key=f"mr_dn_{mr_id}", help="تحريك لأسفل"):
                                next_mr = df_mgr_adm.iloc[idx_mr + 1]
                                for _ri, _rr in df_mgr_adm.iterrows():
                                    c.execute("UPDATE managers_directory SET sort_order=? WHERE id=?",
                                              (df_mgr_adm.index.get_loc(_ri), int(_rr['id'])))
                                c.execute("UPDATE managers_directory SET sort_order=? WHERE id=?", (idx_mr, int(next_mr['id'])))
                                c.execute("UPDATE managers_directory SET sort_order=? WHERE id=?", (idx_mr + 1, mr_id))
                                conn.commit(); st.rerun()
                        if not st.session_state[mr_ek]:
                            if mc6.button("✏️", key=f"mr_e_{mr_id}"): st.session_state[mr_ek]=True; st.rerun()
                            if mc7.button("🗑️", key=f"mr_d_{mr_id}"): st.session_state[mr_ck]=True; st.rerun()
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

            tab_requests_view, tab_add_new_emp, tab_change_pwd, tab_mobile_access, tab_admin_pwd, tab_cwk_perms = st.tabs([
                "📥 طلبات تصفير وتعديل كلمات المرور الواردة",
                "➕ إضافة وتعيين حساب موظف ميداني جديد",
                "🔑 تغيير كلمة مرور أي مستخدم",
                "📱 صلاحية تشغيل النظام من الجوال",
                "🔐 تغيير كلمة مرور مدير النظام",
                "🏢 صلاحيات مستودعات المقاول"
            ])
        
            with tab_requests_view:
                section_card("📥 طلبات إعادة تعيين كلمات المرور", "#37474f")
                df_reqs = pd.read_sql("SELECT id as 'رقم الطلب', phone as 'رقم جوال الموظف الطالب', status as 'حالة الطلب الحالي', request_time as 'توقيت رفع الطلب' FROM access_requests ORDER BY id DESC", conn)
                if not df_reqs.empty:
                    html_table(df_reqs, accent='#37474f', info_label='📥 الطلبات: ', badge_col='حالة الطلب الحالي', badge_map={'معلق':('#f9a825','#333'),'تمت المعالجة':('#1daa60','white'),'مرفوض':('#d32f2f','white')})
                
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
                    new_role = c_u4.selectbox("مستوى الصلاحية الممنوحة *", ["موظف مستودع", "موجه بلاغات", "مدير نظام", "أمين مستودع المقاول"])
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
                                _role_opts = ["موظف مستودع", "موجه بلاغات", "مدير نظام", "أمين مستودع المقاول"]
                                updated_role = col_e4.selectbox("الصلاحية الممنوحة", _role_opts, index=_role_opts.index(r_usr['role']) if r_usr['role'] in _role_opts else 0)
                                # حقل المنصب الوظيفي
                                _pos_opts_edit = ["مدير المشروع", "نائب مدير المشروع", "مستلم بلاغات", "أمين مستودع", "أمين مستودع مقاول", "مسؤول فرق طوارئ", "أخرى"]
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

            with tab_admin_pwd:
                st.write("##### 🔐 تغيير كلمة مرور مدير النظام")
                st.markdown("""
                <div style='background:#fff3cd;border:2px solid #f9a825;border-radius:10px;padding:14px 18px;margin-bottom:18px;direction:rtl;font-size:14px;'>
                    🔐 <b>هذه العملية محمية بكلمة مرور إضافية خاصة.</b><br>
                    <small>كلمة المرور الإضافية مختلفة عن كلمة مرور الدخول للنظام.</small>
                </div>""", unsafe_allow_html=True)

                if not st.session_state.get('admin_pwd_auth'):
                    with st.form("admin_pwd_auth_form"):
                        ap_pass = st.text_input("🔑 أدخل كلمة المرور الإضافية للمتابعة:", type="password")
                        if st.form_submit_button("🔓 تحقق ودخول", use_container_width=True):
                            if ap_pass == "Saeed1102193511":
                                st.session_state['admin_pwd_auth'] = True
                                st.rerun()
                            else:
                                st.error("❌ كلمة المرور الإضافية غير صحيحة!")
                else:
                    col_ap_lock2 = st.columns([4, 1])
                    if col_ap_lock2[1].button("🔒 قفل", key="lock_admin_pwd2"):
                        st.session_state['admin_pwd_auth'] = False; st.rerun()
                    st.success("✅ تم التحقق. يمكنك الآن تغيير كلمة مرور مدير النظام.")
                    admin_users = pd.read_sql("SELECT username, full_name FROM users WHERE role='مدير نظام'", conn)
                    if admin_users.empty:
                        st.warning("⚠️ لا يوجد حسابات مدير نظام مسجلة.")
                    else:
                        with st.form("change_admin_pwd_form2", clear_on_submit=True):
                            if len(admin_users) > 1:
                                sel_admin2 = st.selectbox("اختر حساب مدير النظام:",
                                    options=admin_users['username'].tolist(),
                                    format_func=lambda x: admin_users[admin_users['username']==x]['full_name'].values[0] + f" ({x})")
                            else:
                                sel_admin2 = admin_users.iloc[0]['username']
                                st.info(f"الحساب: **{admin_users.iloc[0]['full_name']}** ({sel_admin2})")
                            cap1, cap2 = st.columns([1, 1])
                            new_admin_pwd2  = cap1.text_input("كلمة المرور الجديدة *", type="password")
                            conf_admin_pwd2 = cap2.text_input("تأكيد كلمة المرور *", type="password")
                            if st.form_submit_button("💾 تغيير كلمة مرور مدير النظام", use_container_width=True):
                                if not new_admin_pwd2:
                                    st.error("⚠️ يرجى إدخال كلمة المرور الجديدة.")
                                elif new_admin_pwd2 != conf_admin_pwd2:
                                    st.error("❌ كلمة المرور وتأكيدها غير متطابقين!")
                                else:
                                    c.execute("UPDATE users SET password=? WHERE username=?", (new_admin_pwd2, sel_admin2))
                                    save_log("تغيير كلمة مرور مدير النظام", sel_admin2, 0,
                                             f"تم تغيير كلمة مرور مدير النظام بكلمة المرور الإضافية الخاصة", u['full_name'])
                                    conn.commit()
                                    st.success("✅ تم تغيير كلمة مرور مدير النظام بنجاح!")
                                    st.session_state['admin_pwd_auth'] = False
                                    st.rerun()

            with tab_cwk_perms:
                st.write("##### 🏢 إدارة صلاحيات المستودعات لأمين مستودع المقاول")
                st.markdown("""
                <div style='background:#e3f2fd;border:2px solid #0288d1;border-radius:10px;padding:14px 18px;margin-bottom:18px;direction:rtl;font-size:14px;'>
                    🔐 <b>من هنا يمكنك تحديد المستودعات التي يُصرح لكل أمين مستودع مقاول برؤيتها فقط.</b><br>
                    <small>• أمين مستودع المقاول لا يرى إلا المستودعات المضافة له هنا.<br>
                    • لا يمكنه الصرف أو التعديل — فقط المشاهدة وإرفاق الفواتير الموقعة.</small>
                </div>""", unsafe_allow_html=True)

                # ── إحصائية الفواتير المعلقة الكلية ──
                try:
                    _total_all_inv  = int(pd.read_sql("SELECT COUNT(*) as cnt FROM archived_invoices", conn).iloc[0]['cnt'])
                    _signed_all_inv = int(pd.read_sql("SELECT COUNT(*) as cnt FROM signed_invoices WHERE deducted=1", conn).iloc[0]['cnt'])
                    _pend_all       = max(0, _total_all_inv - _signed_all_inv)
                    _stat1, _stat2, _stat3 = st.columns(3)
                    _stat1.metric("📄 إجمالي الفواتير", _total_all_inv)
                    _stat2.metric("✅ موقعة ومنفذة", _signed_all_inv)
                    _stat3.metric("⏳ معلقة (لم تُخصم بعد)", _pend_all,
                                  delta=f"-{_pend_all}" if _pend_all > 0 else None, delta_color="inverse")
                    if _pend_all > 0:
                        st.warning(f"⚠️ يوجد {_pend_all} فاتورة معلقة لم تُخصم بعد من المخزون بانتظار توقيع أمين مستودع المقاول.")
                except Exception:
                    pass

                st.divider()

                # ── تفاصيل الفواتير الموقعة (من قام بالإرفاق) ──
                with st.expander("📋 سجل إرفاق الفواتير الموقعة — من قام بالإرفاق ومتى"):
                    df_sig_log = pd.read_sql(
                        "SELECT invoice_no, invoice_type, signed_by, signed_at, deducted FROM signed_invoices ORDER BY id DESC LIMIT 50",
                        conn)
                    if df_sig_log.empty:
                        st.info("لا توجد فواتير موقعة حتى الآن.")
                    else:
                        df_sig_log.columns = ['رقم الفاتورة', 'النوع', 'أرفقها', 'تاريخ الإرفاق', 'تم الخصم']
                        df_sig_log['تم الخصم'] = df_sig_log['تم الخصم'].apply(lambda x: "✅ نعم" if int(x)==1 else "❌ لا")
                        html_table(df_sig_log, accent='#004a99', info_label='📋 السجل: ', badge_col='تم الخصم', badge_map={'✅ نعم':('#1daa60','white'),'❌ لا':('#d32f2f','white')})

                st.divider()

                df_cwk_users = pd.read_sql(
                    "SELECT username, full_name FROM users WHERE role='أمين مستودع المقاول' ORDER BY full_name ASC", conn)
                if df_cwk_users.empty:
                    st.info("ℹ️ لا يوجد مستخدمون بصلاحية (أمين مستودع المقاول) حتى الآن.")
                else:
                    _cwk_opts = df_cwk_users['username'].tolist()

                    # حفظ المستخدم المختار في session_state لإبقائه بعد rerun
                    if 'cwk_sel_user' not in st.session_state:
                        st.session_state['cwk_sel_user'] = _cwk_opts[0] if _cwk_opts else ""
                    # إذا كان المحفوظ غير موجود في القائمة (حُذف مثلاً)، أعد للأول
                    if st.session_state['cwk_sel_user'] not in _cwk_opts:
                        st.session_state['cwk_sel_user'] = _cwk_opts[0] if _cwk_opts else ""

                    _cwk_default_idx = _cwk_opts.index(st.session_state['cwk_sel_user']) if st.session_state['cwk_sel_user'] in _cwk_opts else 0

                    sel_cwk_user = st.selectbox(
                        "اختر أمين مستودع المقاول:",
                        options=_cwk_opts,
                        index=_cwk_default_idx,
                        format_func=lambda x: df_cwk_users[df_cwk_users['username']==x]['full_name'].values[0] + f" ({x})",
                        key="cwk_sel_box"
                    )
                    # تحديث session_state عند تغيير الاختيار
                    if sel_cwk_user != st.session_state['cwk_sel_user']:
                        st.session_state['cwk_sel_user'] = sel_cwk_user

                    if sel_cwk_user:
                        _cwk_full_name = df_cwk_users[df_cwk_users['username']==sel_cwk_user]['full_name'].values[0]

                        # بطاقة المستخدم المختار
                        st.markdown(f"""
                        <div style='background:#e8f5e9;border:2px solid #1daa60;border-radius:10px;
                            padding:12px 18px;direction:rtl;margin-bottom:14px;'>
                            👤 <b style='font-size:15px;'>{_cwk_full_name}</b>
                            <span style='color:#555;font-size:13px;'>({sel_cwk_user})</span><br>
                            <span style='font-size:13px;color:#2e7d32;'>أمين مستودع المقاول</span>
                        </div>""", unsafe_allow_html=True)

                        st.markdown("**🏢 المستودعات المصرح بها حالياً:**")
                        df_cur_perms = pd.read_sql(
                            "SELECT warehouse FROM contractor_warehouse_permissions WHERE username=?",
                            conn, params=(sel_cwk_user,))
                        cur_perms = df_cur_perms['warehouse'].tolist()

                        if cur_perms:
                            for wh_p in cur_perms:
                                col_wp1, col_wp2 = st.columns([3, 1])
                                col_wp1.markdown(f"✅ **{wh_p}**")
                                if col_wp2.button(f"🗑️ إزالة", key=f"rm_cwk_{sel_cwk_user}_{wh_p}"):
                                    c.execute("DELETE FROM contractor_warehouse_permissions WHERE username=? AND warehouse=?",
                                              (sel_cwk_user, wh_p))
                                    conn.commit()
                                    st.session_state['cwk_sel_user'] = sel_cwk_user  # حفظ المستخدم
                                    st.success(f"✅ تم إزالة صلاحية مستودع [{wh_p}]")
                                    st.rerun()
                        else:
                            st.warning("⚠️ لا توجد مستودعات مصرح بها لهذا المستخدم بعد.")

                        st.markdown("---")

                        _wh_not_added = [w for w in list_warehouses if w not in cur_perms]
                        if _wh_not_added:
                            st.markdown("**➕ إضافة مستودع جديد:**")
                            with st.form(f"add_cwk_wh_form"):
                                new_wh_perm = st.selectbox("اختر المستودع:", _wh_not_added, key="new_wh_perm_sel")
                                if st.form_submit_button("💾 إضافة الصلاحية", use_container_width=True):
                                    try:
                                        c.execute(
                                            "INSERT INTO contractor_warehouse_permissions (username, warehouse) VALUES (?,?)",
                                            (sel_cwk_user, new_wh_perm))
                                        conn.commit()
                                        st.session_state['cwk_sel_user'] = sel_cwk_user  # حفظ المستخدم
                                        st.success(f"✅ تم إضافة صلاحية مستودع [{new_wh_perm}] لـ {_cwk_full_name}")
                                        st.rerun()
                                    except Exception:
                                        st.warning("⚠️ هذا المستودع مضاف مسبقاً.")
                        else:
                            st.info("✅ جميع المستودعات المتاحة مضافة لهذا المستخدم.")

    # ---------------------------------------------------------
    # صفحات قسم الفواتير الجديدة
    # ---------------------------------------------------------
    elif st.session_state.page in ("invoices_archive", "invoices_cancel",
                                   "invoices_cancelled_log", "invoices_mine"):
        if role not in ("مدير نظام", "موظف مستودع", "أمين مستودع"):
            st.error("❌ غير مصرح لك بالوصول.")
        else:
            _inv_pages_map = {
                "invoices_archive":       ("🗂️ أرشيف الفواتير والمستندات",   "tab_arch",    "tab_cancel",    "tab_canclog",   "tab_mine",  "tab_delperm"),
                "invoices_cancel":        ("🚫 إلغاء الفواتير",               "tab_arch",    "tab_cancel",    "tab_canclog",   "tab_mine",  "tab_delperm"),
                "invoices_cancelled_log": ("📑 سجل الفواتير الملغية",         "tab_arch",    "tab_cancel",    "tab_canclog",   "tab_mine",  "tab_delperm"),
                "invoices_mine":          ("📄 فواتير منشأة بواسطتي",         "tab_arch",    "tab_cancel",    "tab_canclog",   "tab_mine",  "tab_delperm"),
                "invoices_delete_perm":   ("🗑️ حذف الفواتير نهائياً",        "tab_arch",    "tab_cancel",    "tab_canclog",   "tab_mine",  "tab_delperm"),
            }
            page_header("📑", "قسم الفواتير", "إدارة ومتابعة الفواتير والمستندات", "#004a99")

            # تبويبات
            _tabs_labels = ["🗂️ أرشيف الفواتير", "🚫 إلغاء فاتورة", "📑 الفواتير الملغية", "📄 فواتير بواسطتي"]
            _tabs_all = st.tabs(_tabs_labels)
            _t_arch, _t_cancel, _t_canclog, _t_mine = _tabs_all[0], _tabs_all[1], _tabs_all[2], _tabs_all[3]
            _t_delperm = None

            # ── تبويب ١: أرشيف الفواتير ──
            with _t_arch:
                section_card("🗂️ أرشيف جميع الفواتير والمستندات", "#004a99")
                _fa1, _fa2, _fa3 = st.columns([1.5, 1.5, 1])
                _fa_type   = _fa1.selectbox("نوع الفاتورة:", ["الكل","صرف","ارجاع","نقل"], key="fa_type")
                _fa_search = _fa2.text_input("🔍 رقم الفاتورة أو المقاول:", key="fa_search").strip()
                _fa_wh     = _fa3.selectbox("المستودع:", ["الكل"] + list_warehouses, key="fa_wh")
                _aq = "SELECT id, invoice_no, invoice_type, warehouse_from, warehouse_to, contractor, employee, timestamp FROM archived_invoices WHERE 1=1"
                if _fa_type != "الكل":   _aq += f" AND invoice_type='{_fa_type}'"
                if _fa_search:           _aq += f" AND (invoice_no LIKE '%{_fa_search}%' OR contractor LIKE '%{_fa_search}%')"
                if _fa_wh != "الكل":     _aq += f" AND (warehouse_from='{_fa_wh}' OR warehouse_to='{_fa_wh}')"
                _aq += " ORDER BY id DESC LIMIT 100"
                df_arch = pd.read_sql(_aq, conn)
                if df_arch.empty:
                    st.info("ℹ️ لا توجد فواتير.")
                else:
                    st.caption(f"📋 {len(df_arch)} فاتورة")
                    for _, ar in df_arch.iterrows():
                        _aid = int(ar['id'])
                        with st.expander(f"📄 {ar['invoice_type']} | رقم: {ar['invoice_no']} | {str(ar['timestamp'])[:16]} | {ar['employee']}"):
                            st.markdown(f"""
                            <div style='background:#f0f4ff;border-right:4px solid #004a99;border-radius:8px;padding:10px 14px;direction:rtl;font-size:13px;'>
                            📍 من: <b>{ar.get('warehouse_from','—')}</b>
                            {"➡️ <b>" + str(ar.get('warehouse_to','')) + "</b>" if ar.get('warehouse_to') else ""}
                            {" | 🏗️ <b>" + str(ar.get('contractor','')) + "</b>" if ar.get('contractor') else ""}
                            </div>""", unsafe_allow_html=True)
                            _vk = f"arch_v_{_aid}"
                            if st.button("👁️ عرض الفاتورة", key=f"arch_vbtn_{_aid}"):
                                st.session_state[_vk] = not st.session_state.get(_vk, False)
                            if st.session_state.get(_vk, False):
                                _hr = pd.read_sql("SELECT html_content FROM archived_invoices WHERE id=?", conn, params=(_aid,))
                                if not _hr.empty:
                                    components.html(str(_hr.iloc[0]['html_content']), height=500, scrolling=True)

            # ── تبويب ٢: إلغاء فاتورة (من الموظف نفسه — يذهب للاعتماد) ──
            with _t_cancel:
                section_card("🚫 إلغاء فاتورة — يُرسل طلب للاعتماد", "#c62828")
                st.info("ℹ️ اكتب رقم الفاتورة وسبب الإلغاء — سيذهب الطلب لمدير النظام للاعتماد.")
                with st.form("cancel_inv_form_new"):
                    _cn1, _cn2 = st.columns([1.5, 2])
                    _c_invno  = _cn1.text_input("رقم الفاتورة *")
                    _c_reason = _cn2.text_input("سبب الإلغاء *")
                    if st.form_submit_button("📨 إرسال طلب الإلغاء", use_container_width=True):
                        if not _c_invno.strip() or not _c_reason.strip():
                            st.error("❌ يرجى ملء رقم الفاتورة وسبب الإلغاء.")
                        else:
                            _inv_check = pd.read_sql(f"SELECT id FROM archived_invoices WHERE invoice_no='{_c_invno.strip()}'", conn)
                            if _inv_check.empty:
                                st.error("❌ رقم الفاتورة غير موجود.")
                            else:
                                c.execute("INSERT INTO cancel_invoice_requests (invoice_no, cancel_reason, requester, status, timestamp) VALUES (?,?,?,?,?)",
                                          (_c_invno.strip(), _c_reason.strip(), u['full_name'], "معلق", now_mecca().strftime("%Y-%m-%d %H:%M")))
                                conn.commit()
                                st.success("✅ تم إرسال طلب الإلغاء لمدير النظام.")

            # ── تبويب ٣: سجل الفواتير الملغية ──
            with _t_canclog:
                section_card("📑 سجل الفواتير الملغية المعتمدة", "#7f0000")
                df_cancelled = pd.read_sql("""
                    SELECT invoice_no as 'رقم الفاتورة',
                           cancel_reason as 'سبب الإلغاء',
                           requester as 'طلب الإلغاء',
                           approved_by as 'اعتمد الإلغاء',
                           status as 'الحالة',
                           timestamp as 'التاريخ'
                    FROM cancel_invoice_requests
                    WHERE status='معتمد' ORDER BY id DESC LIMIT 100
                """, conn)
                if df_cancelled.empty:
                    st.info("ℹ️ لا توجد فواتير ملغية.")
                else:
                    html_table(df_cancelled, accent="#7f0000",
                               info_label="📑 الفواتير الملغية: ",
                               badge_col="الحالة",
                               badge_map={"معتمد":("#1daa60","white"),"معلق":("#f9a825","#333"),"مرفوض":("#d32f2f","white")})

            # ── تبويب ٤: فواتير منشأة بواسطتي ──
            with _t_mine:
                section_card(f"📄 الفواتير المنشأة بواسطة: {u['full_name']}", "#004a99")
                _fm_type = st.selectbox("نوع الفاتورة:", ["الكل","صرف","ارجاع","نقل"], key="fm_type")
                _fmq = f"SELECT invoice_no, invoice_type, warehouse_from, contractor, timestamp FROM archived_invoices WHERE employee='{u['full_name']}'"
                if _fm_type != "الكل":
                    _fmq += f" AND invoice_type='{_fm_type}'"
                _fmq += " ORDER BY id DESC LIMIT 100"
                df_mine = pd.read_sql(_fmq, conn)
                if df_mine.empty:
                    st.info("ℹ️ لا توجد فواتير منشأة باسمك.")
                else:
                    df_mine.columns = ['رقم الفاتورة','النوع','المستودع','المقاول','التاريخ']
                    html_table(df_mine, accent="#004a99", info_label="📄 فواتيرك: ")

            # تبويب الحذف النهائي — معطّل حسب سياسة النظام
            if _t_delperm is not None:
                with _t_delperm:
                    st.info("🚫 حذف الفواتير غير مسموح به في هذا النظام.")

    # ---------------------------------------------------------
    # صفحة: قسم BOQ — فواتير البلاغات
    # ---------------------------------------------------------
    elif st.session_state.page == "boq_section":
        if role not in ("مدير نظام", "موظف مستودع", "أمين مستودع"):
            st.error("❌ غير مصرح لك.")
        else:
            page_header("📋", "قسم BOQ — فواتير البلاغات", "عرض وتتبع الفواتير المرتبطة بأرقام البلاغات", "#004a99")

            tab_boq_invoices, tab_boq_search = st.tabs([
                "📑 فواتير BOQ الصادرة",
                "🔍 البحث اليدوي برقم BOQ"
            ])

            # ══════════════════════════════════════
            # تبويب ١: فواتير BOQ الصادرة
            # ══════════════════════════════════════
            with tab_boq_invoices:
                section_card("📑 الفواتير الصادرة المرتبطة بأرقام BOQ", "#004a99")

                # فلاتر
                _bq1, _bq2, _bq3, _bq4 = st.columns([1.5, 1.5, 1.2, 1.2])
                _boq_type   = _bq1.selectbox("نوع الفاتورة:", ["الكل","صرف","ارجاع"], key="boq_type")
                _boq_search = _bq2.text_input("🔍 رقم BOQ / المقاول / رقم الفاتورة:", key="boq_search_txt").strip()
                _boq_df     = _bq3.date_input("📅 من تاريخ:", value=None, key="boq_date_from")
                _boq_dt     = _bq4.date_input("📅 إلى تاريخ:", value=None, key="boq_date_to")

                # جلب الفواتير من signed_invoices التي لها BOQ
                _bq_query = """
                    SELECT s.invoice_no, s.invoice_type, s.boq,
                           s.signed_by, s.signed_at, s.status,
                           a.employee as created_by, a.contractor,
                           a.warehouse_from, a.timestamp as created_at,
                           s.id as sig_id, a.id as arch_id
                    FROM signed_invoices s
                    LEFT JOIN archived_invoices a ON s.original_invoice_id = a.id
                    WHERE (s.boq IS NOT NULL AND s.boq != '')
                """
                if _boq_type != "الكل":
                    _bq_query += f" AND s.invoice_type='{_boq_type}'"
                if _boq_df:
                    _bq_query += f" AND DATE(s.signed_at) >= '{_boq_df.strftime('%Y-%m-%d')}'"
                if _boq_dt:
                    _bq_query += f" AND DATE(s.signed_at) <= '{_boq_dt.strftime('%Y-%m-%d')}'"
                if _boq_search:
                    _bq_query += f" AND (s.boq LIKE '%{_boq_search}%' OR s.invoice_no LIKE '%{_boq_search}%' OR a.contractor LIKE '%{_boq_search}%')"
                _bq_query += " ORDER BY s.id DESC LIMIT 100"

                df_boq = pd.read_sql(_bq_query, conn)

                if df_boq.empty:
                    st.info("ℹ️ لا توجد فواتير مرتبطة بأرقام BOQ.")
                else:
                    st.caption(f"📋 {len(df_boq)} فاتورة مرتبطة بـ BOQ")
                    _status_colors = {"معتمد":"#1daa60","مرفوض":"#d32f2f","مُعادة":"#e65100","بانتظار الاعتماد":"#0288d1"}

                    for _, bqrow in df_boq.iterrows():
                        _sc = _status_colors.get(str(bqrow['status']), "#9e9e9e")
                        with st.expander(
                            f"📋 BOQ: {bqrow['boq']} | فاتورة: {bqrow['invoice_no']} | {bqrow['invoice_type']} | {str(bqrow['signed_at'])[:16]}",
                            expanded=False):

                            # بطاقة معلومات
                            st.markdown(f"""
                            <div style='background:#f0f4ff;border-right:5px solid {_sc};border-radius:10px;
                                padding:14px 18px;direction:rtl;margin-bottom:12px;'>
                                <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;'>
                                    <span style='background:{_sc};color:white;border-radius:8px;padding:3px 12px;font-size:12px;font-weight:bold;'>
                                        {bqrow['status']}
                                    </span>
                                    <span style='font-size:18px;font-weight:900;color:#004a99;'>
                                        📋 BOQ: {bqrow['boq']}
                                    </span>
                                </div>
                                <hr style='border-color:#dde6f5;margin:10px 0;'>
                                <div style='font-size:13px;color:#333;line-height:2;'>
                                    🧾 <b>رقم الفاتورة:</b> {bqrow['invoice_no']} &nbsp;|&nbsp;
                                    📂 <b>النوع:</b> {bqrow['invoice_type']}<br>
                                    📍 <b>المستودع:</b> {bqrow.get('warehouse_from','—')} &nbsp;|&nbsp;
                                    🏗️ <b>المقاول:</b> {bqrow.get('contractor','—') or '—'}<br>
                                    👤 <b>أنشأ الفاتورة:</b> <span style='color:#004a99;font-weight:bold;'>{bqrow.get('created_by','—')}</span> &nbsp;|&nbsp;
                                    📅 <b>تاريخ الإنشاء:</b> {str(bqrow.get('created_at',''))[:16]}<br>
                                    ✍️ <b>أرفقها:</b> <span style='color:#1daa60;font-weight:bold;'>{bqrow['signed_by']}</span> &nbsp;|&nbsp;
                                    📅 <b>تاريخ الإرفاق:</b> {str(bqrow['signed_at'])[:16]}
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # أزرار العرض
                            _bvk1 = f"boq_orig_{int(bqrow['arch_id']) if bqrow['arch_id'] else 0}"
                            _bvk2 = f"boq_sign_{int(bqrow['sig_id'])}"
                            col_b1, col_b2 = st.columns(2)

                            with col_b1:
                                if st.button("👁️ الفاتورة الأصلية (قبل التوقيع)", key=f"boq_orig_btn_{int(bqrow['sig_id'])}"):
                                    st.session_state[_bvk1] = not st.session_state.get(_bvk1, False)
                                if st.session_state.get(_bvk1, False) and bqrow['arch_id']:
                                    _oh = pd.read_sql("SELECT html_content FROM archived_invoices WHERE id=?",
                                                      conn, params=(int(bqrow['arch_id']),))
                                    if not _oh.empty:
                                        st.markdown("**📄 الفاتورة الأصلية:**")
                                        components.html(str(_oh.iloc[0]['html_content']), height=480, scrolling=True)

                            with col_b2:
                                if st.button("📎 الفاتورة بعد التوقيع", key=f"boq_sign_btn_{int(bqrow['sig_id'])}"):
                                    st.session_state[_bvk2] = not st.session_state.get(_bvk2, False)
                                if st.session_state.get(_bvk2, False):
                                    _sh = pd.read_sql("SELECT signed_image_base64 FROM signed_invoices WHERE id=?",
                                                      conn, params=(int(bqrow['sig_id']),))
                                    if not _sh.empty and _sh.iloc[0]['signed_image_base64']:
                                        st.markdown("**📎 الفاتورة الموقعة:**")
                                        st.markdown(
                                            f'<img src="data:image/jpeg;base64,{_sh.iloc[0]["signed_image_base64"]}" '
                                            f'style="max-width:100%;border:2px solid {_sc};border-radius:8px;margin-top:8px;">',
                                            unsafe_allow_html=True)
                                    else:
                                        st.warning("⚠️ لا توجد صورة مرفقة بعد.")

            # ══════════════════════════════════════
            # تبويب ٢: البحث اليدوي برقم BOQ
            # ══════════════════════════════════════
            with tab_boq_search:
                section_card("🔍 البحث اليدوي برقم البلاغ (BOQ)", "#1a3a5c")
                st.info("ℹ️ اكتب رقم BOQ أو جزءاً منه لعرض جميع الفواتير المرتبطة به مع اسم منشئ الفاتورة.")

                _manual_boq = st.text_input("📋 رقم البلاغ (BOQ):", placeholder="مثال: BOQ-2026-001 أو Zone2...", key="manual_boq_input").strip()

                if _manual_boq:
                    _mq = """
                        SELECT s.invoice_no      as 'رقم الفاتورة',
                               s.invoice_type    as 'النوع',
                               s.boq             as 'رقم BOQ',
                               a.employee        as 'منشئ الفاتورة',
                               a.contractor      as 'المقاول',
                               a.warehouse_from  as 'المستودع',
                               s.signed_by       as 'أرفقها',
                               s.status          as 'الحالة',
                               s.signed_at       as 'تاريخ الإرفاق'
                        FROM signed_invoices s
                        LEFT JOIN archived_invoices a ON s.original_invoice_id = a.id
                        WHERE s.boq LIKE ?
                        ORDER BY s.id DESC
                    """
                    df_manual = pd.read_sql(_mq, conn, params=(f"%{_manual_boq}%",))

                    if df_manual.empty:
                        st.warning(f"⚠️ لا توجد فواتير برقم BOQ يحتوي على: '{_manual_boq}'")
                    else:
                        st.success(f"✅ وُجد {len(df_manual)} فاتورة مرتبطة بـ BOQ: '{_manual_boq}'")
                        html_table(
                            df_manual, accent="#004a99",
                            info_label="📋 النتائج: ",
                            badge_col="الحالة",
                            badge_map={
                                "معتمد":             ("#1daa60", "white"),
                                "مرفوض":             ("#d32f2f", "white"),
                                "مُعادة":            ("#e65100", "white"),
                                "بانتظار الاعتماد":  ("#0288d1", "white"),
                            }
                        )

                        # عرض تفصيلي للفواتير المطابقة
                        st.markdown("---")
                        section_card("📄 التفاصيل الكاملة", "#004a99")
                        _mq2 = """
                            SELECT s.id as sig_id, s.invoice_no, s.invoice_type, s.boq,
                                   a.id as arch_id, a.employee as created_by,
                                   a.contractor, a.warehouse_from, a.timestamp as created_at,
                                   s.signed_by, s.signed_at, s.status
                            FROM signed_invoices s
                            LEFT JOIN archived_invoices a ON s.original_invoice_id = a.id
                            WHERE s.boq LIKE ?
                            ORDER BY s.id DESC
                        """
                        df_manual2 = pd.read_sql(_mq2, conn, params=(f"%{_manual_boq}%",))
                        for _, mr in df_manual2.iterrows():
                            _msc = {"معتمد":"#1daa60","مرفوض":"#d32f2f","مُعادة":"#e65100","بانتظار الاعتماد":"#0288d1"}.get(str(mr['status']),"#9e9e9e")
                            with st.expander(f"📄 {mr['invoice_type']} | رقم: {mr['invoice_no']} | BOQ: {mr['boq']}"):
                                st.markdown(f"""
                                <div style='background:#f8f9fa;border-right:4px solid {_msc};border-radius:8px;padding:12px 16px;direction:rtl;font-size:13px;'>
                                    📋 <b>رقم BOQ:</b> <span style='color:#004a99;font-size:15px;font-weight:900;'>{mr['boq']}</span><br>
                                    👤 <b>منشئ الفاتورة:</b> <span style='color:#004a99;font-weight:bold;'>{mr.get('created_by','—')}</span><br>
                                    📅 <b>تاريخ الإنشاء:</b> {str(mr.get('created_at',''))[:16]}<br>
                                    🏗️ <b>المقاول:</b> {mr.get('contractor','—') or '—'} &nbsp;|&nbsp;
                                    📍 <b>المستودع:</b> {mr.get('warehouse_from','—')}<br>
                                    ✍️ <b>أرفقها:</b> <span style='color:#1daa60;font-weight:bold;'>{mr['signed_by']}</span> &nbsp;|&nbsp;
                                    📅 {str(mr['signed_at'])[:16]}<br>
                                    <span style='background:{_msc};color:white;border-radius:6px;padding:2px 10px;font-size:12px;'>{mr['status']}</span>
                                </div>""", unsafe_allow_html=True)

                                mc1, mc2 = st.columns(2)
                                _mvk1 = f"m_orig_{int(mr['sig_id'])}"
                                _mvk2 = f"m_sign_{int(mr['sig_id'])}"
                                with mc1:
                                    if st.button("👁️ الفاتورة الأصلية", key=f"m_orig_btn_{int(mr['sig_id'])}"):
                                        st.session_state[_mvk1] = not st.session_state.get(_mvk1, False)
                                    if st.session_state.get(_mvk1, False) and mr['arch_id']:
                                        _oh2 = pd.read_sql("SELECT html_content FROM archived_invoices WHERE id=?",
                                                           conn, params=(int(mr['arch_id']),))
                                        if not _oh2.empty:
                                            components.html(str(_oh2.iloc[0]['html_content']), height=480, scrolling=True)
                                with mc2:
                                    if st.button("📎 الفاتورة الموقعة", key=f"m_sign_btn_{int(mr['sig_id'])}"):
                                        st.session_state[_mvk2] = not st.session_state.get(_mvk2, False)
                                    if st.session_state.get(_mvk2, False):
                                        _sh2 = pd.read_sql("SELECT signed_image_base64 FROM signed_invoices WHERE id=?",
                                                           conn, params=(int(mr['sig_id']),))
                                        if not _sh2.empty and _sh2.iloc[0]['signed_image_base64']:
                                            st.markdown(
                                                f'<img src="data:image/jpeg;base64,{_sh2.iloc[0]["signed_image_base64"]}" '
                                                f'style="max-width:100%;border:2px solid {_msc};border-radius:8px;">',
                                                unsafe_allow_html=True)
                                        else:
                                            st.warning("⚠️ لا توجد صورة مرفقة.")
                else:
                    st.markdown("""
                    <div style='background:#f0f4ff;border:2px dashed #004a99;border-radius:12px;padding:30px;
                        text-align:center;direction:rtl;color:#555;'>
                        <div style='font-size:40px;margin-bottom:12px;'>📋</div>
                        <div style='font-size:15px;font-weight:700;color:#004a99;'>اكتب رقم BOQ للبحث</div>
                        <div style='font-size:13px;margin-top:6px;'>سيظهر لك اسم منشئ الفاتورة والفاتورة قبل وبعد التوقيع</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: حذف الفواتير — مدير النظام فقط + كلمة سر
    # ---------------------------------------------------------
    elif st.session_state.page == "invoices_delete_perm":
        if role != "مدير نظام":
            st.error("❌ هذه الصفحة لمدير النظام فقط.")
        else:
            page_header("🗑️", "حذف الفواتير", "محمية بكلمة المرور الإضافية — مدير النظام فقط", "#d32f2f")

            # ── التحقق من كلمة المرور الإضافية ──
            if not st.session_state.get('del_inv_auth', False):
                st.markdown("""
                <div style='background:#fff5f5;border:2px solid #e53e3e;border-radius:14px;
                    padding:28px 32px;text-align:center;max-width:420px;margin:30px auto;direction:rtl;'>
                    <div style='font-size:48px;margin-bottom:12px;'>🔐</div>
                    <div style='font-size:17px;font-weight:900;color:#c53030;margin-bottom:8px;'>
                        منطقة محمية
                    </div>
                    <div style='font-size:13px;color:#666;'>
                        أدخل كلمة المرور الإضافية للوصول لصفحة حذف الفواتير
                    </div>
                </div>
                """, unsafe_allow_html=True)
                _, _lc, _ = st.columns([1, 1.5, 1])
                with _lc:
                    with st.form("del_inv_auth_form"):
                        _dap = st.text_input("🔑 كلمة المرور الإضافية:", type="AaSs#123123")
                        if st.form_submit_button("🔓 دخول", use_container_width=True):
                            if _dap == "Saeed1102193511":
                                st.session_state['del_inv_auth'] = True
                                st.rerun()
                            else:
                                st.error("❌ كلمة المرور غير صحيحة!")
            else:
                # ── زر القفل ──
                _lock_col1, _lock_col2 = st.columns([5, 1])
                if _lock_col2.button("🔒 قفل الصفحة", key="lock_del_inv"):
                    st.session_state['del_inv_auth'] = False
                    st.rerun()
                st.success("✅ تم التحقق — يمكنك تحديد الفواتير وحذفها.")

                st.markdown("""
                <div style='background:#fff3cd;border-right:4px solid #f9a825;border-radius:8px;
                    padding:10px 16px;direction:rtl;font-size:13px;margin-bottom:14px;'>
                    ⚠️ <b>تنبيه:</b> الحذف نهائي ولا يمكن التراجع عنه.
                    حدد الفواتير المراد حذفها ثم اضغط "حذف المحددة".
                    لا يمكن تحديد الكل بضغطة واحدة.
                </div>
                """, unsafe_allow_html=True)

                # ── فلاتر ──
                _df1, _df2, _df3, _df4 = st.columns([1.2, 1.2, 1.2, 1.2])
                _di_type  = _df1.selectbox("نوع الفاتورة:", ["الكل","صرف","ارجاع","نقل"], key="di_type")
                _di_wh    = _df2.selectbox("المستودع:", ["الكل"] + list_warehouses, key="di_wh")
                _di_emp   = _df3.text_input("🔍 الموظف أو رقم الفاتورة:", key="di_emp").strip()
                _di_date  = _df4.date_input("📅 من تاريخ:", value=None, key="di_date")

                _diq = "SELECT id, invoice_no, invoice_type, warehouse_from, contractor, employee, timestamp FROM archived_invoices WHERE 1=1"
                if _di_type != "الكل":  _diq += f" AND invoice_type='{_di_type}'"
                if _di_wh != "الكل":    _diq += f" AND warehouse_from='{_di_wh}'"
                if _di_emp:             _diq += f" AND (employee LIKE '%{_di_emp}%' OR invoice_no LIKE '%{_di_emp}%')"
                if _di_date:            _diq += f" AND DATE(timestamp) >= '{_di_date.strftime('%Y-%m-%d')}'"
                _diq += " ORDER BY id DESC LIMIT 200"

                df_di = pd.read_sql(_diq, conn)

                if df_di.empty:
                    st.info("ℹ️ لا توجد فواتير تطابق الفلاتر.")
                else:
                    st.caption(f"📋 {len(df_di)} فاتورة — حدد المراد حذفها:")
                    st.markdown("<hr style='margin:6px 0 12px;'>", unsafe_allow_html=True)

                    # قائمة التحديد
                    _selected_ids = []
                    for _, _drow in df_di.iterrows():
                        _di_id   = int(_drow['id'])
                        _di_invno= str(_drow['invoice_no'])
                        _di_key  = f"del_chk_{_di_id}"

                        _chk_col, _info_col = st.columns([0.5, 5.5])
                        _checked = _chk_col.checkbox("", key=_di_key, label_visibility="collapsed")
                        if _checked:
                            _selected_ids.append((_di_id, _di_invno))

                        _type_color = {"صرف":"#e53e3e","ارجاع":"#2b6cb0","نقل":"#276749"}.get(str(_drow['invoice_type']), "#555")
                        _info_col.markdown(f"""
                        <div style='background:#{"fff5f5" if _checked else "f8f9fa"};
                            border-right:3px solid {_type_color};border-radius:6px;
                            padding:7px 12px;direction:rtl;font-size:13px;
                            {"border:1.5px solid #e53e3e;" if _checked else ""}'>
                            <span style='background:{_type_color};color:white;border-radius:6px;
                                padding:1px 8px;font-size:11px;font-weight:bold;'>
                                {_drow['invoice_type']}
                            </span>
                            &nbsp; رقم: <b>{_di_invno}</b>
                            &nbsp;|&nbsp; 📍 {_drow.get('warehouse_from','—')}
                            &nbsp;|&nbsp; 👤 {_drow.get('employee','—')}
                            &nbsp;|&nbsp; 📅 {str(_drow.get('timestamp',''))[:16]}
                            {f" &nbsp;|&nbsp; 🏗️ {_drow.get('contractor','')}" if _drow.get('contractor') else ""}
                        </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<hr style='margin:12px 0;'>", unsafe_allow_html=True)

                    if _selected_ids:
                        _n = len(_selected_ids)
                        st.markdown(f"""
                        <div style='background:#fff5f5;border:2px solid #e53e3e;border-radius:10px;
                            padding:12px 18px;direction:rtl;margin-bottom:10px;'>
                            🗑️ تم تحديد <b style='color:#e53e3e;font-size:16px;'>{_n}</b> فاتورة للحذف:
                            <b>{", ".join([x[1] for x in _selected_ids[:5]])}{" ..." if _n > 5 else ""}</b>
                        </div>
                        """, unsafe_allow_html=True)

                        _confirm_del = st.checkbox(
                            f"✅ أؤكد حذف {_n} فاتورة نهائياً ولا يمكن التراجع",
                            key="confirm_bulk_del")

                        if _confirm_del:
                            if st.button(f"🗑️ حذف {_n} فاتورة المحددة", key="do_bulk_del",
                                        type="primary", use_container_width=True):
                                _deleted_count = 0
                                for _did, _dno in _selected_ids:
                                    c.execute("DELETE FROM archived_invoices WHERE id=?", (_did,))
                                    c.execute("DELETE FROM signed_invoices WHERE invoice_no=?", (_dno,))
                                    save_log("حذف فاتورة نهائي", _dno, 0,
                                             f"حُذفت بواسطة مدير النظام [{u['full_name']}]",
                                             u['full_name'])
                                    _deleted_count += 1
                                conn.commit()
                                # إعادة ضبط التحديد
                                for _did, _ in _selected_ids:
                                    st.session_state.pop(f"del_chk_{_did}", None)
                                st.success(f"✅ تم حذف {_deleted_count} فاتورة بنجاح.")
                                st.rerun()
                    else:
                        st.info("☑️ حدد فاتورة أو أكثر من القائمة أعلاه للبدء.")

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
    # صفحة: تغيير كلمة مرور مدير النظام (محمية بكلمة مرور خاصة)
    # ---------------------------------------------------------
    elif st.session_state.page == "change_admin_pwd":
        st.markdown("<div class='main-title'>🔑 تغيير كلمة مرور مدير النظام</div>", unsafe_allow_html=True)

        if u['role'] != "مدير نظام":
            st.error("❌ هذه الصفحة متاحة لمدير النظام فقط.")
        elif not st.session_state.get('admin_pwd_auth'):
            st.markdown("""
            <div style='background:#fff3cd;border:2px solid #f9a825;border-radius:10px;padding:20px;text-align:center;margin-bottom:20px;'>
                🔐 <b>هذه الصفحة محمية بكلمة مرور إضافية خاصة</b><br>
                <small>أدخل كلمة المرور الإضافية للوصول إلى تغيير كلمة مرور مدير النظام</small>
            </div>""", unsafe_allow_html=True)
            _, col_ap, _ = st.columns([1, 1.5, 1])
            with col_ap:
                with st.form("admin_pwd_auth_form"):
                    ap_pass = st.text_input("كلمة المرور الإضافية:", type="password")
                    if st.form_submit_button("🔓 دخول", use_container_width=True):
                        if ap_pass == "Saeed1102193511":
                            st.session_state['admin_pwd_auth'] = True
                            st.rerun()
                        else:
                            st.error("❌ كلمة المرور غير صحيحة!")
        else:
            _, col_ap_lock = st.columns([4, 1])
            if col_ap_lock.button("🔒 قفل الصفحة", key="lock_admin_pwd"):
                st.session_state['admin_pwd_auth'] = False; st.rerun()

            st.info("🔑 من هنا يمكنك تغيير كلمة مرور حساب مدير النظام الخاص بك.")
            admin_users = pd.read_sql("SELECT username, full_name FROM users WHERE role='مدير نظام'", conn)
            if admin_users.empty:
                st.warning("⚠️ لا يوجد حسابات مدير نظام مسجلة.")
            else:
                with st.form("change_admin_pwd_form", clear_on_submit=True):
                    if len(admin_users) > 1:
                        sel_admin = st.selectbox("اختر حساب مدير النظام:",
                            options=admin_users['username'].tolist(),
                            format_func=lambda x: admin_users[admin_users['username']==x]['full_name'].values[0] + f" ({x})")
                    else:
                        sel_admin = admin_users.iloc[0]['username']
                        st.info(f"الحساب: **{admin_users.iloc[0]['full_name']}** ({sel_admin})")
                    cap1, cap2 = st.columns([1, 1])
                    new_admin_pwd  = cap1.text_input("كلمة المرور الجديدة *", type="password")
                    conf_admin_pwd = cap2.text_input("تأكيد كلمة المرور الجديدة *", type="password")
                    if st.form_submit_button("💾 تغيير كلمة المرور", use_container_width=True):
                        if not new_admin_pwd:
                            st.error("⚠️ يرجى إدخال كلمة المرور الجديدة.")
                        elif new_admin_pwd != conf_admin_pwd:
                            st.error("❌ كلمة المرور وتأكيدها غير متطابقين!")
                        else:
                            c.execute("UPDATE users SET password=? WHERE username=?", (new_admin_pwd, sel_admin))
                            save_log("تغيير كلمة مرور مدير النظام", sel_admin, 0,
                                     f"تم تغيير كلمة مرور مدير النظام بكلمة المرور الإضافية", u['full_name'])
                            conn.commit()
                            st.success("✅ تم تغيير كلمة مرور مدير النظام بنجاح!")
                            st.session_state['admin_pwd_auth'] = False
                            st.rerun()

    # ---------------------------------------------------------
    # صفحة: تقديم طلب إلغاء فاتورة (موجه البلاغات)
    # ---------------------------------------------------------
    elif st.session_state.page == "cancel_invoice_user":
        st.markdown("<div class='main-title'>🚫 تقديم طلب إلغاء فاتورة</div>", unsafe_allow_html=True)
        st.info("ℹ️ يمكنك هنا تقديم طلب إلغاء فاتورة صرف. سيتم مراجعة الطلب من قِبل مسؤول المستودع أو مدير النظام، وعند الاعتماد ستُرجع المواد للمستودع المحدد.")

        tab_new_cancel, tab_my_cancel = st.tabs(["➕ طلب إلغاء جديد", "📋 طلباتي السابقة"])

        with tab_new_cancel:
            c1_cn, c2_cn = st.columns([1, 1.5])
            cancel_inv_type_sel = c1_cn.selectbox("نوع الفاتورة:", ["صرف", "تحويل"], key="cancel_type_sel")
            cancel_inv_no_input = c2_cn.text_input("رقم الفاتورة المراد إلغاؤها *", key="cancel_no_input").strip()

            if st.button("🔍 بحث عن الفاتورة", key="cancel_search_btn"):
                if not cancel_inv_no_input:
                    st.error("❌ يرجى إدخال رقم الفاتورة!")
                else:
                    df_ci = pd.read_sql(
                        "SELECT * FROM archived_invoices WHERE invoice_no=? AND invoice_type=?",
                        conn, params=(cancel_inv_no_input, cancel_inv_type_sel))
                    if df_ci.empty:
                        st.error(f"❌ لم يتم العثور على فاتورة {cancel_inv_type_sel} برقم ({cancel_inv_no_input}).")
                        st.session_state['cancel_inv_data'] = None
                    else:
                        st.session_state['cancel_inv_data'] = df_ci.iloc[0].to_dict()
                        st.session_state['cancel_inv_confirm'] = False

            if st.session_state.get('cancel_inv_data'):
                ci_row = st.session_state['cancel_inv_data']
                st.success(f"✅ تم العثور على الفاتورة | المستودع: {ci_row.get('warehouse_from','')} | المقاول: {ci_row.get('contractor','')} | التاريخ: {ci_row.get('timestamp','')}")

                # ── معاينة الفاتورة ──
                if st.button("👁️ معاينة الفاتورة", key="cancel_preview_btn"):
                    st.session_state['cancel_show_preview'] = not st.session_state.get('cancel_show_preview', False)
                if st.session_state.get('cancel_show_preview', False):
                    _ci_html = pd.read_sql("SELECT html_content FROM archived_invoices WHERE id=?",
                                           conn, params=(int(ci_row['id']),))
                    if not _ci_html.empty:
                        components.html(_ci_html.iloc[0]['html_content'], height=480, scrolling=True)

                st.markdown("---")

                # ── بيانات الإلغاء ──
                st.markdown("##### 📝 بيانات طلب الإلغاء:")
                ci_col1, ci_col2 = st.columns([1, 1])
                # المستودع الذي ستُرجع إليه المواد
                _wh_opts_ci = list_warehouses
                _ci_wh_default = ci_row.get('warehouse_from', '')
                _ci_wh_idx = _wh_opts_ci.index(_ci_wh_default) if _ci_wh_default in _wh_opts_ci else 0
                cancel_wh_return = ci_col1.selectbox(
                    "📍 المستودع الذي ستُرجع إليه المواد *",
                    _wh_opts_ci, index=_ci_wh_idx, key="cancel_wh_return"
                )
                # المقاول المسلّم للمادة
                _con_opts_ci = list_contractors
                _ci_con_default = ci_row.get('contractor', '')
                _ci_con_idx = _con_opts_ci.index(_ci_con_default) if _ci_con_default in _con_opts_ci else 0
                cancel_contractor = ci_col2.selectbox(
                    "🏗️ المقاول المسلّم للمادة *",
                    _con_opts_ci, index=_ci_con_idx, key="cancel_contractor_sel"
                )
                # سبب الإلغاء الإجباري
                cancel_reason = st.text_area(
                    "📝 سبب الإلغاء * (إجباري)",
                    placeholder="يرجى كتابة سبب إلغاء الفاتورة بوضوح...",
                    key="cancel_reason_txt",
                    height=80
                )
                # BOQ الحالة الإجبارية
                cancel_boq = st.text_input(
                    "📋 BOQ الحالة * (إجباري)",
                    placeholder="أدخل رقم أو وصف BOQ الحالة...",
                    key="cancel_boq_txt"
                ).strip()

                if not st.session_state.get('cancel_inv_confirm'):
                    st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                    if st.button("🚫 تقديم طلب الإلغاء", key="submit_cancel_req"):
                        if not cancel_reason.strip():
                            st.error("❌ يرجى كتابة سبب الإلغاء — هذا الحقل إجباري!")
                        elif not st.session_state.get('cancel_boq_txt', '').strip():
                            st.error("❌ يرجى إدخال BOQ الحالة — هذا الحقل إجباري!")
                        else:
                            st.session_state['cancel_inv_confirm'] = True
                            st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    ci_items = json.loads(ci_row.get('items_json', '[]'))
                    items_summary = "، ".join([f"{i.get('name','?')} ({i.get('qty',0)})" for i in ci_items])
                    _cr_text = st.session_state.get('cancel_reason_txt', cancel_reason)
                    _cr_wh   = st.session_state.get('cancel_wh_return', cancel_wh_return)
                    _cr_con  = st.session_state.get('cancel_contractor_sel', cancel_contractor)
                    st.markdown(f"""<div class='warn-box'>⚠️ <b>هل أنت متأكد أنك تريد إلغاء الفاتورة؟</b><br>
                    سيتم ارجاع المواد المصروفة إلى مستودع <b>{_cr_wh}</b> بعد الاعتماد كما هو في خانة الارجاع.<br>
                    المواد: {items_summary}<br>
                    <b>سبب الإلغاء:</b> {_cr_text}<br>
                    <b>المقاول:</b> {_cr_con}
                    </div>""", unsafe_allow_html=True)
                    col_cy, col_cn_cancel = st.columns([1, 1])
                    if col_cy.button("✅ نعم، تأكيد وإرسال الطلب", key="confirm_cancel_yes"):
                        ts_c = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                        req_no_c = "CR" + now_mecca().strftime("%d%H%M")
                        _ci_html_row = pd.read_sql("SELECT html_content FROM archived_invoices WHERE id=?",
                                                   conn, params=(int(ci_row['id']),))
                        _ci_html_content = _ci_html_row.iloc[0]['html_content'] if not _ci_html_row.empty else ""
                        c.execute("""INSERT INTO cancel_invoice_requests
                                     (request_no, invoice_no, invoice_type, warehouse_return, contractor, items_json,
                                      cancel_reason, boq, requester, status, invoice_html, timestamp)
                                     VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                  (req_no_c, ci_row['invoice_no'], ci_row['invoice_type'],
                                   st.session_state.get('cancel_wh_return', cancel_wh_return),
                                   st.session_state.get('cancel_contractor_sel', cancel_contractor),
                                   ci_row.get('items_json', '[]'),
                                   st.session_state.get('cancel_reason_txt', cancel_reason),
                                   st.session_state.get('cancel_boq_txt', ''),
                                   u['full_name'], "معلق", _ci_html_content, ts_c))
                        conn.commit()
                        save_log("طلب إلغاء فاتورة", "—", 0,
                                 f"طلب إلغاء فاتورة [{ci_row['invoice_no']}] — السبب: {st.session_state.get('cancel_reason_txt', '')}",
                                 u['full_name'])
                        st.session_state['cancel_inv_data'] = None
                        st.session_state['cancel_inv_confirm'] = False
                        st.session_state['last_cancel_req_no'] = req_no_c
                        st.success(f"✅ تم إرسال طلب الإلغاء رقم ({req_no_c}) بنجاح — بانتظار اعتماد مسؤول المستودع أو مدير النظام.")
                        st.rerun()
                    if col_cn_cancel.button("❌ إلغاء", key="confirm_cancel_no"):
                        st.session_state['cancel_inv_confirm'] = False; st.rerun()

            # ── إشعار نجاح بعد إرسال الطلب ──
            if st.session_state.get('last_cancel_req_no') and not st.session_state.get('cancel_inv_data'):
                st.markdown(
                    f"<div style='background:#e8f5e9;border:2px solid #1daa60;border-radius:12px;"
                    f"padding:18px;text-align:center;direction:rtl;margin-top:16px;'>"
                    f"✅ <b>تم إنشاء طلب إلغاء الفاتورة بنجاح — بانتظار اعتماد مدير النظام أو أمين المستودع</b><br>"
                    f"رقم الطلب: <span style='color:red;font-weight:900;font-size:18px;'>"
                    f"{st.session_state['last_cancel_req_no']}</span><br>"
                    f"<small>لن تُرجع المواد إلى المستودع إلا بعد الاعتماد.</small>"
                    f"</div>",
                    unsafe_allow_html=True)
                if st.button("✖️ إغلاق الإشعار", key="close_cancel_notif"):
                    st.session_state['last_cancel_req_no'] = None; st.rerun()

        with tab_my_cancel:
            st.write(f"### 📋 طلبات الإلغاء المقدمة من: {u['full_name']}")
            df_my_cancel = pd.read_sql(
                "SELECT * FROM cancel_invoice_requests WHERE requester=? ORDER BY id DESC",
                conn, params=(u['full_name'],))
            if df_my_cancel.empty:
                st.info("ℹ️ لم تقدم أي طلبات إلغاء فواتير حتى الآن.")
            else:
                for _, cr in df_my_cancel.iterrows():
                    sc = "#2e7d32" if cr['status']=="معتمد" else ("#d32f2f" if cr['status']=="مرفوض" else "#f9a825")
                    st.markdown(f"""<div class='report-box'>
                        🚫 <b>طلب إلغاء رقم (<span style='color:red;'>{cr['request_no']}</span>)</b>
                        <span style='background:{sc};color:white;border-radius:8px;padding:2px 10px;'>{cr['status']}</span><br>
                        📄 رقم الفاتورة: <b>{cr['invoice_no']}</b> ({cr['invoice_type']}) | 📍 المستودع: {cr['warehouse_return']} | 🏗️ {cr['contractor']}<br>
                        📅 {cr['timestamp']} | <b>السبب:</b> {cr['cancel_reason']}
                        {f"<br>✅ اعتمده: <b>{cr['approved_by']}</b> في {cr['approved_at']}" if cr.get('approved_by') else ""}
                    </div>""", unsafe_allow_html=True)
                    st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: اعتماد طلبات إلغاء الفواتير (مسؤول مستودع / مدير نظام)
    # ---------------------------------------------------------
    elif st.session_state.page == "cancel_invoice_admin":
        st.markdown("<div class='main-title'>🚫 طلبات إلغاء الفواتير — المراجعة والاعتماد</div>", unsafe_allow_html=True)
        if role == "موجه بلاغات":
            st.error("❌ هذه الصفحة متاحة لمسؤول المستودع ومدير النظام فقط.")
        else:
            tab_cancel_pending, tab_cancel_all = st.tabs(["⏳ الطلبات المعلقة", "📋 جميع الطلبات"])

            with tab_cancel_pending:
                df_cancel_pending = pd.read_sql(
                    "SELECT * FROM cancel_invoice_requests WHERE status='معلق' ORDER BY id DESC", conn)
                if df_cancel_pending.empty:
                    st.success("✅ لا توجد طلبات إلغاء فواتير معلقة حالياً.")
                else:
                    st.info(f"📋 يوجد ({len(df_cancel_pending)}) طلب إلغاء معلق.")
                    for _, cr in df_cancel_pending.iterrows():
                        cr_items = json.loads(cr.get('items_json', '[]'))
                        with st.expander(f"🚫 طلب رقم {cr['request_no']} | الفاتورة: {cr['invoice_no']} | من: {cr['requester']} | {cr['timestamp']}", expanded=True):
                            st.markdown(f"""
                            <div style='background:#fce4ec;border:1px solid #c62828;border-radius:8px;padding:12px;margin-bottom:10px;'>
                                📄 <b>فاتورة {cr['invoice_type']}:</b> {cr['invoice_no']}<br>
                                📍 <b>المستودع الذي سترجع إليه المواد:</b> {cr['warehouse_return']}<br>
                                🏗️ <b>المقاول:</b> {cr['contractor']}<br>
                                👤 <b>مقدّم الطلب:</b> {cr['requester']}<br>
                                📝 <b>سبب الإلغاء:</b> {cr['cancel_reason']}
                            </div>""", unsafe_allow_html=True)

                            # عرض المواد
                            st.write("##### 📦 المواد التي ستُرجع للمستودع:")
                            if cr_items:
                                df_cr_items = pd.DataFrame(cr_items)
                                _cr_cols = ['code','name','qty'] if 'code' in df_cr_items.columns else df_cr_items.columns.tolist()
                                html_table(df_cr_items[_cr_cols].rename(columns={'code':'كود المادة','name':'الاسم','qty':'الكمية'}), accent='#004a99',
                                  # dummy comment to replace next line
                                             use_container_width=True, hide_index=True)

                            # معاينة الفاتورة الأصلية
                            if st.button(f"👁️ معاينة الفاتورة الأصلية", key=f"cancel_prev_{cr['id']}"):
                                st.session_state.view_archived_html[f"cancel_{cr['id']}"] = not st.session_state.view_archived_html.get(f"cancel_{cr['id']}", False)
                            if st.session_state.view_archived_html.get(f"cancel_{cr['id']}", False) and cr.get('invoice_html'):
                                components.html(cr['invoice_html'], height=480, scrolling=True)

                            st.write("---")
                            btn_ca1, btn_ca2 = st.columns([1, 1])
                            ca_confirm_key = f"ca_confirm_{cr['id']}"
                            if ca_confirm_key not in st.session_state: st.session_state[ca_confirm_key] = False

                            st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                            if btn_ca1.button(f"✅ اعتماد الإلغاء وارجاع المواد", key=f"ca_approve_{cr['id']}"):
                                st.session_state[ca_confirm_key] = True
                            st.markdown("</div>", unsafe_allow_html=True)
                            st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                            if btn_ca2.button(f"❌ رفض الطلب", key=f"ca_reject_{cr['id']}"):
                                c.execute("UPDATE cancel_invoice_requests SET status='مرفوض', approved_by=?, approved_at=? WHERE id=?",
                                          (u['full_name'], now_mecca().strftime("%Y-%m-%d %H:%M:%S"), int(cr['id'])))
                                conn.commit()
                                save_log("رفض طلب إلغاء فاتورة", "—", 0,
                                         f"رفض طلب إلغاء الفاتورة [{cr['invoice_no']}] من [{cr['requester']}]",
                                         u['full_name'])
                                st.warning(f"⚠️ تم رفض طلب الإلغاء ({cr['request_no']})."); st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)

                            if st.session_state.get(ca_confirm_key):
                                items_sum_ca = "، ".join([f"{i.get('name','?')} ({i.get('qty',0)})" for i in cr_items])
                                st.markdown(f"""<div class='warn-box'>⚠️ <b>تأكيد اعتماد إلغاء الفاتورة ({cr['invoice_no']})؟</b><br>
                                سيتم ارجاع المواد التالية إلى مستودع <b>{cr['warehouse_return']}</b>:<br>
                                {items_sum_ca}
                                </div>""", unsafe_allow_html=True)
                                cay, can_c = st.columns([1, 1])
                                if cay.button(f"✅ نعم، اعتماد الإلغاء", key=f"ca_yes_{cr['id']}"):
                                    ts_ca = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                                    for fitem in cr_items:
                                        c.execute("INSERT INTO inventory (item_code, qty, warehouse, contractor, category) VALUES (?,?,?,?,?)",
                                                  (fitem.get('code',''), int(fitem.get('qty',0)), cr['warehouse_return'],
                                                   cr.get('contractor',''), fitem.get('cat','')))
                                        save_log("اعتماد إلغاء فاتورة", fitem.get('code',''), int(fitem.get('qty',0)),
                                                 f"إلغاء فاتورة [{cr['invoice_no']}] وارجاع المواد لمستودع [{cr['warehouse_return']}] — السبب: {cr['cancel_reason']}",
                                                 u['full_name'])
                                    c.execute("UPDATE cancel_invoice_requests SET status='معتمد', approved_by=?, approved_at=? WHERE id=?",
                                              (u['full_name'], ts_ca, int(cr['id'])))
                                    conn.commit()
                                    st.success(f"🎉 تم اعتماد إلغاء الفاتورة ({cr['invoice_no']}) وارجاع المواد لمستودع [{cr['warehouse_return']}] بنجاح!"); st.rerun()
                                if can_c.button(f"❌ إلغاء", key=f"ca_no_{cr['id']}"):
                                    st.session_state[ca_confirm_key] = False; st.rerun()

            with tab_cancel_all:
                st.write("### 📋 جميع طلبات الإلغاء")
                df_cancel_all = pd.read_sql("SELECT * FROM cancel_invoice_requests ORDER BY id DESC", conn)
                if df_cancel_all.empty:
                    st.info("ℹ️ لا توجد أي طلبات إلغاء في النظام حتى الآن.")
                else:
                    for _, cr in df_cancel_all.iterrows():
                        sc = "#2e7d32" if cr['status']=="معتمد" else ("#d32f2f" if cr['status']=="مرفوض" else "#f9a825")
                        st.markdown(f"""<div class='report-box'>
                            🚫 <b>طلب إلغاء (<span style='color:red;'>{cr['request_no']}</span>)</b>
                            <span style='background:{sc};color:white;border-radius:8px;padding:2px 10px;'>{cr['status']}</span><br>
                            📄 فاتورة: <b>{cr['invoice_no']}</b> | 📍 {cr['warehouse_return']} | 🏗️ {cr['contractor']}<br>
                            👤 {cr['requester']} | 📅 {cr['timestamp']} | السبب: {cr['cancel_reason']}
                            {f"<br>✅ اعتمده: <b>{cr['approved_by']}</b> في {cr['approved_at']}" if cr.get('approved_by') else ""}
                        </div>""", unsafe_allow_html=True)
                        st.markdown("<hr style='margin:4px 0;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: رصيد المستودعات لأمين مستودع المقاول (مقيّد بالمستودعات المصرح بها)
    # ---------------------------------------------------------
    elif st.session_state.page == "contractor_inventory":
        if u['role'] != "أمين مستودع المقاول":
            st.error("❌ غير مصرح لك بالوصول لهذه الصفحة.")
        else:
            st.markdown("<div class='main-title'>📊 رصيد المستودعات المصرح بها</div>", unsafe_allow_html=True)
            _cwp = pd.read_sql(
                "SELECT warehouse FROM contractor_warehouse_permissions WHERE username=?",
                conn, params=(u['username'],))
            _allowed_wh = _cwp['warehouse'].tolist()
            if not _allowed_wh:
                st.warning("⚠️ لا توجد مستودعات مصرح لك برؤيتها. يرجى التواصل مع مدير النظام.")
            else:
                st.info(f"🏢 المستودعات المصرح بها: {', '.join(_allowed_wh)}")
                col_s1, col_s2 = st.columns([2, 1])
                search_txt_cwk = col_s1.text_input("🔍 ابحث بكود المادة أو اسمها")
                cat_filter_cwk = col_s2.selectbox("تصفية بحسب الفئة", ["عرض الكل"] + list_categories)
                wh_placeholder = "','".join(_allowed_wh)
                query_cwk = f"""SELECT i.item_code as 'كود المادة', m.item_name as 'اسم المادة',
                           i.category as 'الفئة', i.warehouse as 'المستودع', SUM(i.qty) as 'الرصيد المتاح'
                           FROM inventory i JOIN material_definitions m ON i.item_code = m.item_code
                           WHERE i.warehouse IN ('{wh_placeholder}')"""
                if cat_filter_cwk != "عرض الكل":
                    query_cwk += f" AND i.category='{cat_filter_cwk}'"
                query_cwk += " GROUP BY i.item_code, i.warehouse HAVING SUM(i.qty) > 0"
                df_cwk_inv = pd.read_sql(query_cwk, conn)
                if search_txt_cwk:
                    df_cwk_inv = df_cwk_inv[
                        df_cwk_inv['اسم المادة'].str.contains(search_txt_cwk, na=False) |
                        df_cwk_inv['كود المادة'].str.contains(search_txt_cwk, na=False)]
                if not df_cwk_inv.empty:
                    rows_html_cwk = ""
                    for _, row in df_cwk_inv.iterrows():
                        qty = int(row['الرصيد المتاح'])
                        if qty <= 5:   badge_bg="#d32f2f"; badge_fg="white"
                        elif qty <= 15: badge_bg="#f9a825"; badge_fg="#333"
                        else:           badge_bg="#004a99"; badge_fg="white"
                        rows_html_cwk += f"""
                        <tr>
                            <td style='font-weight:900;color:#004a99;font-size:12px;padding:9px 12px;border-bottom:1px solid #f0f4f8;'>{row['كود المادة']}</td>
                            <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;font-size:13px;'>{row['اسم المادة']}</td>
                            <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;color:#555;font-size:12px;'>{row['الفئة']}</td>
                            <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;font-size:12px;font-weight:bold;color:#333;'>📍 {row['المستودع']}</td>
                            <td style='padding:9px 12px;border-bottom:1px solid #f0f4f8;text-align:center;'>
                                <span style='display:inline-block;background:{badge_bg};color:{badge_fg};border-radius:20px;padding:3px 14px;font-weight:900;font-size:13px;min-width:36px;text-align:center;'>{qty}</span>
                            </td>
                        </tr>"""
                    table_h = min(80 + len(df_cwk_inv)*42, 550)
                    components.html(f"""<html><head><meta charset="utf-8">
                    <style>body{{margin:0;padding:0;font-family:'Tajawal',Arial,sans-serif;direction:rtl;}}
                    .wrap{{border-radius:12px;overflow:hidden;box-shadow:0 2px 14px rgba(0,74,153,0.12);border:1px solid #e8eef6;}}
                    table{{width:100%;border-collapse:collapse;}}
                    thead tr{{background:linear-gradient(90deg,#004a99,#0066cc);color:white;font-weight:900;font-size:13px;}}
                    thead th{{padding:11px 12px;text-align:right;font-weight:900;}}
                    tbody tr:nth-child(even){{background:#f7faff;}}
                    tbody tr:hover{{background:#e8f0fe;}}
                    .info{{display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:#f0f4ff;border-bottom:1px solid #dde6f5;font-size:13px;color:#555;direction:rtl;}}
                    </style></head><body>
                    <div class="info"><span>📦 الأصناف: <b style="color:#004a99;font-size:15px;">{len(df_cwk_inv)}</b></span>
                    <span style="font-size:11px;color:#888;">🔴 حرج ≤5 &nbsp; 🟡 تنبيه ≤15 &nbsp; 🔵 آمن</span></div>
                    <div class="wrap"><table>
                    <thead><tr><th style="width:14%;">كود المادة</th><th style="width:38%;">اسم الصنف</th><th style="width:18%;">الفئة</th><th style="width:18%;">المستودع</th><th style="width:12%;text-align:center;">الرصيد</th></tr></thead>
                    <tbody>{rows_html_cwk}</tbody></table></div>
                    </body></html>""", height=table_h, scrolling=True)
                else:
                    st.warning("⚠️ لا توجد مواد في المستودعات المصرح بها.")

    # ---------------------------------------------------------
    # صفحات أمين مستودع المقاول — عرض الفواتير مع التوقيع والإرفاق
    # ---------------------------------------------------------
    elif st.session_state.page in ("cwk_dispatch_invoices", "cwk_return_invoices",
                                    "cwk_transfer_invoices", "cwk_emg_dispatch",
                                    "cwk_emg_return", "cwk_emg_transfer"):
        if u['role'] != "أمين مستودع المقاول":
            st.error("❌ غير مصرح لك بالوصول لهذه الصفحة.")
        else:
            import base64
            _page_map = {
                "cwk_dispatch_invoices": ("صرف",   "📋 طلبات فواتير الصرف"),
                "cwk_return_invoices":   ("ارجاع", "📤 طلبات الارجاع الواردة"),
                "cwk_transfer_invoices": ("نقل",   "🚛 طلبات نقل المواد الواردة"),
                "cwk_emg_dispatch":      ("صرف",   "🚨 طلبات طرف مواد طوارئ واردة"),
                "cwk_emg_return":        ("ارجاع", "↩️ طلبات ارجاع مواد طوارئ واردة"),
                "cwk_emg_transfer":      ("نقل",   "🔁 طلبات نقل مواد واردة"),
            }
            _inv_type, _page_title = _page_map[st.session_state.page]
            st.markdown(f"<div class='main-title'>{_page_title}</div>", unsafe_allow_html=True)

            # ── إحصائية لهذا النوع ──
            _total_inv = int(pd.read_sql(
                f"SELECT COUNT(*) as cnt FROM archived_invoices WHERE invoice_type='{_inv_type}'", conn
            ).iloc[0]['cnt'])
            try:
                _approved_inv  = int(pd.read_sql(
                    f"SELECT COUNT(*) as cnt FROM signed_invoices WHERE invoice_type='{_inv_type}' AND status='معتمد'", conn
                ).iloc[0]['cnt'])
                _waiting_inv   = int(pd.read_sql(
                    f"SELECT COUNT(*) as cnt FROM signed_invoices WHERE invoice_type='{_inv_type}' AND status='بانتظار الاعتماد'", conn
                ).iloc[0]['cnt'])
                _returned_inv  = int(pd.read_sql(
                    f"SELECT COUNT(*) as cnt FROM signed_invoices WHERE invoice_type='{_inv_type}' AND status='مُعادة'", conn
                ).iloc[0]['cnt'])
            except Exception:
                _approved_inv = _waiting_inv = _returned_inv = 0
            _unsigned_inv = max(0, _total_inv - _approved_inv - _waiting_inv - _returned_inv)

            cs1, cs2, cs3, cs4 = st.columns(4)
            cs1.metric("📄 الإجمالي",              _total_inv)
            cs2.metric("⏳ بانتظار إرفاقك",        _unsigned_inv)
            cs3.metric("🔄 أُرسلت للاعتماد",       _waiting_inv)
            cs4.metric("✅ معتمدة ومخصومة",         _approved_inv)

            if _returned_inv > 0:
                st.error(f"🔴 لديك {_returned_inv} فاتورة مُعادة إليك من المدير — يرجى مراجعتها وإعادة الإرفاق.")

            st.divider()

            # ── فلاتر ──
            _fcol1, _fcol2 = st.columns([2, 1])
            _search_no     = _fcol1.text_input("🔍 ابحث برقم الفاتورة", key=f"cwk_search_{st.session_state.page}").strip()
            _filter_status = _fcol2.selectbox("الحالة:", ["الكل", "⏳ بانتظار الإرفاق", "🔄 بانتظار الاعتماد", "✅ معتمدة", "🔴 مُعادة"],
                                               key=f"cwk_filter_{st.session_state.page}")

            # ── جلب الفواتير ──
            _role_names = pd.read_sql(
                "SELECT full_name FROM users WHERE role IN ('موجه بلاغات','موظف مستودع','أمين مستودع','مدير نظام')", conn
            )['full_name'].tolist()

            _query_arch = f"SELECT * FROM archived_invoices WHERE invoice_type='{_inv_type}'"
            if _search_no:
                _query_arch += f" AND invoice_no LIKE '%{_search_no}%'"
            _query_arch += " ORDER BY id DESC LIMIT 100"

            df_cwk_list = pd.read_sql(_query_arch, conn)
            if not df_cwk_list.empty and _role_names:
                df_cwk_list = df_cwk_list[df_cwk_list['employee'].isin(_role_names)]

            if df_cwk_list.empty:
                st.info("ℹ️ لا توجد فواتير حتى الآن.")
            else:
                # خريطة الفواتير الموقعة لهذا النوع
                _all_signed = pd.read_sql(
                    f"SELECT invoice_no, signed_by, signed_at, status, admin_notes, reviewed_by, reviewed_at FROM signed_invoices WHERE invoice_type='{_inv_type}'", conn)
                _signed_map = {str(r['invoice_no']): r for _, r in _all_signed.iterrows()}

                for _, inv_row in df_cwk_list.iterrows():
                    inv_id  = int(inv_row['id'])
                    inv_no  = str(inv_row['invoice_no'])
                    _sd     = _signed_map.get(inv_no)
                    _s_stat = str(_sd['status']) if _sd is not None else "لم يُرفق"

                    # تطبيق فلتر الحالة
                    if _filter_status == "⏳ بانتظار الإرفاق" and _s_stat != "لم يُرفق":      continue
                    if _filter_status == "🔄 بانتظار الاعتماد" and _s_stat != "بانتظار الاعتماد": continue
                    if _filter_status == "✅ معتمدة" and _s_stat != "معتمد":                    continue
                    if _filter_status == "🔴 مُعادة" and _s_stat != "مُعادة":                   continue

                    # لون وشارة الحالة
                    _badge_map = {
                        "لم يُرفق":           ("<span style='background:#9e9e9e;color:white;border-radius:8px;padding:2px 10px;font-size:12px;'>📝 لم يُرفق بعد</span>",          False),
                        "بانتظار الاعتماد":   ("<span style='background:#0288d1;color:white;border-radius:8px;padding:2px 10px;font-size:12px;'>🔄 أُرسلت للاعتماد</span>",       False),
                        "معتمد":              ("<span style='background:#1daa60;color:white;border-radius:8px;padding:2px 10px;font-size:12px;'>✅ معتمدة ومخصومة</span>",       False),
                        "مرفوض":              ("<span style='background:#d32f2f;color:white;border-radius:8px;padding:2px 10px;font-size:12px;'>❌ مرفوضة</span>",               False),
                        "مُعادة":             ("<span style='background:#e65100;color:white;border-radius:8px;padding:2px 10px;font-size:12px;'>🔴 مُعادة — يلزم تعديل</span>", True),
                    }
                    _badge_html, _is_returned = _badge_map.get(_s_stat, (_badge_map["لم يُرفق"][0], False))

                    with st.expander(
                        f"📄 فاتورة: {inv_no} | {str(inv_row.get('timestamp',''))[:16]}",
                        expanded=(_s_stat == "مُعادة")):

                        # ── رأس الفاتورة ──
                        _notes_html = ""
                        if _sd is not None and str(_sd.get('admin_notes','')).strip():
                            _notes_html = f"""
                            <div style='background:#fff3cd;border-right:4px solid #f9a825;border-radius:6px;
                                padding:8px 12px;margin-top:8px;direction:rtl;font-size:13px;'>
                                💬 <b>ملاحظة المدير / مسؤول المستودع:</b><br>
                                <span style='color:#333;'>{_sd['admin_notes']}</span><br>
                                <small style='color:#888;'>👤 {_sd.get('reviewed_by','')} | 📅 {_sd.get('reviewed_at','')}</small>
                            </div>"""

                        st.markdown(f"""
                        <div style='background:#f8f9fa;border-right:5px solid {"#e65100" if _is_returned else "#004a99"};
                            border-radius:8px;padding:12px 16px;margin-bottom:10px;direction:rtl;'>
                            {_badge_html}<br>
                            <span style='font-size:13px;color:#333;margin-top:6px;display:block;'>
                                📍 المستودع: <b>{inv_row.get('warehouse_from','—')}</b>
                                {"➡️ " + str(inv_row.get('warehouse_to','')) if inv_row.get('warehouse_to') else ""}
                                {" | 🏗️ المقاول: <b>" + str(inv_row.get('contractor','')) + "</b>" if inv_row.get('contractor') else ""}
                                | 👤 أنشأها: <b>{inv_row.get('employee','—')}</b>
                            </span>
                            {f"<span style='font-size:13px;color:#555;'>✍️ أرفقها: <b>{_sd['signed_by']}</b> | 📅 {_sd['signed_at']}</span>" if _sd is not None else ""}
                            {_notes_html}
                        </div>""", unsafe_allow_html=True)

                        # زر عرض الفاتورة الأصلية
                        _sk = f"show_orig_cwk_{inv_id}"
                        if st.button("👁️ عرض الفاتورة الأصلية", key=f"vorig_{inv_id}"):
                            st.session_state[_sk] = not st.session_state.get(_sk, False)
                        if st.session_state.get(_sk, False):
                            components.html(str(inv_row.get('html_content','')), height=500, scrolling=True)

                        # عرض الصورة المرفقة إن وجدت
                        if _sd is not None and _s_stat in ("بانتظار الاعتماد","معتمد","مرفوض","مُعادة"):
                            _imgk = f"show_sig_cwk_{inv_id}"
                            if st.button("🖼️ عرض الفاتورة الموقعة المرفقة", key=f"vimg_{inv_id}"):
                                st.session_state[_imgk] = not st.session_state.get(_imgk, False)
                            if st.session_state.get(_imgk, False):
                                _fsig = pd.read_sql(
                                    "SELECT signed_image_base64 FROM signed_invoices WHERE invoice_no=? AND invoice_type=?",
                                    conn, params=(inv_no, _inv_type))
                                if not _fsig.empty and _fsig.iloc[0]['signed_image_base64']:
                                    st.markdown(
                                        f'<img src="data:image/jpeg;base64,{_fsig.iloc[0]["signed_image_base64"]}" '
                                        f'style="max-width:100%;border:2px solid #004a99;border-radius:8px;margin-top:8px;">',
                                        unsafe_allow_html=True)

                        st.markdown("---")

                        # ── قسم الإرفاق (يظهر فقط إذا لم يُرفق بعد أو مُعادة) ──
                        if _s_stat in ("لم يُرفق", "مُعادة"):
                            if _is_returned:
                                st.warning("🔴 هذه الفاتورة أُعيدت إليك — يرجى مراجعة الملاحظة أعلاه وإعادة إرفاقها.")

                            st.markdown("### 📎 إرفاق الفاتورة بعد التوقيع")
                            st.info("ℹ️ بعد الإرفاق، ستُرسل الفاتورة لاعتماد مدير النظام أو مسؤول المستودع. لن يتم الخصم إلا بعد الاعتماد.")

                            _up_key = f"upload_cwk_{inv_id}"
                            _uploaded = st.file_uploader(
                                "📤 ارفع صورة الفاتورة الموقعة *",
                                type=["jpg","jpeg","png","pdf"],
                                key=_up_key)

                            if _uploaded is not None:
                                _img_b64 = base64.b64encode(_uploaded.read()).decode()
                                st.markdown("**معاينة:**")
                                st.markdown(
                                    f'<img src="data:image/jpeg;base64,{_img_b64}" '
                                    f'style="max-width:55%;border:2px solid #004a99;border-radius:8px;margin:6px 0;">',
                                    unsafe_allow_html=True)
                                st.markdown(f"""
                                <div style='background:#e3f2fd;border:1px solid #0288d1;border-radius:8px;
                                    padding:10px 14px;direction:rtl;font-size:13px;margin:8px 0;'>
                                    📌 سيُسجَّل الإرفاق باسم: <b>{u['full_name']}</b><br>
                                    📅 الوقت: <b>{now_mecca().strftime("%Y-%m-%d %H:%M")}</b><br>
                                    🔄 ستُرسل للاعتماد — لن يتم الخصم الآن.
                                </div>""", unsafe_allow_html=True)

                                # حقل BOQ / رقم البلاغ (للصرف والارجاع فقط — ليس النقل)
                                if _inv_type != "نقل":
                                    _boq_key = f"cwk_boq_{inv_id}"
                                    _boq_val = st.text_input("📋 رقم البلاغ (BOQ) *",
                                        placeholder="أدخل رقم البلاغ المرتبط بهذه الفاتورة...",
                                        key=_boq_key).strip()
                                    st.markdown(f"""
                                    <div style='background:#fff8e1;border-right:3px solid #f9a825;border-radius:6px;
                                        padding:6px 12px;direction:rtl;font-size:12px;color:#555;margin-bottom:8px;'>
                                        📋 BOQ يظهر على الفاتورة المطبوعة ويُحفظ مع المستند.
                                    </div>""", unsafe_allow_html=True)
                                else:
                                    _boq_val = ""

                                if st.button(f"📨 إرسال للاعتماد", key=f"send_approval_{inv_id}", type="primary"):
                                    if _inv_type != "نقل" and not _boq_val:
                                        st.error("❌ يجب إدخال رقم البلاغ (BOQ) قبل الإرسال للصرف والارجاع.")
                                    else:
                                        _ts_s = now_mecca().strftime("%Y-%m-%d %H:%M:%S")
                                        c.execute("DELETE FROM signed_invoices WHERE invoice_no=? AND invoice_type=?",
                                                  (inv_no, _inv_type))
                                        c.execute(
                                            "INSERT INTO signed_invoices (invoice_no,invoice_type,original_invoice_id,signed_by,signed_image_base64,signed_at,deducted,status,admin_notes,reviewed_by,reviewed_at,boq) VALUES (?,?,?,?,?,?,0,'بانتظار الاعتماد','','',?,?)",
                                            (inv_no, _inv_type, inv_id, u['full_name'], _img_b64, _ts_s, _ts_s, _boq_val))
                                        save_log("إرفاق فاتورة موقعة للاعتماد", "-", 0,
                                                 f"فاتورة {_inv_type} رقم {inv_no} أُرسلت لاعتماد الإدارة | BOQ:{_boq_val} | بواسطة: {u['full_name']}", u['full_name'])
                                        conn.commit()
                                        st.success("✅ تم إرسال الفاتورة للاعتماد بنجاح!")
                                        st.rerun()
                            else:
                                st.caption("⬆️ يرجى رفع صورة الفاتورة للمتابعة.")

                        elif _s_stat == "بانتظار الاعتماد":
                            st.info("🔄 الفاتورة أُرسلت للاعتماد وبانتظار مراجعة المدير أو مسؤول المستودع.")

                        elif _s_stat == "معتمد":
                            st.success("✅ الفاتورة معتمدة وتم خصم المواد من المستودع.")

                        elif _s_stat == "مرفوض":
                            st.error("❌ تم رفض هذه الفاتورة. راجع ملاحظة المدير أعلاه.")

    # ---------------------------------------------------------
    # صفحة: اعتماد فواتير أمين مستودع المقاول (مدير النظام / مسؤول المستودع)
    # ---------------------------------------------------------
    elif st.session_state.page == "approve_signed_invoices":
        if u['role'] not in ("مدير نظام", "موظف مستودع", "أمين مستودع"):
            st.error("❌ غير مصرح لك بالوصول لهذه الصفحة.")
        else:
            import base64
            st.markdown("<div class='main-title'>✍️ اعتماد فواتير أمين مستودع المقاول</div>", unsafe_allow_html=True)

            # ── إحصائية عامة ──
            try:
                _agg = pd.read_sql("SELECT status, COUNT(*) as cnt FROM signed_invoices GROUP BY status", conn)
                _agg_map = {r['status']: int(r['cnt']) for _, r in _agg.iterrows()}
            except Exception:
                _agg_map = {}
            _a1,_a2,_a3,_a4 = st.columns(4)
            _a1.metric("🔄 بانتظار الاعتماد", _agg_map.get("بانتظار الاعتماد", 0))
            _a2.metric("✅ معتمدة",            _agg_map.get("معتمد", 0))
            _a3.metric("❌ مرفوضة",            _agg_map.get("مرفوض", 0))
            _a4.metric("🔴 مُعادة",            _agg_map.get("مُعادة", 0))
            st.divider()

            # ════════════════════════════════════════════════════
            # تبويبان: البحث برقم الفاتورة | قائمة الفواتير
            # ════════════════════════════════════════════════════
            tab_search_inv, tab_list_inv = st.tabs([
                "🔍 بحث برقم الفاتورة",
                "📋 قائمة الفواتير"
            ])

            # ══════════════════════════════════════
            # تبويب ١: البحث برقم الفاتورة
            # ══════════════════════════════════════
            with tab_search_inv:
                st.markdown("""
                <div style='background:#e3f2fd;border:2px solid #0288d1;border-radius:10px;
                    padding:12px 18px;direction:rtl;margin-bottom:16px;font-size:14px;'>
                    🔍 <b>ابحث برقم الفاتورة لعرض الفاتورة الأصلية والمرفق الموقع معاً وحالتها الحالية.</b>
                </div>""", unsafe_allow_html=True)

                _sc1, _sc2 = st.columns([2, 1])
                _inv_search_no  = _sc1.text_input("🔢 رقم الفاتورة *", placeholder="أدخل رقم الفاتورة...", key="appr_inv_search_no").strip()
                _inv_search_type = _sc2.selectbox("نوع الفاتورة:", ["الكل","صرف","ارجاع","نقل"], key="appr_inv_search_type")

                if st.button("🔍 بحث", key="appr_search_btn", type="primary", use_container_width=False):
                    st.session_state["appr_search_result"] = _inv_search_no
                    st.session_state["appr_search_type"]   = _inv_search_type

                _res_no   = st.session_state.get("appr_search_result", "")
                _res_type = st.session_state.get("appr_search_type", "الكل")

                if _res_no:
                    # ── جلب الفاتورة الأصلية ──
                    _arch_q = "SELECT * FROM archived_invoices WHERE invoice_no=?"
                    _arch_params = [_res_no]
                    if _res_type != "الكل":
                        _arch_q += " AND invoice_type=?"
                        _arch_params.append(_res_type)
                    df_orig_res = pd.read_sql(_arch_q, conn, params=_arch_params)

                    # ── جلب الفاتورة الموقعة ──
                    _sign_q = "SELECT s.*, a.items_json, a.warehouse_from, a.warehouse_to, a.contractor FROM signed_invoices s LEFT JOIN archived_invoices a ON s.original_invoice_id = a.id WHERE s.invoice_no=?"
                    _sign_params = [_res_no]
                    if _res_type != "الكل":
                        _sign_q += " AND s.invoice_type=?"
                        _sign_params.append(_res_type)
                    df_sign_res = pd.read_sql(_sign_q, conn, params=_sign_params)

                    if df_orig_res.empty and df_sign_res.empty:
                        st.error(f"❌ لم يتم العثور على أي فاتورة بالرقم ({_res_no}).")
                    else:
                        # ── عرض بطاقة الفاتورة الأصلية ──
                        if not df_orig_res.empty:
                            for _, _orig in df_orig_res.iterrows():
                                st.markdown(f"""
                                <div style='background:#f0f4ff;border-right:5px solid #004a99;
                                    border-radius:10px;padding:14px 18px;direction:rtl;margin-bottom:12px;'>
                                    <b style='font-size:15px;color:#004a99;'>📄 الفاتورة الأصلية</b><br>
                                    <span style='font-size:13px;color:#333;'>
                                        🔢 رقم: <b style='color:#c62828;font-size:15px;'>{_orig['invoice_no']}</b>
                                        | 📂 النوع: <b>{_orig['invoice_type']}</b>
                                        | 📅 التاريخ: <b>{str(_orig.get('timestamp',''))[:16]}</b><br>
                                        📍 المستودع: <b>{_orig.get('warehouse_from','—')}</b>
                                        {" ➡️ <b>" + str(_orig.get('warehouse_to','')) + "</b>" if _orig.get('warehouse_to') else ""}
                                        {" | 🏗️ المقاول: <b>" + str(_orig.get('contractor','')) + "</b>" if _orig.get('contractor') else ""}
                                        | 👤 أنشأها: <b>{_orig.get('employee','—')}</b>
                                    </span>
                                </div>""", unsafe_allow_html=True)

                                _vok_s = f"search_orig_html_{int(_orig['id'])}"
                                if st.button("👁️ عرض محتوى الفاتورة الأصلية", key=f"s_orig_btn_{int(_orig['id'])}"):
                                    st.session_state[_vok_s] = not st.session_state.get(_vok_s, False)
                                if st.session_state.get(_vok_s, False):
                                    _orig_html_r = pd.read_sql("SELECT html_content FROM archived_invoices WHERE id=?", conn, params=(int(_orig['id']),))
                                    if not _orig_html_r.empty:
                                        components.html(str(_orig_html_r.iloc[0]['html_content']), height=500, scrolling=True)

                        st.markdown("---")

                        # ── عرض بطاقة الفاتورة الموقعة ──
                        if df_sign_res.empty:
                            st.info("⏳ لم يتم إرفاق فاتورة موقعة لهذا الرقم بعد.")
                        else:
                            for _, _sr in df_sign_res.iterrows():
                                _sr_status = str(_sr.get('status',''))
                                _sr_color  = {"معتمد":"#1daa60","مرفوض":"#d32f2f","مُعادة":"#e65100","بانتظار الاعتماد":"#0288d1"}.get(_sr_status,"#9e9e9e")
                                _sr_id     = int(_sr['id'])
                                _sr_invno  = str(_sr['invoice_no'])
                                _sr_type   = str(_sr['invoice_type'])
                                _sr_by     = str(_sr.get('signed_by',''))
                                _sr_at     = str(_sr.get('signed_at',''))
                                _sr_notes  = str(_sr.get('admin_notes','') or '')
                                _sr_rev_by = str(_sr.get('reviewed_by','') or '')
                                _sr_rev_at = str(_sr.get('reviewed_at','') or '')

                                st.markdown(f"""
                                <div style='background:#f8f9fa;border-right:5px solid {_sr_color};
                                    border-radius:10px;padding:14px 18px;direction:rtl;margin-bottom:12px;'>
                                    <b style='font-size:15px;color:#333;'>📎 الفاتورة الموقعة المرفقة</b>
                                    <span style='background:{_sr_color};color:white;border-radius:8px;
                                        padding:2px 10px;font-size:12px;font-weight:bold;margin-right:8px;'>{_sr_status}</span><br>
                                    <span style='font-size:13px;color:#333;'>
                                        ✍️ أرفقها: <b>{_sr_by}</b> | 📅 {_sr_at}
                                        {f"<br>🔍 راجعها: <b>{_sr_rev_by}</b> | {_sr_rev_at}" if _sr_rev_by else ""}
                                        {f"<br>💬 الملاحظة: <b>{_sr_notes}</b>" if _sr_notes.strip() else ""}
                                    </span>
                                </div>""", unsafe_allow_html=True)

                                # عرض صورة المرفق
                                _imgk_s = f"search_sig_img_{_sr_id}"
                                if st.button("🖼️ عرض صورة الفاتورة الموقعة", key=f"s_img_btn_{_sr_id}"):
                                    st.session_state[_imgk_s] = not st.session_state.get(_imgk_s, False)
                                if st.session_state.get(_imgk_s, False):
                                    _fsig_s = pd.read_sql("SELECT signed_image_base64 FROM signed_invoices WHERE id=?", conn, params=(_sr_id,))
                                    if not _fsig_s.empty and _fsig_s.iloc[0]['signed_image_base64']:
                                        st.markdown(
                                            f'<img src="data:image/jpeg;base64,{_fsig_s.iloc[0]["signed_image_base64"]}" '
                                            f'style="max-width:100%;border:3px solid {_sr_color};border-radius:8px;margin-top:8px;">',
                                            unsafe_allow_html=True)

                                # ── منطقة اتخاذ القرار (فقط إذا بانتظار الاعتماد) ──
                                if _sr_status == "بانتظار الاعتماد":
                                    st.markdown("---")
                                    st.markdown("### 📝 قرار الاعتماد")
                                    _note_ks = f"s_note_{_sr_id}"
                                    _appr_note_s = st.text_area(
                                        "💬 ملاحظة (اختيارية عند الاعتماد، إجبارية عند الرفض/الإعادة):",
                                        key=_note_ks, height=80)
                                    _sb1, _sb2, _sb3 = st.columns(3)
                                    _ts_rev_s = now_mecca().strftime("%Y-%m-%d %H:%M:%S")

                                    with _sb1:
                                        st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                                        if st.button("✅ اعتماد وتنفيذ الخصم", key=f"s_yes_{_sr_id}", use_container_width=True):
                                            try:
                                                _items_s = json.loads(str(_sr.get('items_json','[]') or '[]'))
                                            except Exception:
                                                _items_s = []
                                            _wf = str(_sr.get('warehouse_from',''))
                                            _wt = str(_sr.get('warehouse_to',''))
                                            _ct = str(_sr.get('contractor',''))
                                            for _it in _items_s:
                                                if _sr_type == "صرف":
                                                    c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                              (_it['code'], -int(_it['qty']), _wf, _ct, _it.get('cat','')))
                                                    save_log("خصم—اعتماد فاتورة مقاول", _it['code'], _it['qty'],
                                                             f"فاتورة {_sr_invno} | اعتمدها: {u['full_name']} | أرفقها: {_sr_by}", u['full_name'])
                                                elif _sr_type == "نقل":
                                                    c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                              (_it['code'], -int(_it['qty']), _wf, '', _it.get('cat','')))
                                                    c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                              (_it['code'], int(_it['qty']), _wt, '', _it.get('cat','')))
                                                    save_log("نقل—اعتماد فاتورة مقاول", _it['code'], _it['qty'],
                                                             f"فاتورة {_sr_invno} | اعتمدها: {u['full_name']}", u['full_name'])
                                                elif _sr_type == "ارجاع":
                                                    c.execute("INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                              (_it['code'], int(_it['qty']), _wf, _ct, _it.get('cat','')))
                                                    save_log("ارجاع—اعتماد فاتورة مقاول", _it['code'], _it['qty'],
                                                             f"فاتورة {_sr_invno} | اعتمدها: {u['full_name']}", u['full_name'])
                                            c.execute("UPDATE signed_invoices SET status='معتمد', deducted=1, admin_notes=?, reviewed_by=?, reviewed_at=? WHERE id=?",
                                                      (_appr_note_s.strip(), u['full_name'], _ts_rev_s, _sr_id))
                                            conn.commit()
                                            st.session_state["appr_search_result"] = ""
                                            st.success(f"✅ تم اعتماد الفاتورة ({_sr_invno}) وتنفيذ الخصم!")
                                            st.rerun()
                                        st.markdown("</div>", unsafe_allow_html=True)

                                    with _sb2:
                                        if st.button("🔄 إعادة لأمين المستودع", key=f"s_ret_{_sr_id}", use_container_width=True):
                                            if not _appr_note_s.strip():
                                                st.error("❌ يجب كتابة ملاحظة عند الإعادة.")
                                            else:
                                                c.execute("UPDATE signed_invoices SET status='مُعادة', deducted=0, admin_notes=?, reviewed_by=?, reviewed_at=? WHERE id=?",
                                                          (_appr_note_s.strip(), u['full_name'], _ts_rev_s, _sr_id))
                                                conn.commit()
                                                st.session_state["appr_search_result"] = ""
                                                st.warning(f"🔄 تم إعادة الفاتورة ({_sr_invno}) مع الملاحظة.")
                                                st.rerun()

                                    with _sb3:
                                        st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                                        if st.button("❌ رفض الفاتورة", key=f"s_no_{_sr_id}", use_container_width=True):
                                            if not _appr_note_s.strip():
                                                st.error("❌ يجب كتابة سبب الرفض.")
                                            else:
                                                c.execute("UPDATE signed_invoices SET status='مرفوض', deducted=0, admin_notes=?, reviewed_by=?, reviewed_at=? WHERE id=?",
                                                          (_appr_note_s.strip(), u['full_name'], _ts_rev_s, _sr_id))
                                                conn.commit()
                                                st.session_state["appr_search_result"] = ""
                                                st.error(f"❌ تم رفض الفاتورة ({_sr_invno}).")
                                                st.rerun()
                                        st.markdown("</div>", unsafe_allow_html=True)

            # ══════════════════════════════════════
            # تبويب ٢: قائمة الفواتير
            # ══════════════════════════════════════
            with tab_list_inv:
                # ── فلاتر ──
                _af1, _af2, _af3 = st.columns([1.5, 1.5, 1])
                _af_type   = _af1.selectbox("نوع الفاتورة:", ["الكل","صرف","ارجاع","نقل"], key="af_type")
                _af_status = _af2.selectbox("الحالة:", ["بانتظار الاعتماد","معتمد","مرفوض","مُعادة","الكل"], key="af_status")
                _af_search = _af3.text_input("🔍 رقم الفاتورة:", key="af_search").strip()

                _aq = "SELECT s.*, a.items_json, a.warehouse_from, a.warehouse_to, a.contractor, a.html_content FROM signed_invoices s LEFT JOIN archived_invoices a ON s.original_invoice_id = a.id WHERE 1=1"
                if _af_type != "الكل":   _aq += f" AND s.invoice_type='{_af_type}'"
                if _af_status != "الكل": _aq += f" AND s.status='{_af_status}'"
                if _af_search:           _aq += f" AND s.invoice_no LIKE '%{_af_search}%'"
                _aq += " ORDER BY s.id DESC"

                df_approve = pd.read_sql(_aq, conn)

                if df_approve.empty:
                    st.info("ℹ️ لا توجد فواتير تطابق الفلاتر المحددة.")
                else:
                    st.caption(f"📋 {len(df_approve)} فاتورة")
                    for _, ar in df_approve.iterrows():
                        _ar_id      = int(ar['id'])
                        _ar_invno   = str(ar['invoice_no'])
                        _ar_type    = str(ar['invoice_type'])
                        _ar_status  = str(ar['status'])
                        _ar_notes   = str(ar.get('admin_notes','') or '')
                        _ar_by      = str(ar.get('signed_by',''))
                        _ar_at      = str(ar.get('signed_at',''))
                        _ar_rev_by  = str(ar.get('reviewed_by','') or '')
                        _ar_rev_at  = str(ar.get('reviewed_at','') or '')

                        _badge_c = {"بانتظار الاعتماد":"#0288d1","معتمد":"#1daa60","مرفوض":"#d32f2f","مُعادة":"#e65100"}.get(_ar_status,"#9e9e9e")

                        with st.expander(
                            f"📄 {_ar_type} | رقم: {_ar_invno} | ✍️ {_ar_by} | {_ar_at[:16]}",
                            expanded=(_ar_status == "بانتظار الاعتماد")):

                            # ── رأس البطاقة ──
                            st.markdown(f"""
                            <div style='background:#f8f9fa;border-right:5px solid {_badge_c};
                                border-radius:8px;padding:12px 16px;margin-bottom:10px;direction:rtl;'>
                                <span style='background:{_badge_c};color:white;border-radius:8px;padding:2px 10px;font-size:12px;font-weight:bold;'>{_ar_status}</span><br>
                                <span style='font-size:13px;color:#333;margin-top:6px;display:block;'>
                                    📍 المستودع: <b>{ar.get('warehouse_from','—')}</b>
                                    {"➡️ " + str(ar.get('warehouse_to','')) if ar.get('warehouse_to') else ""}
                                    {" | 🏗️ المقاول: <b>" + str(ar.get('contractor','')) + "</b>" if ar.get('contractor') else ""}
                                </span>
                                <span style='font-size:13px;color:#555;'>
                                    ✍️ أرفقها: <b>{_ar_by}</b> | 📅 {_ar_at}
                                </span>
                                {f"<br><span style='font-size:13px;color:#888;'>🔍 راجعها: <b>{_ar_rev_by}</b> | {_ar_rev_at}</span>" if _ar_rev_by else ""}
                            </div>""", unsafe_allow_html=True)

                            # ملاحظة سابقة
                            if _ar_notes.strip():
                                st.markdown(f"""
                                <div style='background:#fff3cd;border-right:4px solid #f9a825;border-radius:6px;
                                    padding:8px 12px;margin-bottom:10px;direction:rtl;font-size:13px;'>
                                    💬 <b>الملاحظة السابقة:</b> {_ar_notes}
                                </div>""", unsafe_allow_html=True)

                            # عرض الفاتورة الأصلية
                            _vok = f"vappr_orig_{_ar_id}"
                            if st.button("👁️ عرض الفاتورة الأصلية", key=f"vappr_orig_btn_{_ar_id}"):
                                st.session_state[_vok] = not st.session_state.get(_vok, False)
                            if st.session_state.get(_vok, False):
                                _orig_html = str(ar.get('html_content','') or '')
                                if _orig_html:
                                    components.html(_orig_html, height=480, scrolling=True)

                            # عرض الصورة الموقعة
                            _vik = f"vappr_img_{_ar_id}"
                            if st.button("🖼️ عرض صورة الفاتورة الموقعة", key=f"vappr_img_btn_{_ar_id}"):
                                st.session_state[_vik] = not st.session_state.get(_vik, False)
                            if st.session_state.get(_vik, False):
                                _fsig2 = pd.read_sql(
                                    "SELECT signed_image_base64 FROM signed_invoices WHERE id=?",
                                    conn, params=(_ar_id,))
                                if not _fsig2.empty and _fsig2.iloc[0]['signed_image_base64']:
                                    st.markdown(
                                        f'<img src="data:image/jpeg;base64,{_fsig2.iloc[0]["signed_image_base64"]}" '
                                        f'style="max-width:100%;border:2px solid #004a99;border-radius:8px;margin-top:8px;">',
                                        unsafe_allow_html=True)

                            st.markdown("---")

                            # ── منطقة الاعتماد (فقط للفواتير بانتظار الاعتماد) ──
                            if _ar_status == "بانتظار الاعتماد":
                                st.markdown("### 📝 قرار الاعتماد")

                                # خانة الملاحظة
                                _note_key = f"appr_note_{_ar_id}"
                                _appr_note = st.text_area(
                                    "💬 ملاحظة (تظهر لأمين مستودع المقاول والإدارة):",
                                    placeholder="اكتب ملاحظتك هنا — اختيارية عند الاعتماد، إجبارية عند الرفض أو الإعادة...",
                                    key=_note_key, height=90)

                                _btn1, _btn2, _btn3 = st.columns(3)
                                _ts_rev = now_mecca().strftime("%Y-%m-%d %H:%M:%S")

                                # ── اعتماد وخصم ──
                                with _btn1:
                                    st.markdown("<div class='btn-success'>", unsafe_allow_html=True)
                                    if st.button("✅ اعتماد وتنفيذ الخصم", key=f"appr_yes_{_ar_id}", use_container_width=True):
                                        # تنفيذ الخصم من المخزون
                                        try:
                                            _items = json.loads(str(ar.get('items_json','[]') or '[]'))
                                        except Exception:
                                            _items = []
                                        _wh_f = str(ar.get('warehouse_from',''))
                                        _wh_t = str(ar.get('warehouse_to',''))
                                        _cont = str(ar.get('contractor',''))
                                        for _it in _items:
                                            if _ar_type == "صرف":
                                                c.execute(
                                                    "INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                    (_it['code'], -int(_it['qty']), _wh_f, _cont, _it.get('cat','')))
                                                save_log("خصم — اعتماد فاتورة مقاول", _it['code'], _it['qty'],
                                                         f"فاتورة {_ar_invno} | اعتمدها: {u['full_name']} | أرفقها: {_ar_by}", u['full_name'])
                                            elif _ar_type == "نقل":
                                                c.execute(
                                                    "INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                    (_it['code'], -int(_it['qty']), _wh_f, '', _it.get('cat','')))
                                                c.execute(
                                                    "INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                    (_it['code'], int(_it['qty']), _wh_t, '', _it.get('cat','')))
                                                save_log("نقل — اعتماد فاتورة مقاول", _it['code'], _it['qty'],
                                                         f"فاتورة {_ar_invno} | اعتمدها: {u['full_name']} | أرفقها: {_ar_by}", u['full_name'])
                                            elif _ar_type == "ارجاع":
                                                c.execute(
                                                    "INSERT INTO inventory (item_code,qty,warehouse,contractor,category) VALUES (?,?,?,?,?)",
                                                    (_it['code'], int(_it['qty']), _wh_f, _cont, _it.get('cat','')))
                                                save_log("ارجاع — اعتماد فاتورة مقاول", _it['code'], _it['qty'],
                                                         f"فاتورة {_ar_invno} | اعتمدها: {u['full_name']} | أرفقها: {_ar_by}", u['full_name'])
                                        c.execute(
                                            "UPDATE signed_invoices SET status='معتمد', deducted=1, admin_notes=?, reviewed_by=?, reviewed_at=? WHERE id=?",
                                            (_appr_note.strip(), u['full_name'], _ts_rev, _ar_id))
                                        conn.commit()
                                        st.success(f"✅ تم اعتماد الفاتورة ({_ar_invno}) وتنفيذ الخصم بنجاح!")
                                        st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)

                                # ── إعادة للمقاول ──
                                with _btn2:
                                    if st.button("🔄 إعادة لأمين المستودع", key=f"appr_return_{_ar_id}", use_container_width=True):
                                        if not _appr_note.strip():
                                            st.error("❌ يجب كتابة ملاحظة توضح سبب الإعادة.")
                                        else:
                                            c.execute(
                                                "UPDATE signed_invoices SET status='مُعادة', deducted=0, admin_notes=?, reviewed_by=?, reviewed_at=? WHERE id=?",
                                                (_appr_note.strip(), u['full_name'], _ts_rev, _ar_id))
                                            conn.commit()
                                            st.warning(f"🔄 تم إعادة الفاتورة ({_ar_invno}) إلى أمين مستودع المقاول مع الملاحظة.")
                                            st.rerun()

                                # ── رفض ──
                                with _btn3:
                                    st.markdown("<div class='btn-danger'>", unsafe_allow_html=True)
                                    if st.button("❌ رفض الفاتورة", key=f"appr_no_{_ar_id}", use_container_width=True):
                                        if not _appr_note.strip():
                                            st.error("❌ يجب كتابة سبب الرفض في خانة الملاحظة.")
                                        else:
                                            c.execute(
                                                "UPDATE signed_invoices SET status='مرفوض', deducted=0, admin_notes=?, reviewed_by=?, reviewed_at=? WHERE id=?",
                                                (_appr_note.strip(), u['full_name'], _ts_rev, _ar_id))
                                            conn.commit()
                                            st.error(f"❌ تم رفض الفاتورة ({_ar_invno}).")
                                            st.rerun()
                                    st.markdown("</div>", unsafe_allow_html=True)

                            elif _ar_status in ("معتمد", "مرفوض", "مُعادة"):
                                # عرض القرار فقط
                                _dec_color = {"معتمد":"#1daa60","مرفوض":"#d32f2f","مُعادة":"#e65100"}.get(_ar_status,"#555")
                                st.markdown(f"""
                                <div style='background:#f5f5f5;border-right:4px solid {_dec_color};border-radius:8px;
                                    padding:10px 14px;direction:rtl;font-size:13px;'>
                                    📋 <b>القرار:</b> <span style='color:{_dec_color};font-weight:bold;'>{_ar_status}</span><br>
                                    👤 <b>بواسطة:</b> {_ar_rev_by} | 📅 {_ar_rev_at}
                                    {f"<br>💬 <b>الملاحظة:</b> {_ar_notes}" if _ar_notes.strip() else ""}
                                </div>""", unsafe_allow_html=True)

    # ---------------------------------------------------------
    # صفحة: إدارة صلاحيات المستودعات لأمين مستودع المقاول (من داخل manage_staff)
    # ---------------------------------------------------------

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
