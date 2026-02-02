"""
Story Improver Agent for Dreamweaver Bedtime Stories.
Iteratively improves stories based on judge feedback while preserving characters and structure.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from models.pydantic_models import (
    ChapteredStory, Chapter, Character, 
    JudgeEvaluation, ImprovementSuggestion,
    AgeRange, StoryCategory
)
from prompts.prompts import PromptTemplates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoryImproverAgent:
    """
    Agent responsible for improving stories based on judge feedback.
    Preserves character consistency and story structure while addressing specific issues.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.6):
        """
        Initialize the story improver agent.
        
        Args:
            model_name: OpenAI model to use for improvement
            temperature: Temperature for creative but controlled improvement
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
        
        logger.info(f"StoryImproverAgent initialized with model: {model_name}")
    
    def improve_story(
        self,
        story: ChapteredStory,
        judge_evaluation: JudgeEvaluation,
        age_range: str = "5-7",
        category: str = "Bedtime Calm"
    ) -> ChapteredStory:
        """
        Improve a story based on judge evaluation feedback.
        
        Args:
            story: The original ChapteredStory to improve
            judge_evaluation: JudgeEvaluation with scores and suggestions
            age_range: Target age range
            category: Story category
            
        Returns:
            Improved ChapteredStory
        """
        logger.info(f"Improving story '{story.title}' based on judge feedback")
        
        # Format characters as JSON
        characters_json = json.dumps(
            [{"name": c.name, "description": c.description} for c in story.characters],
            indent=2
        )
        
        # Format chapters as JSON
        chapters_json = json.dumps(
            [
                {
                    "chapter_number": ch.chapter_number,
                    "chapter_title": ch.chapter_title,
                    "chapter_text": ch.chapter_text,
                    "chapter_summary": ch.chapter_summary,
                    "image_prompt": ch.image_prompt
                }
                for ch in story.chapters
            ],
            indent=2
        )
        
        # Format judge feedback
        feedback_parts = []
        for suggestion in judge_evaluation.improvement_suggestions:
            feedback_parts.append(
                f"- [{suggestion.criterion}] (Priority {suggestion.priority}): {suggestion.suggestion}"
            )
        
        # Add low-scoring criteria
        scores = judge_evaluation.scores
        if scores.age_appropriate_language.score < 8:
            feedback_parts.append(
                f"- Age-appropriate language needs improvement (scored {scores.age_appropriate_language.score}/10): "
                f"{scores.age_appropriate_language.reasoning}"
            )
        if scores.emotional_safety.score < 9:
            feedback_parts.append(
                f"- CRITICAL: Emotional safety must be improved (scored {scores.emotional_safety.score}/10): "
                f"{scores.emotional_safety.reasoning}"
            )
        if scores.bedtime_suitability.score < 8:
            feedback_parts.append(
                f"- Bedtime suitability needs improvement (scored {scores.bedtime_suitability.score}/10): "
                f"{scores.bedtime_suitability.reasoning}"
            )
        
        judge_feedback = "\n".join(feedback_parts)
        
        # Get improvement prompt
        improvement_prompt = self.prompt_templates.get_story_improver_prompt(
            title=story.title,
            age_range=age_range,
            category=category,
            characters_json=characters_json,
            chapters_json=chapters_json,
            chapter_count=len(story.chapters),
            judge_feedback=judge_feedback
        )
        
        # Try to improve with retries
        for attempt in range(self.max_retries):
            try:
                messages = [HumanMessage(content=improvement_prompt)]
                response = self.llm.invoke(messages)
                
                # Parse and validate improved story
                improved_story = self._parse_improved_story(
                    response.content,
                    original_story=story,
                    age_range=age_range,
                    category=category
                )
                
                logger.info(f"Story improved successfully (attempt {attempt + 1})")
                return improved_story
                
            except Exception as e:
                logger.warning(f"Improvement attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error("All improvement attempts failed, returning original story")
                    return story
        
        return story
    
    def _parse_improved_story(
        self,
        response_content: str,
        original_story: ChapteredStory,
        age_range: str,
        category: str
    ) -> ChapteredStory:
        """
        Parse the LLM response into an improved ChapteredStory.
        Includes robust JSON extraction and fallback to original on failure.
        
        Args:
            response_content: Raw LLM response
            original_story: Original story for fallback
            age_range: Target age range
            category: Story category
            
        Returns:
            Parsed ChapteredStory
        """
        try:
            # Robust JSON extraction
            json_content = self._extract_json(response_content)
            story_data = json.loads(json_content)
            
            # Parse characters (preserve from original if not in response)
            characters = []
            chars_data = story_data.get("characters", [])
            if chars_data:
                for char_data in chars_data:
                    name = char_data.get("name", "").strip()
                    if name:
                        characters.append(Character(
                            name=name,
                            description=char_data.get("description", "")
                        ))
            
            # Fall back to original characters if none parsed
            if not characters:
                characters = original_story.characters
            
            # Parse chapters with validation
            chapters = []
            for i, ch_data in enumerate(story_data.get("chapters", [])):
                chapter_text = ch_data.get("chapter_text", "").strip()
                if not chapter_text:
                    # Use original chapter text if improved is empty
                    if i < len(original_story.chapters):
                        chapter_text = original_story.chapters[i].chapter_text
                    else:
                        continue
                
                chapters.append(Chapter(
                    chapter_number=ch_data.get("chapter_number", i + 1),
                    chapter_title=ch_data.get("chapter_title", f"Chapter {i + 1}"),
                    chapter_text=chapter_text,
                    chapter_summary=ch_data.get("chapter_summary", "")[:200],
                    image_prompt=ch_data.get("image_prompt", f"Children's book illustration for chapter {i + 1}")
                ))
            
            # If no chapters parsed, use original
            if not chapters:
                chapters = original_story.chapters
            
            # Create improved story
            return ChapteredStory(
                title=story_data.get("title", original_story.title),
                category=StoryCategory(category) if category else original_story.category,
                age_range=AgeRange(age_range) if age_range else original_story.age_range,
                characters=characters,
                chapters=chapters,
                moral_or_theme=story_data.get("moral_or_theme", original_story.moral_or_theme)
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in improvement: {str(e)}")
            raise ValueError(f"Invalid JSON in improvement response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing improved story: {str(e)}")
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
    
    def format_improvement_summary(
        self,
        original_score: float,
        new_score: float,
        suggestions_addressed: List[str]
    ) -> str:
        """
        Format a summary of the improvements made.
        
        Args:
            original_score: Score before improvement
            new_score: Score after improvement
            suggestions_addressed: List of addressed suggestions
            
        Returns:
            Formatted summary string
        """
        delta = new_score - original_score
        delta_str = f"+{delta:.1f}" if delta >= 0 else f"{delta:.1f}"
        
        summary_parts = [
            f"Score: {original_score:.1f} → {new_score:.1f} ({delta_str})",
            "",
            "Improvements made:"
        ]
        
        for suggestion in suggestions_addressed[:3]:
            summary_parts.append(f"  • {suggestion}")
        
        return "\n".join(summary_parts)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node function for story improvement.
        
        Args:
            state: Current state dictionary
            
        Returns:
            Updated state with improved story
        """
        # Get story and evaluation from state
        story = state.get("chaptered_story")
        judge_evaluation = state.get("judge_evaluation")
        age_range = state.get("age_range", "5-7")
        category = state.get("category", "Bedtime Calm")
        
        if not story:
            raise ValueError("No chaptered_story found in state")
        if not judge_evaluation:
            raise ValueError("No judge_evaluation found in state")
        
        # Store previous score for delta calculation
        previous_score = judge_evaluation.overall_score
        state["previous_score"] = previous_score
        
        # Improve story
        improved_story = self.improve_story(
            story=story,
            judge_evaluation=judge_evaluation,
            age_range=age_range,
            category=category
        )
        
        # Update state
        state["chaptered_story"] = improved_story
        state["story_text"] = self._story_to_text(improved_story)
        state["improvement_made"] = True
        
        # Track which suggestions were addressed
        addressed = [s.suggestion for s in judge_evaluation.improvement_suggestions[:3]]
        state["suggestions_addressed"] = addressed
        
        logger.info(f"Story improvement completed for '{improved_story.title}'")
        
        return state
    
    def _story_to_text(self, story: ChapteredStory) -> str:
        """Convert ChapteredStory to plain text for evaluation."""
        text_parts = [f"Title: {story.title}\n"]
        
        text_parts.append("Characters:")
        for char in story.characters:
            text_parts.append(f"  - {char.name}: {char.description}")
        
        text_parts.append("")
        
        for chapter in story.chapters:
            text_parts.append(f"\n{chapter.chapter_title}")
            text_parts.append(chapter.chapter_text)
        
        return "\n".join(text_parts)


def create_story_improver(model_name: str = "gpt-3.5-turbo") -> StoryImproverAgent:
    """
    Factory function to create a StoryImproverAgent.
    
    Args:
        model_name: OpenAI model name to use
        
    Returns:
        Configured StoryImproverAgent instance
    """
    return StoryImproverAgent(model_name=model_name)
