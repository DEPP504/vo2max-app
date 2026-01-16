import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 試算表與設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/16niyheTwWVts9A6aKRiOx2OpJypQAIeodE08TN9cERU/edit?usp=sharing"

def push_to_sheets(conn, run_date, final_vo2, run_type, gct, v_osc):
    """資料寫入函數"""
    try:
        existing_data = conn.read(spreadsheet=SHEET_URL)
        new_entry = pd.DataFrame({
            "日期": [str(run_date)],
            "VO2_Max": [final_vo2],
            "類型": [run_type],
            "GCT": [gct],
            "垂直振幅": [v_osc]
        })
        updated_df = pd.concat([existing_data, new_entry], ignore_index=True)
        conn.update(spreadsheet=SHEET_URL, data=updated_df)
        return True, "✅ 數據已成功寫入 Google Sheets！"
    except Exception as e:
        return False, f"❌ 存檔失敗：{e}"

# --- 介面初始化 ---
st.set_page_config(page_title="AI 全能運動教練", layout="wide")
st.title("🚀 AI 運動表現分析與進步預測系統")

if 'weight' not in st.session_state: st.session_state.weight = 80.0
if 'max_hr' not in st.session_state: st.session_state.max_hr = 190
if 'rest_hr' not in st.session_state: st.session_state.rest_hr = 55
if 'last_analysis' not in st.session_state: st.session_state.last_analysis = ""

conn = st.connection("gsheets", type=GSheetsConnection)
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

tab1, tab2 = st.tabs(["數據推算與分析", "長期趨勢與預測"])

# --- Tab 1: 數據分析 ---
with tab1:
    if not api_key:
        st.info("👋 請在左側輸入 API Key 以啟動系統。")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 指標輸入")
                st.session_state.weight = st.number_input("體重 (kg)", value=st.session_state.weight)
                st.session_state.max_hr = st.number_input("最大心率 (bpm)", value=st.session_state.max_hr)
                st.session_state.rest_hr = st.number_input("安靜心率 (bpm)", value=st.session_state.rest_hr)
                gct_val = st.number_input("觸地時間 (ms)", value=200)
                v_osc_val = st.number_input("垂直振幅 (cm)", value=8.0)
            
            with col2:
                st.subheader("📅 訓練內容")
                run_date = st.date_input("訓練日期", datetime.date.today())
                run_type = st.selectbox("類型", ["間歇跑 (Interval)", "穩定跑 (E/M/T)"])
                raw_data = st.text_area("貼上數據", height=150)

            if st.button("啟動 AI 深度分析"):
                with st.spinner("分析中..."):
                    p = f"體重{st.session_state.weight}, MHR:{st.session_state.max_hr}, RHR:{st.session_state.rest_hr}, GCT:{gct_val}, 數據:{raw_data}"
                    st.session_state.last_analysis = model.generate_content(p).text
            
            if st.session_state.last_analysis:
                st.markdown(st.session_state.last_analysis)
                st.divider()
                # 這裡修正了導致錯誤的斷碼
                f_vo2 = st.number_input("確認 VO2 Max 數字", value=42.0, step=0.1)
                if st.button("確認存入雲端"):
                    s, m = push_to_sheets(conn, run_date, f_vo2, run_type, gct_val, v_osc_val)
                    if s: st.success(m)
                    else: st.error(m)
        except Exception as e:
            st.error(f"連線錯誤: {e}")

# --- Tab 2: 趨勢分析 ---
with tab2:
    st.header("📈 長期趨勢監控")
    try:
        df = conn.read(spreadsheet=SHEET_URL)
        if df is not None and not df.empty:
            df["日期"] = pd.to_datetime(df["日期"])
            df = df.sort_values("日期")
            
            # VO2 Max 圖表
            st.subheader("體能發展 (VO2 Max)")
            st.line_chart(df.set_index("日期")["VO2_Max"])
            
            # GCT 圖表
            if "GCT" in df.columns:
                st.subheader("技術發展 (觸地時間)")
                st.line_chart(df.set_index("日期")["GCT"])
            
            # 數據表與預測
            st.divider()
            if len(df) >= 3 and st.button("生成 AI 進步預測"):
                hist = df.tail(10).to_string()
                st.info(model.generate_content(f"分析趨勢並預測: {hist}").text)
            st.dataframe(df, use_container_width=True)
        else:
            st.write("目前尚無數據，請先完成一次存檔。")
    except Exception as e:
        st.write("等待數據載入中...")
