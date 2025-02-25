import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

const BackendUrl = process.env.REACT_APP_BACKEND_URL;

const socket = io(BackendUrl, {
  transports: ['websocket', 'polling'],
});

const useSocket = (threadId) => {
  const [messages, setMessages] = useState([]);
  const [awaitingInput, setAwaitingInput] = useState(true);

  useEffect(() => {
    socket.on('process_output', (data) => {
      setMessages((prevMessages) => [...prevMessages, { text: data.output, user: false }]);
    });

    socket.on('request_user_input', (data) => {
      setAwaitingInput(true);
      console.log("Requesting user input...");
    });

    return () => {
      socket.off('process_output');
      socket.off('request_user_input');
    };
  }, []);

  const sendMessage = (input) => {
    if (input.trim()) {
      setMessages(prevMessages => [...prevMessages, { text: input, user: true }]);
      socket.emit('start_process', { user_input: input, thread_id: threadId });
      setAwaitingInput(false);
    }
  };

  return { messages, sendMessage, setMessages, awaitingInput };
};

export default useSocket;