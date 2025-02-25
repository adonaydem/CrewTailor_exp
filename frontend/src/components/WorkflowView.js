import React, { useState, useEffect, useRef } from 'react';
import './WorkflowView.css';
import { useNavigate } from 'react-router-dom'; 
import { useAuth } from '../contexts/AuthContext';
import parseLogMessage from './parseLogMessage';
const WorkflowView = ({ currentWorkflow, setCurrentWorkflow}) => {
    const [workflowData, setWorkflowData] = useState(null);
    const [isWorkflowChanged, setIsWorkflowChanged] = useState(false);
    const [feedbacks, setFeedbacks] = useState([]);
    const [approvedFeedbacks, setApprovedFeedbacks] = useState([]);
    const approvedfeedbackRef = useRef();
    const [logs, setLogs] = useState([]);
    const navigate = useNavigate();
    const { currentUser } = useAuth();
    const BackendUrl = process.env.REACT_APP_BACKEND_URL;
    console.log("current workflow", currentWorkflow);
    
    useEffect(() => {
        if (currentWorkflow) {
            localStorage.setItem('currentWorkflow', currentWorkflow);
        } else {
            const storedWorkflow = localStorage.getItem('currentWorkflow');
            if (storedWorkflow) {
                setCurrentWorkflow(storedWorkflow);
            }
        }
    }, [currentWorkflow, setCurrentWorkflow]);
    useEffect(() => {
        const fetchWorkflow = async () => {

            try {
                const response = await fetch(`${BackendUrl}/get_workflow?_id=${encodeURIComponent(currentWorkflow)}`, {
                  method: 'GET',
                });
              
                if (!response.ok) {
                  throw new Error(`HTTP error! status: ${response.status}`);
                }
              
                const data = await response.json();
                console.log('API Response:', data);
                setWorkflowData(data);
                console.log("approved feedbacks: ", data.approved_feedbacks) 
                setApprovedFeedbacks(data.approved_feedbacks);// Ensure this function is defined
              } catch (err) {
                console.log('Error while accessing API: ' + err);
              }
        };

        fetchWorkflow();
    }, [currentWorkflow]);

    useEffect(() => {
        const fetchLogs = async () => {
          try {
            const response = await fetch(`${BackendUrl}/get_recent_logs/${currentUser.uid}?workflow_id=${currentWorkflow}`, {
              method: 'GET',
            });
          
            if (!response) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
          
            const data = await response.json();
    
            console.log('API Response logs:', data);
            setLogs(data);
          } catch (err) {
            console.log('Error while accessing API: ' + err);
          }
        };
    
        fetchLogs();
      }, []);

      useEffect(() => {
        async function fetchFeedbacks(workflowId) {
            try {
              const response = await fetch(`${BackendUrl}/store/get_feedbacks?workflowId=${workflowId}`, {
                method: 'GET',
              });
        
              if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
              }
        
              const data = await response.json();
              console.log('Received data:', data);
              if (data == null) {
                setFeedbacks(null);
              } else {
                setFeedbacks(data.feedbacks);
              }
            } catch (error) {
              console.error('Error while fetching feedbacks:', error);
            }
          }

          fetchFeedbacks(currentWorkflow);

      }, [currentWorkflow]);

      useEffect(() => {
        const handleBeforeUnload = (e) => {
            if (isWorkflowChanged) {
                const confirmationMessage = 'You have unsaved changes. Are you sure you want to leave?';
                e.returnValue = confirmationMessage; // Standard for most browsers
                return confirmationMessage; // For some older browsers
            }
        };

        window.addEventListener('beforeunload', handleBeforeUnload);

        return () => {
            window.removeEventListener('beforeunload', handleBeforeUnload);
        };
    }, [isWorkflowChanged]);

    if (!workflowData) {
        return (
            <div className="loading-overlay">
                <div className="loading-spinner"></div>
            </div>
        );
    }

    const submitApprovedFeedback = async () => {
        const content = approvedfeedbackRef.current.value;
        try {
            const response = await fetch(`${BackendUrl}/approved_feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    _id: currentWorkflow,
                    uid: currentUser.uid,
                    content:content
                }),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(`${data.error}`);
                
            }

            setApprovedFeedbacks(prevFeedbacks => [...prevFeedbacks, data]);
            approvedfeedbackRef.current.value = '';
        } catch (err) {
            console.log('Error while submiting feedback: ' + err);
        }
    };

    const handleFeedbackChange = (e, timestamp, content = null) => {
        const newContent = e.target.value;
      
        if (newContent === "DELETE") {
          // Remove the feedback if the content is "DELETE"
          const updatedFeedbacks = approvedFeedbacks.filter((feedback) => feedback.timestamp !== timestamp);
          setApprovedFeedbacks(updatedFeedbacks);
          setWorkflowData((prevWorkflowData) => ({
            ...prevWorkflowData,
            approved_feedbacks: updatedFeedbacks,
          }));
        } else if (newContent === "APPROVE") {
          // Add the feedback to approved feedbacks if the content is "APPROVE"
          const newApprovedFeedback = { content, timestamp };
          const updatedFeedbacks = [...approvedFeedbacks, newApprovedFeedback];
          setApprovedFeedbacks(updatedFeedbacks);
          setWorkflowData((prevWorkflowData) => ({
            ...prevWorkflowData,
            approved_feedbacks: updatedFeedbacks,
          }));
        } else {
          // Update the approved feedbacks
          const updatedFeedbacks = approvedFeedbacks.map((feedback) =>
            feedback.timestamp === timestamp ? { ...feedback, content: newContent } : feedback
          );
          setApprovedFeedbacks(updatedFeedbacks);
          setWorkflowData((prevWorkflowData) => ({
            ...prevWorkflowData,
            approved_feedbacks: updatedFeedbacks,
          }));
        }
      
        setIsWorkflowChanged(true);
      };
    const handleChange = (e, nodeId = null) => {
        const { name, value, type, checked, options } = e.target;

        const processValue = (name, value) => {
            if (name === "to_do_list" || name === "people" || name === "children") {
                return value.split(",").map(item => item.trim());
            }
            return value;
        };

        setWorkflowData(prevData => {
            if (nodeId) {
                const updatedNodes = prevData.nodes.map(node => {
                    if (node.id === nodeId) {
                        if (type === 'checkbox') {
                            return { ...node, [name]: checked };
                        } else if (type === 'radio') {
                            return { ...node, human_direction: value };
                        } else if (name === "toolkits") {
                            const selectedValues = Array.from(options).filter(option => option.selected).map(option => option.value);
                            return { ...node, toolkits: selectedValues };
                        }
                        return { ...node, [name]: processValue(name, value) };
                    }
                    return node;
                });
                return { ...prevData, nodes: updatedNodes };
            } else {
                return {
                    ...prevData,
                    metadata: {
                        ...prevData.metadata,
                        [name]: type === 'checkbox' ? checked : processValue(name, value)
                    }
                };
            }
        });

        setIsWorkflowChanged(true);
    };

    const saveChanges = async () => {
        console.log(workflowData);
        try {
            const response = await fetch(`${BackendUrl}/update_workflow`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    _id: currentWorkflow,
                    workflowData: workflowData,
                    uid: currentUser.uid,
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log('Save Response:', data);
            setIsWorkflowChanged(false);
            alert('Workflow saved successfully!');
        } catch (err) {
            console.log('Error while saving workflow: ' + err);
            alert('Failed to save workflow.');
        }
    };

    const { metadata, nodes } = workflowData;

    const handleRunClick = async (workflow_id) => {
        setCurrentWorkflow(workflow_id);
        navigate('/workflowRun');
    };

    const handleAddNode = () => {
        const maxId = nodes.reduce((max, node) => Math.max(max, parseInt(node.id, 10)), 0);
        const newNode = {
            id: (maxId + 1).toString(), // Increment the maximum existing ID by 1
            name: '',
            description: '',
            human_direction: 'no',
            toolkits: [],
            children: [],
            to_do_list: [],
            people: [],
        };
        setWorkflowData(prevData => ({
            ...prevData,
            nodes: [...prevData.nodes, newNode],
        }));
    };

    const handleDeleteNode = (nodeId) => {
        setWorkflowData(prevData => ({
            ...prevData,
            nodes: prevData.nodes.filter(node => node.id !== nodeId),
        }));
    };
    
    return (
        <div className="main-content custom-scrollbar"><div className='main-content-view custom-scrollbar'>
            <div className="left-content custom-scrollbar">
                <div className="workflow-metadata box">
                <div className="workflow-header">
                    <h2>Workflow: {metadata.name}</h2>
                    
                    <div className="button-container">
                        <button onClick={() => handleRunClick(workflowData._id)} className="run-button">Run</button>
                        <button onClick={saveChanges} className="save-button">Save Changes</button>
                    </div>
                </div>
                

                    <form>
                        <div className="form-group">
                            <label>Name:</label>
                            <input
                                type="text"
                                name="name"
                                value={metadata.name}
                                onChange={(e) => handleChange(e)}
                                className="custom-input"
                            />
                        </div>
                        <div className="form-group">
                            <label>Description:</label>
                            <textarea
                                name="description"
                                value={metadata.description}
                                onChange={(e) => handleChange(e)}
                                className="custom-input"
                            />
                        </div>
                        <div className="form-group">
                            <label>To-Do List:</label>
                            <input
                                type="text"
                                name="to_do_list"
                                value={(metadata.to_do_list || []).join(', ')}
                                onChange={(e) => handleChange(e)}
                                className="custom-input"
                            />
                        </div>
                        <div className="form-group">
                            <label>People:</label>
                            <input
                                type="text"
                                name="people"
                                value={(metadata.people || []).join(', ')}
                                onChange={(e) => handleChange(e)}
                                className="custom-input"
                            />
                        </div>
                        <div className="form-group">
                            <label>
                            <input
                                type="checkbox"
                                name="public"
                                checked={metadata.public}
                                onChange={(e) => handleChange(e)}
                            />
                            Public
                            </label>
                        </div>
                    </form>

                    {'public_metadata' in metadata && (
                        <div>
                            <span>{metadata.public_metadata.likes} Likes    {metadata.public_metadata.downloads} Downloads </span>
                        </div>
                    )}

                </div>
                <div className="workflow-nodes box">
                    <h3>Agents</h3>
                    <div className="node-container">
                        {nodes.map(node => (
                            <div key={node.id} className="node-item box custom-scrollbar">
                                <h4>{node.name} <button onClick={() => handleDeleteNode(node.id)} className="delete-button" style={{ color: 'red' }}>🗑️</button></h4>
                                <form>
                                    <div className="form-group">
                                        <label>ID (read-only):</label>
                                        <input type="text" value={node.id} readOnly className="custom-input read-only" />
                                    </div>
                                    <div className="form-group">
                                        <label>Name:</label>
                                        <input
                                            type="text"
                                            name="name"
                                            value={node.name}
                                            onChange={(e) => handleChange(e, node.id)}
                                            className="custom-input"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Description:</label>
                                        <textarea
                                            name="description"
                                            value={node.description}
                                            onChange={(e) => handleChange(e, node.id)}
                                            className="custom-input"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Human Direction:</label>
                                        <div className="radio-group small">
                                            <label>
                                                <input
                                                    type="radio"
                                                    name={`human_direction_${node.id}`}
                                                    value="yes"
                                                    checked={node.human_direction === 'yes'}
                                                    onChange={(e) => handleChange(e, node.id)}
                                                />
                                                Yes
                                            </label>
                                            <label>
                                                <input
                                                    type="radio"
                                                    name={`human_direction_${node.id}`}
                                                    value="no"
                                                    checked={node.human_direction === 'no'}
                                                    onChange={(e) => handleChange(e, node.id)}
                                                />
                                                No
                                            </label>
                                        </div>
                                    </div>
                                    
                                    <div className="form-group">
                                    <label>Toolkits:</label>
                                    <select name="toolkits" value={node.toolkits} onChange={(e) => {handleChange(e, node.id);}} multiple>
                                        <option selected disabled>General Text and General Tools Only</option>
                                        <option value="database_management">Database Management</option>
                                        <option value="task_management">Task Management</option>
                                        <option value="event_management">Event Management</option>
                                        <option value="project_management">Project Management</option>
                                        <option value="email_management">Email Management</option>
                                        <option value="file_management">File Management</option>
                                        <option value="finance&economics_apipack">Finance and Economics API Pack</option>
                                        </select>
                                    </div>
                                    <div className="form-group">
                                        <label>Children:</label>
                                        <input
                                            type="text"
                                            name="children"
                                            value={(node.children || []).join(', ')}
                                            onChange={(e) => handleChange(e, node.id)}
                                            className="custom-input"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>To-Do List:</label>
                                        <input
                                            type="text"
                                            name="to_do_list"
                                            value={(node.to_do_list || []).join(', ')}
                                            onChange={(e) => handleChange(e, node.id)}
                                            className="custom-input"
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>People:</label>
                                        <input
                                            type="text"
                                            name="people"
                                            value={(node.people || []).join(', ')}
                                            onChange={(e) => handleChange(e, node.id)}
                                            className="custom-input"
                                        />
                                    </div>
                                </form>
                            </div>
                        ))}
                        <button onClick={handleAddNode} className="add-button">Add Agent</button>
                    </div>
                </div>
            </div>
            <div className="right-content box custom-scrollbar">
                <div className='box'>
                <h3>Recent Activity</h3>
                    <ul>
                    {logs.length > 0 ? (
                    <>
                        {logs.map((log) => (
                        <li key={log.timestamp} className="log-item">
                            <span className="log-message" dangerouslySetInnerHTML={{ __html: parseLogMessage(log) }}></span>
                        </li>
                        ))}
                    </>
                    ) : (
                    <li className='log-item'>No recent activity. You need to lighten up!!!</li>
                    )}
                </ul>
                </div>
                
                
                <div className='community-feedbacks box'>
                <h3>Community Feedbacks</h3>
                <ul>
                    {metadata.public === true ? (
                    <>
                        {feedbacks ? (
                        feedbacks.map((feedback) => (
                            <li key={feedback.timestamp}>
                            {feedback.content} - {feedback.user} - {feedback.timestamp}
                            {!approvedFeedbacks.some(approved => approved.timestamp === feedback.timestamp) && (
                                <button
                                className="approve-button"
                                onClick={() => handleFeedbackChange({ target: { value: "APPROVE" } }, feedback.timestamp, feedback.content)}
                                >
                                &#x2713; {/* Unicode character for a check mark */}
                                </button>
                            )}
                            </li>
                        ))
                        ) : (
                        <li>No feedbacks yet.</li>
                        )}
                    </>
                    ) : (
                    <li>Make your workflow public to get feedbacks and improve the crew directly!!!</li>
                    )}
                </ul>
                </div>

                
                <div className='approved-feedbacks box'>
                    <h3>Approved Feedbacks</h3>
                    <p>This will directly pass to the AI system.</p>
                    {approvedFeedbacks && approvedFeedbacks.length > 0 ? (
                    approvedFeedbacks.map((feedback) => (
                        <div key={feedback.timestamp} className="feedback-item">
                        <textarea
                            className="custom-input"
                            type="text"
                            value={feedback.content}
                            onChange={(e) => handleFeedbackChange(e, feedback.timestamp)}
                        />
                        <button
                            className="delete-button"
                            onClick={() => handleFeedbackChange({ target: { value: "DELETE" } }, feedback.timestamp)}
                        >
                            &#x2715; {/* Unicode character for a cross symbol */}
                        </button>
                        </div>
                    ))
                    ) : (
                    <ul>
                        <li>No feedbacks yet.</li>
                    </ul>
                    )}
                    <textarea
                        ref={approvedfeedbackRef}
                        placeholder="Enter your feedback..."
                        className='approved-feedback-input'
                    />
                    <button onClick={ submitApprovedFeedback}>Add</button>
                </div>
            </div>
            </div>
        </div>
    );
};

export default WorkflowView;