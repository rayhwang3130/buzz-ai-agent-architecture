import React from 'react';

const Message = ({ text, sender, logs = [] }) => {
  const className = sender === 'user' ? 'user-message' : 'bot-message';
  const [showLogs, setShowLogs] = React.useState(false);

  const renderContent = () => {
    if (typeof text === 'object' && text.type === 'table') {
      return (
        <>
          {text.explanation && <p>{text.explanation}</p>}
          <table>
            <tbody>
              {text.data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      );
    }
    if (typeof text === 'object' && text.type === 'dual_table') {
      return (
        <>
          {text.explanation && <p>{text.explanation}</p>}
          {text.table1.title && <h4>{text.table1.title}</h4>}
          <table>
            <tbody>
              {text.table1.data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
          <br />
          {text.table2.title && <h4>{text.table2.title}</h4>}
          <table>
            <tbody>
              {text.table2.data.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex}>{cell}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      );
    }
    // Basic text rendering
    if (typeof text === 'string') {
      return <p dangerouslySetInnerHTML={{ __html: text.replace(/\n/g, '<br />') }} />;
    }
    return null;
  };

  return (
    <div className={`message ${className}`}>
      <div className="message-bubble">
        {renderContent()}

        {logs && logs.length > 0 && (
          <div className="message-logs" style={{ marginTop: '10px', fontSize: '0.85em', borderTop: '1px solid #eee', paddingTop: '5px' }}>
            <button
              onClick={() => setShowLogs(!showLogs)}
              style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer', padding: 0, textDecoration: 'underline' }}
            >
              {showLogs ? 'Hide Search Process' : 'Show Search Process'}
            </button>
            {showLogs && (
              <div style={{ backgroundColor: '#f9f9f9', padding: '10px', borderRadius: '5px', marginTop: '5px', maxHeight: '200px', overflowY: 'auto' }}>
                {logs.map((log, idx) => (
                  <div key={idx} style={{ marginBottom: '5px', fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                    {log}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Message;