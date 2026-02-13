# line_notify_module.py
# 此模組負責透過 Line Notify 發送通知。
# Line Notify 是 Line 提供的一項服務，允許開發者透過 API 發送訊息到個人或群組聊天中。

import os
import requests # 匯入 requests 函式庫，用於發送 HTTP 請求

def send_notification(config, message, image_path=None):
    """
    發送訊息和圖片到指定的 Line Notify 聊天室。

    :param config: 應用程式的設定檔字典。
                   預期在 config['line_notify'] 中找到 {'enabled': True, 'token': 'YOUR_LINE_NOTIFY_TOKEN'}
    :param message: 要發送的文字訊息。
    :param image_path: (可選) 要一同發送的圖片檔案路徑。
    """
    # 從主設定檔中取得 Line Notify 的專屬設定
    line_config = config.get('line_notify', {})
    
    # 檢查 Line Notify 功能是否在設定檔中被啟用
    if line_config.get('enabled', False):
        token = line_config.get('token')
        
        # 檢查權杖是否存在
        if not token or token == "YOUR_LINE_NOTIFY_TOKEN":
            print("[Line Notify] 錯誤: Line Notify 已啟用，但未在 config.yaml 中設定有效的 'token'。")
            return

        print(f">>> [Line Notify] 準備發送通知: {message}")
        
        try:
            # --- Line Notify API 呼叫邏輯 ---
            # Line Notify API 的端點
            api_url = "https://notify-api.line.me/api/notify"
            
            # 標頭 (Header) 中必須包含 Authorization，值為 'Bearer ' + 你的權杖
            headers = {"Authorization": f"Bearer {token}"}
            
            # 要傳送的資料 (Payload)，訊息是必要的
            payload = {'message': message}
            
            # 準備檔案物件 (如果提供了圖片路徑)
            files = {}
            image_file_object = None # 用於確保檔案在請求後能被關閉
            if image_path and os.path.exists(image_path):
                print(f"[Line Notify] 正在附加圖片: {image_path}")
                # 'rb' 表示以二進位讀取模式開啟檔案
                image_file_object = open(image_path, 'rb')
                files = {'imageFile': image_file_object}
            
            # 使用 requests.post 發送請求
            response = requests.post(
                api_url, 
                headers=headers, 
                params=payload, 
                files=files
            )
            
            # 檢查 API 回應狀態碼
            response.raise_for_status() # 如果狀態碼是 4xx 或 5xx，會拋出異常
            
            print("[Line Notify] 通知已成功發送！")

        except requests.exceptions.RequestException as e:
            print(f"[Line Notify] 錯誤: 發送通知失敗: {e}")
        finally:
            # 無論成功或失敗，都確保開啟的檔案物件被關閉
            if image_file_object:
                image_file_object.close()
