import discord
from discord.ext import commands
import os
import time
import asyncio
import json
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from sat_utils import SATPrep
from analytics_engine import AnalyticsEngine
from recommendation_engine import RecommendationEngine
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize components
sat = SATPrep()
analytics = AnalyticsEngine(None)
recommender = RecommendationEngine(None)

# Active sessions
active_quizzes = {}
study_sessions = {}
collaboration_rooms = {}

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    print('Advanced SAT Prep Bot is ready!')
    await bot.change_presence(activity=discord.Game(name="SAT Preparation | !help"))

@bot.command()
async def help(ctx):
    """Show help menu"""
    embed = discord.Embed(
        title="SAT Prep Bot - Advanced Commands",
        description="Comprehensive SAT preparation for Omani students",
        color=0x3498db
    )
    
    embed.add_field(name="📚 Practice Commands", value="""
    `!pyq <section> [difficulty]` - Get previous year question
    `!newq <section> [difficulty] [topic]` - Generate new question
    `!adaptive <section>` - Get adaptive question
    `!quiz <section> [count]` - Start a quiz
    """, inline=False)
    
    embed.add_field(name="📊 Analytics Commands", value="""
    `!stats` - Show your statistics
    `!report` - Generate performance report
    `!trends` - Show performance trends
    `!weak` - Show weak areas
    `!compare <user>` - Compare with another user
    """, inline=False)
    
    embed.add_field(name="🎯 Personalization Commands", value="""
    `!recommend` - Get personalized recommendations
    `!plan [days]` - Generate study plan
    `!goals` - Set learning goals
    `!profile` - View your profile
    """, inline=False)
    
    embed.add_field(name="🤝 Collaboration Commands", value="""
    `!studyroom create` - Create study room
    `!studyroom join <id>` - Join study room
    `!studyroom leave` - Leave study room
    `!challenge <user> <section>` - Challenge another user
    """, inline=False)
    
    embed.add_field(name="🌐 Translation Commands", value="""
    `!translate <text>` - Translate text
    `!explain <concept>` - Explain a concept
    `!define <term>` - Define a term
    """, inline=False)
    
    embed.add_field(name="⚙️ Session Commands", value="""
    `!startstudy` - Start study session
    `!endstudy` - End study session
    `!pause` - Pause current session
    `!resume` - Resume paused session
    """, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def pyq(ctx, section: str, difficulty: str = None):
    """Get a previous year question with adaptive selection"""
    diff_map = {'easy': 1, 'medium': 2, 'hard': 3}
    diff = diff_map.get(difficulty.lower(), None) if difficulty else None
    
    question = sat.get_pyq(section, diff, str(ctx.author.id))
    if not question:
        await ctx.send(f"No questions found for section: {section}")
        return
    
    # Create interactive embed
    embed = discord.Embed(
        title=f"PYQ - {section.capitalize()}",
        description=f"Difficulty: {difficulty or 'Adaptive'}",
        color=0x3498db
    )
    
    embed.add_field(name="Question", value=question['question_en'], inline=False)
    
    if question.get('passage_en'):
        embed.add_field(name="Passage", value=question['passage_en'], inline=False)
    
    # Add options as buttons
    options = question['options_en']
    view = QuestionView(ctx.author.id, question, section, 'pyq')
    
    for i, opt in enumerate(options):
        embed.add_field(name=f"Option {chr(65+i)}", value=opt, inline=False)
    
    await ctx.send(embed=embed, view=view)

@bot.command()
async def newq(ctx, section: str, difficulty: str = 'medium', *, topic: str = None):
    """Generate a new AI question"""
    diff_map = {'easy': 1, 'medium': 2, 'hard': 3}
    diff = diff_map.get(difficulty.lower(), 2)
    
    await ctx.send("🤖 Generating a new question... This may take a moment.")
    
    question = sat.generate_new_question(section, diff, topic)
    if not question:
        await ctx.send(f"Could not generate question for section: {section}")
        return
    
    # Create interactive embed
    embed = discord.Embed(
        title=f"AI-Generated Question - {section.capitalize()}",
        description=f"Difficulty: {difficulty} | Topic: {topic or 'General'}",
        color=0x2ecc71
    )
    
    embed.add_field(name="Question", value=question['question'], inline=False)
    
    if question.get('passage'):
        embed.add_field(name="Passage", value=question['passage'], inline=False)
    
    # Add options as buttons
    options = question['options']
    view = QuestionView(ctx.author.id, question, section, 'newq')
    
    for i, opt in enumerate(options):
        embed.add_field(name=f"Option {chr(65+i)}", value=opt, inline=False)
    
    await ctx.send(embed=embed, view=view)

@bot.command()
async def adaptive(ctx, section: str):
    """Get an adaptive question based on user performance"""
    await ctx.send("🧠 Analyzing your performance to generate an adaptive question...")
    
    # Get adaptive question
    question = sat.get_adaptive_question(str(ctx.author.id), section)
    if not question:
        await ctx.send("Could not generate adaptive question. Try !pyq or !newq instead.")
        return
    
    # Create embed
    embed = discord.Embed(
        title=f"Adaptive Question - {section.capitalize()}",
        description="Personalized based on your performance",
        color=0x9b59b6
    )
    
    embed.add_field(name="Question", value=question['question_en'], inline=False)
    
    if question.get('passage_en'):
        embed.add_field(name="Passage", value=question['passage_en'], inline=False)
    
    # Add options as buttons
    options = question['options_en']
    view = QuestionView(ctx.author.id, question, section, 'adaptive')
    
    for i, opt in enumerate(options):
        embed.add_field(name=f"Option {chr(65+i)}", value=opt, inline=False)
    
    await ctx.send(embed=embed, view=view)

@bot.command()
async def stats(ctx):
    """Show comprehensive statistics"""
    stats = sat.get_user_stats(str(ctx.author.id))
    if not stats:
        await ctx.send("You haven't answered any questions yet!")
        return
    
    # Create detailed stats embed
    embed = discord.Embed(
        title=f"📊 Statistics for {ctx.author.name}",
        color=0x3498db
    )
    
    # Overall stats
    overall = stats['overall']
    accuracy = (overall[1] / overall[0]) * 100 if overall[0] > 0 else 0
    
    embed.add_field(name="📈 Overall Performance", value=f"""
    **Questions Answered:** {overall[0]}
    **Correct Answers:** {overall[1]}
    **Accuracy:** {accuracy:.1f}%
    **Avg. Time:** {overall[2]:.1f}s
    """, inline=False)
    
    # Section-wise stats
    section_text = ""
    for section, total, correct, avg_time in stats['sections']:
        sec_accuracy = (correct / total) * 100 if total > 0 else 0
        section_text += f"**{section.capitalize()}**: {correct}/{total} ({sec_accuracy:.1f}%) - Avg: {avg_time:.1f}s\n"
    
    if section_text:
        embed.add_field(name="📚 Section-wise Performance", value=section_text, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def recommend(ctx):
    """Get personalized recommendations"""
    recommendations = recommender.get_personalized_recommendations(str(ctx.author.id))
    
    embed = discord.Embed(
        title=f"🎯 Personalized Recommendations for {ctx.author.name}",
        color=0x9b59b6
    )
    
    for i, rec in enumerate(recommendations[:5], 1):
        emoji = "🔴" if rec['priority'] == 'high' else "🟡" if rec['priority'] == 'medium' else "🟢"
        embed.add_field(name=f"{emoji} Recommendation {i}", value=rec['reason'], inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def translate(ctx, *, text: str):
    """Translate text between Arabic and English"""
    translation = sat.translate(text)
    await ctx.send(f"Translation: {translation}")

@bot.command()
async def explain(ctx, *, concept: str):
    """Explain a concept using AI"""
    await ctx.send("🤖 Generating explanation...")
    
    # Use AI to explain concept
    explanation = sat.explain_concept(concept)
    
    embed = discord.Embed(
        title=f"📖 Explanation: {concept}",
        description=explanation,
        color=0x3498db
    )
    
    await ctx.send(embed=embed)

# View classes for interactive buttons
class QuestionView(discord.ui.View):
    def __init__(self, user_id, question, section, question_type):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.question = question
        self.section = section
        self.question_type = question_type
        self.start_time = time.time()
    
    async def on_timeout(self):
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)
    
    @discord.ui.button(label="A", style=discord.ButtonStyle.secondary)
    async def button_a(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 0)
    
    @discord.ui.button(label="B", style=discord.ButtonStyle.secondary)
    async def button_b(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 1)
    
    @discord.ui.button(label="C", style=discord.ButtonStyle.secondary)
    async def button_c(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 2)
    
    @discord.ui.button(label="D", style=discord.ButtonStyle.secondary)
    async def button_d(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_answer(interaction, 3)
    
    async def process_answer(self, interaction, option_index):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This is not your question!", ephemeral=True)
            return
        
        # Determine correct answer
        if self.question_type == 'newq':
            correct_answer = self.question['answer']
            options = self.question['options']
            try:
                correct_index = options.index(correct_answer)
            except ValueError:
                correct_index = None
        else:
            correct_answer = self.question['answer']
            options = self.question['options_en']
            try:
                correct_index = options.index(correct_answer)
            except ValueError:
                correct_index = None
        
        time_taken = int(time.time() - self.start_time)
        
        if correct_index is not None and option_index == correct_index:
            await interaction.response.send_message(f"✅ Correct! {self.question.get('explanation_en', self.question.get('explanation', ''))}")
            is_correct = True
        else:
            await interaction.response.send_message(f"❌ Wrong! The correct answer is {chr(65 + correct_index) if correct_index is not None else 'unknown'}. {self.question.get('explanation_en', self.question.get('explanation', ''))}")
            is_correct = False
        
        # Record answer
        sat.record_user_answer(
            str(self.user_id),
            interaction.user.name,
            self.question['id'],
            is_correct,
            time_taken
        )
        
        # Update study session
        if self.user_id in study_sessions:
            session = study_sessions[self.user_id]
            session['questions_answered'] += 1
            if is_correct:
                session['correct_answers'] += 1
            if self.section not in session['sections_studied']:
                session['sections_studied'].append(self.section)
        
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        await interaction.message.edit(view=self)

bot.run(TOKEN)
