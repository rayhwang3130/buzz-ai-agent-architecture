import React from 'react';

const Message = ({ text, sender }) => {
  const className = sender === 'user' ? 'user-message' : 'bot-message';

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
    return <p dangerouslySetInnerHTML={{ __html: text.replace(/\n/g, '<br />') }} />;
  };

  return (
    <div className={`message ${className}`}>
      <div className="message-bubble">{renderContent()}</div>
    </div>
  );
};

export default Message;