// frontend/src/App.tsx
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

type Message = {
  sender: 'user' | 'agent';
  text: string;
};

type MemoryEntry = {
  key: string;
  value: string;
  identity?: string;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'agent', text: 'Hello! I am Axon. How can I assist you today?' },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [memoryEntries, setMemoryEntries] = useState<MemoryEntry[]>([]);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
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

    fetch('/memory/default_thread')
      .then((res) => res.json())
      .then((data) => setMemoryEntries(data.facts || []))
      .catch((err) => console.error('Failed to load memory', err));

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

  const addMemoryEntry = () => {
    fetch(`/memory/default_thread?key=${encodeURIComponent(newKey)}&value=${encodeURIComponent(newValue)}`, {
      method: 'POST',
    }).then(() => {
      setMemoryEntries((prev) => [...prev, { key: newKey, value: newValue }]);
      setNewKey('');
      setNewValue('');
    });
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
          {memoryEntries.map((m, idx) => (
            <li key={idx}>{m.key}: {m.value}</li>
          ))}
        </ul>
        <div className="memory-edit">
          <input
            type="text"
            placeholder="key"
            value={newKey}
            onChange={(e) => setNewKey(e.target.value)}
          />
          <input
            type="text"
            placeholder="value"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
          />
          <button onClick={addMemoryEntry}>Add</button>
        </div>
      </div>
    </div>
  );
}

export default App
