import React, { useState } from 'react';
import Header from './components/Header';
import ChatWindow from './components/ChatWindow';
import ChatInput from './components/ChatInput';
import Sidebar from './components/Sidebar';


function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([
    { text: 'Hello! How can I help you today?', sender: 'bot' }
  ]);
  const [history, setHistory] = useState([
    'Previous conversation 1',
    'Another past chat',
  ]);
  const [isTyping, setIsTyping] = useState(false);

  const handleSendMessage = async (text) => {
    const userMessage = { text, sender: 'user' };
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    // Create a placeholder for the bot's response
    const botMessageId = Date.now();
    const botMessage = { text: '', sender: 'bot', logs: [], id: botMessageId };
    setMessages(prev => [...prev, botMessage]);

    try {
      const response = await fetch('/api/run_sse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          app_name: 'data_agent_chatbot',
          user_id: 'local_user', // Fixed user ID for local demo
          session_id: sessionId,
          new_message: {
            parts: [{ text: text }],
            role: 'user'
          }
        }),
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop(); // Keep incomplete chunk

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6);
            try {
              const event = JSON.parse(jsonStr);

              // console.log("Event:", event); // For debugging

              // 1. Session ID update
              if (event.session_id) {
                setSessionId(event.session_id);
              }

              // 2. Parse Content (Text or Tool Calls)
              if (event.content && event.content.parts) {
                setMessages(prevMessages => {
                  const newMsgs = [...prevMessages];
                  const lastMsg = newMsgs[newMsgs.length - 1]; // This is our bot message

                  // Make a copy to mutate
                  const updatedMsg = { ...lastMsg, logs: [...(lastMsg.logs || [])] };

                  event.content.parts.forEach(part => {
                    // A. Text Content
                    if (part.text) {
                      updatedMsg.text = (updatedMsg.text || '') + part.text;
                    }

                    // B. Function Calls (Logs)
                    if (part.function_call) {
                      const funcName = part.function_call.name;
                      const args = JSON.stringify(part.function_call.args);
                      updatedMsg.logs.push(`🛠️ Tool Call: ${funcName}\nArgs: ${args}`);
                    }

                    // C. Code Execution (Logs)
                    if (part.executable_code) {
                      updatedMsg.logs.push(`💻 Code:\n${part.executable_code.code}`);
                    }
                    if (part.code_execution_result) {
                      const outcome = part.code_execution_result.outcome;
                      const output = part.code_execution_result.output;
                      updatedMsg.logs.push(`⚙️ Output [${outcome}]:\n${output}`);
                    }
                  });

                  newMsgs[newMsgs.length - 1] = updatedMsg;
                  return newMsgs;
                });
              }

              // 3. Handle Errors
              if (event.error) {
                console.error("Agent Error:", event.error);
                setMessages(prev => {
                  const newMsgs = [...prev];
                  // Append error to text
                  newMsgs[newMsgs.length - 1].text += `\n[Error: ${event.error}]`;
                  return newMsgs;
                });
              }

            } catch (e) {
              console.error("Error parsing SSE JSON", e);
            }
          }
        }
      }

    } catch (err) {
      console.error("Request failed", err);
      // Update bot message to show error
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1].text = "Sorry, I encountered a connection error.";
        return newMsgs;
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleClearHistory = () => {
    setHistory([]);
    setMessages([{ text: '안녕하세요, 무엇을 도와드릴까요?', sender: 'bot' }]);
  };

  const handleNewChat = () => {
    setMessages([{ text: '안녕하세요, 무엇을 도와드릴까요?', sender: 'bot' }]);
  };

  return (
    <div className="App">
      <div className="App-body">
        <Sidebar history={history} onClearHistory={handleClearHistory} onNewChat={handleNewChat} />
        <div className="main-content">
          <Header />
          <div className="chat-container">
            <ChatWindow messages={messages} isTyping={isTyping} />
            <ChatInput onSendMessage={handleSendMessage} />
          </div>
        </div>
      </div>
      <footer style={{ textAlign: 'center', padding: '10px', fontSize: '0.8em', color: '#777', backgroundColor: '#f0f4f9' }}>
        This is Demo UI, and the Agent AI can make mistakes.
      </footer>
    </div>
  );
}

export default App;