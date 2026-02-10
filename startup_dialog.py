import tkinter as tk
from tkinter import messagebox
import json
import re
import os
import glob
from datetime import datetime
import numpy as np
import yaml
# Optional speech recognition for voice input (requires `speechrecognition` package)
try:
    import speech_recognition as sr
except Exception:
    sr = None  # If the package is not installed, voice input will be disabled gracefully

# Imports for audio recording and playback
try:
    import sounddevice as sd
    from scipy.io.wavfile import write
except Exception:
    sd = None
    write = None

class MonitorConfigDialog:
    def __init__(self, default_question="", default_constraint="", default_trigger="", default_subject="", ai_backend=None):
        self.root = tk.Tk()
        self.root.title("CameraGPT 監控設定")
        self.result = None
        self.ai_backend = ai_backend
        self.chat_messages = [] # Store chat context
        self.recording = False
        self.audio_frames = []
        self.stream = None
        
        # Center the window
        window_width = 1200
        window_height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
        
        # Main Layout: 3 Columns
        main_container = tk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # === Left Column: History List ===
        left_frame = tk.LabelFrame(main_container, text="歷史任務", font=("Microsoft JhengHei", 10, "bold"), width=200)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_frame.pack_propagate(False) # 固定寬度

        self.history_listbox = tk.Listbox(left_frame, font=("Microsoft JhengHei", 10))
        self.history_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)

        # Delete Button
        delete_btn = tk.Button(left_frame, text="刪除所選", command=self.on_history_delete,
                             font=("Microsoft JhengHei", 10), bg="#9E9E9E", fg="white")
        delete_btn.pack(fill=tk.X, padx=5, pady=5, side=tk.BOTTOM)

        # Load history files
        self.load_history_files()

        # === Center Column: Settings & Smart Input ===
        center_column_frame = tk.Frame(main_container)
        center_column_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Header
        header_label = tk.Label(center_column_frame, text="CameraGPT 監控需求設定", font=("Microsoft JhengHei", 16, "bold"))
        header_label.pack(pady=(0, 10))

        # === Smart Input Area ===
        if self.ai_backend:
            smart_frame = tk.LabelFrame(center_column_frame, text="智慧自動輸入 (AI 自動拆解)", font=("Microsoft JhengHei", 11, "bold"), padx=10, pady=10)
            smart_frame.pack(fill=tk.X, pady=(0, 15))

            tk.Label(smart_frame, text="請輸入您的完整需求 (例如: 人有沒有戴帽子?):", font=("Microsoft JhengHei", 10)).pack(anchor="w")
            
            self.smart_input = tk.Text(smart_frame, height=3, font=("Microsoft JhengHei", 10))
            self.smart_input.pack(fill=tk.X, pady=5)
            self.smart_input.insert("1.0", "人有沒有戴帽子?") # Set default text            
            # Container for the two buttons (voice + auto parse) to keep them on the same line
            btn_container = tk.Frame(smart_frame)
            btn_container.pack(fill=tk.X, pady=2)

            # Voice input button (only enabled if speech_recognition is available)
            # Always enable the voice button; on click we will check if SpeechRecognition is available.
            voice_btn = tk.Button(btn_container, text="🎤 語音輸入",
                                 bg="#03A9F4", fg="white", font=("Microsoft JhengHei", 10, "bold"))
            voice_btn.bind("<ButtonPress-1>", self.start_recording)
            voice_btn.bind("<ButtonRelease-1>", self.stop_recording)
            voice_btn.pack(side=tk.LEFT, padx=(0, 5))

            auto_btn = tk.Button(btn_container, text="✨ AI 自動拆解 ✨", command=self.on_auto_parse,
                                 bg="#673AB7", fg="white", font=("Microsoft JhengHei", 10, "bold"))
            auto_btn.pack(side=tk.RIGHT, padx=(5, 0))
        
        # === Manual Input Area (Detailed Settings) ===
        input_frame = tk.LabelFrame(center_column_frame, text="詳細設定", font=("Microsoft JhengHei", 11, "bold"), padx=10, pady=10)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(input_frame, text="監控需求 (Prompt):", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        
        self.prompt_text = tk.Text(input_frame, height=3, font=("Microsoft JhengHei", 10))
        self.prompt_text.pack(fill=tk.X, pady=(5, 10))
        self.prompt_text.insert("1.0", default_question)
        
        # Subject Input (Key Identification Item)
        tk.Label(input_frame, text="關鍵識別項目 (Key Identification Item):", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        
        self.subject_entry = tk.Entry(input_frame, font=("Microsoft JhengHei", 10))
        self.subject_entry.pack(fill=tk.X, pady=(5, 10))
        self.subject_entry.insert(0, "人") # Set default subject

        # Constraint Input
        tk.Label(input_frame, text="回答限制 (例如: 請只回答'是'或'否'):", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        
        self.constraint_entry = tk.Entry(input_frame, font=("Microsoft JhengHei", 10))
        self.constraint_entry.pack(fill=tk.X, pady=(5, 10))
        self.constraint_entry.insert(0, default_constraint)
        
        # Trigger Keyword Input
        tk.Label(input_frame, text="觸發關鍵字 (Trigger Keyword) [選填]:", font=("Microsoft JhengHei", 12)).pack(anchor="w")
        
        self.trigger_entry = tk.Entry(input_frame, font=("Microsoft JhengHei", 10))
        self.trigger_entry.pack(fill=tk.X, pady=(5, 15))
        self.trigger_entry.insert(0, default_trigger)
        
        # Buttons (Bottom of Center Column)
        btn_frame = tk.Frame(center_column_frame, pady=10)
        btn_frame.pack(fill=tk.X)
        
        submit_btn = tk.Button(btn_frame, text="開始監控", command=self.on_submit, 
                             font=("Microsoft JhengHei", 12, "bold"), 
                             bg="#4CAF50", fg="white", padx=20, pady=5)
        submit_btn.pack(side=tk.RIGHT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="取消", command=self.on_cancel, 
                             font=("Microsoft JhengHei", 12), 
                             bg="#f44336", fg="white", padx=20, pady=5)
        cancel_btn.pack(side=tk.RIGHT)

        # === Right Column: AI Chat ===
        if self.ai_backend:
            right_frame = tk.LabelFrame(main_container, text="AI 智慧助手", font=("Microsoft JhengHei", 11, "bold"), width=350)
            right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
            right_frame.pack_propagate(False)

            # Chat History
            self.chat_display = tk.Text(right_frame, font=("Microsoft JhengHei", 10), state='disabled', wrap='word')
            self.chat_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Chat Input
            chat_input_frame = tk.Frame(right_frame)
            chat_input_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self.chat_input = tk.Entry(chat_input_frame, font=("Microsoft JhengHei", 10))
            self.chat_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.chat_input.bind('<Return>', lambda e: self.on_chat_send())
            
            send_btn = tk.Button(chat_input_frame, text="發送", command=self.on_chat_send,
                               bg="#2196F3", fg="white", font=("Microsoft JhengHei", 10))
            send_btn.pack(side=tk.RIGHT, padx=(5, 0))
            
            # Initial Greeting
            self.add_chat_message("Assistant", "你好！我是你的監控設定助手。請告訴我你想監控什麼？\n(例如：幫我看車庫門有沒有關)\n請注意：所有回答都請用 '是' 或 '否'。")

    def add_chat_message(self, role, message):
        self.chat_display.config(state='normal')
        if role == "User":
            self.chat_display.insert(tk.END, f"你: {message}\n", "user_tag")
        else:
            self.chat_display.insert(tk.END, f"AI: {message}\n", "ai_tag")
        self.chat_display.insert(tk.END, "-"*30 + "\n")
        self.chat_display.see(tk.END)
        self.chat_display.config(state='disabled')
        
        # Keep context (simple)
        self.chat_messages.append({"role": role, "content": message})

    def on_chat_send(self):
        user_text = self.chat_input.get().strip()
        if not user_text:
            return
            
        self.chat_input.delete(0, tk.END)
        self.add_chat_message("User", user_text)
        
        # Disable input while processing
        self.root.config(cursor="wait")
        self.chat_input.config(state='disabled')
        self.root.update()
        
        try:
            # Gather current form data to give context to AI
            current_q = self.prompt_text.get("1.0", tk.END).strip()
            current_s = self.subject_entry.get().strip()
            current_c = self.constraint_entry.get().strip()
            current_t = self.trigger_entry.get().strip()
            
            system_prompt = f"""
            你是一個幫助使用者設定監控攝影機的 AI 助手。
            目前的設定狀態如下：
            - 監控需求 (Question): "{current_q}"
            - 關鍵識別項目 (Subject): "{current_s}"
            - 回答限制 (Constraint): "{current_c}"
            - 觸發關鍵字 (Trigger): "{current_t}"
            
            使用者的最新輸入: "{user_text}"
            
            請根據使用者的輸入與目前的設定狀態，進行對話。
            你的目標是引導使用者完成所有設定。
            請確保所有對話回答都僅限於 '是' 或 '否'。 
            
            **重要**：
            如果你從對話中確認了某些欄位的更新資訊，請在回答的**最後面**附上一個 JSON 區塊，格式如下：
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
            
            print(f"[DEBUG] Calling AI Provider: {self.ai_backend.provider}, Model: {self.ai_backend.model_name}")
            response = self.ai_backend.generate_text(system_prompt)
            
            # Separate JSON from text
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            chat_response = response
            
            if json_match:
                json_str = json_match.group(1)
                chat_response = response.replace(json_match.group(0), "").strip()
                try:
                    data = json.loads(json_str)
                    # Update UI
                    if "question" in data:
                        self.prompt_text.delete("1.0", tk.END)
                        self.prompt_text.insert("1.0", data["question"])
                    if "subject" in data:
                        self.subject_entry.delete(0, tk.END)
                        self.subject_entry.insert(0, data["subject"])
                    if "constraint" in data:
                        self.constraint_entry.delete(0, tk.END)
                        self.constraint_entry.insert(0, data["constraint"])
                    if "trigger" in data:
                        self.trigger_entry.delete(0, tk.END)
                        self.trigger_entry.insert(0, data["trigger"])
                except Exception as e:
                    print(f"JSON Parse Error: {e}")
            
            self.add_chat_message("Assistant", chat_response)
            
        except Exception as e:
            self.add_chat_message("System", f"發生錯誤: {e}")
        finally:
            self.root.config(cursor="")
            self.chat_input.config(state='normal')
            self.chat_input.focus()

    def load_history_files(self):
        self.history_listbox.delete(0, tk.END)
        self.history_files = []
        if not os.path.exists("task"):
            os.makedirs("task")
            
        files = glob.glob("task/*.json")
        # Sort by modification time, newest first
        files.sort(key=os.path.getmtime, reverse=True)
        
        for f in files:
            try:
                with open(f, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    # Use question as display name, truncate if too long
                    name = data.get("question", "Unknown")
                    if len(name) > 20:
                        name = name[:20] + "..."
                    self.history_listbox.insert(tk.END, name)
                    self.history_files.append({"file": f, "data": data})
            except Exception as e:
                print(f"Error loading {f}: {e}")

    def on_history_select(self, event):
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            data = self.history_files[index]["data"]
            
            self.prompt_text.delete("1.0", tk.END)
            self.prompt_text.insert("1.0", data.get("question", ""))

            self.subject_entry.delete(0, tk.END)
            self.subject_entry.insert(0, data.get("subject", ""))
            
            self.constraint_entry.delete(0, tk.END)
            self.constraint_entry.insert(0, data.get("constraint", ""))
            
            self.trigger_entry.delete(0, tk.END)
            self.trigger_entry.insert(0, data.get("trigger", ""))
            
            if hasattr(self, 'smart_input'):
                self.smart_input.delete("1.0", tk.END)
                self.smart_input.insert("1.0", data.get("smart_input", ""))

    def on_history_delete(self):
        selection = self.history_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "請先選擇要刪除的任務！")
            return
            
        index = selection[0]
        file_info = self.history_files[index]
        file_path = file_info["file"]
        question = file_info["data"].get("question", "Unknown")
        
        if messagebox.askyesno("確認刪除", f"確定要刪除此任務紀錄嗎？\n\n{question}"):
            try:
                os.remove(file_path)
                self.load_history_files()
                # Clear inputs
                self.prompt_text.delete("1.0", tk.END)
                self.subject_entry.delete(0, tk.END)
                self.constraint_entry.delete(0, tk.END)
                self.trigger_entry.delete(0, tk.END)
                if hasattr(self, 'smart_input'):
                    self.smart_input.delete("1.0", tk.END)
            except Exception as e:
                messagebox.showerror("錯誤", f"刪除失敗: {e}")

    def on_auto_parse(self):
        user_text = self.smart_input.get("1.0", tk.END).strip()
        if not user_text:
            messagebox.showwarning("提示", "請先輸入您的需求描述！")
            return

        try:
            # Load config to get system_prompt
            with open('config.yaml', 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            system_prompt = config.get('system', {}).get('system_prompt', '(所有回答都採用繁體中文回答)')

            # 顯示處理中
            self.root.config(cursor="wait")
            self.root.update()

            prompt_template = f"""
            你是一個幫助設定監控系統的 AI 助手。使用者會用自然語言描述他想監控的畫面情況。
            
            使用者的描述: "{user_text}"

            請將使用者的描述拆解成以下四個欄位，並以 JSON 格式回傳：
            1. "question": 針對使用者描，調整成是否的疑問句，例如 "人是否戴帽子?"
            2. "subject": 擷取關鍵識別項目，例如 "人"、"帽子" (從問題中提取的主要監控的對象或物體，當有人時優先觀察人)
            3. "constraint": 針對AI回答的格式限制，例如 "請只回答 是 或 否"
            4. "trigger": 觸發警報的關鍵字或條件，例如 是 或 否 (針對 "question" 的肯定回答填入 是，否定回答則填入 否)

            請直接回傳 JSON 字串，不要包含 Markdown 標記或其他文字。
            {system_prompt}
            """
            
            print(f"[DEBUG] AI Request (Auto Parse): {prompt_template}")
            print(f"[DEBUG] Calling AI Provider: {self.ai_backend.provider}, Model: {self.ai_backend.model_name}")
            response = self.ai_backend.generate_text(prompt_template)
            print(f"[DEBUG] AI Response (Auto Parse): {response}")
            
            # 清理可能的 Markdown code block
            cleaned_response = re.sub(r'^```json\s*|\s*```$', '', response.strip(), flags=re.MULTILINE)
            
            data = json.loads(cleaned_response)
            
            # 動態檢查所有欄位是否為空字串
            for field, value in data.items():
                if not value or not str(value).strip(): # 檢查值是否存在或為空字串
                    messagebox.showerror("錯誤", f"AI 回傳的欄位 '{field}' 為空或缺失，無法解析。\n回傳內容: {response}")
                    return
            
            # 填入 UI
            if "question" in data:
                self.prompt_text.delete("1.0", tk.END)
                self.prompt_text.insert("1.0", data["question"])

            if "subject" in data:
                self.subject_entry.delete(0, tk.END)
                self.subject_entry.insert(0, data["subject"])
            
            if "constraint" in data:
                self.constraint_entry.delete(0, tk.END)
                self.constraint_entry.insert(0, data["constraint"])
                
            if "trigger" in data:
                self.trigger_entry.delete(0, tk.END)
                self.trigger_entry.insert(0, data["trigger"])
                
            messagebox.showinfo("成功", "AI 已自動拆解並填入設定！")
            
        except json.JSONDecodeError:
            messagebox.showerror("錯誤", f"AI 回傳格式錯誤，無法解析。\n回傳內容: {response}")
        except Exception as e:
            messagebox.showerror("錯誤", f"發生錯誤: {e}")
        finally:
            self.root.config(cursor="")

    def start_recording(self, event):
        """Start recording audio when button is pressed."""
        if sd is None:
            messagebox.showerror("錯誤", "音訊錄製套件未安裝。請執行 `pip install sounddevice scipy` 並重新啟動程式。")
            return
        if self.recording:
            return  # Already recording
        self.recording = True
        self.audio_frames = []
        print("開始錄音...")
        # Start recording in a separate thread or callback
        self.stream = sd.InputStream(samplerate=44100, channels=1, callback=self.audio_callback)
        self.stream.start()

    def stop_recording(self, event):
        """Stop recording audio when button is released and process it."""
        if not self.recording:
            return
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        print("錄音結束！")
        self.process_audio()

    def audio_callback(self, indata, frames, time, status):
        """Callback to collect audio frames."""
        if self.recording:
            self.audio_frames.append(indata.copy())

    def process_audio(self):
        """Process the recorded audio: play, save, and transcribe."""
        if not self.audio_frames:
            return
        try:
            # Concatenate all frames
            myrecording = np.concatenate(self.audio_frames, axis=0)

            # 播放錄音 (選擇性)
            print("播放中...")
            sd.play(myrecording, 44100)
            sd.wait()

            # 儲存檔案
            os.makedirs("temp", exist_ok=True)
            filename = "temp/output.wav"
            write(filename, 44100, myrecording)
            print(f"檔案已成功儲存至: {filename}")

            # 轉換為 speech_recognition 可用的格式
            audio_int16 = (myrecording * 32767).astype('int16')
            audio_bytes = audio_int16.tobytes()

            # 建立 AudioData 物件
            audio_data = sr.AudioData(audio_bytes, 44100, 2)

            # 使用 Google 語音辨識
            recognizer = sr.Recognizer()
            transcript = recognizer.recognize_google(audio_data, language="zh-TW")

            # 填入 smart_input 框
            self.smart_input.delete("1.0", tk.END)
            transcript = transcript + "?"
            self.smart_input.insert("1.0", transcript)

        except sr.WaitTimeoutError:
            messagebox.showwarning("語音輸入", "錄音逾時，請再試一次。")
        except sr.UnknownValueError:
            messagebox.showwarning("語音輸入", "無法辨識語音，請說得更清楚。")
        except sr.RequestError as e:
            messagebox.showerror("語音輸入", f"語音服務錯誤: {e}")
        except Exception as e:
            messagebox.showerror("語音輸入", f"發生未知錯誤: {e}")

    def on_voice_input(self):
        """Legacy method, kept for compatibility."""
        pass

    def on_submit(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        subject = self.subject_entry.get().strip()
        constraint = self.constraint_entry.get().strip()
        trigger = self.trigger_entry.get().strip()
        
        # Get smart input if available
        smart_text = ""
        if hasattr(self, 'smart_input'):
             smart_text = self.smart_input.get("1.0", tk.END).strip()
        
        if not prompt:
            messagebox.showwarning("警告", "請輸入監控需求！")
            return
            
        final_question = f"{prompt} {constraint}".strip()
            
        # Save task to file
        task_data = {
            "question": prompt, # Save raw prompt for display/restoration
            "subject": subject,
            "constraint": constraint,
            "trigger": trigger,
            "smart_input": smart_text,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            if not os.path.exists("task"):
                os.makedirs("task")
            
            # Remove duplicates (tasks with same question)
            existing_files = glob.glob("task/*.json")
            for f in existing_files:
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        existing_data = json.load(file)
                        if existing_data.get("question") == prompt:
                            # Found duplicate, remove it
                            file.close() # Ensure file is closed before removing
                            os.remove(f)
                            print(f"Removed duplicate task file: {f}")
                except Exception as e:
                    print(f"Error checking duplicate {f}: {e}")

            # Create a safe filename based on timestamp
            filename = f"task/task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving task: {e}")

        self.result = {
            "question": final_question,
            "subject": subject,
            "trigger_keyword": trigger
        }
        self.root.destroy()

    def on_cancel(self):
        self.root.destroy()
        
    def show(self):
        self.root.lift()
        self.root.attributes('-topmost',True)
        self.root.after_idle(self.root.attributes,'-topmost',False)
        self.root.mainloop()
        return self.result

if __name__ == "__main__":
    # Test
    dialog = MonitorConfigDialog("圖片中的人有沒有戴帽子？", "請只回答'是'或'否'。", "是")
    print(dialog.show())
