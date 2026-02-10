import cv2
import numpy as np
import time

def check_camera_availability(index):
    """測試特定相機索引是否可用 (包含預熱邏輯)"""
    print(f"--- 嘗試相機索引 {index} (DirectShow) ---")
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print(f"無法開啟相機 {index}")
        return False

    # 嘗試讀取一些屬性
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"相機 {index} 預設解析度: {w}x{h}")

    print("正在預熱相機 (最多 3 秒)...")
    success = False
    
    start_time = time.time()
    frame_count = 0
    
    while time.time() - start_time < 3.0:
        ret, img = cap.read()
        if ret and img is not None:
            # 檢查畫面是否全黑
            if np.sum(img) > 0: 
                frame_count += 1
                # 拿到好幾幀穩定的畫面後就視為成功
                if frame_count > 5:
                    success = True
                    break
        time.sleep(0.1)

    cap.release()
    
    if success:
        print(f"成功確認相機 {index} 可用！")
        return True
    else:
        print(f"相機 {index} 開啟了但讀取不到有效畫面。")
        return False

def find_working_camera():
    """尋找可用的相機索引 (0 或 1)"""
    if check_camera_availability(0):
        return 0
    if check_camera_availability(1):
        return 1
    return None

def open_camera(camera_index):
    """開啟並回傳相機物件 (長連接用)"""
    print(f"--- 初始化相機索引 {camera_index} ---")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        raise IOError(f"無法開啟攝影機 {camera_index}")
    
    # 設定解析度
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # 稍微預熱一下
    for _ in range(5):
        cap.read()
        
    return cap

def capture_frame(cap):
    """從已開啟的相機物件抓取一幀影像 (會清空緩衝區以確保畫面最新)"""
    if not cap.isOpened():
        raise IOError("相機已斷線")
    
    # 清空緩衝區 (Flush Buffer)
    # 連續讀取 5 張，只取最後一張
    # 這能解決 "拿到舊畫面" 以及 "自動曝光剛啟動不穩定" 的問題
    for _ in range(5):
        cap.grab() # grab() 比 read() 快，只抓不解碼
        
    # 真正讀取最新的一幀
    ret, frame = cap.read()
    
    if not ret or frame is None:
        # 嘗試重讀一次
        ret, frame = cap.read()
        if not ret or frame is None:
            raise IOError("無法讀取影像幀")
    
    # 簡單檢查畫面是否有內容 (非全黑)
    if np.sum(frame) == 0:
        # 若全黑，嘗試再讀一幀
        ret, frame = cap.read()
    
    # Debug: 儲存每一張抓到的圖以便除錯
    # 用時間戳記當檔名
    import time
    import os
    if not os.path.exists("temp"):
        os.makedirs("temp")
        
    ts = int(time.time() * 1000)
    filepath = f"temp/debug_{ts}.jpg"
    cv2.imwrite(filepath, frame)
    print(f"[Debug] 已儲存截圖: {filepath}")
        
    return frame

def calculate_diff(frame1, frame2):
    """計算兩張影像的差異值 (加入模糊處理)"""
    if frame1 is None or frame2 is None:
        return 0
    
    # 轉為灰階
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # 高斯模糊 (降低噪點與光線微變化的影響)
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
    
    # 計算絕對差
    diff = cv2.absdiff(gray1, gray2)
    
    # 二值化處理 (去除微小雜訊)
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    
    # 計算變動像素佔比 (百分比)
    # 變動像素值為 255，不變為 0
    non_zero_count = np.count_nonzero(thresh)
    total_pixels = thresh.size
    
    if total_pixels == 0:
        return 0.0
        
    percentage = (non_zero_count / total_pixels) * 100.0
    return percentage

def save_temp_image(frame, filename="temp_capture.jpg"):
    """儲存暫存影像供 AI 分析"""
    import os
    if not os.path.exists("temp"):
        os.makedirs("temp")
        
    # 如果 filename 只有檔名，加上 temp 路徑
    if os.path.dirname(filename) == "":
        filepath = os.path.join("temp", filename)
    else:
        filepath = filename
        
    cv2.imwrite(filepath, frame)
    print(f"[Info] 已儲存 AI 分析用圖: {filepath}")
    return filepath
