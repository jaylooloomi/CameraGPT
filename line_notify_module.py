import os
# import requests # 未來 Line Notify 實作時需要

def send_notification(config, message, image_path=None):
    line_config = config.get('line_notify', {})
    if line_config.get('enabled', False):
        # 這裡放置 Line Notify 的實際實作邏輯
        # 通常會使用 requests 庫發送 POST 請求到 Line Notify API
        # 例如:
        # token = line_config.get('token')
        # headers = {"Authorization": f"Bearer {token}"}
        # payload = {'message': message}
        # files = {} 
        # if image_path and os.path.exists(image_path):
        #    with open(image_path, 'rb') as f:
        #        files = {'imageFile': f}
        # requests.post("https://notify-api.line.me/api/notify", headers=headers, params=payload, files=files)
        
        print(f">>> [Line Notify] 已觸發 Line 通知 (未實作): {message}")
