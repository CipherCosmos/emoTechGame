# Emotech Quiz Game 🎮

A real-time multiplayer quiz game built with React, FastAPI, MongoDB, and WebSockets. Features include organizer dashboard, participant interface, live leaderboards, anti-cheat detection, and multiple question types.

## 🚀 Features

- **Real-time Multiplayer**: Live quiz games with WebSocket communication
- **Multiple Question Types**: MCQ, True/False, Text Input, Scrambled Words
- **Organizer Dashboard**: Create games, manage questions, monitor participants
- **Live Leaderboard**: Real-time score tracking and rankings
- **Anti-Cheat System**: Detect tab switches, dev tools usage, and copy attempts
- **Modern UI**: Beautiful glassmorphism design with dark/light mode
- **Responsive Design**: Works on desktop and mobile devices

## 🏗️ Architecture

- **Frontend**: React 19 + Tailwind CSS + Framer Motion
- **Backend**: FastAPI + WebSockets + MongoDB
- **Database**: MongoDB with Motor (async driver)
- **Real-time**: WebSocket connections for live updates
- **Deployment**: Docker containers with Nginx reverse proxy

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🐳 Quick Start with Docker

### 1. Clone the Repository
```bash
git clone <repository-url>
cd emoTechGame
```

### 2. Start Production Environment
```bash
# Build and start all services
docker-compose up -d

# Or use the Makefile
make prod
```

### 3. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **MongoDB Express**: http://localhost:8081 (admin/admin)
- **MongoDB**: localhost:27017

### 4. Development Environment
```bash
# Start development environment with hot reload
make dev

# Or manually
docker-compose -f docker-compose.dev.yml up -d
```

## 🛠️ Development Setup

### Using Docker (Recommended)
```bash
# Start development environment
make dev

# View logs
make dev-logs

# Stop development environment
make dev-down

# Access container shells
make shell-backend
make shell-frontend
make shell-mongo
```

### Local Development
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# Frontend
cd frontend
yarn install
yarn start
```

## 📁 Project Structure

```
emoTechGame/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main application
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile         # Production Dockerfile
├── frontend/               # React frontend
│   ├── src/
│   │   ├── App.js         # Main application
│   │   └── App.css        # Styles
│   ├── package.json       # Node dependencies
│   └── Dockerfile         # Production Dockerfile
├── docker/                 # Docker configurations
│   ├── mongo/
│   │   └── init.js        # MongoDB initialization
│   └── nginx/
│       └── nginx.conf     # Nginx configuration
├── docker-compose.yml      # Production services
├── docker-compose.dev.yml  # Development services
└── Makefile               # Management commands
```

## 🎮 How to Play

### For Organizers
1. Visit http://localhost:3000
2. Click "Organizer Login"
3. Create a new game
4. Add questions (MCQ, True/False, Input, Scrambled)
5. Start the game when ready

### For Participants
1. Visit http://localhost:3000
2. Enter the game code provided by organizer
3. Enter your name
4. Wait for the game to start
5. Answer questions within the time limit
6. Use hints if available (costs points)
7. View live leaderboard

### Live Leaderboard
- Visit http://localhost:3000/live/GAMECODE
- Real-time updates of participant scores
- No login required

## 🔧 Configuration

### Environment Variables

#### Backend
- `MONGO_URL`: MongoDB connection string
- `DB_NAME`: Database name
- `ENVIRONMENT`: production/development
- `LOG_LEVEL`: logging level

#### Frontend
- `REACT_APP_BACKEND_URL`: Backend API URL
- `REACT_APP_API_URL`: API endpoint URL
- `NODE_ENV`: production/development

### Database Configuration
- **Username**: admin
- **Password**: emotech_password_2025
- **Database**: emotech_quiz (production) / emotech_quiz_dev (development)

## 🧪 Testing

```bash
# Run backend tests
make test

# Or manually
docker-compose exec backend python -m pytest -v
```

## 📊 Database Collections

- `organizers`: Game organizers
- `games`: Quiz games with codes
- `questions`: Game questions (4 types)
- `participants`: Game players
- `answers`: Submitted answers
- `cheat_logs`: Anti-cheat violations

## 🔒 Security Features

- **Anti-Cheat Detection**: Monitors tab switches, dev tools, copy attempts
- **Rate Limiting**: API and WebSocket rate limiting
- **Input Validation**: Server-side validation for all inputs
- **CORS Protection**: Configured CORS policies
- **Security Headers**: XSS protection, content type validation

## 🚀 Deployment

### Production Deployment
```bash
# Build and start production environment
make prod

# Or manually
docker-compose up -d
```

### Custom Domain Setup
1. Update nginx configuration in `docker/nginx/nginx.conf`
2. Add SSL certificates to `docker/nginx/ssl/`
3. Update environment variables for your domain
4. Restart the nginx container

## 📝 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

### Key Endpoints
- `POST /api/organizer/login` - Organizer authentication
- `POST /api/games` - Create new games
- `POST /api/games/{code}/questions` - Add questions
- `POST /api/participants` - Join games
- `POST /api/answers` - Submit answers
- `GET /api/games/{code}/leaderboard` - Live rankings

## 🛠️ Management Commands

```bash
# View all available commands
make help

# Development
make dev          # Start development environment
make dev-logs     # View development logs
make dev-down     # Stop development environment

# Production
make prod         # Start production environment
make prod-logs    # View production logs
make prod-down    # Stop production environment

# Utilities
make clean        # Remove all containers and volumes
make health       # Check service health
make test         # Run tests

# Database
make db-backup    # Create database backup
make db-restore   # Restore database from backup

# Quick access
make frontend     # Open frontend in browser
make backend      # Open API docs in browser
make mongo-express # Open MongoDB Express in browser
```

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :3000
   lsof -i :8001
   
   # Stop conflicting services
   docker-compose down
   ```

2. **MongoDB Connection Issues**
   ```bash
   # Check MongoDB status
   docker-compose logs mongodb
   
   # Restart MongoDB
   docker-compose restart mongodb
   ```

3. **WebSocket Connection Issues**
   - Ensure nginx is properly configured for WebSocket proxying
   - Check firewall settings
   - Verify backend WebSocket handler is running

4. **Build Failures**
   ```bash
   # Clean and rebuild
   make clean
   docker-compose build --no-cache
   ```

### Logs and Debugging
```bash
# View all logs
make logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mongodb

# Access container for debugging
make shell-backend
make shell-frontend
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs using `make logs`
3. Create an issue with detailed information

---

**Happy Quizzing! 🎉**
