"""
Pydantic models for Dreamweaver Bedtime Stories application.
Defines data structures for story evaluation, generation, and validation.
Enhanced with age bands, chapter structure, and detailed judge scoring.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Optional, Any
from enum import Enum


class AgeRange(str, Enum):
    """Age range bands for story customization."""
    YOUNG = "5-7"      # 5-7 years: simpler sentences, smaller vocabulary, more repetition
    OLDER = "7-10"     # 7-10 years: slightly richer plot, still simple and calm


class StoryCategory(str, Enum):
    """Enhanced story categories for classification."""
    BEDTIME_CALM = "Bedtime Calm"
    LIGHT_ADVENTURE = "Light Adventure"
    SILLY_PLAYFUL = "Silly & Playful"
    FRIENDSHIP = "Friendship"
    LEARNING_CURIOSITY = "Learning & Curiosity"
    SURPRISE_ME = "Surprise Me"


class StoryLength(str, Enum):
    """Story length options: Short = 5 chapters, Long = 7 chapters."""
    SHORT = "Short"   # 5 chapters
    LONG = "Long"    # 7 chapters
    
    @property
    def chapter_count(self) -> int:
        """Get the number of chapters for this length."""
        mapping = {
            StoryLength.SHORT: 5,
            StoryLength.LONG: 7
        }
        return mapping[self]


class Character(BaseModel):
    """A character in the story with name and description."""
    name: str = Field(description="Character's name")
    description: str = Field(description="One-line character description")
    
    
class Chapter(BaseModel):
    """A chapter in the story with structured content."""
    chapter_number: int = Field(description="Chapter number (1-indexed)")
    chapter_title: str = Field(description="Title of the chapter")
    chapter_text: str = Field(description="Full text content of the chapter")
    chapter_summary: str = Field(description="Brief 1-2 sentence summary of the chapter")
    image_prompt: str = Field(
        default="A colorful children's book illustration",
        description="Prompt for generating chapter illustration"
    )


class ChapteredStory(BaseModel):
    """Complete story structure with chapters and characters."""
    title: str = Field(description="Overall story title")
    category: StoryCategory = Field(description="Story category")
    age_range: AgeRange = Field(description="Target age range")
    characters: List[Character] = Field(description="List of story characters")
    chapters: List[Chapter] = Field(description="List of story chapters")
    moral_or_theme: Optional[str] = Field(
        default=None,
        description="Optional moral or theme of the story"
    )
    
    @property
    def chapter_count(self) -> int:
        return len(self.chapters)




class JudgeCriterionScore(BaseModel):
    """Score for a single evaluation criterion."""
    score: int = Field(ge=1, le=10, description="Score from 1-10")
    reasoning: str = Field(description="Brief reasoning for this score")


class JudgeScores(BaseModel):
    """Detailed judge scores for story evaluation."""
    age_appropriate_language: JudgeCriterionScore = Field(
        description="Age-appropriate vocabulary and sentence complexity"
    )
    emotional_safety: JudgeCriterionScore = Field(
        description="No scary, violent, or distressing content"
    )
    engagement: JudgeCriterionScore = Field(
        description="How engaging and interesting the story is"
    )
    coherence: JudgeCriterionScore = Field(
        description="Logical flow and story consistency"
    )
    bedtime_suitability: JudgeCriterionScore = Field(
        description="Calm, reassuring ending suitable for bedtime"
    )
    
    @property
    def overall_score(self) -> float:
        """Calculate average score across all criteria."""
        scores = [
            self.age_appropriate_language.score,
            self.emotional_safety.score,
            self.engagement.score,
            self.coherence.score,
            self.bedtime_suitability.score
        ]
        return sum(scores) / len(scores)
    
    def get_scores_dict(self) -> Dict[str, int]:
        """Get all scores as a dictionary."""
        return {
            "Age-Appropriate Language": self.age_appropriate_language.score,
            "Emotional Safety": self.emotional_safety.score,
            "Engagement": self.engagement.score,
            "Coherence": self.coherence.score,
            "Bedtime Suitability": self.bedtime_suitability.score
        }


class ImprovementSuggestion(BaseModel):
    """A specific improvement suggestion from the judge."""
    criterion: str = Field(description="Which criterion this addresses")
    suggestion: str = Field(description="Specific actionable improvement")
    priority: int = Field(ge=1, le=3, description="Priority 1=highest, 3=lowest")


class JudgeEvaluation(BaseModel):
    """Complete judge evaluation with scores and suggestions."""
    scores: JudgeScores = Field(description="Detailed scores for each criterion")
    overall_score: float = Field(description="Average overall score")
    improvement_suggestions: List[ImprovementSuggestion] = Field(
        description="Top 3 actionable improvement suggestions"
    )
    passed: bool = Field(description="Whether the story passes quality threshold")
    pass_reasoning: str = Field(description="Explanation of pass/fail decision")
    
    @classmethod
    def calculate_pass(cls, scores: JudgeScores, threshold: float = 8.0, safety_threshold: int = 9) -> bool:
        """
        Determine if story passes based on thresholds.
        Pass if: overall >= 8.0 AND emotional_safety >= 9
        """
        return (scores.overall_score >= threshold and 
                scores.emotional_safety.score >= safety_threshold)


class IterationResult(BaseModel):
    """Result of a single iteration in the judge loop."""
    iteration_number: int = Field(description="Which iteration (1, 2, or 3)")
    overall_score: float = Field(description="Overall score for this iteration")
    score_delta: Optional[float] = Field(
        default=None,
        description="Change from previous iteration score"
    )
    passed: bool = Field(description="Whether this iteration passed")
    suggestions: List[str] = Field(description="Short list of judge suggestions")


class QualityIterationsPanel(BaseModel):
    """Data for displaying the quality iterations panel in UI."""
    iterations: List[IterationResult] = Field(description="All iteration results")
    final_passed: bool = Field(description="Whether final story passed")
    total_iterations: int = Field(description="Total iterations performed")


class CategoryClassification(BaseModel):
    """Result of story category classification."""
    category: StoryCategory = Field(description="Classified story category")
    confidence: float = Field(
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0
    )


class GenerationSettings(BaseModel):
    """Settings for story generation."""
    age_range: AgeRange = Field(default=AgeRange.YOUNG, description="Target age range")
    category: StoryCategory = Field(default=StoryCategory.BEDTIME_CALM, description="Story category")
    story_length: StoryLength = Field(default=StoryLength.SHORT, description="Story length")
    user_prompt: str = Field(description="User's story idea")
    
    @property
    def chapter_count(self) -> int:
        return self.story_length.chapter_count


class GenerationRequest(BaseModel):
    """Request for story generation."""
    user_prompt: str = Field(description="User's story idea")
    category: StoryCategory = Field(description="Story category")
    age_range: AgeRange = Field(default=AgeRange.YOUNG, description="Target age range")
    story_length: StoryLength = Field(default=StoryLength.SHORT, description="Story length")
    previous_attempt: Optional[str] = Field(
        default=None,
        description="Previous story attempt if regenerating"
    )
    improvement_areas: List[str] = Field(
        default_factory=list,
        description="Areas to improve from previous evaluation"
    )
    previous_characters: Optional[List[Character]] = Field(
        default=None,
        description="Characters from previous attempt to preserve"
    )


class ImageGenerationRequest(BaseModel):
    """Request for image generation."""
    prompt: str = Field(description="Image generation prompt")
    section_title: str = Field(description="Title of the story section")
    style: str = Field(
        default="colorful, friendly, children's book illustration",
        description="Art style for the image"
    )


class UserInteraction(BaseModel):
    """User interaction options after story completion."""
    action: str = Field(description="User's chosen action")
    modification_request: Optional[str] = Field(
        default=None,
        description="Specific modification request if applicable"
    )


# Utility functions
def get_category_emoji(category: StoryCategory) -> str:
    """Get the emoji for a story category."""
    emoji_map = {
        StoryCategory.BEDTIME_CALM: "🌙",
        StoryCategory.LIGHT_ADVENTURE: "🧭",
        StoryCategory.SILLY_PLAYFUL: "😄",
        StoryCategory.FRIENDSHIP: "❤️",
        StoryCategory.LEARNING_CURIOSITY: "🔍",
        StoryCategory.SURPRISE_ME: "🎲"
    }
    return emoji_map.get(category, "📖")


def get_age_range_description(age_range: AgeRange) -> str:
    """Get a description of the age range style."""
    descriptions = {
        AgeRange.YOUNG: "Simple sentences, familiar words, gentle pacing, more repetition",
        AgeRange.OLDER: "Slightly richer vocabulary, more complex plot, still calm and appropriate"
    }
    return descriptions.get(age_range, "")
