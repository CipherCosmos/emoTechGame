from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import logging
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# FastAPI app
app = FastAPI(title="Emotech Quiz Game API")
api_router = APIRouter(prefix="/api")

# Database Collections
organizers_collection = db.organizers
games_collection = db.games
questions_collection = db.questions
participants_collection = db.participants
answers_collection = db.answers
cheat_logs_collection = db.cheat_logs

# Pydantic Models
class OrganizerLogin(BaseModel):
    username: str
    password: str

class CreateGame(BaseModel):
    organizer_id: str
    title: str = "Quiz Game"

class CreateQuestion(BaseModel):
    type: str  # MCQ, INPUT, TRUE_FALSE, SCRAMBLED
    text: str
    options: List[str] = []
    correct_answer: str
    image_url: Optional[str] = None
    hint: Optional[str] = None
    order: int = 1

class CreateParticipant(BaseModel):
    game_code: str
    name: str

class SubmitAnswer(BaseModel):
    participant_id: str
    question_id: str
    answer: Any
    time_taken: int = 0
    used_hint: bool = False

class CheatDetection(BaseModel):
    participant_id: str
    type: str  # TAB_SWITCH, COPY_ATTEMPT, DEV_TOOLS
    details: Dict = {}

# Helper Functions
def generate_game_code():
    """Generate a 6-character game code"""
    return str(uuid.uuid4())[:6].upper()

def get_current_timestamp():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)

def clean_mongodb_doc(doc):
    """Remove MongoDB ObjectId for JSON serialization"""
    if doc and '_id' in doc:
        del doc['_id']
    return doc

# REST API Routes
@api_router.get("/")
async def root():
    return {"message": "Emotech Quiz Game API"}

@api_router.post("/organizer/login")
async def organizer_login(data: OrganizerLogin):
    """Simple organizer login"""
    if data.username and data.password:
        organizer_id = str(uuid.uuid4())
        organizer = {
            'id': organizer_id,
            'username': data.username,
            'created_at': get_current_timestamp()
        }
        
        await organizers_collection.insert_one(organizer)
        
        return {
            'success': True,
            'organizer_id': organizer_id,
            'username': data.username
        }
    
    raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.post("/games")
async def create_game(data: CreateGame):
    """Create a new game"""
    if not data.organizer_id:
        raise HTTPException(status_code=400, detail="Organizer ID required")
    
    game_code = generate_game_code()
    game = {
        'code': game_code,
        'title': data.title,
        'organizer_id': data.organizer_id,
        'status': 'waiting',  # waiting, in_progress, completed
        'created_at': get_current_timestamp(),
        'started_at': None,
        'ended_at': None,
        'settings': {
            'question_time_limit': 30,
            'hint_penalty': 15,
            'cheat_penalty': 10
        }
    }
    
    await games_collection.insert_one(game)
    
    return {
        'success': True,
        'game_code': game_code,
        'game': clean_mongodb_doc(dict(game))
    }

@api_router.post("/games/{game_code}/questions")
async def add_question(game_code: str, data: CreateQuestion):
    """Add a question to a game"""
    game = await games_collection.find_one({'code': game_code})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    question = {
        'id': str(uuid.uuid4()),
        'game_code': game_code,
        'type': data.type,
        'text': data.text,
        'options': data.options,
        'correct_answer': data.correct_answer,
        'image_url': data.image_url,
        'hint': data.hint,
        'order': data.order,
        'created_at': get_current_timestamp()
    }
    
    await questions_collection.insert_one(question)
    
    return {
        'success': True,
        'question': clean_mongodb_doc(dict(question))
    }

@api_router.get("/games/{game_code}/questions")
async def get_questions(game_code: str):
    """Get all questions for a game"""
    questions = await questions_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).sort('order', 1).to_list(length=None)
    
    return {
        'success': True,
        'questions': questions
    }

@api_router.post("/participants")
async def create_participant(data: CreateParticipant):
    """Create a participant for a game"""
    # Check if game exists
    game = await games_collection.find_one({'code': data.game_code})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Check if name is already taken
    existing_participant = await participants_collection.find_one({
        'game_code': data.game_code,
        'name': data.name
    })
    
    if existing_participant:
        raise HTTPException(status_code=400, detail="Name already taken")
    
    # Create participant
    participant_id = str(uuid.uuid4())
    participant = {
        'id': participant_id,
        'game_code': data.game_code,
        'name': data.name,
        'avatar': f'https://api.dicebear.com/7.x/avataaars/svg?seed={data.name}',
        'joined_at': get_current_timestamp(),
        'total_score': 0,
        'answers': [],
        'cheat_flags': {
            'tab_switches': 0,
            'copy_attempts': 0,
            'dev_tools_attempts': 0
        },
        'is_active': True
    }
    
    await participants_collection.insert_one(participant)
    
    return {
        'success': True,
        'participant': clean_mongodb_doc(dict(participant)),
        'game': clean_mongodb_doc(dict(game))
    }

@api_router.post("/games/{game_code}/start")
async def start_game(game_code: str):
    """Start a game"""
    game = await games_collection.find_one({'code': game_code})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    # Update game status
    await games_collection.update_one(
        {'code': game_code},
        {
            '$set': {
                'status': 'in_progress',
                'started_at': get_current_timestamp()
            }
        }
    )
    
    return {'success': True}

@api_router.get("/games/{game_code}")
async def get_game(game_code: str):
    """Get game details"""
    game = await games_collection.find_one({'code': game_code}, {'_id': 0})
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    
    return {
        'success': True,
        'game': game
    }

@api_router.get("/games/{game_code}/participants")
async def get_participants(game_code: str):
    """Get all participants for a game"""
    participants = await participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).to_list(length=None)
    
    return {
        'success': True,
        'participants': participants
    }

@api_router.get("/games/{game_code}/leaderboard")
async def get_leaderboard(game_code: str):
    """Get leaderboard for a game"""
    participants = await participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).sort('total_score', -1).to_list(length=None)
    
    return {
        'success': True,
        'leaderboard': participants
    }

@api_router.post("/answers")
async def submit_answer(data: SubmitAnswer):
    """Submit an answer"""
    # Get participant and question
    participant = await participants_collection.find_one({'id': data.participant_id})
    question = await questions_collection.find_one({'id': data.question_id})
    
    if not participant or not question:
        raise HTTPException(status_code=404, detail="Participant or question not found")
    
    # Check if already answered
    existing_answer = next(
        (a for a in participant.get('answers', []) if a['question_id'] == data.question_id),
        None
    )
    
    if existing_answer:
        raise HTTPException(status_code=400, detail="Already answered this question")
    
    # Calculate score
    base_score = 100
    time_bonus = max(0, 30 - data.time_taken) if data.time_taken < 30 else 0
    hint_penalty = 15 if data.used_hint else 0
    
    # Check if answer is correct
    is_correct = False
    if question['type'] == 'MCQ':
        is_correct = data.answer == question['correct_answer']
    elif question['type'] == 'TRUE_FALSE':
        is_correct = str(data.answer).lower() == str(question['correct_answer']).lower()
    elif question['type'] == 'INPUT':
        is_correct = str(data.answer).lower().strip() == str(question['correct_answer']).lower().strip()
    elif question['type'] == 'SCRAMBLED':
        is_correct = str(data.answer).lower().strip() == str(question['correct_answer']).lower().strip()
    
    score = (base_score + time_bonus - hint_penalty) if is_correct else 0
    
    # Create answer record
    answer_record = {
        'question_id': data.question_id,
        'answer': data.answer,
        'is_correct': is_correct,
        'score': score,
        'time_taken': data.time_taken,
        'used_hint': data.used_hint,
        'submitted_at': get_current_timestamp()
    }
    
    # Update participant
    await participants_collection.update_one(
        {'id': data.participant_id},
        {
            '$push': {'answers': answer_record},
            '$inc': {'total_score': score}
        }
    )
    
    # Store answer in answers collection
    await answers_collection.insert_one({
        'id': str(uuid.uuid4()),
        'participant_id': data.participant_id,
        'game_code': participant['game_code'],
        'question_id': data.question_id,
        'answer': data.answer,
        'is_correct': is_correct,
        'score': score,
        'time_taken': data.time_taken,
        'used_hint': data.used_hint,
        'submitted_at': get_current_timestamp()
    })
    
    return {
        'success': True,
        'score': score,
        'is_correct': is_correct,
        'total_score': participant['total_score'] + score
    }

@api_router.post("/cheat-detected")
async def handle_cheat_detected(data: CheatDetection):
    """Handle cheat detection"""
    participant = await participants_collection.find_one({'id': data.participant_id})
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    # Log cheat attempt
    cheat_log = {
        'id': str(uuid.uuid4()),
        'participant_id': data.participant_id,
        'game_code': participant['game_code'],
        'type': data.type,
        'timestamp': get_current_timestamp(),
        'details': data.details
    }
    
    await cheat_logs_collection.insert_one(cheat_log)
    
    # Update participant cheat flags
    flag_key = f'cheat_flags.{data.type.lower()}s'
    await participants_collection.update_one(
        {'id': data.participant_id},
        {'$inc': {flag_key: 1}}
    )
    
    # Apply penalty
    penalty = 10 if data.type in ['TAB_SWITCH', 'COPY_ATTEMPT'] else 20
    await participants_collection.update_one(
        {'id': data.participant_id},
        {'$inc': {'total_score': -penalty}}
    )
    
    return {
        'success': True,
        'penalty': penalty
    }

# Include the API router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://emotech.vercel.app",
        "https://emotechv1.vercel.app",
        "https://emotech-6jlt.onrender.com",
        "https://emotechv1.onrender.com",
        "http://localhost:3000",  # For local development
        "http://localhost:8001",  # For local development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
