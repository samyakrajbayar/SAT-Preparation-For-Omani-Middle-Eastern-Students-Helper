import sqlite3
import json
from datetime import datetime

class SATDatabase:
    def __init__(self):
        self.conn = sqlite3.connect('sat_prep.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT UNIQUE,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Questions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT,
            question_en TEXT,
            question_ar TEXT,
            options_en TEXT,
            options_ar TEXT,
            answer TEXT,
            explanation_en TEXT,
            explanation_ar TEXT,
            difficulty INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # User progress table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            question_id INTEGER,
            is_correct BOOLEAN,
            time_taken INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (question_id) REFERENCES questions (id)
        )
        ''')
        
        # Study sessions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            questions_answered INTEGER,
            correct_answers INTEGER,
            sections_studied TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        ''')
        
        self.conn.commit()
    
    def add_user(self, discord_id, username):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (discord_id, username) VALUES (?, ?)",
                (discord_id, username)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            cursor.execute(
                "SELECT id FROM users WHERE discord_id = ?",
                (discord_id,)
            )
            return cursor.fetchone()[0]
    
    def add_question(self, section, question_en, question_ar, options_en, options_ar, 
                    answer, explanation_en, explanation_ar, difficulty):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO questions (section, question_en, question_ar, options_en, options_ar,
                               answer, explanation_en, explanation_ar, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (section, question_en, question_ar, json.dumps(options_en), 
              json.dumps(options_ar), answer, explanation_en, explanation_ar, difficulty))
        self.conn.commit()
        return cursor.lastrowid
    
    def record_answer(self, user_id, question_id, is_correct, time_taken):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO user_progress (user_id, question_id, is_correct, time_taken) VALUES (?, ?, ?, ?)",
            (user_id, question_id, is_correct, time_taken)
        )
        self.conn.commit()
    
    def start_study_session(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO study_sessions (user_id, start_time) VALUES (?, ?)",
            (user_id, datetime.now())
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def end_study_session(self, session_id, questions_answered, correct_answers, sections_studied):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE study_sessions 
        SET end_time = ?, questions_answered = ?, correct_answers = ?, sections_studied = ?
        WHERE id = ?
        ''', (datetime.now(), questions_answered, correct_answers, sections_studied, session_id))
        self.conn.commit()
    
    def get_user_stats(self, user_id):
        cursor = self.conn.cursor()
        
        # Overall stats
        cursor.execute('''
        SELECT 
            COUNT(*) as total_questions,
            SUM(is_correct) as correct_answers,
            AVG(time_taken) as avg_time
        FROM user_progress
        WHERE user_id = ?
        ''', (user_id,))
        overall_stats = cursor.fetchone()
        
        # Section-wise stats
        cursor.execute('''
        SELECT 
            q.section,
            COUNT(*) as total,
            SUM(up.is_correct) as correct,
            AVG(up.time_taken) as avg_time
        FROM user_progress up
        JOIN questions q ON up.question_id = q.id
        WHERE up.user_id = ?
        GROUP BY q.section
        ''', (user_id,))
        section_stats = cursor.fetchall()
        
        # Recent sessions
        cursor.execute('''
        SELECT start_time, end_time, questions_answered, correct_answers, sections_studied
        FROM study_sessions
        WHERE user_id = ?
        ORDER BY start_time DESC
        LIMIT 5
        ''', (user_id,))
        recent_sessions = cursor.fetchall()
        
        return {
            'overall': overall_stats,
            'sections': section_stats,
            'recent_sessions': recent_sessions
        }
    
    def get_weak_areas(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT 
            q.section,
            COUNT(*) as total,
            SUM(up.is_correct) as correct,
            (SUM(up.is_correct) * 100.0 / COUNT(*)) as accuracy
        FROM user_progress up
        JOIN questions q ON up.question_id = q.id
        WHERE up.user_id = ?
        GROUP BY q.section
        ORDER BY accuracy ASC
        ''', (user_id,))
        return cursor.fetchall()
    
    def close(self):
        self.conn.close()
