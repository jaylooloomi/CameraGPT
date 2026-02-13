# check_gemini_models.py
# 這是一個獨立的工具腳本，用於查詢並列出使用者 Google AI Studio 中所有可用的 Gemini 模型。
# 執行此腳本可以幫助使用者確認他們的 API 金鑰是否有效，以及有哪些模型名稱可以用於設定檔中。

import google.generativeai as genai
import os
import yaml

def list_models():
    """
    連接 Google Gemini API，並列出所有支援 'generateContent' 方法的模型。
    """
    # --- 步驟 1: 從設定檔 config.yaml 中讀取 API 金鑰 ---
    try:
        print("正在從 config.yaml 讀取 Gemini API Key...")
        with open("config.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            # 導航到設定檔中對應的 API Key 位置
            # 注意: 這裡的路徑 'ai.gemini.api_key' 是根據 config.yaml 的結構寫死的
            api_key = config['ai']['gemini_flash']['api_key'] 
            # 為了安全，只印出 API Key 的前五碼和後五碼
            print(f"成功讀取 API Key: {api_key[:5]}...{api_key[-5:]}")
    except FileNotFoundError:
        print("錯誤: 找不到 config.yaml 檔案。請確認此腳本與設定檔在同一個目錄下。")
        return
    except KeyError:
        print("錯誤: 在 config.yaml 中找不到路徑 'ai.gemini_flash.api_key'。請檢查設定檔結構是否正確。")
        return
    except Exception as e:
        print(f"讀取設定檔時發生未預期的錯誤: {e}")
        return

    # --- 步驟 2: 設定 Gemini API ---
    # 使用讀取到的 API Key 來設定 genai 函式庫
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"設定 Gemini API 時發生錯誤，請檢查 API Key 是否無效或格式錯誤: {e}")
        return

    # --- 步驟 3: 查詢並列出模型 ---
    print("\n正在向 Google API 查詢可用的模型列表...")
    try:
        # 呼叫 genai.list_models() 來取得模型清單
        for m in genai.list_models():
            # 檢查該模型是否支援 'generateContent' 這個最常用的生成方法
            # 這有助於過濾掉一些僅用於特定目的 (如 embedding) 的模型
            if 'generateContent' in m.supported_generation_methods:
                # 印出模型的名稱，例如 'models/gemini-1.5-flash-latest'
                print(f"- {m.name}")
    except Exception as e:
        # 捕捉並印出查詢過程中可能發生的錯誤，例如網路問題、權限問題等
        print(f"查詢模型列表時發生錯誤: {e}")

# 當此腳本被直接執行時，呼叫 list_models 函數
if __name__ == "__main__":
    list_models()