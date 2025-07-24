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
  tags?: string[];
  identity?: string;
  locked?: boolean;
};

function App() {
  const [messages, setMessages] = useState<Message[]>([
    { sender: 'agent', text: 'Hello! I am Axon. How can I assist you today?' },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [memoryEntries, setMemoryEntries] = useState<MemoryEntry[]>([]);
  const [newKey, setNewKey] = useState('');
  const [newValue, setNewValue] = useState('');
  const [newTags, setNewTags] = useState('');
  const [cloudPrompt, setCloudPrompt] = useState<{model: string; prompt: string} | null>(null);
  const [pasteValue, setPasteValue] = useState('');
  const [selectedModel, setSelectedModel] = useState('qwen3:8b');
  const ws = useRef<WebSocket | null>(null);
  const sendMcp = (tool: string, args: Record<string, unknown>) => {
    if (ws.current?.readyState !== WebSocket.OPEN) return;
    const msg = {
      mcp_protocol_version: '1.0',
      tool_name: tool,
      arguments: args,
    };
    ws.current.send(JSON.stringify(msg));
  };

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
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'cloud_prompt') {
          setCloudPrompt({ model: data.model, prompt: data.prompt });
          const agentResponse: Message = { sender: 'agent', text: 'Remote model suggested. Copy the prompt below.' };
          setMessages(prev => [...prev, agentResponse]);
          return;
        }
      } catch {
        // not JSON
      }
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

    ws.current.send(JSON.stringify({ text: inputValue, model: selectedModel }));
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
    const params =
      `key=${encodeURIComponent(newKey)}&value=${encodeURIComponent(newValue)}&tags=${encodeURIComponent(newTags)}`;
    fetch(`/memory/default_thread?${params}`, {
      method: 'POST',
    }).then(() => {
      setMemoryEntries((prev) => [
        ...prev,
        { key: newKey, value: newValue, tags: newTags.split(',').filter(t => t), locked: false },
      ]);
      setNewKey('');
      setNewValue('');
      setNewTags('');
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
          <select value={selectedModel} onChange={(e)=>setSelectedModel(e.target.value)}>
            <option value="qwen3:8b">qwen3:8b</option>
            <option value="mock-model">mock-model</option>
          </select>
          <button onClick={handleSendMessage}>Send</button>
          <button onClick={() => sendMcp('time', {command: 'now'})}>Time</button>
          <button onClick={() => sendMcp('calculator', {command: 'evaluate', expr: '2+2'})}>Calc</button>
          <button onClick={() => sendMcp('filesystem', {command: 'list', path: '.'})}>List Files</button>
          <button onClick={() => sendMcp('markdown_backup', {command: 'save', name: 'demo', content: 'note'})}>Save Note</button>
        </div>
        {cloudPrompt && (
          <div className="cloud-prompt">
            <p>Use {cloudPrompt.model} with the prompt below, then paste the answer:</p>
            <textarea readOnly value={cloudPrompt.prompt} />
            <textarea
              placeholder="Paste model reply here"
              value={pasteValue}
              onChange={(e) => setPasteValue(e.target.value)}
            />
            <button onClick={() => {
              if (ws.current?.readyState === WebSocket.OPEN) {
                ws.current.send(JSON.stringify({
                  type: 'pasteback',
                  model: cloudPrompt.model,
                  prompt: cloudPrompt.prompt,
                  response: pasteValue,
                }));
                setCloudPrompt(null);
                setPasteValue('');
              }
            }}>Submit</button>
          </div>
        )}
      </div>
      <div className="memory-sidebar">
        <h3>Agent Memory</h3>
        <ul>
          {memoryEntries.map((m, idx) => (
            <li key={idx} className="memory-item">
              <input
                value={m.value}
                onChange={(e) => {
                  const val = e.target.value;
                  setMemoryEntries(prev => prev.map((p,i) => i===idx ? {...p, value: val} : p));
                }}
                onBlur={(e) => {
                  const params = `key=${encodeURIComponent(m.key)}&value=${encodeURIComponent(e.target.value)}&tags=${encodeURIComponent((m.tags||[]).join(','))}`;
                  fetch(`/memory/default_thread?${params}`, {
                    method: 'PUT',
                  });
                }}
              />
              <input
                value={(m.tags || []).join(',')}
                placeholder="tags"
                onChange={(e) => {
                  const tags = e.target.value.split(',').filter(t => t);
                  setMemoryEntries(prev => prev.map((p,i) => i===idx ? {...p, tags} : p));
                }}
                onBlur={(e) => {
                  const params = `key=${encodeURIComponent(m.key)}&value=${encodeURIComponent(m.value)}&tags=${encodeURIComponent(e.target.value)}`;
                  fetch(`/memory/default_thread?${params}`, { method: 'PUT' });
                }}
              />
              <label>
                <input
                  type="checkbox"
                  checked={m.locked}
                  onChange={(e) => {
                    fetch(`/memory/default_thread/${encodeURIComponent(m.key)}/lock?locked=${e.target.checked}`, { method: 'POST' })
                      .then(() => {
                        setMemoryEntries(prev => prev.map((p,i)=> i===idx ? {...p, locked: e.target.checked} : p));
                      });
                  }}
                />
                lock
              </label>
              <button onClick={() => {
                fetch(`/memory/default_thread/${encodeURIComponent(m.key)}`, { method: 'DELETE' })
                  .then(res => res.json())
                  .then(() => setMemoryEntries(prev => prev.filter((_,i)=> i!==idx)));
              }}>Delete</button>
              <span className="memory-key">{m.key}</span>
            </li>
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
          <input
            type="text"
            placeholder="tags"
            value={newTags}
            onChange={(e) => setNewTags(e.target.value)}
          />
          <button onClick={addMemoryEntry}>Add</button>
        </div>
      </div>
    </div>
  );
}

export default App
