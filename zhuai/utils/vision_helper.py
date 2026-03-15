"""Vision AI helper for browser automation using Ollama."""

import base64
import json
import httpx
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile


class VisionHelper:
    """Use local Ollama vision models to analyze browser screenshots."""
    
    DEFAULT_MODEL = "gemma3:4b"
    OLLAMA_API = "http://localhost:11434/api"
    
    def __init__(self, model: Optional[str] = None, timeout: int = 60):
        self.model = model or self.DEFAULT_MODEL
        self.timeout = timeout
    
    async def analyze_screenshot(
        self, 
        screenshot_bytes: bytes,
        prompt: str,
    ) -> str:
        """Analyze a screenshot with vision model."""
        image_base64 = base64.b64encode(screenshot_bytes).decode("utf-8")
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [image_base64],
                }
            ],
            "stream": False,
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.OLLAMA_API}/chat",
                json=payload,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("message", {}).get("content", "")
    
    async def detect_captcha_type(self, screenshot_bytes: bytes) -> Dict[str, Any]:
        """Detect what type of CAPTCHA is on the page."""
        prompt = """分析这张网页截图，检测是否有验证码(CAPTCHA)。如果有，请识别类型：

1. 滑块验证 - 需要拖动滑块到指定位置
2. 点击验证 - 需要点击图片中特定位置
3. 文字验证 - 需要输入显示的文字/数字
4. 拼图验证 - 需要拖动拼图块
5. 旋转验证 - 需要旋转图片到正确角度
6. 无验证码

请用JSON格式回复：
{"has_captcha": true/false, "type": "类型名称", "description": "简短描述", "action_needed": "需要的操作"}

如果没有验证码，回复：
{"has_captcha": false, "type": null, "description": "无验证码", "action_needed": null}"""
        
        try:
            result = await self.analyze_screenshot(screenshot_bytes, prompt)
            json_match = result[result.find("{"):result.rfind("}")+1]
            return json.loads(json_match)
        except Exception as e:
            return {"has_captcha": False, "error": str(e)}
    
    async def solve_slider_captcha(
        self, 
        screenshot_bytes: bytes,
    ) -> Optional[Dict[str, int]]:
        """Analyze slider CAPTCHA and return drag offset."""
        prompt = """这是一个滑块验证码。请分析图片：

1. 找到滑块的位置
2. 找到滑块需要移动到的目标位置
3. 计算需要拖动的像素距离

请用JSON格式回复：
{"slider_x": 滑块当前位置x坐标, "target_x": 目标位置x坐标, "drag_distance": 需要拖动的像素距离, "confidence": 0-1的置信度}

如果无法确定，请回复：
{"error": "无法识别", "confidence": 0}"""
        
        try:
            result = await self.analyze_screenshot(screenshot_bytes, prompt)
            json_match = result[result.find("{"):result.rfind("}")+1]
            data = json.loads(json_match)
            if data.get("confidence", 0) > 0.5:
                return data
            return None
        except Exception:
            return None
    
    async def solve_click_captcha(
        self,
        screenshot_bytes: bytes,
        instruction: str = "",
    ) -> Optional[List[Dict[str, int]]]:
        """Analyze click CAPTCHA and return click positions."""
        prompt = f"""这是一个点击验证码。
{instruction if instruction else "请找出需要点击的位置。"}

请用JSON格式回复点击坐标列表：
[{{"x": x坐标, "y": y坐标}}, ...]

如果无法确定，请回复：
[]"""
        
        try:
            result = await self.analyze_screenshot(screenshot_bytes, prompt)
            json_match = result[result.find("["):result.rfind("]")+1]
            return json.loads(json_match)
        except Exception:
            return None
    
    async def solve_text_captcha(
        self,
        screenshot_bytes: bytes,
    ) -> Optional[str]:
        """Recognize text in CAPTCHA image."""
        prompt = """请识别图片中显示的验证码文字或数字。

只回复识别出的文字内容，不要有其他说明。
如果无法识别，回复"UNKNOWN"。"""
        
        try:
            result = await self.analyze_screenshot(screenshot_bytes, prompt)
            text = result.strip()
            if text and text != "UNKNOWN":
                return text
            return None
        except Exception:
            return None
    
    async def analyze_page_for_login(
        self,
        screenshot_bytes: bytes,
    ) -> Dict[str, Any]:
        """Analyze page to detect login requirements."""
        prompt = """分析这个网页截图，检测页面状态：

1. 是否需要登录？
2. 是否有验证码？
3. 页面主要内容是什么？

请用JSON格式回复：
{
    "needs_login": true/false,
    "has_captcha": true/false,
    "page_type": "search_results/login_page/captcha_page/other",
    "description": "简短描述页面内容",
    "suggested_action": "建议的下一步操作"
}"""
        
        try:
            result = await self.analyze_screenshot(screenshot_bytes, prompt)
            json_match = result[result.find("{"):result.rfind("}")+1]
            return json.loads(json_match)
        except Exception as e:
            return {"error": str(e)}
    
    async def find_element_position(
        self,
        screenshot_bytes: bytes,
        element_description: str,
    ) -> Optional[Dict[str, int]]:
        """Find position of a specific element on the page."""
        prompt = f"""在网页截图中找到以下元素并返回其中心坐标：

元素描述：{element_description}

请用JSON格式回复：
{{"x": 中心点x坐标, "y": 中心点y坐标, "width": 元素宽度, "height": 元素高度, "confidence": 0-1的置信度}}

如果找不到，回复：
{{"error": "未找到", "confidence": 0}}"""
        
        try:
            result = await self.analyze_screenshot(screenshot_bytes, prompt)
            json_match = result[result.find("{"):result.rfind("}")+1]
            data = json.loads(json_match)
            if data.get("confidence", 0) > 0.5:
                return data
            return None
        except Exception:
            return None