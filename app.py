"""
Dreamweaver Bedtime Stories - Main Streamlit Application
An AI-powered bedtime story generator for children ages 5-10.
"""

import streamlit as st
import streamlit.components.v1 as components
import os
import logging
from typing import Dict, Any, Optional, List
from PIL import Image
import io

from workflow import create_storyteller_workflow
from models.pydantic_models import (
    ChapteredStory, Chapter, Character, 
    StoryCategory, AgeRange, StoryLength,
    JudgeEvaluation, IterationResult, QualityIterationsPanel,
    get_category_emoji
)
from agents.generator import create_idea_generator
from utils.flipbook import render_flipbook_html

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Dreamweaver Bedtime Stories",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700&display=swap');
    
    /* Night sky background with stars */
    .stApp {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    }
    
    .stApp::before {
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        background-image: 
            radial-gradient(2px 2px at 20px 30px, #fff, transparent),
            radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
            radial-gradient(1px 1px at 90px 40px, #fff, transparent),
            radial-gradient(2px 2px at 160px 120px, rgba(255,255,255,0.9), transparent),
            radial-gradient(1px 1px at 230px 80px, #fff, transparent),
            radial-gradient(2px 2px at 300px 150px, rgba(255,255,255,0.7), transparent),
            radial-gradient(1px 1px at 400px 60px, #fff, transparent),
            radial-gradient(2px 2px at 500px 200px, rgba(255,255,255,0.8), transparent);
        background-repeat: repeat;
        background-size: 550px 250px;
        animation: twinkle 4s ease-in-out infinite;
        z-index: 0;
    }
    
    @keyframes twinkle {
        0%, 100% { opacity: 0.7; }
        50% { opacity: 1; }
    }
    
    .main .block-container {
        position: relative;
        z-index: 1;
        max-width: 100%;
        padding: 1rem 2rem 2rem 2rem;
    }
    
    /* Two-step UI: no sidebar – full-width setup and storybook */
    [data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* Header */
    .header-container {
        text-align: center;
        padding: 1.5rem 2rem 2rem 2rem;
        margin-bottom: 1.5rem;
    }
    
    .header-moon {
        font-size: 2.5rem;
        filter: drop-shadow(0 0 15px rgba(255, 220, 150, 0.5));
        margin-right: 0.3rem;
    }
    
    .main-header {
        font-family: 'Nunito', sans-serif;
        font-size: 2.8rem;
        font-weight: 700;
        color: #f4e4c1;
        margin-bottom: 0.4rem;
        letter-spacing: 2px;
    }
    
    .header-text {
        background: linear-gradient(135deg, #f4e4c1 0%, #daa520 50%, #f4e4c1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .tagline {
        font-family: 'Nunito', sans-serif;
        color: #b8a8c8;
        font-size: 1rem;
        font-style: italic;
        letter-spacing: 1px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e1e3f 0%, #141428 100%);
    }
    
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        font-family: 'Nunito', sans-serif;
        color: #c4b8e0 !important;
    }
    
    /* Input section */
    .input-title {
        font-family: 'Nunito', sans-serif;
        font-weight: 600;
        color: #c4b8e0;
        font-size: 1.3rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Text area */
    .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 12px !important;
        color: #e0d4f7 !important;
        font-family: 'Nunito', sans-serif !important;
    }
    
    /* Buttons */
    .stButton > button {
        font-family: 'Nunito', sans-serif !important;
        font-weight: 600 !important;
        border-radius: 25px !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 5px 20px rgba(102,126,234,0.4) !important;
    }
    
    .stButton > button:not([kind="primary"]) {
        background: rgba(255,255,255,0.1) !important;
        color: #c4b8e0 !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
    }
    
    /* Progress box */
    .progress-box {
        background: rgba(102,126,234,0.2);
        border: 1px solid rgba(102,126,234,0.4);
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        margin: 1.5rem auto;
        max-width: 400px;
    }
    
    .progress-icon {
        font-size: 3rem;
        margin-bottom: 0.5rem;
    }
    
    .progress-text {
        font-family: 'Nunito', sans-serif;
        font-weight: 600;
        color: #c4b8e0;
        font-size: 1.1rem;
    }
    
    /* Section header */
    .section-header {
        font-family: 'Nunito', sans-serif;
        font-weight: 700;
        color: #c4b8e0;
        font-size: 1.2rem;
        margin: 1.5rem 0 1rem 0;
    }
    
    /* Quality panel */
    .quality-box {
        background: rgba(76,175,80,0.15);
        border: 1px solid rgba(76,175,80,0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Hide streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Flipbook container styling */
    .flipbook-wrapper {
        margin: 1rem 0;
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* Fallback tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 0.3rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Nunito', sans-serif !important;
        color: #a99fc4 !important;
        border-radius: 8px !important;
    }
    
    .stTabs [aria-selected="true"] {
        background: rgba(102,126,234,0.3) !important;
        color: #e0d4f7 !important;
    }
    
    /* Character cards for fallback */
    .character-card {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .character-name {
        font-family: 'Nunito', sans-serif;
        font-weight: 700;
        color: #c4b8e0;
        font-size: 1.1rem;
    }
    
    .character-desc {
        font-family: 'Nunito', sans-serif;
        color: #a99fc4;
        font-size: 0.95rem;
    }
    
    /* Chapter card fallback */
    .chapter-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .chapter-title-text {
        font-family: 'Nunito', sans-serif;
        font-weight: 700;
        color: #c4b8e0;
        font-size: 1.4rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
        padding-bottom: 0.5rem;
    }
    
    .chapter-summary {
        background: rgba(76,175,80,0.15);
        border-left: 3px solid #4CAF50;
        padding: 0.8rem 1rem;
        border-radius: 0 8px 8px 0;
        margin-bottom: 1rem;
        color: #a5d6a7;
        font-style: italic;
        font-family: 'Nunito', sans-serif;
    }
    
    .chapter-text {
        font-family: 'Nunito', sans-serif;
        color: #d0c8e8;
        font-size: 1.05rem;
        line-height: 1.8;
    }
    
    /* Moral box */
    .moral-box {
        background: linear-gradient(135deg, rgba(156,39,176,0.2) 0%, rgba(103,58,183,0.2) 100%);
        border: 1px solid rgba(156,39,176,0.4);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 2rem 0;
        text-align: center;
    }
    
    .moral-label {
        font-family: 'Nunito', sans-serif;
        font-weight: 700;
        color: #ce93d8;
        font-size: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .moral-text {
        font-family: 'Nunito', sans-serif;
        color: #e0d4f7;
        font-size: 1.15rem;
        font-style: italic;
    }
</style>
""", unsafe_allow_html=True)


class DreamweaverApp:
    
    CATEGORIES = [
        ("🌙 Bedtime Calm", "Bedtime Calm"),
        ("🧭 Light Adventure", "Light Adventure"),
        ("😄 Silly & Playful", "Silly & Playful"),
        ("❤️ Friendship", "Friendship"),
        ("🔍 Learning & Curiosity", "Learning & Curiosity"),
        ("🎲 Surprise Me", "Surprise Me")
    ]
    
    AGE_RANGES = [
        ("5-7 years", "5-7"),
        ("7-10 years", "7-10")
    ]
    
    STORY_LENGTHS = [
        ("Short (5 chapters)", "Short"),
        ("Long (7 chapters)", "Long")
    ]
    
    def __init__(self):
        self.workflow = None
        self.idea_generator = None
        self._initialize_session_state()
        self._setup_api_key()
    
    def _initialize_session_state(self):
        defaults = {
            'story_generated': False,
            'chaptered_story': None,
            'images': [],
            'workflow_state': {},
            'current_chapter': 0,
            'age_range': "5-7",
            'category': None,  # No default category - user must choose
            'story_length': "Short",
            'generation_in_progress': False,
            'story_idea': "",
            'use_flipbook': True,  # Toggle for flipbook vs tabs
            'scroll_to_top': False
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def _setup_api_key(self):
        from dotenv import load_dotenv
        load_dotenv(override=True)
        
        env_api_key = os.getenv('OPENAI_API_KEY', '')
        if env_api_key:
            os.environ['OPENAI_API_KEY'] = env_api_key
        
        if not os.getenv('OPENAI_API_KEY'):
            st.error("Please add your OpenAI API key to the .env file")
            st.stop()
        
        # Load Gemini key for image generation (optional; placeholders used if missing)
        gemini_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
        if gemini_key:
            os.environ['GEMINI_API_KEY'] = gemini_key.strip()
    
    def _initialize_workflow(self):
        if self.workflow is None:
            with st.spinner("Preparing story magic..."):
                try:
                    self.workflow = create_storyteller_workflow(
                        classifier_model="gpt-3.5-turbo",
                        generator_model="gpt-3.5-turbo",
                        judge_model="gpt-3.5-turbo",
                        image_model="gemini-2.5-flash-image",  # Gemini image generation
                        max_attempts=3
                    )
                except Exception as e:
                    st.error(f"Failed to initialize: {str(e)}")
                    st.stop()
    
    def scroll_to_top(self):
        """Inject JavaScript to scroll to top of page."""
        js = """
        <script>
            window.parent.document.querySelector('section.main').scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        </script>
        """
        st.components.v1.html(js, height=0)
    
    def render_header(self):
        # Scroll to top if requested
        if st.session_state.get('scroll_to_top', False):
            self.scroll_to_top()
            st.session_state.scroll_to_top = False
        
        st.markdown('''
        <div class="header-container">
            <h1 class="main-header"><span class="header-moon">🌙</span> <span class="header-text">Dreamweaver</span></h1>
            <p class="tagline">~ Bedtime stories crafted with care ~</p>
        </div>
        ''', unsafe_allow_html=True)
    
    def render_setup_landing(self):
        """Full-width Setup landing: age, category, length, story idea, Create My Story."""
        st.markdown('<div class="section-header">🌙 Setup your bedtime story</div>', unsafe_allow_html=True)
        st.markdown("")
        
        # Age, Category, Length in one row
        col_age, col_cat, col_len = st.columns(3)
        
        with col_age:
            st.markdown("**🎂 Age range**")
            age_options = [opt[0] for opt in self.AGE_RANGES]
            age_values = [opt[1] for opt in self.AGE_RANGES]
            age_idx = age_values.index(st.session_state.age_range) if st.session_state.age_range in age_values else 0
            selected_age = st.radio("Age:", age_options, index=age_idx, label_visibility="collapsed", horizontal=True)
            st.session_state.age_range = self.AGE_RANGES[age_options.index(selected_age)][1]
        
        with col_cat:
            st.markdown("**📚 Category**")
            cat_options = ["Choose a category..."] + [opt[0] for opt in self.CATEGORIES]
            if st.session_state.category is None:
                cat_idx = 0
            else:
                cat_values = [opt[1] for opt in self.CATEGORIES]
                cat_idx = cat_values.index(st.session_state.category) + 1 if st.session_state.category in cat_values else 0
            selected_cat = st.selectbox("Category:", cat_options, index=cat_idx, label_visibility="collapsed")
            if selected_cat != "Choose a category...":
                st.session_state.category = self.CATEGORIES[cat_options.index(selected_cat) - 1][1]
            else:
                st.session_state.category = None
        
        with col_len:
            st.markdown("**📏 Length**")
            len_options = [opt[0] for opt in self.STORY_LENGTHS]
            len_values = [opt[1] for opt in self.STORY_LENGTHS]
            len_idx = len_values.index(st.session_state.story_length) if st.session_state.story_length in len_values else 0
            selected_len = st.radio("Length:", len_options, index=len_idx, label_visibility="collapsed", horizontal=True)
            st.session_state.story_length = self.STORY_LENGTHS[len_options.index(selected_len)][1]
        
        st.markdown("---")
        st.markdown('<div class="input-title">💭 What shall we dream tonight?</div>', unsafe_allow_html=True)
        
        user_prompt = st.text_area(
            "Story idea:",
            value=st.session_state.story_idea,
            placeholder="A little bunny who rides a cloud to visit the moon...",
            height=100,
            label_visibility="collapsed"
        )
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("✨ Generate a story idea", use_container_width=True):
                if self.idea_generator is None:
                    self.idea_generator = create_idea_generator()
                with st.spinner("Thinking..."):
                    idea_category = st.session_state.category or "Surprise Me"
                    idea = self.idea_generator.generate_idea(idea_category)
                    if idea:
                        st.session_state.story_idea = idea
                        st.rerun()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        has_prompt = user_prompt and user_prompt.strip()
        has_category = st.session_state.category is not None
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            generate_button = st.button(
                "✨ Create My Story ✨",
                type="primary",
                use_container_width=True,
                disabled=not has_prompt or not has_category
            )
            if not has_category and has_prompt:
                st.caption("👆 Please select a category above")
        
        return user_prompt if user_prompt else "", generate_button
    
    def render_progress(self, stage: str):
        stages = {
            "generating": ("✍️", "Writing your story..."),
            "evaluating": ("⭐", "Checking quality..."),
            "improving": ("✨", "Making it better..."),
            "creating_images": ("🎨", "Creating pictures..."),
        }
        
        if stage in stages:
            icon, text = stages[stage]
            st.markdown(f"""
            <div class="progress-box">
                <div class="progress-icon">{icon}</div>
                <div class="progress-text">{text}</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_quality_panel(self, iterations_history, final_passed):
        with st.expander("📊 Quality Check", expanded=False):
            for iteration in iterations_history:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    st.write(f"Round {iteration.iteration_number}")
                with col2:
                    st.write(f"Score: {iteration.overall_score:.1f}/10")
                with col3:
                    st.write("✓ Passed" if iteration.passed else "Improving...")
    
    def render_flipbook(self, story: ChapteredStory, images: List):
        """Render the story in flipbook format."""
        try:
            flipbook_html = render_flipbook_html(story, images)
            components.html(flipbook_html, height=540, scrolling=False)
        except Exception as e:
            logger.error(f"Flipbook render error: {str(e)}")
            st.warning("Could not render flipbook. Showing tab view instead.")
            self.render_fallback_tabs(story, images)
    
    def render_fallback_tabs(self, story: ChapteredStory, images: List):
        """Fallback tab-based chapter view."""
        # Characters
        if story.characters:
            st.markdown('<div class="section-header">👥 Characters</div>', unsafe_allow_html=True)
            cols = st.columns(min(len(story.characters), 3))
            for i, char in enumerate(story.characters):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div class="character-card">
                        <div class="character-name">✨ {char.name}</div>
                        <div class="character-desc">{char.description}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Chapters
        st.markdown('<div class="section-header">📖 Story</div>', unsafe_allow_html=True)
        chapter_titles = [f"Chapter {ch.chapter_number}" for ch in story.chapters]
        tabs = st.tabs(chapter_titles)
        
        for i, (tab, chapter) in enumerate(zip(tabs, story.chapters)):
            with tab:
                if chapter.chapter_summary:
                    st.markdown(f'<div class="chapter-summary">{chapter.chapter_summary}</div>', unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="chapter-card">
                    <div class="chapter-title-text">{chapter.chapter_title}</div>
                    <div class="chapter-text">{chapter.chapter_text}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if i < len(images) and images[i]:
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        st.image(images[i], use_container_width=True)
        
        # Moral
        if story.moral_or_theme:
            st.markdown(f"""
            <div class="moral-box">
                <div class="moral-label">✨ Moral ✨</div>
                <div class="moral-text">"{story.moral_or_theme}"</div>
            </div>
            """, unsafe_allow_html=True)
    
    def render_story(self, story: ChapteredStory, images: List, workflow_state: Dict):
        if not story:
            return

        # View mode toggle (top-right): Book View vs Tab View
        _, col_toggle = st.columns([5, 1])
        with col_toggle:
            st.toggle(
                "📖 Book View",
                key="use_flipbook",
                help="On: flipbook style. Off: chapter tabs.",
            )

        # Render story based on view mode
        if st.session_state.use_flipbook:
            self.render_flipbook(story, images)
        else:
            # Show title for tab view
            emoji = get_category_emoji(story.category)
            st.markdown(f"""
            <div style="text-align: center; margin-bottom: 1rem;">
                <h2 style="color: #e0d4f7; font-family: 'Nunito', sans-serif;">{emoji} {story.title}</h2>
                <p style="color: #a99fc4;">A {story.category.value} story for ages {story.age_range.value}</p>
            </div>
            """, unsafe_allow_html=True)
            self.render_fallback_tabs(story, images)
    
    def generate_story(self, user_prompt):
        # Safety check: ensure category is selected
        if st.session_state.category is None:
            st.error("Please select a category above before creating a story.")
            return
            
        self._initialize_workflow()
        st.session_state.generation_in_progress = True
        
        progress = st.empty()
        
        try:
            with progress.container():
                self.render_progress("generating")
            
            final_state = self.workflow.run(
                user_prompt=user_prompt,
                age_range=st.session_state.age_range,
                story_length=st.session_state.story_length,
                preset_category=st.session_state.category
            )
            
            progress.empty()
            
            if final_state.get("error_message"):
                st.error(final_state["error_message"])
                return
            
            if final_state.get("chaptered_story"):
                st.session_state.chaptered_story = final_state["chaptered_story"]
                st.session_state.images = final_state.get("images", [])
                st.session_state.workflow_state = final_state
                st.session_state.story_generated = True
                st.session_state.story_idea = ""
                st.session_state.scroll_to_top = True
                st.balloons()
                st.rerun()
            else:
                st.error("Failed to generate story. Please try again.")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            logger.error(f"Error: {str(e)}")
        finally:
            st.session_state.generation_in_progress = False
    
    def run(self):
        if not st.session_state.story_generated:
            # Step 1: Full-width Setup landing (no sidebar)
            self.render_header()
            user_prompt, generate = self.render_setup_landing()
            if generate and user_prompt and user_prompt.strip():
                self.generate_story(user_prompt.strip())
        else:
            # Step 2: Immersive full-width storybook (no sidebar)
            self.render_header()
            if st.session_state.chaptered_story:
                self.render_story(
                    st.session_state.chaptered_story,
                    st.session_state.images,
                    st.session_state.workflow_state
                )
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("✨ Generate Another Story", type="primary", use_container_width=True):
                    st.session_state.story_generated = False
                    st.session_state.chaptered_story = None
                    st.session_state.images = []
                    st.session_state.workflow_state = {}
                    st.session_state.story_idea = ""
                    st.rerun()


def main():
    try:
        app = DreamweaverApp()
        app.run()
    except Exception as e:
        st.error(f"Error: {str(e)}")
        logger.error(f"Error: {str(e)}")


if __name__ == "__main__":
    main()
