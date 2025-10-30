// import React, { useState, useRef, useEffect } from 'react';
// import './App.css';

// const App = () => {
//   const [messages, setMessages] = useState([]);
//   const [inputValue, setInputValue] = useState('');
//   const [isLoading, setIsLoading] = useState(false);
//   const [systemStatus, setSystemStatus] = useState(null);
//   const [expandedSources, setExpandedSources] = useState({});
//   const messagesEndRef = useRef(null);

//   const API_BASE_URL = 'http://127.0.0.1:3000';

//   // Fetch system status on mount
//   useEffect(() => {
//     fetchSystemStatus();
//   }, []);

//   // Auto-scroll to bottom when new messages arrive
//   useEffect(() => {
//     messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
//   }, [messages]);

//   const fetchSystemStatus = async () => {
//     try {
//       const response = await fetch(`${API_BASE_URL}/`);
//       const data = await response.json();
//       setSystemStatus(data);
//     } catch (error) {
//       console.error('Failed to fetch system status:', error);
//     }
//   };

//   const toggleSources = (messageIndex) => {
//     setExpandedSources(prev => ({
//       ...prev,
//       [messageIndex]: !prev[messageIndex]
//     }));
//   };

//   const handleSubmit = (e) => {
//     e.preventDefault();
//     if (!inputValue.trim() || isLoading) return;

//     const userMessage = {
//       type: 'user',
//       content: inputValue,
//       timestamp: new Date().toLocaleTimeString()
//     };

//     setMessages(prev => [...prev, userMessage]);
//     const queryText = inputValue;
//     setInputValue('');
//     setIsLoading(true);

//     fetch(`${API_BASE_URL}/query`, {
//       method: 'POST',
//       headers: {
//         'Content-Type': 'application/json',
//       },
//       body: JSON.stringify({
//         query: queryText,
//         top_k: 5
//       })
//     })
//       .then(response => response.json())
//       .then(data => {
//         const botMessage = {
//           type: 'bot',
//           content: data.answer,
//           sources: data.sources,
//           timestamp: new Date().toLocaleTimeString(),
//           numSources: data.num_sources
//         };
//         setMessages(prev => [...prev, botMessage]);
//       })
//       .catch(error => {
//         const errorMessage = {
//           type: 'error',
//           content: 'Failed to get response. Please make sure the server is running.',
//           timestamp: new Date().toLocaleTimeString()
//         };
//         setMessages(prev => [...prev, errorMessage]);
//       })
//       .finally(() => {
//         setIsLoading(false);
//       });
//   };

//   const clearChat = () => {
//     setMessages([]);
//     setExpandedSources({});
//   };

//   const setExample = (text) => {
//     setInputValue(text);
//   };

//   // Function to parse markdown-style formatting
//   const parseMarkdown = (text) => {
//     if (!text) return text;

//     const elements = [];
//     let currentIndex = 0;

//     // Regex to match **bold**, *italic*, and handle line breaks
//     const markdownRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|\n)/g;
//     let match;

//     while ((match = markdownRegex.exec(text)) !== null) {
//       // Add text before the match
//       if (match.index > currentIndex) {
//         elements.push(
//           <span key={`text-${currentIndex}`}>
//             {text.slice(currentIndex, match.index)}
//           </span>
//         );
//       }

//       const matchedText = match[0];

//       // Handle bold **text**
//       if (matchedText.startsWith('**') && matchedText.endsWith('**')) {
//         elements.push(
//           <strong key={`bold-${match.index}`}>
//             {matchedText.slice(2, -2)}
//           </strong>
//         );
//       }
//       // Handle italic *text*
//       else if (matchedText.startsWith('*') && matchedText.endsWith('*')) {
//         elements.push(
//           <em key={`italic-${match.index}`}>
//             {matchedText.slice(1, -1)}
//           </em>
//         );
//       }
//       // Handle line breaks
//       else if (matchedText === '\n') {
//         elements.push(<br key={`br-${match.index}`} />);
//       }

//       currentIndex = match.index + matchedText.length;
//     }

//     // Add remaining text
//     if (currentIndex < text.length) {
//       elements.push(
//         <span key={`text-${currentIndex}`}>
//           {text.slice(currentIndex)}
//         </span>
//       );
//     }

//     return elements.length > 0 ? elements : text;
//   };

//   return (
//     <div className="container">
//       {/* Header */}
//       <header className="header">
//         <div className="header-content">
//           <div className="logo-section">
//             <div className="logo">⚖️</div>
//             <div>
//               <h1 className="title">Legal RAG Assistant</h1>
//               <p className="subtitle">Bharatiya Nyaya Sanhita (BNS) • BNSS • BSA</p>
//             </div>
//           </div>
//           {systemStatus && (
//             <div className="status-badge">
//               <span className={`status-dot ${systemStatus.gemini_api_status ? 'online' : 'offline'}`}></span>
//               <span className="status-text">
//                 {systemStatus.database_count} documents loaded
//               </span>
//             </div>
//           )}
//         </div>
//       </header>

//       {/* Main Content */}
//       <div className="main-content">
//         {/* Chat Area */}
//         <div className="chat-container">
//           {messages.length === 0 ? (
//             <div className="welcome-screen">
//               <div className="welcome-icon">🏛️</div>
//               <h2 className="welcome-title">Welcome to Legal RAG Assistant</h2>
//               <p className="welcome-text">
//                 Ask me anything about Indian legal documents including BNS, BNSS, and BSA.
//               </p>
//               <div className="example-questions">
//                 <p className="example-title">Example questions:</p>
//                 <button
//                   className="example-button"
//                   onClick={() => setExample('What is murder under BNS?')}
//                 >
//                   What is murder under BNS?
//                 </button>
//                 <button
//                   className="example-button"
//                   onClick={() => setExample('Explain the provisions for theft')}
//                 >
//                   Explain the provisions for theft
//                 </button>
//                 <button
//                   className="example-button"
//                   onClick={() => setExample('What are the rights of an arrested person?')}
//                 >
//                   What are the rights of an arrested person?
//                 </button>
//               </div>
//             </div>
//           ) : (
//             <div className="messages-container">
//               {messages.map((message, index) => (
//                 <div
//                   key={index}
//                   className={`message-wrapper ${message.type === 'user' ? 'user' : ''}`}
//                 >
//                   {message.type !== 'user' && (
//                     <div className="avatar bot">🤖</div>
//                   )}
//                   <div className={`message ${message.type}`}>
//                     <div className="message-content">
//                       {parseMarkdown(message.content)}
//                     </div>
//                     {message.sources && message.sources.length > 0 && (
//                       <div className="sources-container">
//                         <button 
//                           className="sources-toggle"
//                           onClick={() => toggleSources(index)}
//                         >
//                           <span className="sources-header">
//                             📚 Sources ({message.numSources})
//                           </span>
//                           <span className={`arrow ${expandedSources[index] ? 'expanded' : ''}`}>
//                             ▼
//                           </span>
//                         </button>
//                         {expandedSources[index] && (
//                           <div className="sources-content">
//                             {message.sources.map((source, idx) => (
//                               <div key={idx} className="source-card">
//                                 <div className="source-title">
//                                   Section {source.section}, Subsection {source.subsection}
//                                 </div>
//                                 <div className="source-details">
//                                   📄 {source.file} • Page {source.page}
//                                 </div>
//                                 <div className="source-preview">
//                                   {source.content_preview}
//                                 </div>
//                               </div>
//                             ))}
//                           </div>
//                         )}
//                       </div>
//                     )}
//                     <div className="timestamp">{message.timestamp}</div>
//                   </div>
//                   {message.type === 'user' && (
//                     <div className="avatar user">👤</div>
//                   )}
//                 </div>
//               ))}
//               {isLoading && (
//                 <div className="message-wrapper">
//                   <div className="avatar bot">🤖</div>
//                   <div className="loading-message">
//                     <div className="loading-dots">
//                       <span className="dot"></span>
//                       <span className="dot"></span>
//                       <span className="dot"></span>
//                     </div>
//                     <div className="loading-text">Searching legal documents...</div>
//                   </div>
//                 </div>
//               )}
//               <div ref={messagesEndRef} />
//             </div>
//           )}
//         </div>

//         {/* Input Area */}
//         <div className="input-container">
//           {messages.length > 0 && (
//             <button className="clear-button" onClick={clearChat}>
//               🗑️ Clear Chat
//             </button>
//           )}
//           <div className="input-form">
//             <input
//               type="text"
//               value={inputValue}
//               onChange={(e) => setInputValue(e.target.value)}
//               onKeyPress={(e) => e.key === 'Enter' && handleSubmit(e)}
//               placeholder="Ask a legal question..."
//               className="input"
//               disabled={isLoading}
//             />
//             <button
//               onClick={handleSubmit}
//               className="send-button"
//               disabled={isLoading || !inputValue.trim()}
//             >
//               {isLoading ? '⏳' : '📤'}
//             </button>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default App;
















import React, { useState, useRef, useEffect } from 'react';
import './App.css';

const App = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState(null);
  const [expandedSources, setExpandedSources] = useState({});
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  const API_BASE_URL = 'http://127.0.0.1:3000';

  // Fetch system status and create session on mount
  useEffect(() => {
    fetchSystemStatus();
    createNewSession();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchSystemStatus = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/`);
      const data = await response.json();
      setSystemStatus(data);
    } catch (error) {
      console.error('Failed to fetch system status:', error);
    }
  };

  const createNewSession = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/session/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      const data = await response.json();
      setSessionId(data.session_id);
      console.log('✅ Session created:', data.session_id);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const clearSession = async () => {
    if (sessionId) {
      try {
        await fetch(`${API_BASE_URL}/session/${sessionId}`, {
          method: 'DELETE'
        });
        console.log('✅ Session cleared');
      } catch (error) {
        console.error('Failed to clear session:', error);
      }
    }
  };

  const toggleSources = (messageIndex) => {
    setExpandedSources(prev => ({
      ...prev,
      [messageIndex]: !prev[messageIndex]
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: inputValue,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    const queryText = inputValue;
    setInputValue('');
    setIsLoading(true);

    fetch(`${API_BASE_URL}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: queryText,
        top_k: 5,
        session_id: sessionId  // Include session ID for conversation context
      })
    })
      .then(response => response.json())
      .then(data => {
        const botMessage = {
          type: 'bot',
          content: data.answer,
          sources: data.sources,
          timestamp: new Date().toLocaleTimeString(),
          numSources: data.num_sources,
          conversationAware: data.conversation_aware
        };
        setMessages(prev => [...prev, botMessage]);
      })
      .catch(error => {
        const errorMessage = {
          type: 'error',
          content: 'Failed to get response. Please make sure the server is running.',
          timestamp: new Date().toLocaleTimeString()
        };
        setMessages(prev => [...prev, errorMessage]);
      })
      .finally(() => {
        setIsLoading(false);
      });
  };

  const clearChat = async () => {
    // Clear session on backend
    await clearSession();
    
    // Clear local state
    setMessages([]);
    setExpandedSources({});
    
    // Create new session
    await createNewSession();
  };

  const setExample = (text) => {
    setInputValue(text);
  };

  // Function to parse markdown-style formatting
  const parseMarkdown = (text) => {
    if (!text) return text;

    const elements = [];
    let currentIndex = 0;

    // Regex to match **bold**, *italic*, and handle line breaks
    const markdownRegex = /(\*\*[^*]+\*\*|\*[^*]+\*|\n)/g;
    let match;

    while ((match = markdownRegex.exec(text)) !== null) {
      // Add text before the match
      if (match.index > currentIndex) {
        elements.push(
          <span key={`text-${currentIndex}`}>
            {text.slice(currentIndex, match.index)}
          </span>
        );
      }

      const matchedText = match[0];

      // Handle bold **text**
      if (matchedText.startsWith('**') && matchedText.endsWith('**')) {
        elements.push(
          <strong key={`bold-${match.index}`}>
            {matchedText.slice(2, -2)}
          </strong>
        );
      }
      // Handle italic *text*
      else if (matchedText.startsWith('*') && matchedText.endsWith('*')) {
        elements.push(
          <em key={`italic-${match.index}`}>
            {matchedText.slice(1, -1)}
          </em>
        );
      }
      // Handle line breaks
      else if (matchedText === '\n') {
        elements.push(<br key={`br-${match.index}`} />);
      }

      currentIndex = match.index + matchedText.length;
    }

    // Add remaining text
    if (currentIndex < text.length) {
      elements.push(
        <span key={`text-${currentIndex}`}>
          {text.slice(currentIndex)}
        </span>
      );
    }

    return elements.length > 0 ? elements : text;
  };

  return (
    <div className="container">
      {/* Header */}
      <header className="header">
        <div className="header-content">
          <div className="logo-section">
            <div className="logo">⚖️</div>
            <div>
              <h1 className="title">Legal RAG Assistant</h1>
              <p className="subtitle">Bharatiya Nyaya Sanhita (BNS) • BNSS • BSA</p>
            </div>
          </div>
          <div className="header-right">
            {systemStatus && (
              <div className="status-badge">
                <span className={`status-dot ${systemStatus.gemini_api_status ? 'online' : 'offline'}`}></span>
                <span className="status-text">
                  {systemStatus.database_count} documents
                </span>
              </div>
            )}
            {sessionId && (
              <div className="session-badge">
                <span className="session-icon">💬</span>
                <span className="session-text">Conversational Mode</span>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Chat Area */}
        <div className="chat-container">
          {messages.length === 0 ? (
            <div className="welcome-screen">
              <div className="welcome-icon">🏛️</div>
              <h2 className="welcome-title">Welcome to Legal RAG Assistant</h2>
              <p className="welcome-text">
                Ask me anything about Indian legal documents including BNS, BNSS, and BSA.
                I can remember our conversation and answer follow-up questions!
              </p>
              <div className="example-questions">
                <p className="example-title">Example questions:</p>
                <button
                  className="example-button"
                  onClick={() => setExample('What is murder under BNS?')}
                >
                  What is murder under BNS?
                </button>
                <button
                  className="example-button"
                  onClick={() => setExample('Explain the provisions for theft')}
                >
                  Explain the provisions for theft
                </button>
                <button
                  className="example-button"
                  onClick={() => setExample('What are the rights of an arrested person?')}
                >
                  What are the rights of an arrested person?
                </button>
              </div>
              <div className="conversation-tip">
                <div className="tip-icon">💡</div>
                {/* <div className="tip-text">
                  <strong>Tip:</strong> You can ask follow-up questions like "What is the punishment for it?" 
                  and I'll understand the context from our conversation!
                </div> */}
              </div>
            </div>
          ) : (
            <div className="messages-container">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`message-wrapper ${message.type === 'user' ? 'user' : ''}`}
                >
                  {message.type !== 'user' && (
                    <div className="avatar bot">🤖</div>
                  )}
                  <div className={`message ${message.type}`}>
                    {message.conversationAware && (
                      <div className="conversation-indicator">
                        💬 Using conversation context
                      </div>
                    )}
                    <div className="message-content">
                      {parseMarkdown(message.content)}
                    </div>
                    {message.sources && message.sources.length > 0 && (
                      <div className="sources-container">
                        <button 
                          className="sources-toggle"
                          onClick={() => toggleSources(index)}
                        >
                          <span className="sources-header">
                            📚 Sources ({message.numSources})
                          </span>
                          <span className={`arrow ${expandedSources[index] ? 'expanded' : ''}`}>
                            ▼
                          </span>
                        </button>
                        {expandedSources[index] && (
                          <div className="sources-content">
                            {message.sources.map((source, idx) => (
                              <div key={idx} className="source-card">
                                <div className="source-title">
                                  Section {source.section}, Subsection {source.subsection}
                                </div>
                                <div className="source-details">
                                  📄 {source.file} • Page {source.page}
                                </div>
                                <div className="source-preview">
                                  {source.content_preview}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    <div className="timestamp">{message.timestamp}</div>
                  </div>
                  {message.type === 'user' && (
                    <div className="avatar user">👤</div>
                  )}
                </div>
              ))}
              {isLoading && (
                <div className="message-wrapper">
                  <div className="avatar bot">🤖</div>
                  <div className="loading-message">
                    <div className="loading-dots">
                      <span className="dot"></span>
                      <span className="dot"></span>
                      <span className="dot"></span>
                    </div>
                    <div className="loading-text">
                      {messages.length > 1 
                        ? 'Analyzing your question with conversation context...' 
                        : 'Searching legal documents...'}
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="input-container">
          {messages.length > 0 && (
            <button className="clear-button" onClick={clearChat}>
              🗑️ Clear Chat & Start New Conversation
            </button>
          )}
          <div className="input-form">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSubmit(e)}
              placeholder={
                messages.length > 0 
                  ? "Ask a follow-up question..." 
                  : "Ask a legal question..."
              }
              className="input"
              disabled={isLoading}
            />
            <button
              onClick={handleSubmit}
              className="send-button"
              disabled={isLoading || !inputValue.trim()}
              title={messages.length > 0 ? "Send (remembers conversation)" : "Send"}
            >
              {isLoading ? '⏳' : '📤'}
            </button>
          </div>
          {messages.length > 0 && (
            <div className="conversation-help">
              💬 I remember our conversation. Feel free to ask follow-up questions!
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default App;