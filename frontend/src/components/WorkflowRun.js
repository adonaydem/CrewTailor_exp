import React, { useState, useRef, useEffect } from 'react';
import useSocketCrew from '../hooks/useSocketCrew';
import ReactMarkdown from 'react-markdown';
import './WorkflowRun.css';
import { useAuth } from '../contexts/AuthContext';
import remarkGfm from 'remark-gfm';

const WorkflowRun = ({ currentWorkflow, setCurrentWorkflow, setIsConsoleCollapsed, selectedThreadId, selectedChallenge }) => {
    const [workflowData, setWorkflowData] = useState(null);
    const [threadId, setThreadId] = useState(null);
    const [challengeThreadId, setChallengeThreadId] = useState(null);
    const [threadData, setThreadData] = useState(null);
    const [inputs, setInputs] = useState({});
    const [activeChat, setActiveChat] = useState(null);
    const [selectedTable, setSelectedTable] = useState(null);
    const [tableData, setTableData] = useState([]);
    const popupRef = useRef(null);
    const tablePopupRef = useRef(null);
    const messagesEndRef = useRef(null);
    const messageRef = useRef(null);
    const { currentUser } = useAuth();
    const [tables, setTables] = useState([]);
    const { messages, sendMessage, setMessages, awaitingInput, emitAbort, progress, setProgress, evaluation, setEvaluation, evaluateChallenge } = useSocketCrew(threadId, challengeThreadId ,currentWorkflow);
    const [files, setFiles] = useState([]);
    const [isChallengeStarted, setIsChallengeStarted] = useState(null);
    const [isEvaluationPopupVisible, setIsEvaluationPopupVisible] = useState(false);
    const [listening, setListening] = useState(false);
    const [recognition, setRecognition] = useState(null);
    const [typing, setTyping] = useState(false);
    const BackendUrl = process.env.REACT_APP_BACKEND_URL;

    useEffect(() => {
        if (currentWorkflow) {
            localStorage.setItem('currentWorkflow', currentWorkflow);
        } else {
            setIsConsoleCollapsed(true);
            const storedWorkflow = localStorage.getItem('currentWorkflow');
            if (storedWorkflow) {
                setCurrentWorkflow(storedWorkflow);
            }
        }
    }, [currentWorkflow, setCurrentWorkflow]);
    const generateThreadId = () => {
        return `thread_${currentUser.uid}_${currentWorkflow}_${new Date().getTime()}`;
    };

    useEffect(() => {
        if (selectedThreadId != null) {
            setMessages([]);
            setThreadId(selectedThreadId);
        } else {
            setMessages([]);
            setThreadId(generateThreadId());
        }
    }, [currentWorkflow, selectedThreadId]);

    useEffect(() => {
        if (!awaitingInput){
            setTyping(true);
        }else{
            setTyping(false);
        }
    }, [awaitingInput]);
    useEffect(() => {
        console.log("thread challenge", threadId, selectedChallenge, isChallengeStarted);
        if (threadId) {
            if (selectedChallenge && !isChallengeStarted) {
                const startChallenge = async () => {
                    try {
                        const response = await fetch(`${BackendUrl}/start_challenge`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                uid: currentUser.uid,
                                thread_id: threadId,
                                challenge_id: selectedChallenge.id,
                                challenge_content: selectedChallenge.content,
                                workflow_id: currentWorkflow,
                                points: selectedChallenge.points
                            })
                        });
                        if (!response.ok) {
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }

                        const data = await response.json();
                        console.log('API Response challenge:', data);
                        setIsChallengeStarted(data.id);
                        setChallengeThreadId(threadId);
                    } catch (err) {
                        console.log('Error while accessing API: ' + err);
                    }
                }

                startChallenge();
            }
        }
    }, [threadId]);

    const handleEvaluationClick = () => {
        setEvaluation(null);
        evaluateChallenge(challengeThreadId);
        setIsEvaluationPopupVisible(true);
    }
    
    useEffect(() => {
        const fetchProgress = async () => {
            try {
                const response = await fetch(`${BackendUrl}/get_progress/${threadId}`, {
                    method: 'GET',
                });
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
    
                const data = await response.json();
                console.log('API Response progress data:', data);
                setProgress(data.progress);
            } catch (err){
                console.log('Error while accessing API: ' + err);
                setProgress([]);
            }
        }

        fetchProgress();
    }, [threadId])
    useEffect(() => {
        setIsConsoleCollapsed(true);
    }, [setIsConsoleCollapsed]);

    useEffect(() => {
        if (currentUser && currentWorkflow) {
            fetchTables();
        }
    }, [currentUser, currentWorkflow]);

    const fetchTables = async () => {
        try {
            const response = await fetch(`${BackendUrl}/get_tables?user_id=${currentUser.uid}&workflow_id=${currentWorkflow}`, {
                method: 'GET',
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('API Response tables:', data);
            setTables(data.tables);
        } catch (error) {
            console.error('Error fetching tables:', error);
        }
    };

    const fetchTableData = async (tableName) => {
        try {
            const response = await fetch(`${BackendUrl}/get_table_data?user_id=${currentUser.uid}&workflow_id=${currentWorkflow}&table_name=${tableName}`, {
                method: 'GET',
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('API Response table data:', data);
            setTableData(data);
            setSelectedTable(tableName);
        } catch (error) {
            console.error('Error fetching table data:', error);
        }
    };

    const handleReadAloud = () => {
        const text = messageRef.current.innerText;
        const speech = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(speech);
    };

    useEffect(() => {
        if (!currentWorkflow) {
            console.log('currentWorkflow is null or undefined');
            return;
        }
        const fetchWorkflow = async () => {
            try {
                const response = await fetch(`${BackendUrl}/get_workflow?_id=${encodeURIComponent(currentWorkflow)}`, {
                    method: 'GET',
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data = await response.json();
                console.log('API Response workflow:', data);
                setWorkflowData(data);
            } catch (err) {
                console.log('Error while accessing API: ' + err);
            }
        };

        fetchWorkflow();
    }, [currentWorkflow]);

    useEffect(() => {
        document.addEventListener('mousedown', handleClosePopup);
        return () => {
            document.removeEventListener('mousedown', handleClosePopup);
        };
    }, []);

    // Emit abort message when the component unmounts or beforeunload event occurs
    useEffect(() => {
        const handleBeforeUnload = (event) => {
          event.preventDefault();
          event.returnValue = ''; // Required for Chrome to show a warning dialog
        };

        window.addEventListener('beforeunload', handleBeforeUnload);
      
        return () => {
          emitAbort();
          window.removeEventListener('beforeunload', handleBeforeUnload);
        };
      }, []);
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

    const fetchFiles = async () => {
        try {
            const response = await fetch(`${BackendUrl}/list_files/${currentUser.uid}/${currentWorkflow}/${threadId}`, {
                method: 'GET',
            });
    
            if (!response.ok) {
                setFiles([]);
                throw new Error(`HTTP error! status: ${response.status}`);
                
            }
    
            const data = await response.json();
            console.log('API Response FILES:', data);
            setFiles(data);
        } catch (err) {
            console.error('Error fetching files:', err);
        }
    };

    useEffect(() => {
        if (threadId) {
            console.log("fetching files....");
            fetchFiles();
        }
    }, [threadId, messages]);

    useEffect(() => {
        if (messages.length) {
            console.log(messages);
            saveMessages(messages);
            const lastMessage = messages[messages.length - 1];
            setActiveChat(lastMessage.agent);
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
                    workflowId: currentWorkflow,
                    messages: messages,
                })
            });

            const result = await response.json();
        } catch (err) {
            console.log('Error while accessing API: ' + err);
        }
    };

    const handleFileUpload = async (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('userId', currentUser.uid);
        formData.append('workflowId', currentWorkflow);
        formData.append('threadId', threadId);

        try {
            const response = await fetch(`${BackendUrl}/upload_file`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('File Upload Response:', data);
            fetchFiles(); // Refresh file list
        } catch (err) {
            console.error('Error uploading file:', err);
        }
    };

    const handleSend = (agent) => {
        if (inputs[agent]?.trim()) {
            sendMessage(inputs[agent], agent);
            setInputs(prevInputs => ({ ...prevInputs, [agent]: '' }));
        }
    };

    const handleKeyDown = (e, agent) => {
        if (e.key === 'Enter' && inputs[agent]?.trim()) {
            handleSend(agent);
        }
    };

    const handleInputChange = (e, agent) => {
        setInputs(prevInputs => ({ ...prevInputs, [agent]: e.target.value }));
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
    
        setRecognition(recognitionInstance);
      }, []);
    
      const handleToggleListening = (agent) => {
        console.log('handleToggleListening', agent);
        if (listening) {
          console.log('stop recording', agent);
          recognition.stop();
          setListening(false);
        } else {
            console.log('recording', agent);
          recognition.onresult = (event) => {
            let transcript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
              if (event.results[i].isFinal) {
                transcript += event.results[i][0].transcript;
              }
            }
            console.log('recorded', transcript);
            setInputs((prevInputs) => ({ ...prevInputs, [agent]: transcript }));
          };
    
          recognition.start();
          setListening(true);
        }
      };
    
    const renderMessages = (agent) => {
        return messages
            .filter(msg => msg.agent === agent)
            .map((msg, index) => {
                let content;
                try {
                    if (typeof msg.text !== 'string') {
                        throw new Error('Message text is not a string');
                    }
                    content = <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.text}</ReactMarkdown>;
                } catch (error) {
                    console.error('Error rendering markdown:', error);
                    content = <div>{String(msg.text)}</div>;
                }
                return (
                    <div
                        key={index}
                        className={`message-container ${msg.user ? 'right' : 'left'}`}
                    >
                        <div className={`message ${msg.user ? 'user' : 'bot'}`}>
                            <div className="message-content" ref={messageRef}>
                                {content}
                            </div>
                            {!msg.user && (
                                <button className="read-aloud-button" onClick={handleReadAloud}>
                                    Read Aloud
                                </button>
                            )}
                        </div>
                    </div>

                );
            });
    };

    const renderChatArea = (agent, name, human_direction, toolkits) => {
        const isActive = activeChat === agent;
        return (
            <div
                className={`chat-area ${isActive ? 'active' : ''}`}
                key={agent}
                onClick={() => setActiveChat(agent)}
            >
                <div className="chat_area-header">
                    <h4>{name}</h4>
                    {toolkits && isActive &&  (
                        <div className="toolkits-section">
                            <div className="toolkits">
                                {toolkits.map((toolkit) => {
                                    const keyword = toolkit.split('_')[0]; // Extract part before underscore
                                    return <span key={toolkit} className="toolkit">{keyword}</span>;
                                })}
                            </div>
                        </div>
                    )}
                </div>
                <div className="messages">
                    {renderMessages(agent)}
                    {typing && isActive && messages.length !== 0 && <div class="typing-indicator">
                                    <span></span>
                                    <span></span>
                                    <span></span>
                                </div>}
                    <div ref={messagesEndRef}></div>
                </div>
                {isActive && (
                    <div className="input-area">
                        {human_direction === "yes" ? (
                            <>
                                <textarea
                                    type="text"
                                    value={inputs[agent] || ''}
                                    onChange={(e) => handleInputChange(e, agent)}
                                    onKeyDown={(e) => handleKeyDown(e, agent)}
                                    placeholder={listening ? "Listening..." : "Type a message and press Enter"}
                                    autoFocus
                                    className="custom-input"
                                ></textarea>
                                <button onClick={() => handleSend(agent)}>Send</button>
                                <button onClick={() => handleToggleListening(agent)}>
                                    {listening ? 'Stop' : 'Record'}
                                </button>
                            </>
                        ) : (
                            <input
                                type="text"
                                placeholder="This agent is autonomous"
                                disabled
                            />
                        )}
                    </div>
                )}
                {toolkits && !isActive &&  (
                        <div className="toolkits-section">
                            <div className="toolkits">
                                {toolkits.map((toolkit) => {
                                    const keyword = toolkit.split('_')[0]; // Extract part before underscore
                                    return <span key={toolkit} className="toolkit">{keyword}</span>;
                                })}
                            </div>
                        </div>
                    )}
            </div>
        );
    };

    const renderFiles = () => {
        return files.map((file, index) => (
          <div key={index}>
            <a href={`${BackendUrl}/download_file/${currentUser.uid}/${currentWorkflow}/${threadId}/${file}`} download>
              {file}
            </a>
          </div>
        ));
      };
      
    const handleTableClick = (tableName) => {
        fetchTableData(tableName);
    };

    const renderTablePopup = () => {
        if (!selectedTable) return null;
    
        return (
            <div className="table-popup">
                <button className="close-button" onClick={() => setSelectedTable(null)}>Close</button>
                <div className="table-popup-content" ref={tablePopupRef}>
                    <h2>{selectedTable}</h2>
                    <table>
                        <thead>
                            <tr>
                                {tableData.length > 0 && 
                                    Object.keys(tableData[0]).map((col, index) => (
                                        <th key={index}>{col}</th>
                                    ))
                                }
                            </tr>
                        </thead>
                        <tbody>
                            {tableData.map((row, rowIndex) => (
                                <tr key={rowIndex}>
                                    {Object.values(row).map((val, colIndex) => (
                                        <td key={colIndex}>{val}</td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    };
    const handleClosePopup = (e) => {
        if (popupRef.current && !popupRef.current.contains(e.target)) {
            setActiveChat(null);
        }
        if (tablePopupRef.current && !tablePopupRef.current.contains(e.target)) {
            setSelectedTable(null);
        }
    };


      

    if (!workflowData) {
        return (
            <div className="loading-overlay">
                <div className="loading-spinner"></div>
            </div>
        );
    }

    return (
        <div className="main-content-main">
          <div className="main-left">
            <div className='main-content-run-workflow'>
              <div className='run'>
                <div style={{ display: 'flex', width: '100%', alignItems: 'center' }}>
                  <h2 className="head">{selectedChallenge && (<span>Challenge </span>)}Run: {workflowData.metadata.name}</h2>
                  <button className="new-instance-button" onClick={() => {setMessages([]);setThreadId(generateThreadId())}}>New instance</button>
                  {selectedChallenge && (<button className='new-instance-button' onClick={handleEvaluationClick}>I finished the challenge and I want a score.</button>)}
                  
                </div>
                <p>Click on any box to start conversation!</p>
                <div className="main-content-run">
                  <div className="manager-area">
                    {renderChatArea('manager', 'Manager', 'yes', null)}
                  </div>
                  <div className="nodes-area">
                    {workflowData.nodes.map(node => renderChatArea(node.name, node.name, node.human_direction, node.toolkits))}
                  </div>
                </div>
                {activeChat && (
                  <div className="popup">
                    <button className="close-button" onClick={() => setActiveChat(null)}>Close</button>
                    <div className="popup-content" ref={popupRef}>
                      {
                        (() => {
                          const node = workflowData.nodes.find(node => node.name === activeChat);
                          if (activeChat === 'manager') {
                            return renderChatArea('manager', 'Manager', 'yes', null);
                          }
                          console.log("toolkits", node.toolkits)
                          return node ? renderChatArea(activeChat, activeChat, node.human_direction, node.toolkits) : null;
                        })()
                      }
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className='main-right'>
            <h2 className="head">Workspace</h2>
            <div className="filespace box">
            <div className="title-container">
            <h2>Filespace</h2>
            <span>per instance</span>
            </div>
              {files.length > 0 ? renderFiles() : <p>No files yet.</p>}
              <input type="file" onChange={handleFileUpload} />
            </div>
            <div className="dataspace box">
            <div class="title-container">
            <h2>Dataspace</h2>
            <span>per workflow</span>
            </div>
                    {tables.length > 0 ? (
                        <ul>
                            {tables.map((table, index) => (
                                <li key={index} onClick={() => handleTableClick(table)}>{table}</li>
                            ))}
                        </ul>
                    ) : (
                        <p>No tables available.</p>
                    )}
                </div>
                <div className="team-progress box">
                    <h2>Team Progress</h2>
                    {progress.length > 0 ? (
                    progress.map((entry, index) => {
                        const memberName = Object.keys(entry)[0];
                        const memberProgress = entry[memberName];
                        return (
                        <div className="progress-card" key={index}>
                            <div className="progress-info">
                            <h3>{memberName}</h3>
                            <p>{memberProgress}</p>
                            </div>
                        </div>
                        );
                    })
                    ) : (
                    <p>No progress available.</p>
                    )}
                </div>
          </div>
          {renderTablePopup()}

          {isEvaluationPopupVisible && (
                <div className="evaluation-popup">
                    <button className="evaluation-close-button" onClick={() => setIsEvaluationPopupVisible(false)}>
                        ×
                    </button>
                    {evaluation === null ? (
                    <div className="evaluation-loading">Waiting for evaluation...</div>
                    ) : (
                    <div className="evaluation-result">
                        <ReactMarkdown>{evaluation.output}</ReactMarkdown>
                    </div>
                    )}
                </div>
            )}
        </div>
      );
};

export default WorkflowRun;