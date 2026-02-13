# CameraGPT - AI-Powered Smart Surveillance System
# CameraGPT - AI 智慧監控系統

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![AI](https://img.shields.io/badge/AI-Multi--Backend-orange.svg)](README.md)

[English](#english) | [繁體中文](#繁體中文)

---

## English

### Overview

**CameraGPT** is an intelligent surveillance system that combines computer vision with multiple AI backends (Ollama, Google Gemini, OpenAI, Anthropic Claude) to analyze camera feeds in real-time. When motion is detected, the system captures images and uses AI to analyze the scene, answering customizable questions about what's happening. It can trigger various notification methods including Email, LINE, phone calls, and alarm sounds.

### Key Features

#### 🎥 **Smart Motion Detection**
- Automatically captures frames at configurable intervals
- Detects scene changes using intelligent difference thresholding
- Triggers AI analysis only when significant motion is detected

#### 🤖 **Multi-AI Backend Support**
- **Ollama** (Local): MiniMax, LLaVA, MiniCPM-V, Moondream
- **Google Gemini**: Gemini 2.0 Flash, Gemini 3 Pro Preview
- **OpenAI**: GPT-4o (with vision)
- **Anthropic**: Claude with vision capabilities
- **Mock Mode**: Test flow without real API calls

#### 🔔 **Flexible Notification System**
- **Email**: Send alerts with images via Gmail
- **LINE Notify**: Instant mobile notifications
- **Phone Call**: Voice alerts via phone
- **Alarm Sound**: Local audio alerts with custom WAV files
- **Alarm Clock**: Schedule specific monitoring times

#### 🧠 **Advanced Trigger Logic**
- **Numeric Comparisons**: Detect conditions like `>80`, `<=50`, `=100`, `!=0`
- **Keyword Matching**: Trigger on specific words like "person", "yes", "detected"
- **Customizable Questions**: Ask AI anything about the scene
- Example: "Is there a person in the frame?" → Trigger on keyword "yes"

#### 🎨 **User-Friendly GUI**
- Interactive startup dialog for configuration
- Real-time monitoring status display
- Easy camera selection and AI backend switching

### Installation

#### Prerequisites
- Python 3.7 or higher
- Webcam or IP camera
- (Optional) Ollama installed locally for offline AI models

#### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies:**
```
opencv-python
numpy
pyyaml
requests
google-generativeai
openai
anthropic
playsound==1.2.2
sounddevice
scipy
```

#### Step 2: Configure API Keys

Edit `config.yaml` and add your credentials:

```yaml
# For Gmail notifications
email:
  enabled: true
  sender_email: "your_email@gmail.com"
  sender_password: "your_app_password"  # Use App Password
  receiver_email: "receiver@example.com"

# For AI backends
ai:
  provider: "gemini_flash"  # or ollama_llava, openai, etc.
  
  gemini_flash:
    api_key: "YOUR_GEMINI_API_KEY"
    model: "gemini-2.0-flash"
  
  openai:
    api_key: "YOUR_OPENAI_API_KEY"
    model: "gpt-4o"
```

**Gmail Setup**: You need to generate an [App Password](https://myaccount.google.com/apppasswords) for Gmail.

**Ollama Setup**: If using Ollama, install and start the required model:
```bash
# Install Ollama from https://ollama.ai
ollama pull llava
ollama serve
```

### Usage

#### Basic Usage

```bash
python camera_daemon.py
```

The system will:
1. Open a configuration dialog on first run
2. Start monitoring the camera feed
3. Detect motion and analyze with AI
4. Send notifications when trigger conditions are met

#### Advanced Configuration

Edit `config.yaml` for detailed customization:

```yaml
system:
  camera_index: 0              # 0 = default webcam
  interval: 5.0                # Check every 5 seconds
  diff_threshold: 3.0          # Motion sensitivity (lower = more sensitive)
  
prompt:
  question: "Is there a person in the frame? Please only reply 'yes' or 'no'."
  trigger_keyword: "yes"       # Send alert when AI response contains "yes"

ai:
  provider: "ollama_llava"     # Choose your AI backend
  
  ollama_llava:
    base_url: "http://localhost:11434"
    model: "llava"
    num_gpu: 0                 # 0 = CPU only
    num_thread: 4              # CPU threads

alarm_sound:
  enabled: true
  sound_file: "source/alert.wav"

alarm_clock:
  enabled: true
  time: "07:00"                # Monitor at specific time
```

### Configuration Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `camera_index` | Camera device ID | `0` (default webcam) |
| `interval` | Check interval in seconds | `5.0` |
| `diff_threshold` | Motion detection sensitivity | `3.0` (1% = 1.0) |
| `question` | Question to ask AI | "Is there a person?" |
| `trigger_keyword` | Alert trigger word | "yes" |
| `provider` | AI backend to use | `ollama_llava`, `gemini_flash`, `openai` |

### AI Provider Comparison

| Provider | Speed | Cost | Offline | Vision Quality |
|----------|-------|------|---------|----------------|
| Ollama LLaVA | Fast | Free | ✅ Yes | Good |
| Ollama MiniCPM-V | Medium | Free | ✅ Yes | Excellent |
| Gemini Flash | Very Fast | Low | ❌ No | Excellent |
| Gemini Pro | Medium | Medium | ❌ No | Outstanding |
| OpenAI GPT-4o | Fast | High | ❌ No | Outstanding |
| Anthropic Claude | Fast | Medium | ❌ No | Excellent |

### Project Structure

```
CameraGPT/
├── camera_daemon.py          # Main monitoring daemon
├── ai_backends.py            # AI provider integrations
├── image_utils.py            # Image processing utilities
├── startup_dialog.py         # GUI configuration dialog
├── email_notify.py           # Email notification module
├── line_notify_module.py     # LINE notification module
├── phone_notify_module.py    # Phone call notification module
├── alarm_sound_module.py     # Local alarm sound module
├── alarm_clock_module.py     # Scheduled monitoring module
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
└── source/                   # Resource files (alert sounds, etc.)
```

### Troubleshooting

**Issue**: Camera not detected
```bash
# List available cameras
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

**Issue**: Ollama connection error
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve
```

**Issue**: Gmail authentication failed
- Make sure you're using an [App Password](https://myaccount.google.com/apppasswords), not your regular password
- Enable "Less secure app access" if using App Password doesn't work

### Use Cases

- 🏠 **Home Security**: Monitor for intruders or unexpected visitors
- 👶 **Baby Monitor**: Alert when baby wakes up or needs attention
- 🐕 **Pet Monitoring**: Get notified when pets are in restricted areas
- 🚪 **Door Monitoring**: Track who enters/exits your space
- 📦 **Package Detection**: Alert when deliveries arrive
- 🚗 **Parking Monitor**: Detect vehicles in parking spots

### Performance Tips

1. **Use Local AI for Speed**: Ollama models run faster on local hardware
2. **Adjust Threshold**: Lower `diff_threshold` for more sensitive detection
3. **GPU Acceleration**: Set `num_gpu > 0` for Ollama to use GPU
4. **Optimize Interval**: Increase `interval` to reduce CPU usage

### Roadmap

- [ ] Multi-camera support
- [ ] Cloud storage integration
- [ ] Mobile app
- [ ] Face recognition
- [ ] Object tracking
- [ ] Web dashboard
- [ ] Docker deployment

### Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### License

This project is licensed under the MIT License.

### Acknowledgments

- Built with OpenCV for computer vision
- Powered by multiple AI providers
- Inspired by smart home automation needs

---

## 繁體中文

### 概述

**CameraGPT** 是一個智慧監控系統，結合電腦視覺與多種 AI 後端（Ollama、Google Gemini、OpenAI、Anthropic Claude）來即時分析攝影機畫面。當偵測到移動時，系統會拍攝影像並使用 AI 分析場景，回答自訂的問題。系統可觸發多種通知方式，包括 Email、LINE、電話、警報音效等。

### 主要功能

#### 🎥 **智慧移動偵測**
- 以可設定的間隔自動擷取畫面
- 使用智慧差異閾值偵測場景變化
- 僅在偵測到顯著移動時觸發 AI 分析

#### 🤖 **多 AI 後端支援**
- **Ollama**（本地）：MiniMax、LLaVA、MiniCPM-V、Moondream
- **Google Gemini**：Gemini 2.0 Flash、Gemini 3 Pro Preview
- **OpenAI**：GPT-4o（含視覺）
- **Anthropic**：Claude 視覺功能
- **模擬模式**：測試流程而不呼叫真實 API

#### 🔔 **彈性通知系統**
- **Email**：透過 Gmail 傳送含影像的警報
- **LINE Notify**：即時行動裝置通知
- **電話通知**：語音警報
- **警報音效**：本地音訊警報（自訂 WAV 檔）
- **鬧鐘功能**：排程特定監控時間

#### 🧠 **進階觸發邏輯**
- **數值比較**：偵測條件如 `>80`、`<=50`、`=100`、`!=0`
- **關鍵字比對**：針對特定詞語觸發，如「人」、「是」、「偵測到」
- **自訂問題**：向 AI 詢問任何關於場景的問題
- 範例：「畫面中有人嗎？」→ 回答包含「是」時觸發

#### 🎨 **友善圖形介面**
- 互動式啟動對話框設定
- 即時監控狀態顯示
- 簡易攝影機選擇和 AI 後端切換

### 安裝

#### 系統需求
- Python 3.7 或更高版本
- 網路攝影機或 IP 攝影機
- （選用）本地安裝 Ollama 以使用離線 AI 模型

#### 步驟 1：安裝相依套件

```bash
pip install -r requirements.txt
```

**相依套件：**
```
opencv-python
numpy
pyyaml
requests
google-generativeai
openai
anthropic
playsound==1.2.2
sounddevice
scipy
```

#### 步驟 2：設定 API 金鑰

編輯 `config.yaml` 並加入您的憑證：

```yaml
# Gmail 通知設定
email:
  enabled: true
  sender_email: "your_email@gmail.com"
  sender_password: "your_app_password"  # 使用應用程式密碼
  receiver_email: "receiver@example.com"

# AI 後端設定
ai:
  provider: "gemini_flash"  # 或 ollama_llava、openai 等
  
  gemini_flash:
    api_key: "YOUR_GEMINI_API_KEY"
    model: "gemini-2.0-flash"
  
  openai:
    api_key: "YOUR_OPENAI_API_KEY"
    model: "gpt-4o"
```

**Gmail 設定**：您需要產生 [應用程式密碼](https://myaccount.google.com/apppasswords)。

**Ollama 設定**：若使用 Ollama，請安裝並啟動所需模型：
```bash
# 從 https://ollama.ai 安裝 Ollama
ollama pull llava
ollama serve
```

### 使用方式

#### 基本使用

```bash
python camera_daemon.py
```

系統會：
1. 首次執行時開啟設定對話框
2. 開始監控攝影機畫面
3. 偵測移動並使用 AI 分析
4. 當符合觸發條件時傳送通知

#### 進階設定

編輯 `config.yaml` 進行詳細自訂：

```yaml
system:
  camera_index: 0              # 0 = 預設網路攝影機
  interval: 5.0                # 每 5 秒檢查一次
  diff_threshold: 3.0          # 移動靈敏度（數值越小越敏感）
  
prompt:
  question: "畫面中有人嗎？請只回答「是」或「否」。"
  trigger_keyword: "是"        # 當 AI 回答包含「是」時發送警報

ai:
  provider: "ollama_llava"     # 選擇您的 AI 後端
  
  ollama_llava:
    base_url: "http://localhost:11434"
    model: "llava"
    num_gpu: 0                 # 0 = 僅使用 CPU
    num_thread: 4              # CPU 執行緒數

alarm_sound:
  enabled: true
  sound_file: "source/alert.wav"

alarm_clock:
  enabled: true
  time: "07:00"                # 在特定時間監控
```

### 設定參數

| 參數 | 說明 | 範例 |
|------|------|------|
| `camera_index` | 攝影機裝置 ID | `0`（預設網路攝影機）|
| `interval` | 檢查間隔（秒）| `5.0` |
| `diff_threshold` | 移動偵測靈敏度 | `3.0`（1% = 1.0）|
| `question` | 要問 AI 的問題 | 「有人嗎？」|
| `trigger_keyword` | 警報觸發關鍵字 | 「是」|
| `provider` | 使用的 AI 後端 | `ollama_llava`、`gemini_flash`、`openai` |

### AI 供應商比較

| 供應商 | 速度 | 成本 | 離線 | 視覺品質 |
|--------|------|------|------|----------|
| Ollama LLaVA | 快 | 免費 | ✅ 是 | 良好 |
| Ollama MiniCPM-V | 中等 | 免費 | ✅ 是 | 優秀 |
| Gemini Flash | 非常快 | 低 | ❌ 否 | 優秀 |
| Gemini Pro | 中等 | 中等 | ❌ 否 | 卓越 |
| OpenAI GPT-4o | 快 | 高 | ❌ 否 | 卓越 |
| Anthropic Claude | 快 | 中等 | ❌ 否 | 優秀 |

### 專案結構

```
CameraGPT/
├── camera_daemon.py          # 主要監控守護程式
├── ai_backends.py            # AI 供應商整合
├── image_utils.py            # 影像處理工具
├── startup_dialog.py         # GUI 設定對話框
├── email_notify.py           # Email 通知模組
├── line_notify_module.py     # LINE 通知模組
├── phone_notify_module.py    # 電話通知模組
├── alarm_sound_module.py     # 本地警報音效模組
├── alarm_clock_module.py     # 排程監控模組
├── config.yaml               # 設定檔
├── requirements.txt          # Python 相依套件
└── source/                   # 資源檔案（警報音效等）
```

### 故障排除

**問題**：偵測不到攝影機
```bash
# 列出可用的攝影機
python -c "import cv2; print([i for i in range(10) if cv2.VideoCapture(i).isOpened()])"
```

**問題**：Ollama 連線錯誤
```bash
# 檢查 Ollama 是否執行中
curl http://localhost:11434/api/tags

# 啟動 Ollama 服務
ollama serve
```

**問題**：Gmail 驗證失敗
- 確保使用[應用程式密碼](https://myaccount.google.com/apppasswords)，而非一般密碼
- 若應用程式密碼無效，請啟用「較不安全的應用程式存取」

### 使用案例

- 🏠 **居家安全**：監控入侵者或意外訪客
- 👶 **嬰兒監視器**：嬰兒醒來或需要照顧時發出警報
- 🐕 **寵物監控**：寵物進入限制區域時通知
- 🚪 **門口監控**：追蹤進出人員
- 📦 **包裹偵測**：配送到達時發出警報
- 🚗 **停車監控**：偵測停車位上的車輛

### 效能建議

1. **使用本地 AI 提升速度**：Ollama 模型在本地硬體上執行更快
2. **調整閾值**：降低 `diff_threshold` 可提高偵測靈敏度
3. **GPU 加速**：將 `num_gpu` 設為 > 0 以使用 GPU
4. **最佳化間隔**：增加 `interval` 可降低 CPU 使用率

### 開發計畫

- [ ] 多攝影機支援
- [ ] 雲端儲存整合
- [ ] 行動應用程式
- [ ] 人臉辨識
- [ ] 物體追蹤
- [ ] 網頁儀表板
- [ ] Docker 部署

### 貢獻

歡迎貢獻！請隨時提交 Pull Request。

### 授權

本專案採用 MIT 授權。

### 致謝

- 使用 OpenCV 進行電腦視覺處理
- 由多個 AI 供應商提供支援
- 靈感來自智慧家庭自動化需求

---

## Contact / 聯絡方式

For questions or support, please open an issue on GitHub.

有任何問題或需要支援，請在 GitHub 開啟 issue。

**Repository**: https://github.com/jaylooloomi/CameraGPT