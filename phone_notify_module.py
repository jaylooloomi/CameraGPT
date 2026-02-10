def send_notification(config, message, image_path=None):
    phone_config = config.get('phone_notify', {})
    if phone_config.get('enabled', False):
        # 這裡放置電話通知的實際實作邏輯
        # 這通常需要整合第三方服務 (如 Twilio, Vonage 等) 或特定的硬體設備
        # 由於涉及較複雜的設定與費用，目前只作為佔位符。
        # 例如:
        # phone_number = phone_config.get('phone_number')
        # if phone_number:
        #     # 呼叫第三方 API 發送語音電話或簡訊
        #     print(f"正在撥打電話到 {phone_number} 進行通知...")

        print(f">>> [Phone Notify] 已觸發電話通知 (未實作): {message}")
