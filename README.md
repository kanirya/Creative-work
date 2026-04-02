# EduPilot by Agentix

> AI Agents Built for Real Life

EduPilot is a comprehensive AI-powered university assistant system designed for Iqra University students. The system integrates with the university's Learning Management System (LMS), captures and transcribes lectures from video conferencing platforms, and provides an intelligent natural language interface for students to query their academic information.

## Features

- 🎓 **LMS Integration**: Automatic synchronization with Iqra University LMS
- 🎤 **Lecture Transcription**: AI-powered transcription of Zoom and Google Meet recordings
- 💬 **Natural Language Queries**: Ask questions in plain English or Urdu
- 📱 **Multi-Platform**: Web, Desktop (Windows/Mac/Linux), and Mobile (iOS/Android)
- 🔍 **Semantic Search**: RAG-powered search across all your academic data
- 📊 **Performance Analytics**: Track your grades, assignments, and deadlines
- 🔔 **Smart Notifications**: Get reminded about upcoming deadlines
- 🔒 **Secure & Private**: FERPA-compliant data handling

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client Applications                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   Web    │  │ Desktop  │  │  Mobile  │  │Marketing │   │
│  │ Next.js  │  │ Electron │  │   Expo   │  │ Next.js  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (.NET 8)                      │
│              Clean Architecture + CQRS + MediatR             │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  AI Agent    │  │ LMS Scraper  │  │Transcription │
│  LangChain   │  │  Playwright  │  │   Whisper    │
│   Python     │  │   Python     │  │   Python     │
└──────────────┘  └──────────────┘  └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              PostgreSQL + pgvector + Redis                   │
└─────────────────────────────────────────────────────────────┘
```

## Tech Stack

### Frontend
- **Next.js 14** - Web applications with App Router
- **Electron** - Cross-platform desktop app
- **React Native + Expo** - Mobile applications
- **TypeScript** - Type safety
- **TanStack Query** - Data fetching and caching
- **Zustand** - State management
- **Tailwind CSS** - Styling

### Backend
- **.NET 8 Web API** - Main API Gateway with Clean Architecture
- **Entity Framework Core 8** - ORM
- **MediatR** - CQRS implementation
- **FluentValidation** - Input validation
- **Serilog** - Structured logging

### Python Microservices
- **FastAPI** - REST APIs
- **LangChain** - AI agent orchestration
- **Playwright** - Web scraping
- **OpenAI Whisper** - Transcription
- **APScheduler** - Job scheduling

### Data & Infrastructure
- **PostgreSQL 16 + pgvector** - Vector database for RAG
- **Redis** - Caching and session management
- **Docker + Docker Compose** - Containerization
- **nginx** - Reverse proxy
- **GitHub Actions** - CI/CD

## Prerequisites

- **Node.js** 20+
- **.NET 8 SDK**
- **Python** 3.11+
- **Docker** and Docker Compose
- **PostgreSQL** 16+ (or use Docker)

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/agentix/edupilot.git
   cd edupilot
   ```

2. **Copy environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Run setup script**
   ```bash
   bash scripts/setup.sh
   ```

4. **Start all services**
   ```bash
   docker-compose up -d
   ```

5. **Access the applications**
   - Web App: http://localhost:3000
   - Marketing Site: http://localhost:3001
   - API Gateway: http://localhost:5000
   - API Documentation: http://localhost:5000/swagger

## Development

### Install dependencies
```bash
npm install
```

### Start development servers
```bash
npm run dev
```

### Run tests
```bash
npm run test
```

### Build for production
```bash
npm run build
```

### Build desktop app
```bash
bash scripts/build-desktop.sh
```

## Project Structure

```
edupilot/
├── apps/
│   ├── web/                    # Student Web App (Next.js)
│   ├── desktop/                # Desktop App (Electron)
│   ├── mobile/                 # Mobile App (React Native)
│   └── marketing/              # Marketing Site (Next.js)
├── services/
│   ├── api-gateway/            # .NET 8 Web API
│   ├── ai-agent/               # Python FastAPI + LangChain
│   ├── lms-scraper/            # Python FastAPI + Playwright
│   ├── transcription/          # Python FastAPI + Whisper
│   └── scheduler/              # Python FastAPI + APScheduler
├── packages/
│   ├── ui/                     # Shared React components
│   ├── types/                  # Shared TypeScript types
│   └── utils/                  # Shared utilities
├── infrastructure/
│   ├── docker/                 # Docker configurations
│   └── nginx/                  # nginx configurations
├── scripts/
│   ├── setup.sh                # Development setup
│   ├── build-desktop.sh        # Build desktop installers
│   └── deploy.sh               # Production deployment
└── docker-compose.yml          # Local development stack
```

## Environment Variables

See `.env.example` for all required environment variables. Key variables include:

- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `OPENAI_API_KEY` - OpenAI API key for AI features
- `JWT_SECRET_KEY` - Secret key for JWT tokens
- Service URLs for microservices communication

## API Documentation

Once the API Gateway is running, visit http://localhost:5000/swagger for interactive API documentation.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details

## Support

For support, email support@agentix.ai or join our Discord community.

---

Built with ❤️ by Agentix
