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
- **TRG 1：Complete Response**: 組織学的に同定可能な生存がん細胞を認めない。腫瘍床は広範な線維化に置き換わっている。
- **TRG 2：Strong Response**: 腫瘍床の線維化が優位であり、残存する生存がん細胞の占める割合が腫瘍床全体の50%未満である。
- **TRG 3：Weak and No Response**: 残存する生存がん細胞が優位であり、その割合が腫瘍床全体の50%以上を占める、あるいは治療による変性・壊死性変化が認められない。
"""

HELP_CD = """
**Clavien-Dindo 分類 (術後30日以内)**
- **Grade I**: 薬物、外科、内視鏡、IVR治療を要さない。解熱鎮痛剤、利尿剤、電解質補充、理学療法、創感染の開放はGrade Iとする。
- **Grade II**: 上記以外の薬物療法、輸血、中心静脈栄養を要する。
- **Grade III**: 外科、内視鏡、IVR治療を要する。
  - **Grade IIIa**: 全身麻酔を要さない治療
  - **Grade IIIb**: 全身麻酔下での治療
- **Grade IV**: IC/ICU管理を要する、生命を脅かす合併症。
  - **Grade IVa**: 単一の臓器不全（透析を含む）
  - **Grade IVb**: 多臓器不全
- **Grade V**: 患者の死亡
"""

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

st.title("JUOG UTUC_Trial：登録・術中・術後30日目 CRF")

# --- メインフォーム ---
patient_id = st.text_input("研究対象者識別コード*", help="文字列__1行__0")

tab1, tab2, tab3, tab4 = st.tabs(["📊 術前・登録時", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

with tab1:
    st.subheader("術前EVP・身体所見")
    c1, c2 = st.columns(2)
    with c1:
        last_evp_date = st.date_input("最終EVP投与日", value=None)
        pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade", [
            "なし", "Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症または医学的に重大", "Grade 4 生命を脅かす", "Grade 5 AE による死亡"
        ])
        ae_detail = st.text_input("CTCAE（詳細記載）")
    with c2:
        vital_abnormality = st.radio("術前身体所見およびバイタルサインの異常", ["異常なし", "異常あり"], horizontal=True)
        vital_detail = st.text_input("異常の詳細（異常ありの場合）")
        cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], horizontal=True)

    st.subheader("術前血液検査")
    bc1, bc2 = st.columns(2)
    with bc1:
        wbc = st.number_input("WBC (/μL)", value=0, step=1, format="%d")
        hb = st.number_input("Hb (g/dL)", value=0.0, format="%.1f")
        plt = st.number_input("PLT (x10^4/μL)", value=0, step=1, format="%d")
        ast = st.number_input("AST (U/L)", value=0, step=1, format="%d")
        alt = st.number_input("ALT (U/L)", value=0, step=1, format="%d")
        ldh = st.number_input("LDH (U/L)", value=0, step=1, format="%d")
    with bc2:
        alb = st.number_input("Alb (g/dL)", value=0.0, format="%.1f")
        bun = st.number_input("BUN (mg/dL)", value=0, step=1, format="%d")
        cre = st.number_input("Cre (mg/dL)", value=0.0, format="%.2f")
        egfr = st.number_input("eGFR (mL/min/1.73m²)", value=0.0, format="%.1f")
        crp = st.number_input("CRP (mg/dL)", value=0.0, format="%.2f")

    with st.expander("白血球分画 (%)"):
        f1, f2 = st.columns(2)
        neutro = f1.number_input("Neutrophil (%)", value=0.0, format="%.1f")
        lympho = f2.number_input("Lymphocyte (%)", value=0.0, format="%.1f")
        mono = f1.number_input("Monocyte (%)", value=0.0, format="%.1f")
        eosino = f2.number_input("Eosinophil (%)", value=0.0, format="%.1f")
        baso = f1.number_input("Basophil (%)", value=0.0, format="%.1f")

with tab2:
    st.subheader("手術実施状況")
    op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], horizontal=True)
    if op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            op_date = st.date_input("手術実施日*", value=None)
            op_type = st.selectbox("術式*", ["根治的腎尿管全摘除術", "尿管部分切除術"])
            approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], horizontal=True)
            op_time = st.number_input("手術時間 (分)", value=0, step=1, format="%d")
        with oc2:
            bleeding = st.number_input("出血量 (mL)", value=0, step=1, format="%d")
            eau_grade = st.selectbox("術中合併症(EAUiaiC)*", [
                "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"
            ], help=HELP_EAUIAIC)
            ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], horizontal=True)
            if ln_dissection == "実施した":
                ln_range = st.multiselect("リンパ節郭清範囲", [
                    "腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"
                ])
                ln_other = st.text_input("郭清範囲 その他（詳細）")
    else:
        no_op_reason = st.selectbox("実施しなかった理由", ["病勢進行", "有害事象の発生", "同意撤回", "その他"])

with tab3:
    st.subheader("術後病理診断")
    pc1, pc2 = st.columns(2)
    with pc1:
        ypt = st.selectbox("ypT分類*", ["ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4"])
        ypn = st.selectbox("ypN分類*", ["ypN0", "ypN1", "ypN2"])
        r0_status = st.radio("R0切除 (断端陰性)*", ["陰性", "陽性"], horizontal=True)
    with pc2:
        trg_grade = st.radio("病理学的治療効果（TRG分類）*", [
            "TRG 1： Complete Response", "TRG 2： Strong Response", "TRG 3： Weak and No Response"
        ], help=HELP_TRG)

with tab4:
    st.subheader("術後30日目評価")
    sc1, sc2 = st.columns(2)
    with sc1:
        cd_grade = st.selectbox("術後合併症 (Clavien-Dindo分類)*", [
            "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"
        ], help=HELP_CD)
        cd_detail = st.text_area("CD分類 詳細（事象名、処置内容など）")
    with sc2:
        adj_plan = st.selectbox("術後補助療法の予定*", [
            "経過観察", "EVP継続投与", "ペムブロリズマブ単剤維持療法", "ニボルマブ単剤療法", "プラチナ製剤併用化学療法", "その他"
        ])
        adj_date = st.date_input("予定（または開始）日", value=None)
        st.divider()
        status_alive = st.radio("生存状況（術後30日時点）*", ["生存", "死亡"], horizontal=True)
        if status_alive == "死亡":
            death_date = st.date_input("死亡日*", value=None)

# --- 保存・送信セクション ---
st.divider()
col_save, col_send = st.columns(2)

# レポート内容の完全構築
report_data = f"""【JUOG UTUC_Trial CRF Report】
研究対象者ID: {patient_id}
最終生存確認: {status_alive} {"(死亡日: "+str(death_date)+")" if status_alive=="死亡" else ""}

1. 術前・登録時
最終EVP投与日: {last_evp_date}
術前AE Grade: {pre_ae_grade} ({ae_detail})
身体所見異常: {vital_abnormality} ({vital_detail})
膀胱鏡所見: {cysto_find}
WBC: {wbc}, Hb: {hb}, PLT: {plt}, AST: {ast}, ALT: {alt}, LDH: {ldh}
Alb: {alb}, BUN: {bun}, Cre: {cre}, eGFR: {egfr}, CRP: {crp}
分画: Neutro {neutro}%, Lympho {lympho}%, Mono {mono}%, Eosino {eosino}%, Baso {baso}%

2. 手術記録
実施状況: {op_performed}
術日: {op_date if op_performed=="実施した" else "N/A"}
術式: {op_type if op_performed=="実施した" else "N/A"} / アプローチ: {approach if op_performed=="実施した" else "N/A"}
時間: {op_time}分 / 出血: {bleeding}mL / EAUiaiC: {eau_grade if op_performed=="実施した" else "N/A"}
郭清: {ln_dissection} (範囲: {", ".join(ln_range) if op_performed=="実施した" and ln_dissection=="実施した" else "N/A"})

3. 病理結果
ypT: {ypt}, ypN: {ypn}, R0切除: {r0_status}
TRG分類: {trg_grade}

4. 30日目評価
CD分類: {cd_grade} / 詳細: {cd_detail}
補助療法予定: {adj_plan} / 予定日: {adj_date}
"""

with col_save:
    st.download_button("💾 下書きとしてPCに保存", data=report_data, file_name=f"Draft_{patient_id}.txt", use_container_width=True)

with col_send:
    if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
        if not patient_id: 
            st.error("IDを入力してください")
        else:
            if send_email(report_data, patient_id):
                st.success("事務局（urosec, yoshida.tks）への送信が完了しました！")
                st.balloons()
            else: 
                st.error("送信に失敗しました。GitHubのSecrets設定を確認してください。")
