import streamlit as st
import json
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

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
        margin-bottom: 80px !important; 
        font-weight: 800; 
        height: 40px;
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
    </style>
    """, unsafe_allow_html=True)

# --- 施設リスト ---
FACILITY_LIST = ["選択してください", "愛知県がんセンター", "秋田大学", "愛媛大学", "大分大学", "大阪公立大学", "大阪大学", "大阪府済生会野江病院", "岡山大学", "香川大学", "鹿児島大学", "関西医科大学", "岐阜大学", "九州大学病院", "京都大学", "久留米大学", "神戸大学", "国立がん研究センター中央病院", "国立病院機構四国がんセンター", "札幌医科大学", "千葉大学", "筑波大学", "東京科学大学", "東京慈恵会医科大学", "東京慈恵会医科大学附属柏病院", "東北大学", "鳥取大学", "富山大学", "長崎大学病院", "名古屋大学", "奈良県立医科大学", "新潟大学大学院 医歯学総合研究科", "浜松医科大学", "原三信病院", "兵庫医科大学", "弘前大学", "北海道大学", "三重大学", "横浜市立大学", "琉球大学", "和歌山県立医科大学", "その他"]

# --- 詳細定義テキスト ---
HELP_EAUIAIC = """
**術中合併症（EAUiaiC）詳細定義**
- **Grade 0**： 介入や手術アプローチの変更を要さず、予定された手術手順からの逸脱がないもの。
- **Grade 1**： 予定された手順において追加・代替処置を要するが、生命を脅かさず、臓器の一部または全摘出を伴わないもの。後遺症を残さない。
- **Grade 2**： 手術アプローチにおいて主要な追加・代替処置を要するが、直ちに生命を脅かすものではないもの。
- **Grade 3**： 予定された手順に加え主要な追加処置を要し、かつ事象が直ちに生命を脅かすものであるが、臓器の一部または全摘出は要さないもの。
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

HELP_CD = """【Clavien-Dindo分類 (術後30日評価)】
* Grade I：正常な術後経過からの逸脱で、薬物療法、外科的治療、内視鏡的治療、IVR治療を要さないもの。（制吐剤、解熱剤、鎮痛剤、利尿剤などは含めない）
* Grade II：制吐剤、解熱剤、鎮痛剤、利尿剤以外の薬物療法を要する。（輸血および中心静脈栄養を含む）
* Grade III：外科的、内視鏡的、または放射線学的介入を要する。
  * IIIa：全身麻酔を要さない治療
  * IIIb：全身麻酔下での治療
* Grade IV：ICU管理を要する、生命を脅かす合併症。
  * IVa：単一の臓器不全
  * IVb：多臓器不全
* Grade V：患者の死亡"""

# --- セッション状態初期化 ---
if 'init_peri_vfinal_sync_v3' not in st.session_state:
    st.session_state['init_peri_vfinal_sync_v3'] = True
    defaults = {
        "facility_name": "選択してください", "patient_id": "", "reporter_email": "",
        "last_evp_date": None, "pre_ae_grade": "選択してください", "ae_detail": "",
        "vital_abnormality": None, "vital_detail": "", "cysto_find": None, "bladder_tumor_tx": "", 
        "wbc_reg": None, "hb_reg": None, "plt_reg": None, "ast_reg": None, "alt_reg": None,
        "ldh_reg": None, "alb_reg": None, "cre_reg": None, "egfr_reg": None, "crp_reg": None,
        "neutro_reg": None, "lympho_reg": None, "mono_reg": None, "eosino_reg": None, "baso_reg": None,
        "op_performed": None, "op_admission_date": None, "op_date": None, "op_discharge_date": None,
        "op_type": "選択してください", "approach": None, "op_completed": None, "op_incomplete_detail": "",
        "no_op_reason": "選択してください", # ここを追加してクラッシュを解消！
        "op_time": None, "bleeding": None, "eau_grade": "選択してください", "eau_detail": "",
        "ln_dissection": None, "ln_range": [],
        "p_histology": "選択してください", "p_histology_other": "", "p_subtype_presence": None, "p_subtype_type": [],
        "p_morphology": "選択してください", "p_size": None, "p_location": [],
        "ypt": "選択してください", "ypn": "選択してください", "ypn_pos_sites": [],
        "p_multiplicity": None, "p_lvi": None, "r0_status": None, "trg_grade": None, "p_eval_failed_reason": "",
        "status_alive": None, "cd_grade": "選択してください", "cd_date_30": None, "cd_detail": "", 
        "final_visit_date_30": None, "death_date_30": None, "death_cause_30": "選択してください",
        "adj_plan": "選択してください", "adj_other_30": "", "adj_start_30": None, "adj_end_30": None, "adj_ongoing_30": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def get_idx(options, value):
    try: return options.index(value)
    except: return 0

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
col_h1, col_h2 = st.columns(2)
with col_h1:
    st.session_state.facility_name = st.selectbox("施設名*", FACILITY_LIST, index=get_idx(FACILITY_LIST, st.session_state.facility_name))
    st.session_state.reporter_email = st.text_input("担当者メールアドレス（控え送付先）*", value=st.session_state.reporter_email)
with col_h2:
    st.session_state.patient_id = st.text_input("研究対象者識別コード*", value=st.session_state.patient_id)

tab1, tab2, tab3, tab4 = st.tabs(["📊 術前・登録時", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

with tab1:
    st.markdown('<div class="juog-header">1. 術前EVP・身体所見</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.last_evp_date = st.date_input("最終EVP投与日", value=st.session_state.last_evp_date)
        ae_opts = ["選択してください", "なし", "Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症", "Grade 4 生命を脅かす", "Grade 5 死亡"]
        st.session_state.pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade*", ae_opts, index=get_idx(ae_opts, st.session_state.pre_ae_grade))
        if st.session_state.pre_ae_grade not in ["選択してください", "なし"]:
            st.session_state.ae_detail = st.text_input("CTCAE詳細*", value=st.session_state.ae_detail)
        # CTCAEリンクの統一配置
        st.markdown("<div style='text-align: right;'><small>参照： <a href='https://jcog.jp/assets/CTCAEv6J_20260301_v28_0.pdf' target='_blank'>CTCAE v6.0 日本語訳 (JCOG版)</a></small></div>", unsafe_allow_html=True)

    with c2:
        st.session_state.vital_abnormality = st.radio("身体所見の異常*", ["異常なし", "異常あり"], index=(0 if st.session_state.vital_abnormality=="異常なし" else 1 if st.session_state.vital_abnormality=="異常あり" else None), horizontal=True)
        if st.session_state.vital_abnormality == "異常あり": st.session_state.vital_detail = st.text_input("異常詳細*", value=st.session_state.vital_detail)
        st.session_state.cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], index=(0 if st.session_state.cysto_find=="腫瘍なし" else 1 if st.session_state.cysto_find=="腫瘍あり" else None), horizontal=True)
        if st.session_state.cysto_find == "腫瘍あり": st.session_state.bladder_tumor_tx = st.text_area("膀胱腫瘍の治療詳細*", value=st.session_state.bladder_tumor_tx)

    st.markdown('<div class="juog-header">2. 術前血液検査</div>', unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        st.session_state.wbc_reg = st.number_input("WBC (/μL)*", value=st.session_state.wbc_reg, step=1.0)
        st.session_state.hb_reg = st.number_input("Hb (g/dL)*", value=st.session_state.hb_reg, step=0.1)
        st.session_state.plt_reg = st.number_input("PLT (x10^4/μL)*", value=st.session_state.plt_reg, step=1.0)
        st.session_state.ast_reg = st.number_input("AST (U/L)*", value=st.session_state.ast_reg, step=1.0)
        st.session_state.alt_reg = st.number_input("ALT (U/L)*", value=st.session_state.alt_reg, step=1.0)
    with bc2:
        st.session_state.ldh_reg = st.number_input("LDH (U/L)*", value=st.session_state.ldh_reg, step=1.0)
        st.session_state.alb_reg = st.number_input("Alb (g/dL)*", value=st.session_state.alb_reg, step=0.1)
        st.session_state.cre_reg = st.number_input("Cre (mg/dL)*", value=st.session_state.cre_reg, step=0.01)
        st.session_state.egfr_reg = st.number_input("eGFR*", value=st.session_state.egfr_reg, step=0.1)
        st.session_state.crp_reg = st.number_input("CRP (mg/dL)*", value=st.session_state.crp_reg, step=0.01)

    st.subheader("白血球分画 (%)")
    f1, f2, f3, f4, f5 = st.columns(5)
    with f1: st.session_state.neutro_reg = st.number_input("Neutro*", value=st.session_state.neutro_reg, step=0.1)
    with f2: st.session_state.lympho_reg = st.number_input("Lympho*", value=st.session_state.lympho_reg, step=0.1)
    with f3: st.session_state.mono_reg = st.number_input("Mono*", value=st.session_state.mono_reg, step=0.1)
    with f4: st.session_state.eosino_reg = st.number_input("Eosino*", value=st.session_state.eosino_reg, step=0.1)
    with f5: st.session_state.baso_reg = st.number_input("Baso*", value=st.session_state.baso_reg, step=0.1)

with tab2:
    st.markdown('<div class="juog-header">4. 手術実施状況</div>', unsafe_allow_html=True)
    st.session_state.op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], index=(0 if st.session_state.op_performed=="実施した" else 1 if st.session_state.op_performed=="実施しなかった" else None), horizontal=True)
    if st.session_state.op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            st.session_state.op_admission_date = st.date_input("入院日*", value=st.session_state.op_admission_date)
            st.session_state.op_date = st.date_input("手術実施日*", value=st.session_state.op_date)
            st.session_state.op_discharge_date = st.date_input("退院日", value=st.session_state.op_discharge_date)
            op_types = ["選択してください", "根治的腎尿管全摘除術", "尿管部分切除術"]
            st.session_state.op_type = st.selectbox("術式*", op_types, index=get_idx(op_types, st.session_state.op_type))
            st.session_state.approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], index=(0 if st.session_state.approach=="開腹" else 1 if st.session_state.approach=="腹腔鏡" else 2 if st.session_state.approach=="ロボット支援" else None), horizontal=True)
            st.session_state.op_completed = st.radio("予定手術が完遂できたか*", ["はい", "いいえ"], index=(0 if st.session_state.op_completed=="はい" else 1 if st.session_state.op_completed=="いいえ" else None), horizontal=True)
            if st.session_state.op_completed == "いいえ": st.session_state.op_incomplete_detail = st.text_area("完遂不能理由*", value=st.session_state.op_incomplete_detail)
        with oc2:
            st.session_state.op_time = st.number_input("手術時間(分)*", value=st.session_state.op_time, step=1)
            st.session_state.bleeding = st.number_input("出血量(mL)*", value=st.session_state.bleeding, step=1)
            eau_opts = ["選択してください", "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"]
            st.session_state.eau_grade = st.selectbox("術中合併症(EAUiaiC)*", eau_opts, index=get_idx(eau_opts, st.session_state.eau_grade), help=HELP_EAUIAIC)
            if st.session_state.eau_grade not in ["選択してください", "Grade 0"]:
                st.session_state.eau_detail = st.text_area("術中合併症詳細*", value=st.session_state.eau_detail)
            st.session_state.ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], index=(0 if st.session_state.ln_dissection=="実施した" else 1 if st.session_state.ln_dissection=="実施しなかった" else None), horizontal=True)
            if st.session_state.ln_dissection == "実施した":
                # 傍大動脈リンパ節を追加
                st.session_state.ln_range = st.multiselect("郭清範囲*", ["腎門部", "下大静脈周囲", "大動脈周囲", "傍大動脈リンパ節", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"], default=st.session_state.ln_range)
    elif st.session_state.op_performed == "実施しなかった":
        noop_opts = ["選択してください", "病勢進行", "G3以上のEVP関連有害事象の発生", "同意撤回", "その他"]
        st.session_state.no_op_reason = st.selectbox("実施しなかった理由*", noop_opts, index=get_idx(noop_opts, st.session_state.no_op_reason))

with tab3:
    if st.session_state.op_performed == "実施した":
        st.markdown('<div class="juog-header">5. 術後病理診断</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            h_opts = ["選択してください", "Urothelial carcinoma", "Squamous cell carcinoma", "Adenocarcinoma", "評価不能", "Other"]
            st.session_state.p_histology = st.selectbox("組織型*", h_opts, index=get_idx(h_opts, st.session_state.p_histology))
            if st.session_state.p_histology == "Other":
                st.session_state.p_histology_other = st.text_input("詳細(Other)", value=st.session_state.p_histology_other)
            st.session_state.p_subtype_presence = st.radio("亜型の有無*", ["なし", "あり"], index=(0 if st.session_state.p_subtype_presence=="なし" else 1 if st.session_state.p_subtype_presence=="あり" else None), horizontal=True)
            if st.session_state.p_subtype_presence == "あり":
                st.session_state.p_subtype_type = st.multiselect("亜型の種類*", ["Nest型", "Micropapillary型", "Plasmacytoid型", "Sarcomatoid変化", "Lymphoepithelioma-like型", "Clear cell型", "Lipid-rich型", "Trophoblastic分化", "Glandular分化", "Squamous分化"], default=st.session_state.p_subtype_type)
            m_opts = ["選択してください", "乳頭状", "非乳頭状", "結節状", "浸潤状", "平坦状", "評価不能", "その他"]
            st.session_state.p_morphology = st.selectbox("形態*", m_opts, index=get_idx(m_opts, st.session_state.p_morphology))
            st.session_state.p_size = st.number_input("最大径(mm)*", value=st.session_state.p_size, step=0.1)
            st.session_state.p_location = st.multiselect("部位*", ["上腎杯", "中腎杯", "下腎杯", "腎盂", "UPJ", "上部尿管", "中部尿管", "下部尿管", "VUJ"], default=st.session_state.p_location)
        with pc2:
            st.session_state.ypt = st.selectbox("ypT*", ["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4", "評価不能"], index=get_idx(["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4", "評価不能"], st.session_state.ypt))
            st.session_state.ypn = st.selectbox("ypN*", ["選択してください", "ypN0", "ypN1", "ypN2", "評価不能"], index=get_idx(["選択してください", "ypN0", "ypN1", "ypN2", "評価不能"], st.session_state.ypn))
            if st.session_state.ypn not in ["ypN0", "選択してください", "評価不能"]:
                # 傍大動脈リンパ節を追加（病理側）
                st.session_state.ypn_pos_sites = st.multiselect("陽性部位*", ["腎門部", "下大静脈周囲", "大動脈周囲", "傍大動脈リンパ節", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"], default=st.session_state.ypn_pos_sites)
            st.session_state.p_multiplicity = st.radio("多発性*", ["単発", "多発"], index=(0 if st.session_state.p_multiplicity=="単発" else 1 if st.session_state.p_multiplicity=="多発" else None), horizontal=True)
            st.session_state.p_lvi = st.radio("LVI*", ["なし", "あり", "評価不能"], index=None, horizontal=True)
            st.session_state.r0_status = st.radio("R0切除*", ["陰性", "陽性", "評価不能"], index=None, horizontal=True)
            trg_opts = ["TRG 1", "TRG 2", "TRG 3", "評価不能"]
            st.session_state.trg_grade = st.radio("TRG分類*", trg_opts, index=(trg_opts.index(st.session_state.trg_grade) if st.session_state.trg_grade in trg_opts else None), help=HELP_TRG)
        if "評価不能" in [st.session_state.p_histology, st.session_state.ypt, st.session_state.ypn]:
            st.session_state.p_eval_failed_reason = st.text_area("病理評価不能理由*", value=st.session_state.p_eval_failed_reason)
    else: st.write("手術未実施のため入力項目はありません。")

with tab4:
    st.markdown('<div class="juog-header">6. 術後30日目評価</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    
    # --- 左側（Column 1）: 合併症 ---
    with sc1:
        if st.session_state.op_performed == "実施した":
            cd_opts = ["選択してください", "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"]
            st.session_state.cd_grade = st.selectbox("術後合併症 (Clavien-Dindo分類)*", cd_opts, index=get_idx(cd_opts, st.session_state.cd_grade), help=HELP_CD)
            if st.session_state.cd_grade not in ["選択してください", "Grade 0"]:
                st.session_state.cd_date_30 = st.date_input("合併症の発現日*", value=st.session_state.cd_date_30)
                st.session_state.cd_detail = st.text_area("外科的合併症の詳細内容*", value=st.session_state.cd_detail)
        else: st.session_state.cd_grade = "N/A"

    # --- 右側（Column 2）: 生存状況および治療予定 ---
    with sc2:
        st.session_state.status_alive = st.radio("生存状況 (術後30日時点)*", ["生存", "死亡"], index=(0 if st.session_state.status_alive=="生存" else 1 if st.session_state.status_alive=="死亡" else None), horizontal=True)
        
        if st.session_state.status_alive == "生存":
            st.session_state.final_visit_date_30 = st.date_input("最終生存確認日*", value=st.session_state.final_visit_date_30)
            st.markdown("---")
            st.markdown("**【今後の予定】**")
            adj_opts = ["選択してください", "無治療（経過観察）", "EVP継続投与", "ペムブロ単剤維持", "ニボルマブ単剤（術後補助療法）", "GC療法（術後補助療法）", "GCarbo療法（術後補助療法）", "放射線治療", "治験・その他薬物療法", "その他"]
            st.session_state.adj_plan = st.selectbox("術後補助療法・今後の治療予定*", adj_opts, index=get_idx(adj_opts, st.session_state.adj_plan))
            
            # Swimmer Plot 用の日程収集ロジック
            if st.session_state.adj_plan not in ["選択してください", "無治療（経過観察）"]:
                if st.session_state.adj_plan in ["治験・その他薬物療法", "その他"]:
                    st.session_state.adj_other_30 = st.text_input("治療の詳細*", value=st.session_state.adj_other_30)
                
                ax1, ax2 = st.columns(2)
                st.session_state.adj_start_30 = ax1.date_input(f"{st.session_state.adj_plan} 開始日*", value=st.session_state.adj_start_30, key="adj_start_30")
                st.session_state.adj_ongoing_30 = ax2.checkbox("現在も継続中", value=st.session_state.adj_ongoing_30, key="adj_ongoing_30")
                if not st.session_state.adj_ongoing_30:
                    st.session_state.adj_end_30 = ax2.date_input(f"{st.session_state.adj_plan} 終了日*", value=st.session_state.adj_end_30, key="adj_end_30")
                else:
                    st.session_state.adj_end_30 = None
            
        elif st.session_state.status_alive == "死亡":
            st.session_state.death_date_30 = st.date_input("死亡日*", value=st.session_state.death_date_30)
            dc_opts = ["選択してください", "癌死", "治療関連死", "他病死", "不明"]
            st.session_state.death_cause_30 = st.selectbox("死因*", dc_opts, index=get_idx(dc_opts, st.session_state.death_cause_30))

    st.divider()

    def f_num(val): return str(val) if (val is not None and val != 0 and val != 0.0) else "N/A"

    if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
        h_errors = []
        d = st.session_state
        if d.facility_name == "選択してください": h_errors.append("・施設名")
        if not d.patient_id: h_errors.append("・識別コード")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", d.reporter_email): h_errors.append("・有効なメールアドレス")
        if d.status_alive is None: h_errors.append("・生存状況")
        if d.op_performed is None: h_errors.append("・手術の実施有無")
        if d.op_performed == "実施しなかった" and d.no_op_reason == "選択してください": h_errors.append("・実施しなかった理由")
        
        # CD分類と補助療法のバリデーション
        if d.op_performed == "実施した":
            if d.cd_grade == "選択してください": h_errors.append("・Clavien-Dindo分類")
            if d.cd_grade not in ["選択してください", "Grade 0", "N/A"]:
                if not d.cd_date_30: h_errors.append("・合併症の発現日")
                if not d.cd_detail: h_errors.append("・外科的合併症の詳細")
                
        if d.status_alive == "生存":
            if d.adj_plan == "選択してください": h_errors.append("・今後の予定(術後補助療法等)")
            if d.adj_plan not in ["選択してください", "無治療（経過観察）"]:
                if not d.adj_start_30: h_errors.append("・治療の開始日")
                if not d.adj_ongoing_30 and not d.adj_end_30: h_errors.append("・治療の終了日")

        elif d.status_alive == "生存" and d.cd_grade == "Grade V": h_errors.append("・生存なのにCD Grade Vです")
        elif d.status_alive == "死亡" and d.cd_grade != "Grade V": h_errors.append("・死亡なのにCD Grade V以外です")

        if h_errors:
            st.error("入力不備があります。修正してください：\n" + "\n".join(h_errors))
        else:
            rep = f"【JUOG 周術期報告】\n施設: {d.facility_name}\nID: {d.patient_id}\n生存: {d.status_alive}\n主要採血: WBC:{f_num(d.wbc_reg)}, Hb:{f_num(d.hb_reg)}, Cre:{f_num(d.cre_reg)}"
            if send_email(rep, d.patient_id, d.facility_name, d.reporter_email):
                st.success(f"正常送信されました。{d.reporter_email} 宛に控えを送付しました。")
                st.balloons()
