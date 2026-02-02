"""
Structured prompt templates for Dreamweaver Bedtime Stories application.
Contains all prompts used by different agents in the pipeline.

PROMPT STYLE PRINCIPLES:
- Clear ROLE definition at the start of each prompt
- Explicit TASK description with context
- Detailed REQUIREMENTS with named rules (VOCABULARY RULE, etc.)
- Specific good/bad examples where helpful
- Structured OUTPUT FORMAT with strict JSON schemas
- Pass/Fail criteria for evaluation prompts
- Feedback integration sections for iterative improvement
"""

from typing import Dict, List, Optional
import json


class PromptTemplates:
    """Collection of structured prompt templates for all agents."""
    
    # =========================================================================
    # CATEGORY CLASSIFICATION
    # =========================================================================
    
    CATEGORY_CLASSIFIER_PROMPT = """
ROLE: You are a precise classifier for children's bedtime story ideas (ages 5-10).

TASK:
Given a short story idea, classify it into exactly ONE category from the list below.

CATEGORIES:
- Bedtime Calm: Focus on peaceful nighttime imagery, sleep, cozy moments, stars, moonlight, gentle quietness.
- Light Adventure: Focus on gentle exploration, discovery, journeys without danger, finding new places or friendly creatures.
- Silly & Playful: Focus on humor, silliness, funny mix-ups, playful absurdity that makes children giggle.
- Friendship: Focus on bonds between friends/family, kindness, sharing, helping each other, emotional warmth.
- Learning & Curiosity: Focus on discovering something new, nature, science, gentle life lessons learned through story.
- Surprise Me: If the idea blends multiple categories or doesn't clearly fit one, use this for creative freedom.

CLASSIFICATION RULES:
- Choose the category that best represents the PRIMARY focus or main appeal of the story.
- If multiple categories seem to fit, pick the one that dominates the idea.
- Do NOT invent new categories.

INPUT:
Story Idea: "{user_prompt}"

OUTPUT FORMAT:
Return ONLY the category name, exactly as one of:
Bedtime Calm
Light Adventure
Silly & Playful
Friendship
Learning & Curiosity
Surprise Me

(No extra words, punctuation, or explanations.)
"""

    # =========================================================================
    # AGE-SPECIFIC STYLE GUIDELINES
    # =========================================================================
    
    AGE_STYLE_GUIDELINES = {
        "5-7": """
AGE BAND: 5-7 Years (Early Readers)

VOCABULARY RULE:
- Use only simple, everyday words that a 5-year-old knows.
- AVOID: complex words like "embarked," "retrieved," "magnificent," "extraordinary"
- INSTEAD USE: "went," "got," "big," "special"
- Example BAD: "The luminescent fireflies danced ethereally."
- Example GOOD: "The little fireflies glowed softly in the dark."

SENTENCE RULE:
- Keep sentences short and clear (5-10 words each).
- Use simple sentence structures (subject-verb-object).
- Include gentle repetition for comfort and rhythm.

PACING RULE:
- Slow, soothing pace throughout.
- Linger on cozy details (soft blankets, warm hugs, quiet sounds).
- Problems should be small and resolved quickly within sentences.

EMOTIONAL RULE:
- All emotions should be simple and positive (happy, cozy, safe, loved).
- Characters are clearly good and friendly.
- Every chapter ends with reassurance.
""",
        "7-10": """
AGE BAND: 7-10 Years (Confident Readers)

VOCABULARY RULE:
- Use moderately rich vocabulary that challenges slightly but remains accessible.
- Can include descriptive words but explain through context.
- AVOID: overly literary words like "luminescent," "melancholy," "treacherous"
- ALLOWED: "curious," "adventure," "discovered," "magnificent" (with context)

SENTENCE RULE:
- Sentences can be longer (up to 15-18 words) with varied rhythm.
- Can use compound sentences with "and," "but," "because."
- Still maintain clarity - one main idea per sentence.

PACING RULE:
- Can have slightly more buildup and complexity.
- Mild challenges that resolve positively.
- Still wind down toward calm by chapter end.

EMOTIONAL RULE:
- Characters can have simple motivations and feelings.
- Can include gentle humor and wordplay.
- Conflicts are still gentle and quickly resolved.
- Ending must be satisfying, peaceful, and bedtime-appropriate.
"""
    }

    # =========================================================================
    # CATEGORY-SPECIFIC TONE GUIDELINES
    # =========================================================================
    
    CATEGORY_GUIDELINES = {
        "Bedtime Calm": """
CATEGORY: Bedtime Calm 🌙

TONE: Dreamy, peaceful, soothing.

REQUIRED ELEMENTS:
- Nighttime imagery: stars, moon, soft darkness, quiet night sounds
- Cozy sensations: warm blankets, soft pillows, gentle breezes
- Slow pacing that encourages sleepiness
- Minimal to no conflict or tension
- Characters preparing for or enjoying sleep

STORY ARC:
- Begin with a quiet, peaceful setting
- Middle shows gentle activity winding down
- End with characters settling into cozy sleep

ABSOLUTELY AVOID: excitement, surprises, any stimulating content
""",
        "Light Adventure": """
CATEGORY: Light Adventure 🧭

TONE: Curious, wonder-filled, gently exciting.

REQUIRED ELEMENTS:
- Exploration: characters discover new places, hidden paths, friendly creatures
- Problem-solving: simple puzzles or challenges overcome easily
- Sense of wonder without fear or danger
- Safe return home by story end

STORY ARC:
- Begin with characters in their safe, normal world
- Middle shows discovery and gentle challenges
- End with successful return, feeling satisfied and ready for rest

ABSOLUTELY AVOID: real danger, scary obstacles, violence, intense fear
""",
        "Silly & Playful": """
CATEGORY: Silly & Playful 😄

TONE: Humorous, lighthearted, giggly.

REQUIRED ELEMENTS:
- Physical comedy described clearly (things falling, mixing up, bouncing)
- Funny sounds and silly situations
- Playful characters who laugh easily
- Absurd but harmless scenarios

COMEDY RULE:
- BAD: "The clumsy bear made everyone laugh."
- GOOD: "The bear stepped on the banana peel and slid across the floor, bumping into a stack of pillows that went POOF everywhere!"

ABSOLUTELY AVOID: mean-spirited humor, embarrassment, bullying, scary surprises
""",
        "Friendship": """
CATEGORY: Friendship ❤️

TONE: Warm, heartfelt, emotionally cozy.

REQUIRED ELEMENTS:
- Central relationship between friends or family members
- Acts of kindness, sharing, or helping
- Small misunderstandings resolved through communication
- Emphasis on how good it feels to be connected

EMOTION RULE:
- Show emotions through physical actions and dialogue
- BAD: "She felt happy about her friend."
- GOOD: "She smiled so big her cheeks hurt, and gave her friend the biggest hug."

ABSOLUTELY AVOID: lasting conflicts, characters being mean, unresolved tension
""",
        "Learning & Curiosity": """
CATEGORY: Learning & Curiosity 🔍

TONE: Wonder-filled, gently educational, satisfying.

REQUIRED ELEMENTS:
- A question or mystery the character wants to understand
- Discovery through exploration (not lecturing)
- Simple explanation woven naturally into story
- Character feels wiser and satisfied at the end

TEACHING RULE:
- Learning happens through the character's experience, not exposition
- BAD: "The wise owl explained that the moon reflects sunlight."
- GOOD: "Luna watched the moon get bigger each night. 'It's not growing,' said Grandma. 'We just see more of its sunny side!'"

ABSOLUTELY AVOID: preachy tone, lecturing, boring explanations
""",
        "Surprise Me": """
CATEGORY: Surprise Me 🎲

TONE: Creative, whimsical, flexibly magical.

REQUIRED ELEMENTS:
- Blend elements from multiple categories creatively
- Choose the tone that best fits the user's specific prompt
- Maintain bedtime-appropriate guidelines regardless of content
- Can be unexpected and imaginative

CREATIVE RULE:
- Prioritize what feels most magical and engaging for the child
- Story can have adventure, friendship, learning, or humor blended
- MUST still end peacefully and be appropriate for bedtime

ABSOLUTELY AVOID: anything that would disqualify the story for bedtime
"""
    }

    # =========================================================================
    # CHAPTER STRUCTURE TEMPLATES (by story length)
    # =========================================================================
    
    CHAPTER_STRUCTURE_3 = """
CHAPTER STRUCTURE (3 Chapters - Short Story):
Follow this narrative arc exactly:

- CHAPTER 1 - THE BEGINNING:
  Introduce the main character(s) and their cozy world. Describe the setting in vivid detail - where they live, what they're doing, how they feel. Establish a warm, inviting atmosphere. Show the character's personality through their actions, thoughts, and dialogue. End with something that sparks curiosity or sets up the story.

- CHAPTER 2 - THE HEART:
  The main gentle event, discovery, or adventure happens here. This is the core of your story. Show the character exploring, learning, or experiencing something special. Include rich sensory details and meaningful dialogue. Build warmth and wonder. Any small challenge should be resolved with kindness.

- CHAPTER 3 - THE PEACEFUL END:
  Wind down completely. Resolve any remaining threads with warmth. Show the character returning home, feeling content, or settling down. Include cozy, sleepy imagery - soft blankets, twinkling stars, gentle yawns. End with the character feeling safe, loved, and ready for sleep.
"""

    CHAPTER_STRUCTURE_5 = """
CHAPTER STRUCTURE (5 Chapters - Medium Story):
Follow this narrative arc exactly:

- CHAPTER 1 - ONCE UPON A TIME:
  Introduce the main character(s) in their normal, cozy world. Describe who they are, where they live, and what makes them special. Show their daily life and personality through actions and dialogue. Establish a warm, safe atmosphere before the adventure begins.

- CHAPTER 2 - SOMETHING NEW:
  Something sparks the character's curiosity - a discovery, an invitation, or a gentle call to adventure. Show their excitement and wonder. Describe what they find or learn. Include sensory details that make the discovery feel magical. The character decides to explore further.

- CHAPTER 3 - THE JOURNEY:
  The heart of the story unfolds. The character is fully engaged in their adventure, activity, or experience. This is where the main action happens. Include rich descriptions of new places, friendly characters they meet, or things they learn. Build the emotional core of the story.

- CHAPTER 4 - ALMOST THERE:
  The gentle climax - any small challenge or question is resolved. Show the character succeeding, understanding, or finding what they were looking for. Warm feelings of accomplishment, friendship, or wonder. Begin to slow the pace slightly.

- CHAPTER 5 - HAPPILY TO SLEEP:
  Full wind-down. The character returns home or settles into a cozy spot. Reflect on the wonderful experience. Include sleepy, peaceful imagery - moonlight, soft sounds, warm feelings. End with the character feeling content, safe, and drifting toward sleep.
"""

    CHAPTER_STRUCTURE_7 = """
CHAPTER STRUCTURE (7 Chapters - Long Story):
Follow this narrative arc exactly:

- CHAPTER 1 - THE BEGINNING:
  Introduce the main character(s) in their cozy, familiar world. Take time to establish who they are, their personality, their home, and the people/creatures they love. Create a vivid picture of their normal life before the adventure.

- CHAPTER 2 - A CURIOUS DISCOVERY:
  Something new catches the character's attention - a mysterious sound, a hidden path, a new friend, or an interesting object. Show their curiosity awakening. Describe their first investigation or reaction. Plant the seeds of the adventure.

- CHAPTER 3 - SETTING OFF:
  The character decides to explore further or embark on a gentle journey. Describe them preparing, saying goodbye, or taking their first steps into something new. Build anticipation and excitement while keeping the tone warm.

- CHAPTER 4 - THE HEART OF THE STORY:
  The main adventure or activity unfolds in full. This is the richest chapter - describe new places, characters, or experiences in detail. Show the character fully engaged, learning, playing, or exploring. Include meaningful interactions and sensory details.

- CHAPTER 5 - A LITTLE CHALLENGE:
  A small, gentle obstacle appears - nothing scary, just something to figure out. Show the character thinking, trying, or asking for help. Resolve it through kindness, cleverness, or friendship. This builds character without creating fear.

- CHAPTER 6 - WARM RESOLUTION:
  Everything comes together beautifully. The character achieves their goal, makes a new friend, or understands something important. Show celebration, gratitude, or quiet satisfaction. Begin transitioning toward calm.

- CHAPTER 7 - TIME FOR SLEEP:
  The gentlest chapter. The character returns home or finds a cozy resting place. Reflect on the wonderful adventure. Describe settling in - soft beds, warm blankets, twinkling stars, loving goodnight wishes. End with peaceful, sleepy imagery that helps the listener drift off to sleep.
"""

    # =========================================================================
    # STORY GENERATION PROMPT
    # =========================================================================
    
    CHAPTERED_STORY_PROMPT = """
ROLE: You are an expert children's bedtime story writer, specializing in age-appropriate, engaging, and calming stories that help children drift off to sleep.

TASK:
Create a complete {chapter_count}-chapter bedtime story based on the user's idea.
You must return ONLY a valid JSON object with no extra text.

INPUT DATA:
- User's Story Idea: "{user_prompt}"
- Target Age: {age_range} years
- Category: {category}
- Chapter Count: {chapter_count}

{age_guidelines}

{category_guidelines}

CRITICAL SAFETY REQUIREMENTS:
1. CONTENT SAFETY: Absolutely NO violence, scary threats, monsters, danger, gore, or distressing content.
2. EMOTIONAL SAFETY: All content must be warm, reassuring, and appropriate for a child to hear before sleep.
3. BEDTIME ARC: The story MUST wind down. Final chapter must be peaceful, calm, and sleep-inducing.
4. CHARACTER CONSISTENCY: Characters must remain consistent in name, description, and personality throughout.

NARRATIVE COHERENCE REQUIREMENT (CRITICAL):
- Every major event must have a clear reason that is explained in the story.
- Characters must have understandable motivations for their actions.
- Each chapter must answer:
  1) What changed from the previous chapter?
  2) Why did it change?
  3) How does the main character feel about this change?
- Do NOT introduce events without setup or explanation.

{chapter_structure_guide}

LENGTH REQUIREMENT (CRITICAL - DO NOT WRITE SHORT CHAPTERS):
- Each chapter must be {min_words_per_chapter} words minimum. Write FULL paragraphs, not brief summaries.
- Include 3-5 paragraphs per chapter with smooth transitions between them.
- Use rich sensory descriptions: describe exactly what characters see, hear, feel, smell, and touch.
- Include meaningful dialogue (at least 2-3 exchanges per chapter) that reveals character personality.
- Show internal thoughts and feelings: "Luna felt her heart flutter with excitement" not just "Luna was excited."
- Describe actions in detail: "She carefully lifted the shimmering acorn, its golden surface warm against her tiny paws" not just "She picked it up."
- Create atmosphere: weather, lighting, ambient sounds, the feel of the environment.

{improvement_instructions}

OUTPUT FORMAT:
Return ONLY valid JSON matching this exact schema. No text before or after.

{{
    "title": "Creative Story Title",
    "characters": [
        {{"name": "Character Name", "description": "One-line description"}},
        {{"name": "Second Character", "description": "One-line description"}}
    ],
    "chapters": [
        {{
            "chapter_number": 1,
            "chapter_title": "Creative Chapter Title",
            "chapter_text": "Full chapter content with multiple paragraphs ({min_words_per_chapter}+ words). Include rich descriptions, dialogue, and sensory details. Write complete scenes, not summaries.",
            "chapter_summary": "One-sentence summary of this chapter.",
            "image_prompt": "Children's book illustration: [specific visual scene from this chapter]"
        }}
    ],
    "moral_or_theme": "Optional gentle lesson or theme (or null)"
}}

VALIDATION:
- Ensure JSON is strictly valid
- All {chapter_count} chapters must be included
- Each chapter_text MUST be at least {min_words_per_chapter} words with 3-5 paragraphs
- Include dialogue and sensory details in EVERY chapter
- Character names must be consistent across all chapters
"""

    # =========================================================================
    # JUDGE EVALUATION PROMPT
    # =========================================================================
    
    JUDGE_EVALUATION_PROMPT = """
ROLE: You are a Lead Quality Evaluator for children's bedtime stories. Your job is to strictly evaluate story drafts against specific quality standards.

TASK:
Evaluate the provided story against 5 metrics. Score each metric 1-10.
Return ONLY a valid JSON evaluation. No extra text.

INPUT DATA:
- Story Title: "{title}"
- Target Age: {age_range} years
- Category: {category}

STORY CONTENT:
{story_text}

---

EVALUATION METRICS:

METRIC 1: Age-Appropriate Language
- REQUIREMENT: Vocabulary and sentence complexity must match the target age.
- SCORING:
  - 1-3: Many words too complex, sentences too long
  - 4-6: Some complex words, mostly appropriate
  - 7-9: Vocabulary well-matched to age
  - 10: Perfect vocabulary and sentence length for age
- FAIL CONDITION: Score below 6 if vocabulary is consistently too advanced.

METRIC 2: Emotional Safety (CRITICAL)
- REQUIREMENT: Content must be 100% safe. NO violence, scary content, danger, death, bullying, or distressing themes.
- SCORING:
  - 1-5: Contains concerning content (immediate fail)
  - 6-7: Minor tension that might worry sensitive children
  - 8-9: Safe with gentle, quickly-resolved challenges
  - 10: Completely warm, reassuring, and safe throughout
- FAIL CONDITION: Score below 9 is CRITICAL FAILURE.

METRIC 3: Engagement
- REQUIREMENT: Story must be interesting and captivating for children.
- SCORING:
  - 1-3: Boring, no compelling elements
  - 4-6: Somewhat interesting but flat in places
  - 7-9: Engaging with good pacing and interesting elements
  - 10: Highly captivating, children would love this
- FAIL CONDITION: Score below 6 indicates story needs more engaging elements.

METRIC 4: Coherence
- REQUIREMENT: Story must flow logically with consistent characters and clear plot.
- SCORING:
  - 1-3: Confusing, characters inconsistent, plot makes no sense
  - 4-6: Some logic gaps or minor inconsistencies
  - 7-9: Clear flow with consistent characters
  - 10: Perfect logical flow and character consistency
- FAIL CONDITION: Score below 6 indicates structural problems.

METRIC 5: Bedtime Suitability
- REQUIREMENT: Story must wind down toward calm. Ending must be peaceful and sleep-inducing.
- SCORING:
  - 1-3: Too exciting, stimulating, or ends on high energy
  - 4-6: Somewhat calming but not optimal for bedtime
  - 7-9: Good wind-down with peaceful ending
  - 10: Perfect bedtime story, ends with cozy, sleepy feelings
- FAIL CONDITION: Score below 7 means story doesn't serve bedtime purpose.

---

PASS/FAIL THRESHOLD:
- PASS: Overall average >= 8.0 AND Emotional Safety >= 9
- FAIL: Otherwise

---

OUTPUT FORMAT:
Return ONLY valid JSON. No markdown, no extra text.

{{
    "scores": {{
        "age_appropriate_language": {{
            "score": <1-10>,
            "reasoning": "Specific explanation with examples from text"
        }},
        "emotional_safety": {{
            "score": <1-10>,
            "reasoning": "Specific explanation - quote any concerning content if found"
        }},
        "engagement": {{
            "score": <1-10>,
            "reasoning": "Specific explanation of what works or doesn't"
        }},
        "coherence": {{
            "score": <1-10>,
            "reasoning": "Specific explanation of flow and consistency"
        }},
        "bedtime_suitability": {{
            "score": <1-10>,
            "reasoning": "Specific explanation of pacing and ending"
        }}
    }},
    "improvement_suggestions": [
        {{
            "criterion": "Name of metric to improve",
            "suggestion": "Specific, actionable improvement instruction",
            "priority": 1
        }},
        {{
            "criterion": "Second metric",
            "suggestion": "Second specific improvement",
            "priority": 2
        }},
        {{
            "criterion": "Third metric",
            "suggestion": "Third specific improvement",
            "priority": 3
        }}
    ],
    "overall_passed": <true or false>,
    "pass_reasoning": "Explanation of why story passes or fails threshold"
}}
"""

    # =========================================================================
    # STORY IMPROVER PROMPT
    # =========================================================================
    
    STORY_IMPROVER_PROMPT = """
ROLE: You are an expert children's story editor specializing in iterative improvement while preserving story structure.

TASK:
Improve the existing story based on judge feedback.
You must PRESERVE the characters and chapter structure exactly.
Return ONLY valid JSON with the improved story.

INPUT DATA:
- Story Title: "{title}"
- Target Age: {age_range} years
- Category: {category}
- Chapter Count: {chapter_count}

ORIGINAL CHARACTERS (PRESERVE EXACTLY):
{characters_json}

ORIGINAL CHAPTERS:
{chapters_json}

---

JUDGE FEEDBACK TO ADDRESS:
{judge_feedback}

---

IMPROVEMENT RULES:

PRESERVATION RULE:
- Character names and basic descriptions MUST remain identical
- Number of chapters MUST remain exactly {chapter_count}
- Overall story arc and plot must be preserved
- Do NOT introduce new major characters or plot elements

TARGETED IMPROVEMENT RULE:
- ONLY make changes that directly address the specific feedback
- If feedback says "vocabulary too complex," simplify specific words
- If feedback says "ending not calm enough," rewrite the final chapter's ending
- If feedback says "lacks engagement," add more sensory details and dialogue

SAFETY RULE:
- All improvements must maintain child-safety
- Never add content that could be scary, violent, or distressing
- When in doubt, make the content gentler, not more intense

{age_guidelines}

{category_guidelines}

---

OUTPUT FORMAT:
Return ONLY valid JSON with the improved story:

{{
    "title": "{title}",
    "characters": [preserved exactly as input],
    "chapters": [
        {{
            "chapter_number": 1,
            "chapter_title": "Title (same or slightly improved)",
            "chapter_text": "Improved content addressing feedback...",
            "chapter_summary": "Updated summary if content changed",
            "image_prompt": "Updated prompt if scene changed significantly"
        }}
    ],
    "moral_or_theme": "Preserved or slightly refined theme"
}}

VALIDATION:
- All {chapter_count} chapters must be included
- Character names must match original exactly
- Changes should be minimal and targeted to feedback
"""

    # =========================================================================
    # IDEA GENERATION PROMPTS
    # =========================================================================
    
    IDEA_GENERATION_PROMPTS = {
        "Bedtime Calm": """
ROLE: You are a creative bedtime story idea generator.

TASK: Generate ONE peaceful bedtime story idea for children aged {age_range}.

REQUIREMENTS:
- Focus on calming imagery: moonlight, stars, soft clouds, cozy blankets, gentle night sounds
- The idea should make a child feel sleepy and safe
- Include a simple, peaceful scenario or character

OUTPUT: Return only the story idea in 1-2 sentences. No extra text.
""",
        "Light Adventure": """
ROLE: You are a creative bedtime story idea generator.

TASK: Generate ONE gentle adventure story idea for children aged {age_range}.

REQUIREMENTS:
- Focus on discovery and exploration without danger
- Ideas like: finding a hidden garden, meeting a friendly creature, exploring a magical forest
- The adventure should be wonder-filled, not scary

OUTPUT: Return only the story idea in 1-2 sentences. No extra text.
""",
        "Silly & Playful": """
ROLE: You are a creative bedtime story idea generator.

TASK: Generate ONE funny, lighthearted story idea for children aged {age_range}.

REQUIREMENTS:
- Focus on silly situations, funny mix-ups, or playful characters
- The humor should be gentle and make children giggle
- No mean-spirited or embarrassing humor

OUTPUT: Return only the story idea in 1-2 sentences. No extra text.
""",
        "Friendship": """
ROLE: You are a creative bedtime story idea generator.

TASK: Generate ONE heartwarming friendship story idea for children aged {age_range}.

REQUIREMENTS:
- Focus on kindness, helping others, or the joy of friendship
- Include at least two characters who care about each other
- The idea should feel warm and emotionally cozy

OUTPUT: Return only the story idea in 1-2 sentences. No extra text.
""",
        "Learning & Curiosity": """
ROLE: You are a creative bedtime story idea generator.

TASK: Generate ONE educational story idea for children aged {age_range}.

REQUIREMENTS:
- Focus on discovering something new about nature, animals, or how things work
- Learning should happen through character experience, not lecturing
- The discovery should feel magical and wonder-filled

OUTPUT: Return only the story idea in 1-2 sentences. No extra text.
""",
        "Surprise Me": """
ROLE: You are a creative bedtime story idea generator.

TASK: Generate ONE creative, whimsical story idea for children aged {age_range}.

REQUIREMENTS:
- Blend elements creatively (adventure + friendship, learning + silliness, etc.)
- Make it unique and charming
- Ensure it's still appropriate for bedtime

OUTPUT: Return only the story idea in 1-2 sentences. No extra text.
"""
    }

    # =========================================================================
    # IMAGE GENERATION PROMPTS (For Gemini)
    # =========================================================================
    
    IMAGE_STYLE_PRESETS = {
        "Bedtime Calm": (
            "STYLE: Soft, dreamy watercolor illustration. "
            "COLORS: Gentle purples, deep blues, soft silver moonlight, warm golden glows. "
            "MOOD: Peaceful, sleepy, serene, cozy."
        ),
        "Light Adventure": (
            "STYLE: Vibrant children's book illustration, Pixar-style. "
            "COLORS: Bright greens, warm yellows, adventure blues, sunset oranges. "
            "MOOD: Wonder-filled, curious, exciting but safe."
        ),
        "Silly & Playful": (
            "STYLE: Whimsical cartoon illustration with expressive characters. "
            "COLORS: Bright primary colors, playful pinks, silly purples. "
            "MOOD: Joyful, giggly, energetic but friendly."
        ),
        "Friendship": (
            "STYLE: Warm, textured illustration like colored pencil or soft pastel. "
            "COLORS: Warm oranges, cozy browns, gentle pinks, loving reds. "
            "MOOD: Heartwarming, connected, emotionally cozy."
        ),
        "Learning & Curiosity": (
            "STYLE: Clear, detailed illustration with natural elements. "
            "COLORS: Nature greens, sky blues, earthy browns, curious yellows. "
            "MOOD: Wonder-filled, discovery, gentle excitement."
        ),
        "Surprise Me": (
            "STYLE: Magical, whimsical illustration blending styles. "
            "COLORS: Varied palette matching scene mood. "
            "MOOD: Enchanting, creative, imaginative."
        )
    }
    
    IMAGE_BASE_PROMPT = """
ROLE: You are a world-class children's book illustrator creating images for ages 5-10.

TECHNICAL REQUIREMENTS:
- Style: Children's book illustration, colorful, friendly, age-appropriate
- Composition: Main subject centered, clear focal point
- SAFETY: No violence, no scary elements, no dark themes, G-rated only
- TEXT POLICY: ABSOLUTELY NO TEXT, labels, or speech bubbles in the image

SCENE TO ILLUSTRATE:
{scene_description}

{style_preset}

ADDITIONAL GUIDANCE:
- Make characters look friendly with soft, rounded features
- Use warm, inviting colors even in nighttime scenes
- Include cozy details (soft textures, warm lights, gentle nature)
- The image should feel safe and welcoming for young children
"""

    COVER_IMAGE_PROMPT = """
ROLE: You are creating a book cover illustration for a children's bedtime story.

STORY DETAILS:
- Title: "{title}"
- Category: {category}
- Summary: {summary}

TECHNICAL REQUIREMENTS:
- Style: Professional children's book cover, eye-catching but gentle
- Composition: Main character(s) prominently featured, inviting scene
- SAFETY: G-rated, warm, welcoming
- TEXT POLICY: NO TEXT on the image (title will be added separately)

{style_preset}

COVER GUIDANCE:
- Show the main character(s) in an inviting pose
- Include key elements from the story setting
- The cover should make children want to read the story
- Mood should promise a cozy, enjoyable bedtime experience
"""

    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    @classmethod
    def get_chaptered_story_prompt(
        cls,
        user_prompt: str,
        age_range: str,
        category: str,
        chapter_count: int,
        improvement_instructions: str = ""
    ) -> str:
        """Get the prompt for generating a chaptered story."""
        age_guidelines = cls.AGE_STYLE_GUIDELINES.get(age_range, cls.AGE_STYLE_GUIDELINES["5-7"])
        category_guidelines = cls.CATEGORY_GUIDELINES.get(category, cls.CATEGORY_GUIDELINES["Bedtime Calm"])
        
        # Select chapter structure template (Short = 5 chapters, Long = 7 chapters)
        if chapter_count <= 5:
            chapter_structure_guide = cls.CHAPTER_STRUCTURE_5
        else:
            chapter_structure_guide = cls.CHAPTER_STRUCTURE_7
        
        # Calculate minimum words per chapter (5 ch = Short, 7 ch = Long)
        if age_range == "5-7":
            min_words_per_chapter = 120 if chapter_count <= 5 else 100
        else:
            min_words_per_chapter = 170 if chapter_count <= 5 else 140
        
        improvement_text = ""
        if improvement_instructions:
            improvement_text = f"""
IMPROVEMENT FOCUS (from previous iteration):
{improvement_instructions}
Address these specific issues while maintaining story quality.
"""
        
        return cls.CHAPTERED_STORY_PROMPT.format(
            user_prompt=user_prompt,
            age_range=age_range,
            category=category,
            chapter_count=chapter_count,
            min_words_per_chapter=min_words_per_chapter,
            age_guidelines=age_guidelines,
            category_guidelines=category_guidelines,
            chapter_structure_guide=chapter_structure_guide,
            improvement_instructions=improvement_text
        )

    @classmethod
    def get_judge_evaluation_prompt(
        cls,
        title: str,
        age_range: str,
        category: str,
        story_text: str
    ) -> str:
        """Get the judge evaluation prompt."""
        return cls.JUDGE_EVALUATION_PROMPT.format(
            title=title,
            age_range=age_range,
            category=category,
            story_text=story_text
        )

    @classmethod
    def get_story_improver_prompt(
        cls,
        title: str,
        age_range: str,
        category: str,
        characters_json: str,
        chapters_json: str,
        chapter_count: int,
        judge_feedback: str
    ) -> str:
        """Get the prompt for story improvement."""
        age_guidelines = cls.AGE_STYLE_GUIDELINES.get(age_range, cls.AGE_STYLE_GUIDELINES["5-7"])
        category_guidelines = cls.CATEGORY_GUIDELINES.get(category, cls.CATEGORY_GUIDELINES["Bedtime Calm"])
        
        return cls.STORY_IMPROVER_PROMPT.format(
            title=title,
            age_range=age_range,
            category=category,
            characters_json=characters_json,
            chapters_json=chapters_json,
            chapter_count=chapter_count,
            judge_feedback=judge_feedback,
            age_guidelines=age_guidelines,
            category_guidelines=category_guidelines
        )

    @classmethod
    def get_category_classifier_prompt(cls, user_prompt: str) -> str:
        """Get the category classification prompt."""
        return cls.CATEGORY_CLASSIFIER_PROMPT.format(user_prompt=user_prompt)

    @classmethod
    def get_idea_generation_prompt(cls, category: str, age_range: str = "5-7") -> str:
        """Get the idea generation prompt for a specific category."""
        prompt_template = cls.IDEA_GENERATION_PROMPTS.get(
            category, 
            cls.IDEA_GENERATION_PROMPTS["Surprise Me"]
        )
        return prompt_template.format(age_range=age_range)

    @classmethod
    def get_image_prompt(cls, scene_description: str, category: str = "Bedtime Calm") -> str:
        """Get the image generation prompt for Gemini."""
        style_preset = cls.IMAGE_STYLE_PRESETS.get(category, cls.IMAGE_STYLE_PRESETS["Bedtime Calm"])
        return cls.IMAGE_BASE_PROMPT.format(
            scene_description=scene_description,
            style_preset=style_preset
        )

    @classmethod
    def get_cover_image_prompt(cls, title: str, category: str, summary: str) -> str:
        """Get the cover image generation prompt."""
        style_preset = cls.IMAGE_STYLE_PRESETS.get(category, cls.IMAGE_STYLE_PRESETS["Bedtime Calm"])
        return cls.COVER_IMAGE_PROMPT.format(
            title=title,
            category=category,
            summary=summary,
            style_preset=style_preset
        )

    @classmethod
    def parse_judge_feedback(cls, judge_response_json: str) -> str:
        """
        Parse judge JSON response and extract actionable feedback.
        Returns formatted feedback string for the improver.
        """
        try:
            data = json.loads(judge_response_json)
            
            if data.get("overall_passed", False):
                return ""
            
            feedback_parts = []
            
            # Add pass reasoning
            if data.get("pass_reasoning"):
                feedback_parts.append(f"SUMMARY: {data['pass_reasoning']}")
            
            feedback_parts.append("\nSPECIFIC IMPROVEMENTS NEEDED:")
            
            # Extract failed metrics
            scores = data.get("scores", {})
            for metric_name, details in scores.items():
                score = details.get("score", 0)
                if score < 8:  # Below passing threshold
                    readable_name = metric_name.replace("_", " ").title()
                    reasoning = details.get("reasoning", "Needs improvement")
                    feedback_parts.append(f"- [{readable_name}] (Score: {score}/10): {reasoning}")
            
            # Add improvement suggestions
            suggestions = data.get("improvement_suggestions", [])
            if suggestions:
                feedback_parts.append("\nACTIONABLE SUGGESTIONS:")
                for sugg in suggestions:
                    criterion = sugg.get("criterion", "General")
                    suggestion = sugg.get("suggestion", "Improve this area")
                    priority = sugg.get("priority", 0)
                    feedback_parts.append(f"- [Priority {priority}] {criterion}: {suggestion}")
            
            return "\n".join(feedback_parts)
            
        except json.JSONDecodeError:
            return "ERROR: Could not parse judge response. Please ensure story meets safety and quality requirements."
