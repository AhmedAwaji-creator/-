import streamlit as st
import os

st.set_page_config(
    page_title="نظام إدارة مستودعات الطوارئ",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# إخفاء عناصر Streamlit الافتراضية
st.markdown("""
<style>
#MainMenu, header, footer, .stDeployButton {display:none!important}
.block-container {padding:0!important;max-width:100%!important}
iframe {border:none!important}
</style>
""", unsafe_allow_html=True)

# قراءة ملف النظام
html_file = os.path.join(os.path.dirname(__file__), "index.html")
with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()

# عرض النظام كاملاً
st.components.v1.html(html_content, height=900, scrolling=True)
