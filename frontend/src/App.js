import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useNavigate, useParams } from 'react-router-dom';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import { motion, AnimatePresence } from 'framer-motion';
import Confetti from 'react-confetti';
import './App.css';

// Backend URL configuration - use local Docker backend
// In Docker environment, this will be set by environment variables
// In development, fallback to localhost
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 
                   (window.location.hostname === 'localhost' ? 'http://localhost:8001' : 'http://localhost:8001');
const API = `${BACKEND_URL}/api`;

// Log the backend URL for debugging
console.log('Environment:', process.env.NODE_ENV);
console.log('Backend URL:', BACKEND_URL);
console.log('API URL:', API);
console.log('Current hostname:', window.location.hostname);

// Polling-based real-time communication manager
class PollingManager {
  constructor() {
    this.intervals = new Map();
    this.callbacks = new Map();
  }

  startPolling(key, callback, intervalMs = 2000) {
    // Clear existing polling for this key
    this.stopPolling(key);
    
    this.callbacks.set(key, callback);
    const intervalId = setInterval(callback, intervalMs);
    this.intervals.set(key, intervalId);
    
    // Execute immediately
    callback();
  }

  stopPolling(key) {
    const intervalId = this.intervals.get(key);
    if (intervalId) {
      clearInterval(intervalId);
      this.intervals.delete(key);
      this.callbacks.delete(key);
    }
  }

  stopAllPolling() {
    for (const [key] of this.intervals) {
      this.stopPolling(key);
    }
  }
}

// Global polling manager
const pollingManager = new PollingManager();

// Home Page
const HomePage = () => {
  const navigate = useNavigate();
  const [gameCode, setGameCode] = useState('');
  const [isDarkMode, setIsDarkMode] = useState(true);

  const handleJoinGame = (e) => {
    e.preventDefault();
    if (gameCode.trim()) {
      navigate(`/game/${gameCode.toUpperCase()}`);
    } else {
      toast.error('Please enter a game code');
    }
  };

  const toggleDarkMode = () => {
    setIsDarkMode(!isDarkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <div className={`min-h-screen transition-all duration-500 ${isDarkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      <div className="relative overflow-hidden">
        {/* Animated Background */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 dark:from-gray-900 dark:via-purple-900 dark:to-indigo-900">
          <div className="absolute inset-0 opacity-20">
            <div className="absolute top-0 left-0 w-full h-full bg-purple-800/10 rounded-full blur-3xl animate-pulse"></div>
            <div className="absolute bottom-0 right-0 w-2/3 h-2/3 bg-blue-800/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
          </div>
        </div>

        {/* Header */}
        <header className="relative z-10 p-6">
          <div className="flex justify-between items-center max-w-6xl mx-auto">
            <motion.h1 
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-400 bg-clip-text text-transparent"
            >
              EMOTECH
            </motion.h1>
            <button
              onClick={toggleDarkMode}
              className="p-2 rounded-lg bg-white/10 backdrop-blur-sm hover:bg-white/20 transition-all duration-300"
            >
              {isDarkMode ? '☀️' : '🌙'}
            </button>
          </div>
        </header>

        {/* Main Content */}
        <div className="relative z-10 flex items-center justify-center min-h-[80vh] px-4">
          <div className="max-w-md w-full">
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6 }}
              className="bg-white/10 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-white/20"
            >
              <div className="text-center mb-8">
                <h2 className="text-4xl font-bold text-white mb-2">
                  Quiz Challenge
                </h2>
                <p className="text-gray-300">
                  Join the ultimate real-time multiplayer quiz experience
                </p>
              </div>

              <form onSubmit={handleJoinGame} className="space-y-6">
                <div>
                  <input
                    type="text"
                    placeholder="Enter Game Code"
                    value={gameCode}
                    onChange={(e) => setGameCode(e.target.value.toUpperCase())}
                    className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 transition-all duration-300"
                    maxLength="6"
                  />
                </div>
                
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  type="submit"
                  className="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:from-cyan-600 hover:to-purple-600 transition-all duration-300 shadow-lg"
                >
                  Join Game
                </motion.button>
              </form>

              <div className="mt-8 space-y-4">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => navigate('/organizer')}
                  className="w-full py-3 px-6 rounded-lg bg-white/10 text-white font-semibold hover:bg-white/20 transition-all duration-300 border border-white/20"
                >
                  Organizer Login
                </motion.button>
                
                <div className="text-center">
                  <p className="text-gray-400 text-sm">
                    Want to watch live? Use game code at{' '}
                    <span className="text-cyan-400">/live/CODE</span>
                  </p>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Organizer Login
const OrganizerLogin = () => {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/organizer/login`, credentials);
      if (response.data.success) {
        localStorage.setItem('organizer_id', response.data.organizer_id);
        localStorage.setItem('organizer_username', response.data.username);
        toast.success('Login successful!');
        navigate('/organizer/dashboard');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white/10 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-white/20 max-w-md w-full"
      >
        <h2 className="text-3xl font-bold text-white text-center mb-8">
          Organizer Login
        </h2>
        
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <input
              type="text"
              placeholder="Username"
              value={credentials.username}
              onChange={(e) => setCredentials(prev => ({ ...prev, username: e.target.value }))}
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
              required
            />
          </div>
          
          <div>
            <input
              type="password"
              placeholder="Password"
              value={credentials.password}
              onChange={(e) => setCredentials(prev => ({ ...prev, password: e.target.value }))}
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
              required
            />
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isLoading}
            className="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:from-cyan-600 hover:to-purple-600 transition-all duration-300 shadow-lg disabled:opacity-50"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </motion.button>
        </form>
        
        <button
          onClick={() => navigate('/')}
          className="w-full mt-4 py-2 text-gray-400 hover:text-white transition-colors"
        >
          ← Back to Home
        </button>
      </motion.div>
    </div>
  );
};

// Organizer Dashboard
const OrganizerDashboard = () => {
  const navigate = useNavigate();
  const [games, setGames] = useState([]);
  const [showCreateGame, setShowCreateGame] = useState(false);
  const [gameTitle, setGameTitle] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const organizerId = localStorage.getItem('organizer_id');
  const organizerUsername = localStorage.getItem('organizer_username');

  useEffect(() => {
    if (!organizerId) {
      navigate('/organizer');
    }
  }, [organizerId, navigate]);

  const createGame = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await axios.post(`${API}/games`, {
        organizer_id: organizerId,
        title: gameTitle
      });

      if (response.data.success) {
        toast.success('Game created successfully!');
        setGames(prev => [...prev, response.data.game]);
        setShowCreateGame(false);
        setGameTitle('');
        
        // Navigate to game management
        navigate(`/organizer/game/${response.data.game_code}`);
      }
    } catch (error) {
      toast.error('Failed to create game');
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('organizer_id');
    localStorage.removeItem('organizer_username');
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">Organizer Dashboard</h1>
            <p className="text-gray-300">Welcome, {organizerUsername}</p>
          </div>
          <button
            onClick={logout}
            className="px-4 py-2 rounded-lg bg-red-500 text-white hover:bg-red-600 transition-colors"
          >
            Logout
          </button>
        </div>

        {/* Create Game Section */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 mb-8">
          {!showCreateGame ? (
            <div className="text-center">
              <h2 className="text-xl font-semibold text-white mb-4">Create New Game</h2>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setShowCreateGame(true)}
                className="px-6 py-3 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:from-cyan-600 hover:to-purple-600 transition-all duration-300"
              >
                + Create Game
              </motion.button>
            </div>
          ) : (
            <form onSubmit={createGame} className="max-w-md mx-auto">
              <h2 className="text-xl font-semibold text-white mb-4 text-center">New Game</h2>
              <div className="space-y-4">
                <input
                  type="text"
                  placeholder="Game Title"
                  value={gameTitle}
                  onChange={(e) => setGameTitle(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                  required
                />
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="flex-1 py-3 rounded-lg bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold hover:from-green-600 hover:to-blue-600 transition-all duration-300 disabled:opacity-50"
                  >
                    {isLoading ? 'Creating...' : 'Create'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateGame(false)}
                    className="flex-1 py-3 rounded-lg bg-gray-500 text-white font-semibold hover:bg-gray-600 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </form>
          )}
        </div>

        {/* Games List */}
        <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
          <h2 className="text-xl font-semibold text-white mb-4">Your Games</h2>
          {games.length === 0 ? (
            <p className="text-gray-400 text-center py-8">No games created yet</p>
          ) : (
            <div className="grid gap-4">
              {games.map(game => (
                <div key={game.code} className="bg-white/5 rounded-lg p-4 border border-white/10">
                  <div className="flex justify-between items-center">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{game.title}</h3>
                      <p className="text-gray-400">Code: {game.code}</p>
                      <p className="text-sm text-gray-500">Status: {game.status}</p>
                    </div>
                    <button
                      onClick={() => navigate(`/organizer/game/${game.code}`)}
                      className="px-4 py-2 rounded-lg bg-cyan-500 text-white hover:bg-cyan-600 transition-colors"
                    >
                      Manage
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Game Management (Organizer)
const GameManagement = () => {
  const { code } = useParams();
  const navigate = useNavigate();
  const [game, setGame] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [showAddQuestion, setShowAddQuestion] = useState(false);
  const [newQuestion, setNewQuestion] = useState({
    type: 'MCQ',
    text: '',
    options: ['', '', '', ''],
    correct_answer: '',
    hint: '',
    image_url: ''
  });

  const organizerId = localStorage.getItem('organizer_id');

  useEffect(() => {
    if (!organizerId) {
      navigate('/organizer');
      return;
    }

    fetchGameData();
    
    // Poll for participant updates
    pollingManager.startPolling('participants', async () => {
      try {
        const response = await axios.get(`${API}/games/${code}/participants`);
        if (response.data.success) {
          setParticipants(response.data.participants);
        }
      } catch (error) {
        console.error('Error fetching participants:', error);
      }
    }, 3000);

    return () => {
      pollingManager.stopPolling('participants');
    };
  }, [code, organizerId, navigate]);

  const fetchGameData = async () => {
    try {
      const [gameRes, questionsRes, participantsRes] = await Promise.all([
        axios.get(`${API}/games/${code}`),
        axios.get(`${API}/games/${code}/questions`),
        axios.get(`${API}/games/${code}/participants`)
      ]);

      if (gameRes.data.success) {
        setGame(gameRes.data.game);
      }
      if (questionsRes.data.success) {
        setQuestions(questionsRes.data.questions);
      }
      if (participantsRes.data.success) {
        setParticipants(participantsRes.data.participants);
      }
    } catch (error) {
      toast.error('Failed to load game data');
    }
  };

  const addQuestion = async (e) => {
    e.preventDefault();
    
    try {
      const response = await axios.post(`${API}/games/${code}/questions`, {
        ...newQuestion,
        order: questions.length + 1
      });

      if (response.data.success) {
        setQuestions(prev => [...prev, response.data.question]);
        setShowAddQuestion(false);
        setNewQuestion({
          type: 'MCQ',
          text: '',
          options: ['', '', '', ''],
          correct_answer: '',
          hint: '',
          image_url: ''
        });
        toast.success('Question added successfully!');
      }
    } catch (error) {
      toast.error('Failed to add question');
    }
  };

  const startGame = async () => {
    try {
      const response = await axios.post(`${API}/games/${code}/start`);
      if (response.data.success) {
        setGame(prev => ({ ...prev, status: 'in_progress' }));
        toast.success('Game started!');
      }
    } catch (error) {
      toast.error('Failed to start game');
    }
  };

  if (!game) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading game...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-white">{game.title}</h1>
            <p className="text-gray-300">Code: {game.code} | Status: {game.status}</p>
          </div>
          <div className="flex space-x-4">
            {game.status === 'waiting' && questions.length > 0 && (
              <button
                onClick={startGame}
                className="px-6 py-3 rounded-lg bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold hover:from-green-600 hover:to-blue-600 transition-all duration-300"
              >
                Start Game
              </button>
            )}
            <button
              onClick={() => navigate('/organizer/dashboard')}
              className="px-4 py-2 rounded-lg bg-gray-500 text-white hover:bg-gray-600 transition-colors"
            >
              Back to Dashboard
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Questions Section */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-white">Questions ({questions.length})</h2>
              <button
                onClick={() => setShowAddQuestion(true)}
                className="px-4 py-2 rounded-lg bg-cyan-500 text-white hover:bg-cyan-600 transition-colors"
              >
                + Add Question
              </button>
            </div>

            {questions.length === 0 ? (
              <p className="text-gray-400 text-center py-8">No questions added yet</p>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {questions.map((question, index) => (
                  <div key={question.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <span className="text-xs text-cyan-400 font-semibold">{question.type}</span>
                        <h3 className="text-white font-medium">{index + 1}. {question.text}</h3>
                        {question.type === 'MCQ' && (
                          <ul className="text-sm text-gray-400 mt-2">
                            {question.options.map((option, i) => (
                              <li key={i} className={option === question.correct_answer ? 'text-green-400' : ''}>
                                {String.fromCharCode(65 + i)}. {option}
                              </li>
                            ))}
                          </ul>
                        )}
                        {(question.type === 'INPUT' || question.type === 'TRUE_FALSE' || question.type === 'SCRAMBLED') && (
                          <p className="text-sm text-green-400 mt-2">Answer: {question.correct_answer}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Participants Section */}
          <div className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20">
            <h2 className="text-xl font-semibold text-white mb-4">Participants ({participants.length})</h2>
            
            {participants.length === 0 ? (
              <p className="text-gray-400 text-center py-8">No participants yet</p>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {participants.map((participant) => (
                  <div key={participant.id} className="bg-white/5 rounded-lg p-4 border border-white/10">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <img
                          src={participant.avatar}
                          alt="Avatar"
                          className="w-10 h-10 rounded-full border-2 border-cyan-400"
                        />
                        <div>
                          <h3 className="text-white font-medium">{participant.name}</h3>
                          <p className="text-sm text-gray-400">Score: {participant.total_score}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-400">
                          Answers: {participant.answers?.length || 0}
                        </p>
                        {participant.cheat_flags && (
                          <p className="text-xs text-red-400">
                            Violations: {Object.values(participant.cheat_flags).reduce((a, b) => a + b, 0)}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Add Question Modal */}
        <AnimatePresence>
          {showAddQuestion && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50"
            >
              <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="bg-white/10 backdrop-blur-md rounded-2xl p-6 border border-white/20 max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              >
                <h2 className="text-2xl font-bold text-white mb-6">Add New Question</h2>
                
                <form onSubmit={addQuestion} className="space-y-4">
                  <div>
                    <label className="block text-white font-medium mb-2">Question Type</label>
                    <select
                      value={newQuestion.type}
                      onChange={(e) => setNewQuestion(prev => ({ 
                        ...prev, 
                        type: e.target.value,
                        options: e.target.value === 'MCQ' ? ['', '', '', ''] : [],
                        correct_answer: ''
                      }))}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
                    >
                      <option value="MCQ">Multiple Choice</option>
                      <option value="TRUE_FALSE">True/False</option>
                      <option value="INPUT">Text Input</option>
                      <option value="SCRAMBLED">Scrambled Word</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-white font-medium mb-2">Question Text</label>
                    <textarea
                      value={newQuestion.text}
                      onChange={(e) => setNewQuestion(prev => ({ ...prev, text: e.target.value }))}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                      rows="3"
                      required
                    />
                  </div>

                  {newQuestion.type === 'MCQ' && (
                    <div>
                      <label className="block text-white font-medium mb-2">Options</label>
                      {newQuestion.options.map((option, index) => (
                        <input
                          key={index}
                          type="text"
                          placeholder={`Option ${String.fromCharCode(65 + index)}`}
                          value={option}
                          onChange={(e) => {
                            const newOptions = [...newQuestion.options];
                            newOptions[index] = e.target.value;
                            setNewQuestion(prev => ({ ...prev, options: newOptions }));
                          }}
                          className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 mb-2"
                          required
                        />
                      ))}
                    </div>
                  )}

                  <div>
                    <label className="block text-white font-medium mb-2">Correct Answer</label>
                    {newQuestion.type === 'MCQ' ? (
                      <select
                        value={newQuestion.correct_answer}
                        onChange={(e) => setNewQuestion(prev => ({ ...prev, correct_answer: e.target.value }))}
                        className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
                        required
                      >
                        <option value="">Select correct option</option>
                        {newQuestion.options.map((option, index) => (
                          <option key={index} value={option}>{String.fromCharCode(65 + index)}. {option}</option>
                        ))}
                      </select>
                    ) : newQuestion.type === 'TRUE_FALSE' ? (
                      <select
                        value={newQuestion.correct_answer}
                        onChange={(e) => setNewQuestion(prev => ({ ...prev, correct_answer: e.target.value }))}
                        className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
                        required
                      >
                        <option value="">Select answer</option>
                        <option value="True">True</option>
                        <option value="False">False</option>
                      </select>
                    ) : (
                      <input
                        type="text"
                        value={newQuestion.correct_answer}
                        onChange={(e) => setNewQuestion(prev => ({ ...prev, correct_answer: e.target.value }))}
                        className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                        required
                      />
                    )}
                  </div>

                  <div>
                    <label className="block text-white font-medium mb-2">Hint (Optional)</label>
                    <input
                      type="text"
                      value={newQuestion.hint}
                      onChange={(e) => setNewQuestion(prev => ({ ...prev, hint: e.target.value }))}
                      className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                    />
                  </div>

                  <div className="flex space-x-4 pt-4">
                    <button
                      type="submit"
                      className="flex-1 py-3 rounded-lg bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold hover:from-green-600 hover:to-blue-600 transition-all duration-300"
                    >
                      Add Question
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowAddQuestion(false)}
                      className="flex-1 py-3 rounded-lg bg-gray-500 text-white font-semibold hover:bg-gray-600 transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};

// Game Lobby (Participant)
const GameLobby = () => {
  const { code } = useParams();
  const navigate = useNavigate();
  const [participantName, setParticipantName] = useState('');
  const [participant, setParticipant] = useState(null);
  const [game, setGame] = useState(null);
  const [gameStarted, setGameStarted] = useState(false);
  const [isJoining, setIsJoining] = useState(false);

  useEffect(() => {
    // Check game status periodically
    pollingManager.startPolling('game_status', async () => {
      try {
        const response = await axios.get(`${API}/games/${code}`);
        if (response.data.success) {
          const gameData = response.data.game;
          setGame(gameData);
          
          if (gameData.status === 'in_progress' && participant) {
            setGameStarted(true);
            pollingManager.stopPolling('game_status');
          }
        }
      } catch (error) {
        // Game might not exist yet, ignore error
      }
    }, 3000);

    return () => {
      pollingManager.stopPolling('game_status');
    };
  }, [code, participant]);

  // Anti-cheat detection
  useEffect(() => {
    if (!participant) return;

    const handleVisibilityChange = () => {
      if (document.hidden && participant) {
        // Send cheat detection via API
        axios.post(`${API}/cheat-detected`, {
          participant_id: participant.id,
          type: 'TAB_SWITCH'
        }).catch(() => {}); // Ignore errors
      }
    };

    const handleKeyDown = (e) => {
      if (participant && (
        (e.ctrlKey && (e.key === 'u' || e.key === 'c')) ||
        e.key === 'F12'
      )) {
        e.preventDefault();
        axios.post(`${API}/cheat-detected`, {
          participant_id: participant.id,
          type: 'DEV_TOOLS'
        }).catch(() => {});
      }
    };

    const handleContextMenu = (e) => {
      if (participant) {
        e.preventDefault();
        axios.post(`${API}/cheat-detected`, {
          participant_id: participant.id,
          type: 'COPY_ATTEMPT'
        }).catch(() => {});
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('contextmenu', handleContextMenu);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('contextmenu', handleContextMenu);
    };
  }, [participant]);

  const joinGame = async (e) => {
    e.preventDefault();
    if (participantName.trim()) {
      setIsJoining(true);
      
      try {
        // Create participant via REST API
        const response = await axios.post(`${API}/participants`, {
          game_code: code,
          name: participantName.trim()
        });

        if (response.data.success) {
          setParticipant(response.data.participant);
          setGame(response.data.game);
          toast.success('Joined game successfully!');
        } else {
          toast.error(response.data.message || 'Failed to join game');
        }
      } catch (error) {
        const message = error.response?.data?.detail || error.response?.data?.message || 'Failed to join game';
        toast.error(message);
      } finally {
        setIsJoining(false);
      }
    }
  };

  if (gameStarted && participant && game) {
    return <QuizGame participant={participant} game={game} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white/10 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-white/20 max-w-md w-full"
      >
        {!participant ? (
          <div>
            <h2 className="text-3xl font-bold text-white text-center mb-2">
              Join Game
            </h2>
            <p className="text-gray-300 text-center mb-8">Code: {code}</p>
            
            <form onSubmit={joinGame} className="space-y-6">
              <div>
                <input
                  type="text"
                  placeholder="Enter your name"
                  value={participantName}
                  onChange={(e) => setParticipantName(e.target.value)}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
                  required
                />
              </div>
              
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                type="submit"
                disabled={isJoining}
                className="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:from-cyan-600 hover:to-purple-600 transition-all duration-300 shadow-lg disabled:opacity-50"
              >
                {isJoining ? 'Joining...' : 'Join Game'}
              </motion.button>
            </form>
          </div>
        ) : (
          <div className="text-center">
            <div className="mb-6">
              <img
                src={participant.avatar}
                alt="Avatar"
                className="w-20 h-20 rounded-full mx-auto mb-4 border-4 border-cyan-400"
              />
              <h3 className="text-2xl font-bold text-white">{participant.name}</h3>
              <p className="text-gray-300">Joined successfully!</p>
            </div>
            
            <div className="bg-white/5 rounded-lg p-4 mb-6">
              <h4 className="text-lg font-semibold text-white mb-2">{game?.title}</h4>
              <p className="text-gray-300">Waiting for organizer to start the game...</p>
            </div>
            
            <div className="flex justify-center">
              <div className="animate-spin w-8 h-8 border-4 border-cyan-400 border-t-transparent rounded-full"></div>
            </div>
          </div>
        )}
        
        <button
          onClick={() => navigate('/')}
          className="w-full mt-6 py-2 text-gray-400 hover:text-white transition-colors"
        >
          ← Back to Home
        </button>
      </motion.div>
    </div>
  );
};

// Quiz Game Component
const QuizGame = ({ participant, game }) => {
  const [questions, setQuestions] = useState([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [timeLeft, setTimeLeft] = useState(30);
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [showHint, setShowHint] = useState(false);
  const [usedHint, setUsedHint] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [gameCompleted, setGameCompleted] = useState(false);
  const [updatedParticipant, setUpdatedParticipant] = useState(participant);

  const currentQuestion = questions[currentQuestionIndex];

  useEffect(() => {
    // Fetch questions
    const fetchQuestions = async () => {
      try {
        const response = await axios.get(`${API}/games/${game.code}/questions`);
        if (response.data.success) {
          setQuestions(response.data.questions);
        }
      } catch (error) {
        toast.error('Failed to load questions');
      }
    };

    fetchQuestions();
  }, [game.code]);

  // Timer effect
  useEffect(() => {
    if (timeLeft > 0 && !isSubmitting && !gameCompleted && currentQuestion) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000);
      return () => clearTimeout(timer);
    } else if (timeLeft === 0 && !isSubmitting && currentQuestion) {
      submitAnswer();
    }
  }, [timeLeft, isSubmitting, gameCompleted, currentQuestion]);

  const submitAnswer = async () => {
    if (isSubmitting || !currentQuestion) return;
    
    setIsSubmitting(true);
    const timeTaken = 30 - timeLeft;

    try {
      const response = await axios.post(`${API}/answers`, {
        participant_id: updatedParticipant.id,
        question_id: currentQuestion.id,
        answer: selectedAnswer,
        time_taken: timeTaken,
        used_hint: usedHint
      });

      if (response.data.success) {
        toast.success(`${response.data.is_correct ? 'Correct!' : 'Incorrect'} Score: ${response.data.score}`);
        
        // Update participant score
        setUpdatedParticipant(prev => ({
          ...prev,
          total_score: response.data.total_score
        }));
        
        // Move to next question or complete game
        setTimeout(() => {
          if (currentQuestionIndex < questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
            setSelectedAnswer('');
            setShowHint(false);
            setUsedHint(false);
            setTimeLeft(30);
            setIsSubmitting(false);
          } else {
            setGameCompleted(true);
          }
        }, 2000);
      }
    } catch (error) {
      toast.error('Failed to submit answer');
      setIsSubmitting(false);
    }
  };

  const renderQuestion = () => {
    if (!currentQuestion) return null;

    switch (currentQuestion.type) {
      case 'MCQ':
        return (
          <div className="space-y-3">
            {currentQuestion.options.map((option, index) => (
              <motion.button
                key={index}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedAnswer(option)}
                className={`w-full p-4 rounded-lg text-left border-2 transition-all duration-300 ${
                  selectedAnswer === option
                    ? 'border-cyan-400 bg-cyan-400/20 text-white'
                    : 'border-white/20 bg-white/5 text-gray-300 hover:border-white/40'
                }`}
              >
                {String.fromCharCode(65 + index)}. {option}
              </motion.button>
            ))}
          </div>
        );

      case 'TRUE_FALSE':
        return (
          <div className="grid grid-cols-2 gap-4">
            {['True', 'False'].map((option) => (
              <motion.button
                key={option}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setSelectedAnswer(option)}
                className={`p-4 rounded-lg font-semibold border-2 transition-all duration-300 ${
                  selectedAnswer === option
                    ? 'border-cyan-400 bg-cyan-400/20 text-white'
                    : 'border-white/20 bg-white/5 text-gray-300 hover:border-white/40'
                }`}
              >
                {option}
              </motion.button>
            ))}
          </div>
        );

      case 'INPUT':
      case 'SCRAMBLED':
        return (
          <div>
            <input
              type="text"
              placeholder="Type your answer..."
              value={selectedAnswer}
              onChange={(e) => setSelectedAnswer(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-cyan-400"
            />
          </div>
        );

      default:
        return null;
    }
  };

  if (gameCompleted) {
    return <GameCompleted participant={updatedParticipant} />;
  }

  if (!currentQuestion) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading questions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <span className="text-white font-semibold">
              Question {currentQuestionIndex + 1} of {questions.length}
            </span>
            <span className="text-cyan-400 font-bold text-xl">
              {timeLeft}s
            </span>
          </div>
          <div className="w-full bg-white/20 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-cyan-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
              style={{ width: `${((currentQuestionIndex + 1) / questions.length) * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Question Card */}
        <motion.div
          key={currentQuestionIndex}
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          className="bg-white/10 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-white/20"
        >
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-4">
              {currentQuestion.text}
            </h2>
            
            {currentQuestion.image_url && (
              <img
                src={currentQuestion.image_url}
                alt="Question"
                className="w-full max-w-md mx-auto rounded-lg mb-4"
              />
            )}
            
            {currentQuestion.hint && (
              <div className="mb-4">
                {!showHint ? (
                  <button
                    onClick={() => {
                      setShowHint(true);
                      setUsedHint(true);
                    }}
                    className="px-4 py-2 rounded-lg bg-yellow-500 text-black font-semibold hover:bg-yellow-600 transition-colors"
                  >
                    💡 Use Hint (-15 points)
                  </button>
                ) : (
                  <div className="p-4 rounded-lg bg-yellow-500/20 border border-yellow-500">
                    <p className="text-yellow-200">💡 Hint: {currentQuestion.hint}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {renderQuestion()}

          <div className="mt-6 flex justify-between items-center">
            <div className="text-gray-400">
              <span className="font-semibold text-white">{updatedParticipant.name}</span>
              <br />
              Current Score: {updatedParticipant.total_score}
            </div>
            
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={submitAnswer}
              disabled={!selectedAnswer || isSubmitting}
              className="px-6 py-3 rounded-lg bg-gradient-to-r from-green-500 to-blue-500 text-white font-semibold hover:from-green-600 hover:to-blue-600 transition-all duration-300 disabled:opacity-50"
            >
              {isSubmitting ? 'Submitting...' : 'Submit Answer'}
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

// Game Completed Component
const GameCompleted = ({ participant }) => {
  const navigate = useNavigate();
  const [showConfetti, setShowConfetti] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setShowConfetti(false), 5000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4 relative">
      {showConfetti && <Confetti />}
      
      <div className="max-w-2xl mx-auto text-center py-12">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/10 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-white/20"
        >
          <h1 className="text-4xl font-bold text-white mb-6">
            🎉 Game Completed! 🎉
          </h1>
          
          <div className="mb-8">
            <img
              src={participant.avatar}
              alt="Avatar"
              className="w-24 h-24 rounded-full mx-auto mb-4 border-4 border-cyan-400"
            />
            <h2 className="text-2xl font-bold text-white">{participant.name}</h2>
            <p className="text-3xl font-bold text-cyan-400 mt-2">
              Final Score: {participant.total_score}
            </p>
          </div>
          
          <div className="space-y-4 mb-8">
            <button
              onClick={() => navigate('/live/' + participant.game_code)}
              className="w-full py-3 px-6 rounded-lg bg-gradient-to-r from-cyan-500 to-purple-500 text-white font-semibold hover:from-cyan-600 hover:to-purple-600 transition-all duration-300"
            >
              View Live Leaderboard
            </button>
            
            <button
              onClick={() => navigate('/')}
              className="w-full py-3 px-6 rounded-lg bg-white/10 text-white font-semibold hover:bg-white/20 transition-all duration-300 border border-white/20"
            >
              Join Another Game
            </button>
          </div>
          
          <p className="text-gray-400">
            Thank you for playing Emotech Quiz!
          </p>
        </motion.div>
      </div>
    </div>
  );
};

// Live Leaderboard
const LiveLeaderboard = () => {
  const { code } = useParams();
  const [game, setGame] = useState(null);
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    fetchGameData();
    
    // Poll for leaderboard updates
    pollingManager.startPolling('leaderboard', async () => {
      try {
        const response = await axios.get(`${API}/games/${code}/leaderboard`);
        if (response.data.success) {
          setLeaderboard(response.data.leaderboard);
        }
      } catch (error) {
        console.error('Error fetching leaderboard:', error);
      }
    }, 3000);

    return () => {
      pollingManager.stopPolling('leaderboard');
    };
  }, [code]);

  const fetchGameData = async () => {
    try {
      const [gameRes, leaderboardRes] = await Promise.all([
        axios.get(`${API}/games/${code}`),
        axios.get(`${API}/games/${code}/leaderboard`)
      ]);

      if (gameRes.data.success) {
        setGame(gameRes.data.game);
      }
      if (leaderboardRes.data.success) {
        setLeaderboard(leaderboardRes.data.leaderboard);
      }
    } catch (error) {
      toast.error('Failed to load game data');
    }
  };

  if (!game) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-white text-center">
          <div className="animate-spin w-12 h-12 border-4 border-cyan-400 border-t-transparent rounded-full mx-auto mb-4"></div>
          <p>Loading leaderboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">🏆 Live Leaderboard</h1>
          <p className="text-xl text-gray-300">{game.title}</p>
          <p className="text-lg text-cyan-400">Game Code: {game.code}</p>
          <div className="mt-4">
            <span className={`px-4 py-2 rounded-full text-sm font-semibold ${
              game.status === 'waiting' ? 'bg-yellow-500/20 text-yellow-400' :
              game.status === 'in_progress' ? 'bg-green-500/20 text-green-400' :
              'bg-blue-500/20 text-blue-400'
            }`}>
              {game.status.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-6 shadow-2xl border border-white/20">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">
            Rankings ({leaderboard.length} participants)
          </h2>
          
          {leaderboard.length === 0 ? (
            <p className="text-gray-400 text-center py-12">No participants yet</p>
          ) : (
            <div className="space-y-3">
              {leaderboard.map((participant, index) => (
                <motion.div
                  key={participant.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                    index === 0 ? 'border-yellow-400 bg-yellow-400/10' :
                    index === 1 ? 'border-gray-400 bg-gray-400/10' :
                    index === 2 ? 'border-orange-400 bg-orange-400/10' :
                    'border-white/20 bg-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="text-center">
                        <span className={`text-2xl font-bold ${
                          index === 0 ? 'text-yellow-400' :
                          index === 1 ? 'text-gray-400' :
                          index === 2 ? 'text-orange-400' :
                          'text-white'
                        }`}>
                          #{index + 1}
                        </span>
                        {index < 3 && (
                          <div className="text-xl">
                            {index === 0 ? '🥇' : index === 1 ? '🥈' : '🥉'}
                          </div>
                        )}
                      </div>
                      
                      <img
                        src={participant.avatar}
                        alt="Avatar"
                        className="w-12 h-12 rounded-full border-2 border-cyan-400"
                      />
                      
                      <div>
                        <h3 className="text-lg font-bold text-white">{participant.name}</h3>
                        <p className="text-sm text-gray-400">
                          Answers: {participant.answers?.length || 0}
                        </p>
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <p className="text-2xl font-bold text-cyan-400">
                        {participant.total_score}
                      </p>
                      <p className="text-xs text-gray-400">points</p>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
        
        <div className="text-center mt-8">
          <p className="text-gray-400">
            Updates automatically • Refresh not needed
          </p>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/organizer" element={<OrganizerLogin />} />
          <Route path="/organizer/dashboard" element={<OrganizerDashboard />} />
          <Route path="/organizer/game/:code" element={<GameManagement />} />
          <Route path="/game/:code" element={<GameLobby />} />
          <Route path="/live/:code" element={<LiveLeaderboard />} />
        </Routes>
      </BrowserRouter>
      <Toaster position="top-right" />
    </div>
  );
}

export default App;