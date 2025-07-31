from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import uuid
import json
import asyncio
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

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.game_rooms: Dict[str, List[str]] = {}
        self.admin_connections: Dict[str, List[str]] = {}
        self.live_connections: Dict[str, List[str]] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        await websocket.accept()
        self.active_connections[connection_id] = websocket

    def disconnect(self, connection_id: str):
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove from all rooms
        for game_code in list(self.game_rooms.keys()):
            if connection_id in self.game_rooms[game_code]:
                self.game_rooms[game_code].remove(connection_id)
                if not self.game_rooms[game_code]:
                    del self.game_rooms[game_code]
        
        for game_code in list(self.admin_connections.keys()):
            if connection_id in self.admin_connections[game_code]:
                self.admin_connections[game_code].remove(connection_id)
                if not self.admin_connections[game_code]:
                    del self.admin_connections[game_code]
        
        for game_code in list(self.live_connections.keys()):
            if connection_id in self.live_connections[game_code]:
                self.live_connections[game_code].remove(connection_id)
                if not self.live_connections[game_code]:
                    del self.live_connections[game_code]

    def join_game_room(self, connection_id: str, game_code: str):
        if game_code not in self.game_rooms:
            self.game_rooms[game_code] = []
        if connection_id not in self.game_rooms[game_code]:
            self.game_rooms[game_code].append(connection_id)

    def join_admin_room(self, connection_id: str, game_code: str):
        if game_code not in self.admin_connections:
            self.admin_connections[game_code] = []
        if connection_id not in self.admin_connections[game_code]:
            self.admin_connections[game_code].append(connection_id)

    def join_live_room(self, connection_id: str, game_code: str):
        if game_code not in self.live_connections:
            self.live_connections[game_code] = []
        if connection_id not in self.live_connections[game_code]:
            self.live_connections[game_code].append(connection_id)

    async def send_to_connection(self, connection_id: str, message: dict):
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_text(json.dumps(message))
            except:
                self.disconnect(connection_id)

    async def broadcast_to_game(self, game_code: str, message: dict):
        if game_code in self.game_rooms:
            for connection_id in self.game_rooms[game_code].copy():
                await self.send_to_connection(connection_id, message)

    async def broadcast_to_admin(self, game_code: str, message: dict):
        if game_code in self.admin_connections:
            for connection_id in self.admin_connections[game_code].copy():
                await self.send_to_connection(connection_id, message)

    async def broadcast_to_live(self, game_code: str, message: dict):
        if game_code in self.live_connections:
            for connection_id in self.live_connections[game_code].copy():
                await self.send_to_connection(connection_id, message)

manager = ConnectionManager()

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

class SubmitAnswer(BaseModel):
    participant_id: str
    question_id: str
    answer: Any
    time_taken: int = 0
    used_hint: bool = False

# Helper Functions
def generate_game_code():
    """Generate a 6-character game code"""
    return str(uuid.uuid4())[:6].upper()

def get_current_timestamp():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)

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
    
    # Remove MongoDB ObjectId for JSON serialization
    game_response = dict(game)
    if '_id' in game_response:
        del game_response['_id']
    
    return {
        'success': True,
        'game_code': game_code,
        'game': game_response
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
    
    # Remove MongoDB ObjectId for JSON serialization
    question_response = dict(question)
    if '_id' in question_response:
        del question_response['_id']
    
    return {
        'success': True,
        'question': question_response
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
    
    # Notify all connected participants
    await manager.broadcast_to_game(game_code, {
        'type': 'game_started',
        'data': {
            'game_code': game_code,
            'message': 'Game has started!'
        }
    })
    
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

# WebSocket endpoint
@app.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    await manager.connect(websocket, connection_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            await handle_websocket_message(connection_id, message)
            
    except WebSocketDisconnect:
        manager.disconnect(connection_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(connection_id)

async def handle_websocket_message(connection_id: str, message: dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get('type')
    data = message.get('data', {})
    
    if message_type == 'join_game':
        await handle_join_game(connection_id, data)
    elif message_type == 'join_admin':
        await handle_join_admin(connection_id, data)
    elif message_type == 'join_live':
        await handle_join_live(connection_id, data)
    elif message_type == 'submit_answer':
        await handle_submit_answer(connection_id, data)
    elif message_type == 'cheat_detected':
        await handle_cheat_detected(connection_id, data)

async def handle_join_game(connection_id: str, data: dict):
    """Handle participant joining a game"""
    game_code = data.get('game_code')
    participant_name = data.get('name')
    
    if not game_code or not participant_name:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Game code and name required'}
        })
        return
    
    # Check if game exists
    game = await games_collection.find_one({'code': game_code})
    if not game:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Game not found'}
        })
        return
    
    # Check if name is already taken
    existing_participant = await participants_collection.find_one({
        'game_code': game_code,
        'name': participant_name
    })
    
    if existing_participant:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Name already taken'}
        })
        return
    
    # Create participant
    participant_id = str(uuid.uuid4())
    participant = {
        'id': participant_id,
        'game_code': game_code,
        'name': participant_name,
        'avatar': f'https://api.dicebear.com/7.x/avataaars/svg?seed={participant_name}',
        'connection_id': connection_id,
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
    
    # Store in database
    await participants_collection.insert_one(participant)
    
    # Remove MongoDB ObjectId for JSON serialization
    participant_response = dict(participant)
    if '_id' in participant_response:
        del participant_response['_id']
    
    # Join game room
    manager.join_game_room(connection_id, game_code)
    
    # Notify participant
    await manager.send_to_connection(connection_id, {
        'type': 'joined_game',
        'data': {
            'success': True,
            'participant': participant,
            'game': game
        }
    })
    
    # Notify admin
    await manager.broadcast_to_admin(game_code, {
        'type': 'participant_joined',
        'data': {'participant': participant}
    })

async def handle_join_admin(connection_id: str, data: dict):
    """Handle organizer joining admin room"""
    game_code = data.get('game_code')
    organizer_id = data.get('organizer_id')
    
    if not game_code or not organizer_id:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Game code and organizer ID required'}
        })
        return
    
    # Verify organizer owns this game
    game = await games_collection.find_one({
        'code': game_code,
        'organizer_id': organizer_id
    })
    
    if not game:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Access denied'}
        })
        return
    
    # Join admin room
    manager.join_admin_room(connection_id, game_code)
    
    # Get current participants
    participants = await participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).to_list(length=None)
    
    await manager.send_to_connection(connection_id, {
        'type': 'admin_joined',
        'data': {
            'success': True,
            'game': game,
            'participants': participants
        }
    })

async def handle_join_live(connection_id: str, data: dict):
    """Handle public viewer joining live view"""
    game_code = data.get('game_code')
    
    if not game_code:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Game code required'}
        })
        return
    
    # Check if game exists
    game = await games_collection.find_one({'code': game_code})
    if not game:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Game not found'}
        })
        return
    
    # Join live room
    manager.join_live_room(connection_id, game_code)
    
    # Get current leaderboard
    participants = await participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).sort('total_score', -1).to_list(length=None)
    
    await manager.send_to_connection(connection_id, {
        'type': 'live_joined',
        'data': {
            'success': True,
            'game': game,
            'leaderboard': participants
        }
    })

async def handle_submit_answer(connection_id: str, data: dict):
    """Handle answer submission"""
    participant_id = data.get('participant_id')
    question_id = data.get('question_id')
    answer = data.get('answer')
    time_taken = data.get('time_taken', 0)
    used_hint = data.get('used_hint', False)
    
    if not all([participant_id, question_id, answer is not None]):
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Missing required data'}
        })
        return
    
    # Get participant and question
    participant = await participants_collection.find_one({'id': participant_id})
    question = await questions_collection.find_one({'id': question_id})
    
    if not participant or not question:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Participant or question not found'}
        })
        return
    
    # Check if already answered
    existing_answer = next(
        (a for a in participant.get('answers', []) if a['question_id'] == question_id),
        None
    )
    
    if existing_answer:
        await manager.send_to_connection(connection_id, {
            'type': 'error',
            'data': {'message': 'Already answered this question'}
        })
        return
    
    # Calculate score
    base_score = 100
    time_bonus = max(0, 30 - time_taken) if time_taken < 30 else 0
    hint_penalty = 15 if used_hint else 0
    
    # Check if answer is correct
    is_correct = False
    if question['type'] == 'MCQ':
        is_correct = answer == question['correct_answer']
    elif question['type'] == 'TRUE_FALSE':
        is_correct = str(answer).lower() == str(question['correct_answer']).lower()
    elif question['type'] == 'INPUT':
        is_correct = str(answer).lower().strip() == str(question['correct_answer']).lower().strip()
    elif question['type'] == 'SCRAMBLED':
        is_correct = str(answer).lower().strip() == str(question['correct_answer']).lower().strip()
    
    score = (base_score + time_bonus - hint_penalty) if is_correct else 0
    
    # Create answer record
    answer_record = {
        'question_id': question_id,
        'answer': answer,
        'is_correct': is_correct,
        'score': score,
        'time_taken': time_taken,
        'used_hint': used_hint,
        'submitted_at': get_current_timestamp()
    }
    
    # Update participant
    await participants_collection.update_one(
        {'id': participant_id},
        {
            '$push': {'answers': answer_record},
            '$inc': {'total_score': score}
        }
    )
    
    # Store answer in answers collection
    await answers_collection.insert_one({
        'id': str(uuid.uuid4()),
        'participant_id': participant_id,
        'game_code': participant['game_code'],
        'question_id': question_id,
        'answer': answer,
        'is_correct': is_correct,
        'score': score,
        'time_taken': time_taken,
        'used_hint': used_hint,
        'submitted_at': get_current_timestamp()
    })
    
    # Notify participant
    await manager.send_to_connection(connection_id, {
        'type': 'answer_submitted',
        'data': {
            'success': True,
            'score': score,
            'is_correct': is_correct
        }
    })
    
    # Update live leaderboard
    updated_participant = await participants_collection.find_one({'id': participant_id}, {'_id': 0})
    await manager.broadcast_to_live(participant['game_code'], {
        'type': 'leaderboard_update',
        'data': {'participant': updated_participant}
    })
    
    # Notify admin
    await manager.broadcast_to_admin(participant['game_code'], {
        'type': 'answer_received',
        'data': {
            'participant_id': participant_id,
            'question_id': question_id,
            'answer': answer,
            'is_correct': is_correct,
            'score': score
        }
    })

async def handle_cheat_detected(connection_id: str, data: dict):
    """Handle cheat detection"""
    participant_id = data.get('participant_id')
    cheat_type = data.get('type')  # TAB_SWITCH, COPY_ATTEMPT, DEV_TOOLS
    
    if not participant_id or not cheat_type:
        return
    
    participant = await participants_collection.find_one({'id': participant_id})
    if not participant:
        return
    
    # Log cheat attempt
    cheat_log = {
        'id': str(uuid.uuid4()),
        'participant_id': participant_id,
        'game_code': participant['game_code'],
        'type': cheat_type,
        'timestamp': get_current_timestamp(),
        'details': data.get('details', {})
    }
    
    await cheat_logs_collection.insert_one(cheat_log)
    
    # Update participant cheat flags
    flag_key = f'cheat_flags.{cheat_type.lower()}s'
    await participants_collection.update_one(
        {'id': participant_id},
        {'$inc': {flag_key: 1}}
    )
    
    # Apply penalty
    penalty = 10 if cheat_type in ['TAB_SWITCH', 'COPY_ATTEMPT'] else 20
    await participants_collection.update_one(
        {'id': participant_id},
        {'$inc': {'total_score': -penalty}}
    )
    
    # Notify admin
    await manager.broadcast_to_admin(participant['game_code'], {
        'type': 'cheat_detected',
        'data': {
            'participant_id': participant_id,
            'type': cheat_type,
            'penalty': penalty,
            'timestamp': get_current_timestamp()
        }
    })

# Include the API router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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