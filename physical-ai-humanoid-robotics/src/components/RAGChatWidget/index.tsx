/**
 * RAGChatWidget - Secure RAG-Powered Chatbot for Physical AI & Humanoid Robotics
 *
 * SECURITY FEATURES:
 * - NO API keys or credentials in frontend code
 * - All API calls go through backend proxy
 * - Sanitized error messages (no internal details)
 *
 * MODES:
 * 1. Book Mode - Full RAG with Qdrant vector search
 * 2. Selection-Only Mode - Uses ONLY highlighted text (NO Qdrant)
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import styles from './styles.module.css';

// API Configuration - Backend proxy only (NO direct external API calls)
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Types
interface Citation {
  chunk_id: string;
  content: string;
  source_path: string;
  module: string;
  chapter: string;
  section: string;
  score: number;
}

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  mode?: 'book' | 'selection_only';
  timestamp: Date;
  isStreaming?: boolean;
  error?: boolean;
}

interface RAGQueryResponse {
  answer: string;
  citations: Citation[];
  mode: string;
  query: string;
  token_usage: { [key: string]: number };
  processing_time_ms: number;
}

// Text Selection Popup Component
function SelectionPopup({
  position,
  onAskAbout,
  onClose,
}: {
  position: { x: number; y: number } | null;
  onAskAbout: () => void;
  onClose: () => void;
}) {
  if (!position) return null;

  return (
    <div
      className={styles.selectionPopup}
      style={{
        left: position.x,
        top: position.y,
      }}
    >
      <button onClick={onAskAbout} className={styles.selectionButton}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
          <path
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            stroke="currentColor"
            strokeWidth="2"
          />
        </svg>
        Ask about this selection
      </button>
      <button onClick={onClose} className={styles.selectionCloseBtn}>
        x
      </button>
    </div>
  );
}

// Citation Card Component
function CitationCard({ citation, index }: { citation: Citation; index: number }) {
  const [expanded, setExpanded] = useState(false);

  // Don't show citation details for user selections
  if (citation.chunk_id === 'user_selection') {
    return null;
  }

  return (
    <div className={styles.citationCard}>
      <div className={styles.citationHeader} onClick={() => setExpanded(!expanded)}>
        <span className={styles.citationIndex}>[{index + 1}]</span>
        <span className={styles.citationSource}>
          {citation.module} &gt; {citation.section}
        </span>
        <span className={styles.citationScore}>
          {Math.round(citation.score * 100)}% match
        </span>
        <span className={styles.expandIcon}>{expanded ? '-' : '+'}</span>
      </div>
      {expanded && (
        <div className={styles.citationContent}>
          <p>{citation.content}</p>
          <small>Source: {citation.source_path}</small>
        </div>
      )}
    </div>
  );
}

export default function RAGChatWidget(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectionPosition, setSelectionPosition] = useState<{ x: number; y: number } | null>(null);
  const [mode, setMode] = useState<'book' | 'selection'>('book');
  const [moduleFilter, setModuleFilter] = useState<string>('');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Handle text selection on the page
  useEffect(() => {
    const handleSelection = () => {
      const selection = window.getSelection();
      const text = selection?.toString().trim();

      if (text && text.length >= 10 && text.length <= 5000) {
        const range = selection?.getRangeAt(0);
        const rect = range?.getBoundingClientRect();

        if (rect) {
          setSelectedText(text);
          setSelectionPosition({
            x: rect.left + rect.width / 2,
            y: rect.top - 50,
          });
        }
      } else {
        setSelectedText('');
        setSelectionPosition(null);
      }
    };

    document.addEventListener('mouseup', handleSelection);
    return () => document.removeEventListener('mouseup', handleSelection);
  }, []);

  // Welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: `Welcome to the **Secure RAG Assistant**!

I use advanced AI to answer your questions from the textbook:

**Two Modes:**
- **Book Mode** - Search the entire book for answers with citations
- **Selection Mode** - Highlight text and I'll explain ONLY that selection

**Topics I cover:**
- **Module 1:** ROS 2 - Nodes, Topics, Services, URDF
- **Module 2:** Digital Twins - Gazebo, Unity, Sensors
- **Module 3:** NVIDIA Isaac - Sim, Nav2, Perception
- **Module 4:** VLA - Voice Commands, LLMs, Manipulation

**Tip:** Select any text on the page and click "Ask about this selection" for focused explanations!`,
          timestamp: new Date(),
        },
      ]);
    }
  }, [messages.length]);

  // Handle asking about selected text
  const handleAskAboutSelection = () => {
    if (selectedText) {
      setMode('selection');
      setIsOpen(true);
      setInput(`Explain this: "${selectedText.substring(0, 100)}${selectedText.length > 100 ? '...' : ''}"`);
      setSelectionPosition(null);
    }
  };

  // Send message to backend API (SECURE - no direct external API calls)
  const sendMessage = async () => {
    if (!input.trim() || isTyping) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      mode: mode === 'selection' && selectedText ? 'selection_only' : 'book',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const userQuery = input.trim();
    setInput('');
    setIsTyping(true);

    // Create placeholder for streaming response
    const assistantMessageId = `assistant-${Date.now()}`;
    setMessages((prev) => [
      ...prev,
      {
        id: assistantMessageId,
        role: 'assistant',
        content: '',
        citations: [],
        isStreaming: true,
        timestamp: new Date(),
      },
    ]);

    try {
      let response: RAGQueryResponse;

      if (mode === 'selection' && selectedText) {
        // Selection-only mode - Backend will NOT query Qdrant
        const res = await fetch(`${API_BASE_URL}/api/rag/query-selection`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: userQuery,
            selected_text: selectedText,
            temperature: 0.7,
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        response = await res.json();
      } else {
        // Book mode - Full RAG with Qdrant
        const res = await fetch(`${API_BASE_URL}/api/rag/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            query: userQuery,
            top_k: 5,
            module_filter: moduleFilter || undefined,
            min_score: 0.5,
            temperature: 0.7,
          }),
        });

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        response = await res.json();
      }

      // Update message with response
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: response.answer,
                citations: response.citations,
                mode: response.mode as 'book' | 'selection_only',
                isStreaming: false,
              }
            : msg
        )
      );
    } catch (error) {
      console.error('RAG API error:', error);

      // SECURITY: Don't expose internal error details to user
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                content: `I'm having trouble connecting to the assistant. Please try again.

**Troubleshooting:**
- Check if the backend server is running
- Ensure your internet connection is stable
- Try refreshing the page

If the problem persists, browse the book content directly!`,
                isStreaming: false,
                error: true,
              }
            : msg
        )
      );
    }

    setIsTyping(false);
    setMode('book'); // Reset to book mode
    setSelectedText(''); // Clear selection
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (content: string) => {
    let formatted = content
      .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br />');
    formatted = formatted.replace(/- /g, '<span class="bullet">-</span> ');
    return formatted;
  };

  const quickQuestions = [
    'What is ROS 2?',
    'Explain VLA pipeline',
    'How does Nav2 navigation work?',
    'What is a Digital Twin?',
  ];

  const modules = [
    { id: '', name: 'All Modules' },
    { id: 'module-1-ros2', name: 'Module 1: ROS 2' },
    { id: 'module-2-digital-twin', name: 'Module 2: Digital Twin' },
    { id: 'module-3-isaac', name: 'Module 3: Isaac' },
    { id: 'module-4-vla', name: 'Module 4: VLA' },
  ];

  return (
    <>
      {/* Selection Popup */}
      <SelectionPopup
        position={selectionPosition}
        onAskAbout={handleAskAboutSelection}
        onClose={() => setSelectionPosition(null)}
      />

      {/* Chat Toggle Button */}
      <button
        className={styles.chatToggle}
        onClick={() => setIsOpen(!isOpen)}
        aria-label={isOpen ? 'Close chat' : 'Open chat'}
      >
        {isOpen ? (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M18 6L6 18M6 6l12 12"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <path
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
        {mode === 'selection' && selectedText && (
          <span className={styles.selectionBadge}>Selection</span>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className={styles.chatWindow}>
          <div className={styles.chatHeader}>
            <div className={styles.headerInfo}>
              <span className={styles.headerTitle}>
                {mode === 'selection' ? 'Selection Mode' : 'RAG Assistant'}
              </span>
              <span className={styles.headerStatus}>
                {isTyping ? 'Thinking...' : 'Secure RAG Chatbot'}
              </span>
            </div>
            <button
              className={styles.closeButton}
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              x
            </button>
          </div>

          {/* Mode Indicator */}
          <div className={styles.modeIndicator}>
            <span className={mode === 'book' ? styles.activeMode : ''}>
              Book Mode
            </span>
            <span className={mode === 'selection' ? styles.activeMode : ''}>
              Selection Mode
            </span>
          </div>

          {/* Module Filter (only in Book mode) */}
          {mode === 'book' && (
            <div className={styles.filterBar}>
              <select
                value={moduleFilter}
                onChange={(e) => setModuleFilter(e.target.value)}
                className={styles.moduleSelect}
              >
                {modules.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Selected Text Preview (only in Selection mode) */}
          {selectedText && mode === 'selection' && (
            <div className={styles.selectionPreview}>
              <span className={styles.previewLabel}>Selected text:</span>
              <span className={styles.previewText}>
                "{selectedText.substring(0, 150)}
                {selectedText.length > 150 ? '...' : ''}"
              </span>
              <button
                onClick={() => { setSelectedText(''); setMode('book'); }}
                className={styles.clearSelection}
              >
                Clear
              </button>
            </div>
          )}

          {/* Messages */}
          <div className={styles.messagesContainer}>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`${styles.message} ${
                  message.role === 'user' ? styles.userMessage : styles.assistantMessage
                } ${message.error ? styles.errorMessage : ''}`}
              >
                {message.mode && (
                  <div className={styles.messageMode}>
                    {message.mode === 'selection_only' ? 'Selection Mode' : 'Book Mode'}
                  </div>
                )}
                <div
                  className={styles.messageContent}
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                />
                {message.isStreaming && (
                  <div className={styles.loadingDots}>
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                )}
                {message.citations && message.citations.length > 0 && message.mode === 'book' && (
                  <div className={styles.citations}>
                    <div className={styles.citationsHeader}>Sources ({message.citations.length})</div>
                    {message.citations.map((citation, i) => (
                      <CitationCard key={citation.chunk_id} citation={citation} index={i} />
                    ))}
                  </div>
                )}
              </div>
            ))}
            {isTyping && !messages.find((m) => m.isStreaming) && (
              <div className={`${styles.message} ${styles.assistantMessage}`}>
                <div className={styles.loadingDots}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions (only in Book mode and at start) */}
          {messages.length <= 1 && mode === 'book' && (
            <div className={styles.quickQuestions}>
              {quickQuestions.map((q, i) => (
                <button
                  key={i}
                  className={styles.quickQuestion}
                  onClick={() => {
                    setInput(q);
                    setTimeout(() => sendMessage(), 100);
                  }}
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className={styles.inputContainer}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                mode === 'selection'
                  ? 'Ask about the selected text...'
                  : 'Ask about ROS 2, VLA, Nav2, Isaac...'
              }
              className={styles.input}
              disabled={isTyping}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isTyping}
              className={styles.sendButton}
              aria-label="Send message"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path
                  d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>
          </div>
        </div>
      )}
    </>
  );
}
