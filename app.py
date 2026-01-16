import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
import os

# --- 檔案設定 ---
DATA_FILE = "running_history.csv"

def save_data(date, vo2max, run_type):
    new_data = pd.DataFrame([[str(date), vo2max, run_type]], columns=["日期", "VO2_Max", "類型"])
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        df = pd.concat([df, new_data], ignore_index=True)
    else:
        df = new_data
    df.to_csv(DATA_FILE, index=False)

# --- 介面設定 ---
st.set_page_config(page_title="建希的運動投資儀表板", layout="wide")
st.title("🏃‍♂️ 跑步數據與 $VO_2 Max$ 長期追蹤")

api_key = st.sidebar.text_input("輸入 Gemini API Key", type="password")

# --- 主畫面分頁 ---
tab1, tab2 = st.tabs(["數據推算", "歷史分析與趨勢"])

with tab1:
    if api_key:
        try:
            genai.configure(api_key=api_key)
            
            # --- 自動模型相容邏輯 ---
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target = "models/gemini-1.5-flash"
            if target not in available_models:
                target = available_models[0]
            
            model_name = target.replace("models/", "")
            model = genai.GenerativeModel(model_name)
            
            st.success(f"✅ 系統已成功連線至：{model_name}")
            
            st.divider()
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("體重 (kg)", value=80.0)
                max_hr = st.number_input("最大心率 (bpm)", value=190)
            with col2:
                run_date = st.date_input("訓練日期", datetime.date.today())
                run_type = st.selectbox("訓練類型", ["間歇跑 (Interval)", "穩定跑 (E/M/T)"])

            raw_data = st.text_area("貼上 Lap 數據 (例如週五的衝刺紀錄)", height=150)

            if st.button("開始 AI 分析"):
                with st.spinner("AI 教練正在閱卷中..."):
                    prompt = f"""
                    你是一位專業跑步教練。請分析以下數據：
                    - 跑者體重：{weight}kg
                    - 最大心率：{max_hr}
                    - 數據內容：{raw_data}
                    
                    請執行：
                    1. 識別間歇衝刺段並計算該段的配速效率。
                    2. 根據心率漂移情況推算一個具體的 VO2 Max 數字。
                    3. 給予簡短的下週訓練建議。
                    """
                    response = model.generate_content(prompt)
                    st.markdown(response.text)
                
                st.divider()
                st.subheader("確認存檔區")
                final_vo2 = st.number_input("請輸入 AI 推算的 VO2 Max 數字 (例如 42.5)", value=40.0, step=0.1)
                if st.button("確認存入歷史資料庫"):
                    save_data(run_date, final_vo2, run_type)
                    st.success(f"已記錄 {run_date} 的數據！請切換到趨勢分頁查看。")
                    
        except Exception as e:
            st.error(f"發生錯誤：{e}")
    else:
        st.info("👋 你好建希！請先在左側邊欄輸入 API Key 啟動系統。")

with tab2:
    st.header("📈 $VO_2 Max$ 成長曲線")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        # 確保日期排序正確
        df = df.sort_values("日期")
        st.line_chart(df.set_index("日期")["VO2_Max"])
        st.dataframe(df)
    else:
        st.write("目前尚未有存檔紀錄，快去進行第一次分析吧！")
