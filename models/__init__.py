"""
Models package for Dreamweaver Bedtime Stories.
Contains Pydantic models for data validation and structure.
"""

from .pydantic_models import (
    # Enums
    AgeRange,
    StoryCategory,
    StoryLength,
    # Chaptered story models
    Character,
    Chapter,
    ChapteredStory,
    # Judge scoring models
    JudgeCriterionScore,
    JudgeScores,
    ImprovementSuggestion,
    JudgeEvaluation,
    IterationResult,
    QualityIterationsPanel,
    # Settings and requests
    GenerationSettings,
    GenerationRequest,
    ImageGenerationRequest,
    UserInteraction,
    CategoryClassification,
    # Utility functions
    get_category_emoji,
    get_age_range_description
)

__all__ = [
    # Enums
    "AgeRange",
    "StoryCategory",
    "StoryLength",
    # Story models
    "Character",
    "Chapter", 
    "ChapteredStory",
    # Judge models
    "JudgeCriterionScore",
    "JudgeScores",
    "ImprovementSuggestion",
    "JudgeEvaluation",
    "IterationResult",
    "QualityIterationsPanel",
    # Request models
    "GenerationSettings",
    "GenerationRequest",
    "ImageGenerationRequest",
    "UserInteraction",
    "CategoryClassification",
    # Functions
    "get_category_emoji",
    "get_age_range_description"
]
