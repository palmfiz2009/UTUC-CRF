import streamlit as st
import json
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- ページ設定 ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF", layout="wide")

# --- JUOG専用デザインCSS (変更なし) ---
st.markdown("""
    <style>
    header[data-testid="stHeader"] { visibility: hidden; }
    .block-container { 
        max-width: 1100px !important; 
        padding-top: 1.5rem !important; 
        padding-bottom: 5rem !important; 
        margin: auto !important;
    }
    h1 { 
        font-size: 26px !important; 
        color: #0F172A; 
        text-align: center; 
        margin-top: 0px !important; 
        margin-bottom: 30px !important; 
        font-weight: 800; 
        height: 40px;
    }
    .top-info-bar {
        background-color: transparent !important;
        padding: 0px !important;
        margin-bottom: 25px !important;
        border: none !important;
        min-height: 80px;
    }
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
    label { font-weight: 600 !important; color: #334155 !important; }
    div[data-baseweb="select"] ul { white-space: normal !important; }
    div[role="option"] { line-height: 1.4 !important; padding: 8px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; border-bottom: 1px solid #E2E8F0; }
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
    .stSelectbox div[data-baseweb="select"], .stNumberInput input, .stTextInput input, .stTextArea textarea {
        background-color: transparent !important;
        border: 1px solid #E2E8F0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 施設リスト ---
FACILITY_LIST = [
    "選択してください", "愛知県がんセンター", "秋田大学", "愛媛大学", "大分大学", "大阪公立大学", 
    "大阪大学", "大阪府済生会野江病院", "岡山大学", "香川大学", "鹿児島大学", "関西医科大学", 
    "岐阜大学", "九州大学病院", "京都大学", "久留米大学", "神戸大学", "国立がん研究センター中央病院", 
    "国立病院機構四国がんセンター", "札幌医科大学", "千葉大学", "筑波大学", "東京科学大学", 
    "東京慈恵会医科大学", "東京慈恵会医科大学附属柏病院", "東北大学", "鳥取大学", "富山大学", 
    "長崎大学病院", "名古屋大学", "奈良県立医科大学", "新潟大学大学院 医歯学総合研究科", 
    "浜松医科大学", "原三信病院", "兵庫医科大学", "弘前大学", "北海道大学", "三重大学", 
    "横浜市立大学", "琉球大学", "和歌山県立医科大学", "その他"
]

# --- ヘルプテキスト定義 ---
HELP_EAUIAIC = """
**術中合併症（EAUiaiC）詳細定義**
- **Grade 0**： 介入や手術アプローチの変更を要さず、予定された手術手順からの逸脱がないもの。患者への影響がないもの。
- **Grade 1**： 予定された手術手順において追加・代替処置を要するが、生命を脅かさず、臓器の一部または全摘出を伴わないもの。事象は制御下に置かれ、長期的な副作用、後遺症を残さない。
- **Grade 2**： 手術アプローチにおいて主要な追加・代替処置を要するが、直ちに生命を脅かすものではないもの。
- **Grade 3**： 予定された手術手順に加え主要な追加・代替処置を要し、かつ事象が直ちに生命を脅かすものであるが、臓器の一部または全摘出は要さないもの。
- **Grade 4**： 直ちに生命を脅かす事態となり、患者に短期または長期的な重大な結果をもたらすもの。4A: 臓器摘出、4B: 手術完了不能。
- **Grade 5**： 5A: 部位間違い等、5B: 術中死亡。
"""

HELP_TRG = """
**TRG (Tumor Regression Grade) 分類**
Voskuilen らの提唱する分類。
- **TRG 1：Complete Response**: 生存がん細胞を認めない。腫瘍床は広範な線維化に置換。
- **TRG 2：Strong Response**: 線維化が優位。生存がん細胞が全体の50%未満。
- **TRG 3：Weak and No Response**: 生存がん細胞が優位（50%以上）、または変化なし。
"""

# 指示箇所：詳細な定義への書き換え
HELP_CD = """
**Clavien-Dindo 分類 (術後30日以内)**
Gradingの原則：

- **Grade I**：正常な術後経過からの逸脱で、薬物療法、または外科的治療、内視鏡的治療、IVR 治療を要さないもの。
ただし、制吐剤、解熱剤、鎮痛剤、利尿剤による治療、電解質補充、理学療法は必要とする治療には含めない。また、ベッドサイドでの創感染の開放は Grade I とする。

- **Grade II**：制吐剤、解熱剤、鎮痛剤、利尿剤以外の薬物療法を要する。輸血および中心静脈栄養を要する場合を含む。

- **Grade III**：外科的治療、内視鏡的治療、IVR 治療を要する。
    - **Grade IIIa**：全身麻酔を要さない治療
    - **Grade IIIb**：全身麻酔下での治療

- **Grade IV**：ICU 管理を要する、生命を脅かす合併症（中枢神経系の合併症を含む）
    - **Grade IVa**：単一の臓器不全（透析を含む）
    - **Grade IVb**：多臓器不全

- **Grade V**：患者の死亡
"""

# --- セッション状態初期化 ---
if 'init_done' not in st.session_state:
    st.session_state['init_done'] = True
    defaults = {
        "facility_name": "選択してください", "patient_id": "",
        "vital_detail": "N/A", "bladder_tumor_tx": "N/A", "op_performed": None,
        "op_date": None, "op_admission_date": None, "op_discharge_date": None,
        "op_type": "未選択", "approach": "未選択", "op_completed": "未選択", "op_incomplete_detail": "N/A",
        "op_time": None, "bleeding": None, "eau_grade": "未選択", "eau_detail": "N/A", "ln_dissection": "未選択",
        "ln_range": [], "p_histology": "未選択", "p_histology_other": "N/A",
        "p_subtype_presence": "未選択", "p_subtype_type": [], "p_morphology": "未選択",
        "p_size": None, "p_location": [], "ypt": "未選択", "ypn": "未選択", "ypn_pos_sites": [],
        "p_multiplicity": "未選択", "p_lvi": "未選択", "r0_status": "未選択", "p_eval_failed_reason": "",
        "trg_grade": None, "no_op_reason": "選択してください", "no_op_reason_other": "", "cd_grade": "未選択", "cd_detail": "N/A",
        "adj_plan": "選択してください", "adj_other_detail": "", "status_alive": None,
        "needs_confirm": False, "do_send": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def send_email(report_content, pid, facility):
    try:
        mail_user = st.secrets["email"]["user"]; mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        msg = MIMEMultipart(); msg['From'] = mail_user; msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = f"【JUOG CRF】周術期報告（{facility} / ID: {pid}）"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass); server.send_message(msg); server.quit()
        return True
    except: return False

st.title("JUOG UTUC_Conlidative 周術期CRF")

# --- 共通ヘッダー ---
st.markdown('<div class="top-info-bar">', unsafe_allow_html=True)
col_h1, col_h2 = st.columns(2)
with col_h1:
    idx_fac = FACILITY_LIST.index(st.session_state.facility_name) if st.session_state.facility_name in FACILITY_LIST else 0
    st.session_state.facility_name = st.selectbox("施設名*", FACILITY_LIST, index=idx_fac)
with col_h2:
    st.session_state.patient_id = st.text_input("研究対象者識別コード*", value=st.session_state.patient_id)
st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 術前・登録時", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

with tab1:
    st.markdown('<div class="juog-header">1. 術前EVP・身体所見</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.date_input("最終EVP投与日", value=None)
        pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade*", ["選択してください", "なし", "Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症", "Grade 4 生命を脅かす", "Grade 5 死亡"], index=0)
        st.caption("[JCOG版 CTCAE v6.0 日本語訳（外部リンク）](https://jcog.jp/assets/CTCAEv6J_20260301_v28_0.pdf)")
        ae_detail = st.text_input("CTCAE（詳細記載）") if pre_ae_grade not in ["選択してください", "なし"] else "なし"
    with c2:
        vital_abnormality = st.radio("術前身体所見およびバイタルサインの異常*", ["異常なし", "異常あり"], index=None, horizontal=True)
        if vital_abnormality == "異常あり": st.session_state.vital_detail = st.text_input("異常の詳細*")
        cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], index=None, horizontal=True)
        if cysto_find == "腫瘍あり": st.session_state.bladder_tumor_tx = st.text_area("膀胱腫瘍の治療法についての詳細*")

    st.markdown('<div class="juog-header">2. 術前血液検査（一か月以内）</div>', unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        # 指示箇所：デフォルト値を None に設定
        wbc = st.number_input("WBC (/μL)*", value=None, step=1)
        hb = st.number_input("Hb (g/dL)*", value=None, step=0.1)
        plt = st.number_input("PLT (x10^4/μL)*", value=None, step=1)
        ast = st.number_input("AST (U/L)*", value=None, step=1)
        alt = st.number_input("ALT (U/L)*", value=None, step=1)
    with bc2:
        ldh = st.number_input("LDH (U/L)*", value=None, step=1)
        alb = st.number_input("Alb (g/dL)*", value=None, step=0.1)
        cre = st.number_input("Cre (mg/dL)*", value=None, step=0.01)
        egfr = st.number_input("eGFR (mL/min/1.73m²)*", value=None, step=0.1)
        crp = st.number_input("CRP (mg/dL)*", value=None, step=0.01)

    st.subheader("白血球分画 (%)")
    f1, f2, f3, f4, f5 = st.columns(5)
    neutro = f1.number_input("Neutro*", value=None, step=0.1)
    lympho = f2.number_input("Lympho*", value=None, step=0.1)
    mono = f3.number_input("Mono*", value=None, step=0.1)
    eosino = f4.number_input("Eosino*", value=None, step=0.1)
    baso = f5.number_input("Baso*", value=None, step=0.1)

with tab2:
    st.markdown('<div class="juog-header">4. 手術実施状況</div>', unsafe_allow_html=True)
    st.session_state.op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], index=(["実施した", "実施しなかった"].index(st.session_state.op_performed) if st.session_state.op_performed else None), horizontal=True)
    if st.session_state.op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            st.session_state.op_admission_date = st.date_input("入院日*", value=st.session_state.op_admission_date)
            st.session_state.op_date = st.date_input("手術実施日*", value=st.session_state.op_date)
            st.session_state.op_discharge_date = st.date_input("退院日（または退院予定日）", value=st.session_state.op_discharge_date)
            st.session_state.op_type = st.selectbox("術式*", ["選択してください", "根治的腎尿管全摘除術", "尿管部分切除術"], index=0)
            st.session_state.approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], index=None, horizontal=True)
            st.session_state.op_completed = st.radio("予定手術が完遂できたか*", ["はい", "いいえ"], index=None, horizontal=True)
            if st.session_state.op_completed == "いいえ": st.session_state.op_incomplete_detail = st.text_area("完遂できなかった理由*")
            st.session_state.op_time = st.number_input("手術時間 (分)*", value=None, step=1)
            st.session_state.bleeding = st.number_input("出血量 (mL)*", value=None, step=1)
        with oc2:
            st.session_state.eau_grade = st.selectbox("術中合併症（EAUiaiC）*", ["選択してください", "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"], index=0, help=HELP_EAUIAIC)
            if st.session_state.eau_grade not in ["選択してください", "Grade 0"]: st.session_state.eau_detail = st.text_area("術中合併症詳細*")
            st.session_state.ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], index=None, horizontal=True)
            if st.session_state.ln_dissection == "実施した":
                st.session_state.ln_range = st.multiselect("リンパ節郭清範囲*", ["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"])
    elif st.session_state.op_performed == "実施しなかった":
        no_op_opts = ["選択してください", "病勢進行", "G3以上のEVP関連有害事象の発生", "同意撤回", "その他"]
        idx_noop = no_op_opts.index(st.session_state.no_op_reason) if st.session_state.no_op_reason in no_op_opts else 0
        st.session_state.no_op_reason = st.selectbox("実施しなかった理由*", no_op_opts, index=idx_noop)
        if st.session_state.no_op_reason == "その他":
            st.session_state.no_op_reason_other = st.text_area("「その他」の具体的な理由を入力してください*", value=st.session_state.no_op_reason_other)

with tab3:
    if st.session_state.op_performed == "実施した":
        st.markdown('<div class="juog-header">5. 術後病理診断</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        p_checks = []
        with pc1:
            st.session_state.p_histology = st.selectbox("組織型*", ["選択してください", "Urothelial carcinoma", "Squamous cell carcinoma", "Adenocarcinoma", "評価不能", "Other"], index=0)
            p_checks.append(st.session_state.p_histology)
            if st.session_state.p_histology == "Other": st.session_state.p_histology_other = st.text_input("詳細（Other）")
            p_sub_presence = st.radio("亜型の有無*", ["なし", "あり"], index=None, horizontal=True)
            if p_sub_presence == "あり": st.session_state.p_subtype_type = st.multiselect("亜型の種類*", ["Nest型", "Micropapillary型", "Plasmacytoid型", "Sarcomatoid変化", "Lymphoepithelioma-like型", "Clear cell型", "Lipid-rich型", "Trophoblastic分化", "Glandular分化", "Squamous分化"])
            st.session_state.p_morphology = st.selectbox("形態*", ["選択してください", "乳頭状", "非乳頭状", "結節状", "浸潤状", "平坦状", "評価不能", "その他"], index=0)
            p_checks.append(st.session_state.p_morphology)
            st.session_state.p_size = st.number_input("大きさ (最大径 mm)*", value=None, step=0.1)
            st.session_state.p_location = st.multiselect("部位*", ["上腎杯", "中腎杯", "下腎杯", "腎盂", "UPJ", "上部尿管", "中部尿管", "下部尿管", "VUJ"])
        with pc2:
            st.session_state.ypt = st.selectbox("ypT分類*", ["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4", "評価不能"], index=0)
            p_checks.append(st.session_state.ypt)
            st.session_state.ypn = st.selectbox("ypN分類*", ["選択してください", "ypN0", "ypN1", "ypN2", "評価不能"], index=0)
            p_checks.append(st.session_state.ypn)
            if st.session_state.ypn not in ["ypN0", "選択してください", "評価不能"]:
                st.session_state.ypn_pos_sites = st.multiselect("陽性部位*", options=["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"])
            st.session_state.p_multiplicity = st.radio("多発性*", ["単発", "多発"], index=None, horizontal=True)
            st.session_state.p_lvi = st.radio("LVI（脈管侵襲）*", ["なし", "あり", "評価不能"], index=None, horizontal=True)
            p_checks.append(st.session_state.p_lvi)
            st.session_state.r0_status = st.radio("R0切除*", ["陰性", "陽性", "評価不能"], index=None, horizontal=True)
            p_checks.append(st.session_state.r0_status)
            st.session_state.trg_grade = st.radio("病理学的治療効果（TRG分類）*", ["TRG 1", "TRG 2", "TRG 3", "評価不能"], index=None, help=HELP_TRG)
            p_checks.append(st.session_state.trg_grade)

        if "評価不能" in p_checks:
            st.markdown("---")
            st.session_state.p_eval_failed_reason = st.text_area("病理評価不能の理由*", placeholder="評価不能とした詳細な理由を入力してください")
    else: st.write("手術未実施のため入力項目はありません。")

with tab4:
    st.markdown('<div class="juog-header">6. 術後30日目評価</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        if st.session_state.op_performed == "実施した":
            cd_opts = ["選択してください", "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"]
            idx_cd = cd_opts.index(st.session_state.cd_grade) if st.session_state.cd_grade in cd_opts else 0
            st.session_state.cd_grade = st.selectbox("術後合併症 (CD分類)*", cd_opts, index=idx_cd, help=HELP_CD)
            if st.session_state.cd_grade not in ["選択してください", "Grade 0"]: st.session_state.cd_detail = st.text_area("CD分類詳細*")
        else: st.session_state.cd_grade = "N/A"
    with sc2:
        if st.session_state.op_performed == "実施した":
            adj_options = ["選択してください", "無治療（経過観察）", "EVP継続投与", "ペムブロリズマブ単剤維持療法", "ニボルマブ単剤療法（術後補助療法として）", "GC療法（術後補助化学療法として）", "GCarbo療法（術後補助化学療法として）", "その他（放射線療法、治験参加、転移巣切除など）"]
        else:
            adj_options = ["選択してください", "無治療（経過観察）", "EVP継続投与", "ペムブロリズマブ単剤維持療法", "ニボルマブ単剤療法", "GC療法", "GCarbo療法", "その他（放射線療法、治験参加、転移巣切除など）"]
        
        idx_adj = adj_options.index(st.session_state.adj_plan) if st.session_state.adj_plan in adj_options else 0
        st.session_state.adj_plan = st.selectbox("今後の治療予定（または実施中）*", adj_options, index=idx_adj)
        
        if st.session_state.adj_plan in ["その他（放射線療法、治験参加、転移巣切除など）"]: 
            st.session_state.adj_other_detail = st.text_area("治療内容の詳細*", height=200)
        adj_date = st.date_input("次回治療開始予定日または実施日*", value=None)
        st.session_state.status_alive = st.radio("生存状況（術後30日時点）*", ["生存", "死亡"], index=None, horizontal=True)

    st.divider()

    # --- 送信・バリデーションロジック ---
    def f_num(val): return str(val) if (val is not None and val != 0 and val != 0.0) else "【未入力・要確認】"

    if not st.session_state.needs_confirm:
        if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
            h_errors = []
            if st.session_state.facility_name == "選択してください": h_errors.append("・施設名")
            if not st.session_state.patient_id: h_errors.append("・研究対象者識別コード")
            if st.session_state.op_performed is None: h_errors.append("・手術の実施の有無")
            elif st.session_state.op_performed == "実施しなかった":
                if st.session_state.no_op_reason == "選択してください": h_errors.append("・手術を実施しなかった理由")
                elif st.session_state.no_op_reason == "その他" and not st.session_state.no_op_reason_other.strip(): h_errors.append("・「その他」の具体的な理由入力")
            if st.session_state.status_alive is None: h_errors.append("・生存状況")
            
            if st.session_state.op_performed == "実施した":
                p_check_vals = [st.session_state.p_histology, st.session_state.p_morphology, st.session_state.ypt, st.session_state.ypn, st.session_state.p_lvi, st.session_state.r0_status, st.session_state.trg_grade]
                if "評価不能" in p_check_vals and not st.session_state.p_eval_failed_reason.strip():
                    h_errors.append("・病理評価不能の理由（理由の記載が必須です）")
            
            if h_errors:
                st.error("【必須入力エラー】以下の項目を必ず入力してください：\n" + "\n".join(h_errors))
            else:
                s_errors = []
                blood_items = {"WBC":wbc, "Hb":hb, "PLT":plt, "AST":ast, "ALT":alt, "LDH":ldh, "Alb":alb, "Cre":cre, "eGFR":egfr}
                for k, v in blood_items.items(): 
                    if v == 0 or v == 0.0 or v is None: s_errors.append(k)
                if (neutro == 0 or neutro is None) and (lympho == 0 or lympho is None): s_errors.append("白血球分画")
                if st.session_state.adj_plan == "選択してください": s_errors.append("今後の治療予定")

                if s_errors:
                    st.session_state.needs_confirm = True
                    st.session_state.pending_s_errors = s_errors
                    st.rerun()
                else:
                    st.session_state.do_send = True
    
    if st.session_state.needs_confirm:
        st.warning(f"【確認】未入力または未選択の項目があります： " + ", ".join(st.session_state.pending_s_errors) + "\n\n測定していない等の理由で入力困難な場合は、このまま送信可能です。送信しますか？")
        c_col1, c_col2 = st.columns(2)
        if c_col1.button("⚠️ はい、不足を承知で送信します", use_container_width=True):
            st.session_state.do_send = True
            st.session_state.needs_confirm = False
        if c_col2.button("戻って修正する", use_container_width=True):
            st.session_state.needs_confirm = False
            st.rerun()

    if st.session_state.do_send:
        rep = f"""
【基本情報】
施設: {st.session_state.facility_name} / ID: {st.session_state.patient_id}

【血液検査】
WBC: {f_num(wbc)}, Hb: {f_num(hb)}, PLT: {f_num(plt)}, AST: {f_num(ast)}, ALT: {f_num(alt)}, LDH: {f_num(ldh)}, Alb: {f_num(alb)}, Cre: {f_num(cre)}, eGFR: {f_num(egfr)}, CRP: {f_num(crp)}
分画: Neutro {f_num(neutro)}%, Lympho {f_num(lympho)}%, Mono {f_num(mono)}%, Eosino {f_num(eosino)}%, Baso {f_num(baso)}%

【手術状況】
実施: {st.session_state.op_performed} / 理由: {st.session_state.no_op_reason if st.session_state.no_op_reason != 'その他' else 'その他: ' + st.session_state.no_op_reason_other}
入院日: {st.session_state.op_admission_date} / 手術日: {st.session_state.op_date} / 退院(予定)日: {st.session_state.op_discharge_date}
術式: {st.session_state.op_type} / 完遂: {st.session_state.op_completed} (理由: {st.session_state.op_incomplete_detail}) / EAU: {st.session_state.eau_grade}

【病理診断】
組織型: {st.session_state.p_histology} (亜型: {st.session_state.p_subtype_type})
形態: {st.session_state.p_morphology} / サイズ: {st.session_state.p_size}mm / 部位: {st.session_state.p_location}
ypT: {st.session_state.ypt} / ypN: {st.session_state.ypn} / LVI: {st.session_state.p_lvi} / R0: {st.session_state.r0_status} / TRG: {st.session_state.trg_grade}
※病理評価不能理由: {st.session_state.p_eval_failed_reason if st.session_state.p_eval_failed_reason else "なし"}

【30日目評価】
生存: {st.session_state.status_alive} / CD: {st.session_state.cd_grade} (詳細: {st.session_state.cd_detail}) / 今後の予定: {st.session_state.adj_plan} (詳細: {st.session_state.adj_other_detail}) / 次回: {adj_date}
"""
        if send_email(rep, st.session_state.patient_id, st.session_state.facility_name):
            st.success("全ての項目が正常に事務局へ送信されました。")
            st.balloons()
        st.session_state.do_send = False
