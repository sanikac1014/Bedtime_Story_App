"""
Story Generator Agent for Dreamweaver Bedtime Stories.
Generates structured chaptered stories based on age range, category, and story length.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from models.pydantic_models import (
    StoryCategory, ChapteredStory, Chapter, Character, AgeRange
)
from prompts.prompts import PromptTemplates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoryGeneratorAgent:
    """
    Agent responsible for generating structured chaptered stories.
    Supports age bands, expanded categories, and configurable story length.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.7):
        """
        Initialize the story generator agent.
        
        Args:
            model_name: OpenAI model to use for story generation
            temperature: Temperature for creative generation
        """
        import os
        from dotenv import load_dotenv
        
        load_dotenv(override=True)
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("No OpenAI API key found. Please set OPENAI_API_KEY in your .env file.")
        
        os.environ['OPENAI_API_KEY'] = api_key
        
        self.llm = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=4000,
            openai_api_key=api_key
        )
        self.prompt_templates = PromptTemplates()
        self.max_retries = 2
        
        logger.info(f"StoryGeneratorAgent initialized with model: {model_name}")
    
    def generate_chaptered_story(
        self,
        user_prompt: str,
        age_range: str = "5-7",
        category: str = "Bedtime Calm",
        chapter_count: int = 5,
        improvement_instructions: str = ""
    ) -> ChapteredStory:
        """
        Generate a structured chaptered story.
        
        Args:
            user_prompt: User's story idea
            age_range: Target age range ("5-7" or "7-10")
            category: Story category
            chapter_count: Number of chapters (5 or 7)
            improvement_instructions: Optional instructions for improvement
            
        Returns:
            ChapteredStory object
        """
        logger.info(f"Generating {chapter_count}-chapter {category} story for ages {age_range}")
        
        # Get the generation prompt
        generation_prompt = self.prompt_templates.get_chaptered_story_prompt(
            user_prompt=user_prompt,
            age_range=age_range,
            category=category,
            chapter_count=chapter_count,
            improvement_instructions=improvement_instructions
        )
        
        # Try generation with retries
        for attempt in range(self.max_retries):
            try:
                messages = [HumanMessage(content=generation_prompt)]
                response = self.llm.invoke(messages)
                
                # Parse the response
                story = self._parse_chaptered_story_response(
                    response.content,
                    age_range=age_range,
                    category=category
                )
                
                logger.info(f"Story generated successfully: '{story.title}' ({attempt + 1} attempt(s))")
                return story
                
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error("All generation attempts failed")
                    raise Exception(f"Story generation failed after {self.max_retries} attempts: {str(e)}")
        
        raise Exception("Story generation failed")
    
    def _parse_chaptered_story_response(
        self,
        response_content: str,
        age_range: str,
        category: str
    ) -> ChapteredStory:
        """
        Parse LLM response into a ChapteredStory object.
        Includes robust JSON extraction and validation.
        
        Args:
            response_content: Raw LLM response
            age_range: Target age range
            category: Story category
            
        Returns:
            Parsed ChapteredStory
        """
        try:
            # Robust JSON extraction
            json_content = self._extract_json(response_content)
            story_data = json.loads(json_content)
            
            # Validate required fields
            if not story_data.get("title"):
                story_data["title"] = "A Bedtime Story"
            
            # Parse characters
            characters = []
            for char_data in story_data.get("characters", []):
                name = char_data.get("name", "").strip()
                description = char_data.get("description", "").strip()
                if name:  # Only add if name exists
                    characters.append(Character(
                        name=name,
                        description=description or "A character in the story"
                    ))
            
            # Ensure at least one character
            if not characters:
                characters = [Character(name="Main Character", description="The hero of our story")]
            
            # Parse chapters with validation
            chapters = []
            for i, ch_data in enumerate(story_data.get("chapters", [])):
                chapter_text = ch_data.get("chapter_text", "").strip()
                if not chapter_text:
                    continue  # Skip empty chapters
                    
                chapters.append(Chapter(
                    chapter_number=ch_data.get("chapter_number", i + 1),
                    chapter_title=ch_data.get("chapter_title", f"Chapter {i + 1}"),
                    chapter_text=chapter_text,
                    chapter_summary=ch_data.get("chapter_summary", "")[:200],  # Limit summary length
                    image_prompt=ch_data.get("image_prompt", f"Children's book illustration for chapter {i + 1}")
                ))
            
            if not chapters:
                raise ValueError("No valid chapters found in story data")
            
            # Create ChapteredStory
            return ChapteredStory(
                title=story_data.get("title", "A Bedtime Story"),
                category=StoryCategory(category),
                age_range=AgeRange(age_range),
                characters=characters,
                chapters=chapters,
                moral_or_theme=story_data.get("moral_or_theme")
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.debug(f"Response content: {response_content[:500]}...")
            raise ValueError(f"Invalid JSON in story response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing story: {str(e)}")
            raise
    
    def _extract_json(self, content: str) -> str:
        """
        Robustly extract JSON from LLM response.
        Handles markdown code blocks and extra text.
        
        Args:
            content: Raw LLM response
            
        Returns:
            Extracted JSON string
        """
        content = content.strip()
        
        # Try to extract from markdown code block
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()
        
        # Try to extract from generic code block
        if "```" in content:
            start = content.find("```") + 3
            # Skip any language identifier on the same line
            newline = content.find("\n", start)
            if newline > start:
                start = newline + 1
            end = content.find("```", start)
            if end > start:
                return content[start:end].strip()
        
        # Find JSON object boundaries
        start_idx = content.find('{')
        end_idx = content.rfind('}') + 1
        
        if start_idx == -1 or end_idx <= start_idx:
            raise ValueError("No JSON found in response")
        
        return content[start_idx:end_idx]
    
    def _story_to_text(self, story: ChapteredStory) -> str:
        """
        Convert ChapteredStory to plain text for evaluation.
        
        Args:
            story: ChapteredStory object
            
        Returns:
            Plain text representation
        """
        text_parts = [f"Title: {story.title}\n"]
        
        text_parts.append("Characters:")
        for char in story.characters:
            text_parts.append(f"  - {char.name}: {char.description}")
        
        text_parts.append("")
        
        for chapter in story.chapters:
            text_parts.append(f"\n--- {chapter.chapter_title} ---")
            text_parts.append(chapter.chapter_text)
        
        if story.moral_or_theme:
            text_parts.append(f"\nTheme: {story.moral_or_theme}")
        
        return "\n".join(text_parts)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node function for story generation.
        
        Args:
            state: Current state dictionary
            
        Returns:
            Updated state with generated story
        """
        user_prompt = state.get("user_prompt", "")
        age_range = state.get("age_range", "5-7")
        category = state.get("category", "Bedtime Calm")
        story_length = state.get("story_length", "Short")
        
        # Get chapter count from story length (Short = 5, Long = 7)
        length_to_chapters = {
            "Short": 5,
            "Long": 7
        }
        chapter_count = length_to_chapters.get(story_length, 5)
        
        # Check for improvement instructions
        improvement_instructions = ""
        if state.get("improvement_needed") and state.get("judge_feedback"):
            improvement_instructions = state["judge_feedback"]
        
        if not user_prompt:
            raise ValueError("No user_prompt found in state")
        
        # Generate the chaptered story
        chaptered_story = self.generate_chaptered_story(
            user_prompt=user_prompt,
            age_range=age_range,
            category=category,
            chapter_count=chapter_count,
            improvement_instructions=improvement_instructions
        )
        
        # Update state
        state["chaptered_story"] = chaptered_story
        state["story_text"] = self._story_to_text(chaptered_story)
        state["story_title"] = chaptered_story.title
        
        logger.info(f"Story generation completed: '{chaptered_story.title}'")
        
        return state


def create_story_generator(model_name: str = "gpt-3.5-turbo") -> StoryGeneratorAgent:
    """
    Factory function to create a StoryGeneratorAgent.
    
    Args:
        model_name: OpenAI model name to use
        
    Returns:
        Configured StoryGeneratorAgent instance
    """
    return StoryGeneratorAgent(model_name=model_name)
