# CameraGPT 智慧監控系統

這個系統會每隔幾秒抓取攝像頭畫面，當偵測到畫面有變動時，會將圖片傳送給 AI (Ollama, Gemini, 或 OpenAI) 進行分析。如果 AI 的回答符合特定條件（例如偵測到人有戴帽子），系統會發送 Email 通知使用者。

## 功能
1. **自動監控**: 每 2 秒抓取一次截圖。
2. **移動偵測**: 比對前後兩幀圖片，只有在發生顯著變化時才呼叫 AI (節省成本)。
3. **多模型支援**: 支援 Ollama (本地), Google Gemini, OpenAI GPT-4o。
4. **Email 警報**: 當 AI 確認目標特徵時發送帶有截圖的 Email。

## 安裝

1. 安裝 Python 依賴:
   ```bash
   pip install -r requirements.txt
   ```

2. 設置 `config.yaml`:
   複製 `config.yaml` 並填入你的 API Key 和 Email 資訊。
   - 如果使用 **Gmail**，你需要申請 [App Password](https://myaccount.google.com/apppasswords)。
   - 如果使用 **Ollama**，請確保已安裝並執行了支援視覺的模型 (如 `llava`)。

## 執行

```bash
python camera_daemon.py
```

## 設定說明 (`config.yaml`)

- `system.diff_threshold`: 靈敏度調整，數值越小越容易觸發 AI 分析。
- `prompt.question`: 你想問 AI 的問題。
- `prompt.trigger_keyword`: 當 AI 回答包含此詞彙時發送通知。
- `ai.provider`: 切換後端 (`mock`, `ollama`, `gemini`, `openai`)。

## 測試模式
預設 `ai.provider` 為 `mock`，它不會真的呼叫 API，僅用於測試流程是否順暢。確認沒問題後，請修改 `config.yaml` 切換到真實的 AI Provider。
