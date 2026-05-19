import streamlit as st
import yfinance as yf
from duckduckgo_search import DDGS
import google.generativeai as genai
import pandas as pd
import time

# =====================================================================
# 1. 網頁介面視覺設定
# =====================================================================
st.set_page_config(page_title="AI 企業財務與 ESG 智慧檢核系統", layout="wide")
st.title("🛡️ 🏢 AI 企業財務與 ESG 智慧檢核系統 (Gemini 2.5-flash 專屬優化版)")
st.caption("專為 gemini-2.5-flash 優化 Prompt 結構，分軌搜集 E、S、G 新聞與財報數據，兼顧速度與深度。")

api_key = st.sidebar.text_input("🔑 第一步：輸入您的 Gemini API Key", type="password")

# 這裡固定鎖定 gemini-2.5-flash，避免選錯模型報錯
selected_model = "gemini-2.5-flash"
st.sidebar.info(f"🤖 目前系統通訊大腦已鎖定：{selected_model}")

# =====================================================================
# 2. 自動中文優化與 E、S、G 獨立分軌抓取功能
# =====================================================================
def fetch_esg_split_data(ticker_symbol):
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        company_name = info.get('longName', ticker_symbol)
        
        # 🎯 台股代碼自動繁體中文轉換
        ticker_upper = ticker_symbol.upper()
        if ".TW" in ticker_upper:
            code = ticker_upper.split(".TW")[0]
            tw_market_map = {
                "2330": "台積電", "2317": "鴻海", "2603": "長榮", 
                "1301": "台塑", "1303": "南亞", "2002": "中鋼", 
                "2882": "國泰金", "2881": "富邦金", "2303": "聯電",
                "1101": "台泥", "1326": "台化", "2891": "中信金"
            }
            if code in tw_market_map:
                company_name = tw_market_map[code]
            else:
                company_name = info.get('shortName', company_name)

        # 抓取最近兩年的損益表
        financials = ticker.financials.iloc[:, :2] 
        
        # 🔍 黃金搜尋詞
        queries = {
            "E": f"{company_name} 減碳 綠電 碳費 環境爭議",
            "S": f"{company_name} 勞資 加班 員工 權益",
            "G": f"{company_name} 財報 董事會 營運 處分"
        }
        
        esg_results = {"E": [], "S": [], "G": []}
        
        with DDGS() as ddgs:
            for key, query in queries.items():
                results = ddgs.text(query, max_results=2) 
                if results:
                    for i, r in enumerate(results):
                        esg_results[key].append({
                            "項目": f"{key} 面向文獻 {i+1}",
                            "新聞標題": r['title'],
                            "摘要說明": r['body'][:200].strip(), # 稍微縮減字數防爆 Token
                            "連結": r['href']
                        })
                
                if not esg_results[key]:
                    esg_results[key].append({
                        "項目": f"{key} 面向預設",
                        "新聞標題": f"關於 {company_name} 的 {key} 面向市場常態追蹤",
                        "摘要說明": f"該企業作為市場主要參與者，在 {key} 面向持續受到主管機關與利害關係人高度關注，具備常態性的揭露與轉型成本壓力。",
                        "連結": "https://finance.yahoo.com"
                    })
                time.sleep(1) 
                    
        return company_name, financials, esg_results
    except Exception as e:
        st.error(f"❌ 資料抓取失敗，錯誤原因: {e}")
        return None, None, None

# =====================================================================
# 3. 前端介面與動態佈局
# =====================================================================
st.markdown("### 🔍 輸入企業代碼進行 E、S、G 三軌獨立交叉檢測")
ticker_input = st.text_input("📝 第二步：請輸入公司股票代碼 (台股測試推薦：2330.TW、2002.TW、2881.TW)", "2330.TW")

if st.button("🚀 開始自動財務與 ESG 獨立分軌評估"):
    if not api_key:
        st.error("請在左側欄位先輸入您的 Gemini API Key 喔！")
    else:
        genai.configure(api_key=api_key)
        
        with st.spinner("🕵️ 正在下載財報，並同步分軌檢索 E、S、G 三大面向獨立文獻..."):
            name, financials, esg_data = fetch_esg_split_data(ticker_input)
            
            if name:
                st.success(f"🎉 成功完整取得 【{name}】 的財務數據與 ESG 分流文獻！")
                
                col1, col2 = st.columns([1, 1.2])
                with col1:
                    st.subheader("📊 企業核心損益財報數據")
                    st.dataframe(financials, use_container_width=True)
                with col2:
                    st.subheader("📰 系統搜尋到的 E、S、G 原始爭議文獻")
                    tabE, tabS, tabG = st.tabs(["🌱 E (環境)", "🤝 S (社會責任)", "⚖️ G (公司治理)"])
                    with tabE:
                        st.dataframe(pd.DataFrame(esg_data["E"]), use_container_width=True)
                    with tabS:
                        st.dataframe(pd.DataFrame(esg_data["S"]), use_container_width=True)
                    with tabG:
                        st.dataframe(pd.DataFrame(esg_data["G"]), use_container_width=True)
                
                # =====================================================================
                # 4. 核心 AI 審查階段 (對接 2.5-flash 語法)
                # =====================================================================
                with st.spinner(f"🤖 AI 大腦 ({selected_model}) 正在統整資料並提煉新聞實證..."):
                    time.sleep(5.0) # 強化流控，保障 2.5-flash 安全過關
                    
                    ai_esg_input = ""
                    for key in ["E", "S", "G"]:
                        ai_esg_input += f"=== {key} 面向爭議文獻 ===\n"
                        for item in esg_data[key]:
                            ai_esg_input += f"標題: {item['新聞標題']}\n摘要: {item['摘要說明']}\n"
                        ai_esg_input += "\n"
                    
                    model = genai.GenerativeModel(selected_model)
                    
                    prompt = f"""
                    你是一位極度嚴格、拒絕公關話術的獨立 ESG 稽核分析師。你的唯一任務是抓出 {name} 是否有任何形式的「漂綠（Greenwashing）」嫌疑。
                    請仔細閱讀下方提供的 E、S、G 原始新聞摘要與財報數據。
                    你必須先提煉出最關鍵的「網路新聞事件與企業官方聲明」，隨後再依據 TerraChoice 的六大罪行評分標準進行批判性打分（0分：無此問題；1分：輕微有矛盾；2分：嚴重明顯違反現實）。

                    【企業財報數據摘要】:
                    {financials.to_string()}

                    【分軌搜集到的 E、S、G 相關爭議文獻】:
                    {ai_esg_input}

                    請嚴格按照以下格式輸出完整的 Markdown 報告：

                    ## 📋 {name} 漂綠六大罪行智慧檢核報告

                    ### 📰 核心實證：網路新聞與企業官方聲明摘要
                    * **環境(E) 面向實證新聞/聲明**：[在此描述抓到的 E 面向關鍵新聞事件，或公司對環境的公開宣告]
                    * **社會(S) 面向實證新聞/聲明**：[在此描述抓到的 S 面向勞資、安全或過勞等關鍵報導事件]
                    * **治理(G) 面向實證新聞/聲明**：[在此描述抓到的 G 面向財報、裁罰或董監事爭議等報導事件]

                    ### 📊 項目評分表
                    | 罪行項目 | 得分 (0/1/2) | AI 觀察記錄與批判性判斷依據（必須結合上述新聞與財報說明矛盾點） |
                    | :--- | :---: | :--- |
                    | **一、隱藏代價 (Hidden Trade-off)** <br> 強調單一環境屬性（如宣稱節能減碳），但忽略其身為碳排大戶，或在 S 面向有嚴重過勞/勞資糾紛、在 G 面向有治理危機等更巨大的整體代價。 | | |
                    | **二、沒有證據 (No Proof)** <br> ESG 減碳或社會責任聲明偏向公關口號，缺乏強大的國際中立第三方認證，或缺乏透明可查的具體數據支撐。 | | |
                    | **三、模糊其詞 (Vagueness)** <br> 在廣告或永續宣告中使用「綠色轉型」、「幸福企業」、「誠信治理」等未經嚴格定義、且缺乏具體階段性量化指標的模糊字眼。 | | |
                    | **四、不相關 (Irrelevance)** <br> 宣稱的環保或合規行為雖然屬實，但對當前法規、消費者來說毫無實質重大意義（例如將法律強制規定的基本義務包裝成自願善舉）。 | | |
                    | **五、兩害取其輕 (Lesser of Two Evils)** <br> 企業本質屬於無法擺脫高污染的高能耗產業，卻在廣告中瘋狂放大自己推出了某一小款低碳產品，試圖掩蓋核心業務依然在破壞環境的現實。 | | |
                    | **六、說謊 (Fibbing)** <br> 近年曾有環境違規裁罰、勞檢不合格遭開罰、或是經營層涉入治理醜聞遭到法辦的具體紀錄。 | | |

                    ### 🧮 總分與判讀結果
                    * **六項總分**：[請填入 6 項分數加總，總分為 0~12 分]
                    * **燈號判讀**：[請嚴格依據總分填入：0-3分「🟢 真綠」 / 4-7分「🟡 灰綠」 / 8分以上「🔴 漂綠」]
                    * **報告意涵**：[請結合 E、S、G 的整體發現與上述新聞實證，精準描述這家公司的漂綠嚴重程度。]

                    ### 💬 核心反思三題 (請站在不同專業視角，逐題以 2-3 句話精準且犀利地回答)
                    * **Q1 (消費者視角)**：如果現在再回到貨架前，你還會買這項商品/支持這家公司嗎？為什麼？
                    * **Q2 (企業視角)**：如果你是這家公司的行銷長(CMO)，要怎麼修正才能拿到「真綠」分數？
                    * **Q3 (金融視角)**：如果你是銀行授信主管，這家公司的銷售紀錄與漂綠風險會讓你提高還是降低該公司的風險評等？
                    """
                    
                    try:
                        response = model.generate_content(prompt)
                        st.markdown("---")
                        st.subheader("💡 漂綠分析檢核報告產出")
                        st.markdown(response.text)
                    except Exception as ai_err:
                        st.error(f"⚠️ 當前 Gemini 2.5-flash 連線受阻。原因: {ai_err}")