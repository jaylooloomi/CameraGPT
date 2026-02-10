import abc
import time
import base64
import requests
import os

class AIBackend(abc.ABC):
    def __init__(self, provider_name, model_name):
        self.provider = provider_name
        self.model_name = model_name

    @abc.abstractmethod
    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        """分析圖片並返回文字結果"""
        pass

    def generate_text(self, prompt, system_prompt_text=""):
        """僅生成文字 (用於 NLP 任務)"""
        return "尚未實作此功能的 Text Generation"

class MockBackend(AIBackend):
    """用於測試的假後端，隨機返回結果或固定返回"""
    def __init__(self, config=None):
        super().__init__("mock", "N/A") # Mock backend doesn't have a real model name

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        print(f"[MockAI] 正在分析 {image_path}，問題: {final_prompt}")
        # 這裡模擬 AI 有時候看到，有時候沒看到
        # 實際使用請替換為真實 API
        return "沒有"
    
    def generate_text(self, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        # 模擬回傳一個 JSON 格式的解析結果
        return '''{
            "question": "圖片中浴缸水有多少?",
            "subject": "浴缸",
            "constraint": "10%~80%",
            "trigger": ">80%"
        }'''

class OllamaBackend(AIBackend):
    def __init__(self, config):
        super().__init__("ollama", config.get('model', 'llava'))
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.model = self.model_name # Use the base class's model_name
        self.num_gpu = config.get('num_gpu', 0)  # GPU 層數
        self.num_thread = config.get('num_thread', 4)  # CPU 執行緒數

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        with open(image_path, "rb") as f:
            image_bytes = f.read()
            base64_image = base64.b64encode(image_bytes).decode('utf-8')

        payload = {
            "model": self.model,
            "prompt": final_prompt,
            "images": [base64_image],
            "stream": False
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[Ollama] Request to {self.base_url}/api/generate took {elapsed_time:.2f} seconds")
            return response.json().get('response', '').strip()
        except requests.exceptions.ConnectionError:
            print(f"[Ollama] Error: 無法連接到 Ollama 服務。請確保 Ollama 服務正在運行，且 base_url ({self.base_url}) 配置正確。")
            return "Error: Ollama connection failed."
        except requests.exceptions.RequestException as e:
            print(f"[Ollama] HTTP Request Error: {e}")
            return "Error"
        except Exception as e:
            print(f"[Ollama] Unexpected Error: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
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
            print(f"[Ollama Text] Request to {self.base_url}/api/generate took {elapsed_time:.2f} seconds")
            return response.json().get('response', '').strip()
        except requests.exceptions.ConnectionError:
            print(f"[Ollama Text] Error: 無法連接到 Ollama 服務。請確保 Ollama 服務正在運行，且 base_url ({self.base_url}) 配置正確。")
            return "Error: Ollama connection failed."
        except requests.exceptions.RequestException as e:
            print(f"[Ollama Text] HTTP Request Error: {e}")
            return "{}"
        except Exception as e:
            print(f"[Ollama Text] Unexpected Error: {e}")
            return "{}"

class GeminiBackend(AIBackend):
    def __init__(self, config):
        super().__init__("gemini", config.get('model', 'gemini-1.5-flash'))
        import google.generativeai as genai
        # Retrieve and strip any surrounding whitespace or newline characters
        # Retrieve API key from config and strip whitespace; if missing, fall back to environment variable
        self.api_key = config.get('api_key', '').strip()
        if not self.api_key:
            import os
            env_key = os.getenv('ANTHROPIC_API_KEY')
            if env_key:
                self.api_key = env_key.strip()
                print("[Anthropic] 從環境變數 ANTHROPIC_API_KEY 取得 API Key。")
        if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
            print("[Gemini] 警告: 未設定 API Key，請在 config.yaml 中填入。")
        
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(self.model_name)

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        import PIL.Image
        try:
            if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
                return "Error: Missing API Key"
                
            img = PIL.Image.open(image_path)
            response = self.model.generate_content([final_prompt, img])
            if response.text:
                return response.text.strip()
            return "無回應"
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        try:
            if not self.api_key or self.api_key == "YOUR_GEMINI_API_KEY":
                return "Error: Missing API Key"
            start_time = time.time()
            response = self.model.generate_content(final_prompt)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"[Gemini Text] Request to generate_content took {elapsed_time:.2f} seconds")
            if response.text:
                return response.text.strip()
            return ""
        except Exception as e:
            print(f"[Gemini Text] Error: {e}")
            return ""

class OpenAIBackend(AIBackend):
    def __init__(self, config):
        super().__init__("openai", config.get('model', 'gpt-4o'))
        from openai import OpenAI
        self.client = OpenAI(api_key=config.get('api_key'))
        self.model = self.model_name # Use the base class's model_name

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        try:
            start_time = time.time()
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
            print(f"[OpenAI] Request to chat.completions.create took {elapsed_time:.2f} seconds")
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[OpenAI] Error: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
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
            print(f"[OpenAI Text] Error: {e}")
            return ""

class AnthropicBackend(AIBackend):
    def __init__(self, config):
        super().__init__("anthropic", config.get('model', 'claude-3-opus-20240229'))
        import anthropic
        # Retrieve API key from config and strip any surrounding whitespace or newlines
        raw_key = config.get('api_key', '')
        # Fallback to environment variable if not provided in config
        if not raw_key:
            import os
            raw_key = os.getenv('ANTHROPIC_API_KEY', '')
            if raw_key:
                print("[Anthropic] 從環境變數 ANTHROPIC_API_KEY 取得 API Key。")
        # Ensure the key is a clean string
        self.api_key = raw_key.strip()
        if not self.api_key or self.api_key == "YOUR_ANTHROPIC_API_KEY":
            print("[Anthropic] 警告: 未設定 API Key，請在 config.yaml 中填入有效的 Anthropic API Key。")
        else:
            # Show first few characters of the key for verification (mask the rest)
            print(f"[Anthropic] 使用的 API Key 前 5 個字元: {self.api_key[:5]}*****")
        # Initialise the client with the cleaned key
        self.client = anthropic.Anthropic(api_key=self.api_key)
        # Additional debugging information
        if self.api_key:
            key_len = len(self.api_key)
            # Mask the key except first 5 and last 5 characters for safety
            masked = f"{self.api_key[:5]}{'*' * (key_len - 10)}{self.api_key[-5:]}" if key_len > 10 else self.api_key
            print(f"[Anthropic] API Key 長度: {key_len}, 完整遮蔽顯示: {masked}")

    def analyze_image(self, image_path, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        with open(image_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode('utf-8')

        try:
            # Debug: print API key snippet before making request
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
            print(f"[Anthropic] Request to messages.create took {elapsed_time:.2f} seconds")
            return message.content[0].text.strip()
        except Exception as e:
            print(f"[Anthropic] Error: {e}")
            return "Error"

    def generate_text(self, prompt, system_prompt_text=""):
        final_prompt = f"{prompt} {system_prompt_text}".strip()
        try:
            # Debug: print API key snippet before making request
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
            print(f"[Anthropic Text] Request to messages.create took {elapsed_time:.2f} seconds")
            return message.content[0].text.strip()
        except Exception as e:
            print(f"[Anthropic Text] Error: {e}")
            return ""

def get_ai_backend(config):
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
        return MockBackend()
