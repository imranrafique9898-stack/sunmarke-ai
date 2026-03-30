# 🎓 Sunmarke Voice Agent - Frontend

Next.js frontend for the AI Voice Agent technical assessment. Uses Web Speech API for voice input and text-to-speech for audio output.

## Features

- 🎤 **Voice Recording**: Real-time speech-to-text using Web Speech API
- 🎯 **3-Column Layout**: Display responses from all 3 LLMs side-by-side
- 🔊 **Audio Playback**: Browser-based text-to-speech for responses
- 📱 **Responsive Design**: Mobile-friendly UI with Tailwind CSS
- ⚡ **Real-time Updates**: Live stats from backend

## Tech Stack

- **Framework**: Next.js 14 (TypeScript)
- **Styling**: Tailwind CSS
- **Voice I/O**: 
  - Speech-to-text: Web Speech API
  - Text-to-speech: Web Speech Synthesis API
- **HTTP Client**: Axios
- **State Management**: React Hooks

## Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure Environment

Create `.env.local`:

```bash
cp .env.example .env.local
```

Update with your backend URL (default: `http://localhost:8000`):

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features Explained

### Voice Recording
- Click "🎤 Start Recording" to begin speech recognition
- Speak your question naturally
- Click "⏹️ Stop Recording" when done
- Transcribed text appears in the textarea
- Click "📤 Send Query" to submit

### 3-Column Response Layout
- **Google Gemini** (🔵): Response from Google's Gemini model
- **Kimi (Moonshot)** (🟡): Response from Kimi/Moonshot AI
- **DeepSeek** (🔴): Response from DeepSeek model

All three models receive the same query and respond in parallel (~600ms combined).

### Audio Playback
- Click "🔊 Listen to Response" under any response
- Browser reads the text aloud
- Uses native Web Speech Synthesis API (no TTS fees)

## Browser Compatibility

### Speech Recognition (Voice Input)
- ✅ Chrome 25+
- ✅ Edge 79+
- ✅ Firefox 55+
- ❌ Safari (limited support)

### Text-to-Speech (Audio Output)
- ✅ All modern browsers
- Chrome, Edge, Firefox, Safari, Opera

## API Integration

The frontend calls the backend API at `NEXT_PUBLIC_API_URL`.

### Health Check
```bash
GET /health
```

### Query Endpoint
```bash
POST /api/query
Content-Type: application/json

{
  "query": "What is Sunmarke's mission?",
  "transcribed_text": "What is Sunmarke's mission?"
}
```

### Response
```json
{
  "query": "...",
  "rag": {
    "context": "...",
    "sources": ["..."],
    "chunks_count": 5
  },
  "responses": {
    "gemini": "...",
    "kimi": "...",
    "deepseek": "..."
  },
  "response_time_ms": 598
}
```

## Troubleshooting

**"Backend is not available"**
- Make sure backend is running at `http://localhost:8000`
- Check `NEXT_PUBLIC_API_URL` in `.env.local`
- Run `python backend/main.py` in another terminal

**Speech recognition not working**
- Use Chrome, Edge, or Firefox
- Check microphone permissions
- Reload the page

**No audio output**
- Check browser volume
- Try a different browser
- Check system audio settings

## Development

### Build for Production

```bash
npm run build
npm start
```

### Lint Code

```bash
npm run lint
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx      # Root layout
│   ├── page.tsx        # Main page
│   └── globals.css     # Global styles
├── components/
│   ├── VoiceRecorder.tsx   # Voice input component
│   ├── ResponseCard.tsx    # Response display card
│   └── AudioPlayer.tsx     # Audio playback
├── utils/
│   └── api.ts          # Backend API client
├── public/             # Static assets
├── package.json
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── README.md
```

## Deployment

### Vercel (Recommended)

```bash
vercel deploy
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

## Performance Tips

- **Parallel LLM calls**: Backend calls all 3 LLMs simultaneously (~600ms vs 1800ms sequential)
- **Lazy loading**: Components only render when needed
- **Optimized images**: Next.js auto-optimizes images
- **Code splitting**: Automatic by Next.js

## Security

- API keys stored on backend (not exposed to frontend)
- Environment variables for configuration
- CORS middleware on backend
- Input validation with Pydantic

## License

XPLServices Technical Assessment 2024

## Support

For issues or questions, refer to:
- [Frontend README](./README.md) - This file
- [Backend Setup](../BACKEND_SETUP.md) - Backend instructions
- [Architecture](../ARCHITECTURE.md) - System design
