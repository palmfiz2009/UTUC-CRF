import streamlit as st
from datetime import date, datetime

# --- デザイン設定 (前回準拠) ---
st.set_page_config(page_title="JUOG UTUC_Trial CRF (30-day)", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F8FAFC; }
    .block-container { padding-top: 1.5rem !important; max-width: 1100px !important; margin: auto; padding-bottom: 5rem !important; }
    h1 { font-size: 24px !important; color: #0F172A; text-align: center; margin-bottom: 20px !important; font-weight: 800; border-bottom: 3px solid #1E3A8A; padding-bottom: 10px; }
    h2 { font-size: 16px !important; color: #FFFFFF !important; background-color: #1E3A8A !important; padding: 8px 15px !important; border-radius: 5px !important; margin-top: 20px !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #E2E8F0; border-radius: 5px 5px 0 0; padding: 10px 20px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #1E3A8A !important; color: white !important; }
    .help-box { background-color: #F1F5F9; padding: 15px; border-radius: 8px; border-left: 5px solid #64748B; font-size: 0.85rem; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("JUOG UTUC_Trial：術前・術中・術後30日目 CRF")

# --- ヘルプ情報の定義 ---
HELP_EAUIAIC = """
**EAUiaiC 分類詳細**
- **Grade 0**: 逸脱なし。患者への影響なし。
- **Grade 1**: 追加・代替処置を要するが、生命を脅かさず後遺症なし。
- **Grade 2**: 主要な追加処置を要する。後遺症の可能性あり。
- **Grade 3**: 生命を脅かす事態だが臓器摘出は不要。
- **Grade 4A**: 臓器の一部または全摘出を要する。
- **Grade 4B**: 完遂不能または予定外ストーマ造設。
- **Grade 5A**: 部位・側・患者間違い。
- **Grade 5B**: 術中死亡。
"""

HELP_CD = """
**Clavien-Dindo 分類詳細**
- **Grade I**: 薬剤、手術、内視鏡等の介入不要。
- **Grade II**: 薬物療法（輸血、中心静脈栄養含む）を要する。
- **Grade IIIa**: 全身麻酔を要さない外科、内視鏡的介入。
- **Grade IIIb**: 全身麻酔下での介入。
- **Grade IVa/b**: ICU管理を要する単一/多臓器不全。
- **Grade V**: 死亡。
"""

# --- 入力フォーム ---
with st.container():
    # 基本情報
    col_id1, col_id2 = st.columns([1, 1])
    with col_id1:
        patient_id = st.text_input("研究対象者識別コード*", help="kintone: 文字列__1行__0")
    with col_id2:
        status_alive = st.radio("生存状況*", ["生存", "死亡"], horizontal=True, help="kintone: ラジオボタン_13")

    tab_pre, tab_op, tab_path, tab_post = st.tabs(["📊 術前データ", "🔪 手術記録", "🔬 病理結果", "📋 30日目評価"])

    # --- タブ1: 術前データ ---
    with tab_pre:
        st.subheader("術前EVP・身体所見")
        c1, c2 = st.columns(2)
        with c1:
            last_evp_date = st.date_input("最終EVP投与日", value=None, help="kintone: 日付_0")
            pre_ae_grade = st.selectbox("術前EVP関連AE: CTCAE grade", ["Grade 1 軽症", "Grade 2 中等症", "Grade 3 重症", "Grade 4 生命を脅かす", "Grade 5 死亡"], help="kintone: ラジオボタン_3")
        with c2:
            vital_abnormality = st.radio("術前身体所見およびバイタルサインの異常", ["異常なし", "異常あり"], horizontal=True, help="kintone: ラジオボタン_4")
            if vital_abnormality == "異常あり":
                vital_detail = st.text_input("異常の詳細", help="kintone: 文字列__1行__5")

        st.subheader("術前血液検査")
        bc1, bc2, bc3, bc4 = st.columns(4)
        with bc1:
            wbc = st.number_input("WBC (/μL)", format="%d", help="kintone: 数値_2")
            hb = st.number_input("Hb (g/dL)", format="%.1f", help="kintone: 数値_3")
            plt = st.number_input("PLT (/μL)", format="%d", help="kintone: 数値_19")
        with bc2:
            ast = st.number_input("AST (U/L)", format="%d", help="kintone: 数値_5")
            alt = st.number_input("ALT (U/L)", format="%d", help="kintone: 数値_6")
            ldh = st.number_input("LDH (U/L)", format="%d", help="kintone: 数値_11")
        with bc3:
            alb = st.number_input("Alb (g/dL)", format="%.1f", help="kintone: 数値_9")
            bun = st.number_input("BUN (mg/dL)", format="%d", help="kintone: 数値_8")
            cre = st.number_input("Cre (mg/dL)", format="%.2f", help="kintone: 数値_12")
        with bc4:
            egfr = st.number_input("eGFR (mL/min/1.73m²)", format="%.1f", help="kintone: 数値_13")
            crp = st.number_input("CRP (mg/dL)", format="%.2f", help="kintone: 数値_18")

        with st.expander("白血球分画 (%)"):
            f1, f2, f3, f4, f5 = st.columns(5)
            neutro = f1.number_input("Neutro", format="%.1f")
            lympho = f2.number_input("Lympho", format="%.1f")
            mono = f3.number_input("Mono", format="%.1f")
            eosino = f4.number_input("Eosino", format="%.1f")
            baso = f5.number_input("Baso", format="%.1f")
            diff_total = neutro + lympho + mono + eosino + baso
            if diff_total > 0:
                st.caption(f"分画合計: {diff_total:.1f}% (通常は100%前後)")

    # --- タブ2: 手術記録 ---
    with tab_op:
        op_performed = st.radio("手術の実施*", ["実施した", "実施しなかった"], horizontal=True, help="kintone: ラジオボタン_0")
        
        if op_performed == "実施した":
            c_op1, c_op2 = st.columns(2)
            with c_op1:
                op_date = st.date_input("手術実施日*", value=None, help="kintone: 日付")
                # 待機期間計算
                if op_date and last_evp_date:
                    wait_weeks = (op_date - last_evp_date).days / 7
                    st.metric("術前待機期間", f"{wait_weeks:.1f} 週間")
                
                op_type = st.selectbox("術式*", ["根治的腎尿管全摘除術", "尿管部分切除術"], help="kintone: ラジオボタン_17")
                approach = st.radio("アプローチ*", ["開腹", "腹腔鏡", "ロボット支援"], horizontal=True, help="kintone: ラジオボタン_1")
            
            with c_op2:
                op_time = st.number_input("手術時間 (分)", min_value=0, help="kintone: 数値_0")
                bleeding = st.number_input("出血量 (mL)", min_value=0, help="kintone: 数値_1")
                
                with st.popover("術中合併症 (EAUiaiC) の分類を確認"):
                    st.markdown(HELP_EAUIAIC)
                eau_grade = st.selectbox("術中合併症(EAUiaiC)*", [
                    "Grade 0：逸脱なし・影響なし", "Grade 1：追加処置あり・後遺症なし", 
                    "Grade 2：主要な追加処置・後遺症の可能性", "Grade 3：生命の危険あり・臓器摘出なし",
                    "Grade 4A：臓器の一部または全摘出", "Grade 4B：完遂不能・予定外ストーマ",
                    "Grade 5A：患者/部位/術式の間違い", "Grade 5B：術中死亡"
                ], help="kintone: ドロップダウン_0")

            st.subheader("リンパ節郭清")
            l1, l2 = st.columns([1, 2])
            with l1:
                ln_dissection = st.radio("リンパ節郭清*", ["実施した", "実施しなかった"], horizontal=True, help="kintone: ラジオボタン_2")
            with l2:
                if ln_dissection == "実施した":
                    ln_range = st.multiselect("リンパ節郭清範囲", [
                        "腎門部", "下大静脈周囲", "大動脈周囲", "大動脈静脈間", 
                        "総腸骨動脈周囲", "外腸骨動脈周囲", "内腸骨動脈周囲", "閉鎖", "その他"
                    ], help="kintone: チェックボックス")

        else:
            no_op_reason = st.selectbox("実施しなかった理由", ["病勢進行", "有害事象の発生", "同意撤回", "その他"], help="kintone: ドロップダウン")

    # --- タブ3: 病理結果 ---
    with tab_path:
        st.subheader("病理診断 (ypTNM)")
        pa1, pa2, pa3 = st.columns(3)
        with pa1:
            ypt = st.selectbox("ypT分類*", ["ypT0", "ypTa", "ypTis", "ypT1", "ypT2", "ypT3", "ypT4"], help="kintone: ラジオボタン_5")
        with pa2:
            ypn = st.selectbox("ypN分類*", ["ypN0", "ypN1", "ypN2"], help="kintone: ラジオボタン_6")
        with pa3:
            r0_res = st.radio("R0切除_断端陰性*", ["陰性", "陽性"], horizontal=True, help="kintone: ラジオボタン_7")
        
        trg = st.radio("病理学的治療効果（TRG分類）*", [
            "TRG 1 : Complete Response （pCR）", 
            "TRG 2： Strong Response", 
            "TRG 3： Weak and No Response"
        ], help="kintone: ラジオボタン_8")

    # --- タブ4: 30日目評価 ---
    with tab_post:
        st.subheader("術後30日目の安全性と今後")
        
        with st.popover("Clavien-Dindo 分類を確認"):
            st.markdown(HELP_CD)
            
        cd_grade = st.selectbox("術後合併症_Clavien-Dindo分類*", [
            "Grade 0", "Grade I：治療を要さない", "Grade II：薬物・輸血等を要する",
            "Grade IIIa：介入（全麻なし）", "Grade IIIb：介入（全麻下）",
            "Grade IVa：単一臓器不全", "Grade IVb：多臓器不全", "Grade V：死亡"
        ], help="kintone: ラジオボタン_10")
        
        cd_detail = st.text_area("Clavien-Dindo分類 (詳細)", help="kintone: 文字列__1行_")

        st.divider()
        adj_plan = st.selectbox("術後補助療法の予定（または実施中）*", [
            "無治療（経過観察）", "EVP継続投与（予定回数の完遂まで）", 
            "ペムブロリズマブ単剤維持療法", "ニボルマブ単剤療法",
            "プラチナ製剤併用化学療法", "その他"
        ], help="kintone: ラジオボタン_9")
        adj_date = st.date_input("予定（または実施）日付", value=None, help="kintone: 日付_2")

# --- 保存ボタン ---
st.divider()
if st.button("CRF入力を完了し、レポートを生成する", type="primary", use_container_width=True):
    st.success("レポートを生成しました。内容を確認し、事務局へ送信してください。")
    # ここにレポート生成ロジック
