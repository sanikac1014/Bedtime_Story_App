"""
Category Classifier Agent for Dreamweaver Bedtime Stories.
Classifies user story ideas into one of six categories.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from models.pydantic_models import CategoryClassification, StoryCategory
from prompts.prompts import PromptTemplates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CategoryClassifierAgent:
    """
    Agent responsible for classifying story ideas into one of six categories.
    Categories: Bedtime Calm, Light Adventure, Silly & Playful, Friendship,
    Learning & Curiosity, Surprise Me.
    """
    
    # Category keywords for validation and confidence boosting
    CATEGORY_KEYWORDS = {
        "Bedtime Calm": [
            "sleep", "night", "dream", "moon", "star", "bed", "cozy", "warm",
            "quiet", "peaceful", "gentle", "rest", "sleepy", "blanket", "pillow"
        ],
        "Light Adventure": [
            "adventure", "journey", "explore", "discover", "travel", "quest",
            "find", "search", "treasure", "map", "secret", "hidden"
        ],
        "Silly & Playful": [
            "funny", "silly", "laugh", "joke", "giggle", "play", "fun",
            "crazy", "wacky", "hilarious", "comedy", "goofy"
        ],
        "Friendship": [
            "friend", "together", "share", "help", "kind", "love", "care",
            "hug", "buddy", "pal", "team", "family"
        ],
        "Learning & Curiosity": [
            "learn", "why", "how", "what", "curious", "wonder", "discover",
            "science", "nature", "question", "teach", "explore"
        ],
        "Surprise Me": []  # No specific keywords - this is a fallback
    }
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.1):
        """
        Initialize the category classifier agent.
        
        Args:
            model_name: OpenAI model to use for classification
            temperature: Temperature for LLM generation (low for consistent classification)
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
            max_tokens=100,
            openai_api_key=api_key
        )
        self.prompt_templates = PromptTemplates()
        
        logger.info(f"CategoryClassifierAgent initialized with model: {model_name}")
    
    def classify_story_idea(self, user_prompt: str) -> CategoryClassification:
        """
        Classify a user's story idea into one of the six categories.
        
        Args:
            user_prompt: The user's story idea input
            
        Returns:
            CategoryClassification object with category and confidence
        """
        logger.info(f"Classifying story idea: {user_prompt[:50]}...")
        
        try:
            # Get classification prompt
            classification_prompt = self.prompt_templates.get_category_classifier_prompt(user_prompt)
            
            # Call LLM for classification
            messages = [HumanMessage(content=classification_prompt)]
            response = self.llm.invoke(messages)
            
            # Extract category from response
            category_text = response.content.strip()
            logger.info(f"LLM classification response: {category_text}")
            
            # Parse and validate category
            category = self._parse_category(category_text)
            
            # Calculate confidence
            confidence = self._calculate_confidence(category, user_prompt)
            
            result = CategoryClassification(
                category=category,
                confidence=confidence
            )
            
            logger.info(f"Classification result: {category.value} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in story classification: {str(e)}")
            # Return Surprise Me as fallback with low confidence
            return CategoryClassification(
                category=StoryCategory.SURPRISE_ME,
                confidence=0.5
            )
    
    def _parse_category(self, category_text: str) -> StoryCategory:
        """
        Parse and validate the category from LLM response.
        
        Args:
            category_text: Raw category text from LLM
            
        Returns:
            StoryCategory enum value
        """
        # Direct match first
        try:
            return StoryCategory(category_text)
        except ValueError:
            pass
        
        # Case-insensitive and partial matching
        category_lower = category_text.lower().strip()
        
        category_mapping = {
            "bedtime calm": StoryCategory.BEDTIME_CALM,
            "bedtime": StoryCategory.BEDTIME_CALM,
            "calm": StoryCategory.BEDTIME_CALM,
            "peaceful": StoryCategory.BEDTIME_CALM,
            "light adventure": StoryCategory.LIGHT_ADVENTURE,
            "adventure": StoryCategory.LIGHT_ADVENTURE,
            "silly & playful": StoryCategory.SILLY_PLAYFUL,
            "silly and playful": StoryCategory.SILLY_PLAYFUL,
            "silly": StoryCategory.SILLY_PLAYFUL,
            "playful": StoryCategory.SILLY_PLAYFUL,
            "funny": StoryCategory.SILLY_PLAYFUL,
            "friendship": StoryCategory.FRIENDSHIP,
            "friend": StoryCategory.FRIENDSHIP,
            "learning & curiosity": StoryCategory.LEARNING_CURIOSITY,
            "learning and curiosity": StoryCategory.LEARNING_CURIOSITY,
            "learning": StoryCategory.LEARNING_CURIOSITY,
            "curiosity": StoryCategory.LEARNING_CURIOSITY,
            "educational": StoryCategory.LEARNING_CURIOSITY,
            "surprise me": StoryCategory.SURPRISE_ME,
            "surprise": StoryCategory.SURPRISE_ME
        }
        
        for key, category in category_mapping.items():
            if key in category_lower:
                return category
        
        # Default to Surprise Me if no match
        logger.warning(f"Could not parse category '{category_text}', defaulting to Surprise Me")
        return StoryCategory.SURPRISE_ME
    
    def _calculate_confidence(self, category: StoryCategory, user_prompt: str) -> float:
        """
        Calculate confidence score for the classification.
        
        Args:
            category: Classified category
            user_prompt: Original user prompt
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.75  # Base confidence
        
        # Check for keyword matches
        user_prompt_lower = user_prompt.lower()
        keywords = self.CATEGORY_KEYWORDS.get(category.value, [])
        
        matching_keywords = sum(1 for kw in keywords if kw in user_prompt_lower)
        
        if matching_keywords >= 3:
            confidence = min(confidence + 0.2, 0.98)
        elif matching_keywords >= 1:
            confidence = min(confidence + 0.1, 0.95)
        
        # Reduce confidence for Surprise Me (it's a fallback)
        if category == StoryCategory.SURPRISE_ME:
            confidence = max(confidence - 0.1, 0.6)
        
        return confidence
    
    def resolve_surprise_me(self, user_prompt: str) -> StoryCategory:
        """
        When category is 'Surprise Me', intelligently select the best actual category.
        
        Args:
            user_prompt: User's story idea
            
        Returns:
            Resolved StoryCategory (never Surprise Me)
        """
        user_prompt_lower = user_prompt.lower()
        
        # Score each category based on keyword matches
        scores = {}
        for category_name, keywords in self.CATEGORY_KEYWORDS.items():
            if category_name == "Surprise Me":
                continue
            scores[category_name] = sum(1 for kw in keywords if kw in user_prompt_lower)
        
        # Get highest scoring category, default to Bedtime Calm
        if max(scores.values()) > 0:
            best_category_name = max(scores, key=scores.get)
            return StoryCategory(best_category_name)
        
        # Default to Bedtime Calm for true surprises
        return StoryCategory.BEDTIME_CALM
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node function for category classification.
        
        Args:
            state: Current state dictionary containing user_prompt
            
        Returns:
            Updated state with classification result
        """
        user_prompt = state.get("user_prompt", "")
        
        if not user_prompt:
            raise ValueError("No user_prompt found in state")
        
        # Check if category was pre-selected by user
        preset_category = state.get("preset_category")
        if preset_category:
            try:
                category = StoryCategory(preset_category)
                
                # Resolve Surprise Me to actual category
                if category == StoryCategory.SURPRISE_ME:
                    category = self.resolve_surprise_me(user_prompt)
                    logger.info(f"Resolved 'Surprise Me' to: {category.value}")
                
                state["category"] = category.value
                state["category_confidence"] = 0.99  # User-selected
                
                logger.info(f"Using preset category: {category.value}")
                return state
                
            except ValueError:
                logger.warning(f"Invalid preset category: {preset_category}")
        
        # Perform automatic classification
        classification = self.classify_story_idea(user_prompt)
        
        # Resolve Surprise Me if classified as such
        category = classification.category
        if category == StoryCategory.SURPRISE_ME:
            category = self.resolve_surprise_me(user_prompt)
            logger.info(f"Resolved 'Surprise Me' to: {category.value}")
        
        # Update state
        state["category"] = category.value
        state["category_confidence"] = classification.confidence
        
        logger.info(f"Category classification completed: {category.value}")
        
        return state


def create_category_classifier(model_name: str = "gpt-3.5-turbo") -> CategoryClassifierAgent:
    """
    Factory function to create a CategoryClassifierAgent.
    
    Args:
        model_name: OpenAI model name to use
        
    Returns:
        Configured CategoryClassifierAgent instance
    """
    return CategoryClassifierAgent(model_name=model_name)
