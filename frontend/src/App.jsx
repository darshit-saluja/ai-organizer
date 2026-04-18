import { useState, useCallback, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const MODAL_URL = import.meta.env.VITE_MODAL_URL || 'https://getluminousai--ai-organizer-backend-generate-roadmap.modal.run';

const PHRASES = [
  "Scanning source artifacts...",
  "Identifying cross-file themes...",
  "Mapping technical dependencies...",
  "Synthesizing execution phases...",
  "Finalizing roadmap document...",
  "Polishing strategic narrative..."
];

// ── Components ──

function PhraseCycler() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setIndex((i) => (i + 1) % PHRASES.length);
    }, 2500);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="phrase-container">
      <div className="spinner-small" />
      <span className="phrase-text">{PHRASES[index]}</span>
    </div>
  );
}

function CollapsibleRoadmap({ content }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="roadmap-container">
      <button 
        className="roadmap-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
      >
        <span>Project Roadmap</span>
        <svg 
          className={`arrow-icon ${isOpen ? 'open' : ''}`}
          viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.5"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>
      
      <div className={`roadmap-expandable ${isOpen ? 'open' : ''}`}>
        <div className="roadmap-content">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }) {
  const roadmapRegex = /\[ROADMAP_START\]([\s\S]*?)\[ROADMAP_END\]/;
  const match = message.content.match(roadmapRegex);
  const displayText = message.content.replace(roadmapRegex, '').trim();

  return (
    <div className={`message ${message.role}`}>
      <span className="message-label">{message.role === 'user' ? 'USER' : 'SYSTEM'}</span>
      <div className="message-content">
        {displayText && (
          <div className="chat-markdown-renderer">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayText}</ReactMarkdown>
          </div>
        )}
        {match && <CollapsibleRoadmap content={match[1].trim()} />}
      </div>
    </div>
  );
}

// ── Main App ──
export default function App() {
  const [files, setFiles] = useState([]);
  const [pendingFiles, setPendingFiles] = useState([]); // STAGED FILES
  const [messages, setMessages] = useState([]);
  const [currentRoadmap, setCurrentRoadmap] = useState(null);
  const [inputText, setInputText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  
  const scrollRef = useRef(null);
  const appendFilesRef = useRef(null);

  useEffect(() => {
    const handleBeforeUnload = (e) => {
      if (messages.length > 0) {
        e.preventDefault();
        e.returnValue = '';
      }
    };
    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [messages]);

  useEffect(() => {
    if (scrollRef.current && messages.length > 0) {
      scrollRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const processRequest = async (updatedMessages, currentFiles = files) => {
    setIsProcessing(true);
    try {
      const response = await fetch(MODAL_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          files: currentFiles, 
          messages: updatedMessages,
          current_roadmap: currentRoadmap
        }),
      });

      if (!response.ok) throw new Error(`Server error: ${response.status}`);
      const data = await response.json();
      if (data.error) throw new Error(data.error);

      // Add assistant response
      const assistantMsg = { role: 'assistant', content: data.response };
      setMessages(prev => [...prev, assistantMsg]);

      // Update roadmap state if present
      const roadmapRegex = /\[ROADMAP_START\]([\s\S]*?)\[ROADMAP_END\]/;
      const match = data.response.match(roadmapRegex);
      if (match) {
        setCurrentRoadmap(match[1].trim());
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: `[CRITICAL ERROR] ${err.message}` }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleInitialFiles = async (e) => {
    const acceptedFiles = Array.from(e.target.files);
    if (acceptedFiles.length === 0) return;

    const fileData = await Promise.all(
      acceptedFiles.map(file =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (ev) => resolve({
            filename: file.name,
            content: ev.target.result,
            word_count: ev.target.result.split(/\s+/).filter(Boolean).length,
            line_count: ev.target.result.split(/\r\n|\r|\n/).length,
          });
          reader.onerror = reject;
          reader.readAsText(file);
        })
      )
    );

    setFiles(fileData);
    const initialMsg = { role: 'user', content: "Please analyze these files and generate a comprehensive roadmap." };
    setMessages([initialMsg]);
    await processRequest([initialMsg], fileData);
  };

  // Stage files without sending
  const handleStageFiles = async (e) => {
    const acceptedFiles = Array.from(e.target.files);
    if (acceptedFiles.length === 0) return;

    const stagedData = await Promise.all(
      acceptedFiles.map(file =>
        new Promise((resolve, reject) => {
          const reader = new FileReader();
          reader.onload = (ev) => resolve({
            filename: file.name,
            content: ev.target.result,
            word_count: ev.target.result.split(/\s+/).filter(Boolean).length,
            line_count: ev.target.result.split(/\r\n|\r|\n/).length,
          });
          reader.onerror = reject;
          reader.readAsText(file);
        })
      )
    );

    setPendingFiles(prev => [...prev, ...stagedData]);
    // RESET THE INPUT so same file can be selected again if needed
    e.target.value = '';
  };

  const removePendingFile = (index) => {
    setPendingFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputText.trim() && pendingFiles.length === 0) return;
    if (isProcessing) return;

    // Merge staged files into permanent files context
    const updatedFiles = [...files, ...pendingFiles];
    if (pendingFiles.length > 0) {
      setFiles(updatedFiles);
    }

    const newMsg = { role: 'user', content: inputText };
    const updatedMessages = [...messages, newMsg];
    
    setMessages(updatedMessages);
    setInputText('');
    setPendingFiles([]); // HEAL THE QUEUE
    
    await processRequest(updatedMessages, updatedFiles);
  };

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1 className="header-title">AI Organizer</h1>
          <p className="header-sub" style={{ fontFamily: 'Space Mono', fontSize: '0.65rem', textTransform: 'uppercase', color: '#71717a', letterSpacing: '0.1em', marginTop: '0.4rem' }}>
            v2.2 // Context-Staged Workflow
          </p>
        </div>
        <div className="status-dot" />
      </header>

      <main className="chat-feed">
        {messages.length === 0 && (
          <div className="hero-box">
            <div className="hero-box-accent" />
            <h2 className="hero-title">Initialize Workspace</h2>
            <p className="hero-desc">
              Drop your scattered notes, brain dumps, and artifacts below. 
              The system will build a high-density roadmap to guide your execution.
            </p>
            
            <label className="dropzone-trigger">
              + Upload Artifacts
              <input type="file" multiple onChange={handleInitialFiles} style={{ display: 'none' }} />
            </label>
            <span className="dropzone-note">Supported formats: .txt, .md, .markdown</span>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}
        
        {isProcessing && messages.length > 0 && (
          <div className="message assistant">
            <span className="message-label">SYSTEM</span>
            <div className="message-content">
              <PhraseCycler />
            </div>
          </div>
        )}
        
        <div ref={scrollRef} style={{ height: '1px' }} />
      </main>

      {messages.length > 0 && (
        <div className="chat-input-container">
          
          {/* STAGING AREA */}
          {pendingFiles.length > 0 && (
            <div className="staging-area">
              {pendingFiles.map((file, idx) => (
                <div key={idx} className="staging-chip">
                  <span className="file-name">{file.filename}</span>
                  <button className="remove-file" onClick={() => removePendingFile(idx)}>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}

          <form className="chat-input-wrapper" onSubmit={handleSendMessage}>
            <button 
              type="button" 
              className="add-files-btn"
              onClick={() => appendFilesRef.current?.click()}
              title="Stage more context"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <input 
                type="file" 
                multiple 
                style={{ display: 'none' }} 
                ref={appendFilesRef} 
                onChange={handleStageFiles} 
              />
            </button>
            <input 
              className="chat-input"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={pendingFiles.length > 0 ? "Ask a question about these files..." : "Say something..."}
              disabled={isProcessing}
            />
            <button className="send-btn" type="submit" disabled={isProcessing || (!inputText.trim() && pendingFiles.length === 0)}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
              </svg>
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
