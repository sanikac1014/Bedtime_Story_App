"""
Flipbook Component for Dreamweaver Bedtime Stories.
Real page-flip book experience with images on left, text on right.
"""

import html
import base64
from typing import List, Optional
from models.pydantic_models import ChapteredStory, Chapter, Character


def escape_html(text: str) -> str:
    """Safely escape HTML characters in user content."""
    if not text:
        return ""
    return html.escape(str(text))


def image_to_base64(image) -> str:
    """Convert PIL image to base64 string."""
    try:
        import io
        from PIL import Image
        if image is None:
            return ""
        if isinstance(image, Image.Image):
            buffer = io.BytesIO()
            image.save(buffer, format='PNG')
            return base64.b64encode(buffer.getvalue()).decode()
    except:
        pass
    return ""


def render_flipbook_html(story: ChapteredStory, images: Optional[List] = None) -> str:
    """Generate HTML/CSS/JS for a flipbook with images on left, text on right."""
    
    title = escape_html(story.title)
    category = escape_html(story.category.value) if story.category else "Bedtime"
    age_range = escape_html(story.age_range.value) if story.age_range else "5-10"
    moral = escape_html(story.moral_or_theme) if story.moral_or_theme else ""
    
    # Convert images to base64
    image_data = []
    if images:
        for img in images:
            b64 = image_to_base64(img)
            image_data.append(b64)
    
    # Build all pages (spreads)
    pages = []
    
    # Page 0: Cover (full spread)
    pages.append({
        'left': f'''
            <div class="cover-left">
                <div class="cover-decoration">✨</div>
            </div>
        ''',
        'right': f'''
            <div class="cover-right">
                <div class="cover-moon">🌙</div>
                <h1 class="cover-title">{title}</h1>
                <p class="cover-cat">A {category} Story</p>
                <p class="cover-age">For ages {age_range}</p>
                <p class="cover-hint">Click to open →</p>
            </div>
        '''
    })
    
    # Page 1: Characters
    chars_html = ""
    for char in story.characters:
        chars_html += f'<div class="char"><span class="char-name">✨ {escape_html(char.name)}</span><br>{escape_html(char.description)}</div>'
    
    pages.append({
        'left': f'''
            <div class="page-left-content">
                <div class="left-title">Our Heroes</div>
                <div class="left-icon">👥</div>
            </div>
        ''',
        'right': f'''
            <div class="page-right-content">
                <h2 class="page-title">Characters</h2>
                <div class="chars-list">{chars_html}</div>
            </div>
        '''
    })
    
    # Page 2: Table of Contents
    toc_html = ""
    for i, ch in enumerate(story.chapters):
        toc_html += f'<div class="toc-row" onclick="flipTo({i + 3})"><span class="toc-num">{ch.chapter_number}.</span> {escape_html(ch.chapter_title)}</div>'
    
    pages.append({
        'left': f'''
            <div class="page-left-content">
                <div class="left-title">Contents</div>
                <div class="left-icon">📖</div>
            </div>
        ''',
        'right': f'''
            <div class="page-right-content">
                <h2 class="page-title">Chapters</h2>
                <div class="toc-list">{toc_html}</div>
            </div>
        '''
    })
    
    # Chapter pages with images
    for i, ch in enumerate(story.chapters):
        ch_text = escape_html(ch.chapter_text)
        
        # Get image for this chapter
        img_html = ""
        if i < len(image_data) and image_data[i]:
            img_html = f'<img src="data:image/png;base64,{image_data[i]}" class="chapter-image" alt="Chapter {ch.chapter_number} illustration">'
        else:
            # Placeholder with chapter number
            img_html = f'''
                <div class="image-placeholder">
                    <div class="placeholder-icon">🎨</div>
                    <div class="placeholder-text">Chapter {ch.chapter_number}</div>
                </div>
            '''
        
        pages.append({
            'left': f'''
                <div class="image-page">
                    {img_html}
                </div>
            ''',
            'right': f'''
                <div class="page-right-content chapter">
                    <div class="ch-num">Chapter {ch.chapter_number}</div>
                    <h2 class="ch-title">{escape_html(ch.chapter_title)}</h2>
                    <p class="ch-text">{ch_text}</p>
                </div>
            '''
        })
    
    # Moral page
    if moral:
        pages.append({
            'left': f'''
                <div class="moral-left">
                    <div class="moral-decoration">🌟</div>
                </div>
            ''',
            'right': f'''
                <div class="moral-right">
                    <div class="moral-star">⭐</div>
                    <h2 class="moral-label">Moral</h2>
                    <p class="moral-text">"{moral}"</p>
                    <p class="the-end">~ The End ~</p>
                </div>
            '''
        })
    
    # Build page elements
    pages_html = ""
    for i, page in enumerate(pages):
        z = len(pages) - i
        pages_html += f'''
        <div class="page" style="z-index: {z};" data-page="{i}">
            <div class="page-front">
                <div class="page-left">{page['left']}</div>
                <div class="page-right">{page['right']}</div>
            </div>
            <div class="page-back"></div>
        </div>
        '''
    
    total = len(pages)
    
    return f'''<!DOCTYPE html>
<html>
<head>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ 
    font-family: 'Georgia', serif; 
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 15px;
}}

.book-wrapper {{
    perspective: 2000px;
}}

.book {{
    position: relative;
    width: 680px;
    height: 440px;
    transform-style: preserve-3d;
}}

.page {{
    position: absolute;
    width: 100%;
    height: 100%;
    transform-origin: left center;
    transition: transform 0.9s cubic-bezier(0.645, 0.045, 0.355, 1);
    transform-style: preserve-3d;
    cursor: pointer;
}}

.page.flipped {{
    transform: rotateY(-180deg);
}}

.page-front, .page-back {{
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    border-radius: 0 8px 8px 0;
    overflow: hidden;
    display: flex;
}}

.page-front {{
    background: #faf6ee;
    box-shadow: 2px 0 15px rgba(0,0,0,0.15);
}}

.page-back {{
    background: linear-gradient(to left, #e8e2d5 0%, #f0ebe0 100%);
    transform: rotateY(180deg);
}}

.page-left, .page-right {{
    width: 50%;
    height: 100%;
    overflow: hidden;
}}

.page-left {{
    background: linear-gradient(to right, #f0ebe0 0%, #f5f0e6 100%);
    border-right: 1px solid #e0d5c5;
}}

.page-right {{
    background: linear-gradient(to right, #faf6ee 0%, #fdfbf7 100%);
}}

/* Cover */
.cover-left {{
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #2a1810 0%, #3d2914 100%);
    display: flex;
    justify-content: center;
    align-items: center;
}}

.cover-decoration {{ font-size: 4rem; opacity: 0.3; }}

.cover-right {{
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #3d2914 0%, #5a3a1d 100%);
    color: #f4e4c1;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 20px;
}}

.cover-moon {{ font-size: 3rem; margin-bottom: 12px; }}
.cover-title {{ font-size: 1.5rem; font-weight: bold; line-height: 1.3; margin-bottom: 10px; }}
.cover-cat {{ font-size: 0.95rem; opacity: 0.85; margin-bottom: 5px; }}
.cover-age {{ font-size: 0.8rem; opacity: 0.6; }}
.cover-hint {{ font-size: 0.7rem; opacity: 0.4; margin-top: 25px; }}

/* Left page content */
.page-left-content {{
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #f5f0e6 0%, #ebe5da 100%);
}}

.left-title {{ font-size: 1rem; color: #8d6e63; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 15px; }}
.left-icon {{ font-size: 4rem; opacity: 0.4; }}

/* Right page content */
.page-right-content {{
    padding: 25px;
    height: 100%;
    overflow-y: auto;
}}

.page-title {{
    font-size: 1.2rem;
    color: #5d4037;
    text-align: center;
    padding-bottom: 10px;
    margin-bottom: 15px;
    border-bottom: 2px dashed #e0d5c5;
}}

/* Characters */
.chars-list {{ display: flex; flex-direction: column; gap: 10px; }}
.char {{
    padding: 10px;
    background: rgba(255,255,255,0.6);
    border-radius: 6px;
    border-left: 3px solid #8d6e63;
    font-size: 0.85rem;
    color: #5d4037;
    line-height: 1.4;
}}
.char-name {{ font-weight: bold; color: #5d4037; }}

/* TOC */
.toc-list {{ display: flex; flex-direction: column; gap: 8px; }}
.toc-row {{
    padding: 8px 10px;
    background: rgba(255,255,255,0.5);
    border-radius: 5px;
    font-size: 0.9rem;
    color: #5d4037;
    cursor: pointer;
    transition: all 0.15s;
}}
.toc-row:hover {{ background: rgba(139,90,43,0.1); transform: translateX(3px); }}
.toc-num {{ font-weight: bold; color: #8d6e63; }}

/* Image page */
.image-page {{
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, #f5f0e6 0%, #ebe5da 100%);
    padding: 15px;
}}

.chapter-image {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    border-radius: 8px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
}}

.image-placeholder {{
    width: 90%;
    height: 85%;
    background: linear-gradient(135deg, #e8e2d5 0%, #d5cfc2 100%);
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    border: 2px dashed #c5bfb2;
}}

.placeholder-icon {{ font-size: 3rem; opacity: 0.4; margin-bottom: 10px; }}
.placeholder-text {{ font-size: 0.9rem; color: #a09080; }}

/* Chapter */
.ch-num {{ font-size: 0.65rem; color: #a1887f; text-transform: uppercase; letter-spacing: 2px; text-align: center; margin-bottom: 5px; }}
.ch-title {{ font-size: 1.1rem; color: #5d4037; text-align: center; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e0d5c5; }}
.ch-text {{ font-size: 0.88rem; color: #4e342e; line-height: 1.75; text-align: justify; }}

/* Moral */
.moral-left {{
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #c8e6c9 0%, #a5d6a7 100%);
    display: flex;
    justify-content: center;
    align-items: center;
}}

.moral-decoration {{ font-size: 4rem; opacity: 0.3; }}

.moral-right {{
    width: 100%;
    height: 100%;
    background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    padding: 20px;
}}

.moral-star {{ font-size: 2rem; margin-bottom: 10px; }}
.moral-label {{ font-size: 0.9rem; color: #388e3c; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 10px; }}
.moral-text {{ font-size: 1rem; color: #2e7d32; font-style: italic; line-height: 1.5; max-width: 250px; }}
.the-end {{ margin-top: 18px; font-size: 0.95rem; color: #66bb6a; }}

/* Book spine */
.book::before {{
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    width: 20px;
    height: 100%;
    background: linear-gradient(to right, 
        rgba(0,0,0,0.2) 0%,
        rgba(0,0,0,0.08) 50%,
        transparent 100%);
    z-index: 1000;
    border-radius: 8px 0 0 8px;
}}

/* Center fold shadow */
.page-front::after {{
    content: '';
    position: absolute;
    left: 50%;
    top: 0;
    width: 30px;
    height: 100%;
    transform: translateX(-50%);
    background: linear-gradient(to right,
        rgba(0,0,0,0.06) 0%,
        rgba(0,0,0,0.02) 30%,
        transparent 50%,
        rgba(0,0,0,0.02) 70%,
        rgba(0,0,0,0.06) 100%);
    pointer-events: none;
}}

.instructions {{
    position: absolute;
    bottom: -30px;
    left: 50%;
    transform: translateX(-50%);
    color: rgba(255,255,255,0.5);
    font-size: 0.7rem;
    white-space: nowrap;
}}
</style>
</head>
<body>
<div class="book-wrapper">
    <div class="book" id="book">
        {pages_html}
    </div>
    <div class="instructions">Click pages to flip • Arrow keys to navigate</div>
</div>

<script>
const pages = document.querySelectorAll('.page');
const total = {total};
let current = 0;

pages.forEach((page, i) => {{
    page.addEventListener('click', (e) => {{
        const rect = page.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const pageWidth = rect.width;
        
        // Click on right side to flip forward
        if (clickX > pageWidth * 0.5 && i === current && current < total - 1) {{
            page.classList.add('flipped');
            current++;
        }}
        // Click on left side to flip back
        else if (clickX < pageWidth * 0.5 && current > 0) {{
            current--;
            pages[current].classList.remove('flipped');
        }}
    }});
}});

document.addEventListener('keydown', (e) => {{
    if (e.key === 'ArrowRight' && current < total - 1) {{
        pages[current].classList.add('flipped');
        current++;
    }} else if (e.key === 'ArrowLeft' && current > 0) {{
        current--;
        pages[current].classList.remove('flipped');
    }}
}});

function flipTo(pageNum) {{
    while (current < pageNum && current < total - 1) {{
        pages[current].classList.add('flipped');
        current++;
    }}
}}
</script>
</body>
</html>'''
