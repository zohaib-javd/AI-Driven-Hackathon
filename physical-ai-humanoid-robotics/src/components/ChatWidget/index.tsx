/**
 * ChatWidget - Floating chatbot for Physical AI RAG
 *
 * A floating chat widget that provides AI-powered Q&A
 * about the Physical AI & Humanoid Robotics textbook.
 */

import React, { useState, useRef, useEffect, useCallback } from 'react';
import styles from './styles.module.css';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
  timestamp: Date;
  isVoice?: boolean;
}

interface Citation {
  chapter_title: string;
  chapter: string;
  module: string;
  excerpt: string;
  relevance_score: number;
}

interface ChatResponse {
  message: {
    content: string;
    citations: Citation[];
  };
  session_id: string;
  processing_time_ms: number;
}

const API_URL = process.env.NODE_ENV === 'production'
  ? 'https://your-backend-url.railway.app'
  : 'http://localhost:8000';

export default function ChatWidget(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showCitations, setShowCitations] = useState(false);
  const [selectedCitations, setSelectedCitations] = useState<Citation[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  // Welcome message
  useEffect(() => {
    if (messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content:
            "Hello! I'm your Physical AI assistant. I can help you with questions about:\n\n" +
            "• **ROS 2** - Nodes, topics, services, URDF\n" +
            "• **Gazebo & Unity** - Simulation and digital twins\n" +
            "• **NVIDIA Isaac** - Perception and navigation\n" +
            "• **VLA** - Voice-controlled autonomous robots\n\n" +
            "What would you like to learn about?",
          timestamp: new Date(),
        },
      ]);
    }
  }, [messages.length]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: sessionId,
          include_citations: true,
          max_context_chunks: 5,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data: ChatResponse = await response.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.message.content,
        citations: data.message.citations,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setSessionId(data.session_id);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content:
            "I'm sorry, I encountered an error. Please make sure the backend is running and try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const viewCitations = (citations: Citation[]) => {
    setSelectedCitations(citations);
    setShowCitations(true);
  };

  // Voice recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        stream.getTracks().forEach((track) => track.stop());
        await transcribeAudio(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Failed to start recording:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Could not access microphone. Please check your permissions.',
          timestamp: new Date(),
        },
      ]);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    setIsTranscribing(true);

    try {
      const formData = new FormData();
      formData.append('file', audioBlob, 'recording.wav');

      const response = await fetch(`${API_URL}/api/voice/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const data = await response.json();
      const transcribedText = data.text;

      if (transcribedText) {
        // Add voice message and send to chat
        const userMessage: Message = {
          id: `user-${Date.now()}`,
          role: 'user',
          content: transcribedText,
          timestamp: new Date(),
          isVoice: true,
        };

        setMessages((prev) => [...prev, userMessage]);
        await sendMessageToAPI(transcribedText);
      } else {
        setMessages((prev) => [
          ...prev,
          {
            id: `error-${Date.now()}`,
            role: 'assistant',
            content: "I couldn't understand the audio. Please try again.",
            timestamp: new Date(),
          },
        ]);
      }
    } catch (error) {
      console.error('Transcription error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: 'Voice transcription failed. Please type your message instead.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTranscribing(false);
    }
  };

  const sendMessageToAPI = async (message: string) => {
    setIsLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: sessionId,
          include_citations: true,
          max_context_chunks: 5,
          temperature: 0.7,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data: ChatResponse = await response.json();

      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: data.message.content,
        citations: data.message.citations,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setSessionId(data.session_id);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content:
            "I'm sorry, I encountered an error. Please make sure the backend is running and try again.",
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const formatMessage = (content: string) => {
    // Simple markdown-like formatting
    return content
      .split('\n')
      .map((line, i) => {
        // Bold
        line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Code
        line = line.replace(/`([^`]+)`/g, '<code>$1</code>');
        // Bullet points
        if (line.startsWith('• ') || line.startsWith('- ')) {
          return `<li key="${i}">${line.substring(2)}</li>`;
        }
        return line;
      })
      .join('<br />');
  };

  return (
    <>
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
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className={styles.chatWindow}>
          {/* Header */}
          <div className={styles.chatHeader}>
            <div className={styles.headerInfo}>
              <span className={styles.headerTitle}>Physical AI Assistant</span>
              <span className={styles.headerStatus}>
                {isLoading ? 'Thinking...' : 'Online'}
              </span>
            </div>
            <button
              className={styles.closeButton}
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ×
            </button>
          </div>

          {/* Messages */}
          <div className={styles.messagesContainer}>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`${styles.message} ${
                  message.role === 'user' ? styles.userMessage : styles.assistantMessage
                }`}
              >
                <div
                  className={styles.messageContent}
                  dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }}
                />
                {message.citations && message.citations.length > 0 && (
                  <button
                    className={styles.citationButton}
                    onClick={() => viewCitations(message.citations!)}
                  >
                    📚 {message.citations.length} source
                    {message.citations.length > 1 ? 's' : ''}
                  </button>
                )}
              </div>
            ))}
            {isLoading && (
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

          {/* Input */}
          <div className={styles.inputContainer}>
            {(isRecording || isTranscribing) && (
              <div className={styles.transcriptionIndicator}>
                <span>●</span>
                {isRecording ? 'Recording...' : 'Transcribing...'}
              </div>
            )}
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about ROS 2, Gazebo, Isaac..."
              className={styles.input}
              disabled={isLoading || isRecording || isTranscribing}
            />
            {/* Voice Button */}
            <button
              onClick={toggleRecording}
              disabled={isLoading || isTranscribing}
              className={`${styles.voiceButton} ${isRecording ? styles.recording : ''}`}
              aria-label={isRecording ? 'Stop recording' : 'Start voice input'}
              title={isRecording ? 'Stop recording' : 'Voice input'}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                {isRecording ? (
                  <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
                ) : (
                  <>
                    <path
                      d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z"
                      fill="currentColor"
                    />
                    <path
                      d="M19 10v2a7 7 0 01-14 0v-2"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                    <path
                      d="M12 19v4M8 23h8"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                    />
                  </>
                )}
              </svg>
            </button>
            <button
              onClick={sendMessage}
              disabled={!input.trim() || isLoading || isRecording}
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

      {/* Citations Modal */}
      {showCitations && (
        <div className={styles.citationsOverlay} onClick={() => setShowCitations(false)}>
          <div className={styles.citationsModal} onClick={(e) => e.stopPropagation()}>
            <div className={styles.citationsHeader}>
              <h3>Sources</h3>
              <button onClick={() => setShowCitations(false)}>×</button>
            </div>
            <div className={styles.citationsList}>
              {selectedCitations.map((citation, i) => (
                <div key={i} className={styles.citationItem}>
                  <div className={styles.citationTitle}>
                    📖 {citation.chapter_title}
                  </div>
                  <div className={styles.citationModule}>
                    {citation.module.replace(/-/g, ' ').replace('module', 'Module')}
                  </div>
                  <div className={styles.citationExcerpt}>{citation.excerpt}</div>
                  <div className={styles.citationScore}>
                    Relevance: {(citation.relevance_score * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
