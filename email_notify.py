import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os

def send_email(config, image_path, ai_response):
    """發送帶有圖片附件的 Email"""
    smtp_server = config.get('smtp_server')
    smtp_port = config.get('smtp_port')
    sender = config.get('sender_email')
    password = config.get('sender_password')
    receiver = config.get('receiver_email')
    
    if not all([smtp_server, sender, password, receiver]):
        print("[Email] 配置不完整，跳過發送郵件")
        return

    msg = MIMEMultipart()
    msg['Subject'] = config.get('subject', 'CameraGPT Alert')
    msg['From'] = sender
    msg['To'] = receiver

    body = f"""
    CameraGPT 系統通知:
    
    AI 分析結果: {ai_response}
    
    請查看附件中的截圖。
    """
    msg.attach(MIMEText(body, 'plain'))

    # 讀取並附加圖片
    if image_path and os.path.exists(image_path):
        with open(image_path, 'rb') as f:
            img_data = f.read()
            image = MIMEImage(img_data, name=os.path.basename(image_path))
            msg.attach(image)

    try:
        print(f"[Email] 正在發送郵件至 {receiver}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        print("[Email] 郵件發送成功！")
    except Exception as e:
        print(f"[Email] 發送失敗: {e}")
