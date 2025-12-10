
import os
import google.generativeai as genai
import httpx
from PIL import Image
from typing import List, Optional, Dict, Any
import base64
from io import BytesIO

# --- Gemini API configuration ---
def configure_gemini_api() -> None:
    """配置 Gemini API（Google 官方 SDK）"""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)

def get_text_provider() -> str:
    """Returns the configured text provider name."""
    return os.getenv("TEXT_PROVIDER", "gemini") # Default to gemini if not set

# --- TextClient definition ---
class TextClient:
    def __init__(self):
        self.model = None
        self._configure_model()

    def _configure_model(self):
        configure_gemini_api() # Ensure API key is configured
        model_name = os.getenv("TEXT_MODEL")
        if not model_name:
            raise ValueError("TEXT_MODEL environment variable not set.")
        self.model = genai.GenerativeModel(model_name)

    def generate_text(self, prompt: str) -> str:
        """
        Generates text using the configured Gemini model.
        The prompt should already contain the narrative text to be analyzed.
        """
        if not self.model:
            self._configure_model()
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"Error generating text: {e}")
            raise

_text_client_instance = None

def get_text_client() -> TextClient:
    global _text_client_instance
    if _text_client_instance is None:
        _text_client_instance = TextClient()
    return _text_client_instance

# --- ImageClient implementation for Doubao ---
class ImageClient:
    def __init__(self):
        self.api_key = os.getenv("DOUBAO_API_KEY")
        self.api_base_url = os.getenv("DOUBAO_API_BASE_URL")
        self.model_id = os.getenv("DOUBAO_IMAGE_MODEL_ID")

        if not self.api_key:
            raise ValueError("DOUBAAO_API_KEY environment variable not set.")
        if not self.api_base_url:
            raise ValueError("DOUBAO_API_BASE_URL environment variable not set.")
        if not self.model_id:
            raise ValueError("DOUBAO_IMAGE_MODEL_ID environment variable not set.")

        self.http_client = httpx.Client(base_url=self.api_base_url)

    def generate_image(self, prompt: str, output_path: Optional[str] = None,reference_images: Optional[list[str]] = None, **kwargs) -> Optional[str]:
        """
        Generates an image using the configured Doubao model.

        Args:
            prompt (str): The text prompt for image generation.
            output_path (str, optional): If provided, the generated image will be saved to this path.
                                         Otherwise, the image data will be returned (if base64) or not saved.
            **kwargs: Additional parameters for the Doubao API (e.g., resolution, style).

        Returns:
            Optional[str]: The path to the saved image file, or None if saving failed or output_path was not provided.
        """
        if not self.api_key or not self.api_base_url or not self.model_id:
            raise ValueError("Doubao ImageClient not properly configured. Check environment variables.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        # Doubao Seedream models typically use 'prompt' and 'extra_params' structure
        payload = {
          "model": self.model_id,
          "prompt": prompt,  # 下方会给出定制化prompt模板
          "image": kwargs.get("images", reference_images or []),  # 核心：传入图片（支持URL或base64编码）
          "image_strength": kwargs.get("image_strength", 0.6),  # 图片影响强度（0~1）
          # 原有参数保留
          "n": kwargs.get("n", 1),  # 单张生成保证细节，如需多版可设2-3
          "size": kwargs.get("size", "1280x720"),  # 宽高比16:9更适配阳光感场景，也可保留1024x1024
          "response_format": kwargs.get("response_format", "url"),
          "extra_params": {
             # 核心风格控制
             "seed": kwargs.get("seed", 42),  # 固定seed便于复现，0为随机
             "style": kwargs.get("style", "anime"),  # 基础风格锚定动漫，靠prompt强化赛璐珞
             "quality": kwargs.get("quality", "hd"),  # 高清模式保证细节/色彩精度
             # 赛璐珞+水粉关键参数
             "steps": kwargs.get("steps", 40),  # 40步平衡细节与笔触自然度（20步太糊，50步笔触会过度平滑）
             "cfg_scale": kwargs.get("cfg_scale", 10.0),  # 高CFG（10）强制贴合prompt的风格描述，避免偏离赛璐珞/水粉
             "sampler": kwargs.get("sampler", "DPM++ 2M Karras"),  # 该采样器能精准还原硬边缘+色块，避免渐变
             "negative_prompt": kwargs.get("negative_prompt", "blurry, gradient, soft shadow, low saturation, flat color, digital painting, smooth brush, overdetailed, messy lines, dull light, gray tone, watermark"),  # 排除所有不符合的特征
             # 色彩/光影强化
             "detail_level": kwargs.get("detail_level", "high"),  # 保留自然笔触的同时保证细节
             "enhance": kwargs.get("enhance", True),  # 开启画质增强，强化饱和度/阳光感
             "contrast": kwargs.get("contrast", 1.2),  # 对比度+20%，强化色块边界
             "saturation": kwargs.get("saturation", 1.4),  # 饱和度+40%，契合高饱和需求（若模型支持该参数，无则靠prompt补充）
             "brightness": kwargs.get("brightness", 1.1),  # 亮度+10%，强化阳光感
             # 随机性控制（避免风格跑偏）
             "seed_override": kwargs.get("seed_override", True),  # 固定seed，复现最优效果
             "variation_strength": kwargs.get("variation_strength", 0.1)  # 低差异度，保证风格稳定
             }
           }

        try:
            # Assuming the endpoint for image generation is '/images/generations'
            response = self.http_client.post("/images/generations", json=payload, headers=headers, timeout=120)
            response.raise_for_status() # Raise an exception for bad status codes

            response_data = response.json()
            # print(f"Doubao API response: {response_data}") # For debugging

            if "data" in response_data and len(response_data["data"]) > 0:
                image_info = response_data["data"][0] # Take the first generated image

                if image_info.get("b64_json"):
                    # Handle base64 encoded image
                    image_data = base64.b64decode(image_info["b64_json"])
                    if output_path:
                        with open(output_path, "wb") as f:
                            f.write(image_data)
                        print(f"Generated image saved to {output_path}")
                        return output_path
                    else:
                        print("Image generated as base64, but no output_path provided to save it.")
                        return None # Or return BytesIO(image_data)
                elif image_info.get("url"):
                    # Handle image URL
                    image_url = image_info["url"]
                    if output_path:
                        image_response = httpx.get(image_url, timeout=60)
                        image_response.raise_for_status()
                        with open(output_path, "wb") as f:
                            f.write(image_response.content)
                        print(f"Generated image saved to {output_path}")
                        return output_path
                    else:
                        print(f"Image generated as URL: {image_url}, but no output_path provided to save it.")
                        return image_url # Return URL if not saving locally
            else:
                print(f"No image data found in Doubao API response: {response_data}")
                return None

        except httpx.HTTPStatusError as e:
            print(f"HTTP error generating image: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            print(f"Request error generating image: {e}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during image generation: {e}")
            raise

_image_client_instance = None

def get_image_client() -> ImageClient:
    global _image_client_instance
    if _image_client_instance is None:
        _image_client_instance = ImageClient()
    return _image_client_instance