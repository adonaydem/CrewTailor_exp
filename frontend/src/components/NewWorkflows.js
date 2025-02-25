import React, { useState, useEffect  } from 'react';
import './NewWorkflows.css';
import WorkflowVisualizer from './WorkflowVisualizer';
import { useAuth} from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom'; 
const NewWorkflows = ({ setCurrentWorkflow }) => {
  const [selectedOption, setSelectedOption] = useState('Form'); // Default selected option
  const { currentUser } = useAuth();
  const navigate = useNavigate();
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;
  useEffect(() => {
    if (currentUser) {
      console.log("id:",currentUser.uid); 
      const uid = currentUser.uid;
    }
  }, [currentUser]);
  const [nodes, setNodes] = useState([
    { id: '1', type: 'input', data: { label: 'Start Node', workerDetails: {} }, position: { x: 250, y: 5 } },
    { id: '2', data: { label: 'End Node', workerDetails: {} }, position: { x: 250, y: 250 } },
  ]);
  const [edges, setEdges] = useState([
    { id: 'e1-2', source: '1', target: '2', animated: true },
  ]);
  const handleOptionChange = (option) => {
    setSelectedOption(option);
  };

  const [workflowData, setWorkflowData] = useState({
    name: '',
    description: '',
    todoList: '',
    peopleInvolved: '',
    public: false,
    workers: [
      { name: '', toolkits: '', humanDirection: 'yes', description: '', connectedTo: '', workerTodoList: '', workerPeopleInvolved: '' },
      { name: '', toolkits: '', humanDirection: 'yes', description: '', connectedTo: '', workerTodoList: '', workerPeopleInvolved: '' },
      { name: '', toolkits: '', humanDirection: 'yes', description: '', connectedTo: '', workerTodoList: '', workerPeopleInvolved: '' }
    ]
  });

  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  const handleInputChange = (e, index, isWorker) => {
    const { name, value, type, checked, options } = e.target;
  
    if (isWorker) {
      const updatedWorkers = [...workflowData.workers];
      if (name === 'toolkits') {
        // Handle multiple select
        const selectedValues = Array.from(options).filter(option => option.selected).map(option => option.value);
        updatedWorkers[index] = { ...updatedWorkers[index], [name]: selectedValues };
      } else {
        // Handle other fields
        updatedWorkers[index] = { ...updatedWorkers[index], [name]: type === 'checkbox' ? checked : value };
      }
      setWorkflowData({ ...workflowData, workers: updatedWorkers });
    } else {
      // Handle changes for other fields
      setWorkflowData({
        ...workflowData,
        [name]: type === 'checkbox' ? checked : value,
      });
    }
  };

  const addWorker = () => {
    setWorkflowData({
      ...workflowData,
      workers: [
        ...workflowData.workers,
        { name: '', toolkits: '', humanDirection: 'yes', description: '', connectedTo: '', workerTodoList: '', workerPeopleInvolved: '' }
      ]
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
  
    console.log('Submitting...');
  
    // Extract node names
    const nodeNames = workflowData.workers.map(worker => worker.name.trim());
  
    // Check for duplicate names
    const nameSet = new Set(nodeNames);
    if (nameSet.size !== nodeNames.length) {
      setErrorMessage('Error: Two or more nodes have the same name.');
      setSuccessMessage(null); // Clear any previous success message
      return;
    }
  
    // Transform the state into the required format
    const formattedData = {
      metadata: {
        name: workflowData.name,
        description: workflowData.description,
        pad: "",
        to_do_list: workflowData.todoList.split('\n').map(item => item.trim()),
        people: workflowData.peopleInvolved.split(',').map(person => person.trim()),
        public: workflowData.public
      },
      nodes: workflowData.workers.map((worker, index) => ({
        id: (index + 1).toString(),
        name: worker.name,
        toolkits: worker.toolkits,
        human_direction: worker.humanDirection,
        description: worker.description,
        children: worker.connectedTo.split(',').map(child => child.trim()),
        pad: "",
        to_do_list: worker.workerTodoList.split('\n').map(item => item.trim()),
        people: worker.workerPeopleInvolved.split(',').map(person => person.trim())
      }))
    };
  
    try {
      const response = await fetch(`${BackendUrl}/add_workflow/${currentUser.uid}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formattedData)
      });
  
      const result = await response.json();
  
      if (response.ok  && result.workflow_id) {
        setSuccessMessage('Workflow submitted successfully');
        setErrorMessage(null); // Clear any previous error message
  
        // Clear form
        setWorkflowData({
          name: '',
          description: '',
          todoList: '',
          peopleInvolved: '',
          workers: [
            { name: '', toolkits: '', humanDirection: '', description: '', connectedTo: '', workerTodoList: '', workerPeopleInvolved: '' },
            { name: '', toolkits: '', humanDirection: '', description: '', connectedTo: '', workerTodoList: '', workerPeopleInvolved: '' },
            { name: '', toolkits: '', humanDirection: '', description: '', connectedTo: '', workerTodoList: '', workerPeopleInvolved: '' }
          ]
        });
        setCurrentWorkflow(result.workflow_id);
        navigate('/workflowView');
      } else {
        setErrorMessage(result.message || 'An error occurred while submitting the form');
        setSuccessMessage(null); // Clear any previous success message
      }
    } catch (error) {
      console.error('Error submitting form:', error);
      setErrorMessage('An error occurred while submitting the form');
      setSuccessMessage(null); // Clear any previous success message
    }
  };
  return (
    <main className="main-content"><div className="main-content-new">
      <h2>New Workflows</h2>
      <div className="workflow-navigation">
        <ul>
          <li className={selectedOption === 'Form' ? 'active' : ''} onClick={() => handleOptionChange('Form')}>Form</li>
          <li className={selectedOption === 'Visualizer' ? 'active' : ''} onClick={() => handleOptionChange('Visualizer')}>Visualizer</li>
          <li className={selectedOption === 'Chat' ? 'active' : ''} onClick={() => handleOptionChange('Chat')}>Chat with PAM</li>
        </ul>
      </div>
      <div className="new-workflows">
        {/* Render the Form content only when 'Form' option is selected */}
        {selectedOption === 'Form' && (
          <form onSubmit={handleSubmit} className="workflow-form">
            {/* General Workflow Details Section */}
            <div className="workflow-section general-section">
              <h3>General Workflow Details</h3>
              <div className="form-group">
                <label>Name:</label>
                <input type="text" name="name" value={workflowData.name} onChange={handleInputChange} required />
              </div>
              
              <div className="form-group">
                <label>Description:</label>
                <textarea name="description" value={workflowData.description} onChange={handleInputChange} required></textarea>
              </div>
              
              <div className="form-group">
                <label>General To-Do List:</label>
                <textarea name="todoList" value={workflowData.todoList} onChange={handleInputChange} required></textarea>
              </div>
              
              <div className="form-group">
                <label>People Involved:</label>
                <input type="text" name="peopleInvolved" value={workflowData.peopleInvolved} onChange={handleInputChange} />
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    name="public"
                    checked={workflowData.public}
                    onChange={(e) => handleInputChange(e)}
                  />
                  Public
                </label>
              </div>
            </div>

            {/* Workers Section */}
            <div className="workflow-section workers-section">
              <h3>Agents (Team Members)</h3>
              <div className="workers-grid">
                {workflowData.workers.map((worker, index) => (
                  <div key={index} className="worker-node">
                    <h4>Agent {index + 1}</h4>
                    <div className="form-group">
                      <label>Name:</label>
                      <input type="text" name="name" value={worker.name} onChange={(e) => handleInputChange(e, index, true)} />
                    </div>
                    <div className="form-group">
                      <label>Description:</label>
                      <textarea name="description" value={worker.description} onChange={(e) => handleInputChange(e, index, true)}></textarea>
                    </div>
                    <div className="form-group">
                    <label>Toolkits:</label>
                    <select name="toolkits" value={worker.toolkits} onChange={(e) => handleInputChange(e, index, true)} multiple>
                      <option selected disabled>General Text and General Tools Only</option>
                      <option value="database_management">Database Management</option>
                      <option value="file_management">File Management</option>
                      <option value="task_management">Task Management</option>
                      <option value="event_management">Event Management</option>
                      <option value="project_management">Project Management</option>
                      <option value="finance&economics_apipack">Finance and Economics API Pack</option>
                    </select>
                    </div>
                    <div className="form-group">
                      <label>Human Direction:</label>
                      <select name="humanDirection" value={worker.humanDirection} onChange={(e) => handleInputChange(e, index, true)}>
                        <option value="yes">Yes</option>
                        <option value="no">No</option>
                      </select>
                    </div>

                    

                    <div className="form-group">
                      <label>Connected To:</label>
                      <input type="text" name="connectedTo" value={worker.connectedTo} onChange={(e) => handleInputChange(e, index, true)} />
                    </div>

                    <div className="form-group">
                      <label>To-Do List:</label>
                      <textarea name="workerTodoList" value={worker.workerTodoList} onChange={(e) => handleInputChange(e, index, true)}></textarea>
                    </div>

                    <div className="form-group">
                      <label>People Involved:</label>
                      <input type="text" name="workerPeopleInvolved" value={worker.workerPeopleInvolved} onChange={(e) => handleInputChange(e, index, true)} />
                    </div>
                  </div>
                ))}
              </div>

              <button type="button" onClick={addWorker} className="add-worker-button">Add Worker</button>
            </div>

            {/* Display Error or Success Messages */}
            {errorMessage && <div className="error-message">{errorMessage}</div>}
            {successMessage && <div className="success-message">{successMessage}</div>}

            <button type="submit" className="submit-button">Submit Workflow</button>
          </form>
        )}

        {/* Render the Visualizer content only when 'Visualizer' option is selected */}
        {selectedOption === 'Visualizer' && (
          <WorkflowVisualizer nodes={nodes} edges={edges} />
        )}

        {/* Render the Chat content only when 'Chat' option is selected */}
        {selectedOption === 'Chat' && (
          <div className="chat-container">
            <h3>You can talk with PAM in console.</h3>
            {/* Add your chat component content here */}
          </div>
        )}

      </div></div>
    </main>
  );
};

export default NewWorkflows;