"""
LangGraph Workflow for Dreamweaver Bedtime Stories.
Orchestrates the multi-agent pipeline with iterative evaluation, improvement, and regeneration.
"""

import logging
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from agents.classifier import create_category_classifier
from agents.storyteller import create_story_generator
from agents.story_critic import create_story_judge
from agents.story_improver import create_story_improver
from agents.gemini_image_generator import create_gemini_image_generator
from models.pydantic_models import (
    ChapteredStory, JudgeEvaluation, IterationResult,
    QualityIterationsPanel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StorytellerState(TypedDict):
    """State schema for the storyteller workflow."""
    # User input and settings
    user_prompt: str
    preset_category: Optional[str]
    age_range: str
    story_length: str
    
    # Classification
    category: str
    category_confidence: float
    
    # Story generation
    chaptered_story: Optional[ChapteredStory]
    story_text: str
    story_title: str
    
    # Evaluation and iteration
    judge_evaluation: Optional[JudgeEvaluation]
    story_passed: bool
    overall_score: float
    previous_score: Optional[float]
    judge_feedback: str
    
    # Iteration tracking
    current_iteration: int
    max_iterations: int
    iterations_history: List[IterationResult]
    generation_attempts: int
    
    # Image generation
    images: List[Any]
    images_generated: bool
    
    # Workflow control
    workflow_complete: bool
    error_message: str
    current_stage: str


class StorytellerWorkflow:
    """
    LangGraph workflow orchestrating the complete storytelling pipeline.
    Includes classification, generation, iterative evaluation/improvement, and image creation.
    """
    
    def __init__(
        self,
        classifier_model: str = "gpt-3.5-turbo",
        generator_model: str = "gpt-3.5-turbo",
        judge_model: str = "gpt-3.5-turbo",
        improver_model: str = "gpt-3.5-turbo",
        image_model: str = "gemini-2.5-flash-image",
        max_iterations: int = 3
    ):
        """
        Initialize the storyteller workflow.
        
        Args:
            classifier_model: Model for category classification
            generator_model: Model for story generation
            judge_model: Model for story evaluation
            improver_model: Model for story improvement
            image_model: Model for image generation (Gemini)
            max_iterations: Maximum improvement iterations
        """
        self.max_iterations = max_iterations
        
        # Initialize agents
        # Note: OpenAI models (gpt-3.5-turbo) used for text generation/evaluation
        # Gemini used ONLY for image generation
        self.classifier = create_category_classifier(classifier_model)
        self.generator = create_story_generator(generator_model)
        self.judge = create_story_judge(judge_model)
        self.improver = create_story_improver(improver_model)
        self.image_generator = create_gemini_image_generator(model=image_model)
        
        # Build workflow graph
        self.workflow = self._build_workflow()
        
        logger.info("StorytellerWorkflow initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow with nodes and edges.
        
        Returns:
            Compiled StateGraph workflow
        """
        workflow = StateGraph(StorytellerState)
        
        # Add nodes
        workflow.add_node("classify_category", self._classify_category_node)
        workflow.add_node("generate_story", self._generate_story_node)
        workflow.add_node("evaluate_story", self._evaluate_story_node)
        workflow.add_node("improve_story", self._improve_story_node)
        workflow.add_node("generate_images", self._generate_images_node)
        workflow.add_node("complete_workflow", self._complete_workflow_node)
        
        # Set entry point
        workflow.set_entry_point("classify_category")
        
        # Add edges
        workflow.add_edge("classify_category", "generate_story")
        
        # Check story generation success
        workflow.add_conditional_edges(
            "generate_story",
            self._check_story_generation_success,
            {
                "success": "evaluate_story",
                "failed": "complete_workflow"
            }
        )
        
        # Conditional edge after evaluation
        workflow.add_conditional_edges(
            "evaluate_story",
            self._should_improve_or_proceed,
            {
                "improve": "improve_story",
                "proceed": "generate_images"
            }
        )
        
        # After improvement, re-evaluate
        workflow.add_edge("improve_story", "evaluate_story")
        
        # After images, complete
        workflow.add_edge("generate_images", "complete_workflow")
        workflow.add_edge("complete_workflow", END)
        
        return workflow.compile()
    
    def _classify_category_node(self, state: StorytellerState) -> StorytellerState:
        """Node for story category classification."""
        logger.info("Stage: Classifying category")
        state["current_stage"] = "classifying"
        
        try:
            # Initialize state values
            state["current_iteration"] = 0
            state["max_iterations"] = self.max_iterations
            state["iterations_history"] = []
            state["workflow_complete"] = False
            state["error_message"] = ""
            state["previous_score"] = None
            state["generation_attempts"] = 0
            
            # Set defaults if not provided
            if "age_range" not in state or not state["age_range"]:
                state["age_range"] = "5-7"
            if "story_length" not in state or not state["story_length"]:
                state["story_length"] = "Short"
            
            # Classify category
            result_state = self.classifier(dict(state))
            state.update(result_state)
            
            logger.info(f"Category classified as: {state['category']}")
            
        except Exception as e:
            logger.error(f"Error in category classification: {str(e)}")
            state["error_message"] = f"Category classification failed: {str(e)}"
            state["category"] = "Bedtime Calm"
            state["category_confidence"] = 0.5
        
        return state
    
    def _generate_story_node(self, state: StorytellerState) -> StorytellerState:
        """Node for story generation."""
        attempt = state.get("generation_attempts", 0) + 1
        logger.info(f"Stage: Generating story (attempt {attempt})")
        state["current_stage"] = "generating"
        
        try:
            state["generation_attempts"] = attempt
            
            # Generate story
            result_state = self.generator(dict(state))
            state.update(result_state)
            
            logger.info(f"Story generated: '{state.get('story_title', 'Unknown')}'")
            
        except Exception as e:
            logger.error(f"Error in story generation: {str(e)}")
            state["error_message"] = f"Story generation failed: {str(e)}"
            state["chaptered_story"] = None
            state["story_text"] = ""
            state["workflow_complete"] = True
        
        return state
    
    def _evaluate_story_node(self, state: StorytellerState) -> StorytellerState:
        """Node for story evaluation."""
        iteration = state.get("current_iteration", 0) + 1
        logger.info(f"Stage: Evaluating story (iteration {iteration})")
        state["current_stage"] = "evaluating"
        
        try:
            # Evaluate story
            result_state = self.judge(dict(state))
            state.update(result_state)
            
            logger.info(
                f"Evaluation complete - Score: {state.get('overall_score', 0):.1f}, "
                f"Passed: {state.get('story_passed', False)}"
            )
            
        except Exception as e:
            logger.error(f"Error in story evaluation: {str(e)}")
            state["error_message"] = f"Story evaluation failed: {str(e)}"
            state["story_passed"] = False
            state["overall_score"] = 0.0
        
        return state
    
    def _improve_story_node(self, state: StorytellerState) -> StorytellerState:
        """Node for story improvement based on judge feedback."""
        iteration = state.get("current_iteration", 1)
        logger.info(f"Stage: Improving story (iteration {iteration})")
        state["current_stage"] = "improving"
        
        try:
            # Store previous score for delta
            state["previous_score"] = state.get("overall_score", 0)
            
            # Improve story
            result_state = self.improver(dict(state))
            state.update(result_state)
            
            logger.info("Story improvement completed")
            
        except Exception as e:
            logger.error(f"Error in story improvement: {str(e)}")
            # Continue with current story if improvement fails
            state["error_message"] = f"Story improvement failed: {str(e)}"
        
        return state
    
    def _generate_images_node(self, state: StorytellerState) -> StorytellerState:
        """Node for generating images for each chapter using Gemini."""
        logger.info("Stage: Generating images with Gemini")
        state["current_stage"] = "creating_images"
        
        try:
            chaptered_story = state.get("chaptered_story")
            if not chaptered_story or not chaptered_story.chapters:
                logger.warning("No chapters found for image generation")
                state["images"] = []
                state["images_generated"] = False
                return state
            
            # Get category for style matching
            category = state.get("category", "Bedtime Calm")
            
            images = []
            for i, chapter in enumerate(chaptered_story.chapters):
                logger.info(f"Generating image for chapter {i+1}: {chapter.chapter_title}")
                
                try:
                    image = self.image_generator.generate_image(
                        prompt=chapter.image_prompt,
                        section_title=chapter.chapter_title,
                        category=category
                    )
                    images.append(image)
                    
                except Exception as e:
                    logger.error(f"Error generating image for chapter {i+1}: {str(e)}")
                    images.append(None)
                
                # Small delay between Gemini requests
                if i < len(chaptered_story.chapters) - 1:
                    import time
                    time.sleep(0.5)
            
            state["images"] = images
            state["images_generated"] = True
            
            successful = len([img for img in images if img])
            logger.info(f"Image generation complete: {successful}/{len(images)} successful")
            
        except Exception as e:
            logger.error(f"Error in image generation node: {str(e)}")
            state["images"] = []
            state["images_generated"] = False
        
        return state
    
    def _complete_workflow_node(self, state: StorytellerState) -> StorytellerState:
        """Node for workflow completion."""
        logger.info("Stage: Completing workflow")
        state["current_stage"] = "complete"
        
        # Ensure images list exists
        if "images" not in state:
            state["images"] = []
        if "images_generated" not in state:
            state["images_generated"] = False
        
        state["workflow_complete"] = True
        
        # Create quality iterations panel data
        iterations_panel = QualityIterationsPanel(
            iterations=state.get("iterations_history", []),
            final_passed=state.get("story_passed", False),
            total_iterations=state.get("current_iteration", 1)
        )
        state["quality_panel"] = iterations_panel
        
        logger.info(
            f"Workflow completed - Final score: {state.get('overall_score', 0):.1f}, "
            f"Passed: {state.get('story_passed', False)}, "
            f"Iterations: {state.get('current_iteration', 1)}"
        )
        
        return state
    
    def _check_story_generation_success(self, state: StorytellerState) -> str:
        """Check if story generation was successful."""
        if state.get("error_message") or not state.get("chaptered_story"):
            logger.info("Story generation failed, skipping to completion")
            return "failed"
        
        logger.info("Story generation successful, proceeding to evaluation")
        return "success"
    
    def _should_improve_or_proceed(self, state: StorytellerState) -> str:
        """Determine if story should be improved or proceed to images."""
        story_passed = state.get("story_passed", False)
        current_iteration = state.get("current_iteration", 1)
        max_iterations = state.get("max_iterations", self.max_iterations)
        
        # If passed, proceed to images
        if story_passed:
            logger.info("Story passed evaluation, proceeding to image generation")
            return "proceed"
        
        # If max iterations reached, proceed anyway
        if current_iteration >= max_iterations:
            logger.info(f"Max iterations ({max_iterations}) reached, proceeding with current story")
            return "proceed"
        
        # Otherwise, improve
        logger.info(f"Story needs improvement (iteration {current_iteration}/{max_iterations})")
        return "improve"
    
    def run(
        self,
        user_prompt: str,
        age_range: str = "5-7",
        story_length: str = "Short",
        preset_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run the complete storytelling workflow.
        
        Args:
            user_prompt: User's story idea
            age_range: Target age range ("5-7" or "7-10")
            story_length: Story length ("Short" = 5 chapters, "Long" = 7 chapters)
            preset_category: Optional pre-selected category
            
        Returns:
            Final state dictionary with story, images, and metadata
        """
        logger.info(f"Starting storytelling workflow for: {user_prompt[:50]}...")
        
        # Initialize state
        initial_state = StorytellerState(
            user_prompt=user_prompt,
            preset_category=preset_category,
            age_range=age_range,
            story_length=story_length,
            category="",
            category_confidence=0.0,
            chaptered_story=None,
            story_text="",
            story_title="",
            judge_evaluation=None,
            story_passed=False,
            overall_score=0.0,
            previous_score=None,
            judge_feedback="",
            current_iteration=0,
            max_iterations=self.max_iterations,
            iterations_history=[],
            generation_attempts=0,
            images=[],
            images_generated=False,
            workflow_complete=False,
            error_message="",
            current_stage="starting"
        )
        
        try:
            # Run workflow
            final_state = self.workflow.invoke(initial_state)
            
            logger.info("Storytelling workflow completed successfully")
            return dict(final_state)
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            initial_state["error_message"] = f"Workflow failed: {str(e)}"
            initial_state["workflow_complete"] = True
            return dict(initial_state)
    
    def cleanup(self):
        """Clean up resources used by the workflow."""
        try:
            if hasattr(self.image_generator, 'cleanup'):
                self.image_generator.cleanup()
            logger.info("Workflow resources cleaned up")
        except Exception as e:
            logger.warning(f"Error during workflow cleanup: {str(e)}")


def create_storyteller_workflow(
    classifier_model: str = "gpt-3.5-turbo",
    generator_model: str = "gpt-3.5-turbo",
    judge_model: str = "gpt-3.5-turbo",
    image_model: str = "gemini-2.5-flash-image",
    max_attempts: int = 3
) -> StorytellerWorkflow:
    """
    Factory function to create a StorytellerWorkflow.
    
    Args:
        classifier_model: Model for category classification
        generator_model: Model for story generation
        judge_model: Model for story evaluation
        image_model: Model for image generation (Gemini)
        max_attempts: Maximum generation/improvement attempts
        
    Returns:
        Configured StorytellerWorkflow instance
    """
    return StorytellerWorkflow(
        classifier_model=classifier_model,
        generator_model=generator_model,
        judge_model=judge_model,
        improver_model=generator_model,  # Use same model for improvement
        image_model=image_model,
        max_iterations=max_attempts
    )
