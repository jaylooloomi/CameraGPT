import sounddevice as sd
from scipy.io.wavfile import write # 引入儲存檔案的函數
import numpy as np

# 設定參數
fs = 44100      # 採樣率 (Sample rate)
duration = 2.0  # 錄音長度 (秒)
filename = "output.wav" # 存檔路徑

print("錄音中，請對麥克風說話...")
# sd.rec 會回傳一個 numpy 陣列
myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=1)

# 等待錄音結束
sd.wait()
print("錄音結束！")

# 1. 播放錄音 (選擇性)
print("播放中...")
sd.play(myrecording, fs)
sd.wait()

# 2. 儲存檔案
# 將 numpy 陣列寫入 wav 檔案
write(filename, fs, myrecording) 
print(f"檔案已成功儲存至: {filename}")