import streamlit as st
import json
from datetime import date, datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- ページ設定 ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF", layout="wide")

# --- CSSデザイン ---
st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .block-container { padding-top: 1.5rem !important; max-width: 1100px !important; margin: auto; padding-bottom: 5rem !important; }
    h1 { font-size: 24px !important; color: #0F172A; text-align: center; margin-bottom: 20px !important; font-weight: 800; border-bottom: 3px solid #1E3A8A; padding-bottom: 10px; }
    h2 { font-size: 16px !important; color: #FFFFFF !important; background-color: #1E3A8A !important; padding: 8px 15px !important; border-radius: 5px !important; margin-top: 20px !important; margin-bottom: 15px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #E2E8F0; border-radius: 5px 5px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    label { font-weight: 600 !important; color: #334155 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ヘルプテキスト定義 ---
HELP_EAUIAIC = """
**術中合併症(EAUiaiC) 定義**
- **Grade 0**: 逸脱なし。
- **Grade 1**: 追加・代替処置を要するが、生命を脅かさず後遺症なし。
- **Grade 2**: 主要な追加処置を要する。後遺症の可能性あり。
- **Grade 3**: 生命を脅かす事態だが臓器摘出は不要。
- **Grade 4A**: 臓器の一部または全摘出を要する。
- **Grade 4B**: 完遂不能または予定外ストーマ造設。
- **Grade 5A**: 部位・側・患者間違い。
- **Grade 5B**: 術中死亡。
"""

HELP_TRG = """
**TRG (Tumor Regression Grade) 分類**
Voskuilen らの提唱する分類（線維化と残存生存腫瘍細胞の割合）。
- **TRG 1：Complete Response**: 生存がん細胞を認めない。腫瘍床は広範な線維化に置換。
- **TRG 2：Strong Response**: 線維化が優位。生存がん細胞が腫瘍床全体の50%未満。
- **TRG 3：Weak and No Response**: 生存がん細胞が優位（50%以上）、または変性・壊死性変化が認められない。
"""

HELP_CD = """
**Clavien-Dindo 分類 (術後30日以内)**
- **Grade I**: 薬物、外科、内視鏡、IVR治療を要さない。解熱鎮痛剤、利尿剤、電解質補充、理学療法、創感染の開放はGrade Iとする。
- **Grade II**: 上記以外の薬物療法、輸血、中心静脈栄養を要する。
- **Grade III**: 外科、内視鏡、IVR治療を要する。
  - **Grade IIIa**: 全身麻酔を要さない
  - **Grade IIIb**: 全身麻酔下
- **Grade IV**: IC/ICU管理を要する生命を脅かす合併症。
  - **Grade IVa**: 単一臓器不全
  - **Grade IVb**: 多臓器不全
- **Grade V**: 患者の死亡
"""

# --- メール送信関数 ---
def send_email(report_content):
    try:
        mail_user = st.secrets["email"]["user"]
        mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        msg = MIMEMultipart()
        msg['From'] = mail_user
        msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = f"【JUOG CRF】術後30日報告（ID: {patient_id}）"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass)
        server.send_message(msg)
        server.quit()
        return True
    except:
