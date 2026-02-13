# email_notify.py
# 此模組負責發送電子郵件通知。
# 它使用 Python 內建的 smtplib 和 email 函式庫來建立並發送包含文字和圖片附件的郵件。

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

def send_email(config, image_path, ai_response):
    """
    根據設定檔發送一封帶有圖片附件的 Email。

    :param config: 一個字典，應包含 SMTP 伺服器設定和寄件人/收件人資訊。
                   例如: {
                       'smtp_server': 'smtp.example.com',
                       'smtp_port': 587,
                       'sender_email': 'user@example.com',
                       'sender_password': 'your_password',
                       'receiver_email': 'recipient@example.com',
                       'subject': 'Alert from CameraGPT'
                   }
    :param image_path: 要作為附件的圖片檔案路徑。
    :param ai_response: AI 模型的回應，將被包含在郵件內文中。
    """
    # --- 步驟 1: 從設定檔中讀取郵件伺服器和帳號資訊 ---
    smtp_server = config.get('smtp_server')
    smtp_port = config.get('smtp_port')
    sender = config.get('sender_email')
    password = config.get('sender_password')
    receiver = config.get('receiver_email')
    
    # 檢查所有必要的設定欄位是否都存在，否則無法發送
    if not all([smtp_server, sender, password, receiver]):
        print("[Email] 錯誤: Email 設定不完整 (缺少伺服器、寄件人、密碼或收件人)，跳過發送郵件。")
        return

    # --- 步驟 2: 建立郵件物件 (MIMEMultipart) ---
    # MIMEMultipart 允許我們在同一封郵件中包含文字和附件
    msg = MIMEMultipart()
    msg['Subject'] = config.get('subject', '來自 CameraGPT 的系統警報') # 郵件主旨
    msg['From'] = sender  # 寄件人
    msg['To'] = receiver  # 收件人

    # --- 步驟 3: 建立並附加郵件內文 ---
    body = f"""
    CameraGPT 系統已觸發警報：
    
    AI 分析結果:
    "{ai_response}"
    
    詳細情況請查看附件中的監控截圖。
    """
    # 將純文字內文附加到郵件物件中
    msg.attach(MIMEText(body, 'plain', 'utf-8'))

    # --- 步驟 4: 讀取圖片檔案並附加到郵件中 ---
    if image_path and os.path.exists(image_path):
        try:
            with open(image_path, 'rb') as f:
                img_data = f.read()
                # 建立圖片附件物件
                image = MIMEImage(img_data, name=os.path.basename(image_path))
                # 將圖片附加到郵件中
                msg.attach(image)
        except Exception as e:
            print(f"[Email] 錯誤: 無法讀取或附加圖片檔案 '{image_path}': {e}")
    else:
        print(f"[Email] 警告: 找不到指定的圖片檔案 '{image_path}'，郵件將不包含附件。")


    # --- 步驟 5: 連接到 SMTP 伺服器並發送郵件 ---
    try:
        print(f"[Email] 正在透過 {smtp_server}:{smtp_port} 發送郵件至 {receiver}...")
        # 建立與 SMTP 伺服器的連線
        server = smtplib.SMTP(smtp_server, smtp_port)
        # 啟用 TLS 加密傳輸
        server.starttls()
        # 登入寄件人信箱
        server.login(sender, password)
        # 發送郵件
        server.send_message(msg)
        # 關閉連線
        server.quit()
        print("[Email] 郵件已成功發送！")
    except smtplib.SMTPAuthenticationError:
        print("[Email] 錯誤: SMTP 認證失敗。請檢查您的寄件人信箱和密碼是否正確。")
    except Exception as e:
        # 捕捉其他所有可能的錯誤，例如網路連線問題
        print(f"[Email] 郵件發送失敗: {e}")
