import streamlit as st
import json
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# --- ページ設定 ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF", layout="wide")

# --- JUOG専用デザインCSS (タイトル余白80pxを死守) ---
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
        margin-bottom: 80px !important; /* 80pxの余白を死守 */
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
FACILITY_LIST = ["選択してください", "愛知県がんセンター", "秋田大学", "愛媛大学", "大分大学", "大阪公立大学", "大阪大学", "大阪府済生会野江病院", "岡山大学", "香川大学", "鹿児島大学", "関西医科大学", "岐阜大学", "九州大学病院", "京都大学", "久留米大学", "神戸大学", "国立がん研究センター中央病院", "国立病院機構四国がんセンター", "札幌医科大学", "千葉大学", "筑波大学", "東京科学大学", "東京慈恵会医科大学", "東京慈恵会医科大学附属柏病院", "東北大学", "鳥取大学", "富山大学", "長崎大学病院", "名古屋大学", "奈良県立医科大学", "新潟大学大学院 医歯学総合研究科", "浜松医科大学", "原三信病院", "兵庫医科大学", "弘前大学", "北海道大学", "三重大学", "横浜市立大学", "琉球大学", "和歌山県立医科大学", "その他"]

# --- ヘルプテキスト定義 (死守) ---
HELP_EAUIAIC = """
**術中合併症（EAUiaiC）詳細定義**
- **Grade 0**： 介入や手術アプローチの変更を要さず、予定された手術手順からの逸脱がないもの。
- **Grade 1**： 追加処置を要するが生命を脅かさず、後遺症を残さない。
- **Grade 2**： 手術アプローチにおいて主要な追加処置を要する。
- **Grade 3**： 生命を脅かす事態だが臓器摘出は要さない。
- **Grade 4**： 重大な結果をもたらす。4A: 臓器摘出、4B: 手術完了不能。
- **Grade 5**： 5A: 部位間違い等、5B: 術中死亡。
"""

HELP_TRG = """
**TRG (Tumor Regression Grade) 分類**
- **TRG 1：Complete Response**: 生存がん細胞なし。広範な線維化。
- **TRG 2：Strong Response**: 線維化優位。生存がん細胞50%未満。
- **TRG 3：Weak and No Response**: 生存がん細胞優位、または変化なし。
"""

HELP_CD = """
**Clavien-Dindo 分類 (術後30日以内)**
Gradingの原則：
- **Grade I**：薬物・外科的治療等を要さない。正常な術後経過からの逸脱。
- **Grade II**：制吐剤、解熱剤等以外の薬物療法（輸血、TPN含む）を要する。
- **Grade III**：外科的・内視鏡的治療等を要する（IIIa: 局麻、IIIb: 全麻）。
- **Grade IV**：ICU管理を要する生命を脅かす合併症（IVa: 単一臓器不全、IVb: 多臓器不全）。
- **Grade V**：患者の死亡。
"""

# --- セッション状態初期化 (血液検査項目と生存詳細を完全網羅) ---
if 'init_done' not in st.session_state:
    st.session_state['init_done'] = True
    defaults = {
        "facility_name": "選択してください", "patient_id": "", "reporter_email": "",
        "last_evp_date": None, "pre_ae_grade": "選択してください", "ae_detail": "なし",
        "vital_abnormality": None, "vital_detail": "N/A", 
        "cysto_find": None, "bladder_tumor_tx": "N/A", 
        "wbc_90": None, "hb_90": None, "plt_90": None, "ast_90": None, "alt_90": None,
        "ldh_90": None, "alb_90": None, "cre_90": None, "egfr_90": None, "crp_90": None,
        "neutro_90": None, "lympho_90": None, "mono_90": None, "eosino_90": None, "baso_90": None,
        "op_performed": None, "op_date": None, "op_admission_date": None, "op_discharge_date": None,
        "op_type": "選択してください", "approach": None, "op_completed": None, "op_incomplete_detail": "N/A",
        "op_time": None, "bleeding": None, "eau_grade": "選択してください", "eau_detail": "N/A", "ln_dissection": None,
        "ln_range": [], "p_histology": "選択してください", "p_histology_other": "N/A",
        "p_subtype_presence": None, "p_subtype_type": [], "p_morphology": "選択してください",
        "p_size": None, "p_location": [], "ypt": "選択してください", "ypn": "選択してください", "ypn_pos_sites": [],
        "p_multiplicity": None, "p_lvi": None, "r0_status": None, "p_eval_failed_reason": "",
        "trg_grade": None, "no_op_reason": "選択してください", "no_op_reason_other": "",
        "cd_grade": "選択してください", "cd_detail": "N/A", "adj_plan": "選択してください", "adj_other_detail": "", "adj_date": None,
        "status_alive": None, "final_visit_date_30": None, "death_date_30": None, "death_cause_30": "選択してください",
        "needs_confirm": False, "do_send": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def send_email(report_content, pid, facility, reporter_email=None):
    try:
        mail_user = st.secrets["email"]["user"]; mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        if reporter_email: to_addrs.append(reporter_email)
        msg = MIMEMultipart(); msg['From'] = mail_user; msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = f"【JUOG CRF】周術期報告（{facility} / ID: {pid}）"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass); server.send_message(msg); server.quit()
        return True
    except: return False

st.title("JUOG UTUC_Consolidative 周術期CRF")

# --- 共通ヘッダー ---
st.markdown('<div class="top-info-bar">', unsafe_allow_html=True)
col_h1, col_h2 = st.columns(2)
with col_h1:
    idx_fac = FACILITY_LIST.index(st.session_state.facility_name) if st.session_state.facility_name in FACILITY_LIST else 0
    st.session_state.facility_name = st.selectbox("施設名*", FACILITY_LIST, index=idx_fac)
    st.session_state.reporter_email = st.text_input("担当者メールアドレス（控えの送付先）*", value=st.session_state.reporter_email)
with col_h2:
    st.session_state.patient_id = st.text_input("研究対象者識別コード*", value=st.session_state.patient_id)
st.markdown('</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs(["📊 術前・登録時", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

with tab1:
    st.markdown('<div class="juog-header">1. 術前EVP・身体所見</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.last_evp_date = st.date_input("最終EVP投与日", value=st.session_state.last_evp_date)
        ae_opts = ["選択してください", "なし", "Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症", "Grade 4 生命を脅かす", "Grade 5 死亡"]
        idx_ae = ae_opts.index(st.session_state.pre_ae_grade) if st.session_state.pre_ae_grade in ae_opts else 0
        st.session_state.pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade*", ae_opts, index=idx_ae)
        if st.session_state.pre_ae_grade not in ["選択してください", "なし"]:
            st.session_state.ae_detail = st.text_input("CTCAE（詳細記載）*", value=st.session_state.ae_detail)
    with c2:
        st.session_state.vital_abnormality = st.radio("術前身体所見およびバイタルサインの異常*", ["異常なし", "異常あり"], index=(0 if st.session_state.vital_abnormality == "異常なし" else 1 if st.session_state.vital_abnormality == "異常あり" else None), horizontal=True)
        if st.session_state.vital_abnormality == "異常あり": st.session_state.vital_detail = st.text_input("異常の詳細*", value=st.session_state.vital_detail)
        st.session_state.cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], index=(0 if st.session_state.cysto_find == "腫瘍なし" else 1 if st.session_state.cysto_find == "腫瘍あり" else None), horizontal=True)
        if st.session_state.cysto_find == "腫瘍あり": st.session_state.bladder_tumor_tx = st.text_area("膀胱腫瘍の治療法についての詳細*", value=st.session_state.bladder_tumor_tx)

    st.markdown('<div class="juog-header">2. 術前血液検査（一か月以内）</div>', unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        wbc = st.number_input("WBC (/μL)*", value=st.session_state.wbc_90, step=1.0)
        hb = st.number_input("Hb (g/dL)*", value=st.session_state.hb_90, step=0.1)
        plt = st.number_input("PLT (x10^4/μL)*", value=st.session_state.plt_90, step=1.0)
        ast = st.number_input("AST (U/L)*", value=st.session_state.ast_90, step=1.0)
        alt = st.number_input("ALT (U/L)*", value=st.session_state.alt_90, step=1.0)
    with bc2:
        ldh = st.number_input("LDH (U/L)*", value=st.session_state.ldh_90, step=1.0)
        alb = st.number_input("Alb (g/dL)*", value=st.session_state.alb_90, step=0.1)
        cre = st.number_input("Cre (mg/dL)*", value=st.session_state.cre_90, step=0.01)
        egfr = st.number_input("eGFR (mL/min/1.73m²)*", value=st.session_state.egfr_90, step=0.1)
        crp = st.number_input("CRP (mg/dL)*", value=st.session_state.crp_90, step=0.01)

    st.subheader("白血球分画 (%)")
    f1, f2, f3, f4, f5 = st.columns(5)
    neutro = f1.number_input("Neutro*", value=st.session_state.neutro_90, step=0.1)
    lympho = f2.number_input("Lympho*", value=st.session_state.lympho_90, step=0.1)
    mono = f3.number_input("Mono*", value=st.session_state.mono_90, step=0.1)
    eosino = f4.number_input("Eosino*", value=st.session_state.eosino_90, step=0.1)
    baso = f5.number_input("Baso*", value=st.session_state.baso_90, step=0.1)

with tab2:
    st.markdown('<div class="juog-header">4. 手術実施状況</div>', unsafe_allow_html=True)
    st.session_state.op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], index=(0 if st.session_state.op_performed == "実施した" else 1 if st.session_state.op_performed == "実施しなかった" else None), horizontal=True)
    if st.session_state.op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            st.session_state.op_admission_date = st.date_input("入院日*", value=st.session_state.op_admission_date)
            st.session_state.op_date = st.date_input("手術実施日*", value=st.session_state.op_date)
            st.session_state.op_discharge_date = st.date_input("退院日（または退院予定日）", value=st.session_state.op_discharge_date)
            op_types = ["選択してください", "根治的腎尿管全摘除術", "尿管部分切除術"]
            idx_op = op_types.index(st.session_state.op_type) if st.session_state.op_type in op_types else 0
            st.session_state.op_type = st.selectbox("術式*", op_types, index=idx_op)
            st.session_state.approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], index=(0 if st.session_state.approach=="開腹" else 1 if st.session_state.approach=="腹腔鏡" else 2 if st.session_state.approach=="ロボット支援" else None), horizontal=True)
            st.session_state.op_time = st.number_input("手術時間 (分)*", value=st.session_state.op_time, step=1)
            st.session_state.bleeding = st.number_input("出血量 (mL)*", value=st.session_state.bleeding, step=1)
        with oc2:
            eau_opts = ["選択してください", "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"]
            idx_eau = eau_opts.index(st.session_state.eau_grade) if st.session_state.eau_grade in eau_opts else 0
            st.session_state.eau_grade = st.selectbox("術中合併症（EAUiaiC）*", eau_opts, index=idx_eau, help=HELP_EAUIAIC)
            st.session_state.ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], index=(0 if st.session_state.ln_dissection=="実施した" else 1 if st.session_state.ln_dissection=="実施しなかった" else None), horizontal=True)
            if st.session_state.ln_dissection == "実施した":
                st.session_state.ln_range = st.multiselect("リンパ節郭清範囲*", ["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"], default=st.session_state.ln_range)
    elif st.session_state.op_performed == "実施しなかった":
        no_op_opts = ["選択してください", "病勢進行", "G3以上のEVP関連有害事象の発生", "同意撤回", "その他"]
        idx_noop = no_op_opts.index(st.session_state.no_op_reason) if st.session_state.no_op_reason in no_op_opts else 0
        st.session_state.no_op_reason = st.selectbox("実施しなかった理由*", no_op_opts, index=idx_noop)

with tab3:
    if st.session_state.op_performed == "実施した":
        st.markdown('<div class="juog-header">5. 術後病理診断</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            h_opts = ["選択してください", "Urothelial carcinoma", "Other"]
            idx_h = h_opts.index(st.session_state.p_histology) if st.session_state.p_histology in h_opts else 0
            st.session_state.p_histology = st.selectbox("組織型*", h_opts, index=idx_h)
            st.session_state.p_size = st.number_input("大きさ (最大径 mm)*", value=st.session_state.p_size, step=0.1)
        with pc2:
            ypt_opts = ["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4"]
            idx_ypt = ypt_opts.index(st.session_state.ypt) if st.session_state.ypt in ypt_opts else 0
            st.session_state.ypt = st.selectbox("ypT分類*", ypt_opts, index=idx_ypt)
            ypn_opts = ["選択してください", "ypN0", "ypN1", "ypN2"]
            idx_ypn = ypn_opts.index(st.session_state.ypn) if st.session_state.ypn in ypn_opts else 0
            st.session_state.ypn = st.selectbox("ypN分類*", ypn_opts, index=idx_ypn)
            trg_opts = ["TRG 1", "TRG 2", "TRG 3", "評価不能"]
            idx_trg = trg_opts.index(st.session_state.trg_grade) if st.session_state.trg_grade in trg_opts else None
            st.session_state.trg_grade = st.radio("病理学的治療効果（TRG分類）*", trg_opts, index=idx_trg, help=HELP_TRG)

with tab4:
    st.markdown('<div class="juog-header">6. 術後30日目評価</div>', unsafe_allow_html=True)
    
    # --- 1段目: 生存状況を左、合併症を右に配置 ---
    sc1, sc2 = st.columns(2)
    with sc1:
        # 生存状況のラジオボタンを左側に死守
        st.session_state.status_alive = st.radio("生存状況 (術後30日時点)*", ["生存", "死亡"], index=(0 if st.session_state.status_alive=="生存" else 1 if st.session_state.status_alive=="死亡" else None), horizontal=True)
    with sc2:
        if st.session_state.op_performed == "実施した":
            cd_opts = ["選択してください", "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"]
            idx_cd = cd_opts.index(st.session_state.cd_grade) if st.session_state.cd_grade in cd_opts else 0
            st.session_state.cd_grade = st.selectbox("術後合併症 (CD分類)*", cd_opts, index=idx_cd, help=HELP_CD)
            if st.session_state.cd_grade not in ["選択してください", "Grade 0"]:
                st.session_state.cd_detail = st.text_area("CD分類詳細*", value=st.session_state.cd_detail)
        else: st.session_state.cd_grade = "N/A"

    # --- 2段目: 日付・詳細を左、今後の予定を右に配置 ---
    sd1, sd2 = st.columns(2)
    with sd1:
        if st.session_state.status_alive == "生存":
            st.session_state.final_visit_date_30 = st.date_input("最終生存確認日(最終来院日)*", value=st.session_state.final_visit_date_30)
        elif st.session_state.status_alive == "死亡":
            st.session_state.death_date_30 = st.date_input("死亡日*", value=st.session_state.death_date_30)
            death_causes = ["選択してください", "癌死 (原疾患による)", "治療関連死 (合併症・有害事象)", "他病死", "不明"]
            idx_dc = death_causes.index(st.session_state.death_cause_30) if st.session_state.death_cause_30 in death_causes else 0
            st.session_state.death_cause_30 = st.selectbox("死因*", death_causes, index=idx_dc)

    with sd2:
        # 生存時のみ表示される設定（死亡時は空白となり省略されない）
        if st.session_state.status_alive == "生存":
            st.markdown("**【今後の予定】**")
            adj_plans = ["選択してください", "無治療（経過観察）", "EVP継続投与", "ペムブロ単剤維持", "その他"]
            idx_ap = adj_plans.index(st.session_state.adj_plan) if st.session_state.adj_plan in adj_plans else 0
            st.session_state.adj_plan = st.selectbox("今後の治療予定*", adj_plans, index=idx_ap)
            if st.session_state.adj_plan == "その他":
                st.session_state.adj_other_detail = st.text_area("詳細内容*", value=st.session_state.adj_other_detail)
            st.session_state.adj_date = st.date_input("次回治療開始予定日*", value=st.session_state.adj_date)

    st.divider()

    def f_num(val): return str(val) if (val is not None and val != 0 and val != 0.0) else "N/A"

    if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
        h_errors = []
        d = st.session_state
        if d.facility_name == "選択してください": h_errors.append("・施設名")
        if not d.patient_id: h_errors.append("・識別コード")
        if not d.reporter_email or not re.match(r"[^@]+@[^@]+\.[^@]+", d.reporter_email): h_errors.append("・有効なメールアドレス")
        
        if d.status_alive is None: 
            h_errors.append("・生存状況")
        elif d.status_alive == "生存":
            if not d.final_visit_date_30: h_errors.append("・最終生存確認日")
            if d.cd_grade == "Grade V": h_errors.append("・生存なのにCD分類がGrade Vになっています")
            if d.adj_plan == "選択してください": h_errors.append("・今後の治療予定を選択してください")
        elif d.status_alive == "死亡":
            if d.cd_grade != "Grade V": h_errors.append("・死亡なのにCD分類がGrade V以外になっています")
            if not d.death_date_30: h_errors.append("・死亡日")
            if d.death_cause_30 == "選択してください": h_errors.append("・死因")

        if h_errors:
            st.error("【入力エラー】以下の項目を確認してください：\n" + "\n".join(h_errors))
        else:
            rep = f"""【JUOG 周術期報告】
施設: {d.facility_name} / ID: {d.patient_id}
報告者控え: {d.reporter_email}

【生存状況 (30日目)】
状況: {d.status_alive}
"""
            if d.status_alive == "生存":
                rep += f"最終生存確認日: {d.final_visit_date_30}\n今後の予定: {d.adj_plan} (開始日: {d.adj_date})\n"
            else:
                rep += f"死亡日: {d.death_date_30} / 死因: {d.death_cause_30}\n"

            rep += f"""
【合併症・他】
CD分類: {d.cd_grade} (詳細: {d.cd_detail})
主要採血: WBC:{f_num(wbc)}, Hb:{f_num(hb)}, Cre:{f_num(cre)}
"""
            if send_email(rep, d.patient_id, d.facility_name, d.reporter_email):
                st.success(f"正常に送信されました。{d.reporter_email} 宛に控えを送付しました。")
                st.balloons()
