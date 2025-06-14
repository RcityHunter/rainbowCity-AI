import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { isAuthenticated, getCurrentUser } from '../services/auth_service';
import { API_CONFIG, fetchWithTimeout, formatErrorMessage } from './AiChatConfig';

// 导入样式文件
import './AiChat.dark.css';

// 导入处理函数和渲染函数
import { 
  handleSubmit, 
  handleFileUpload, 
  handleImageUpload,
  handleAudioUpload,
  handleVideoUpload,
  handleDocumentUpload,
  handleAttachmentClick,
  removeAttachment,
  handleCreateNewChat,
  handleSelectConversation,
  handleToolAction,
  saveConversation,
  fetchUserConversations,
  checkLoginStatus,
  generateUUID
} from './AiChatHandlers';

import {
  renderMessageContent,
  renderAttachmentPreviews,
  renderSavedImages
} from './AiChatRenderers';

// 消息类型枚举
export const MessageType = {
  TEXT: 'text',
  IMAGE: 'image',
  AUDIO: 'audio',
  VIDEO: 'video',
  DOCUMENT: 'document',
  TOOL_OUTPUT: 'tool_output',
  SYSTEM: 'system',
  MIXED: 'mixed'  // 混合类型，包含文本和其他内容
};

// 发送者角色枚举
export const SenderRole = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system'
};

// 创建新的消息对象
export const createMessage = (role, content, type = MessageType.TEXT, additionalData = {}) => {
  return {
    id: generateUUID(),
    role,
    content,
    type,
    timestamp: new Date().toISOString(),
    ...additionalData
  };
};

function AiChatCore() {
  const navigate = useNavigate();
  
  // 状态管理
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [messages, setMessages] = useState([
    {
      id: '1',
      role: SenderRole.SYSTEM,
      content: '你是彩虹城系统的AI助手，专门解答关于彩虹城系统、频率编号和关系管理的问题。',
      type: MessageType.SYSTEM,
      timestamp: new Date().toISOString(),
      visible: false // 系统消息默认不显示
    },
    {
      id: '2',
      role: SenderRole.ASSISTANT,
      content: '你好！我是彩虹城AI，有什么我可以帮你的吗？',
      type: MessageType.TEXT,
      timestamp: new Date().toISOString(),
      visible: true,
      isTyping: true,
      displayedContent: '' // 初始为空字符串，将逐字显示
    }
  ]);
  
  // 是否使用Agent增强版聊天
  const [useAgentChat, setUseAgentChat] = useState(true);
  
  // 输入状态
  const [textInput, setTextInput] = useState('');
  const [attachments, setAttachments] = useState([]);
  const [savedAttachments, setSavedAttachments] = useState([]); // 已保存的附件，即使发送后仍然可用
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // 添加安全计时器，确保isLoading状态不会无限期地保持为true
  useEffect(() => {
    let safetyTimer;
    if (isLoading) {
      safetyTimer = setTimeout(() => {
        console.warn('[WARN] 安全计时器触发，重置加载状态');
        setIsLoading(false);
        setError('请求处理时间过长，已自动取消。请重试。');
      }, 30000); // 30秒后强制重置加载状态
    }
    return () => {
      if (safetyTimer) clearTimeout(safetyTimer);
    };
  }, [isLoading]);
  
  // 会话状态
  const [sessionId, setSessionId] = useState(generateUUID());
  const [turnId, setTurnId] = useState(generateUUID());
  const [currentConversationId, setCurrentConversationId] = useState(null);
  
  // 聊天历史记录
  const [conversations, setConversations] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  
  // 工具状态
  const [availableTools, setAvailableTools] = useState([
    { id: 'frequency_generator', name: '频率生成器', description: '生成频率编号' },
    { id: 'ai_id_generator', name: 'AI-ID生成器', description: '生成AI标识符' },
    { id: 'relationship_manager', name: '关系管理器', description: '管理AI关系' }
  ]);
  const [activeTools, setActiveTools] = useState([]);
  
  // 用于自动滚动到最新消息
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const videoInputRef = useRef(null);
  const documentInputRef = useRef(null);
  const inputRef = useRef(null);
  
  // 上传按钮悬停状态
  const [isUploadHovered, setIsUploadHovered] = useState(false);
  
  // 绑定处理函数到组件上下文
  const boundHandleSubmit = (e) => handleSubmit(e, {
    textInput, setTextInput, attachments, setAttachments, messages, setMessages,
    sessionId, turnId, setTurnId, generateUUID, useAgentChat, setIsLoading,
    setError, savedAttachments, setSavedAttachments, isLoggedIn,
    saveConversation, currentConversationId, setCurrentConversationId, setActiveTools, SenderRole,
    MessageType, createMessage, boundFetchUserConversations, navigate
  });
  
  const boundHandleFileUpload = (e, fileType) => handleFileUpload(e, fileType, {
    setAttachments, MessageType
  });
  
  const boundHandleImageUpload = (e) => handleImageUpload(e, { boundHandleFileUpload });
  const boundHandleAudioUpload = (e) => handleAudioUpload(e, { boundHandleFileUpload });
  const boundHandleVideoUpload = (e) => handleVideoUpload(e, { boundHandleFileUpload });
  const boundHandleDocumentUpload = (e) => handleDocumentUpload(e, { boundHandleFileUpload });
  
  const boundRemoveAttachment = (attachmentId) => removeAttachment(attachmentId, {
    setAttachments
  });
  
  const boundHandleCreateNewChat = () => {
    // 调用创建新对话函数
    handleCreateNewChat({
      setMessages, setSessionId, setTurnId, generateUUID, setCurrentConversationId,
      SenderRole, MessageType
    });
    
    // 导航到新对话路径
    if (navigate) {
      navigate('/ai-chat');
    }
  };
  
  const boundHandleSelectConversation = (conversationId) => handleSelectConversation(
    conversationId, {
      setIsLoading, setError, setCurrentConversationId, setMessages, setSessionId,
      navigate
    }
  );
  
  const boundHandleToolAction = (toolId, action) => handleToolAction(toolId, action, {
    navigate, availableTools
  });
  
  const boundFetchUserConversations = () => fetchUserConversations({
    setIsLoadingConversations, 
    setConversations, 
    setError, 
    setCurrentConversationId, 
    setSessionId, 
    setMessages, 
    navigate
  });
  
  // 测试API连接 - 使用新的配置和函数
  const testApiConnection = async () => {
    console.log('[DEBUG] 开始测试API连接...');
    setError(null);
    setIsLoading(true);
    
    try {
      // 使用新的fetchWithTimeout函数发送请求
      const response = await fetchWithTimeout(
        API_CONFIG.ENDPOINTS.HEALTH,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        },
        API_CONFIG.TIMEOUT // 使用配置中的超时时间
      );
      
      console.log('[DEBUG] API连接测试响应状态码:', response.status);
      
      if (!response.ok) {
        throw new Error(`服务器响应错误: ${response.status}`);
      }
      
      // 尝试读取响应内容
      const text = await response.text();
      console.log('[DEBUG] API连接测试响应内容:', text);
      
      // 显示成功消息
      setError(`API连接测试成功: ${response.status} - ${text}`);
    } catch (err) {
      console.error('[ERROR] API连接测试失败:', err);
      
      // 使用格式化错误消息函数
      const errorMessage = `API连接测试失败: ${formatErrorMessage(err)}`;
      
      // 输出错误详情便于调试
      console.error('[ERROR] 错误详情:', {
        message: err.message,
        name: err.name,
        stack: err.stack
      });
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 处理附件点击
  const handleAttachmentClick = () => {
    fileInputRef.current.click();
  };
  
  // 处理输入变化
  const handleInputChange = (e) => {
    setTextInput(e.target.value);
  };
  
  // 自动滚动到底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // 处理初始消息的打字动画效果
  useEffect(() => {
    // 查找所有标记为isTyping的消息
    const typingMessages = messages.filter(msg => msg.isTyping && msg.visible !== false);
    
    if (typingMessages.length > 0) {
      typingMessages.forEach(message => {
        const fullContent = message.content;
        let currentIndex = message.displayedContent ? message.displayedContent.length : 0;
        
        // 如果还没有显示完整的内容
        if (currentIndex < fullContent.length) {
          const typingInterval = setInterval(() => {
            setMessages(prevMessages => {
              return prevMessages.map(msg => {
                if (msg.id === message.id) {
                  const newIndex = msg.displayedContent ? msg.displayedContent.length + 1 : 1;
                  const newDisplayedContent = fullContent.substring(0, newIndex);
                  
                  // 如果已经显示完整内容，停止打字动画
                  if (newIndex >= fullContent.length) {
                    clearInterval(typingInterval);
                    return { ...msg, displayedContent: fullContent, isTyping: false };
                  }
                  
                  return { ...msg, displayedContent: newDisplayedContent };
                }
                return msg;
              });
            });
          }, 50); // 每50毫秒显示一个字符
        }
      });
    }
  }, []); // 只在组件挂载时运行一次
  
  // 检查登录状态并获取对话列表
  useEffect(() => {
    checkLoginStatus({ setIsLoggedIn, setUser });
    
    if (isLoggedIn) {
      boundFetchUserConversations();
    }
  }, [isLoggedIn]);
  
  // 渲染组件
  return (
    <div className="ai-chat-container">
      <div className="chat-sidebar">
        <div className="sidebar-header">
          <h2>对话历史</h2>
          <button 
            onClick={boundHandleCreateNewChat}
            className="new-chat-button"
          >
            新对话
          </button>
        </div>
        
        <div className="conversations-list">
          {isLoadingConversations ? (
            <div className="loading-conversations">加载中...</div>
          ) : conversations.length > 0 ? (
            conversations.map(conv => (
              <div 
                key={conv.id}
                className={`conversation-item ${currentConversationId === conv.id ? 'active' : ''}`}
                onClick={() => boundHandleSelectConversation(conv.id)}
              >
                <div className="conversation-title">
                  {conv.title || '新对话'}
                </div>
                <div className="conversation-date">
                  {new Date(conv.updated_at || conv.created_at).toLocaleDateString()}
                </div>
              </div>
            ))
          ) : (
            <div className="no-conversations">没有历史对话</div>
          )}
        </div>
      </div>
      
      <div className="chat-main">
        <div className="chat-header">
          <h1>彩虹城AI助手</h1>
          <div className="chat-settings">
            <label className="agent-toggle">
              <input 
                type="checkbox" 
                checked={useAgentChat} 
                onChange={() => setUseAgentChat(!useAgentChat)}
              />
              <span className="toggle-label">{useAgentChat ? "AI-Agent模式已启用" : "AI-Agent模式已关闭"}</span>
            </label>
          </div>
        </div>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <div className="messages-container">
          {messages.filter(msg => msg.visible !== false).map((message) => (
            <div key={message.id} className={`message-wrapper ${message.role}-wrapper`}>
              <div className={`message ${message.role}`}>
                <div className="message-role">
                  {message.role === SenderRole.USER ? '你' : 
                   message.role === SenderRole.ASSISTANT ? '彩虹城AI' : '系统'}
                  <span className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}
                  </span>
                </div>
                {renderMessageContent(message)}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="typing-indicator">
              <div className="message-wrapper assistant-wrapper">
                <div className="message assistant">
                  <div className="message-role">
                    彩虹城AI
                    <span className="message-time">
                      {new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}
                    </span>
                  </div>
                  <div className="thinking">
                    <div className="thinking-dots">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>
        
        {/* 活动工具区域 */}
        {activeTools.length > 0 && (
          <div className="active-tools">
            <div className="tools-header">可用工具</div>
            <div className="tools-list">
              {activeTools.map(tool => (
                <div key={tool.id} className="tool-item">
                  <div className="tool-name">{tool.name}</div>
                  <button 
                    className="tool-open-button"
                    onClick={() => boundHandleToolAction(tool.id, 'navigate')}
                  >
                    打开
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}
        
        {renderSavedImages({ savedAttachments, boundRemoveAttachment })}
        
        <form onSubmit={boundHandleSubmit} className="input-container">
          {attachments.length > 0 && (
            <div className="attachment-previews">
              {attachments.map((attachment, index) => (
                <div key={index} className="attachment-preview">
                  {attachment.type.startsWith('image/') ? (
                    <div className="image-preview">
                      <img src={URL.createObjectURL(attachment.file)} alt="Preview" className="preview-image" />
                      <button
                        type="button"
                        className="remove-attachment"
                        onClick={() => boundRemoveAttachment(index)}
                      >
                        ×
                      </button>
                    </div>
                  ) : attachment.type.startsWith('audio/') ? (
                    <div className="audio-preview">
                      <span>🎵</span>
                      <span className="file-name">{attachment.file.name}</span>
                      <button
                        type="button"
                        className="remove-attachment"
                        onClick={() => boundRemoveAttachment(index)}
                      >
                        ×
                      </button>
                    </div>
                  ) : attachment.type.startsWith('video/') ? (
                    <div className="video-preview">
                      <span>🎬</span>
                      <span className="file-name">{attachment.file.name}</span>
                      <button
                        type="button"
                        className="remove-attachment"
                        onClick={() => boundRemoveAttachment(index)}
                      >
                        ×
                      </button>
                    </div>
                  ) : (
                    <div className="document-preview">
                      <span>📄</span>
                      <span className="file-name">{attachment.file.name}</span>
                      <button
                        type="button"
                        className="remove-attachment"
                        onClick={() => boundRemoveAttachment(index)}
                      >
                        ×
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
          
          <div className="upload-container">
            <button
              type="button"
              onClick={handleAttachmentClick}
              className="attachment-button"
              disabled={isLoading}
            >
              <span className="attachment-icon"></span>
            </button>
            <input
              type="file"
              ref={fileInputRef}
              style={{ display: 'none' }}
              onChange={boundHandleFileUpload}
              multiple
            />
          </div>
          
          <div className="input-wrapper">
            <input
              type="text"
              value={textInput}
              onChange={handleInputChange}
              placeholder="输入消息..."
              disabled={isLoading}
              className="chat-input"
              ref={inputRef}
            />
          </div>
          
          <button
            type="button"
            onClick={testApiConnection}
            className="test-button"
            disabled={isLoading}
            title="测试API连接"
          >
            <i className="fas fa-plug"></i>
          </button>
          
          <button
            type="submit"
            className="send-button"
            disabled={isLoading || (!textInput.trim() && attachments.length === 0)}
          >
            <svg className="send-icon" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M22 2L11 13" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          
          {/* 注意：隐藏的文件输入已移动到上面的upload-container中 */}
        </form>
      </div>
    </div>
  );
}

export default AiChatCore;
