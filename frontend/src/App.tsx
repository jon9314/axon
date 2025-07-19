// frontend/src/App.tsx
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

type Message = {
  sender: 'user' | 'agent';
  text: string;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'agent', text: "Hello! I am Axon. How can I assist you today?" }
  ]);
  const [inputValue, setInputValue] = useState('');
  const ws = useRef<WebSocket | null>(null);

  useEffect(() => {
    // --- CORRECTED WEBSOCKET URL ---
    // This now uses the same hostname as the browser's address bar,
    // ensuring it connects to the correct server.
    const wsHost = window.location.hostname;
    const wsUrl = `ws://${wsHost}:8000/ws/chat`;
    
    console.log(`Attempting to connect to WebSocket at: ${wsUrl}`);
    ws.current = new WebSocket(wsUrl);

    ws.current.onopen = () => console.log("WebSocket connected!");
    ws.current.onclose = () => console.log("WebSocket disconnected.");
    ws.current.onerror = (error) => console.error("WebSocket Error: ", error);

    ws.current.onmessage = (event) => {
      const agentResponse: Message = { sender: 'agent', text: event.data };
      setMessages(prevMessages => [...prevMessages, agentResponse]);
    };

    return () => {
      ws.current?.close();
    };
  }, []);

  const handleSendMessage = () => {
    if (inputValue.trim() === '' || ws.current?.readyState !== WebSocket.OPEN) {
        console.error("Cannot send message, WebSocket is not open.");
        return;
    }

    const userMessage: Message = { sender: 'user', text: inputValue };
    setMessages(prevMessages => [...prevMessages, userMessage]);

    ws.current.send(inputValue);
    setInputValue('');
  };

  const handleInputChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(event.target.value);
  };

  const handleKeyPress = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="app-container">
      <div className="chat-view">
        <div className="message-display">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.sender}`}>
              <p>{msg.text}</p>
            </div>
          ))}
        </div>
        <div className="input-area">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
          />
          <button onClick={handleSendMessage}>Send</button>
        </div>
      </div>
      <div className="memory-sidebar">
        <h3>Agent Memory</h3>
        <ul>
          <li>Fact: User's name is Alex.</li>
          <li>Note: Prefers concise answers.</li>
          <li>Fact: Project codename is "Frankie".</li>
          <li>Note: Interested in Python and AI.</li>
        </ul>
      </div>
    </div>
  );
}

export default App;