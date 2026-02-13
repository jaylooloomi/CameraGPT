# -*- coding: utf-8 -*-
# 主程式: CameraGPT 背景守護程式
# 功能:
# 1. 定期使用攝影機拍攝畫面。
# 2. 比對前後畫面的差異，當差異超過閾值時觸發 AI 分析。
# 3. 呼叫指定的 AI 後端 (例如 Ollama, Gemini, OpenAI) 來分析畫面。
# 4. 根據 AI 的回答和預設的觸發條件，決定是否執行通知動作。
# 5. 支援多種通知方式，如 Email、Line Notify、電話等。

import time
import yaml
import os
import cv2
import shutil
import re
import subprocess
from datetime import datetime

# 匯入專案內的其他模組
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
    檢查 AI 的回應是否滿足觸發條件。

    此函數支援兩種主要的觸發模式：
    1.  **數值比較**:
        - 格式: ">80", "<=50.5", "=100", "!=0"
        - 它會從 AI 回應中提取第一個數字進行比較。
    2.  **文字匹配**:
        - 關鍵字: "是", "有", "否", "沒有" 等。
        - 它會判斷 AI 回應的意圖是肯定還是否定，並與觸發詞的意圖比對。
        - 如果觸發詞不是預設的肯定/否定詞，則進行簡單的文字包含判斷。

    :param trigger: 從設定檔讀取的觸發條件字串。
    :param response: AI 模型回傳的原始文字回應。
    :return: 布林值。如果滿足條件則為 True，否則為 False。
    """
    if not trigger:
        return False
        
    trigger = str(trigger).strip()
    response = str(response).strip()
    
    # --- 模式一: 數值比較 ---
    # 使用正規表示式來匹配 "運算子" + "數值" 的格式，例如 ">80", "<=30.5"
    match = re.match(r'^([<>]=?|!=|=)(?:\s*)(\d+(?:\.\d+)?)', trigger)
    if match:
        operator = match.group(1)  # 運算子，例如 ">", "<="
        target_val = float(match.group(2))  # 目標數值
        
        # 從 AI 的回應中提取所有數字 (包含整數、浮點數)
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", response)
        
        if not numbers:
            print(f"[Trigger Check] 警告: 觸發條件為數值比較 '{trigger}'，但 AI 回應中找不到任何數字。回答: '{response}'")
            return False
            
        print(f"[Trigger Check] 數值比較模式: 運算子='{operator}', 目標值={target_val}。從回應中找到的數字: {numbers}")
        
        # 遍歷所有找到的數字，只要有任何一個滿足條件，就回傳 True
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
                    if abs(val - target_val) < 0.01: is_match = True # 考慮浮點數精度問題
                elif operator == '!=':
                    if abs(val - target_val) > 0.01: is_match = True
                
                if is_match:
                    print(f"[Trigger Check] 命中! 回應中的數字 {val} {operator} {target_val} 條件成立。")
                    return True
            except ValueError:
                # 如果從回應中解析出的字串無法轉換為浮點數，則忽略
                continue
        # 如果所有數字都不符合條件，則返回 False
        return False
        
    # --- 模式二: 文字意圖匹配 ---
    # 定義一組常用於肯定與否定的詞彙
    affirmative_responses = ["是", "yes", "對", "有"]
    negative_responses = ["否", "no", "錯", "沒有"]

    # 標準化觸發詞的意圖 (是/否)
    trigger_intent = None
    if trigger.lower() in [s.lower() for s in affirmative_responses]:
        trigger_intent = "是"
    elif trigger.lower() in [s.lower() for s in negative_responses]:
        trigger_intent = "否"

    response_lower = response.lower()

    # 進行意圖判斷
    if trigger_intent == "是":
        # 如果觸發意圖為 "是"，則 AI 回應需包含肯定詞，且不能包含否定詞，以避免歧義
        has_affirmative = any(keyword.lower() in response_lower for keyword in affirmative_responses)
        has_negative = any(keyword.lower() in response_lower for keyword in negative_responses)
        return has_affirmative and not has_negative
    elif trigger_intent == "否":
        # 如果觸發意圖為 "否"，則 AI 回應需包含否定詞，且不能包含肯定詞
        has_negative = any(keyword.lower() in response_lower for keyword in negative_responses)
        has_affirmative = any(keyword.lower() in response_lower for keyword in affirmative_responses)
        return has_negative and not has_affirmative

    # --- 模式三: 原始文字包含判斷 ---
    # 如果觸發詞不是上述的特定意圖詞，則退回最簡單的字串包含判斷
    if trigger in response:
        return True
        
    return False

def kill_old_instances():
    """
    (僅限 Windows) 檢查並強制關閉任何先前未正常關閉的 camera_daemon.py 程序。
    
    主要目的:
    - 解決攝影機資源被舊程序佔用的問題。在程式異常退出時，攝影機可能不會被正確釋放，
      導致新啟動的程式無法存取攝影機。
    
    運作方式:
    - 使用 Windows 的 `wmic` 指令查詢所有正在運行的 `python.exe` 程序。
    - 過濾出命令列中包含 `camera_daemon.py` 的程序。
    - 取得這些程序的 PID (Process ID)。
    - 使用 `taskkill` 指令強制終止所有非當前程序的舊程序。
    """
    print("正在檢查是否有殘留的 CameraGPT 程序...")
    current_pid = os.getpid()
    try:
        # WMIC 指令: 查詢所有 python.exe 程序，並過濾出命令列 (commandline) 包含 'camera_daemon.py' 的
        cmd = 'wmic process where "name=\'python.exe\' and commandline like \'%camera_daemon.py%\'" get processid'
        
        process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if process.returncode != 0:
            print("[Kill Old] wmic 指令執行失敗或找不到符合的程序。")
            return

        output = stdout.decode('utf-8', errors='ignore')
        
        # 解析 WMIC 的輸出，提取 PID
        pids = []
        for line in output.splitlines():
            line = line.strip()
            if line.isdigit(): # PID 應為數字
                pids.append(int(line))
        
        killed_count = 0
        for pid in pids:
            if pid != current_pid: # 避免關閉自己
                print(f">>> 發現舊程序 PID: {pid}，嘗試強制關閉...")
                try:
                    # 使用 taskkill 強制終止程序
                    subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    killed_count += 1
                except Exception as e:
                    print(f"無法關閉 PID {pid}: {e}")
        
        if killed_count > 0:
            print(f">>> 已清理 {killed_count} 個舊程序，相機資源應已釋放。")
            time.sleep(1) # 給系統一點時間來實際釋放硬體資源
        else:
            print("未發現其他殘留程序。")
                
    except Exception as e:
        print(f"清理舊程序時發生錯誤 (此錯誤不影響主程式): {e}")

def perform_ai_analysis(ai_engine, image_path, config):
    """
    執行核心的 AI 分析流程並根據結果觸發相應的通知。

    :param ai_engine: 已初始化的 AI 後端物件 (例如 OllamaBackend, GeminiBackend)。
    :param image_path: 要分析的圖片檔案路徑。
    :param config: 應用程式的設定檔字典。
    :return: 布林值。如果 AI 回應觸發了條件，則返回 True，表示任務完成；否則返回 False。
    """
    # 從設定檔中讀取 AI 分析所需的問題、觸發關鍵字和系統提示
    question = config['prompt']['question']
    trigger_keyword = config['prompt']['trigger_keyword']
    system_prompt_text = config['system'].get('system_prompt', '')
    
    print("-" * 30)
    print(f"[Request] 正在詢問 AI: {question}")
    
    # 呼叫 AI 引擎的 analyze_image 方法進行分析
    ai_answer = ai_engine.analyze_image(image_path, question, system_prompt_text)
    print(f"[Response] AI 回答: {ai_answer}")
    print("-" * 30)
    
    # 檢查 AI 的回答是否觸發了設定的條件
    if check_trigger(trigger_keyword, ai_answer):
        print(f">>> 命中觸發條件 '{trigger_keyword}'，啟動通知程序！")
        
        # 根據設定檔，依序觸發各種通知模組
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
        # 鬧鐘功能 (預留)
        if config.get('alarm_clock', {}).get('enabled', False):
            alarm_clock_module.trigger_alarm(config)

        print(">>> 任務達成，停止監控。")
        return True # 表示任務已完成
    else:
        print(f">>> AI 回應 '{ai_answer}' 未觸發通知 (條件: {trigger_keyword})。")
        return False # 表示未達到觸發條件，應繼續監控

def load_config(path="config.yaml"):
    """
    從指定的路徑載入 YAML 設定檔。

    :param path: YAML 檔案的路徑。
    :return: 包含設定的字典，如果檔案不存在則返回 None。
    """
    if not os.path.exists(path):
        print(f"錯誤: 找不到設定檔 {path}，請確保設定檔存在。")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def main():
    """
    主執行函數。
    """
    print("=== CameraGPT Daemon 啟動中 ===")
    
    # --- 步驟 0: 環境準備 ---
    # 強制清理可能殘留的舊程序，以確保攝影機資源可用
    kill_old_instances()
    
    # 清空並重建用於儲存暫存圖片的 temp 資料夾
    if os.path.exists("temp"):
        print("正在清空 temp 資料夾...")
        shutil.rmtree("temp")
    os.makedirs("temp")

    # --- 步驟 1: 載入設定與初始化 AI ---
    config = load_config()
    if not config:
        return

    print("正在初始化 AI 後端...")
    try:
        ai_engine = ai_backends.get_ai_backend(config['ai'])
        print(f"已成功載入 AI 提供者: {config['ai']['provider']}")
    except Exception as e:
        print(f"AI 初始化失敗: {e}")
        return

    # --- 步驟 2: 啟動 GUI 設定視窗，讓使用者確認或修改監控任務 ---
    print("等待使用者輸入監控需求...")
    # 從設定檔讀取預設值
    default_q = config['prompt'].get('question', '')
    default_constraint = "請只回答'是'或'否'。" # GUI 中給予一個通用的預設限制
    default_k = config['prompt'].get('trigger_keyword', '')
    default_s = config['prompt'].get('subject', '')
    
    # 建立並顯示 GUI 對話框
    dialog = MonitorConfigDialog(default_q, default_constraint, default_k, default_s, ai_backend=ai_engine)
    user_settings = dialog.show()
    
    # 如果使用者關閉了視窗或點擊取消，則結束程式
    if not user_settings:
        print("使用者取消或未輸入設定，程式終止。")
        return
        
    # 將使用者在 GUI 中輸入的設定更新回 config 變數中
    config['prompt']['question'] = user_settings['question']
    config['prompt']['trigger_keyword'] = user_settings['trigger_keyword']
    config['prompt']['subject'] = user_settings['subject']
    
    print("使用者設定已更新:")
    print(f"  - 監控問題: {config['prompt']['question']}")
    print(f"  - 識別主體: {config['prompt']['subject']}")
    if config['prompt']['trigger_keyword']:
        print(f"  - 觸發條件: {config['prompt']['trigger_keyword']}")

    # --- 步驟 3: 初始化攝影機 ---
    print("正在尋找可用的攝影機...")
    working_cam_idx = image_utils.find_working_camera()
    if working_cam_idx is None:
        print("錯誤: 找不到任何可用的攝影機。程式終止。")
        return
    
    print(f"已選擇攝影機索引: {working_cam_idx}")
    camera_idx = working_cam_idx
    
    # 從設定檔讀取監控間隔和畫面差異閾值
    interval = config['system']['interval']
    diff_threshold = config['system']['diff_threshold']
    
    try:
        # 開啟與攝影機的連接
        cap = image_utils.open_camera(camera_idx)
    except Exception as e:
        print(f"攝影機初始化失敗: {e}")
        return

    # --- 步驟 4: 相機暖機與抓取基準畫面 ---
    print("正在暖機相機 (連續讀取 30 幀以穩定自動曝光)...")
    # 連續讀取多幀畫面，給予相機的自動曝光(AE)和自動白平衡(AWB)功能足夠的時間來穩定
    for i in range(30):
        cap.read()
        time.sleep(0.1)
    
    try:
        # 拍攝第一張基準畫面 (此時畫面應該是穩定且清晰的)
        last_frame = image_utils.capture_frame(cap)
        print("已成功抓取基準畫面 (照片1)")
    except Exception as e:
        print(f"基準畫面抓取失敗: {e}")
        cap.release()
        return

    # --- 步驟 5: 初始畫面分析 ---
    # 在進入主循環前，先對第一張基準畫面進行一次分析
    # 這可以確保如果監控目標一開始就存在，能夠立即觸發警報
    print(">>> 正在分析初始畫面...")
    temp_last_frame_path = image_utils.save_temp_image(last_frame, "initial_frame.jpg")
    
    # [備用邏輯] 驗證初始畫面中是否包含監控主體 (此段程式碼目前被註解，可視需求啟用)
    # subject = config['prompt'].get('subject', '').strip()
    # if subject:
    #     ... (驗證邏輯) ...

    # 對初始畫面執行一次完整的 AI 分析與觸發檢查
    if perform_ai_analysis(ai_engine, temp_last_frame_path, config):
        cap.release() # 如果任務達成，釋放相機並結束程式
        return
    else:
        print(">>> 初始畫面未達成目標，準備進入持續監控模式...")
        
    # --- 步驟 6: 進入主監控迴圈 ---
    print(f"等待 {interval} 秒後開始持續監控...")
    time.sleep(interval)

    print("-" * 50)
    print(f"監控已開始 (間隔: {interval}秒, 變化閾值: {diff_threshold}%)")
    print("提示: 按下 Ctrl+C 可以手動停止程式。")
    print("-" * 50)

    try:
        while True:
            start_time = time.time()
            
            try:
                # 1. 抓取當前畫面 (照片2)
                current_frame = image_utils.capture_frame(cap)
                
                # 2. 與上一張基準畫面比對像素差異百分比
                diff_score = image_utils.calculate_diff(last_frame, current_frame)
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 畫面差異: {diff_score:.2f}%")

                # 3. 如果差異大於設定的閾值，則觸發 AI 分析
                if diff_score > diff_threshold:
                    print(f">>> 偵測到顯著變化 ({diff_score:.2f}% > {diff_threshold}%)，呼叫 AI 進行分析...")
                    
                    # 將當前畫面儲存為暫存圖片，以供 AI 分析
                    temp_img_path = image_utils.save_temp_image(current_frame, "alert_frame.jpg")
                    
                    # 4. 呼叫 AI 分析函數
                    if perform_ai_analysis(ai_engine, temp_img_path, config):
                        break # 如果任務達成，跳出迴圈以結束程式
                    else:
                        print(">>> AI 分析後未達成目標，將繼續監控...")
                        
                # 5. 更新基準畫面: 將當前畫面設為下一輪比對的基準
                # 必須使用 .copy()，確保複製的是影像資料本身，而不是記憶體參照
                last_frame = current_frame.copy()

            except Exception as e:
                print(f"主迴圈發生錯誤: {e}")
                # 簡單的錯誤處理: 如果錯誤訊息和相機有關，嘗試重新連接
                if "相機" in str(e) or "斷線" in str(e):
                    print("偵測到相機可能斷線，嘗試重新連接...")
                    try:
                        cap.release()
                        time.sleep(1)
                        cap = image_utils.open_camera(camera_idx)
                        # 重連成功後，重新抓取基準畫面
                        last_frame = image_utils.capture_frame(cap)
                        print("相機已重新連接並抓取新基準畫面。")
                    except Exception as recon_e:
                        print(f"重新連接失敗: {recon_e}，等待下一輪重試...")
                        pass
            
            # 控制迴圈頻率，確保每次執行的間隔大致符合設定值
            elapsed = time.time() - start_time
            sleep_time = max(0, interval - elapsed)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n使用者手動中斷程式，停止監控。")
    finally:
        # --- 步驟 7: 清理資源 ---
        # 程式結束前，不論是正常結束還是發生錯誤，都確保釋放攝影機資源
        if 'cap' in locals() and cap is not None and cap.isOpened():
            cap.release()
            print("攝影機資源已成功釋放。")

# Python 的主程式進入點
if __name__ == "__main__":
    main()
