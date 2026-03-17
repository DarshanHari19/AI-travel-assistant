# Setup Instructions - Executive Strategic Travel Assistant

## Quick Start

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

## What's New in This Refactor

### Executive-Grade Design
- **Dark Theme**: Deep Indigo and Slate gradient background
- **Premium Layout**: Thin centered column (max-width 4xl)
- **Glass Morphism**: Translucent backdrop with blur effects
- **Professional Typography**: All-caps headers with wide tracking

### Enhanced Features
1. **Rich Text Rendering**: Markdown support (headers, bullets, bold)
2. **Auto-Scroll**: Smooth scroll to newest messages
3. **Loading States**: 
   - Button changes from "Analyze" to "Thinking..." with bounce animation
   - Animated dots indicator in chat
4. **Fixed Session**: Uses 'demo-user' session_id for all requests

### API Integration
- Endpoint: `http://localhost:8000/chat`
- Payload: `{ "message": string, "session_id": "demo-user" }`
- Response: `{ "response": string, "session_id": string }`

### New Dependencies
- **react-markdown**: Renders assistant responses with proper formatting
- **@tailwindcss/typography**: Provides beautiful prose styles

## Running the Full Stack

### Terminal 1 - Backend
```bash
cd backend-agent
python3 agent.py
```

Backend runs on `http://localhost:8000`

### Terminal 2 - Frontend
```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`

## Design System

### Color Palette
- **Background**: Slate 900 → Indigo 900 gradient
- **User Messages**: Indigo 600-700 gradient
- **Assistant Messages**: White with subtle border
- **Accents**: Indigo 500-700 for icons and buttons

### Typography
- **Header**: "STRATEGIC TRAVEL ASSISTANT" - tracking-widest
- **Subhead**: "EXECUTIVE INTELLIGENCE • POWERED BY AI"
- **Labels**: Uppercase with wide tracking
- **Messages**: Prose typography for rich text

### Component Hierarchy
```
App.jsx (main container)
├── Header (branding + title)
├── Messages Container (scrollable)
│   ├── Message Bubbles (user/assistant)
│   ├── Loading Indicator (when processing)
│   └── Auto-scroll Ref
├── Input Area
│   ├── Textarea (with Enter key handling)
│   ├── Analyze/Thinking Button
│   └── Quick Query Chips
└── Footer (powered by info)
```

## Key Features

### 1. State Management
```javascript
const [messages, setMessages] = useState([...])  // Array of {role, content}
const [input, setInput] = useState('')           // Current input
const [isLoading, setIsLoading] = useState(false) // Loading state
```

### 2. Auto-Scroll
```javascript
const messagesEndRef = useRef(null)

useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
}, [messages])
```

### 3. Rich Text Rendering
```javascript
<ReactMarkdown>{message.content}</ReactMarkdown>
```

Supports:
- Headers (### Text)
- Bullet points (- Item)
- Bold text (**Bold**)
- Line breaks

### 4. Loading Animation
- Button text: "Analyze" → "Thinking..."
- Bounce animation on "Thinking..." text
- Spinning icon
- Animated dots in chat area

## Troubleshooting

### Dependencies not installing
```bash
rm -rf node_modules package-lock.json
npm install
```

### Backend not responding
Verify backend is running:
```bash
curl http://localhost:8000/health
```

### Port conflict
Change port in `vite.config.js`:
```javascript
server: {
  port: 3001, // or any available port
}
```

### Markdown not rendering
Ensure `react-markdown` is installed:
```bash
npm install react-markdown
```

## Development Tips

### Testing Messages
Use the quick query chips to test:
- "Weather forecast for London"
- "Packing list for Tokyo in spring"
- "Will my Paris flight be delayed?"

### Inspecting State
Add console logs in `handleSend`:
```javascript
console.log('Messages:', messages)
console.log('Response:', response.data)
```

### Styling Changes
All styles are in:
- `src/App.jsx` (inline Tailwind classes)
- `src/index.css` (scrollbar, animations)
- `tailwind.config.js` (theme configuration)

## Production Build

```bash
npm run build
npm run preview
```

Outputs to `dist/` directory.

---

**Ready!** Start both services and visit `http://localhost:3000` for the executive experience. 🚀
