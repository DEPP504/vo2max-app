import streamlit as st
import google.generativeai as genai
import pandas as pd
import datetime
import os

# --- 檔案設定 ---
DATA_FILE = "running_history.csv"

def save_data(date, vo2max, run_type):
    new_data = pd.DataFrame([[date, vo2max, run_type]], columns=["日期", "VO2_Max", "類型"])
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
        # 1. 取得所有可用的模型名稱
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 2. 篩選出最適合的 flash 或 pro
        # 雲端有時需要去掉 'models/' 前綴才能運作
        target = "models/gemini-1.5-flash"
        if target not in available_models:
            target = available_models[0] # 若找不到，就選該 API Key 權限下的第一個
            
        model_name = target.replace("models/", "") # 關鍵修正：去除前綴
        model = genai.GenerativeModel(model_name)
        
        st.success(f"✅ 已成功連線至：{model_name}")
            
            col1, col2 = st.columns(2)
            with col1:
                weight = st.number_input("體重 (kg)", value=80.0)
                max_hr = st.number_input("最大心率 (bpm)", value=190)
            with col2:
                run_date = st.date_input("訓練日期", datetime.date.today())
                run_type = st.selectbox("訓練類型", ["間歇跑 (Interval)", "穩定跑 (E/M/T)"])

            raw_data = st.text_area("貼上 Lap 數據", height=150)

            if st.button("分析並存檔"):
                prompt = f"你是教練，分析數據並給出一個確定的 VO2 Max 數字。體重{weight}, 最大心率{max_hr}。數據：{raw_data}"
                response = model.generate_content(prompt)
                
                # 這裡假設 AI 會給出一個數字，我們先簡單模擬一個提取數字的邏輯
                # 實務上可以請 AI 格式化輸出，例如 [VO2_MAX: 42.5]
                st.markdown(response.text)
                
                # 這裡手動輸入分析後的數字以便存檔（或讓 AI 自動回傳）
                final_vo2 = st.number_input("確認本次推算的 VO2 Max (供存檔用)", value=41.5)
                if st.button("確認存入資料庫"):
                    save_data(run_date, final_vo2, run_type)
                    st.success("紀錄已成功存入雲端檔案！")
                    
        except Exception as e:
            st.error(f"錯誤：{e}")
    else:
        st.info("請先輸入 API Key")

with tab2:
    st.header("📈 $VO_2 Max$ 成長曲線")
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        st.line_chart(df.set_index("日期")["VO2_Max"])
        st.dataframe(df)
    else:

        st.write("目前尚無歷史紀錄。")

