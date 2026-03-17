# Strategic Travel Assistant - Frontend

A modern, professional React frontend for the Strategic Business Travel Assistant with real-time weather intelligence.

## Features

- ✨ **Executive Design** - Professional Slate and Indigo color palette
- 💬 **Real-time Chat** - Instant responses from AI agent
- 🎯 **Smart UI** - Loading states, auto-scroll, example queries
- 📱 **Responsive** - Works on desktop and mobile
- ⚡ **Fast** - Built with Vite and React 18

## Tech Stack

- **React 18** - Modern React with hooks
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling with custom executive theme
- **Axios** - HTTP client for API calls

## Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

## Usage

### Starting the Frontend

```bash
npm run dev
```

### Building for Production

```bash
npm run build
npm run preview
```

## Architecture

```
frontend/
├── src/
│   ├── components/
│   │   └── StrategicTravelAssistant.jsx  # Main chat component
│   ├── App.jsx                            # Root component
│   ├── main.jsx                           # Entry point
│   └── index.css                          # Global styles + Tailwind
├── index.html                             # HTML template
├── package.json                           # Dependencies
├── vite.config.js                         # Vite configuration
├── tailwind.config.js                     # Tailwind + Executive theme
└── postcss.config.js                      # PostCSS config
```

## Component Features

### State Management

```javascript
const [messages, setMessages] = useState([])    // Chat history
const [input, setInput] = useState('')          // Current input
const [isLoading, setIsLoading] = useState(false) // Loading state
```

### API Integration

```javascript
const handleSend = async () => {
  const response = await axios.post('http://localhost:8000/chat', {
    message: userMessage,
    session_id: sessionId
  });
  // Handle response...
}
```

### Executive Color Palette

- **Slate** - Professional grays and neutrals
  - Background: `executive-slate-50`
  - Text: `executive-slate-900`
  - Borders: `executive-slate-200`
  
- **Indigo** - Accent and interactive elements
  - Primary: `executive-indigo-500`
  - Buttons: `executive-indigo-600`
  - Hover: `executive-indigo-700`

## Key Features

### 1. Professional Design
- Clean, minimalist interface
- Executive color scheme (Slate + Indigo)
- Smooth animations and transitions
- Professional iconography

### 2. Smart Loading States
- Disabled input while processing
- Animated "thinking" indicator
- Loading spinner on send button
- Prevents duplicate submissions

### 3. User Experience
- Auto-scroll to latest message
- Auto-focus input field
- Enter to send (Shift+Enter for new line)
- Example queries for quick start
- Clear chat functionality

### 4. Message Display
- User messages: Right-aligned, Indigo gradient
- Assistant messages: Left-aligned, Slate background
- Avatar icons for visual distinction
- Proper text wrapping and formatting

## Configuration

### API Endpoint

The frontend connects to the backend at `http://localhost:8000/chat`. To change this:

1. Edit `src/components/StrategicTravelAssistant.jsx`
2. Update the axios URL in `handleSend`

Or use the Vite proxy (already configured):

```javascript
// Use relative URL
axios.post('/api/chat', { ... })
```

### Styling

Customize the theme in `tailwind.config.js`:

```javascript
extend: {
  colors: {
    executive: {
      slate: { /* your colors */ },
      indigo: { /* your colors */ }
    }
  }
}
```

## Example Queries

The UI includes example queries:
- "Weather in London?"
- "Packing for Tokyo trip"
- "Flight delays to Paris?"

Click any to populate the input field.

## Error Handling

The component gracefully handles:
- Network errors
- API errors
- Empty messages
- Loading state management

Errors are displayed as assistant messages to maintain conversation flow.

## Development

### Hot Module Replacement

Vite provides instant HMR. Changes to React components update immediately without losing state.

### ESLint (Optional)

Add ESLint for code quality:

```bash
npm install -D eslint eslint-plugin-react
```

## Production Deployment

### Build

```bash
npm run build
```

Outputs to `dist/` directory.

### Deploy Options

1. **Vercel**: `vercel deploy`
2. **Netlify**: `netlify deploy`
3. **Static Server**: Serve the `dist/` folder

### Environment Variables

For production, set:
- `VITE_API_URL` - Backend API URL

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

- Lazy loading for optimal bundle size
- Efficient re-renders with React hooks
- Optimized Tailwind CSS (purged in production)
- Fast dev server with Vite

## Screenshots

The interface features:
- Clean header with logo and title
- Scrollable message area
- Professional message bubbles
- Smart input with example queries
- Loading indicators

## Troubleshooting

### Port already in use

Change port in `vite.config.js`:

```javascript
server: {
  port: 3001, // or any available port
}
```

### API connection issues

Ensure backend is running on `http://localhost:8000`

### Styling not loading

Clear cache and restart:

```bash
rm -rf node_modules/.vite
npm run dev
```

## License

MIT

---

**Ready to use!** Start both backend and frontend for the complete experience.

```bash
# Terminal 1 - Backend
cd backend-agent
python agent.py

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Visit `http://localhost:3000` to chat with your Strategic Travel Assistant! 🚀
