"""
Idea Generator Agent for Dreamweaver Bedtime Stories.
Generates creative story ideas based on categories using LLM.
"""

import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from prompts.prompts import PromptTemplates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IdeaGeneratorAgent:
    """
    Agent responsible for generating creative story ideas based on categories.
    Uses OpenAI LLM to create fresh, engaging story concepts for children.
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.8):
        """
        Initialize the idea generator agent.
        
        Args:
            model_name: OpenAI model to use for idea generation
            temperature: Higher temperature for more creative ideas
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
            max_tokens=200,
            openai_api_key=api_key
        )
        self.prompt_templates = PromptTemplates()
        
        logger.info(f"IdeaGeneratorAgent initialized with model: {model_name}")
    
    def generate_idea(self, category: str, age_range: str = "5-7") -> str:
        """
        Generate a creative story idea for the specified category.
        
        Args:
            category: Story category (Bedtime Calm, Light Adventure, etc.)
            age_range: Target age range ("5-7" or "7-10")
            
        Returns:
            Generated story idea as a string
        """
        logger.info(f"Generating {category} story idea for ages {age_range}")
        
        try:
            # Get the prompt from templates
            prompt = self.prompt_templates.get_idea_generation_prompt(category, age_range)
            messages = [HumanMessage(content=prompt)]
            response = self.llm.invoke(messages)
            
            idea = response.content.strip()
            logger.info(f"Generated {category} idea: {idea[:50]}...")
            
            return idea
            
        except Exception as e:
            logger.error(f"Error generating {category} idea: {str(e)}")
            return self._get_fallback_idea(category)
    
    def _get_fallback_idea(self, category: str) -> str:
        """
        Get a fallback idea if generation fails.
        
        Args:
            category: Story category
            
        Returns:
            Fallback story idea
        """
        fallback_ideas = {
            "Bedtime Calm": "A sleepy little cloud drifts across the moonlit sky, gathering starlight to share with dreaming children.",
            "Light Adventure": "A curious bunny discovers a hidden garden where flowers glow softly in the evening light.",
            "Silly & Playful": "A penguin who thinks it can fly tries increasingly creative (and hilarious) methods to soar.",
            "Friendship": "Two unlikely friends - a shy mouse and a gentle owl - learn to understand each other's worlds.",
            "Learning & Curiosity": "A young owl asks why the moon changes shape, and discovers the wonder of lunar phases.",
            "Surprise Me": "A magical paintbrush that brings bedtime drawings to life leads to unexpected cozy adventures."
        }
        
        return fallback_ideas.get(category, fallback_ideas["Surprise Me"])


def create_idea_generator(model_name: str = "gpt-3.5-turbo") -> IdeaGeneratorAgent:
    """
    Factory function to create an IdeaGeneratorAgent.
    
    Args:
        model_name: OpenAI model name to use
        
    Returns:
        Configured IdeaGeneratorAgent instance
    """
    return IdeaGeneratorAgent(model_name=model_name)
