import streamlit as st
import json
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- ページ設定 ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF", layout="wide")

# --- JUOG専用デザインCSS ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .block-container { padding-top: 2rem !important; max-width: 1000px !important; margin: auto; }
    
    /* 登録用CRF風ヘッダーバー */
    .juog-header {
        background-color: #1E3A8A;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    
    h1 { font-size: 26px !important; color: #0F172A; text-align: center; margin-bottom: 30px !important; font-weight: 800; }
    label { font-size: 14px !important; font-weight: 600 !important; color: #334155 !important; }
    
    /* 余計な背景や枠を排除し、標準的な表示に統一 */
    .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextInput input, .stTextArea textarea {
        background-color: transparent !important;
        border-radius: 4px !important;
    }

    /* タブのデザイン */
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 変数初期化 (NameError防止) ---
if 'init_done' not in st.session_state:
    st.session_state['init_done'] = True
    defaults = {
        "vital_detail": "N/A", "bladder_tumor_tx": "N/A", "op_date": None, "op_type": "未選択",
        "approach": "未選択", "op_completed": "未選択", "op_incomplete_detail": "N/A",
        "op_time": 0, "bleeding": 0, "eau_grade": "未選択", "ln_dissection": "未選択",
        "ln_range": [], "p_histology": "未選択", "p_histology_other": "N/A",
        "p_subtype_presence": "未選択", "p_subtype_type": [], "p_morphology": "",
        "p_size": 0.0, "p_location": [], "ypt": "未選択", "ypn": "未選択",
        "p_multiplicity": "未選択", "p_lvi": "未選択", "r0_status": "未選択",
        "trg_grade": "未選択", "no_op_reason": "未選択", "cd_grade": "未選択", "cd_detail": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

# --- ヘルプテキスト定義 ---
HELP_EAUIAIC = """Grade 0： 介入や手術アプローチの変更を要さず、予定された手術手順からの逸脱がないもの。
Grade 1： 追加・代替処置を要するが生命を脅かさず後遺症を残さない。
Grade 2： 主要な追加処置を要するが直ちに生命を脅かさない。後遺症の可能性あり。
Grade 3： 主要な追加処置を要し直ちに生命を脅かすが臓器摘出不要。
Grade 4A： 臓器の一部または全摘出。
Grade 4B： 完遂不能または予定外ストーマ造設。
Grade 5A： 部位・側・患者間違い。
Grade 5B： 術中死亡。"""

HELP_TRG = """TRG 1： 生存がん細胞を認めない。腫瘍床は広範な線維化に置換。
TRG 2： 線維化が優位。生存がん細胞が腫瘍床全体の50%未満。
TRG 3： 生存がん細胞が優位（50%以上）、または治療による変性・壊死性変化が認められない。"""

HELP_CD = """Grade I: 薬物、外科、内視鏡、IVR治療を要さない（解熱剤、利尿剤などはGrade I）。
Grade II: 上記以外の薬物療法、輸血、中心静脈栄養を要する。
Grade III: 外科、内視鏡、IVR治療を要する（IIIa: 全麻なし、IIIb: 全麻下）。
Grade IV: IC/ICU管理を要する生命を脅かす合併症。
Grade V: 患者の死亡"""

def send_email(report_content, pid):
    try:
        mail_user = st.secrets["email"]["user"]; mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        msg = MIMEMultipart(); msg['From'] = mail_user; msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = f"【JUOG CRF】術後30日報告（ID: {pid}）"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass); server.send_message(msg); server.quit()
        return True
    except: return False

st.title("JUOG UTUC_Conlidative 登録用CRF")

patient_id = st.text_input("研究対象者識別コード*")

tab1, tab2,
