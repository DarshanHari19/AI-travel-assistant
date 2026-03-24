import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

// Risk Level Calculator
const calculateRiskLevel = (content) => {
  const lowerContent = content.toLowerCase();
  
  // Check for explicit low-risk phrases first (these override keyword matching)
  const lowRiskPhrases = [
    'no delays', 'unlikely to experience delays', 'delays are unlikely',
    'should not be concerned', 'should not worry', 'smooth sailing',
    'no significant', 'minimal risk', 'favorable conditions',
    'clear skies', 'good weather', 'excellent conditions',
    'should have no issues', 'no weather-related concerns'
  ];
  
  for (const phrase of lowRiskPhrases) {
    if (lowerContent.includes(phrase)) {
      return { level: 'LOW', color: 'from-green-500 to-emerald-500', bgColor: 'bg-green-500/10', textColor: 'text-green-400' };
    }
  }
  
  // High risk indicators (specific negative conditions)
  const highRiskPhrases = [
    'severe', 'dangerous', 'extreme', 'significant delays',
    'heavy storm', 'major delays', 'flight cancellations',
    'do not travel', 'strongly advise against', 'hazardous'
  ];
  
  for (const phrase of highRiskPhrases) {
    if (lowerContent.includes(phrase)) {
      return { level: 'HIGH', color: 'from-red-500 to-red-600', bgColor: 'bg-red-500/10', textColor: 'text-red-400' };
    }
  }
  
  // Medium risk indicators (check for concerning patterns without negative context)
  const moderateRiskPhrases = [
    'possible delays', 'may experience delays', 'could cause delays',
    'moderate risk', 'some delays', 'potential for delays',
    'heavy rain', 'strong winds', 'stormy conditions',
    'consider delays', 'expect some delays'
  ];
  
  for (const phrase of moderateRiskPhrases) {
    if (lowerContent.includes(phrase)) {
      return { level: 'MODERATE', color: 'from-yellow-500 to-orange-500', bgColor: 'bg-yellow-500/10', textColor: 'text-yellow-400' };
    }
  }
  
  // Default to LOW if no specific risk indicators found
  return { level: 'LOW', color: 'from-green-500 to-emerald-500', bgColor: 'bg-green-500/10', textColor: 'text-green-400' };
};

// Risk Meter Component
const RiskMeter = ({ level, color, bgColor, textColor }) => (
  <div className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg ${bgColor} border border-white/10`}>
    <div className="relative w-16 h-2 bg-slate-700 rounded-full overflow-hidden">
      <div 
        className={`absolute left-0 top-0 h-full bg-gradient-to-r ${color} rounded-full transition-all duration-500`}
        style={{ 
          width: level === 'HIGH' ? '100%' : level === 'MODERATE' ? '60%' : '30%' 
        }}
      ></div>
    </div>
    <span className={`text-xs font-bold tracking-wider ${textColor}`}>
      {level} RISK
    </span>
  </div>
);

// System Log Component
const SystemLog = ({ toolCalls, citiesAnalyzed, isOpen, setIsOpen }) => {
  if (!toolCalls || toolCalls.length === 0) return null;
  
  return (
    <div className="mb-3">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 text-xs text-slate-400 hover:text-slate-300 transition-colors group"
      >
        <svg 
          className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-90' : ''}`}
          fill="none" 
          stroke="currentColor" 
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
        <span className="font-semibold uppercase tracking-wider">System Reasoning</span>
        <span className="text-slate-500">({toolCalls.length} operations)</span>
      </button>
      
      {isOpen && (
        <div className="mt-2 space-y-1.5 pl-5 border-l-2 border-indigo-500/30">
          {toolCalls.map((call, idx) => (
            <div 
              key={idx}
              className="flex items-center space-x-2 text-xs"
            >
              <div className={`w-1.5 h-1.5 rounded-full ${
                call.status === 'success' ? 'bg-green-400' : 'bg-red-400'
              }`}></div>
              <span className="text-slate-400">
                {call.status === 'success' ? '✓' : '✗'}
              </span>
              <span className="text-slate-300">
                Fetched {call.city} weather data
              </span>
              <span className="text-slate-500 text-[10px]">
                {new Date(call.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
          {citiesAnalyzed && citiesAnalyzed.length > 0 && (
            <div className="pt-1.5 mt-1.5 border-t border-white/5">
              <span className="text-slate-400 text-xs">
                Analyzed: <span className="text-indigo-400 font-medium">{citiesAnalyzed.join(', ')}</span>
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

function App() {
  // State management
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Welcome to your Strategic Travel Assistant. I provide executive-level travel intelligence powered by real-time weather data.\n\n**I can help you with:**\n- Weather forecasts and 3-day outlooks\n- Flight delay predictions based on conditions\n- Tailored packing recommendations\n- Optimal travel timing analysis\n\nWhere are you headed?',
      toolCalls: [],
      citiesAnalyzed: []
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [openLogIndex, setOpenLogIndex] = useState(null);
  
  // Auto-scroll ref
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom when messages change
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Handle message submission
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage, toolCalls: [], citiesAnalyzed: [] }]);
    setIsLoading(true);

    try {
      // POST to backend API
      const response = await axios.post('http://localhost:8000/chat', {
        message: userMessage,
        session_id: 'demo-user'
      });

      // Add assistant response to chat with metadata
      setMessages(prev => [
        ...prev,
        { 
          role: 'assistant', 
          content: response.data.response,
          toolCalls: response.data.tool_calls || [],
          citiesAnalyzed: response.data.cities_analyzed || []
        }
      ]);
    } catch (error) {
      console.error('Error:', error);
      
      // Add error message
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: `**System Error**\n\nI encountered an issue processing your request: ${error.response?.data?.detail || error.message}\n\nPlease verify the backend service is running and try again.`,
          toolCalls: [],
          citiesAnalyzed: []
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-indigo-900">
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-4xl flex flex-col h-[90vh] bg-white/5 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/10">
          
          {/* Header */}
          <div className="px-8 py-6 border-b border-white/10">
            <div className="flex items-center space-x-4">
              <div className="flex items-center justify-center w-14 h-14 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-xl shadow-lg">
                <svg 
                  className="w-8 h-8 text-white" 
                  fill="none" 
                  stroke="currentColor" 
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" 
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-widest">
                  STRATEGIC TRAVEL ASSISTANT
                </h1>
                <p className="text-sm text-slate-300 tracking-widest mt-1">
                  EXECUTIVE INTELLIGENCE • POWERED BY AI
                </p>
              </div>
            </div>
          </div>

          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto px-8 py-6 space-y-6 chat-scroll">
            {messages.map((message, index) => {
              const riskInfo = message.role === 'assistant' ? calculateRiskLevel(message.content) : null;
              
              return (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-3xl rounded-xl px-6 py-4 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-indigo-600 to-indigo-700 text-white shadow-lg'
                        : 'bg-white border border-slate-200 text-slate-900 shadow-md'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      {message.role === 'assistant' && (
                        <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-full flex items-center justify-center shadow-md">
                          <svg 
                            className="w-5 h-5 text-white" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path 
                              strokeLinecap="round" 
                              strokeLinejoin="round" 
                              strokeWidth={2} 
                              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" 
                            />
                          </svg>
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-3">
                          <p className={`text-xs font-semibold uppercase tracking-wider ${
                            message.role === 'user' ? 'text-indigo-200' : 'text-slate-500'
                          }`}>
                            {message.role === 'user' ? 'You' : 'Strategic Assistant'}
                          </p>
                          {message.role === 'assistant' && riskInfo && (
                            <RiskMeter {...riskInfo} />
                          )}
                        </div>
                        
                        {/* System Log for Assistant Messages */}
                        {message.role === 'assistant' && message.toolCalls && (
                          <SystemLog 
                            toolCalls={message.toolCalls}
                            citiesAnalyzed={message.citiesAnalyzed}
                            isOpen={openLogIndex === index}
                            setIsOpen={(open) => setOpenLogIndex(open ? index : null)}
                          />
                        )}
                        
                        <div className={`prose prose-sm max-w-none ${
                          message.role === 'user' 
                            ? 'prose-invert prose-headings:text-white prose-p:text-white prose-li:text-white prose-strong:text-indigo-100' 
                            : 'prose-slate prose-headings:text-slate-900 prose-p:text-slate-700 prose-li:text-slate-700 prose-strong:text-slate-900'
                        }`}>
                          {message.role === 'assistant' ? (
                            <ReactMarkdown>{message.content}</ReactMarkdown>
                          ) : (
                            <p className="whitespace-pre-wrap">{message.content}</p>
                          )}
                        </div>
                      </div>
                      {message.role === 'user' && (
                        <div className="flex-shrink-0 w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                          <svg 
                            className="w-5 h-5 text-white" 
                            fill="none" 
                            stroke="currentColor" 
                            viewBox="0 0 24 24"
                          >
                            <path 
                              strokeLinecap="round" 
                              strokeLinejoin="round" 
                              strokeWidth={2} 
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" 
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-3xl rounded-xl px-6 py-4 bg-white border border-slate-200 shadow-md">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-indigo-500 to-indigo-700 rounded-full flex items-center justify-center shadow-md">
                      <svg 
                        className="w-5 h-5 text-white animate-pulse" 
                        fill="none" 
                        stroke="currentColor" 
                        viewBox="0 0 24 24"
                      >
                        <path 
                          strokeLinecap="round" 
                          strokeLinejoin="round" 
                          strokeWidth={2} 
                          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" 
                        />
                      </svg>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-slate-600 font-medium">Processing intelligence...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="px-8 py-6 border-t border-white/10">
            <div className="flex space-x-4">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about weather, flight delays, packing advice..."
                disabled={isLoading}
                rows="1"
                className="flex-1 px-5 py-4 bg-slate-800/50 border border-slate-600 rounded-xl 
                         text-white placeholder-slate-400
                         focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent
                         disabled:opacity-50 disabled:cursor-not-allowed
                         resize-none transition-all duration-200"
                style={{ minHeight: '56px', maxHeight: '120px' }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                }}
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-indigo-700 
                         text-white font-bold rounded-xl shadow-lg uppercase tracking-wider text-sm
                         hover:from-indigo-700 hover:to-indigo-800
                         focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 focus:ring-offset-slate-900
                         disabled:opacity-50 disabled:cursor-not-allowed
                         transition-all duration-200 transform hover:scale-105 active:scale-95
                         flex items-center space-x-2 min-w-[140px] justify-center"
              >
                {isLoading ? (
                  <>
                    <svg 
                      className="animate-spin h-5 w-5 text-white" 
                      xmlns="http://www.w3.org/2000/svg" 
                      fill="none" 
                      viewBox="0 0 24 24"
                    >
                      <circle 
                        className="opacity-25" 
                        cx="12" 
                        cy="12" 
                        r="10" 
                        stroke="currentColor" 
                        strokeWidth="4"
                      ></circle>
                      <path 
                        className="opacity-75" 
                        fill="currentColor" 
                        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      ></path>
                    </svg>
                    <span className="animate-bounce">Thinking...</span>
                  </>
                ) : (
                  <>
                    <svg 
                      className="w-5 h-5" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth={2} 
                        d="M13 10V3L4 14h7v7l9-11h-7z" 
                      />
                    </svg>
                    <span>Analyze</span>
                  </>
                )}
              </button>
            </div>

            {/* Example queries */}
            <div className="mt-4 flex flex-wrap gap-2">
              <span className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Quick Queries:</span>
              {[
                "Weather forecast for London",
                "Packing list for Tokyo in spring",
                "Will my Paris flight be delayed?"
              ].map((example, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(example)}
                  disabled={isLoading}
                  className="px-3 py-1.5 text-xs font-medium text-indigo-300 bg-indigo-900/30 
                           hover:bg-indigo-900/50 rounded-lg transition-colors border border-indigo-700/30
                           disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="px-8 py-4 border-t border-white/10">
            <p className="text-xs text-center text-slate-400 tracking-wider">
              POWERED BY GPT-4 • OPENWEATHERMAP API • REAL-TIME INTELLIGENCE
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
