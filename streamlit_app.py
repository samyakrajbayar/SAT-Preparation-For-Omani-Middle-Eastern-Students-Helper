import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time
import json
import os
from datetime import datetime, timedelta
from sat_utils import SATPrep
from analytics_engine import AnalyticsEngine
from recommendation_engine import RecommendationEngine
from ml_models import SATMLModels
from nlp_processor import NLPProcessor
import networkx as nx

# Initialize components
sat = SATPrep()
analytics = AnalyticsEngine(None)
recommender = RecommendationEngine(None)
ml_models = SATMLModels()
nlp = NLPProcessor()

# Page configuration
st.set_page_config(
    page_title="SAT Prep Oman - Ultra Advanced",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://discord.gg/satprep',
        'Report a bug': "mailto:support@satprepoman.com",
        'About': "# SAT Prep Oman\n\nAdvanced SAT preparation platform for Omani students"
    }
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        background: linear-gradient(45deg, #1f77b4, #2ca02c);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #3498db;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 0.5rem;
        padding: 1rem;
        color: white;
        text-align: center;
    }
    .recommendation-card {
        background-color: #f8f9fa;
        border-left: 4px solid #3498db;
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0.25rem;
    }
    .high-priority {
        border-left-color: #e74c3c;
    }
    .medium-priority {
        border-left-color: #f39c12;
    }
    .low-priority {
        border-left-color: #2ecc71;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = str(time.time())
if 'current_question' not in st.session_state:
    st.session_state.current_question = None
if 'show_answer' not in st.session_state:
    st.session_state.show_answer = False
if 'study_session' not in st.session_state:
    st.session_state.study_session = None
if 'session_stats' not in st.session_state:
    st.session_state.session_stats = {
        'questions_answered': 0,
        'correct_answers': 0,
        'sections_studied': set(),
        'start_time': None
    }
if 'page' not in st.session_state:
    st.session_state.page = 'dashboard'

# Main header
st.markdown('<div class="main-header">SAT Prep Oman - Ultra Advanced</div>', unsafe_allow_html=True)
st.write("Next-generation SAT preparation with AI, machine learning, and personalized learning paths")

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Dashboard",
    "Practice",
    "Analytics",
    "Recommendations",
    "Study Plan",
    "Collaboration",
    "AI Tools",
    "Settings"
])

# Update session state
st.session_state.page = page

# Dashboard Page
if page == "Dashboard":
    st.markdown('<div class="section-header">Personal Dashboard</div>', unsafe_allow_html=True)
    
    # Get user stats
    user_stats = sat.get_user_stats(st.session_state.user_id)
    
    if user_stats:
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall = user_stats['overall']
            accuracy = (overall[1] / overall[0]) * 100 if overall[0] > 0 else 0
            st.markdown(f"""
            <div class="metric-card">
                <h3>{overall[0]}</h3>
                <p>Questions Answered</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{accuracy:.1f}%</h3>
                <p>Overall Accuracy</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{user_stats['overall'][2]:.1f}s</h3>
                <p>Avg. Time per Question</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(user_stats['recent_sessions'])}</h3>
                <p>Study Sessions</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Section performance
        st.markdown('<div class="section-header">Section Performance</div>', unsafe_allow_html=True)
        
        if user_stats['sections']:
            sections = [s[0] for s in user_stats['sections']]
            accuracies = [s[3] for s in user_stats['sections']]
            
            fig = go.Figure(data=[
                go.Bar(name='Accuracy', x=sections, y=accuracies, marker_color='#3498db')
            ])
            fig.update_layout(
                title="Section-wise Accuracy",
                yaxis_title="Accuracy (%)",
                yaxis=dict(range=[0, 100])
            )
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("Start practicing to see your dashboard statistics!")

# Practice Page
elif page == "Practice":
    st.markdown('<div class="section-header">Practice Questions</div>', unsafe_allow_html=True)
    
    # Study session controls
    col1, col2 = st.columns(2)
    
    with col1:
        if not st.session_state.study_session:
            if st.button("Start Study Session", key="start_session"):
                session_id = sat.start_study_session(st.session_state.user_id, "Streamlit User")
                st.session_state.study_session = session_id
                st.session_state.session_stats = {
                    'questions_answered': 0,
                    'correct_answers': 0,
                    'sections_studied': set(),
                    'start_time': time.time()
                }
                st.success("Study session started!")
        else:
            if st.button("End Study Session", key="end_session"):
                sat.end_study_session(
                    st.session_state.study_session,
                    st.session_state.session_stats['questions_answered'],
                    st.session_state.session_stats['correct_answers'],
                    ','.join(st.session_state.session_stats['sections_studied'])
                )
                st.session_state.study_session = None
                st.success("Study session ended!")
    
    with col2:
        if st.session_state.study_session:
            duration = int(time.time() - st.session_state.session_stats['start_time'])
            accuracy = (st.session_state.session_stats['correct_answers'] / 
                       st.session_state.session_stats['questions_answered']) * 100 if st.session_state.session_stats['questions_answered'] > 0 else 0
            
            st.metric("Session Duration", f"{duration // 60}m {duration % 60}s")
            st.metric("Session Accuracy", f"{accuracy:.1f}%")
    
    # Question selection
    st.markdown("### Select Question Type")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        question_mode = st.selectbox("Mode", ["Previous Year Questions", "AI Generated", "Adaptive"])
    
    with col2:
        section = st.selectbox("Section", ["math", "reading", "writing"])
    
    with col3:
        if question_mode == "AI Generated":
            difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
            topic = st.text_input("Specific Topic (optional)")
        else:
            difficulty = st.selectbox("Difficulty", ["any", "easy", "medium", "hard"])
            topic = None
    
    # Get question button
    if st.button("Get Question", key="get_question"):
        with st.spinner("Loading question..."):
            if question_mode == "Previous Year Questions":
                diff_map = {'easy': 1, 'medium': 2, 'hard': 3}
                diff = diff_map.get(difficulty, None) if difficulty != "any" else None
                question = sat.get_pyq(section, diff, st.session_state.user_id)
            elif question_mode == "AI Generated":
                diff_map = {'easy': 1, 'medium': 2, 'hard': 3}
                diff = diff_map[difficulty]
                question = sat.generate_new_question(section, diff, topic)
            else:  # Adaptive
                question = sat.get_adaptive_question(st.session_state.user_id, section)
            
            if question:
                st.session_state.current_question = question
                st.session_state.show_answer = False
            else:
                st.error("No questions available for this selection")
    
    # Display question
    if st.session_state.current_question:
        q = st.session_state.current_question
        
        st.markdown(f"### {question_mode} - {section.capitalize()}")
        
        # Language toggle
        lang = st.radio("Language", ["English", "Arabic"], key="lang_toggle")
        
        if lang == "English":
            st.markdown(f"**Question:** {q.get('question_en', q.get('question', ''))}")
            if q.get('passage_en'):
                st.markdown(f"**Passage:** {q['passage_en']}")
            options = q.get('options_en', q.get('options', []))
            explanation = q.get('explanation_en', q.get('explanation', ''))
        else:
            st.markdown(f"**Question:** {q.get('question_ar', q.get('question_ar', ''))}")
            if q.get('passage_ar'):
                st.markdown(f"**Passage:** {q['passage_ar']}")
            options = q.get('options_ar', q.get('options_ar', []))
            explanation = q.get('explanation_ar', q.get('explanation_ar', ''))
        
        # Display options
        user_answer = st.radio("Select your answer:", options, key="answer_radio")
        
        # Submit button
        if st.button("Submit Answer", key="submit_answer"):
            # Check answer
            correct_answer = q.get('answer')
            is_correct = user_answer == correct_answer
            
            # Update session stats
            if st.session_state.study_session:
                st.session_state.session_stats['questions_answered'] += 1
                if is_correct:
                    st.session_state.session_stats['correct_answers'] += 1
                st.session_state.session_stats['sections_studied'].add(section)
            
            # Record answer
            sat.record_user_answer(
                st.session_state.user_id,
                "Streamlit User",
                q['id'],
                is_correct,
                0  # Time tracking not implemented
            )
            
            # Show result
            if is_correct:
                st.success(f"✅ Correct! {explanation}")
            else:
                st.error(f"❌ Incorrect! The correct answer is: {correct_answer}\n\n{explanation}")
            
            st.session_state.show_answer = True

# AI Tools Page
elif page == "AI Tools":
    st.markdown('<div class="section-header">AI-Powered Tools</div>', unsafe_allow_html=True)
    
    # Concept explanation
    st.markdown("### Concept Explainer")
    
    concept = st.text_input("Enter a concept to explain")
    
    if st.button("Explain Concept", key="explain_concept"):
        if concept:
            with st.spinner("Generating explanation..."):
                explanation = nlp.generate_explanation(concept, "", "intermediate")
                st.success(explanation)
    
    # Question generation
    st.markdown("### AI Question Generator")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        gen_section = st.selectbox("Section", ["math", "reading", "writing"])
    
    with col2:
        gen_difficulty = st.selectbox("Difficulty", ["easy", "medium", "hard"])
    
    with col3:
        gen_topic = st.text_input("Specific Topic")
    
    if st.button("Generate Question", key="ai_generate"):
        with st.spinner("Generating question..."):
            diff_map = {'easy': 1, 'medium': 2, 'hard': 3}
            question = sat.generate_new_question(gen_section, diff_map[gen_difficulty], gen_topic)
            
            if question:
                st.markdown(f"**Question:** {question['question']}")
                if question.get('passage'):
                    st.markdown(f"**Passage:** {question['passage']}")
                
                st.markdown("**Options:**")
                for i, opt in enumerate(question['options']):
                    st.write(f"{chr(65+i)}. {opt}")
                
                st.markdown(f"**Answer:** {question['answer']}")
                st.markdown(f"**Explanation:** {question['explanation']}")
            else:
                st.error("Could not generate question")
    
    # Translation tool
    st.markdown("### Advanced Translation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        translate_text = st.text_area("Text to Translate", height=150)
    
    with col2:
        translate_target = st.selectbox("Translate to", ["Arabic", "English"])
        preserve_meaning = st.checkbox("Preserve Educational Meaning")
        
        if st.button("Translate", key="translate_text"):
            if translate_text:
                lang_code = 'ar' if translate_target == "Arabic" else 'en'
                
                if preserve_meaning:
                    translation = nlp.translate_complex_concepts(translate_text, lang_code)
                else:
                    translation = sat.translate(translate_text, lang_code)
                
                st.success(translation)

# Footer
st.markdown("---")
st.markdown("SAT Prep Oman - Ultra Advanced Edition | Built with ❤️ for Omani Students")
