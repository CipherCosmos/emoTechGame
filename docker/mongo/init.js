// MongoDB initialization script for Emotech Quiz Game
// This script runs when the MongoDB container starts for the first time

// Switch to the emotech_quiz database
db = db.getSiblingDB('emotech_quiz');

// Create collections with proper indexes
print('Creating collections and indexes for Emotech Quiz Game...');

// Create collections
db.createCollection('organizers');
db.createCollection('games');
db.createCollection('questions');
db.createCollection('participants');
db.createCollection('answers');
db.createCollection('cheat_logs');

// Create indexes for better performance
print('Creating indexes...');

// Organizers collection indexes
db.organizers.createIndex({ "username": 1 }, { unique: true });
db.organizers.createIndex({ "created_at": 1 });

// Games collection indexes
db.games.createIndex({ "code": 1 }, { unique: true });
db.games.createIndex({ "organizer_id": 1 });
db.games.createIndex({ "status": 1 });
db.games.createIndex({ "created_at": 1 });

// Questions collection indexes
db.questions.createIndex({ "game_code": 1 });
db.questions.createIndex({ "game_code": 1, "order": 1 });
db.questions.createIndex({ "id": 1 }, { unique: true });

// Participants collection indexes
db.participants.createIndex({ "game_code": 1, "name": 1 }, { unique: true });
db.participants.createIndex({ "game_code": 1 });
db.participants.createIndex({ "id": 1 }, { unique: true });
db.participants.createIndex({ "total_score": -1 });

// Answers collection indexes
db.answers.createIndex({ "participant_id": 1, "question_id": 1 }, { unique: true });
db.answers.createIndex({ "game_code": 1 });
db.answers.createIndex({ "submitted_at": 1 });

// Cheat logs collection indexes
db.cheat_logs.createIndex({ "participant_id": 1 });
db.cheat_logs.createIndex({ "game_code": 1 });
db.cheat_logs.createIndex({ "timestamp": 1 });

// Insert sample data for testing (optional)
print('Inserting sample data...');

// Sample organizer
db.organizers.insertOne({
    id: "sample-organizer-001",
    username: "demo_organizer",
    created_at: new Date()
});

// Sample game
db.games.insertOne({
    code: "DEMO01",
    title: "Demo Quiz Game",
    organizer_id: "sample-organizer-001",
    status: "waiting",
    created_at: new Date(),
    started_at: null,
    ended_at: null,
    settings: {
        question_time_limit: 30,
        hint_penalty: 15,
        cheat_penalty: 10
    }
});

// Sample questions
const sampleQuestions = [
    {
        id: "q1",
        game_code: "DEMO01",
        type: "MCQ",
        text: "What does API stand for?",
        options: ["Application Programming Interface", "Advanced Programming Interface", "Automated Programming Interface", "Application Process Interface"],
        correct_answer: "Application Programming Interface",
        hint: "It's about how applications communicate",
        order: 1,
        created_at: new Date()
    },
    {
        id: "q2",
        game_code: "DEMO01",
        type: "TRUE_FALSE",
        text: "Python is a compiled language.",
        options: ["True", "False"],
        correct_answer: "False",
        hint: "Think about how Python code is executed",
        order: 2,
        created_at: new Date()
    },
    {
        id: "q3",
        game_code: "DEMO01",
        type: "INPUT",
        text: "What is the default port for HTTP?",
        options: [],
        correct_answer: "80",
        hint: "It's a two-digit number",
        order: 3,
        created_at: new Date()
    }
];

db.questions.insertMany(sampleQuestions);

print('MongoDB initialization completed successfully!');
print('Collections created: organizers, games, questions, participants, answers, cheat_logs');
print('Sample data inserted for testing');
print('Database ready for Emotech Quiz Game!'); 