# alarm_clock_module.py

def trigger_alarm(config):
    """
    觸發鬧鐘功能。

    這個函數會檢查設定檔中 'alarm_clock' 的設定。如果 'enabled' 為 True，
    它會印出一則訊息來表示鬧鐘已被觸發。

    目前這只是一個佔位符 (placeholder) 函數，未來可以擴充以實現更複雜的鬧鐘邏輯，
    例如：
    - 透過 API 呼叫一個智慧家庭裝置。
    - 播放一段特定的警告音效。
    - 結合其他通知模組發送警報。

    :param config: 一個包含應用程式設定的字典。
                    預期在 config['alarm_clock'] 中找到相關設定，
                    例如: {'enabled': True, 'time': '08:00'}
    """
    # 從主設定檔中取得鬧鐘功能的專屬設定
    alarm_config = config.get('alarm_clock', {})

    # 檢查鬧鐘功能是否在設定檔中被啟用
    if alarm_config.get('enabled', False):
        # 取得設定的鬧鐘時間，如果未設定則提供預設文字
        alarm_time = alarm_config.get('time', '未設定')
        
        # 印出觸發訊息到主控台
        # 這部分是目前的主要功能，用於提示開發者或使用者此功能已被呼叫
        print(f">>> [Alarm Clock] 鬧鐘功能已被觸發，設定時間: {alarm_time}")
        
        # TODO: 在此處擴充實際的鬧鐘觸發邏輯
        # 例如：
        # from alarm_sound_module import play_alarm_sound
        # play_alarm_sound()
        #
        # from phone_notify_module import send_phone_notification
        # send_phone_notification("鬧鐘響了！")
        pass
