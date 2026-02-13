# 匯入必要的模組
import abc  # 用於定義抽象基底類別
import time  # 用於計時
import base64  # 用於圖片的 Base64 編碼
import requests  # 用於發送 HTTP 請求
import os  # 用於與作業系統互動，例如讀取環境變數

# 定義 AI 後端的抽象基底類別 (Abstract Base Class)
# 所有具體的 AI 後端都應該繼承這個類別，並實作其抽象方法
class AIBackend(abc.ABC):
    """AI 後端抽象基底類別"""
    def __init__(self, provider_name, model_name):
        """
        初始化 AI 後端物件。
        :param provider_name: AI 服務提供者的名稱 (例如: "ollama", "gemini")
        :param model_name: 所使用的模型名稱 (例如: "llava", "gemini-1.5-flash")
        """
        self.provider = provider_name
        self.model_name = model_name

    @abc.abstractmethod
    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        """
        分析指定的圖片並返回文字結果。這是一個抽象方法，必須在子類別中被實作。
        :param image_path: 圖片檔案的路徑
        :param prompt: 使用者提供的問題或提示
        :param system_prompt_text: (可選) 系統級的提示，用於指導模型的行為
        :return: AI 模型分析後產生的文字
        """
        pass

    def generate_text(self, prompt, system_prompt_text=""):
        """
        僅根據文字提示生成文字 (用於自然語言處理任務)。
        :param prompt: 使用者提供的問題或提示
        :param system_prompt_text: (可選) 系統級的提示
        :return: AI 模型產生的文字
        """
        return "尚未實作此功能的 Text Generation"

# 用於測試和開發的模擬後端
class MockBackend(AIBackend):
    """
    用於測試的假後端。不進行真實的 API 呼叫，而是返回固定的或隨機的結果。
    這有助於在沒有 API 金鑰或網路連線的情況下進行開發和測試。
    """
    def __init__(self, config=None):
        """初始化模擬後端"""
        super().__init__("mock", "N/A") # 模擬後端沒有真實的模型名稱

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        """
        模擬圖片分析的行為。
        :param image_path: 圖片檔案的路徑
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: 固定的 "沒有" 字串，用於測試
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        print(f"[MockAI] 正在分析 {image_path}，問題: {final_prompt}")
        # 這裡模擬 AI 有時候看到，有時候沒看到
        # 實際使用時，應替換為對真實 API 的呼叫
        return "沒有"
    
    def generate_text(self, prompt, system_prompt_text=""):
        """
        模擬文字生成的行為，返回一個固定的 JSON 字串。
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: 一個模擬的 JSON 格式字串
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        # 模擬回傳一個 JSON 格式的解析結果
        return '''{
            "question": "圖片中浴缸水有多少?",
            "subject": "浴缸",
            "constraint": "10%~80%",
            "trigger": ">80%"
        }'''

# 連接本地 Ollama 服務的後端
class OllamaBackend(AIBackend):
    """與本地運行的 Ollama 服務進行互動的後端"""
    def __init__(self, config):
        """
        初始化 Ollama 後端。
        :param config: 包含 'model', 'base_url', 'num_gpu', 'num_thread' 的字典
        """
        super().__init__("ollama", config.get('model', 'llava'))
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = self.model_name
        self.num_gpu = config.get('num_gpu', 0)  # 設定要使用的 GPU 層數
        self.num_thread = config.get('num_thread', 4)  # 設定要使用的 CPU 執行緒數

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        """
        使用 Ollama 分析圖片。
        :param image_path: 圖片檔案的路徑
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: Ollama 模型的回應或錯誤訊息
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        # 讀取圖片並轉為 Base64 編碼
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # 準備請求的 payload
        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "images": [base64_image],
            "stream": False
        }
        
        try:
            start_time = time.time()
            # 發送 POST 請求到 Ollama API
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()  # 如果 HTTP 狀態碼是 4xx 或 5xx，則拋出異常
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[Ollama] 請求到 {self.base_url}/api/generate 花費了 {elapsed_time:.2f} 秒")
            # 解析 JSON 回應並返回結果
            return response.json().get('response', '').strip()
        except requests.exceptions.ConnectionError:
            print(f"[Ollama] 錯誤: 無法連接到 Ollama 服務。請確保 Ollama 正在運行，且 base_url ({self.base_url}) 配置正確。")
            return "Error: Ollama connection failed."
        except requests.exceptions.RequestException as e:
            print(f"[Ollama] HTTP 請求錯誤: {e}")
            return "Error"
        except Exception as e:
            print(f"[Ollama] 未預期的錯誤: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
        """
        使用 Ollama 生成文字。
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: Ollama 模型的回應或錯誤訊息
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "stream": False,
            "options": {
                "num_gpu": self.num_gpu,
                "num_thread": self.num_thread
            }
        }
        try:
            start_time = time.time()
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[Ollama Text] 請求到 {self.base_url}/api/generate 花費了 {elapsed_time:.2f} 秒")
            return response.json().get('response', '').strip()
        except requests.exceptions.ConnectionError:
            print(f"[Ollama Text] 錯誤: 無法連接到 Ollama 服務。請確保 Ollama 正在運行，且 base_url ({self.base_url}) 配置正確。")
            return "Error: Ollama connection failed."
        except requests.exceptions.RequestException as e:
            print(f"[Ollama Text] HTTP 請求錯誤: {e}")
            return "{}"
        except Exception as e:
            print(f"[Ollama Text] 未預期的錯誤: {e}")
            return "{}"

# 連接 Google Gemini API 的後端
class GeminiBackend(AIBackend):
    """與 Google Gemini API 進行互動的後端"""
    def __init__(self, config):
        """
        初始化 Gemini 後端。
        :param config: 包含 'model' 和 'api_key' 的字典
        """
        super().__init__("gemini", config.get('model', 'gemini-1.5-flash'))
        import google.generativeai as genai
        
        # 從設定檔或環境變數中取得 API Key
        self.api_key = config.get('api_key', '').strip()
        if not self.api_key:
            import os
            # 從環境變數 ANTHROPIC_API_KEY (此處應為 GEMINI_API_KEY，可能是個筆誤) 中取得
            env_key = os.getenv('GEMINI_API_KEY') # 修正: 應為 GEMINI_API_KEY
            if env_key:
                self.api_key = env_key.strip()
                print("[Gemini] 從環境變數 GEMINI_API_KEY 取得 API Key。")

        # 檢查 API Key 是否有效
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            print("[Gemini] 警告: 未設定 API Key，請在 config.yaml 中填入。")
        
        # 設定 Gemini API
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        """
        使用 Gemini 分析圖片。
        :param image_path: 圖片檔案的路徑
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: Gemini 模型的回應或錯誤訊息
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        import PIL.Image
        try:
            # 再次檢查 API Key
            if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
                return "Error: Missing API Key"
                
            img = PIL.Image.open(image_path)
            # 將提示和圖片一起發送到模型
            response = self.model.generate_content([final_prompt, img])
            if response.text:
                return response.text.strip()
            return "無回應"
        except Exception as e:
            print(f"[Gemini] 錯誤: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
        """
        使用 Gemini 生成文字。
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: Gemini 模型的回應或空字串
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        try:
            if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
                return "Error: Missing API Key"
            start_time = time.time()
            response = self.model.generate_content(final_prompt)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[Gemini Text] 請求到 generate_content 花費了 {elapsed_time:.2f} 秒")
            if response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            print(f"[Gemini Text] 錯誤: {e}")
            return ""

# 連接 OpenAI API 的後端 (例如 GPT-4o)
class OpenAIBackend(AIBackend):
    """與 OpenAI API 進行互動的後端"""
    def __init__(self, config):
        """
        初始化 OpenAI 後端。
        :param config: 包含 'model' 和 'api_key' 的字典
        """
        super().__init__("openai", config.get('model', 'gpt-4o'))
        from openai import OpenAI
        self.client = OpenAI(api_key=config.get('api_key'))
        self.model = self.model_name

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        """
        使用 OpenAI 模型 (如 GPT-4o) 分析圖片。
        :param image_path: 圖片檔案的路徑
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: OpenAI 模型的回應或錯誤訊息
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        # 讀取圖片並轉為 Base64 編碼
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        try:
            start_time = time.time()
            # 發送請求到 Chat Completions API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": final_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[OpenAI] 請求到 chat.completions.create 花費了 {elapsed_time:.2f} 秒")
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[OpenAI] 錯誤: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
        """
        使用 OpenAI 模型生成文字。
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: OpenAI 模型的回應或空字串
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": final_prompt}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[OpenAI Text] 錯誤: {e}")
            return ""

# 連接 Anthropic API 的後端 (例如 Claude 3)
class AnthropicBackend(AIBackend):
    """與 Anthropic API (Claude) 進行互動的後端"""
    def __init__(self, config):
        """
        初始化 Anthropic 後端。
        :param config: 包含 'model' 和 'api_key' 的字典
        """
        super().__init__("anthropic", config.get('model', 'claude-3-opus-20240229'))
        import anthropic
        
        # 從設定檔或環境變數中取得 API Key
        raw_key = config.get('api_key', '')
        if not raw_key:
            import os
            raw_key = os.getenv('ANTHROPIC_API_KEY', '')
            if raw_key:
                print("[Anthropic] 從環境變數 ANTHROPIC_API_KEY 取得 API Key。")

        self.api_key = raw_key.strip()
        
        # 檢查 API Key 是否有效並提供提示
        if not self.api_key or self.api_key == "YOUR_ANTHROPIC_API_KEY":
            print("[Anthropic] 警告: 未設定 API Key，請在 config.yaml 中填入有效的 Anthropic API Key。")
        else:
            # 顯示金鑰的前幾位以供驗證
            print(f"[Anthropic] 使用的 API Key 前 5 個字元: {self.api_key[:5]}*****")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        """
        使用 Anthropic 模型 (如 Claude 3) 分析圖片。
        :param image_path: 圖片檔案的路徑
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: Anthropic 模型的回應或錯誤訊息
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        try:
            if getattr(self, "api_key", None):
                print(f"[Anthropic] 呼叫 analyze_image 時使用的 API Key 前 5 個字元: {self.api_key[:5]}*****")
            start_time = time.time()
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=300,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image,
                                },
                            },
                            {"type": "text", "text": final_prompt}
                        ],
                    }
                ],
            )
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[Anthropic] 請求到 messages.create 花費了 {elapsed_time:.2f} 秒")
            return message.content[0].text.strip()
        except Exception as e:
            print(f"[Anthropic] 錯誤: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
        """
        使用 Anthropic 模型生成文字。
        :param prompt: 使用者提示
        :param system_prompt_text: 系統提示
        :return: Anthropic 模型的回應或空字串
        """
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        try:
            if getattr(self, "api_key", None):
                print(f"[Anthropic Text] 呼叫 generate_text 時使用的 API Key 前 5 個字元: {self.api_key[:5]}*****")
            start_time = time.time()
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=300,
                messages=[
                    {"role": "user", "content": final_prompt}
                ],
            )
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[Anthropic Text] 請求到 messages.create 花費了 {elapsed_time:.2f} 秒")
            return message.content[0].text.strip()
        except Exception as e:
            print(f"[Anthropic Text] 錯誤: {e}")
            return ""

# 工廠函數 (Factory Function)
def get_ai_backend(config):
    """
    根據設定檔中的 'provider' 欄位，建立並返回對應的 AI 後端實例。
    這是一種設計模式，可以將物件的建立邏輯集中管理，使程式碼更具彈性。
    :param config: 應用程式的整體設定字典
    :return: 一個 AIBackend 的子類別實例
    """
    provider = config.get('provider', 'mock')
    if provider == 'ollama_minmax':
        return OllamaBackend(config.get('ollama_minmax', {}))
    elif provider == 'ollama_llava':
        return OllamaBackend(config.get('ollama_llava', {}))
    elif provider == 'ollama_moondream':
        return OllamaBackend(config.get('ollama_moondream', {}))
    elif provider == 'ollama_minicpm':
        return OllamaBackend(config.get('ollama_minicpm', {}))
    elif provider == 'gemini_pro':
        return GeminiBackend(config.get('gemini_pro', {}))
    elif provider == 'gemini_flash':
        return GeminiBackend(config.get('gemini_flash', {}))
    elif provider == 'openai':
        return OpenAIBackend(config.get('openai', {}))
    elif provider == 'anthropic':
        return AnthropicBackend(config.get('anthropic', {}))
    else:
        # 如果 provider 名稱不匹配或未提供，則預設返回 MockBackend
        return MockBackend()
