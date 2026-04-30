import streamlit as st
import json
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- ページ設定 ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF", layout="wide")

# --- JUOG専用デザインCSS (スタイリッシュなタブへ変更) ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .block-container { padding-top: 2rem !important; max-width: 1000px !important; margin: auto; }
    
    /* セクションヘッダー */
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
    
    /* スタイリッシュなタブデザイン（青背景を廃止し、下線方式へ） */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        border-bottom: 1px solid #E2E8F0;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        color: #64748B !important;
        padding: 10px 4px !important;
        font-weight: 600 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #1E3A8A !important;
        border-bottom: 3px solid #1E3A8A !important;
    }

    /* 入力項目の標準化 */
    .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextInput input, .stTextArea textarea {
        background-color: transparent !important;
        border: 1px solid #E2E8F0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ヘルプテキスト定義（箇条書き化） ---[cite: 3, 4]
HELP_EAUIAIC = """
- **Grade 0**: 逸脱なし。
- **Grade 1**: 追加処置あり。後遺症なし。（止血処置など）
- **Grade 2**: 主要な追加処置あり。後遺症の可能性あり。
- **Grade 3**: 生命を脅かす事態だが臓器摘出不要。
- **Grade 4**: 臓器の一部または全摘出(4A)、または完遂不能(4B)。
- **Grade 5**: 部位・患者間違い(5A)、または術中死亡(5B)。
"""

HELP_TRG = """
- **TRG 1**: 生存がん細胞を認めない。
- **TRG 2**: 線維化優位。生存がん細胞が50%未満。
- **TRG 3**: 生存がん細胞が50%以上、または変化なし。
"""

HELP_CD = """
- **Grade I**: 薬剤、手術、介入不要（解熱剤、利尿剤などは含む）。
- **Grade II**: 輸血、中心静脈栄養、特定の薬物療法が必要。
- **Grade III**: 外科、内視鏡、IVR治療が必要（IIIa: 全麻なし、IIIb: 全麻下）。
- **Grade IV**: ICU管理を要する生命を脅かす合併症。
- **Grade V**: 患者の死亡。
"""

# --- 変数初期化 ---
if 'init_done' not in st.session_state:
    st.session_state['init_done'] = True
    defaults = {
        "vital_detail": "N/A", "bladder_tumor_tx": "N/A", "op_date": None, "op_type": "未選択",
        "approach": "未選択", "op_completed": "未選択", "op_incomplete_detail": "N/A",
        "op_time": 0, "bleeding": 0, "eau_grade": "未選択", "ln_dissection": "未選択",
        "ln_range": [], "p_histology": "未選択", "p_histology_other": "N/A",
        "p_subtype_presence": "未選択", "p_subtype_type": [], "p_morphology": "未選択",
        "p_size": 0.0, "p_location": [], "ypt": "未選択", "ypn": "未選択", "ypn_pos_sites": [],
        "p_multiplicity": "未選択", "p_lvi": "未選択", "r0_status": "未選択",
        "trg_grade": "未選択", "no_op_reason": "未選択", "cd_grade": "未選択", "cd_detail": ""
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def send_email(report_content, pid):
    try:
        mail_user = st.secrets["email"]["user"]; mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        msg = MIMEMultipart(); msg['From'] = mail_user; msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = f"【JUOG CRF】周術期報告（ID: {pid}）"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass); server.send_message(msg); server.quit()
        return True
    except: return False

st.title("JUOG UTUC_Conlidative 周術期CRF")

patient_id = st.text_input("研究対象者識別コード*")

tab1, tab2, tab3, tab4 = st.tabs(["📊 術前・登録時", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

with tab1:
    st.markdown('<div class="juog-header">1. 術前EVP・身体所見</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        last_evp_date = st.date_input("最終EVP投与日", value=None)
        pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade*", ["選択してください", "なし", "Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症", "Grade 4 生命を脅かす", "Grade 5 死亡"], index=0)
        st.caption("[CTCAE v6.0 公式リファレンス（外部リンク）](https://ctep.cancer.gov/protocoldevelopment/electronic_applications/ctc.htm#ctc_60)")
        ae_detail = st.text_input("CTCAE（詳細記載）")
    with c2:
        vital_abnormality = st.radio("術前身体所見およびバイタルサインの異常*", ["異常なし", "異常あり"], index=None, horizontal=True)
        if vital_abnormality == "異常あり":
            st.session_state.vital_detail = st.text_input("異常の詳細*")
        
        cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], index=None, horizontal=True)
        if cysto_find == "腫瘍あり":
            st.session_state.bladder_tumor_tx = st.text_area("膀胱腫瘍の治療法についての詳細*")

    st.markdown('<div class="juog-header">2. 術前血液検査（一か月以内）</div>', unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        wbc = st.number_input("WBC (/μL)*", value=0, step=1)
        hb = st.number_input("Hb (g/dL)*", value=0.0, step=0.1)
        plt = st.number_input("PLT (x10^4/μL)*", value=0, step=1)
        ast = st.number_input("AST (U/L)*", value=0, step=1)
        alt = st.number_input("ALT (U/L)*", value=0, step=1)
    with bc2:
        ldh = st.number_input("LDH (U/L)*", value=0, step=1)
        alb = st.number_input("Alb (g/dL)*", value=0.0, step=0.1)
        bun = st.number_input("BUN (mg/dL)*", value=0, step=1)
        cre = st.number_input("Cre (mg/dL)*", value=0.00, step=0.01)
        crp = st.number_input("CRP (mg/dL)*", value=0.00, step=0.01)

    st.subheader("白血球分画 (%)")
    f1, f2, f3, f4, f5 = st.columns(5)
    neutro = f1.number_input("Neutro*", value=0.0, step=0.1)
    lympho = f2.number_input("Lympho*", value=0.0, step=0.1)
    mono = f3.number_input("Mono*", value=0.0, step=0.1)
    eosino = f4.number_input("Eosino*", value=0.0, step=0.1)
    baso = f5.number_input("Baso*", value=0.0, step=0.1)

with tab2:
    st.markdown('<div class="juog-header">4. 手術実施状況</div>', unsafe_allow_html=True)
    op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], index=None, horizontal=True)
    
    if op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            st.session_state.op_date = st.date_input("手術実施日*", value=None)
            st.session_state.op_type = st.selectbox("術式*", ["選択してください", "根治的腎尿管全摘除術", "尿管部分切除術"], index=0)
            st.session_state.approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], index=None, horizontal=True)
            st.session_state.op_completed = st.radio("予定手術が完遂できたか*", ["はい", "いいえ"], index=None, horizontal=True)
            if st.session_state.op_completed == "いいえ":
                st.session_state.op_incomplete_detail = st.text_area("完遂できなかった理由・詳細*")
            st.session_state.op_time = st.number_input("手術時間 (分)*", value=0, step=1)
            st.session_state.bleeding = st.number_input("出血量 (mL)*", value=0, step=1)
        with oc2:
            st.session_state.eau_grade = st.selectbox("術中合併症（EAUiaiC）*", ["選択してください", "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"], index=0, help=HELP_EAUIAIC)
            st.session_state.ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], index=None, horizontal=True)
            if st.session_state.ln_dissection == "実施した":
                st.session_state.ln_range = st.multiselect("リンパ節郭清範囲*", ["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"])
    elif op_performed == "実施しなかった":
        st.session_state.no_op_reason = st.selectbox("実施しなかった理由*", ["選択してください", "病勢進行", "有害事象の発生", "同意撤回", "その他"], index=0)

with tab3:
    if op_performed == "実施した":
        st.markdown('<div class="juog-header">5. 術後病理診断</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            st.session_state.p_histology = st.selectbox("組織型*", ["選択してください", "Urothelial carcinoma", "Squamous cell carcinoma", "Adenocarcinoma", "Other"], index=0)
            if st.session_state.p_histology == "Other":
                st.session_state.p_histology_other = st.text_input("組織型 詳細*")
            p_sub_presence = st.radio("亜型の有無*", ["なし", "あり"], index=None, horizontal=True)
            if p_sub_presence == "あり":
                st.session_state.p_subtype_type = st.multiselect("亜型の種類*", ["Nest型", "Micropapillary型", "Plasmacytoid型", "Sarcomatoid変化", "Lymphoepithelioma-like型", "Clear cell型", "Lipid-rich型", "Trophoblastic分化", "Glandular分化", "Squamous分化"])
            
            # 腫瘍形態の選択肢化
            st.session_state.p_morphology = st.selectbox("形態*", ["選択してください", "乳頭状(Papillary)", "非乳頭状(Non-papillary)", "結節状(Nodular)", "浸潤状(Infiltrative)", "平坦状(Flat)", "その他"], index=0)
            
            st.session_state.p_size = st.number_input("大きさ (最大径 mm)*", value=0.0, step=0.1)
            st.session_state.p_location = st.multiselect("場所*", ["上腎杯", "中腎杯", "下腎杯", "腎盂", "UPJ", "上部尿管", "中部尿管", "下部尿管", "VUJ"])
        with pc2:
            st.session_state.ypt = st.selectbox("ypT分類*", ["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4"], index=0)
            
            # ypN陽性部位のロジック
            st.session_state.ypn = st.selectbox("ypN分類*", ["選択してください", "ypN0", "ypN1", "ypN2"], index=0)
            if st.session_state.ypn != "ypN0" and st.session_state.ypn != "選択してください":
                st.session_state.ypn_pos_sites = st.multiselect("陽性部位（リンパ節郭清部位より選択）*", options=["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"])
            
            st.session_state.p_multiplicity = st.radio("多発性*", ["単発", "多発"], index=None, horizontal=True)
            st.session_state.p_lvi = st.radio("LVI（脈管侵襲）*", ["なし", "あり"], index=None, horizontal=True)
            st.session_state.r0_status = st.radio("R0切除*", ["陰性", "陽性"], index=None, horizontal=True)
            st.session_state.trg_grade = st.radio("病理学的治療効果（TRG分類）*", ["TRG 1： Complete Response", "TRG 2： Strong Response", "TRG 3： Weak and No Response"], index=None, help=HELP_TRG)
    else:
        st.write("手術未実施のため、入力項目はありません。")

with tab4:
    st.markdown('<div class="juog-header">6. 術後30日目（フォローアップ）評価</div>', unsafe_allow_html=True)
    if op_performed == "実施した" and st.session_state.op_date:
        t30 = st.session_state.op_date + timedelta(days=30)
        st.info(f"術後30日目目安: {t30}"); (st.warning(f"まだ30日に達していません。") if date.today() < t30 else None)
    sc1, sc2 = st.columns(2)
    with sc1:
        if op_performed == "実施した":
            st.session_state.cd_grade = st.selectbox("術後合併症 (Clavien-Dindo分類)*", ["選択してください", "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"], index=0, help=HELP_CD)
            st.session_state.cd_detail = st.text_area("CD分類 詳細")
        else: st.session_state.cd_grade = "N/A"
    with sc2:
        adj_plan = st.selectbox("今後の治療予定*", ["選択してください", "経過観察", "EVP継続", "ペムブロ単剤", "ニボ単剤", "プラチナ製剤", "その他"], index=0)
        adj_date = st.date_input("次回フォロー予定日*", value=None)
        st.session_state.status_alive = st.radio("生存状況（術後30日時点）*", ["生存", "死亡"], index=None, horizontal=True)

    st.divider()
    if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
        if not patient_id: st.error("IDを入力してください")
        elif st.session_state.status_alive is None: st.error("生存状況を選択してください")
        else:
            rep = f"ID: {patient_id}\n生存: {st.session_state.status_alive}\n手術: {op_performed}\nCD分類: {st.session_state.cd_grade}\nypN: {st.session_state.ypn} (陽性部位: {st.session_state.ypn_pos_sites})\nTRG: {st.session_state.trg_grade}"
            if send_email(rep, patient_id): st.success("送信完了しました！"); st.balloons()
            else: st.error("送信失敗しました。")
