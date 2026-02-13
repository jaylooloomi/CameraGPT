# test.py
# 這是一個用於測試音訊錄製和播放功能的獨立腳本。
# 主要目的：
# 1. 驗證麥克風是否能被 `sounddevice` 函式庫正常偵測和使用。
# 2. 測試錄製下來的音訊品質。
# 3. 確保 `scipy` 函式庫可以正確地將音訊數據儲存為 .wav 檔案。
#
# 使用的函式庫：
# - sounddevice: 用於錄製和播放音訊。
# - scipy.io.wavfile.write: 用於將 NumPy 陣列格式的音訊數據寫入 .wav 檔案。
# - numpy: 用於處理音訊數據陣列。

import sounddevice as sd
from scipy.io.wavfile import write # 從 scipy.io.wavfile 模組中引入 write 函數
import numpy as np

# --- 設定錄音參數 ---
fs = 44100      # 採樣率 (Sample Rate) in Hz。44100 Hz 是 CD 音質的標準。
duration = 5.0  # 錄音長度 (秒)。
filename = "output.wav" # 儲存音訊的檔案名稱。

print("錄音即將開始，請對著麥克風說話...")
# time.sleep(1) # 可以選擇在開始前稍作等待

print(f"正在錄音，持續 {duration} 秒...")

# --- 執行錄音 ---
# sd.rec() 函數會開始錄音，並將音訊數據儲存在一個 NumPy 陣列中。
# 參數:
#   - int(duration * fs): 要錄製的總樣本數。
#   - samplerate: 採樣率。
#   - channels: 聲道數 (1 表示單聲道，2 表示立體聲)。
myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)

# --- 等待錄音完成 ---
# sd.wait() 會暫停程式執行，直到錄音完成。這是一個阻塞操作。
sd.wait()
print("錄音結束！")

# --- 步驟 1: 播放錄製的音訊 (用於驗證) ---
# 這個步驟是選擇性的，可以讓使用者立即聽到錄音的結果。
try:
    print("正在播放錄音...")
    # sd.play() 函數會播放 NumPy 陣列中的音訊數據。
    sd.play(myrecording, fs)
    # 再次使用 sd.wait() 來等待播放完成。
    sd.wait()
    print("播放完畢。")
except Exception as e:
    print(f"播放音訊時發生錯誤: {e}")

# --- 步驟 2: 儲存音訊檔案 ---
# 使用 scipy 的 write 函數將 NumPy 陣列寫入 .wav 檔案。
try:
    print(f"正在將錄音儲存至檔案: {filename}...")
    # 參數:
    #   - filename: 檔案名稱。
    #   - fs: 採樣率。
    #   - myrecording: 包含音訊數據的 NumPy 陣列。
    write(filename, fs, myrecording) 
    print(f"檔案已成功儲存！")
except Exception as e:
    print(f"儲存檔案時發生錯誤: {e}")