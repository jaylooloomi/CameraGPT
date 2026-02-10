import os
import playsound

def play_sound(config):
    alarm_config = config.get('alarm_sound', {})
    if alarm_config.get('enabled', False):
        sound_file = alarm_config.get('sound_file')
        if sound_file and os.path.exists(sound_file):
            try:
                print(f">>> 播放警報音效: {sound_file}")
                playsound.playsound(sound_file, block=True)
            except Exception as e:
                print(f"播放警報音效失敗: {e}")
        else:
            print(f"警告: 警報音效檔案 {sound_file} 不存在或未設定。")
