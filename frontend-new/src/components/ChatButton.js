import React, { useState } from 'react';
import AiChat from './AiChat';
import './ChatButton.css';

function ChatButton() {
  const [isOpen, setIsOpen] = useState(false);

  const toggleChat = () => {
    setIsOpen(!isOpen);
  };

  return (
    <>
      <div className="chat-button-container">
        <button className="chat-button" onClick={toggleChat} title="打开智能助手">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
            <path d="M12 1c-6.627 0-12 4.208-12 9.4 0 3.131 1.929 5.924 4.908 7.575l-1.394 3.48c-.153.39.145.734.56.6l5.435-1.762c.75.226 1.55.356 2.39.356 6.627 0 12-4.208 12-9.4s-5.373-9.4-12-9.4zm0 17c-.691 0-1.366-.076-2.024-.22l-2.393.786.87-2.174c-1.661-1.033-2.753-2.795-2.753-4.792 0-3.314 2.826-6 6.3-6s6.3 2.686 6.3 6-2.826 6-6.3 6z"/>
          </svg>
        </button>
      </div>

      {isOpen && (
        <div className="chat-modal">
          <div className="chat-modal-header">
            <h3 className="chat-modal-title">一体七翼智能助手</h3>
            <button className="chat-modal-close" onClick={toggleChat}>×</button>
          </div>
          <div className="chat-modal-content">
            <AiChat />
          </div>
        </div>
      )}
    </>
  );
}

export default ChatButton;
