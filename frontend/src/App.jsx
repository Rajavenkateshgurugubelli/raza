import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './index.css';

function App() {
  const [messages, setMessages] = useState([
    { role: 'agent', content: "I am R.A.Z.A. Online and ready. What do you need, Raza?", isTool: false }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef(null);

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;
    
    const userMsg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setLoading(true);
    
    // Add an empty agent message placeholder
    setMessages(prev => [...prev, { role: 'agent', content: "" }]);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMsg, session_id: "demo-session" })
      });

      if (!res.body) throw new Error("No readable stream");

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      
      let done = false;
      let finalContent = "";
      
      while (!done) {
        const { value, done: readerDone } = await reader.read();
        done = readerDone;
        if (value) {
          const chunkStr = decoder.decode(value, { stream: true });
          const messagesRaw = chunkStr.split("\n\n");
          for (let raw of messagesRaw) {
            if (raw.startsWith("data: ")) {
              const data = raw.substring(6);
              if (data === "[DONE]") break;
              finalContent += data;
              setMessages(prev => {
                const newArr = [...prev];
                newArr[newArr.length - 1] = { role: 'agent', content: finalContent };
                return newArr;
              });
            }
          }
        }
      }
    } catch (err) {
      console.error(err);
      setMessages(prev => {
        const newArr = [...prev];
        newArr[newArr.length - 1] = { role: 'agent', content: "Error connecting to backend." };
        return newArr;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="raza-container">
      <div className="header">
        <div className="agent-avatar">R</div>
        <div className="header-info">
          <h1>R.A.Z.A.</h1>
          <p>Rapid Autonomous Zettelkasten Agent</p>
        </div>
      </div>
      
      <div className="chat-box">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === 'agent' && msg.content.includes("🛠️") ? (
              <div className="tool-indicator">
                <span /> <i>{msg.content}</i>
              </div>
            ) : (
               <ReactMarkdown>{msg.content}</ReactMarkdown>
            )}
          </div>
        ))}
        {loading && !messages[messages.length - 1].content && (
          <div className="message agent tool-indicator">
            <span /> Processing...
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      <div className="input-area">
        <input 
          type="text" 
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Command R.A.Z.A...."
          disabled={loading}
        />
        <button onClick={handleSend} disabled={loading}>
          ↗
        </button>
      </div>
    </div>
  );
}

export default App;
