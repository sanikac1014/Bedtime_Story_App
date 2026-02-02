"""
Story Judge Agent for Dreamweaver Bedtime Stories.
Evaluates stories with detailed 1-10 scoring across 5 criteria.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from models.pydantic_models import (
    JudgeScores, JudgeCriterionScore, JudgeEvaluation, 
    ImprovementSuggestion, IterationResult
)
from prompts.prompts import PromptTemplates

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StoryJudgeAgent:
    """
    Agent responsible for evaluating story quality with detailed 1-10 scoring.
    Uses 5 criteria: age-appropriate language, emotional safety, engagement,
    coherence, and bedtime suitability.
    """
    
    # Pass thresholds
    OVERALL_THRESHOLD = 8.0
    SAFETY_THRESHOLD = 9
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", temperature: float = 0.1):
        """
        Initialize the story judge agent.
        
        Args:
            model_name: OpenAI model to use for evaluation
            temperature: Low temperature for consistent evaluation
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
            max_tokens=1500,
            openai_api_key=api_key
        )
        self.prompt_templates = PromptTemplates()
        self.max_retries = 2
        
        logger.info(f"StoryJudgeAgent initialized with model: {model_name}")
    
    def evaluate_story(
        self,
        story_text: str,
        title: str = "Story",
        age_range: str = "5-7",
        category: str = "Bedtime Calm"
    ) -> JudgeEvaluation:
        """
        Evaluate a story with detailed 1-10 scoring.
        
        Args:
            story_text: Complete story text to evaluate
            title: Story title
            age_range: Target age range
            category: Story category
            
        Returns:
            JudgeEvaluation with scores and suggestions
        """
        logger.info(f"Evaluating story '{title}' for ages {age_range}")
        
        # Get evaluation prompt
        evaluation_prompt = self.prompt_templates.get_judge_evaluation_prompt(
            title=title,
            age_range=age_range,
            category=category,
            story_text=story_text
        )
        
        for attempt in range(self.max_retries):
            try:
                messages = [HumanMessage(content=evaluation_prompt)]
                response = self.llm.invoke(messages)
                
                # Parse evaluation
                evaluation = self._parse_judge_evaluation(response.content)
                
                logger.info(
                    f"Evaluation completed - Overall: {evaluation.overall_score:.1f}, "
                    f"Safety: {evaluation.scores.emotional_safety.score}, "
                    f"Passed: {evaluation.passed}"
                )
                
                return evaluation
                
            except Exception as e:
                logger.warning(f"Evaluation attempt {attempt + 1} failed: {str(e)}")
                if attempt == self.max_retries - 1:
                    logger.error("All evaluation attempts failed, returning default")
                    return self._create_default_evaluation()
        
        return self._create_default_evaluation()
    
    def _parse_judge_evaluation(self, response_content: str) -> JudgeEvaluation:
        """
        Parse LLM response into JudgeEvaluation.
        Includes robust JSON extraction with retry logic.
        
        Args:
            response_content: Raw LLM response
            
        Returns:
            Parsed JudgeEvaluation
        """
        try:
            # Robust JSON extraction
            json_content = self._extract_json(response_content)
            eval_data = json.loads(json_content)
            
            # Parse scores
            scores_data = eval_data.get("scores", {})
            
            scores = JudgeScores(
                age_appropriate_language=JudgeCriterionScore(
                    score=self._safe_score(scores_data.get("age_appropriate_language", {}).get("score", 7)),
                    reasoning=scores_data.get("age_appropriate_language", {}).get("reasoning", "")
                ),
                emotional_safety=JudgeCriterionScore(
                    score=self._safe_score(scores_data.get("emotional_safety", {}).get("score", 9)),
                    reasoning=scores_data.get("emotional_safety", {}).get("reasoning", "")
                ),
                engagement=JudgeCriterionScore(
                    score=self._safe_score(scores_data.get("engagement", {}).get("score", 7)),
                    reasoning=scores_data.get("engagement", {}).get("reasoning", "")
                ),
                coherence=JudgeCriterionScore(
                    score=self._safe_score(scores_data.get("coherence", {}).get("score", 7)),
                    reasoning=scores_data.get("coherence", {}).get("reasoning", "")
                ),
                bedtime_suitability=JudgeCriterionScore(
                    score=self._safe_score(scores_data.get("bedtime_suitability", {}).get("score", 7)),
                    reasoning=scores_data.get("bedtime_suitability", {}).get("reasoning", "")
                )
            )
            
            # Parse improvement suggestions
            suggestions = []
            for i, sugg_data in enumerate(eval_data.get("improvement_suggestions", [])[:3]):
                suggestions.append(ImprovementSuggestion(
                    criterion=sugg_data.get("criterion", "General"),
                    suggestion=sugg_data.get("suggestion", "Improve story quality"),
                    priority=sugg_data.get("priority", i + 1)
                ))
            
            # Ensure we have 3 suggestions
            while len(suggestions) < 3:
                suggestions.append(ImprovementSuggestion(
                    criterion="General",
                    suggestion="Consider enhancing overall story quality",
                    priority=len(suggestions) + 1
                ))
            
            # Calculate overall score and pass status
            overall_score = scores.overall_score
            passed = JudgeEvaluation.calculate_pass(scores)
            pass_reasoning = eval_data.get("pass_reasoning", 
                f"Overall score: {overall_score:.1f}, Safety score: {scores.emotional_safety.score}")
            
            return JudgeEvaluation(
                scores=scores,
                overall_score=overall_score,
                improvement_suggestions=suggestions,
                passed=passed,
                pass_reasoning=pass_reasoning
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error in evaluation: {str(e)}")
            raise ValueError(f"Invalid JSON in evaluation response: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing evaluation: {str(e)}")
            raise
    
    def _safe_score(self, score: Any) -> int:
        """Safely convert score to int within valid range."""
        try:
            s = int(score)
            return max(1, min(10, s))
        except (ValueError, TypeError):
            return 7  # Default middle score
    
    def _create_default_evaluation(self) -> JudgeEvaluation:
        """Create a default evaluation when parsing fails."""
        default_score = JudgeCriterionScore(score=7, reasoning="Default score due to evaluation error")
        
        scores = JudgeScores(
            age_appropriate_language=default_score,
            emotional_safety=JudgeCriterionScore(score=8, reasoning="Assumed safe"),
            engagement=default_score,
            coherence=default_score,
            bedtime_suitability=default_score
        )
        
        return JudgeEvaluation(
            scores=scores,
            overall_score=scores.overall_score,
            improvement_suggestions=[
                ImprovementSuggestion(criterion="General", suggestion="Review story for improvements", priority=1),
                ImprovementSuggestion(criterion="Engagement", suggestion="Add more engaging elements", priority=2),
                ImprovementSuggestion(criterion="Language", suggestion="Ensure age-appropriate vocabulary", priority=3)
            ],
            passed=False,
            pass_reasoning="Default evaluation - manual review recommended"
        )
    
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
            raise ValueError("No JSON found in evaluation response")
        
        return content[start_idx:end_idx]
    
    def create_iteration_result(
        self,
        evaluation: JudgeEvaluation,
        iteration_number: int,
        previous_score: Optional[float] = None
    ) -> IterationResult:
        """
        Create an IterationResult from a JudgeEvaluation.
        
        Args:
            evaluation: The judge evaluation
            iteration_number: Which iteration this is
            previous_score: Previous iteration's score for delta
            
        Returns:
            IterationResult for UI display
        """
        score_delta = None
        if previous_score is not None:
            score_delta = evaluation.overall_score - previous_score
        
        suggestions = [s.suggestion for s in evaluation.improvement_suggestions[:3]]
        
        return IterationResult(
            iteration_number=iteration_number,
            overall_score=evaluation.overall_score,
            score_delta=score_delta,
            passed=evaluation.passed,
            suggestions=suggestions
        )
    
    def format_evaluation_summary(self, evaluation: JudgeEvaluation) -> str:
        """
        Create a human-readable summary of the evaluation.
        
        Args:
            evaluation: JudgeEvaluation to summarize
            
        Returns:
            Formatted summary string
        """
        scores = evaluation.scores
        lines = [
            "📊 Story Quality Evaluation",
            "=" * 30,
            f"Age-Appropriate Language: {scores.age_appropriate_language.score}/10",
            f"Emotional Safety: {scores.emotional_safety.score}/10",
            f"Engagement: {scores.engagement.score}/10",
            f"Coherence: {scores.coherence.score}/10",
            f"Bedtime Suitability: {scores.bedtime_suitability.score}/10",
            "-" * 30,
            f"Overall Score: {evaluation.overall_score:.1f}/10",
            f"Status: {'✅ PASSED' if evaluation.passed else '🔄 NEEDS IMPROVEMENT'}",
        ]
        
        if not evaluation.passed:
            lines.extend([
                "",
                "Suggestions for Improvement:",
            ])
            for sugg in evaluation.improvement_suggestions:
                lines.append(f"  {sugg.priority}. [{sugg.criterion}] {sugg.suggestion}")
        
        return "\n".join(lines)
    
    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        LangGraph node function for story evaluation.
        
        Args:
            state: Current state dictionary
            
        Returns:
            Updated state with evaluation results
        """
        story_text = state.get("story_text", "")
        title = state.get("story_title", "Story")
        age_range = state.get("age_range", "5-7")
        category = state.get("category", "Bedtime Calm")
        
        if not story_text:
            raise ValueError("No story_text found in state for evaluation")
        
        # Get previous score for delta calculation
        previous_score = state.get("previous_score")
        
        # Evaluate story
        evaluation = self.evaluate_story(
            story_text=story_text,
            title=title,
            age_range=age_range,
            category=category
        )
        
        # Track iteration
        current_iteration = state.get("current_iteration", 0) + 1
        
        # Create iteration result
        iteration_result = self.create_iteration_result(
            evaluation=evaluation,
            iteration_number=current_iteration,
            previous_score=previous_score
        )
        
        # Update iteration history
        iterations_history = state.get("iterations_history", [])
        iterations_history.append(iteration_result)
        
        # Update state
        state["judge_evaluation"] = evaluation
        state["story_passed"] = evaluation.passed
        state["overall_score"] = evaluation.overall_score
        state["previous_score"] = evaluation.overall_score  # For next iteration
        state["current_iteration"] = current_iteration
        state["iterations_history"] = iterations_history
        state["judge_feedback"] = self._format_feedback_for_improver(evaluation)
        
        logger.info(
            f"Evaluation completed - Iteration {current_iteration}, "
            f"Score: {evaluation.overall_score:.1f}, Passed: {evaluation.passed}"
        )
        
        return state
    
    def _format_feedback_for_improver(self, evaluation: JudgeEvaluation) -> str:
        """
        Format evaluation feedback for the improver agent.
        Uses structured format matching the new prompt style.
        """
        lines = []
        
        # Add summary if not passed
        if not evaluation.passed:
            lines.append(f"SUMMARY: {evaluation.pass_reasoning}")
            lines.append("\nSPECIFIC IMPROVEMENTS NEEDED:")
        
        # Add low-scoring criteria details
        scores = evaluation.scores
        if scores.emotional_safety.score < 9:
            lines.append(f"- [CRITICAL - Emotional Safety] (Score: {scores.emotional_safety.score}/10): {scores.emotional_safety.reasoning}")
        if scores.age_appropriate_language.score < 8:
            lines.append(f"- [Age-Appropriate Language] (Score: {scores.age_appropriate_language.score}/10): {scores.age_appropriate_language.reasoning}")
        if scores.bedtime_suitability.score < 8:
            lines.append(f"- [Bedtime Suitability] (Score: {scores.bedtime_suitability.score}/10): {scores.bedtime_suitability.reasoning}")
        if scores.engagement.score < 8:
            lines.append(f"- [Engagement] (Score: {scores.engagement.score}/10): {scores.engagement.reasoning}")
        if scores.coherence.score < 8:
            lines.append(f"- [Coherence] (Score: {scores.coherence.score}/10): {scores.coherence.reasoning}")
        
        # Add improvement suggestions
        if evaluation.improvement_suggestions:
            lines.append("\nACTIONABLE SUGGESTIONS:")
            for sugg in evaluation.improvement_suggestions:
                lines.append(f"- [Priority {sugg.priority}] {sugg.criterion}: {sugg.suggestion}")
        
        return "\n".join(lines)


def create_story_judge(model_name: str = "gpt-3.5-turbo") -> StoryJudgeAgent:
    """
    Factory function to create a StoryJudgeAgent.
    
    Args:
        model_name: OpenAI model name to use
        
    Returns:
        Configured StoryJudgeAgent instance
    """
    return StoryJudgeAgent(model_name=model_name)
