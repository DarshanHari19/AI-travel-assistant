import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

// Get API URL from environment variable (Vite uses import.meta.env)
// PRODUCTION: Railway URL hardcoded as fallback
// Build v4-final - Last attempt to bypass Vercel cache
const API_URL = import.meta.env.VITE_API_URL || 'https://ai-travel-assistant-production.up.railway.app';

// Debug: Log API URL on component load (build verification)
console.log('Travel Assistant - API URL configured:', API_URL);
console.log('Environment check - VITE_API_URL:', import.meta.env.VITE_API_URL);
console.log('Build version: v4-final');

const StrategicTravelAssistant = () => {
  // State management
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Welcome! I\'m your Strategic Business Travel Assistant. I can help you with weather forecasts, packing recommendations, flight delay predictions, and travel planning. Where are you heading?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);
  const [inputError, setInputError] = useState('');
  
  // Ref for auto-scrolling
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Input validation function
  const validateInput = (message) => {
    // Length checks
    if (message.length === 0) {
      return 'Message cannot be empty';
    }
    if (message.length > 2000) {
      return 'Message is too long (max 2000 characters)';
    }

    // Check for suspicious patterns (prompt injection attempts)
    const injectionPatterns = [
      /ignore\s+(previous|all|prior)\s+instructions?/i,
      /ignore\s+all\s+previous/i,
      /new\s+instructions?:/i,
      /system:/i,
      /(^|\s)assistant:/i,
      /<\|im_start\|>/i,
      /<\|im_end\|>/i,
      /\[SYSTEM\]/i,
      /\[INST\]/i,
    ];

    for (const pattern of injectionPatterns) {
      if (pattern.test(message)) {
        return 'Message contains potentially unsafe content. Please rephrase your question.';
      }
    }

    // Check for excessive special characters (might indicate injection attempt)
    const specialCharCount = (message.match(/[!@#$%^&*(){}[\]]/g) || []).length;
    if (specialCharCount > 20) {
      return 'Message contains too many special characters. Please use normal text.';
    }

    // Check for repetitive character spam
    if (/(.)\1{20,}/.test(message)) {
      return 'Message contains suspicious repetitive patterns.';
    }

    return null; // Valid input
  };

  // Auto-scroll to bottom when new messages arrive
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  // Handle sending messages
  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    
    // Validate input
    const validationError = validateInput(userMessage);
    if (validationError) {
      setInputError(validationError);
      return;
    }

    // Clear any previous errors
    setInputError('');
    setInput('');

    // Add user message to chat
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // POST to backend API (uses environment-based URL)
      const response = await axios.post(`${API_URL}/chat`, {
        message: userMessage,
        session_id: sessionId
      });

      // Add assistant response to chat
      setMessages(prev => [
        ...prev,
        { role: 'assistant', content: response.data.response }
      ]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      // Handle different error types
      let errorMessage = 'I apologize, but I encountered an error. Please try again.';
      
      if (error.response) {
        // Handle specific HTTP status codes
        if (error.response.status === 429) {
          errorMessage = '⏰ Rate limit exceeded. Please wait a moment before sending more messages.';
        } else if (error.response.status === 400) {
          errorMessage = `⚠️ ${error.response.data?.message || error.response.data?.detail || 'Invalid request. Please check your input.'}`;
        } else if (error.response.status === 504) {
          errorMessage = '⏱️ The request timed out. Please try again with a simpler query.';
        } else if (error.response.status === 503) {
          errorMessage = '🔧 The service is temporarily unavailable. Please try again in a moment.';
        } else if (error.response.data?.message) {
          errorMessage = `❌ ${error.response.data.message}`;
        } else if (error.response.data?.detail) {
          errorMessage = `❌ ${error.response.data.detail}`;
        }
      } else if (error.request) {
        errorMessage = '🌐 Unable to reach the server. Please check your connection.';
      }
      
      // Add error message to chat
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          content: errorMessage
        }
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  // Handle Enter key
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Clear chat
  const handleClear = () => {
    setMessages([
      {
        role: 'assistant',
        content: 'Chat cleared. How can I assist you with your travel plans today?'
      }
    ]);
  };

  return (
    <div className="flex flex-col h-screen max-w-6xl mx-auto p-4">
      {/* Header */}
      <header className="bg-white shadow-lg rounded-t-2xl border-b border-executive-slate-200">
        <div className="px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center justify-center w-12 h-12 bg-gradient-to-br from-executive-indigo-500 to-executive-indigo-700 rounded-xl shadow-md">
                <svg 
                  className="w-7 h-7 text-white" 
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
                <h1 className="text-2xl font-bold text-executive-slate-900">
                  Strategic Travel Assistant
                </h1>
                <p className="text-sm text-executive-slate-600 mt-0.5">
                  Powered by AI • Weather Intelligence
                </p>
              </div>
            </div>
            <button
              onClick={handleClear}
              className="px-4 py-2 text-sm font-medium text-executive-slate-600 hover:text-executive-slate-900 hover:bg-executive-slate-100 rounded-lg transition-colors"
            >
              Clear Chat
            </button>
          </div>
        </div>
      </header>

      {/* Messages Container */}
      <div className="flex-1 bg-white shadow-lg overflow-hidden">
        <div className="h-full overflow-y-auto chat-scroll px-6 py-6 space-y-6">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-2xl px-5 py-4 shadow-sm ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-executive-indigo-500 to-executive-indigo-600 text-white'
                    : 'bg-executive-slate-50 text-executive-slate-900 border border-executive-slate-200'
                }`}
              >
                <div className="flex items-start space-x-3">
                  {message.role === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-executive-indigo-500 to-executive-indigo-700 rounded-full flex items-center justify-center shadow-md">
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
                          d="M13 10V3L4 14h7v7l9-11h-7z" 
                        />
                      </svg>
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium mb-2 opacity-75">
                      {message.role === 'user' ? 'You' : 'Assistant'}
                    </p>
                    <div className="text-base leading-relaxed whitespace-pre-wrap break-words">
                      {message.content}
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
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex justify-start">
              <div className="max-w-3xl rounded-2xl px-5 py-4 bg-executive-slate-50 border border-executive-slate-200 shadow-sm">
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-gradient-to-br from-executive-indigo-500 to-executive-indigo-700 rounded-full flex items-center justify-center shadow-md">
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
                        d="M13 10V3L4 14h7v7l9-11h-7z" 
                      />
                    </svg>
                  </div>
                  <div className="flex space-x-2">
                    <div className="w-2 h-2 bg-executive-slate-400 rounded-full animate-pulse" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-executive-slate-400 rounded-full animate-pulse" style={{ animationDelay: '200ms' }}></div>
                    <div className="w-2 h-2 bg-executive-slate-400 rounded-full animate-pulse" style={{ animationDelay: '400ms' }}></div>
                  </div>
                  <span className="text-sm text-executive-slate-600">Analyzing...</span>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white shadow-lg rounded-b-2xl border-t border-executive-slate-200">
        <div className="px-6 py-5">
          {/* Error message display */}
          {inputError && (
            <div className="mb-3 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center space-x-2">
              <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <span>{inputError}</span>
            </div>
          )}
          
          <div className="flex space-x-4">
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => {
                  setInput(e.target.value);
                  // Clear error when user starts typing
                  if (inputError) setInputError('');
                }}
                onKeyPress={handleKeyPress}
                placeholder="Ask about weather, packing tips, flight delays..."
                disabled={isLoading}
                rows="1"
                className={`w-full px-5 py-3 bg-executive-slate-50 border rounded-xl 
                         text-executive-slate-900 placeholder-executive-slate-400
                         focus:outline-none focus:ring-2 focus:ring-executive-indigo-500 focus:border-transparent
                         disabled:opacity-50 disabled:cursor-not-allowed
                         resize-none transition-all duration-200
                         ${inputError ? 'border-red-300 focus:ring-red-500' : 'border-executive-slate-300'}`}
                style={{ minHeight: '52px', maxHeight: '150px' }}
                onInput={(e) => {
                  e.target.style.height = 'auto';
                  e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
                }}
              />
              <div className="absolute right-3 bottom-3 text-xs text-executive-slate-400 flex items-center space-x-2">
                <span className="text-executive-slate-300">{input.length}/2000</span>
                <span>• Press Enter to send</span>
              </div>
            </div>
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="px-8 py-3 bg-gradient-to-r from-executive-indigo-500 to-executive-indigo-600 
                       text-white font-medium rounded-xl shadow-md
                       hover:from-executive-indigo-600 hover:to-executive-indigo-700
                       focus:outline-none focus:ring-2 focus:ring-executive-indigo-500 focus:ring-offset-2
                       disabled:opacity-50 disabled:cursor-not-allowed
                       transition-all duration-200 transform hover:scale-105 active:scale-95
                       flex items-center space-x-2"
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
                  <span>Sending</span>
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
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" 
                    />
                  </svg>
                  <span>Send</span>
                </>
              )}
            </button>
          </div>
          
          {/* Example queries */}
          <div className="mt-4 flex flex-wrap gap-2">
            <span className="text-xs text-executive-slate-500 font-medium">Try asking:</span>
            {[
              "Weather in London?",
              "Packing for Tokyo trip",
              "Flight delays to Paris?"
            ].map((example, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setInput(example);
                  inputRef.current?.focus();
                }}
                disabled={isLoading}
                className="px-3 py-1 text-xs font-medium text-executive-indigo-600 bg-executive-indigo-50 
                         hover:bg-executive-indigo-100 rounded-lg transition-colors
                         disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="mt-4 text-center">
        <p className="text-xs text-executive-slate-500">
          Powered by GPT-4 and OpenWeatherMap • Real-time Travel Intelligence
        </p>
      </div>
    </div>
  );
};

export default StrategicTravelAssistant;
