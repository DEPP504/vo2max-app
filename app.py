import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
from streamlit_gsheets import GSheetsConnection

# --- 試算表設定 ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/16niyheTwWVts9A6aKRiOx2OpJypQAIeodE08TN9cERU/edit?usp=sharing"

def push_to_sheets(conn, run_date, final_vo2, run_type, gct, v_osc):
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
        return True, "✅ 數據已成功存入雲端！"
    except Exception as e:
        return False, f"❌ 存檔失敗：{e}"

# --- 介面初始化 ---
st.set_page_config(page_title="AI 跑步專家系統", layout="wide")
st.title("🏃‍♂️ AI 運動表現與技術分析系統")

if 'last_analysis' not in st.session_state: st.session_state.last_analysis = ""

conn = st.connection("gsheets", type=GSheetsConnection)
api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

tab1, tab2 = st.tabs(["數據推算與分析", "長期趨勢與預測"])

with tab1:
    if not api_key:
        st.info("👋 請輸入 API Key。")
    else:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 基礎生理資訊")
                weight = st.number_input("體重 (kg)", value=80.0)
                mhr = st.number_input("最大心率 (bpm)", value=190)
                rhr = st.number_input("安靜心率 (bpm)", value=55)
            
            with col2:
                st.subheader("📅 訓練記錄內容")
                run_date = st.date_input("訓練日期", datetime.date.today())
                # 更新跑步類型
                run_type = st.selectbox("跑步類型", ["衝刺", "間歇", "節奏跑", "輕鬆跑", "LSD"])
                raw_data = st.text_area("請貼上 Lap 數據（系統將自動分析技術指標）", height=150)

            if st.button("啟動 AI 深度分析"):
                with st.spinner("AI 正在解析數據細節..."):
                    # 強化 Prompt，要求 AI 提取關鍵數字
                    prompt = f"""
                    你是一位專業跑力教練。請分析以下數據：
                    1. 生理：體重{weight}kg, MHR:{mhr}, RHR:{rhr}。
                    2. 數據內容：{raw_data}
                    
                    請執行以下任務：
                    - 估算本次 VO2 Max。
                    - 從 Lap 數據中提取平均『觸地時間(GCT)』與『垂直振幅』。
                    - 給予技術修正建議。
                    """
                    st.session_state.last_analysis = model.generate_content(prompt).text
            
            if st.session_state.last_analysis:
                st.divider()
                st.markdown(st.session_state.last_analysis)
                
                # --- 存檔確認區 (這部分由使用者根據 AI 分析結果填入/確認) ---
                st.subheader("💾 數據存檔確認區")
                st.info("💡 請根據上方 AI 提取的數值進行最後確認：")
                c1, c2, c3 = st.columns(3)
                with c1:
                    final_vo2 = st.number_input("確認 VO2 Max", value=42.0, step=0.1)
                with c2:
                    final_gct = st.number_input("確認觸地時間 (ms)", value=200)
                with c3:
                    final_v_osc = st.number_input("確認垂直振幅 (cm)", value=8.0, step=0.1)
                
                if st.button("確認數據無誤，永久存檔"):
                    s, m = push_to_sheets(conn, run_date, final_vo2, run_type, final_gct, final_v_osc)
                    if s: st.success(m)
                    else: st.error(m)
        except Exception as e:
            st.error(f"錯誤：{e}")

with tab2:
    st.header("📈 成長趨勢監控")
    try:
        df = conn.read(spreadsheet=SHEET_URL)
        if df is not None and not df.empty:
            df["日期"] = pd.to_datetime(df["日期"])
            df = df.sort_values("日期")
            st.subheader("體能進步 (VO2 Max)")
            st.line_chart(df.set_index("日期")["VO2_Max"])
            st.subheader("技術效率 (觸地時間)")
            st.line_chart(df.set_index("日期")["GCT"])
            st.dataframe(df, use_container_width=True)
        else:
            st.write("目前尚無數據。")
    except:
        st.write("等待雲端同步中...")
