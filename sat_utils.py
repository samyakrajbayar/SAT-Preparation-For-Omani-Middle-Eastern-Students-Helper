import json
import random
import time
from deep_translator import GoogleTranslator
from database import SATDatabase
from ai_generator import AIQuestionGenerator
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

class SATPrep:
    def __init__(self):
        self.db = SATDatabase()
        self.ai_generator = AIQuestionGenerator()
        self.translation_cache = {}
        
        # Load initial questions from JSON if database is empty
        if self._is_database_empty():
            self._load_initial_questions()
    
    def _is_database_empty(self):
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM questions")
        return cursor.fetchone()[0] == 0
    
    def _load_initial_questions(self):
        with open('questions.json', 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        for section, q_list in questions.items():
            for q in q_list:
                self.db.add_question(
                    section=section,
                    question_en=q['question']['en'],
                    question_ar=q['question']['ar'],
                    options_en=[opt['en'] for opt in q['options']],
                    options_ar=[opt['ar'] for opt in q['options']],
                    answer=q['answer'],
                    explanation_en=q['explanation']['en'],
                    explanation_ar=q['explanation']['ar'],
                    difficulty=q.get('difficulty', 2)
                )
    
    def get_pyq(self, section, difficulty=None, user_id=None):
        """Get a previous year question with adaptive difficulty"""
        cursor = self.db.conn.cursor()
        
        # If user_id is provided, get their weak areas
        if user_id:
            weak_areas = self.db.get_weak_areas(user_id)
            if weak_areas:
                # Prioritize questions from weak areas
                weak_sections = [area[0] for area in weak_areas if area[3] < 70]  # Less than 70% accuracy
                if weak_sections:
                    section = random.choice(weak_sections)
        
        # Build query based on parameters
        query = "SELECT * FROM questions WHERE section = ?"
        params = [section]
        
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        
        cursor.execute(query, params)
        questions = cursor.fetchall()
        
        if not questions:
            return None
        
        # Convert to dict
        columns = [desc[0] for desc in cursor.description]
        question = dict(zip(columns, random.choice(questions)))
        
        # Parse JSON fields
        question['options_en'] = json.loads(question['options_en'])
        question['options_ar'] = json.loads(question['options_ar'])
        
        return question
    
    def generate_new_question(self, section, difficulty=2, topic=None):
        """Generate a new question using AI"""
        question_data = self.ai_generator.generate_question(section, difficulty, topic)
        
        if not question_data:
            return None
        
        # Generate Arabic translation
        translation = self.ai_generator.generate_arabic_translation(question_data)
        
        if translation:
            question_data.update(translation)
        
        # Save to database
        question_id = self.db.add_question(
            section=section,
            question_en=question_data['question'],
            question_ar=question_data.get('question_ar', ''),
            options_en=question_data['options'],
            options_ar=question_data.get('options_ar', []),
            answer=question_data['answer'],
            explanation_en=question_data['explanation'],
            explanation_ar=question_data.get('explanation_ar', ''),
            difficulty=question_data['difficulty']
        )
        
        question_data['id'] = question_id
        return question_data
    
    def get_adaptive_question(self, user_id, section):
        """Get an adaptive question based on user performance"""
        # Get user stats
        stats = self.db.get_user_stats(user_id)
        if not stats:
            return self.get_pyq(section)
        
        # Calculate average accuracy
        total_correct = sum(s[1] for s in stats['sections'])
        total_questions = sum(s[0] for s in stats['sections'])
        avg_accuracy = (total_correct / total_questions) * 100 if total_questions > 0 else 50
        
        # Adjust difficulty based on accuracy
        if avg_accuracy > 80:
            difficulty = 3  # Hard
        elif avg_accuracy > 60:
            difficulty = 2  # Medium
        else:
            difficulty = 1  # Easy
        
        return self.get_pyq(section, difficulty, user_id)
    
    def translate(self, text, target_lang='en'):
        """Translate text with caching"""
        cache_key = f"{text}_{target_lang}"
        if cache_key in self.translation_cache:
            return self.translation_cache[cache_key]
        
        try:
            translator = GoogleTranslator(source='auto', target=target_lang)
            translation = translator.translate(text)
            self.translation_cache[cache_key] = translation
            return translation
        except Exception as e:
            print(f"Translation error: {e}")
            return text
    
    def record_user_answer(self, discord_id, username, question_id, is_correct, time_taken):
        """Record user's answer and update progress"""
        user_id = self.db.add_user(discord_id, username)
        self.db.record_answer(user_id, question_id, is_correct, time_taken)
        return user_id
    
    def get_user_stats(self, discord_id):
        """Get comprehensive user statistics"""
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE discord_id = ?", (discord_id,))
        user = cursor.fetchone()
        
        if not user:
            return None
        
        return self.db.get_user_stats(user[0])
    
    def explain_concept(self, concept):
        """Explain a concept using AI"""
        # This would use the AI generator to create an explanation
        prompt = f"Explain the concept of {concept} in simple terms for a high school student preparing for the SAT."
        
        try:
            # In a real implementation, this would call the AI API
            explanation = f"{concept} is an important concept for the SAT. Here's a simple explanation:\n\n1. Definition: [Definition of {concept}]\n2. Importance: Why it matters for the SAT\n3. Example: A practical example\n4. Tips: How to approach questions about {concept}"
            return explanation
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    def close(self):
        self.db.close()
