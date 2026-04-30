import streamlit as st
import json
from datetime import date, datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- デザイン設定 ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .block-container { padding-top: 1.5rem !important; max-width: 1100px !important; margin: auto; padding-bottom: 5rem !important; }
    h1 { font-size: 24px !important; color: #0F172A; text-align: center; margin-bottom: 20px !important; font-weight: 800; border-bottom: 3px solid #1E3A8A; padding-bottom: 10px; }
    h2 { font-size: 16px !important; color: #FFFFFF !important; background-color: #1E3A8A !important; padding: 8px 15px !important; border-radius: 5px !important; margin-top: 20px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #E2E8F0; border-radius: 5px 5px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ヘルプ情報の詳細定義 ---
HELP_TRG = """
**TRG (Tumor Regression Grade) 分類詳細**
Voskuilen らが提唱する分類を用い、腫瘍床における線維化と生存腫瘍細胞の割合で評価する。

- **TRG 1：Complete Response**
組織学的に同定可能な生存がん細胞を認めない。腫瘍床は広範な線維化に置き換わっている。
- **TRG 2：Strong Response**
腫瘍床の線維化が優位であり、残存する生存がん細胞の占める割合が腫瘍床全体の50%未満である。
- **TRG 3：Weak and No Response**
残存する生存がん細胞が優位であり、その割合が腫瘍床全体の50%以上を占める、あるいは治療による変性・壊死性変化が認められない。
"""

HELP_CD = """
**Clavien-Dindo 分類詳細**
- **Grade I**: 正常な術後経過からの逸脱で、薬物療法、または外科・内視鏡・IVR治療を要さないもの。解熱鎮痛剤、利尿剤、電解質補充、理学療法、創感染の開放は含む。
- **Grade II**: 上記以外の薬物療法、輸血、中心静脈栄養を要する。
- **Grade III**: 外科・内視鏡・IVR治療を要する。
  - **Grade IIIa**: 全身麻酔を要さない治療
  - **Grade IIIb**: 全身麻酔下での治療
- **Grade IV**: IC/ICU管理を要する、生命を脅かす合併症。
  - **Grade IVa**: 単一臓器不全（透析を含む）
  - **Grade IVb**: 多臓器不全
- **Grade V**: 患者の死亡
"""

# --- メール送信関数 ---
def send_email(report_text):
    try:
        mail_user = st.secrets["email"]["user"]
        mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        
        msg = MIMEMultipart()
        msg['From'] = mail_user
        msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = "【JUOG CRFレポート】術後30日目報告"
        msg.attach(MIMEText(report_text, 'plain'))
        
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"メール送信失敗: {e}")
        return False

st.title("JUOG UTUC_Trial：術前・術中・術後30日目 CRF")

# --- メインフォーム ---
with st.container():
    patient_id = st.text_input("研究対象者識別コード*", help="事務局指定のIDを入力してください")

    tab_pre, tab_op, tab_path, tab_post = st.tabs(["📊 術前データ", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

    # --- タブ1: 術前データ ---
    with tab_pre:
        st.subheader("術前検査・所見")
        c1, c2 = st.columns(2)
        with c1:
            cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], horizontal=True)
            last_evp_date = st.date_input("最終EVP投与日", value=None)
        with c2:
            pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade", ["なし", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"])

        st.subheader("術前血液検査")
        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1:
            wbc = st.number_input("WBC (/μL)", value=0, step=1, format="%d")
            hb = st.number_input("Hb (g/dL)", value=0.0, format="%.1f")
            plt = st.number_input("PLT (x10^4/μL)", value=0, step=1, format="%d")
        with bc2:
            ast = st.number_input("AST (U/L)", value=0, step=1, format="%d")
            alt = st.number_input("ALT (U/L)", value=0, step=1, format="%d")
            ldh = st.number_input("LDH (U/L)", value=0, step=1, format="%d")
        with bc3:
            alb = st.number_input("Alb (g/dL)", value=0.0, format="%.1f")
            bun = st.number_input("BUN (mg/dL)", value=0, step=1, format="%d")
            cre = st.number_input("Cre (mg/dL)", value=0.0, format="%.2f")
        with bc4:
            egfr = st.number_input("eGFR (mL/min/1.73m²)", value=0.0, format="%.1f")
            crp = st.number_input("CRP (mg/dL)", value=0.0, format="%.2f")

    # --- タブ2: 手術記録 ---
    with tab_op:
        op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], horizontal=True)
        if op_performed == "実施した":
            c_op1, c_op2 = st.columns(2)
            with c_op1:
                op_date = st.date_input("手術実施日*", value=None)
                op_type = st.selectbox("術式*", ["根治的腎尿管全摘除術", "尿管部分切除術"])
            with c_op2:
                eau_grade = st.selectbox("術中合併症(EAUiaiC)*", 
                                       ["Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"],
                                       help="Voskuilenらの提唱する基準に基づき入力してください")
                op_time = st.number_input("手術時間 (分)", value=0, step=1, format="%d")

    # --- タブ3: 病理結果 ---
    with tab_path:
        st.subheader("病理診断")
        pa1, pa2 = st.columns(2)
        with pa1:
            ypt = st.selectbox("ypT分類*", ["ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4"])
            ypn = st.selectbox("ypN分類*", ["ypN0", "ypN1", "ypN2"])
        with pa2:
            trg = st.radio("病理学的治療効果（TRG分類）*", 
                          ["TRG 1： Complete Response", "TRG 2： Strong Response", "TRG 3： Weak and No Response"],
                          help=HELP_TRG)

    # --- タブ4: 30日目評価 ---
    with tab_post:
        st.subheader("術後30日目の評価")
        cd_grade = st.selectbox("術後合併症 (Clavien-Dindo分類)*", 
                               ["Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"],
                               help=HELP_CD)
        cd_detail = st.text_area("合併症の詳細内容")
        
        st.divider()
        adj_plan = st.selectbox("術後補助療法の予定*", ["経過観察", "EVP継続", "ペムブロ単剤", "ニボ単剤", "プラチナ製剤", "その他"])
        
        status_alive = st.radio("最終生存確認（術後30日時点）*", ["生存", "死亡"], horizontal=True)

# --- アクションエリア ---
st.divider()
col_btn1, col_btn2 = st.columns(2)

# データまとめ（送信・保存用）
input_data = {
    "ID": patient_id,
    "膀胱鏡": cysto_find,
    "最終EVP": str(last_evp_date),
    "WBC": wbc, "Hb": hb, "Cre": cre, "CRP": crp,
    "術式": op_performed,
    "TRG": trg,
    "CD分類": cd_grade,
    "生存状況": status_alive
}

with col_btn1:
    # 一時保存（JSONダウンロード）
    st.download_button("💾 下書きを自分のPCに保存", 
                       data=json.dumps(input_data, ensure_ascii=False, indent=2),
                       file_name=f"Draft_{patient_id}_{date.today()}.json",
                       mime="application/json")

with col_btn2:
    if st.button("🚀 CRFを確定して事務局へ送信", type="primary", use_container_width=True):
        if not patient_id:
            st.error("識別コードを入力してください")
        else:
            report_text = f"【JUOG CRFレポート】\nID: {patient_id}\n判定日: {date.today()}\n\n" + \
                          "\n".join([f"{k}: {v}" for k, v in input_data.items()])
            
            if send_email(report_text):
                st.success("事務局への送信が完了しました！")
                st.balloons()
