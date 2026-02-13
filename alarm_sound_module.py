# alarm_sound_module.py

import os
# playsound 是一個跨平台的 Python 函式庫，用於播放音效檔案，沒有其他相依性
import playsound

def play_sound(config):
    """
    播放警報音效。

    此函數會根據設定檔中的 'alarm_sound' 區塊來決定是否播放音效。
    它會檢查功能是否啟用 ('enabled': True)，並確認指定的音效檔案是否存在。

    :param config: 一個包含應用程式設定的字典。
                    預期在 config['alarm_sound'] 中找到相關設定，例如:
                    {'enabled': True, 'sound_file': 'path/to/your/sound.wav'}
    """
    # 從主設定檔中取得警報音效的專屬設定
    alarm_config = config.get('alarm_sound', {})

    # 檢查警報音效功能是否在設定檔中被啟用
    if alarm_config.get('enabled', False):
        # 取得音效檔案的路徑
        sound_file = alarm_config.get('sound_file')

        # 檢查 sound_file 是否有被設定，以及該檔案是否存在於指定的路徑
        if sound_file and os.path.exists(sound_file):
            try:
                print(f">>> [Alarm Sound] 正在播放警報音效: {sound_file}")
                # 呼叫 playsound 函式庫來播放音效
                # block=True 表示程式會等到音效播放完畢後才繼續執行
                playsound.playsound(sound_file, block=True)
            except Exception as e:
                # 捕捉並印出播放過程中可能發生的任何錯誤
                print(f"[Alarm Sound] 錯誤: 播放警報音效失敗: {e}")
        else:
            # 如果檔案路徑未設定或檔案不存在，則印出警告訊息
            print(f"[Alarm Sound] 警告: 警報音效檔案 '{sound_file}' 不存在或未在設定檔中指定。")
