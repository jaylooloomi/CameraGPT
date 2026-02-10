import time
import yaml
import os
import cv2
import shutil
import re
import subprocess
from datetime import datetime

import image_utils
import ai_backends
import email_notify
import line_notify_module
import phone_notify_module
import alarm_sound_module
import alarm_clock_module
from startup_dialog import MonitorConfigDialog

def check_trigger(trigger, response):
    """
    檢查 AI 回答是否觸發條件
    支援:
    1. 數值比較: >80, <50, >=30, <=100, =50
    2. 文字包含: "有", "看到"
    """
    if not trigger:
        return False
        
    trigger = str(trigger).strip()
    response = str(response).strip()
    
    # 1. 檢查是否為數學比較 (e.g., ">80", "<= 30.5", "> 80%")
    # Regex 抓取: Group 1 (Operator), Group 2 (Number)
    match = re.match(r'^([<>]=?|!=|=)(?:\s*)(\d+(?:\.\d+)?)', trigger)
    if match:
        operator = match.group(1)
        target_val = float(match.group(2))
        
        # 從 AI 回答中提取所有數字
        # 尋找像是 "60", "60.5", "60%" 這樣的數字
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", response)
        
        if not numbers:
            print(f"[Trigger Check] 警告: 條件為數值比較 '{trigger}'，但回答中找不到數字。回答: '{response}'")
            return False
            
        print(f"[Trigger Check] 數值比較模式: {operator} {target_val}，找到數字: {numbers}")
        
        # 檢查是否有任何一個數字符合條件
        for num_str in numbers:
            try:
                val = float(num_str)
                is_match = False
                if operator == '>':
                    if val > target_val: is_match = True
                elif operator == '<':
                    if val < target_val: is_match = True
                elif operator == '>=':
                    if val >= target_val: is_match = True
                elif operator == '<=':
                    if val <= target_val: is_match = True
                elif operator == '=' or operator == '==':
                    if abs(val - target_val) < 0.01: is_match = True
                elif operator == '!=':
                    if abs(val - target_val) > 0.01: is_match = True
                
                if is_match:
                    return True
            except ValueError:
                continue
        return False
        
    # 2. 文字匹配模式
    # 定義所有可能的中英文肯定和否定詞 (不區分大小寫)
    affirmative_responses = ["是", "yes", "對", "有"]
    negative_responses = ["否", "no", "錯", "沒有"]

    # 將觸發關鍵字標準化為 '是' 或 '否' 的意圖
    trigger_intent = None
    if trigger.lower() in [s.lower() for s in ["是", "yes", "對", "有"]]:
        trigger_intent = "是"
    elif trigger.lower() in [s.lower() for s in ["否", "no", "錯", "沒有"]]:
        trigger_intent = "否"

    response_lower = response.lower()

    if trigger_intent == "是":
        # 如果觸發意圖是 '是'，則回應中必須包含肯定詞，且不包含否定詞
        has_affirmative = any(keyword.lower() in response_lower for keyword in affirmative_responses)
        has_negative = any(keyword.lower() in response_lower for keyword in negative_responses)
        return has_affirmative and not has_negative
    elif trigger_intent == "否":
        # 如果觸發意圖是 '否'，則回應中必須包含否定詞，且不包含肯定詞
        has_negative = any(keyword.lower() in response_lower for keyword in negative_responses)
        has_affirmative = any(keyword.lower() in response_lower for keyword in affirmative_responses)
        return has_negative and not has_affirmative

    # 如果觸發關鍵字不是肯定或否定意圖，則回歸原始的直接包含判斷
    if trigger in response:
        return True
        
    return False

def kill_old_instances():
    """
    檢查並強制關閉其他正在執行的 camera_daemon.py 程序，
    以釋放被佔用的相機資源。
    """
    print("正在檢查是否有殘留的 CameraGPT 程序...")
    current_pid = os.getpid()
    try:
        # 使用 WMIC 查詢 python.exe 且包含 camera_daemon.py 的進程
        # 注意: wmic output 包含 header 和空行
        cmd = 'wmic process where "name=\'python.exe\' and commandline like \'%camera_daemon.py%\'" get processid'
        
        # 使用 subprocess 執行指令
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            # wmic 執行失敗或找不到符合的 (找不到時也可能 return 0 但 output 空)
            return

        output = stdout.decode('utf-8', errors='ignore')
        
        pids = []
        for line in output.splitlines():
            line = line.strip()
            if line.isdigit():
                pids.append(int(line))
        
        killed_count = 0
        for pid in pids:
            if pid != current_pid:
                print(f">>> 發現舊程序 PID: {pid}，嘗試強制關閉...")
                try:
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    killed_count += 1
                except Exception as e:
                    print(f"無法關閉 PID {pid}: {e}")
        
        if killed_count > 0:
            print(f">>> 已清理 {killed_count} 個舊程序，相機資源應已釋放。")
            time.sleep(1) # 給系統一點時間釋放資源
        else:
            print("未發現其他殘留程序。")
                
    except Exception as e:
        print(f"清理舊程序時發生錯誤 (此錯誤不影響主程式): {e}")

def perform_ai_analysis(ai_engine, image_path, config):
    """
    執行 AI 分析並處理結果 (回傳 True 表示任務達成，應停止監控)
    """
    question = config['prompt']['question']
    trigger_keyword = config['prompt']['trigger_keyword']
    system_prompt_text = config['system'].get('system_prompt', '')
    
    print("-" * 30)
    print(f"[Request] 詢問 AI: {question}")
    
    ai_answer = ai_engine.analyze_image(image_path, question, system_prompt_text)
    print(f"[Response] AI 回答: {ai_answer}")
    print("-" * 30)
    
    if check_trigger(trigger_keyword, ai_answer):
        print(f">>> 命中關鍵字 '{trigger_keyword}'，發送通知！")
        # Email 通知
        if config.get('email', {}).get('enabled', False):
            email_notify.send_email(config['email'], image_path, ai_answer)
        # Line 通知
        if config.get('line_notify', {}).get('enabled', False):
            line_notify_module.send_notification(config, f"警報：檢測到目標特徵！ AI 回答: {ai_answer}", image_path)
        # 電話通知
        if config.get('phone_notify', {}).get('enabled', False):
            phone_notify_module.send_notification(config, f"警報：檢測到目標特徵！ AI 回答: {ai_answer}", image_path)
        # 警報音效
        if config.get('alarm_sound', {}).get('enabled', False):
            alarm_sound_module.play_sound(config)
        # 鬧鐘功能
        if config.get('alarm_clock', {}).get('enabled', False):
            alarm_clock_module.trigger_alarm(config)

        print(">>> 任務達成，停止監控。")
        return True
    else:
        print(f">>> AI 回答 '{ai_answer}'，未觸發通知 (關鍵字: {trigger_keyword})。")
        return False

def load_config(path="config.yaml"):
    if not os.path.exists(path):
        print(f"找不到設定檔 {path}，請先建立。")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    print("=== CameraGPT Daemon 啟動中 ===")
    
    # 0. 強制清理舊程序 (釋放相機資源)
    kill_old_instances()
    
    # 清空 temp 資料夾
    if os.path.exists("temp"):
        print("正在清空 temp 資料夾...")
        shutil.rmtree("temp")
    os.makedirs("temp")

    config = load_config()
    if not config:
        return

    # 初始化 AI 後端 (提前至 GUI 之前，以便支援自動拆解功能)
    print("正在初始化 AI 後端...")
    try:
        ai_engine = ai_backends.get_ai_backend(config['ai'])
        print(f"已載入 AI 提供者: {config['ai']['provider']}")
    except Exception as e:
        print(f"AI 初始化失敗: {e}")
        return

    # === 啟動 GUI 設定視窗 ===
    print("等待使用者輸入監控需求...")
    default_q = config['prompt'].get('question', '')
    # 這裡我們不自動解析 config 中的限制，而是給一個空白或預設值，讓使用者確認
    default_constraint = "請只回答'是'或'否'。" 
    default_k = config['prompt'].get('trigger_keyword', '')
    default_s = config['prompt'].get('subject', '')
    
    dialog = MonitorConfigDialog(default_q, default_constraint, default_k, default_s, ai_backend=ai_engine)
    user_settings = dialog.show()
    
    if not user_settings:
        print("使用者取消或未輸入設定，程式終止。")
        return
        
    # 更新設定
    config['prompt']['question'] = user_settings['question']
    config['prompt']['trigger_keyword'] = user_settings['trigger_keyword']
    config['prompt']['subject'] = user_settings['subject']
    
    print(f"監控需求更新: {config['prompt']['question']}")
    print(f"識別項目: {config['prompt']['subject']}")
    if config['prompt']['trigger_keyword']:
        print(f"觸發關鍵字: {config['prompt']['trigger_keyword']}")

    # 自動尋找可用相機
    print("正在尋找可用攝影機...")
    working_cam_idx = image_utils.find_working_camera()
    if working_cam_idx is None:
        print("錯誤: 找不到可用的攝影機 (索引 0 或 1)。程式終止。")
        return
    
    print(f"已選擇攝影機索引: {working_cam_idx}")
    camera_idx = working_cam_idx
    
    interval = config['system']['interval']
    diff_threshold = config['system']['diff_threshold']
    
    # 初始化相機連接 (長連接模式)
    try:
        cap = image_utils.open_camera(camera_idx)
    except Exception as e:
        print(f"相機初始化失敗: {e}")
        return

    # === 確保相機穩定並抓取基準圖 ===
    print("正在暖機相機 (連續讀取 30 幀以穩定曝光)...")
    # 強制連續讀取，讓自動曝光 (AE) 有時間收斂
    for i in range(30):
        cap.read()
        time.sleep(0.1)
    
    try:
        # 照片 1 (這時曝光應該穩定了)
        last_frame = image_utils.capture_frame(cap)
        print("已抓取基準畫面 (照片1)")
    except Exception as e:
        print(f"基準畫面抓取失敗: {e}")
        return

    # === 初始檢查：立即分析第一張畫面 ===
    print(">>> 正在分析初始畫面...")
    temp_last_frame_path = image_utils.save_temp_image(last_frame, "initial_frame.jpg")
    
    # 檢查圖片中是否可以看到關鍵識別項目
    subject = config['prompt'].get('subject', '').strip()
    if subject:

        """
        print(f">>> 正在驗證關鍵識別項目: {subject} ...")
        check_prompt = f"圖中有沒有看到{subject}? 請只回答'是'或'否'。"
        
        max_retries = 3
        current_temp_image_path = temp_last_frame_path # 第一次使用初始畫面

        for attempt in range(1, max_retries + 1):
            if attempt > 1: # 第二次嘗試開始重新拍照
                print(f">>> 重新拍攝畫面進行驗證 (嘗試 {attempt}/{max_retries})... ")
                try:
                    new_frame = image_utils.capture_frame(cap)
                    current_temp_image_path = image_utils.save_temp_image(new_frame, "retry_initial_frame.jpg")
                except Exception as e:
                    print(f"重新拍攝畫面失敗: {e}。終止驗證。")
                    cap.release()
                    return

            print("-" * 30)
            print(f"[Request] 驗證詢問 (嘗試 {attempt}/{max_retries}): {check_prompt}")
            check_response = ai_engine.analyze_image(current_temp_image_path, check_prompt, config['system'].get('system_prompt', '')) # 傳入 system_prompt_text
            print(f"[Response] 驗證結果: {check_response}")
            print("-" * 30)
            
            if check_trigger("是", check_response): # 檢查是否為 '是'
                print(f">>> 確認畫面中包含: {subject}")
                break # 找到後跳出迴圈
            else:
                print(f">>> 第 {attempt} 次嘗試未找到 '{subject}'。")
                if attempt < max_retries:
                    print("等待 2 秒後重試...")
                    time.sleep(2)
                else:
                    print(f"!!! 錯誤: {max_retries} 次嘗試後仍找不到關鍵識別項目 '{subject}'。停止監控。")
                    cap.release()
                    return
        """
    if perform_ai_analysis(ai_engine, temp_last_frame_path, config):
        cap.release()
        return
    else:
        print(">>> 初始畫面未達成目標，繼續監控...")
        
    # 等待 5 秒 (interval)
    print(f"等待 {interval} 秒後抓取下一張...")
    time.sleep(interval)

    print(f"開始監控 (間隔: {interval}秒, 閾值: {diff_threshold}%)...")
    print("按 Ctrl+C 停止")

    try:
        while True:
            start_time = time.time()
            
            try:
                # 1. 抓取當前畫面 (照片2)
                current_frame = image_utils.capture_frame(cap)
                
                # 2. 比對像素變化 (回傳百分比)
                diff_score = image_utils.calculate_diff(last_frame, current_frame)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 畫面差異: {diff_score:.2f}%")

                # 3. 如果發生大量改變
                if diff_score > diff_threshold:
                    print(">>> 偵測到顯著變化，呼叫 AI 分析...")
                    
                    # 儲存暫存圖 (傳送照片2)
                    temp_img_path = image_utils.save_temp_image(current_frame, "alert_frame.jpg")
                    
                    # 4. 呼叫 AI API (使用共用邏輯)
                    if perform_ai_analysis(ai_engine, temp_img_path, config):
                        break
                    else:
                        print(">>> 尚未達成目標，繼續監控...")
                        
                # 更新基準畫面 (照片2 變成下一輪的照片1)
                # 使用 copy() 確保獨立記憶體空間，避免參照到被釋放的 buffer
                last_frame = current_frame.copy()

            except Exception as e:
                print(f"發生錯誤: {e}")
                # 如果是相機斷線，嘗試重連
                if "相機" in str(e) or "斷線" in str(e):
                    print("嘗試重新連接相機...")
                    try:
                        cap.release()
                        time.sleep(1)
                        cap = image_utils.open_camera(camera_idx)
                        # 重連後重新抓基準圖
                        last_frame = image_utils.capture_frame(cap)
                    except:
                        pass
            
            # 確保間隔時間
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n停止監控")
    finally:
        if 'cap' in locals() and cap is not None:
            cap.release()
            print("相機資源已釋放")

if __name__ == "__main__":
    main()
