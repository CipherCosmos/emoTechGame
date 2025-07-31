from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room, rooms
from flask_cors import CORS
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime, timezone
import json
from typing import Dict, List
import threading
import time

# Load environment variables
load_dotenv()

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = MongoClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Flask app with SocketIO
app = Flask(__name__)
app.config['SECRET_KEY'] = 'emotech_secret_key_2025'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)
CORS(app)

# Game states and data storage
active_games = {}
connected_users = {}

# Database Collections
organizers_collection = db.organizers
games_collection = db.games
questions_collection = db.questions
participants_collection = db.participants
answers_collection = db.answers
cheat_logs_collection = db.cheat_logs

# Helper Functions
def generate_game_code():
    """Generate a 6-character game code"""
    return str(uuid.uuid4())[:6].upper()

def get_current_timestamp():
    """Get current UTC timestamp"""
    return datetime.now(timezone.utc)

# REST API Routes
@app.route('/api/', methods=['GET'])
def root():
    return jsonify({"message": "Emotech Quiz Game API"})

@app.route('/api/organizer/login', methods=['POST'])
def organizer_login():
    """Simple organizer login - in production, use proper auth"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Simple auth - in production, use proper password hashing
    if username and password:
        organizer_id = str(uuid.uuid4())
        organizer = {
            'id': organizer_id,
            'username': username,
            'created_at': get_current_timestamp()
        }
        
        # Store in database
        organizers_collection.insert_one(organizer)
        
        return jsonify({
            'success': True,
            'organizer_id': organizer_id,
            'username': username
        })
    
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/games', methods=['POST'])
def create_game():
    """Create a new game"""
    data = request.json
    organizer_id = data.get('organizer_id')
    game_title = data.get('title', 'Quiz Game')
    
    if not organizer_id:
        return jsonify({'error': 'Organizer ID required'}), 400
    
    game_code = generate_game_code()
    game = {
        'code': game_code,
        'title': game_title,
        'organizer_id': organizer_id,
        'status': 'waiting',  # waiting, in_progress, completed
        'created_at': get_current_timestamp(),
        'started_at': None,
        'ended_at': None,
        'settings': {
            'question_time_limit': 30,  # seconds
            'hint_penalty': 15,
            'cheat_penalty': 10
        }
    }
    
    # Store in database and memory
    games_collection.insert_one(game)
    active_games[game_code] = game
    
    return jsonify({
        'success': True,
        'game_code': game_code,
        'game': game
    })

@app.route('/api/games/<game_code>/questions', methods=['POST'])
def add_question(game_code):
    """Add a question to a game"""
    data = request.json
    
    if game_code not in active_games:
        return jsonify({'error': 'Game not found'}), 404
    
    question = {
        'id': str(uuid.uuid4()),
        'game_code': game_code,
        'type': data.get('type'),  # MCQ, INPUT, TRUE_FALSE, SCRAMBLED
        'text': data.get('text'),
        'options': data.get('options', []),
        'correct_answer': data.get('correct_answer'),
        'image_url': data.get('image_url'),
        'hint': data.get('hint'),
        'order': data.get('order', 1),
        'created_at': get_current_timestamp()
    }
    
    # Store in database
    questions_collection.insert_one(question)
    
    return jsonify({
        'success': True,
        'question': question
    })

@app.route('/api/games/<game_code>/questions', methods=['GET'])
def get_questions(game_code):
    """Get all questions for a game"""
    questions = list(questions_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).sort('order', 1))
    
    return jsonify({
        'success': True,
        'questions': questions
    })

@app.route('/api/games/<game_code>/start', methods=['POST'])
def start_game(game_code):
    """Start a game"""
    if game_code not in active_games:
        return jsonify({'error': 'Game not found'}), 404
    
    # Update game status
    active_games[game_code]['status'] = 'in_progress'
    active_games[game_code]['started_at'] = get_current_timestamp()
    
    # Update in database
    games_collection.update_one(
        {'code': game_code},
        {
            '$set': {
                'status': 'in_progress',
                'started_at': get_current_timestamp()
            }
        }
    )
    
    # Notify all connected participants
    socketio.emit('game_started', {
        'game_code': game_code,
        'message': 'Game has started!'
    }, room=f'game_{game_code}')
    
    return jsonify({'success': True})

@app.route('/api/games/<game_code>', methods=['GET'])
def get_game(game_code):
    """Get game details"""
    game = games_collection.find_one({'code': game_code}, {'_id': 0})
    if not game:
        return jsonify({'error': 'Game not found'}), 404
    
    return jsonify({
        'success': True,
        'game': game
    })

@app.route('/api/games/<game_code>/participants', methods=['GET'])
def get_participants(game_code):
    """Get all participants for a game"""
    participants = list(participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ))
    
    return jsonify({
        'success': True,
        'participants': participants
    })

@app.route('/api/games/<game_code>/leaderboard', methods=['GET'])
def get_leaderboard(game_code):
    """Get leaderboard for a game"""
    participants = list(participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).sort('total_score', -1))
    
    return jsonify({
        'success': True,
        'leaderboard': participants
    })

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')
    connected_users[request.sid] = {
        'connected_at': get_current_timestamp()
    }

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')
    if request.sid in connected_users:
        del connected_users[request.sid]

@socketio.on('join_game')
def handle_join_game(data):
    """Handle participant joining a game"""
    game_code = data.get('game_code')
    participant_name = data.get('name')
    
    if not game_code or not participant_name:
        emit('error', {'message': 'Game code and name required'})
        return
    
    # Check if game exists
    game = games_collection.find_one({'code': game_code})
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Check if name is already taken
    existing_participant = participants_collection.find_one({
        'game_code': game_code,
        'name': participant_name
    })
    
    if existing_participant:
        emit('error', {'message': 'Name already taken'})
        return
    
    # Create participant
    participant_id = str(uuid.uuid4())
    participant = {
        'id': participant_id,
        'game_code': game_code,
        'name': participant_name,
        'avatar': f'https://api.dicebear.com/7.x/avataaars/svg?seed={participant_name}',
        'socket_id': request.sid,
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
    participants_collection.insert_one(participant)
    
    # Join socket room
    join_room(f'game_{game_code}')
    
    # Update connected users
    connected_users[request.sid] = {
        'participant_id': participant_id,
        'game_code': game_code,
        'name': participant_name,
        'connected_at': get_current_timestamp()
    }
    
    # Notify participant
    emit('joined_game', {
        'success': True,
        'participant': participant,
        'game': game
    })
    
    # Notify organizer
    socketio.emit('participant_joined', {
        'participant': participant
    }, room=f'admin_{game_code}')
    
    print(f'Participant {participant_name} joined game {game_code}')

@socketio.on('join_admin')
def handle_join_admin(data):
    """Handle organizer joining admin room"""
    game_code = data.get('game_code')
    organizer_id = data.get('organizer_id')
    
    if not game_code or not organizer_id:
        emit('error', {'message': 'Game code and organizer ID required'})
        return
    
    # Verify organizer owns this game
    game = games_collection.find_one({
        'code': game_code,
        'organizer_id': organizer_id
    })
    
    if not game:
        emit('error', {'message': 'Access denied'})
        return
    
    # Join admin room
    join_room(f'admin_{game_code}')
    
    # Get current participants
    participants = list(participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ))
    
    emit('admin_joined', {
        'success': True,
        'game': game,
        'participants': participants
    })

@socketio.on('join_live')
def handle_join_live(data):
    """Handle public viewer joining live view"""
    game_code = data.get('game_code')
    
    if not game_code:
        emit('error', {'message': 'Game code required'})
        return
    
    # Check if game exists
    game = games_collection.find_one({'code': game_code})
    if not game:
        emit('error', {'message': 'Game not found'})
        return
    
    # Join live room
    join_room(f'live_{game_code}')
    
    # Get current leaderboard
    participants = list(participants_collection.find(
        {'game_code': game_code},
        {'_id': 0}
    ).sort('total_score', -1))
    
    emit('live_joined', {
        'success': True,
        'game': game,
        'leaderboard': participants
    })

@socketio.on('submit_answer')
def handle_submit_answer(data):
    """Handle answer submission"""
    participant_id = data.get('participant_id')
    question_id = data.get('question_id')
    answer = data.get('answer')
    time_taken = data.get('time_taken', 0)
    used_hint = data.get('used_hint', False)
    
    if not all([participant_id, question_id, answer is not None]):
        emit('error', {'message': 'Missing required data'})
        return
    
    # Get participant and question
    participant = participants_collection.find_one({'id': participant_id})
    question = questions_collection.find_one({'id': question_id})
    
    if not participant or not question:
        emit('error', {'message': 'Participant or question not found'})
        return
    
    # Check if already answered
    existing_answer = next(
        (a for a in participant.get('answers', []) if a['question_id'] == question_id),
        None
    )
    
    if existing_answer:
        emit('error', {'message': 'Already answered this question'})
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
    participants_collection.update_one(
        {'id': participant_id},
        {
            '$push': {'answers': answer_record},
            '$inc': {'total_score': score}
        }
    )
    
    # Store answer in answers collection
    answers_collection.insert_one({
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
    emit('answer_submitted', {
        'success': True,
        'score': score,
        'is_correct': is_correct
    })
    
    # Update live leaderboard
    updated_participant = participants_collection.find_one({'id': participant_id}, {'_id': 0})
    socketio.emit('leaderboard_update', {
        'participant': updated_participant
    }, room=f'live_{participant["game_code"]}')
    
    # Notify admin
    socketio.emit('answer_received', {
        'participant_id': participant_id,
        'question_id': question_id,
        'answer': answer,
        'is_correct': is_correct,
        'score': score
    }, room=f'admin_{participant["game_code"]}')

@socketio.on('cheat_detected')
def handle_cheat_detected(data):
    """Handle cheat detection"""
    participant_id = data.get('participant_id')
    cheat_type = data.get('type')  # TAB_SWITCH, COPY_ATTEMPT, DEV_TOOLS
    
    if not participant_id or not cheat_type:
        return
    
    participant = participants_collection.find_one({'id': participant_id})
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
    
    cheat_logs_collection.insert_one(cheat_log)
    
    # Update participant cheat flags
    flag_key = f'cheat_flags.{cheat_type.lower()}s'
    participants_collection.update_one(
        {'id': participant_id},
        {'$inc': {flag_key: 1}}
    )
    
    # Apply penalty
    penalty = 10 if cheat_type in ['TAB_SWITCH', 'COPY_ATTEMPT'] else 20
    participants_collection.update_one(
        {'id': participant_id},
        {'$inc': {'total_score': -penalty}}
    )
    
    # Notify admin
    socketio.emit('cheat_detected', {
        'participant_id': participant_id,
        'type': cheat_type,
        'penalty': penalty,
        'timestamp': get_current_timestamp()
    }, room=f'admin_{participant["game_code"]}')
    
    print(f'Cheat detected: {cheat_type} by participant {participant_id}')

if __name__ == '__main__':
    print("Starting Emotech Quiz Game Server...")
    socketio.run(app, host='0.0.0.0', port=8001, debug=True)