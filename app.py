import streamlit as st
import json
from datetime import date, datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re

# --- ページ設定 ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF", layout="wide")

# --- JUOG専用デザインCSS (80pxの余白を死守) ---
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

# --- ヘルプテキスト定義 (死守) ---
HELP_EAUIAIC = """**術中合併症（EAUiaiC）詳細定義**
- Grade 0： 逸脱なし。
- Grade 1： 追加処置要すが生命に別状なし。後遺症なし。
- Grade 2： 主要な追加・代替処置を要する。
- Grade 3： 手順に加え主要な追加処置を要し、かつ事象が生命を脅かすもの。
- Grade 4： 重大な結果（4A: 臓器摘出、4B: 手術完了不能）。
- Grade 5： 5A: 部位間違い、5B: 術中死亡。"""

HELP_TRG = """**TRG 分類**
- TRG 1：Complete Response (生存細胞なし)
- TRG 2：Strong Response (生存細胞50%未満)
- TRG 3：Weak/No Response (生存細胞50%以上)"""

HELP_CD = """**Clavien-Dindo 分類**
- Grade I：薬物・外科治療不要。
- Grade II：制吐剤・解熱剤等以外の薬物療法。
- Grade III：外科・内視鏡的治療等。
- Grade IV：生命を脅かす合併症（ICU管理）。
- Grade V：死亡。"""

# --- セッション状態初期化 (全てのAttributeErrorを防止) ---
if 'init_peri_done' not in st.session_state:
    st.session_state['init_peri_done'] = True
    defaults = {
        "facility_name": "選択してください", "patient_id": "", "reporter_email": "",
        "last_evp_date": None, "pre_ae_grade": "選択してください", "ae_detail": "なし",
        "vital_abnormality": None, "vital_detail": "N/A", "cysto_find": None, "bladder_tumor_tx": "N/A", 
        "wbc_90": None, "hb_90": None, "plt_90": None, "ast_90": None, "alt_90": None,
        "ldh_90": None, "alb_90": None, "cre_90": None, "egfr_90": None, "crp_90": None,
        "neutro_90": None, "lympho_90": None, "mono_90": None, "eosino_90": None, "baso_90": None,
        "op_performed": None, "op_date": None, "op_admission_date": None, "op_discharge_date": None,
        "op_type": "選択してください", "approach": None, "op_completed": None, "op_incomplete_detail": "N/A",
        "op_time": None, "bleeding": None, "eau_grade": "選択してください", "eau_detail": "N/A",
        "ln_dissection": None, "ln_range": [],
        "p_histology": "選択してください", "p_histology_other": "N/A", "p_subtype_presence": None, "p_subtype_type": [],
        "p_morphology": "選択してください", "p_size": None, "p_location": [],
        "ypt": "選択してください", "ypn": "選択してください", "ypn_pos_sites": [],
        "p_multiplicity": None, "p_lvi": None, "r0_status": None, "trg_grade": None, "p_eval_failed_reason": "",
        "cd_grade": "選択してください", "cd_detail": "N/A", "adj_plan": "選択してください", "adj_other_detail": "", "adj_date": None,
        "status_alive": None, "final_visit_date_30": None, "death_date_30": None, "death_cause_30": "選択してください",
        "do_send": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

def send_email(report_content, pid, facility, user_email=None):
    try:
        mail_user = st.secrets["email"]["user"]; mail_pass = st.secrets["email"]["pass"]
        to_addrs = ["urosec@kmu.ac.jp", "yoshida.tks@kmu.ac.jp"]
        if user_email: to_addrs.append(user_email)
        msg = MIMEMultipart(); msg['From'] = mail_user; msg['To'] = ", ".join(to_addrs)
        msg['Subject'] = f"【JUOG 周術期】（{facility} / ID: {pid}）"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_pass); server.send_message(msg); server.quit()
        return True
    except: return False

st.title("JUOG UTUC_Consolidative 周術期CRF")

# --- 共通ヘッダー ---
col_h1, col_h2 = st.columns(2)
with col_h1:
    idx_fac = FACILITY_LIST.index(st.session_state.facility_name) if st.session_state.facility_name in FACILITY_LIST else 0
    st.session_state.facility_name = st.selectbox("施設名*", FACILITY_LIST, index=idx_fac)
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
        idx_ae = ae_opts.index(st.session_state.pre_ae_grade) if st.session_state.pre_ae_grade in ae_opts else 0
        st.session_state.pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade*", ae_opts, index=idx_ae)
        if st.session_state.pre_ae_grade not in ["選択してください", "なし"]:
            st.session_state.ae_detail = st.text_input("CTCAE詳細*", value=st.session_state.ae_detail)
    with c2:
        st.session_state.vital_abnormality = st.radio("身体所見の異常*", ["異常なし", "異常あり"], index=(0 if st.session_state.vital_abnormality=="異常なし" else 1 if st.session_state.vital_abnormality=="異常あり" else None), horizontal=True)
        if st.session_state.vital_abnormality == "異常あり": st.session_state.vital_detail = st.text_input("異常詳細*", value=st.session_state.vital_detail)
        st.session_state.cysto_find = st.radio("膀胱鏡所見*", ["腫瘍なし", "腫瘍あり"], index=(0 if st.session_state.cysto_find=="腫瘍なし" else 1 if st.session_state.cysto_find=="腫瘍あり" else None), horizontal=True)
        if st.session_state.cysto_find == "腫瘍あり": st.session_state.bladder_tumor_tx = st.text_area("膀胱腫瘍の治療詳細*", value=st.session_state.bladder_tumor_tx)

    st.markdown('<div class="juog-header">2. 術前血液検査</div>', unsafe_allow_html=True)
    bc1, bc2 = st.columns(2)
    with bc1:
        st.session_state.wbc_90 = st.number_input("WBC (/μL)*", value=st.session_state.wbc_90, step=1.0)
        st.session_state.hb_90 = st.number_input("Hb (g/dL)*", value=st.session_state.hb_90, step=0.1)
        st.session_state.plt_90 = st.number_input("PLT (x10^4/μL)*", value=st.session_state.plt_90, step=1.0)
        st.session_state.ast_90 = st.number_input("AST (U/L)*", value=st.session_state.ast_90, step=1.0)
        st.session_state.alt_90 = st.number_input("ALT (U/L)*", value=st.session_state.alt_90, step=1.0)
    with bc2:
        st.session_state.ldh_90 = st.number_input("LDH (U/L)*", value=st.session_state.ldh_90, step=1.0)
        st.session_state.alb_90 = st.number_input("Alb (g/dL)*", value=st.session_state.alb_90, step=0.1)
        st.session_state.cre_90 = st.number_input("Cre (mg/dL)*", value=st.session_state.cre_90, step=0.01)
        st.session_state.egfr_90 = st.number_input("eGFR*", value=st.session_state.egfr_90, step=0.1)
        st.session_state.crp_90 = st.number_input("CRP (mg/dL)*", value=st.session_state.crp_90, step=0.01)

    st.subheader("白血球分画 (%)")
    f1, f2, f3, f4, f5 = st.columns(5)
    with f1: st.session_state.neutro_90 = st.number_input("Neutro*", value=st.session_state.neutro_90, step=0.1)
    with f2: st.session_state.lympho_90 = st.number_input("Lympho*", value=st.session_state.lympho_90, step=0.1)
    with f3: st.session_state.mono_90 = st.number_input("Mono*", value=st.session_state.mono_90, step=0.1)
    with f4: st.session_state.eosino_90 = st.number_input("Eosino*", value=st.session_state.eosino_90, step=0.1)
    with f5: st.session_state.baso_90 = st.number_input("Baso*", value=st.session_state.baso_90, step=0.1)

with tab2:
    st.markdown('<div class="juog-header">4. 手術実施状況</div>', unsafe_allow_html=True)
    st.session_state.op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], index=(0 if st.session_state.op_performed=="実施した" else 1 if st.session_state.op_performed=="実施しなかった" else None), horizontal=True)
    if st.session_state.op_performed == "実施した":
        oc1, oc2 = st.columns(2)
        with oc1:
            st.session_state.op_admission_date = st.date_input("入院日*", value=st.session_state.op_admission_date)
            st.session_state.op_date = st.date_input("手術実施日*", value=st.session_state.op_date)
            st.session_state.op_discharge_date = st.date_input("退院(予定)日", value=st.session_state.op_discharge_date)
            opts_type = ["選択してください", "根治的腎尿管全摘除術", "尿管部分切除術"]
            st.session_state.op_type = st.selectbox("術式*", opts_type, index=opts_type.index(st.session_state.op_type))
            st.session_state.approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], index=(0 if st.session_state.approach=="開腹" else 1 if st.session_state.approach=="腹腔鏡" else 2 if st.session_state.approach=="ロボット支援" else None), horizontal=True)
            st.session_state.op_completed = st.radio("完遂できたか*", ["はい", "いいえ"], index=(0 if st.session_state.op_completed=="はい" else 1 if st.session_state.op_completed=="いいえ" else None), horizontal=True)
            if st.session_state.op_completed == "いいえ": st.session_state.op_incomplete_detail = st.text_area("完遂不能理由*", value=st.session_state.op_incomplete_detail)
        with oc2:
            st.session_state.op_time = st.number_input("手術時間(分)*", value=st.session_state.op_time, step=1)
            st.session_state.bleeding = st.number_input("出血量(mL)*", value=st.session_state.bleeding, step=1)
            opts_eau = ["選択してください", "Grade 0", "Grade 1", "Grade 2", "Grade 3", "Grade 4A", "Grade 4B", "Grade 5A", "Grade 5B"]
            st.session_state.eau_grade = st.selectbox("術中合併症(EAUiaiC)*", opts_eau, index=opts_eau.index(st.session_state.eau_grade), help=HELP_EAUIAIC)
            if st.session_state.eau_grade not in ["選択してください", "Grade 0"]:
                st.session_state.eau_detail = st.text_area("術中合併症詳細*", value=st.session_state.eau_detail)
            st.session_state.ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], index=(0 if st.session_state.ln_dissection=="実施した" else 1 if st.session_state.ln_dissection=="実施しなかった" else None), horizontal=True)
            if st.session_state.ln_dissection == "実施した":
                st.session_state.ln_range = st.multiselect("郭清範囲*", ["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"], default=st.session_state.ln_range)
    elif st.session_state.op_performed == "実施しなかった":
        st.session_state.no_op_reason = st.selectbox("未実施理由*", ["選択してください", "病勢進行", "G3以上有害事象", "同意撤回", "その他"])

with tab3:
    if st.session_state.op_performed == "実施した":
        st.markdown('<div class="juog-header">5. 術後病理診断</div>', unsafe_allow_html=True)
        pc1, pc2 = st.columns(2)
        with pc1:
            h_opts = ["選択してください", "Urothelial carcinoma", "Squamous cell carcinoma", "Adenocarcinoma", "評価不能", "Other"]
            st.session_state.p_histology = st.selectbox("組織型*", h_opts, index=h_opts.index(st.session_state.p_histology))
            if st.session_state.p_histology == "Other": st.session_state.p_histology_other = st.text_input("詳細(Other)", value=st.session_state.p_histology_other)
            st.session_state.p_subtype_presence = st.radio("亜型の有無*", ["なし", "あり"], index=(0 if st.session_state.p_subtype_presence=="なし" else 1 if st.session_state.p_subtype_presence=="あり" else None), horizontal=True)
            if st.session_state.p_subtype_presence == "あり":
                st.session_state.p_subtype_type = st.multiselect("亜型の種類*", ["Nest型", "Micropapillary型", "Plasmacytoid型", "Sarcomatoid変化", "Lymphoepithelioma-like型", "Clear cell型", "Lipid-rich型", "Trophoblastic分化", "Glandular分化", "Squamous分化"], default=st.session_state.p_subtype_type)
            st.session_state.p_morphology = st.selectbox("形態*", ["選択してください", "乳頭状", "非乳頭状", "結節状", "浸潤状", "平坦状", "評価不能", "その他"], index=0)
            st.session_state.p_size = st.number_input("最大径(mm)*", value=st.session_state.p_size, step=0.1)
            st.session_state.p_location = st.multiselect("部位*", ["上腎杯", "中腎杯", "下腎杯", "腎盂", "UPJ", "上部尿管", "中部尿管", "下部尿管", "VUJ"], default=st.session_state.p_location)
        with pc2:
            st.session_state.ypt = st.selectbox("ypT*", ["選択してください", "ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4", "評価不能"], index=0)
            st.session_state.ypn = st.selectbox("ypN*", ["選択してください", "ypN0", "ypN1", "ypN2", "評価不能"], index=0)
            if st.session_state.ypn not in ["ypN0", "選択してください", "評価不能"]:
                st.session_state.ypn_pos_sites = st.multiselect("陽性部位*", ["腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"], default=st.session_state.ypn_pos_sites)
            st.session_state.p_multiplicity = st.radio("多発性*", ["単発", "多発"], index=(0 if st.session_state.p_multiplicity=="単発" else 1 if st.session_state.p_multiplicity=="多発" else None), horizontal=True)
            st.session_state.p_lvi = st.radio("LVI*", ["なし", "あり", "評価不能"], index=None, horizontal=True)
            st.session_state.r0_status = st.radio("R0切除*", ["陰性", "陽性", "評価不能"], index=None, horizontal=True)
            trg_opts = ["TRG 1", "TRG 2", "TRG 3", "評価不能"]
            st.session_state.trg_grade = st.radio("TRG分類*", trg_opts, index=None, help=HELP_TRG)
        if "評価不能" in [st.session_state.p_histology, st.session_state.ypt, st.session_state.ypn]:
            st.session_state.p_eval_failed_reason = st.text_area("病理評価不能理由*", value=st.session_state.p_eval_failed_reason)
    else: st.write("手術未実施のため項目なし")

with tab4:
    st.markdown('<div class="juog-header">6. 術後30日目評価</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns(2)
    with sc1:
        # 生存状況を左側に死守
        st.session_state.status_alive = st.radio("生存状況 (術後30日時点)*", ["生存", "死亡"], index=(0 if st.session_state.status_alive=="生存" else 1 if st.session_state.status_alive=="死亡" else None), horizontal=True)
    with sc2:
        if st.session_state.op_performed == "実施した":
            cd_opts = ["選択してください", "Grade 0", "Grade I", "Grade II", "Grade IIIa", "Grade IIIb", "Grade IVa", "Grade IVb", "Grade V"]
            st.session_state.cd_grade = st.selectbox("術後合併症 (CD分類)*", cd_opts, index=cd_opts.index(st.session_state.cd_grade), help=HELP_CD)
            if st.session_state.cd_grade not in ["選択してください", "Grade 0"]:
                st.session_state.cd_detail = st.text_area("CD詳細*", value=st.session_state.cd_detail)
        else: st.session_state.cd_grade = "N/A"

    sd1, sd2 = st.columns(2)
    with sd1:
        if st.session_state.status_alive == "生存":
            st.session_state.final_visit_date_30 = st.date_input("最終生存確認日*", value=st.session_state.final_visit_date_30)
        elif st.session_state.status_alive == "死亡":
            st.session_state.death_date_30 = st.date_input("死亡日*", value=st.session_state.death_date_30)
            dc_opts = ["選択してください", "癌死", "治療関連死", "他病死", "不明"]
            st.session_state.death_cause_30 = st.selectbox("死因*", dc_opts, index=dc_opts.index(st.session_state.death_cause_30))
    with sd2:
        # 生存時のみ今後の予定を表示 (死亡時は消える)
        if st.session_state.status_alive == "生存":
            st.markdown("**【今後の予定】**")
            adj_opts = ["選択してください", "無治療（経過観察）", "EVP継続投与", "ペムブロ単剤維持", "その他"]
            st.session_state.adj_plan = st.selectbox("治療予定*", adj_opts, index=adj_opts.index(st.session_state.adj_plan))
            st.session_state.adj_date = st.date_input("次回治療開始日*", value=st.session_state.adj_date)

    st.divider()

    def f_num(val): return str(val) if (val is not None and val != 0 and val != 0.0) else "N/A"

    if st.button("🚀 事務局へ確定送信", type="primary", use_container_width=True):
        h_errors = []
        d = st.session_state
        if d.facility_name == "選択してください": h_errors.append("・施設名")
        if not d.patient_id: h_errors.append("・識別コード")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", d.reporter_email): h_errors.append("・有効なメールアドレス")
        if d.status_alive is None: h_errors.append("・生存状況")
        elif d.status_alive == "生存" and d.cd_grade == "Grade V": h_errors.append("・生存なのにCD Grade Vです")
        elif d.status_alive == "死亡" and d.cd_grade != "Grade V": h_errors.append("・死亡なのにCD Grade V以外です")

        if h_errors:
            st.error("修正してください：\n" + "\n".join(h_errors))
        else:
            rep = f"【JUOG 周術期報告】\n施設: {d.facility_name}\nID: {d.patient_id}\n生存: {d.status_alive}\n主要採血: WBC:{f_num(d.wbc_90)}, Hb:{f_num(d.hb_90)}, Cre:{f_num(d.cre_90)}"
            if send_email(rep, d.patient_id, d.facility_name, d.reporter_email):
                st.success(f"正常送信されました。{d.reporter_email} 宛に控えを送付しました。")
                st.balloons()
