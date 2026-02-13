# image_utils.py
# 這個模組封裝了所有與攝影機互動和圖片處理相關的功能。
# 它主要使用 OpenCV (cv2) 函式庫來進行操作。

import cv2
import numpy as np
import time
import os

def check_camera_availability(index):
    """
    測試指定的攝影機索引是否可用，並確保能讀取到有效的影像幀。

    運作方式:
    1. 嘗試使用 DirectShow 後端 (cv2.CAP_DSHOW，在 Windows 上更穩定) 開啟攝影機。
    2. 如果成功開啟，會嘗試讀取幾幀畫面進行 "預熱"，以確保相機自動曝光等功能穩定。
    3. 檢查讀取到的畫面是否非全黑，以確認相機有在正常運作。

    :param index: 要測試的攝影機索引 (通常從 0 開始)。
    :return: 如果攝影機可用且能讀取到有效畫面，則返回 True；否則返回 False。
    """
    print(f"--- 正在嘗試攝影機索引 {index} (使用 DirectShow 後端) ---")
    # 使用 cv2.CAP_DSHOW 可以提高在 Windows 上的相容性和效能
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        print(f"無法開啟攝影機 {index}。")
        return False

    # 嘗試讀取攝影機的預設解析度
    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"攝影機 {index} 回報的預設解析度: {int(w)}x{int(h)}")

    print("正在預熱攝影機並讀取畫面 (最多 3 秒)...")
    success = False
    start_time = time.time()
    frame_count = 0
    
    # 在 3 秒的超時時間內，嘗試讀取多幀畫面
    while time.time() - start_time < 3.0:
        ret, img = cap.read()
        if ret and img is not None:
            # 檢查畫面是否全黑 (有些攝影機剛啟動時會回傳全黑畫面)
            if np.sum(img) > 0: 
                frame_count += 1
                # 如果能連續讀取到超過 5 幀有效畫面，就視為成功
                if frame_count > 5:
                    success = True
                    break
        time.sleep(0.1) # 短暫延遲，避免 CPU 過度使用

    cap.release()
    
    if success:
        print(f"成功確認攝影機 {index} 可用！")
        return True
    else:
        print(f"攝影機 {index} 已開啟但無法讀取到有效的影像畫面。")
        return False

def find_working_camera():
    """
    自動尋找一個可用的攝影機索引。

    它會依序測試索引 0 和 1，並返回第一個成功通過 `check_camera_availability` 測試的索引。
    :return: 可用的攝影機索引 (0 或 1)，如果都找不到則返回 None。
    """
    if check_camera_availability(0):
        return 0
    if check_camera_availability(1):
        return 1
    return None

def open_camera(camera_index):
    """
    開啟指定的攝影機並返回其物件，用於後續的持續影像抓取。

    :param camera_index: 要開啟的攝影機索引。
    :return: 一個 cv2.VideoCapture 物件。
    :raises IOError: 如果無法開啟攝影機，則拋出異常。
    """
    print(f"--- 正在初始化攝影機索引 {camera_index} 以進行持續監控 ---")
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    
    if not cap.isOpened():
        raise IOError(f"無法開啟攝影機 {camera_index}")
    
    # 設定一個常見的解析度，以確保穩定性
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # 短暫預熱
    for _ in range(5):
        cap.read()
        
    return cap

def capture_frame(cap):
    """
    從一個已開啟的攝影機物件中抓取一幀最新的影像。

    此函數包含一個重要的 "清空緩衝區" 技巧，以避免讀取到舊的、延遲的畫面。
    
    :param cap: `open_camera` 返回的 cv2.VideoCapture 物件。
    :return: 一幀影像 (Numpy array)。
    :raises IOError: 如果攝影機斷線或無法讀取畫面，則拋出異常。
    """
    if not cap.isOpened():
        raise IOError("攝影機連線中斷")
    
    # --- 清空緩衝區 (Flush Buffer) ---
    # 許多攝影機會將影像暫存在一個內部緩衝區。如果程式處理速度比攝影機幀率慢，
    # 直接 cap.read() 可能會拿到幾秒前的舊畫面。
    # 這裡我們先用 cap.grab() 快速地 "丟棄" 幾幀舊畫面。
    # grab() 只抓取影像到緩衝區，但不解碼，速度比 read() 快。
    for _ in range(5):
        cap.grab()
        
    # 在清空緩衝區後，用 cap.read() 讀取最新的一幀並解碼
    ret, frame = cap.read()
    
    if not ret or frame is None:
        # 如果失敗，嘗試再讀一次，以增加穩定性
        print("[Warning] 第一次影像讀取失敗，正在重試...")
        ret, frame = cap.read()
        if not ret or frame is None:
            raise IOError("無法從攝影機讀取有效的影像幀")
    
    # 儲存每一張成功抓取的畫面到 temp/debug 資料夾，以便於事後分析和除錯
    ts = int(time.time() * 1000)
    filepath = os.path.join("temp", f"debug_{ts}.jpg")
    cv2.imwrite(filepath, frame)
    print(f"[Debug] 已儲存除錯用截圖: {filepath}")
        
    return frame

def calculate_diff(frame1, frame2):
    """
    計算兩張影像之間的差異百分比。

    這個函數透過一系列的影像處理步驟來突顯兩張圖的真實變化，並忽略微小的雜訊和光影變化。
    
    處理流程:
    1. 將彩色圖片轉為灰階。
    2. 使用高斯模糊來平滑圖片，去除雜訊。
    3. 計算兩張模糊後圖片的絕對差異圖。
    4. 使用二值化處理，將差異明顯的像素標記為白色，其餘為黑色。
    5. 計算白色像素佔總像素的百分比。

    :param frame1: 第一張影像 (Numpy array)。
    :param frame2: 第二張影像 (Numpy array)。
    :return: 差異的百分比 (float)。
    """
    if frame1 is None or frame2 is None:
        return 0.0
    
    # 轉為灰階，因為顏色資訊在差異比對中不是必需的，且可以簡化計算
    gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
    
    # 使用高斯模糊來降低影像雜訊和微小光線變化的影響
    # (21, 21) 的核心大小表示一個較強的模糊程度
    gray1 = cv2.GaussianBlur(gray1, (21, 21), 0)
    gray2 = cv2.GaussianBlur(gray2, (21, 21), 0)
    
    # 計算兩張灰階圖之間的絕對差異
    diff = cv2.absdiff(gray1, gray2)
    
    # 二值化處理：將差異大於 30 的像素設為 255 (白色)，小於等於 30 的設為 0 (黑色)
    # 這一步可以有效地過濾掉非常微小的、不重要的變化
    _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
    
    # 計算非零像素 (白色像素) 的數量
    non_zero_count = np.count_nonzero(thresh)
    total_pixels = thresh.size
    
    if total_pixels == 0:
        return 0.0
        
    # 計算差異百分比
    percentage = (non_zero_count / total_pixels) * 100.0
    return percentage

def save_temp_image(frame, filename="temp_capture.jpg"):
    """
    將影像幀儲存到 'temp' 資料夾中，以供 AI 分析或其他模組使用。

    :param frame: 要儲存的影像 (Numpy array)。
    :param filename: 儲存的檔案名稱。
    :return: 儲存後的完整檔案路徑。
    """
    # 確保 temp 資料夾存在
    if not os.path.exists("temp"):
        os.makedirs("temp")
        
    filepath = os.path.join("temp", filename)
        
    # 使用 OpenCV 的 imwrite 函數儲存圖片
    cv2.imwrite(filepath, frame)
    print(f"[Info] 已儲存 AI 分析用圖片: {filepath}")
    return filepath
