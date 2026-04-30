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

# --- 施設リスト（あいうえお順） ---
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
- **Grade 0**： 介入や手術アプローチの変更を要さず、予定された手術手順からの逸脱がないもの。
- **Grade 1**： 追加処置を要するが、生命を脅かさない。
- **Grade 2**： 主要な追加・代替処置を要する。
- **Grade 3**： 生命を脅かすが、臓器摘出は要さない。
- **Grade 4**： 重大な結果（4A:臓器摘出, 4B:完了不能）。
- **Grade 5**： 術中死亡など。
"""

HELP_TRG = """
**TRG (Tumor Regression Grade) 分類**
- **TRG 1**：Complete Response
- **TRG 2**：Strong Response (生存がん細胞50%未満)
- **TRG 3**：Weak and No Response (生存がん細胞50%以上)
"""

HELP_CD = """
**Clavien-Dindo 分類 (術後30日以内)**
- **Grade I**: 薬物、外科、内視鏡治療を要さない。
- **Grade II**: 輸血、中心静脈栄養、一部の薬物療法。
- **Grade III**: 外科、内視鏡、IVR治療を要する。
- **Grade IV**: ICU管理を要する生命を脅かす合併症。
- **Grade V**: 患者の死亡。
"""

# --- セッション状態初期化 ---
if 'init_done' not in st.session_state:
    st.session_state['init_done'] = True
    defaults = {
        "facility_name": "選択してください", "patient_id": "",
        "pre_ae_grade": "選択してください", "vital_abnormality": None, "vital_detail": "",
        "cysto_find": None, "bladder_tumor_tx": "",
        "op_performed": None, "op_date": None, "op_admission_date": None, "op_discharge_date": None,
        "op_type": "選択してください", "approach": None, "op_completed": None, "op_incomplete_detail": "",
        "op_time": 0, "bleeding": 0, "eau_grade": "選択してください", "eau_detail": "", "ln_dissection": None,
        "ln_range": [], "p_histology": "選択してください", "p_histology_other": "",
        "p_subtype_presence": None, "p_subtype_type": [], "p_morphology": "選択してください",
        "p_size": 0.0, "p_location": [], "ypt": "選択してください", "ypn": "選択してください", "ypn_pos_sites": [],
        "p_multiplicity": None, "p_lvi": None, "r0_status": None, "p_eval_failed_reason": "",
        "trg_grade": None, "no_op_reason": "選択してください", "no_op_reason_other": "", "cd_grade": "選択してください", "cd_detail": "",
        "adj_plan": "選択してください", "adj_other_detail": "", "adj_date": None, "status_alive": None,
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
        ae_opts = ["選択してください", "なし", "Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症", "Grade 4 生命を脅かす", "Grade 5 死亡"]
        idx_ae = ae_opts.index(st.session_state.pre_ae_grade) if st.session_state.pre_ae_grade in ae_opts else 0
        st.session_state.pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade*", ae_opts, index=idx_ae)
        st.caption("[JCOG版 CTCAE v6.0 日本語訳（外部リンク）](https://jcog.jp/assets/CTCAEv6J_20260301_v28_0.pdf)")
        ae_detail = st.text_input("CTCAE（詳細記載）") if st.session_state.pre_ae_grade not in ["選択してください", "なし"] else "なし"
    with c2:
        idx_vital = ["異常なし", "異常あり"].index(st.session_state.vital_abnormality) if st.session_state.vital_abnormality in ["異常なし", "異常あり"] else None
        st.session_state.vital_abnormality = st.radio("術前身体所見およびバイタルサインの異常*", ["異常なし", "異常あり"], index=idx_vital, horizontal=True)
        if st.session_state.vital_abnormality == "異常あり": st.session_state.vital_detail = st.text_input("異常の詳細*", value=st.session_state.vital_detail)
        idx_cysto = ["腫瘍なし", "腫瘍あり"].index(st.session_state.cysto_find) if st.session_state.cysto_find in ["腫瘍なし", "腫瘍あり"] else None
        st.session_state.cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], index=idx_cysto, horizontal=True)
        if st.session_state.cysto_find == "腫瘍あり": st.session_state.bladder_tumor_tx = st.text_area("膀胱腫瘍の治療法についての詳細*", value=st.session_state.bladder_tumor_tx)

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
        cre = st.number_input("Cre (mg/dL)*", value=0.00, step=0.01)
        egfr = st.number_input("eGFR (mL/min/1.73m²)*", value=0.0, step=0.1)
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
    idx_perf = ["実施した", "実施しなかった"].index(st.session_state.op_performed) if st.session_state.op_performed in ["実施した", "実施しなかった"] else None
    st.session_state.op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], index=idx_perf, horizontal=True)
    if st.session_state.op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            st.session_state.op_admission_date = st.date_input("入院日*", value=st.session_state.op_admission_date)
            st.session_state.op_date = st.date_input("手術実施日*", value=st.session_state.op_date)
            st.session_state.op_discharge_date = st.date_input("退院日（または退院予定日）", value=st.session_state.op_discharge_date)
            op_opts = ["選択してください", "根治的腎尿管全摘除術", "尿管部分切除術"]
            idx_op = op_opts.index(st.session_state.op_type) if st.session_state.op_type in op_opts else 0
            st.session_state.op_type = st.selectbox("術式*", op_opts, index=idx_op)
            idx_app = ["開腹", "腹腔鏡", "ロボット支援"].index(st.session_state.approach) if st.session_state.approach in ["開腹", "腹腔鏡", "ロボット支援"] else None
            st.session_state.approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], index=idx_app, horizontal=True)
            idx_comp = ["はい", "いいえ"].index(st.session_state.op_completed) if st.session_state.op_completed in ["はい", "いいえ"] else None
            st.session_state.op_completed = st.radio("予定手術が完遂できたか*", ["はい", "いいえ"], index=idx_comp, horizontal=True)
            if st.session_state.op_completed == "いいえ": st.session_state.op_incomplete_detail = st.text_area("完遂できなかった理由*", value=st.session_state.op_incomplete_detail)
            st.session_state.op_time = st.number_input("手術時間 (分)*", value=st.session_state.op_time, step=1)
            st.session_state.bleeding = st.number_input("出血量 (mL)*", value=st.session_state.bleeding, step=1)
        with oc2:
            eau_opts = ["選択してください", "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"]
            idx_eau = eau_opts.index(st.session_state.eau_grade) if st.session_state.eau_grade in eau_opts else 0
            st.session_state.eau_grade = st.selectbox("術中合併症（EAUiaiC）*", eau_opts, index=idx_eau, help=HELP_EAUIAIC)
            if st.session_state.eau_grade not in ["選択してください", "Grade 0"]: st.session_state.eau_detail = st.text_area("術中合併症詳細*", value=st.session_state.eau_detail)
            idx_ln = ["実施した", "実施しなかった"].index(st.session_state.ln_dissection) if st.session_state.ln_dissection in ["実施した", "実施しなかった"] else None
            st.session_state.ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], index=idx_ln, horizontal=True)
            if st.session_state.ln_dissection == "実施した":
                st.session_state.ln_range = st.multiselect("リンパ節郭清範囲*", ["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"], default=st.session_state.ln_range)
    elif st.session_state.op_performed == "実施しなかった":
        no_op_options = ["選択してください", "病勢進行", "G3以上のEVP関連有害事象の発生", "同意撤回", "その他"]
        idx_noop = no_op_options.index(st.session_state.no_op_reason) if st.session_state.no_op_reason in no_op_options else 0
        st.session_state.no_op_reason = st.selectbox("実施しなかった理由*", no_op_options, index=idx_noop)
        if st.session_state.no_op_reason == "その他":
            st.session_state.no_op_reason_other = st.text_area("「その他」の具体的な理由を入力してください*", value=st.session_state.no_op_reason_other)

with tab3:
    if st.session_state.op_performed == "実施した":
        st.markdown('<div class="juog-header">5. 術後病理診断</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        p_checks = []
        with pc1:
            h_opts = ["選択してください", "Urothelial carcinoma", "Squamous cell carcinoma", "Adenocarcinoma", "評価不能", "Other"]
            idx_hist = h_opts.index(st.session_state.p_histology) if st.session_state.p_histology in h_opts else 0
            st.session_state.p_histology = st.selectbox("組織型*", h_opts, index=idx_hist)
            p_checks.append(st.session_state.p_histology)
            if st.session_state.p_histology == "Other": st.session_state.p_histology_other = st.text_input("詳細（Other）*", value=st.session_state.p_histology_other)
            idx_sub = ["なし", "あり"].index(st.session_state.p_subtype_presence) if st.session_state.p_subtype_presence in ["なし", "あり"] else None
            st.session_state.p_subtype_presence = st.radio("亜型の有無*", ["なし", "あり"], index=idx_sub, horizontal=True)
            if st.session_state.p_subtype_presence == "あり": st.session_state.p_subtype_type = st.multiselect("亜型の種類*", ["Nest型", "Micropapillary型", "Plasmacytoid型", "Sarcomatoid変化", "Lymphoepithelioma-like型", "Clear cell型", "Lipid-rich型", "Trophoblastic分化", "Glandular分化", "Squamous分化"], default=st.session_state.p_subtype_type)
            m_opts = ["選択してください", "乳頭状", "非乳頭状", "結節状", "浸潤状", "平坦状", "評価不能", "その他"]
            idx_morph = m_opts.index(st.session_state.p_morphology) if st.session_state.p_morphology in m_opts else 0
            st.session_state.p_morphology = st.selectbox("形態*", m_opts, index=idx_morph)
            p_checks.append(st.session_state.p_morphology)
            st.session_state.p_size = st.number_input("大きさ (最大径 mm)*", value=st.session_state.p_size, step=0.1)
            st.session_state.p_location = st.multiselect("部位*", ["上腎杯", "中腎杯", "下腎杯", "腎盂", "UPJ", "上部尿管", "中部尿管", "下部尿管", "VUJ"], default=st.session_state.p_location)
        with pc2:
            t_opts = ["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4", "評価不能"]
            idx_t = t_opts.index(st.session_state.ypt) if st.session_state.ypt in t_opts else 0
            st.session_state.ypt = st.selectbox("ypT分類*", t_opts, index=idx_t)
            p_checks.append(st.session_state.ypt)
            n_opts = ["選択してください", "ypN0", "ypN1", "ypN2", "評価不能"]
            idx_n = n_opts.index(st.session_state.ypn) if st.session_state.ypn in n_opts else 0
            st.session_state.ypn = st.selectbox("ypN分類*", n_opts, index=idx_n)
            p_checks.append(st.session_state.ypn)
            if st.session_state.ypn not in ["ypN0", "選択してください", "評価不能"]:
                st.session_state.ypn_pos_sites = st.multiselect("陽性部位*", options=["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"], default=st.session_state.ypn_pos_sites)
            idx_mult = ["単発", "多発"].index(st.session_state.p_multiplicity) if st.session_state.p_multiplicity in ["単発", "多発"] else None
            st.session_state.p_multiplicity = st.radio("多発性*", ["単発", "多発"], index=idx_mult, horizontal=True)
            idx_lvi = ["なし", "あり", "評価不能"].index(st.session_state.p_lvi) if st.session_state.p_lvi in ["なし", "あり", "評価不能"] else None
            st.session_state.p_lvi = st.radio("LVI（脈管侵襲）*", ["なし", "あり", "評価不能"], index=idx_lvi, horizontal=True)
            p_checks.append(st.session_state.p_lvi)
            idx_r0 = ["陰性", "陽性", "評価不能"].index(st.session_state.r0_status) if st.session_state.r0_status in ["陰性", "陽性", "評価不能"] else None
            st.session_state.r0_status = st.radio("R0切除*", ["陰性", "陽性", "評価不能"], index=idx_r0, horizontal=True)
            p_checks.append(st.session_state.r0_status)
            trg_opts = ["TRG 1", "TRG 2", "TRG 3", "評価不能"]
            idx_trg = trg_opts.index(st.session_state.trg_grade) if st.session_state.trg_grade in trg_opts else None
            st.session_state.trg_grade = st.radio("病理学的治療効果（TRG分類）*", trg_opts, index=idx_trg, help=HELP_TRG)
            p_checks.append(st.session_state.trg_grade)

        if "評価不能" in p_checks:
            st.markdown("---")
            st.session_state.p_eval_failed_reason = st.text_area("病理評価不能の理由*", value=st.session_state.p_eval_failed_reason, placeholder="評価不能とした詳細な理由を入力してください")
    else: st.write("手術未実施のため入力項目はありません。")

with tab4:
    st.markdown('<div class="juog-header">6. 術後30日目評価</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        if st.session_state.op_performed == "実施した":
            cd_opts = ["選択してください", "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"]
            # 修正箇所：エラーの回避（session_stateの値がリストにない場合は0を返す）
            idx_cd = cd_opts.index(st.session_state.cd_grade) if st.session_state.cd_grade in cd_opts else 0
            st.session_state.cd_grade = st.selectbox("術後合併症 (CD分類)*", cd_opts, index=idx_cd, help=HELP_CD)
            if st.session_state.cd_grade not in ["選択してください", "Grade 0"]: st.session_state.cd_detail = st.text_area("CD分類詳細*", value=st.session_state.cd_detail)
        else: st.session_state.cd_grade = "N/A"
    with sc2:
        if st.session_state.op_performed == "実施した":
            adj_options = ["選択してください", "無治療（経過観察）", "EVP継続投与", "ペムブロリズマブ単剤維持療法", "ニボルマブ単剤療法（術後補助療法として）", "GC療法（術後補助化学療法として）", "GCarbo療法（術後補助化学療法として）", "その他（放射線療法、治験参加、転移巣切除など）"]
        else:
            adj_options = ["選択してください", "無治療（経過観察）", "EVP継続投与", "ペムブロリズマブ単剤維持療法", "ニボルマブ単剤療法", "GC療法", "GCarbo療法", "その他（放射線療法、治験参加、転移巣切除など）"]
        
        idx_adj = adj_options.index(st.session_state.adj_plan) if st.session_state.adj_plan in adj_options else 0
        st.session_state.adj_plan = st.selectbox("今後の治療予定（または実施中）*", adj_options, index=idx_adj)
        if st.session_state.adj_plan == "その他（放射線療法、治験参加、転移巣切除など）": 
            st.session_state.adj_other_detail = st.text_area("治療内容の詳細*", value=st.session_state.adj_other_detail, height=100)
        st.session_state.adj_date = st.date_input("次回治療開始予定日または実施日*", value=st.session_state.adj_date)
        idx_alive = ["生存", "死亡"].index(st.session_state.status_alive) if st.session_state.status_alive in ["生存", "死亡"] else None
        st.session_state.status_alive = st.radio("生存状況（術後30日時点）*", ["生存", "死亡"], index=idx_alive, horizontal=True)

    st.divider()

    # --- 送信・バリデーションロジック ---
    if not st.session_state.needs_confirm:
        if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
            h_errors = []
            if st.session_state.facility_name == "選択してください": h_errors.append("・施設名")
            if not st.session_state.patient_id: h_errors.append("・研究対象者識別コード")
            if st.session_state.pre_ae_grade == "選択してください": h_errors.append("・術前EVP関連AE")
            if st.session_state.vital_abnormality is None: h_errors.append("・バイタル異常の有無")
            elif st.session_state.vital_abnormality == "異常あり" and not st.session_state.vital_detail.strip(): h_errors.append("・異常の詳細内容")
            if st.session_state.cysto_find is None: h_errors.append("・膀胱鏡所見")
            elif st.session_state.cysto_find == "腫瘍あり" and not st.session_state.bladder_tumor_tx.strip(): h_errors.append("・膀胱腫瘍の治療法詳細")
            if st.session_state.op_performed is None: h_errors.append("・手術の実施の有無")
            elif st.session_state.op_performed == "実施した":
                if not st.session_state.op_admission_date: h_errors.append("・入院日")
                if not st.session_state.op_date: h_errors.append("・手術実施日")
                if st.session_state.op_type == "選択してください": h_errors.append("・術式")
                if st.session_state.approach is None: h_errors.append("・アプローチ")
                if st.session_state.op_completed is None: h_errors.append("・手術完遂の有無")
                elif st.session_state.op_completed == "いいえ" and not st.session_state.op_incomplete_detail.strip(): h_errors.append("・完遂できなかった理由")
                if st.session_state.op_time <= 0: h_errors.append("・手術時間")
                if st.session_state.eau_grade == "選択してください": h_errors.append("・術中合併症(EAU)")
                elif st.session_state.eau_grade != "Grade 0" and not st.session_state.eau_detail.strip(): h_errors.append("・術中合併症の詳細")
                if st.session_state.ln_dissection is None: h_errors.append("・リンパ節郭清の有無")
                elif st.session_state.ln_dissection == "実施した" and not st.session_state.ln_range: h_errors.append("・リンパ節郭清範囲")
                if st.session_state.p_histology == "選択してください": h_errors.append("・組織型")
                if st.session_state.p_histology == "Other" and not st.session_state.p_histology_other.strip(): h_errors.append("・組織型(Other)の詳細")
                if st.session_state.p_subtype_presence is None: h_errors.append("・亜型の有無")
                if st.session_state.p_morphology == "選択してください": h_errors.append("・形態")
                if st.session_state.p_size <= 0: h_errors.append("・腫瘍サイズ")
                if not st.session_state.p_location: h_errors.append("・部位")
                if st.session_state.ypt == "選択してください": h_errors.append("・ypT分類")
                if st.session_state.ypn == "選択してください": h_errors.append("・ypN分類")
                if st.session_state.p_multiplicity is None: h_errors.append("・多発性")
                if st.session_state.p_lvi is None: h_errors.append("・LVI")
                if st.session_state.r0_status is None: h_errors.append("・R0切除")
                if st.session_state.trg_grade is None: h_errors.append("・TRG分類")
                p_check_vals = [st.session_state.p_histology, st.session_state.p_morphology, st.session_state.ypt, st.session_state.ypn, st.session_state.p_lvi, st.session_state.r0_status, st.session_state.trg_grade]
                if "評価不能" in p_check_vals and not st.session_state.p_eval_failed_reason.strip(): h_errors.append("・病理評価不能の理由")
            else:
                if st.session_state.no_op_reason == "選択してください": h_errors.append("・手術を実施しなかった理由")
                elif st.session_state.no_op_reason == "その他" and not st.session_state.no_op_reason_other.strip(): h_errors.append("・「その他」の具体的な理由入力")
            if st.session_state.op_performed == "実施した":
                if st.session_state.cd_grade == "選択してください": h_errors.append("・術後合併症(CD)")
                elif st.session_state.cd_grade != "Grade 0" and not st.session_state.cd_detail.strip(): h_errors.append("・CD分類の詳細")
            if st.session_state.adj_plan == "選択してください": h_errors.append("・今後の治療予定")
            elif st.session_state.adj_plan == "その他（放射線療法、治験参加、転移巣切除など）" and not st.session_state.adj_other_detail.strip(): h_errors.append("・今後の治療詳細")
            if not st.session_state.adj_date: h_errors.append("・次回治療予定日")
            if st.session_state.status_alive is None: h_errors.append("・生存状況")
            
            if h_errors:
                st.error("【必須入力エラー】以下の項目を埋めてください：\n" + "\n".join(h_errors))
            else:
                s_errors = []
                blood_items = {"WBC":wbc, "Hb":hb, "PLT":plt, "AST":ast, "ALT":alt, "LDH":ldh, "Alb":alb, "Cre":cre, "eGFR":egfr}
                for k, v in blood_items.items(): 
                    if v == 0 or v == 0.0: s_errors.append(k)
                if neutro == 0 and lympho == 0: s_errors.append("白血球分画")
                if s_errors:
                    st.session_state.needs_confirm = True
                    st.session_state.pending_s_errors = s_errors
                    st.rerun()
                else:
                    st.session_state.do_send = True
    
    if st.session_state.needs_confirm:
        st.warning(f"確認：血液データが 0 です ({', '.join(st.session_state.pending_s_errors)})。送信しますか？")
        c_col1, c_col2 = st.columns(2)
        if c_col1.button("⚠️ はい、不足を承知で送信します", use_container_width=True):
            st.session_state.do_send = True
            st.session_state.needs_confirm = False
        if c_col2.button("戻って修正する", use_container_width=True):
            st.session_state.needs_confirm = False
            st.rerun()

    if st.session_state.do_send:
        def f_num(val): return str(val) if val != 0 and val != 0.0 else "N/A"
        final_no_op = st.session_state.no_op_reason
        if final_no_op == "その他": final_no_op = f"その他: {st.session_state.no_op_reason_other}"
        
        rep = f"""
【報告】施設: {st.session_state.facility_name} / ID: {st.session_state.patient_id}
術前AE: {st.session_state.pre_ae_grade} / バイタル異常: {st.session_state.vital_abnormality}
手術: {st.session_state.op_performed} / 理由: {final_no_op} / 日付: {st.session_state.op_date}
病理: T:{st.session_state.ypt} N:{st.session_state.ypn} TRG:{st.session_state.trg_grade}
生存: {st.session_state.status_alive} / CD: {st.session_state.cd_grade} / 今後の予定: {st.session_state.adj_plan}
"""
        if send_email(rep, st.session_state.patient_id, st.session_state.facility_name):
            st.success("全ての項目が正常に事務局へ送信されました。")
            st.balloons()
        st.session_state.do_send = False
