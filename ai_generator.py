import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

class AIQuestionGenerator:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
    
    def generate_question(self, section, difficulty, topic=None):
        """Generate a new SAT question using OpenAI API"""
        prompt = self._create_prompt(section, difficulty, topic)
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert SAT question creator for Omani students."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            return self._parse_response(response.choices[0].message['content'])
        except Exception as e:
            print(f"Error generating question: {e}")
            return None
    
    def _create_prompt(self, section, difficulty, topic):
        """Create a prompt for the AI based on section and difficulty"""
        difficulty_map = {
            1: "easy",
            2: "medium",
            3: "hard"
        }
        
        section_prompts = {
            "math": f"Create a {difficulty_map.get(difficulty, 'medium')} SAT Math question{' about ' + topic if topic else ''}.",
            "reading": f"Create a {difficulty_map.get(difficulty, 'medium')} SAT Reading question{' about ' + topic if topic else ''}. Include a short passage.",
            "writing": f"Create a {difficulty_map.get(difficulty, 'medium')} SAT Writing question{' about ' + topic if topic else ''}."
        }
        
        base_prompt = section_prompts.get(section, "")
        
        return f"""
        {base_prompt}
        
        The question should be culturally appropriate for Omani students.
        
        Format your response as JSON with the following structure:
        {{
            "question": "The question text",
            "passage": "The passage text (if applicable)",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "answer": "The correct option",
            "explanation": "Explanation of the answer",
            "difficulty": {difficulty}
        }}
        """
    
    def _parse_response(self, response_text):
        """Parse the AI response into a structured format"""
        try:
            # Extract JSON from the response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            
            import json
            return json.loads(json_str)
        except Exception as e:
            print(f"Error parsing response: {e}")
            return None
    
    def generate_arabic_translation(self, question_data):
        """Generate Arabic translation for a question"""
        prompt = f"""
        Translate the following SAT question and its options into Arabic. 
        Maintain the meaning and difficulty level.
        
        Question: {question_data['question']}
        Passage: {question_data.get('passage', '')}
        Options: {', '.join(question_data['options'])}
        Answer: {question_data['answer']}
        Explanation: {question_data['explanation']}
        
        Format your response as JSON:
        {{
            "question_ar": "Arabic translation of the question",
            "passage_ar": "Arabic translation of the passage (if applicable)",
            "options_ar": ["Arabic translation of option A", ...],
            "explanation_ar": "Arabic translation of the explanation"
        }}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert translator for educational content."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return self._parse_response(response.choices[0].message['content'])
        except Exception as e:
            print(f"Error generating translation: {e}")
            return None
