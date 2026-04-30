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
        font-size: 18px;
        margin-top: 25px;
        margin-bottom: 15px;
    }
    
    h1 { font-size: 28px !important; color: #0F172A; text-align: center; margin-bottom: 30px !important; font-weight: 800; }
    label { font-size: 14px !important; font-weight: 600 !important; color: #334155 !important; }
    
    /* タブのデザイン調整 */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #F1F5F9;
        border-radius: 5px 5px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    
    /* 入力枠のスタイル */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        background-color: #F8FAFC !important;
        border: 1px solid #E2E8F0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 変数初期化（NameError防止） ---
# 送信レポート作成時に、非表示項目が参照されてもエラーにならないよう初期化しておきます
vital_detail = "N/A"
bladder_tumor_tx = "N/A"
op_date = "N/A"
op_type = "N/A"
approach = "N/A"
op_completed = "N/A"
op_incomplete_detail = "N/A"
op_time = 0
bleeding = 0
eau_grade = "N/A"
ln_dissection = "N/A"
ln_range = []
p_histology = "N/A"
p_histology_other = "N/A"
p_subtype_type = "N/A"
p_morphology = "N/A"
p_size = 0.0
p_location = []
ypt = "N/A"
ypn = "N/A"
p_multiplicity = "N/A"
p_lvi = "N/A"
r0_status = "N/A"
trg_grade = "N/A"
no_op_reason = "N/A"

# --- ヘルプテキスト ---
HELP_EAUIAIC = "術中合併症の評価指標（EAUiaiC分類）。詳細はプロトコルまたは？マークを確認してください。"
HELP_TRG = "腫瘍床における線維化と生存腫瘍細胞の割合に基づく病理学的治療効果判定。"
HELP_CD = "術後30日以内の合併症分類。"

# --- メール送信関数 ---
def send_email(report_content, pid):
    try:
        mail_user = st.secrets["email"]["user"]
        mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        msg = MIMEMultipart()
        msg['From'] = mail_user
        msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = f"【JUOG CRF】術後30日報告（ID: {pid}）"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

st.title("JUOG UTUC_Trial：術後30日目評価CRF")

# --- メインフォーム ---
patient_id = st.text_input("研究対象者識別コード*")

tab1, tab2, tab3, tab4 = st.tabs(["📊 術前・登録時", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

# --- タブ1: 術前・登録時 ---
with tab1:
    st.markdown('<div class="juog-header">1. 術前EVP・身体所見</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        last_evp_date = st.date_input("最終EVP投与日", value=None)
        pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade*", 
                                   ["選択してください", "なし", "Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症", "Grade 4 生命を脅かす", "Grade 5 死亡"], index=0)
        ae_detail = st.text_input("CTCAE（詳細記載）")
    with c2:
        vital_abnormality = st.radio("術前身体所見およびバイタルサインの異常*", ["異常なし", "異常あり"], index=None, horizontal=True)
        if vital_abnormality == "異常あり":
            vital_detail = st.text_input("異常の詳細*")
        
        cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], index=None, horizontal=True)
        if cysto_find == "腫瘍あり":
            bladder_tumor_tx = st.text_area("膀胱腫瘍の治療法についての詳細*")

    st.markdown('<div class="juog-header">2. 術前血液検査（一か月以内）</div>', unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        wbc = st.number_input("WBC (/μL)*", value=None, format="%d")
        hb = st.number_input("Hb (g/dL)*", value=None, format="%.1f")
        plt = st.number_input("PLT (x10^4/μL)*", value=None, format="%d")
        ast = st.number_input("AST (U/L)*", value=None, format="%d")
        alt = st.number_input("ALT (U/L)*", value=None, format="%d")
    with bc2:
        ldh = st.number_input("LDH (U/L)*", value=None, format="%d")
        alb = st.number_input("Alb (g/dL)*", value=None, format="%.1f")
        bun = st.number_input("BUN (mg/dL)*", value=None, format="%d")
        cre = st.number_input("Cre (mg/dL)*", value=None, format="%.2f")
        crp = st.number_input("CRP (mg/dL)*", value=None, format="%.2f")

    st.markdown('<div class="juog-header">3. 白血球分画 (%)</div>', unsafe_allow_html=True)
    f1, f2, f3, f4, f5 = st.columns(5)
    neutro = f1.number_input("Neutro*", value=None, format="%.1f")
    lympho = f2.number_input("Lympho*", value=None, format="%.1f")
    mono = f3.number_input("Mono*", value=None, format="%.1f")
    eosino = f4.number_input("Eosino*", value=None, format="%.1f")
    baso = f5.number_input("Baso*", value=None, format="%.1f")

# --- タブ2: 手術記録 ---
with tab2:
    st.markdown('<div class="juog-header">4. 手術実施状況</div>', unsafe_allow_html=True)
    op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], index=None, horizontal=True)
    
    if op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            op_date = st.date_input("手術実施日*", value=None)
            op_type = st.selectbox("術式*", ["選択してください", "根治的腎尿管全摘除術", "尿管部分切除術"], index=0)
            approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], index=None, horizontal=True)
            op_completed = st.radio("予定手術が完遂できたか*", ["はい", "いいえ"], index=None, horizontal=True)
            if op_completed == "いいえ":
                op_incomplete_detail = st.text_area("完遂できなかった理由・詳細*")
            op_time = st.number_input("手術時間 (分)*", value=None, format="%d")
            bleeding = st.number_input("出血量 (mL)*", value=None, format="%d")
        with oc2:
            eau_grade = st.selectbox("術中合併症（EAUiaiC）*", 
                                   ["選択してください", "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"], 
                                   index=0, help=HELP_EAUIAIC)
            ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], index=None, horizontal=True)
            if ln_dissection == "実施した":
                ln_range = st.multiselect("リンパ節郭清範囲*", 
                                        ["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"])
    elif op_performed == "実施しなかった":
        no_op_reason = st.selectbox("実施しなかった理由*", ["選択してください", "病勢進行", "有害事象の発生", "同意撤回", "その他"], index=0)
        st.info("手術未実施のため、病理結果の入力は不要です。「30日目評価」タブへ進んでください。")

# --- タブ3: 病理結果 ---
with tab3:
    if op_performed == "実施した":
        st.markdown('<div class="juog-header">5. 術後病理診断</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            p_histology = st.selectbox("組織型*", 
                                      ["選択してください", "Urothelial carcinoma", "Squamous cell carcinoma", "Adenocarcinoma", "Other"], index=0)
            if p_histology == "Other":
                p_histology_other = st.text_input("組織型 詳細*")
            
            p_subtype_presence = st.radio("亜型の有無*", ["なし", "あり"], index=None, horizontal=True)
            if p_subtype_presence == "あり":
                p_subtype_type = st.multiselect("亜型の種類 (UC Variant)*", 
                                              ["Nest型", "Micropapillary型", "Plasmacytoid型", "Sarcomatoid変化", "Lymphoepithelioma-like型", "Clear cell型", "Lipid-rich型", "Trophoblastic分化", "Glandular分化", "Squamous分化"])
            
            p_morphology = st.text_input("形態（乳頭状、結節状など）")
            p_size = st.number_input("大きさ (最大径 mm)*", value=None, format="%.1f")
            
            p_location = st.multiselect("場所（複数選択可）*", 
                                       ["上腎杯", "中腎杯", "下腎杯", "腎盂", "UPJ", "上部尿管", "中部尿管", "下部尿管", "VUJ"])
            
        with pc2:
            ypt = st.selectbox("ypT分類*", ["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4"], index=0)
            ypn = st.selectbox("ypN分類*", ["選択してください", "ypN0", "ypN1", "ypN2"], index=0)
            p_multiplicity = st.radio("多発性*", ["単発", "多発"], index=None, horizontal=True)
            p_lvi = st.radio("LVI（脈管侵襲）の有無*", ["なし", "あり"], index=None, horizontal=True)
            r0_status = st.radio("R0切除 (断端陰性)*", ["陰性", "陽性"], index=None, horizontal=True)
            trg_grade = st.radio("病理学的治療効果（TRG分類）*", 
                               ["TRG 1： Complete Response", "TRG 2： Strong Response", "TRG 3： Weak and No Response"], 
                               index=None, help=HELP_TRG)
    else:
        st.write("手術未実施のため入力項目はありません。")

# --- タブ4: 30日目評価 ---
with tab4:
    st.markdown('<div class="juog-header">6. 術後30日目（フォローアップ）評価</div>', unsafe_allow_html=True)
    
    # 30日目アラート
    if op_performed == "実施した" and op_date:
        target_30day = op_date + timedelta(days=30)
        st.info(f"術後30日目目安: **{target_30day}**")
        if date.today() < target_30day:
            st.warning(f"【アラート】術後30日（{target_30day}）に達していません。")

    sc1, sc2 = st.columns(2)
    with sc1:
        if op_performed == "実施した":
            cd_grade = st.selectbox("術後合併症 (Clavien-Dindo分類)*", 
                                   ["選択してください", "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"], 
                                   index=0, help=HELP_CD)
            cd_detail = st.text_area("CD分類 詳細")
        else:
            st.write("手術未実施のため、合併症評価はスキップします。")
            cd_grade = "N/A"

    with sc2:
        adj_plan = st.selectbox("今後の治療（術後補助療法）予定*", 
                               ["選択してください", "経過観察", "EVP継続", "ペムブロ単剤", "ニボ単剤", "プラチナ製剤", "その他"], index=0)
        adj_date = st.date_input("次回フォロー/治療予定日*", value=None)
        status_alive = st.radio("生存状況（術後30日時点）*", ["生存", "死亡"], index=None, horizontal=True)

    # --- 送信セクション ---
    st.divider()
    
    # レポート作成（手術未実施でもエラーにならないよう初期化した値を使用）
    report_data = f"""【JUOG UTUC_Trial CRF Report】
ID: {patient_id}
膀胱鏡: {cysto_find} (詳細: {bladder_tumor_tx})
WBC: {wbc} / Hb: {hb} / AST: {ast} / ALT: {alt}
分画: Ne:{neutro}/Ly:{lympho}/Mo:{mono}/Eo:{eosino}/Ba:{baso}

手術実施: {op_performed}
理由(未実施時): {no_op_reason}
完遂: {op_completed} (詳細: {op_incomplete_detail})
術式: {op_type} / アプローチ: {approach} / 合併症(EAU): {eau_grade}

病理組織: {p_histology} ({p_histology_other}) / 亜型: {p_subtype_type}
場所: {p_location} / 大きさ: {p_size}mm / LVI: {p_lvi}
ypT: {ypt} / ypN: {ypn} / TRG: {trg_grade}

CD分類: {cd_grade}
補助療法: {adj_plan} / 予定日: {adj_date}
生存状況: {status_alive}
"""

    col_save, col_send = st.columns(2)
    with col_save:
        st.download_button("💾 下書きとしてPCに保存", data=report_data, file_name=f"Draft_{patient_id}.txt", use_container_width=True)

    with col_send:
        if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
            if not patient_id: 
                st.error("識別コードを入力してください")
            elif status_alive is None:
                st.error("生存状況を選択してください")
            else:
                if send_email(report_data, patient_id):
                    st.success("事務局への送信が完了しました！")
                    st.balloons()
                else: 
                    st.error("送信に失敗しました。Secretsの設定を確認してください。")
