import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

const BackendUrl = process.env.REACT_APP_BACKEND_URL;

const socket = io(BackendUrl, {
  transports: ['websocket', 'polling'],
});

const useSocketCrew = (threadId, challengeThreadId, w_id) => {
  const [messages, setMessages] = useState([]);
  const [awaitingInput, setAwaitingInput] = useState(true);
  const [progress, setProgress] = useState([]);
  const [evaluation, setEvaluation] = useState(null);

  useEffect(() => {
    const handleProcessOutput = (data) => {
      setMessages((prevMessages) => [...prevMessages, { text: data.output, agent: data.agent, user: false }]);
    };

    const handleRequestUserInput = (data) => {
      setAwaitingInput(true);
      console.log("Requesting user input...");
    };

    const handleTeamProgress = (data) => {
      setProgress(data);
      console.log("recieved progress");
    };

    const handleEvalOutput = (data) => {
      setEvaluation(data);
      console.log("recieved evaluation");
    };

    socket.on('process_output', handleProcessOutput);
    socket.on('request_user_input', handleRequestUserInput);
    socket.on('team_progress', handleTeamProgress);
    socket.on('challenge_evaluation_output', handleEvalOutput);

    return () => {
      socket.off('process_output', handleProcessOutput);
      socket.off('request_user_input', handleRequestUserInput);
      socket.on('team_progress', handleTeamProgress);
    };
  }, [threadId]);

  const sendMessage = (input, agent) => {
    if (awaitingInput && messages[messages.length - 1]?.agent != agent) {
      emitAbort();
    }
    if (input.trim()) {
      setMessages(prevMessages => [...prevMessages, { text: input, agent: agent, user: true }]);
      if (awaitingInput && agent !== "manager") {
        console.log("Sending user input as an agent...");
        socket.emit('user_input', { input, thread_id: threadId });
        setAwaitingInput(false);
      } else if (agent !== "manager") {
        console.log("Sending user input as reconnect...");
        socket.emit('start_process_crew', { user_input: "User wants to reconnect with " + agent + " with message " + input, thread_id: threadId, w_id: w_id });
        setAwaitingInput(false);
      } else {
        console.log("Sending user input as new");
        socket.emit('start_process_crew', { user_input: input, thread_id: threadId, w_id: w_id });
        setAwaitingInput(false);
      }
    }
  };

  const evaluateChallenge = (threadId) => {
    socket.emit('evaluate_challenge', { thread_id: threadId });
  }
  const emitAbort = () => {
    console.log("Emitting abort message from socket...");
    socket.emit('abort_process', { thread_id: threadId });
  };

  return { messages, sendMessage, setMessages, awaitingInput, emitAbort, progress, setProgress, evaluation, setEvaluation, evaluateChallenge };
};

export default useSocketCrew;