import { useState, useEffect } from 'react';
import io from 'socket.io-client';

const useSocketStore = () => {
  const [workflows, setWorkflows] = useState([]);
  const [isFeedbackPopupOpen, setIsFeedbackPopupOpen] = useState(false);
  const [currentFeedbackWorkflow, setCurrentFeedbackWorkflow] = useState(null);
  const [feedbackContent, setFeedbackContent] = useState('');
  const [feedbackList, setFeedbackList] = useState([]);
  const BackendUrl = process.env.REACT_APP_BACKEND_URL;

  const socket = io(BackendUrl); // Adjust the URL as needed

  useEffect(() => {
    const socket = io(BackendUrl); // Adjust the URL as needed
  
    socket.on('connect', () => {
      console.log('Socket connected');
    });
  
    socket.on('disconnect', () => {
      console.log('Socket disconnected');
    });
  
    socket.on('workflowUpdate', (data) => {
      console.log('Received workflow update:', data);
      setWorkflows((prevWorkflows) => data);
    });
  
    socket.on('workflowLikeUpdate', (data) => {
      console.log('Received workflow like update:', data);
      setWorkflows((prevWorkflows) => {
        return prevWorkflows.map((workflow) => {
          if (workflow.workflow_id === data.workflow_id) {
            return { ...workflow, likes: [...workflow.likes, data.uid] };
          }
          return workflow;
        });
      });
      console.log('Updated workflows:', workflows);
    });

    socket.on('workflowFeedbackUpdate', (data) => {
      console.log('Received workflow feedback update:', data);
      setFeedbackList(data.feedbacks);
      console.log('Updated feedback list:', feedbackList);
    });
  
    return () => {
      socket.off('workflowUpdate');
      socket.off('workflowLikeUpdate');
      socket.disconnect();
    };
  }, []);
  const handleLike = (workflow_id, uid) => {
    console.log('handleLike called with workflow_id:', workflow_id);
    socket.emit('likeWorkflow', { workflow_id: workflow_id, uid: uid });
};

  const handleSubmitFeedback = (workflow_id, uid, feedback) => {
    console.log('handlesubmitfeedback called with workflow_id:', workflow_id);
    socket.emit('submitFeedback', { workflow_id: workflow_id, uid: uid, content: feedback });
    setFeedbackContent('');
  };

  return {
    workflows,
    handleLike,
    handleSubmitFeedback,
    setWorkflows,
    isFeedbackPopupOpen,
    setIsFeedbackPopupOpen,
    currentFeedbackWorkflow,
    setCurrentFeedbackWorkflow,
    feedbackContent,
    setFeedbackContent,
    feedbackList,
    setFeedbackList,
  };
};

export default useSocketStore;
