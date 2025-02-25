import React, { useState, useCallback } from 'react';
import ReactFlow, {
  addEdge,
  MiniMap,
  Controls,
  Background,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
} from 'react-flow-renderer';
import NodeDetailsModal from './NodeDetailsModal';
import GeneralWorkflowModal from './GeneralWorkflowModal';
import { useAuth} from '../contexts/AuthContext';
const WorkflowVisualizer = () => {
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [workflowData, setWorkflowData] = useState({
    name: '',
    description: '',
    todoList: '',
    peopleInvolved: '',
    public: false,
  });
  const { currentUser } = useAuth();
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;

  const handleInputChange = (event) => {
    const { name, value, type, checked } = event.target;
    setWorkflowData({
      ...workflowData,
      [name]: type === 'checkbox' ? checked : value,
    });
  };

  const onConnect = (params) => setRfEdges((eds) => addEdge(params, eds));

  const addNode = useCallback(() => {
    const newNode = {
      id: (rfNodes.length + 1).toString(),
      data: { label: `Agent ${rfNodes.length + 1}`, workerDetails: {} },
      position: { x: Math.random() * 100, y: Math.random() * 100 },
    };
    setRfNodes((nds) => nds.concat(newNode));
  }, [rfNodes, setRfNodes]);

  const onNodeClick = (event, node) => {
    setSelectedNode(node);
  };

  const handleSave = (nodeId, details) => {
    setRfNodes((nds) =>
      nds.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, label: details.name, workerDetails: details } }
          : node
      )
    );
  };
  

  const handleClose = () => {
    setSelectedNode(null);
  };

  const getChildrenNodes = (node) => {
    return rfEdges
      .filter(edge => edge.source === node.id)
      .map(edge => edge.target);
  };

  const handleFormSubmit = async (event) => {
    event.preventDefault();
  
    if (!workflowData || !workflowData.name || !workflowData.description) {
      setErrorMessage('Please provide all required workflow details.');
      return;
    }
  
    const nodeNames = rfNodes.map(node => (node.data.workerDetails?.name || "").trim());
    const nameSet = new Set(nodeNames);
    if (nameSet.size !== nodeNames.length) {
      setErrorMessage('Error: Two or more nodes have the same name.');
      setSuccessMessage(null); // Clear any previous success message
      return;
    }
  
    const formattedData = {
      metadata: {
        name: workflowData.name,
        description: workflowData.description,
        pad: "",
        to_do_list: workflowData.todoList ? workflowData.todoList.split('\n').map(item => item.trim()) : [],
        people: workflowData.peopleInvolved ? workflowData.peopleInvolved.split(',').map(person => person.trim()) : [],
        public: workflowData.public
      },
      nodes: rfNodes.map((node, index) => {
        const worker = node.data.workerDetails || {};
        return {
          id: (index + 1).toString(),
          name: worker.name || "",
          toolkits: worker.toolkits || [],
          human_direction: worker.humanDirection || "",
          description: worker.description || "",
          children: getChildrenNodes(node),
          pad: "",
          to_do_list: worker.workerTodoList ? worker.workerTodoList.split('\n').map(item => item.trim()) : [],
          people: worker.peopleInvolved ? worker.peopleInvolved.split(',').map(person => person.trim()) : []
        };
      })
    };
    
    try {
      console.log("new ", formattedData);
      const response = await fetch(`${BackendUrl}/add_workflow/${currentUser.uid}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formattedData)
      });
  
      const result = await response.json();
  
      if (response.ok) {
        setSuccessMessage('Workflow submitted successfully');
        setErrorMessage(null); // Clear any previous error message
  
        // Clear form
        setWorkflowData({
          name: '',
          description: '',
          todoList: '',
          peopleInvolved: '',
          public: false
        });
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
  <div style={{ display: 'flex', height: '100vh' }}>
    <div style={{ flex: 1, height: '100%' }}>
      <ReactFlowProvider>
        <div className="visualizer-header">
          <button onClick={addNode} style={{ marginBottom: '10px' }}>
            Add Agent
          </button>
        </div>
        <ReactFlow
          nodes={rfNodes}
          edges={rfEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
        {selectedNode && (
          <NodeDetailsModal
            node={selectedNode}
            connectedNodes={getChildrenNodes(selectedNode)}
            onClose={handleClose}
            onSave={handleSave}
          />
        )}
      </ReactFlowProvider>
    </div>
    <div style={{ width: '300px', padding: '20px' }}>
      {errorMessage && <div style={{ color: 'red' }}>{errorMessage}</div>}
      {successMessage && <div style={{ color: 'green' }}>{successMessage}</div>}
      <GeneralWorkflowModal 
        workflowData={workflowData}
        handleInputChange={handleInputChange}
        handleFormSubmit={handleFormSubmit}
      />
    </div>
  </div>
);
};

export default WorkflowVisualizer;