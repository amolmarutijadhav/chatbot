# Intelligent MCP Chatbot Frontend

A modern, responsive React frontend for the Intelligent MCP Chatbot system.

## Features

- 🎨 **Modern UI/UX** - Clean, responsive design with Tailwind CSS
- 💬 **Real-time Chat** - Interactive chat interface with typing indicators
- 📊 **System Status** - Live system health and statistics monitoring
- 🔄 **Session Management** - Create new sessions and manage conversations
- ⚡ **Fast Performance** - Optimized with React hooks and efficient rendering
- 📱 **Mobile Responsive** - Works perfectly on all device sizes

## Tech Stack

- **React 18** - Modern React with hooks
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API communication
- **Lucide React** - Beautiful icons
- **Date-fns** - Date formatting utilities

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- The backend API server running on `localhost:8000`

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

3. Open [http://localhost:3000](http://localhost:3000) in your browser.

### Building for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/          # React components
│   ├── ChatInterface.tsx    # Main chat interface
│   ├── ChatMessage.tsx      # Individual message component
│   ├── ChatInput.tsx        # Message input component
│   ├── TypingIndicator.tsx  # Loading indicator
│   └── SystemStatus.tsx     # System health display
├── services/            # API services
│   └── api.ts              # API client and endpoints
├── types/               # TypeScript type definitions
│   └── api.ts              # API response types
├── App.tsx              # Main app component
├── index.tsx            # React entry point
└── index.css            # Global styles
```

## API Integration

The frontend communicates with the backend API through:

- **Health Check**: `GET /api/v1/health`
- **Statistics**: `GET /api/v1/stats`
- **Chat**: `POST /api/v1/chat`
- **Sessions**: `POST/GET/DELETE /api/v1/sessions`

## Development

### Available Scripts

- `npm start` - Start development server
- `npm build` - Build for production
- `npm test` - Run tests
- `npm eject` - Eject from Create React App

### Environment Variables

Create a `.env` file in the root directory:

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
```

## Contributing

1. Follow the existing code style
2. Add TypeScript types for new features
3. Test your changes thoroughly
4. Update documentation as needed

## License

This project is part of the Intelligent MCP Chatbot system. 