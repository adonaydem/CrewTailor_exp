import React, { useState, useRef, useEffect } from 'react';
import useSocket from '../hooks/useSocket';
import ReactMarkdown from 'react-markdown';
import './ConsoleFooter.css';
import { useAuth } from '../contexts/AuthContext';
const ConsoleFooter = ({ setIsConsoleCollapsed, isSidebarCollapsed, selectedThreadIdPAM }) => {
  const [height, setHeight] = useState(200); // Default height of the console footer
  const [input, setInput] = useState('');
  const [threadId, setThreadId] = useState(null);
  const [threadData, setThreadData] = useState(null);
  const { messages, sendMessage, setMessages, awaitingInput } = useSocket(threadId);
  const messagesEndRef = useRef(null);
  const messageRef = useRef(null);
  const consoleFooterRef = useRef(null);
  const { currentUser } = useAuth();
  const [listening, setListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [typing, setTyping] = useState(false);
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;

  useEffect(() => {
    if (!awaitingInput){
        setTyping(true);
    }else{
        setTyping(false);
    }
}, [awaitingInput]);

  useEffect(() => {
    const adjustFooterWidth = () => {
      if (consoleFooterRef.current) {
        const sidebarWidth = isSidebarCollapsed ? 0 : 300; // Adjust based on your sidebar width
        consoleFooterRef.current.style.width = `calc(100% - ${sidebarWidth}px)`;
      }
    };

    adjustFooterWidth();
  }, [isSidebarCollapsed]);
  const generateThreadId = () => {
    return `thread_${currentUser.uid}_${new Date().getTime()}`;
  };

  useEffect(() => {
      if (selectedThreadIdPAM != null) {
          setMessages([]);
          setThreadId(selectedThreadIdPAM);
      } else {
          setMessages([]); 
          setThreadId(generateThreadId());
      }
  }, [selectedThreadIdPAM, currentUser.uid]);

  const handleReadAloud = () => {
    if (!messageRef.current) {
      console.error('Message reference is null');
      return;
    }

    let text = messageRef.current.innerText;

    // Remove emojis from the text
    text = text.replace(/[\u{1F600}-\u{1F6FF}]/gu, '');
    const speech = new SpeechSynthesisUtterance(text);
    const voices = window.speechSynthesis.getVoices();

    // Select a high-quality voice
    const selectedVoice = voices.find(voice => voice.name.includes('Google') || voice.name.includes('Microsoft')) || voices[0];
    
    speech.voice = selectedVoice;
    speech.pitch = 1; // Adjust pitch (0 to 2)
    speech.rate = 1;  // Adjust rate (0.1 to 10)

    window.speechSynthesis.speak(speech);
  };

  // Ensure voices are loaded before calling handleReadAloud
  window.speechSynthesis.onvoiceschanged = handleReadAloud;

  const fetchThread = async () => {
    if (!threadId) {
        console.error('Thread ID is null');
        return;
    }

    try {
        const response = await fetch(`${BackendUrl}/get_thread/${threadId}`, {
            method: 'GET',
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log('API Response current thread:', data);
        setThreadData(data);
        
        if (data != null){
            console.log("messages state", data.messages);
            setMessages(data.messages);
        } else{
            console.log("messages state", "Empty");
            setMessages([]);
        }
    } catch (err) {
        console.error('Error fetching threads:', err);
      }
    };

    useEffect(() => {
        if (threadId) {
            fetchThread();
        }
    }, [threadId]);

    useEffect(() => {
      if (messages.length) {
          console.log(messages);
          saveMessages(messages);
          messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
  }, [messages, threadId]);

  const saveMessages = async (messages) => {
      try {
          console.log(threadId);
          const response = await fetch(`${BackendUrl}/save_messages/${currentUser.uid}`, {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json'
              },
              body: JSON.stringify({
                  threadId: threadId,
                  messages: messages,
              })
          });

          const result = await response.json();
      } catch (err) {
          console.log('Error while accessing API: ' + err);
      }
  };
  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && input.trim()) {
      handleSend();
    }
  };

  const handleMouseDown = (e) => {
    e.preventDefault();
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleMouseUp);
  };
  
  const handleMouseMove = (e) => {
    const newHeight = Math.max(100, window.innerHeight - e.clientY);
    setHeight(newHeight);
  };
  
  const handleTouchMove = (e) => {
    e.preventDefault(); // This will now work because passive is set to false
    const touch = e.touches[0];
    const newHeight = Math.max(100, window.innerHeight - touch.clientY);
    setHeight(newHeight);
  };
  
  const handleMouseUp = () => {
    document.removeEventListener('mousemove', handleMouseMove);
    document.removeEventListener('mouseup', handleMouseUp);
    document.removeEventListener('touchmove', handleTouchMove);
    document.removeEventListener('touchend', handleMouseUp);
  };
  
  useEffect(() => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Sorry, your browser does not support speech recognition.');
      return;
    }

    const SpeechRecognition = window.webkitSpeechRecognition;
    const recognitionInstance = new SpeechRecognition();
    recognitionInstance.continuous = true;
    recognitionInstance.interimResults = true;
    recognitionInstance.lang = 'en-US';

    recognitionInstance.onresult = (event) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        }
      }
      setInput(finalTranscript);
    };

    recognitionInstance.onerror = (event) => {
      console.error('Speech recognition error detected: ' + event.error);
    };

    setRecognition(recognitionInstance);
  }, []);

  const handleToggleListening = () => {
    if (listening) {
      console.log('stop recording');
      recognition.stop();
    } else {
      console.log('start recording');
      recognition.start();
    }
    setListening(!listening);
  };



  return (
    <footer className="console-footer" style={{ height }} ref={consoleFooterRef}>
      <div className="drag-handle" onMouseDown={handleMouseDown} onTouchStart={handleMouseDown}></div>
      <div className="cf-messages">
        {Array.isArray(messages) && messages.map((msg, index) => (
          <div
          key={index}
          className={`message-container ${msg.user ? 'right' : 'left'}`}
        >
          <div className={`message ${msg.user ? 'user' : 'bot'}`}>
              <div className="message-content" ref={messageRef}>
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
              {!msg.user && (
                  <button className="read-aloud-button" onClick={handleReadAloud}>
                      Read Aloud
                  </button>
              )}
          </div>
      </div>
          
        ))}
        {typing && messages.length !== 0 && <div class="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>}
        <div ref={messagesEndRef}></div>
      </div>
      <div className="input-area">
      <button onClick={() => {setMessages([]);setThreadId(generateThreadId())}} id='new-chat'>New chat</button>
      <button onClick={() => setIsConsoleCollapsed(true)} id='collapse'>Collapse</button>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={listening ? "Listening" : "Type a message and press Enter"}
        />
        <button onClick={handleSend}>Send</button>
        <button onClick={handleToggleListening}>
        {listening ? 'Stop' : 'Record'}
        </button>
        
        
      </div>
    </footer>
  );
};

export default ConsoleFooter;