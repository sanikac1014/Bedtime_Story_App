"""
Gemini Image Generator Agent for Dreamweaver Bedtime Stories.
Generates child-friendly illustrations using Google Gemini (google-genai SDK).
"""

import logging
import os
import io
import sys
from typing import Dict, Any, List, Optional
from PIL import Image
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiImageGenerator:
    """
    Image generator using Google Gemini (google-genai Client).
    Creates child-friendly illustrations for bedtime stories.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash-image"):
        """
        Initialize the Gemini image generator.

        Args:
            model_name: Gemini model for image generation (e.g. gemini-2.5-flash-image, gemini-2.0-flash-exp).
        """
        load_dotenv(override=True)
        _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        load_dotenv(os.path.join(_root, ".env"), override=True)

        api_key = (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY") or "").strip()
        if not api_key:
            raise ValueError(
                "No GOOGLE_API_KEY or GEMINI_API_KEY found. "
                "Set one of these in your .env file for image generation."
            )
        os.environ["GOOGLE_API_KEY"] = api_key

        try:
            from google import genai
            self.client = genai.Client(api_key=api_key)
        except ImportError as e:
            raise ImportError(
                "google-genai package not installed or wrong Python environment. "
                "Install with: python -m pip install google-genai "
                "(Use the same Python that runs Streamlit. Current: %s)" % sys.executable
            ) from e

        self.model_name = model_name
        logger.info(f"GeminiImageGenerator initialized with model: {model_name}")

    def _build_safe_prompt(self, base_prompt: str, category: str) -> str:
        """Build a safety-enhanced prompt for child-friendly images."""
        style_hints = {
            "Bedtime Calm": "soft dreamy watercolor style, gentle purple and blue tones, peaceful moonlit scene",
            "Light Adventure": "bright colorful children's book illustration, warm yellows and greens, sense of wonder",
            "Silly & Playful": "whimsical cartoon style, bright cheerful colors, expressive funny characters",
            "Friendship": "warm cozy illustration style, soft oranges and pinks, heartwarming scene",
            "Learning & Curiosity": "clear detailed illustration, nature colors, sense of discovery",
            "Surprise Me": "magical whimsical illustration, varied colorful palette",
        }
        style = style_hints.get(category, style_hints["Bedtime Calm"])
        return f"""Create a children's book illustration.

STYLE: {style}

SCENE: {base_prompt}

REQUIREMENTS:
- Safe, G-rated content appropriate for ages 5-10
- Friendly, welcoming characters with soft rounded features
- No text, labels, or speech bubbles
- Warm, inviting colors
- Clear composition with main subject centered
"""

    def _generate_image(self, prompt: str, section_title: str) -> Optional[Image.Image]:
        """
        Call Gemini API and return PIL Image or None.
        """
        try:
            logger.info(f"Calling Gemini API for: {section_title or 'scene'}")

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt],
            )

            parts = None
            if hasattr(response, "candidates") and response.candidates:
                c0 = response.candidates[0]
                if c0.content and hasattr(c0.content, "parts"):
                    parts = c0.content.parts
            elif hasattr(response, "parts"):
                parts = response.parts

            if not parts:
                logger.warning(f"No parts in response for: {section_title}")
                return None

            for part in parts:
                if hasattr(part, "inline_data") and part.inline_data is not None:
                    image_data = part.inline_data.data
                    logger.info(f"Generated image for: {section_title}")

                    image = Image.open(io.BytesIO(image_data))
                    if image.mode == "RGBA":
                        background = Image.new("RGB", image.size, (255, 255, 255))
                        background.paste(image, mask=image.split()[3])
                        image = background
                    elif image.mode != "RGB":
                        image = image.convert("RGB")
                    return image

                if hasattr(part, "text") and part.text:
                    logger.debug(f"Text response: {part.text[:200]}")

            logger.warning(f"No image data in response for: {section_title}")
            return None

        except Exception as e:
            logger.error(f"Error generating image for {section_title}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return None

    def generate_image(
        self,
        prompt: str,
        section_title: str = "",
        category: str = "Bedtime Calm",
        max_retries: int = 2,
    ) -> Optional[Image.Image]:
        """
        Generate one image. Returns PIL Image or None (no placeholder).
        """
        full_prompt = self._build_safe_prompt(prompt, category)
        for attempt in range(max_retries):
            img = self._generate_image(full_prompt, section_title or "scene")
            if img is not None:
                return img
            if attempt < max_retries - 1:
                import time
                time.sleep(1)
                logger.info(f"Retry {attempt + 2}/{max_retries} for: {section_title}")
        return None

    def generate_chapter_images(
        self,
        chapters: List[Dict[str, Any]],
        category: str = "Bedtime Calm",
    ) -> List[Optional[Image.Image]]:
        """
        Generate one image per chapter. Returns list of PIL Image or None (no placeholders).
        """
        images = []
        for i, chapter in enumerate(chapters):
            prompt = chapter.get("image_prompt", "")
            title = chapter.get("chapter_title", f"Chapter {i + 1}")
            if not prompt:
                images.append(None)
                continue
            image = self.generate_image(
                prompt=prompt,
                section_title=title,
                category=category,
            )
            images.append(image)
            if i < len(chapters) - 1:
                import time
                time.sleep(0.5)
        return images

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph node: generate chapter images and update state."""
        chaptered_story = state.get("chaptered_story")
        if not chaptered_story or not getattr(chaptered_story, "chapters", None):
            state["images"] = []
            state["images_generated"] = False
            return state

        category = getattr(chaptered_story.category, "value", None) or "Bedtime Calm"
        chapters_data = [
            {
                "chapter_title": ch.chapter_title,
                "image_prompt": getattr(ch, "image_prompt", "") or "",
            }
            for ch in chaptered_story.chapters
        ]
        images = self.generate_chapter_images(chapters_data, category)
        state["images"] = images
        state["images_generated"] = True
        successful = sum(1 for img in images if img is not None)
        logger.info(f"Image generation complete: {successful}/{len(images)} successful")
        return state

    def cleanup(self):
        """Release client reference."""
        self.client = None
        logger.info("GeminiImageGenerator cleaned up")


def create_gemini_image_generator(
    model: str = "gemini-2.5-flash-image",
) -> GeminiImageGenerator:
    """Factory: create GeminiImageGenerator. Raises if GOOGLE_API_KEY / GEMINI_API_KEY missing."""
    return GeminiImageGenerator(model_name=model)
