#!/usr/bin/env python3
"""
Final Backend API Test - Focus on Working Components
"""

import requests
import json
import uuid
from datetime import datetime

# Configuration
BACKEND_URL = "https://01c20ec6-6f32-4da6-b33e-28aa4ae0e92a.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_complete_api_flow():
    """Test complete API flow without WebSockets"""
    session = requests.Session()
    results = {}
    
    print("🚀 Testing Complete API Flow")
    print("=" * 50)
    
    # 1. Organizer Login
    print("\n1️⃣ Testing Organizer Login...")
    login_data = {
        "username": "tech_organizer_2025",
        "password": "secure_quiz_password"
    }
    
    response = session.post(f"{API_BASE}/organizer/login", json=login_data)
    if response.status_code == 200:
        data = response.json()
        organizer_id = data.get('organizer_id')
        print(f"✅ Organizer logged in: {data.get('username')} (ID: {organizer_id[:8]}...)")
        results['organizer_login'] = True
    else:
        print(f"❌ Organizer login failed: {response.status_code}")
        results['organizer_login'] = False
        return results
    
    # 2. Game Creation
    print("\n2️⃣ Testing Game Creation...")
    game_data = {
        "organizer_id": organizer_id,
        "title": "Advanced Tech Quiz Championship 2025"
    }
    
    response = session.post(f"{API_BASE}/games", json=game_data)
    if response.status_code == 200:
        data = response.json()
        game_code = data.get('game_code')
        print(f"✅ Game created: {data.get('game', {}).get('title')} (Code: {game_code})")
        results['game_creation'] = True
    else:
        print(f"❌ Game creation failed: {response.status_code}")
        results['game_creation'] = False
        return results
    
    # 3. Question Management - All Types
    print("\n3️⃣ Testing Question Management...")
    questions = [
        {
            "type": "MCQ",
            "text": "Which programming language is known for its use in data science and machine learning?",
            "options": ["JavaScript", "Python", "C++", "Ruby"],
            "correct_answer": "Python",
            "hint": "It's named after a British comedy group",
            "order": 1
        },
        {
            "type": "TRUE_FALSE",
            "text": "REST APIs are stateless by design.",
            "options": ["True", "False"],
            "correct_answer": "True",
            "hint": "Think about how REST handles client-server communication",
            "order": 2
        },
        {
            "type": "INPUT",
            "text": "What is the standard HTTP status code for 'Not Found'?",
            "options": [],
            "correct_answer": "404",
            "hint": "It's a very famous error code",
            "order": 3
        },
        {
            "type": "SCRAMBLED",
            "text": "Unscramble this database term: XENDI",
            "options": [],
            "correct_answer": "INDEX",
            "hint": "It helps speed up database queries",
            "order": 4
        }
    ]
    
    question_ids = []
    for i, question in enumerate(questions):
        response = session.post(f"{API_BASE}/games/{game_code}/questions", json=question)
        if response.status_code == 200:
            data = response.json()
            question_id = data.get('question', {}).get('id')
            question_ids.append(question_id)
            print(f"✅ Added {question['type']} question: {question['text'][:40]}...")
        else:
            print(f"❌ Failed to add {question['type']} question: {response.status_code}")
    
    results['question_management'] = len(question_ids) == len(questions)
    
    # 4. Question Retrieval
    print("\n4️⃣ Testing Question Retrieval...")
    response = session.get(f"{API_BASE}/games/{game_code}/questions")
    if response.status_code == 200:
        data = response.json()
        questions_retrieved = data.get('questions', [])
        print(f"✅ Retrieved {len(questions_retrieved)} questions")
        results['question_retrieval'] = len(questions_retrieved) == len(questions)
    else:
        print(f"❌ Question retrieval failed: {response.status_code}")
        results['question_retrieval'] = False
    
    # 5. Game Details
    print("\n5️⃣ Testing Game Details...")
    response = session.get(f"{API_BASE}/games/{game_code}")
    if response.status_code == 200:
        data = response.json()
        game = data.get('game', {})
        print(f"✅ Game details: {game.get('title')} - Status: {game.get('status')}")
        results['game_details'] = True
    else:
        print(f"❌ Game details failed: {response.status_code}")
        results['game_details'] = False
    
    # 6. Participants (should be empty initially)
    print("\n6️⃣ Testing Participants Endpoint...")
    response = session.get(f"{API_BASE}/games/{game_code}/participants")
    if response.status_code == 200:
        data = response.json()
        participants = data.get('participants', [])
        print(f"✅ Participants endpoint working: {len(participants)} participants")
        results['participants_endpoint'] = True
    else:
        print(f"❌ Participants endpoint failed: {response.status_code}")
        results['participants_endpoint'] = False
    
    # 7. Leaderboard
    print("\n7️⃣ Testing Leaderboard...")
    response = session.get(f"{API_BASE}/games/{game_code}/leaderboard")
    if response.status_code == 200:
        data = response.json()
        leaderboard = data.get('leaderboard', [])
        print(f"✅ Leaderboard working: {len(leaderboard)} entries")
        results['leaderboard'] = True
    else:
        print(f"❌ Leaderboard failed: {response.status_code}")
        results['leaderboard'] = False
    
    # 8. Game Start
    print("\n8️⃣ Testing Game Start...")
    response = session.post(f"{API_BASE}/games/{game_code}/start")
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Game started successfully")
            results['game_start'] = True
            
            # Verify status change
            response = session.get(f"{API_BASE}/games/{game_code}")
            if response.status_code == 200:
                game_data = response.json()
                game = game_data.get('game', {})
                if game.get('status') == 'in_progress':
                    print("✅ Game status updated to 'in_progress'")
                    results['game_status_update'] = True
                else:
                    print(f"❌ Game status not updated: {game.get('status')}")
                    results['game_status_update'] = False
        else:
            print("❌ Game start returned success=false")
            results['game_start'] = False
    else:
        print(f"❌ Game start failed: {response.status_code}")
        results['game_start'] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 API TEST SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    print(f"Total API Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    print("\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    return results

if __name__ == "__main__":
    test_complete_api_flow()