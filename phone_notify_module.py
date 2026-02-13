# phone_notify_module.py
# 此模組旨在透過第三方服務 (例如 Twilio, Vonage) 發送電話或簡訊通知。
# 注意：這類服務通常需要付費，並且需要進行帳號設定、API 金鑰管理等複雜步驟。
# 因此，此模組目前僅作為一個佔位符 (placeholder) 和實作範例。

def send_notification(config, message, image_path=None):
    """
    透過第三方服務發送電話或簡訊通知。

    :param config: 應用程式的設定檔字典。
                   預期在 config['phone_notify'] 中找到服務供應商所需的憑證，例如:
                   {
                       'enabled': True,
                       'provider': 'twilio', // 假設未來支援多個供應商
                       'account_sid': 'ACxxxxxxxxxxxxxxx',
                       'auth_token': 'your_auth_token',
                       'from_number': '+15017122661', // Twilio 提供的號碼
                       'to_number': '+886912345678' // 要接收通知的電話號碼
                   }
    :param message: 要在簡訊或語音通話中傳達的訊息。
    :param image_path: (可選) 圖片路徑，某些服務可能支援彩信 (MMS)。
    """
    # 從主設定檔中取得電話通知的專屬設定
    phone_config = config.get('phone_notify', {})
    
    # 檢查此功能是否已在設定檔中啟用
    if phone_config.get('enabled', False):
        
        # --- 以下為使用 Twilio 函式庫的實作範例 (目前為註解狀態) ---
        # 實際使用前，需要先安裝 Twilio 的 Python 函式庫: pip install twilio
        
        # from twilio.rest import Client
        
        # account_sid = phone_config.get('account_sid')
        # auth_token = phone_config.get('auth_token')
        # from_number = phone_config.get('from_number')
        # to_number = phone_config.get('to_number')

        # if not all([account_sid, auth_token, from_number, to_number]):
        #     print("[Phone Notify] 錯誤: Twilio 設定不完整 (缺少 SID, token 或號碼)。")
        #     return
            
        # try:
        #     print(f">>> [Phone Notify] 準備透過 Twilio 發送簡訊至 {to_number}...")
        #     client = Client(account_sid, auth_token)
            
        #     # 建立簡訊內容
        #     sms = client.messages.create(
        #         body=message,
        #         from_=from_number,
        #         to=to_number
        #     )
        #     print(f"[Phone Notify] 簡訊已成功發送，SID: {sms.sid}")
            
        # except Exception as e:
        #     print(f"[Phone Notify] 錯誤: 簡訊發送失敗: {e}")
        
        # --- 目前的佔位符邏輯 ---
        # 因為需要付費服務，預設只印出訊息，表示此功能已被觸發
        print(f">>> [Phone Notify] 已觸發電話/簡訊通知 (此為模擬，未實際發送): {message}")
