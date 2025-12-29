import React from 'react';
import './Sidebar.css';

const Sidebar = ({ history, onClearHistory, onNewChat }) => {
  return (
    <div className="sidebar">
      <button onClick={onNewChat} className="new-chat-button">
        + New Chat
      </button>
      <h2>History</h2>
      <ul className="history-list">
        {history.map((item, index) => (
          <li key={index}>{item}</li>
        ))}
      </ul>
      <button onClick={onClearHistory} className="clear-history-button">
        Clear History
      </button>
    </div>
  );
};

export default Sidebar;
