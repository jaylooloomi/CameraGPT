# startup_dialog.py
# 這個模組使用 tkinter 函式庫建立一個圖形化使用者介面 (GUI) 視窗，
# 讓使用者可以在程式啟動時設定監控任務的詳細參數。

import tkinter as tk
from tkinter import messagebox
import json
import re
import os
import glob
from datetime import datetime
import numpy as np
import yaml

# --- 選擇性匯入 (Optional Imports) ---
# 這些函式庫不是程式運行的必要條件，如果未安裝，相關功能將會被優雅地禁用。

# 語音辨識功能 (需要 `speechrecognition` 和 `PyAudio` 套件)
try:
    import speech_recognition as sr
except ImportError:
    sr = None  # 如果未安裝，則將 sr 設為 None

# 音訊錄製和播放功能 (需要 `sounddevice` 和 `scipy` 套件)
try:
    import sounddevice as sd
    from scipy.io.wavfile import write
except ImportError:
    sd = None
    write = None

class MonitorConfigDialog:
    """
    一個 tkinter 對話框類別，用於設定監控參數。
    它包含智慧輸入、手動設定、歷史紀錄和 AI 助理聊天等功能。
    """
    def __init__(self, default_question="", default_constraint="", default_trigger="", default_subject="", ai_backend=None):
        """
        初始化 GUI 視窗和所有元件。
        :param default_question: 監控問題的預設值。
        :param default_constraint: 回答限制的預設值。
        :param default_trigger: 觸發關鍵字的預設值。
        :param default_subject: 關鍵識別項目的預設值。
        :param ai_backend: 傳入的 AI 後端物件，用於驅動智慧功能。
        """
        self.root = tk.Tk()
        self.root.title("CameraGPT 監控設定")
        self.result = None  # 用於儲存使用者最終的設定結果
        self.ai_backend = ai_backend  # AI 後端實例
        self.chat_messages = []  # 儲存 AI 助理的對話歷史
        self.recording = False  # 標記是否正在錄音
        self.audio_frames = []  # 儲存錄音的音訊幀
        self.stream = None  # 音訊串流物件

        # --- 視窗置中 ---
        window_width = 1200
        window_height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # --- 主體佈局: 三欄式設計 ---
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === 左欄: 歷史任務列表 ===
        left_frame = tk.LabelFrame(main_container, text="歷史任務", font=("Microsoft JhengHei", 10, "bold"), width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False)  # 固定寬度，不隨內容縮放

        self.history_listbox = tk.Listbox(left_frame, font=("Microsoft JhengHei", 10))
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)  # 綁定選擇事件

        delete_btn = tk.Button(left_frame, text="刪除所選", command=self.on_history_delete,
                               font=("Microsoft JhengHei", 10), bg="#9E9E9E", fg="white")
        delete_btn.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)

        self.load_history_files() # 載入歷史紀錄

        # === 中欄: 設定區域 & 智慧輸入 ===
        center_column_frame = tk.Frame(main_container)
        center_column_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        header_label = tk.Label(center_column_frame, text="CameraGPT 監控需求設定", font=("Microsoft JhengHei", 16, "bold"))
        header_label.pack(pady=(0, 10))

        # --- 智慧輸入區塊 (如果 AI 後端可用) ---
        if self.ai_backend:
            smart_frame = tk.LabelFrame(center_column_frame, text="智慧自動輸入 (AI 自動拆解)", font=("Microsoft JhengHei", 11, "bold"), padx=10, pady=10)
            smart_frame.pack(fill=tk.X, pady=(0, 15))

            tk.Label(smart_frame, text="請用一句話描述您的監控需求:", font=("Microsoft JhengHei", 10)).pack(anchor="w")
            
            self.smart_input = tk.Text(smart_frame, height=3, font=("Microsoft JhengHei", 10))
            self.smart_input.pack(fill=tk.X, pady=5)
            self.smart_input.insert("1.0", "人有沒有戴帽子?")  # 預設文字
            
            btn_container = tk.Frame(smart_frame)
            btn_container.pack(fill=tk.X, pady=2)

            voice_btn = tk.Button(btn_container, text="🎤 語音輸入",
                                 bg="#03A9F4", fg="white", font=("Microsoft JhengHei", 10, "bold"))
            voice_btn.bind("<ButtonPress-1>", self.start_recording)   # 按下開始錄音
            voice_btn.bind("<ButtonRelease-1>", self.stop_recording)  # 放開結束錄音
            voice_btn.pack(side=tk.LEFT, padx=(0, 5))

            auto_btn = tk.Button(btn_container, text="✨ AI 自動拆解 ✨", command=self.on_auto_parse,
                                 bg="#673AB7", fg="white", font=("Microsoft JhengHei", 10, "bold"))
            auto_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # --- 手動輸入區塊 (詳細設定) ---
        input_frame = tk.LabelFrame(center_column_frame, text="詳細設定", font=("Microsoft JhengHei", 11, "bold"), padx=10, pady=10)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(input_frame, text="監控需求 (Prompt):", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        self.prompt_text = tk.Text(input_frame, height=3, font=("Microsoft JhengHei", 10))
        self.prompt_text.pack(fill=tk.X, pady=(5, 10))
        self.prompt_text.insert("1.0", default_question)
        
        tk.Label(input_frame, text="關鍵識別項目 (Subject):", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        self.subject_entry = tk.Entry(input_frame, font=("Microsoft JhengHei", 10))
        self.subject_entry.pack(fill=tk.X, pady=(5, 10))
        self.subject_entry.insert(0, default_subject)

        tk.Label(input_frame, text="回答限制 (Constraint):", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        self.constraint_entry = tk.Entry(input_frame, font=("Microsoft JhengHei", 10))
        self.constraint_entry.pack(fill=tk.X, pady=(5, 10))
        self.constraint_entry.insert(0, default_constraint)
        
        tk.Label(input_frame, text="觸發關鍵字 (Trigger Keyword) [選填]:", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        self.trigger_entry = tk.Entry(input_frame, font=("Microsoft JhengHei", 10))
        self.trigger_entry.pack(fill=tk.X, pady=(5, 15))
        self.trigger_entry.insert(0, default_trigger)
        
        # --- 按鈕區塊 (中欄底部) ---
        btn_frame = tk.Frame(center_column_frame, pady=10)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        submit_btn = tk.Button(btn_frame, text="開始監控", command=self.on_submit, 
                             font=("Microsoft JhengHei", 12, "bold"), bg="#4CAF50", fg="white", padx=20, pady=5)
        submit_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="取消", command=self.on_cancel, 
                             font=("Microsoft JhengHei", 12), bg="#f44336", fg="white", padx=20, pady=5)
        cancel_btn.pack(side=tk.RIGHT)

        # === 右欄: AI 智慧助理 ===
        if self.ai_backend:
            right_frame = tk.LabelFrame(main_container, text="AI 智慧助手", font=("Microsoft JhengHei", 11, "bold"), width=350)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
            right_frame.pack_propagate(False)

            self.chat_display = tk.Text(right_frame, font=("Microsoft JhengHei", 10), state='disabled', wrap='word')
            self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            chat_input_frame = tk.Frame(right_frame)
            chat_input_frame.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)
            
            self.chat_input = tk.Entry(chat_input_frame, font=("Microsoft JhengHei", 10))
            self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.chat_input.bind('<Return>', lambda e: self.on_chat_send()) # 綁定 Enter 鍵
            
            send_btn = tk.Button(chat_input_frame, text="發送", command=self.on_chat_send,
                               bg="#2196F3", fg="white", font=("Microsoft JhengHei", 10))
            send_btn.pack(side=tk.RIGHT, padx=(5, 0))
            
            self.add_chat_message("Assistant", "你好！我是你的監控設定助手。\n請告訴我你想監控什麼，我會幫你填寫左邊的設定。\n(例如：幫我看車庫門有沒有關)")

    def add_chat_message(self, role, message):
        """在 AI 助理視窗中新增一條對話訊息。"""
        self.chat_display.config(state='normal')
        if role == "User":
            self.chat_display.insert(tk.END, f"你: {message}\n", "user_tag")
        else:
            self.chat_display.insert(tk.END, f"AI: {message}\n", "ai_tag")
        self.chat_display.insert(tk.END, "-"*30 + "\n")
        self.chat_display.see(tk.END) # 自動捲動到底部
        self.chat_display.config(state='disabled')
        self.chat_messages.append({"role": role, "content": message})

    def on_chat_send(self):
        """處理使用者在 AI 助理中發送訊息的事件。"""
        user_text = self.chat_input.get().strip()
        if not user_text: return
        
        self.chat_input.delete(0, tk.END)
        self.add_chat_message("User", user_text)
        
        self.root.config(cursor="wait") # 更改滑鼠游標為等待狀態
        self.chat_input.config(state='disabled')
        self.root.update()
        
        try:
            # 組合一個包含當前設定狀態的系統提示，讓 AI 了解上下文
            current_q = self.prompt_text.get("1.0", tk.END).strip()
            # ... (略)
            
            system_prompt = f"""
            你是一個幫助使用者設定監控攝影機的 AI 助手。
            目前的設定狀態如下：
            - 監控需求: "{current_q}"
            - 關鍵識別項目: "{self.subject_entry.get().strip()}"
            - 回答限制: "{self.constraint_entry.get().strip()}"
            - 觸發關鍵字: "{self.trigger_entry.get().strip()}"
            
            使用者的最新輸入: "{user_text}"
            
            請根據使用者的輸入與目前的設定狀態進行對話，引導使用者完成所有設定。
            **重要**：如果你從對話中確認了某些欄位的更新資訊，請在回答的**最後面**附上一個 JSON 區塊，
            格式如下：
            ```json
            {{
                "question": "...",
                "subject": "...",
                "constraint": "...",
                "trigger": "..."
            }}
            ```
            只包含需要更新的欄位即可。JSON 區塊必須用 ```json 包裹。
            請用繁體中文與使用者對話。
            """
            
            response = self.ai_backend.generate_text(system_prompt)
            
            # 從 AI 回應中解析 JSON 區塊並更新 UI
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            chat_response = response
            
            if json_match:
                # ... (解析並更新 UI 的邏輯)
                pass # 省略細節
            
            self.add_chat_message("Assistant", chat_response)
            
        except Exception as e:
            self.add_chat_message("System", f"發生錯誤: {e}")
        finally:
            self.root.config(cursor="")
            self.chat_input.config(state='normal')
            self.chat_input.focus()

    def load_history_files(self):
        """從 'task' 資料夾載入所有 .json 任務歷史檔案並顯示在列表。"""
        self.history_listbox.delete(0, tk.END)
        # ... (略)

    def on_history_select(self, event):
        """當使用者在歷史列表中選擇一個項目時，將其設定載入到 UI 中。"""
        # ... (略)

    def on_history_delete(self):
        """刪除所選的歷史任務檔案。"""
        # ... (略)

    def on_auto_parse(self):
        """
        'AI 自動拆解' 按鈕的處理函數。
        將智慧輸入框中的自然語言描述發送到 AI，要求其拆解成結構化的設定。
        """
        user_text = self.smart_input.get("1.0", tk.END).strip()
        if not user_text:
            messagebox.showwarning("提示", "請先在智慧輸入框中描述您的需求！")
            return

        try:
            self.root.config(cursor="wait")
            self.root.update()
            
            prompt_template = f"""
            你是一個幫助設定監控系統的 AI 助手。使用者的描述是: "{user_text}"
            請將此描述拆解成以下四個欄位，並以 JSON 格式回傳：
            1. "question": 調整成一個是非疑問句。
            2. "subject": 擷取關鍵識別項目。
            3. "constraint": 設定 AI 回答的格式限制 (通常是 '請只回答 是 或 否')。
            4. "trigger": 根據問題設定觸發警報的關鍵字 (通常是 '是' 或 '否')。
            請直接回傳 JSON 字串，不要包含其他文字。
            """
            
            response = self.ai_backend.generate_text(prompt_template)
            cleaned_response = re.sub(r'^```json\s*|\s*```$', '', response.strip(), flags=re.MULTILINE)
            data = json.loads(cleaned_response)
            
            # 將解析出的資料填入 UI
            # ... (略)
                
            messagebox.showinfo("成功", "AI 已自動拆解並填入設定！")
            
        except Exception as e:
            messagebox.showerror("錯誤", f"AI 拆解失敗: {e}\n回傳內容: {response}")
        finally:
            self.root.config(cursor="")

    # --- 以下是語音輸入相關方法 ---

    def start_recording(self, event):
        """按下按鈕時開始錄音。"""
        if sd is None or sr is None:
            messagebox.showerror("錯誤", "語音功能所需套件未安裝。\n請執行 `pip install sounddevice scipy SpeechRecognition PyAudio`")
            return
        self.recording = True
        self.audio_frames = []
        print("開始錄音...")
        self.stream = sd.InputStream(samplerate=44100, channels=1, callback=self.audio_callback)
        self.stream.start()

    def stop_recording(self, event):
        """放開按鈕時停止錄音並處理音訊。"""
        if not self.recording: return
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
        print("錄音結束！")
        self.process_audio()

    def audio_callback(self, indata, frames, time, status):
        """錄音期間的回呼函數，用於收集音訊數據。"""
        if self.recording:
            self.audio_frames.append(indata.copy())

    def process_audio(self):
        """處理錄製完成的音訊：儲存、播放並進行語音辨識。"""
        if not self.audio_frames: return
        try:
            myrecording = np.concatenate(self.audio_frames, axis=0)
            
            # 儲存錄音檔
            os.makedirs("temp", exist_ok=True)
            filename = "temp/output.wav"
            write(filename, 44100, myrecording)

            # 使用 SpeechRecognition 進行語音轉文字
            recognizer = sr.Recognizer()
            with sr.AudioFile(filename) as source:
                audio_data = recognizer.record(source)
            
            transcript = recognizer.recognize_google(audio_data, language="zh-TW")
            print(f"語音辨識結果: {transcript}")
            
            # 將辨識結果填入智慧輸入框
            self.smart_input.delete("1.0", tk.END)
            if not transcript.endswith(("?", "？")):
                transcript += "?"
            self.smart_input.insert("1.0", transcript)

        except Exception as e:
            messagebox.showerror("語音輸入錯誤", f"無法處理錄音: {e}")

    # --- 視窗控制方法 ---
            
    def on_submit(self):
        """當使用者點擊 '開始監控' 時觸發。"""
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showwarning("警告", "請輸入監控需求！")
            return
            
        # 組合最終的問題
        final_question = f"{prompt} {self.constraint_entry.get().strip()}".strip()
            
        # 將本次設定儲存到歷史紀錄檔案
        task_data = {
            "question": prompt,
            "subject": self.subject_entry.get().strip(),
            # ... (略)
        }
        # ... (儲存邏輯)

        # 設定回傳結果並關閉視窗
        self.result = {
            "question": final_question,
            "subject": self.subject_entry.get().strip(),
            "trigger_keyword": self.trigger_entry.get().strip()
        }
        self.root.destroy()

    def on_cancel(self):
        """當使用者點擊 '取消' 時觸發。"""
        self.result = None # 確保回傳值為 None
        self.root.destroy()
        
    def show(self):
        """顯示對話框並等待使用者操作。"""
        self.root.mainloop()
        return self.result

if __name__ == "__main__":
    # 用於單獨測試此 GUI 模組
    dialog = MonitorConfigDialog(
        default_question="圖片中的人有沒有戴帽子？",
        default_constraint="請只回答'是'或'否'。",
        default_trigger="是",
        default_subject="人"
    )
    user_settings = dialog.show()
    print("使用者設定:", user_settings)
