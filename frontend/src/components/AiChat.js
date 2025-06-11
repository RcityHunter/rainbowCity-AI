import React, { useRef, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { isAuthenticated, getCurrentUser } from '../services/auth_service';
import './AiChat.dark.css';
import ChatSidebar from './ChatSidebar';

// 消息类型枚举
const MessageType = {
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
const SenderRole = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system'
};

function AiChat() {
  const navigate = useNavigate();
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  // 用户状态 - 当前未使用但保留以便后续功能开发
  const [user] = useState(null);
  
  // 状态管理
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
  // 错误状态
  const [error, setError] = useState(null);
  
  // 会话状态
  const [sessionId, setSessionId] = useState(generateUUID());
  // 对话轮次ID - 用于标识对话轮次
  const [turnId, setTurnId] = useState(generateUUID());
  const [currentConversationId, setCurrentConversationId] = useState(null);
  
  // 聊天历史记录
  const [conversations, setConversations] = useState([]);
  const [isLoadingConversations, setIsLoadingConversations] = useState(false);
  
  // 工具状态
  // 可用工具列表
  const [availableTools] = useState([
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
  
  // 上传按钮悬停状态
  const [isUploadHovered, setIsUploadHovered] = useState(false);
  
  // 自动滚动到最新消息
  useEffect(() => {
    const scrollToBottom = () => {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    scrollToBottom();
  }, [messages]);
  

  
  // 检查登录状态
  useEffect(() => {
    const checkLoginStatus = async () => {
      const loginStatus = isAuthenticated();
      setIsLoggedIn(loginStatus);
      
      if (loginStatus) {
        try {
          const currentUser = await getCurrentUser();
          // setUser(currentUser); // 当前未使用，暂时注释
        } catch (err) {
          console.error('获取用户信息失败:', err);
        }
      }
    };
    
    checkLoginStatus();
    // 调用获取对话列表函数
    if (typeof fetchUserConversations === 'function') {
      fetchUserConversations();
    }
  }, []);
  
  // 实现打字机效果
  useEffect(() => {
    const typingMessages = messages.filter(msg => msg.isTyping && msg.displayedContent !== msg.content);
    
    if (typingMessages.length === 0) return;
    
    // 对每个正在打字的消息设置定时器
    const timers = typingMessages.map(message => {
      return setTimeout(() => {
        setMessages(prevMessages => {
          return prevMessages.map(msg => {
            if (msg.id === message.id) {
              // 如果显示内容已经等于完整内容，则停止打字
              if (msg.displayedContent === msg.content) {
                return { ...msg, isTyping: false };
              }
              
              // 否则添加下一个字符
              const nextChar = msg.content.charAt(msg.displayedContent.length);
              return { 
                ...msg, 
                displayedContent: msg.displayedContent + nextChar 
              };
            }
            return msg;
          });
        });
      }, 30); // 每30毫秒添加一个字符
    });
    
    // 清除定时器
    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [messages]);
  
  // 生成UUID函数
  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0;
      const v = c === 'x' ? r : ((r & 0x3) | 0x8);
      return v.toString(16);
    });
  }

  // 处理文本输入变化
  const handleInputChange = (e) => {
    setTextInput(e.target.value);
  };

  // 处理文件附件上传
  const handleFileUpload = (e, fileType = 'any') => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;
    
    let filteredFiles = files;
    
    // 根据文件类型过滤
    if (fileType === 'image') {
      filteredFiles = files.filter(file => file.type.startsWith('image/'));
    } else if (fileType === 'audio') {
      filteredFiles = files.filter(file => file.type.startsWith('audio/'));
    } else if (fileType === 'video') {
      filteredFiles = files.filter(file => file.type.startsWith('video/'));
    } else if (fileType === 'document') {
      filteredFiles = files.filter(file => 
        !file.type.startsWith('image/') && 
        !file.type.startsWith('audio/') && 
        !file.type.startsWith('video/'));
    }
    
    const newAttachments = filteredFiles.map(file => ({
      id: generateUUID(),
      file,
      type: file.type.startsWith('image/') ? MessageType.IMAGE : 
            file.type.startsWith('audio/') ? MessageType.AUDIO : 
            file.type.startsWith('video/') ? MessageType.VIDEO : 
            MessageType.DOCUMENT,
      name: file.name,
      size: file.size,
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : null
    }));
    
    setAttachments(prev => [...prev, ...newAttachments]);
  };
  
  // 处理不同类型的文件上传
  const handleImageUpload = (e) => handleFileUpload(e, 'image');
  const handleAudioUpload = (e) => handleFileUpload(e, 'audio');
  const handleVideoUpload = (e) => handleFileUpload(e, 'video');
  const handleDocumentUpload = (e) => handleFileUpload(e, 'document');
  
  // 删除附件
  const removeAttachment = (attachmentId) => {
    setAttachments(prev => prev.filter(attachment => attachment.id !== attachmentId));
  };

  // 创建新的消息对象
  const createMessage = (role, content, type = MessageType.TEXT, additionalData = {}) => {
    // 创建基本消息对象
    const message = {
      id: generateUUID(),
      role,
      content,
      type,
      timestamp: new Date().toISOString(),
      visible: true,
      isTyping: role === SenderRole.ASSISTANT, // 助手消息默认启用打字机效果
      displayedContent: role === SenderRole.ASSISTANT ? '' : content, // 初始显示内容为空
    };
    
    // 如果是混合消息，确保数据结构正确
    if (type === MessageType.MIXED && additionalData.attachment) {
      message.data = {
        attachment: additionalData.attachment
      };
    }
    
    // 合并其他附加数据
    return { ...message, ...additionalData };
  };

  // 创建新聊天
  const handleCreateNewChat = () => {
    // 创建新的会话ID
    const newSessionId = generateUUID();
    setSessionId(newSessionId);
    
    // 重置消息列表
    setMessages([
      {
        id: generateUUID(),
        role: SenderRole.SYSTEM,
        content: '你是彩虹城系统的AI助手，专门解答关于彩虹城系统、频率编号和关系管理的问题。',
        type: MessageType.SYSTEM,
        timestamp: new Date().toISOString(),
        visible: false
      },
      {
        id: generateUUID(),
        role: SenderRole.ASSISTANT,
        content: '你好！我是彩虹城AI助手。我可以帮助你了解彩虹城系统、频率编号和关系管理。有什么我可以帮你的吗？',
        type: MessageType.TEXT,
        timestamp: new Date().toISOString(),
        visible: true
      }
    ]);
    
    // 创建新的对话记录
    const newConversation = {
      id: newSessionId,
      title: '新对话 ' + new Date().toLocaleString(),
      preview: '你好！我是彩虹城AI助手...',
      lastUpdated: new Date().toISOString(),
      messages: []
    };
    
    setConversations(prev => [newConversation, ...prev]);
  };
  
  // 从后端获取用户对话列表
  const fetchUserConversations = async () => {
    try {
      // 检查用户是否登录
      if (!isAuthenticated()) {
        console.log('用户未登录，不获取对话列表');
        return;
      }
      
      setIsLoadingConversations(true);
      const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000';
      const token = localStorage.getItem('token');
      
      // 检查token是否存在
      if (!token) {
        console.error('未找到用户认证令牌，请重新登录');
        // 可能需要重定向到登录页
        return;
      }
      
      console.log('获取用户对话列表:', `${API_BASE_URL}/api/chats`);
      console.log('使用的认证令牌:', `Bearer ${token.substring(0, 10)}...`);
      
      const response = await fetch(`${API_BASE_URL}/api/chats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        },
        credentials: 'include' // 包含cookie信息
      });
      
      if (!response.ok) {
        if (response.status === 401) {
          console.error('认证失败，可能令牌已过期，请重新登录');
          // 清除本地存储的过期令牌
          localStorage.removeItem('token');
          setIsLoggedIn(false);
          return;
        }
        throw new Error(`获取用户对话列表失败: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('获取到的用户对话列表:', data);
      
      if (data && Array.isArray(data.conversations)) {
        // 处理对话列表数据
        const processedConversations = data.conversations.map(conversation => ({
          id: conversation.id,
          title: conversation.title,
          preview: conversation.preview,
          lastUpdated: conversation.lastUpdated,
          messages: conversation.messages
        }));
        
        setConversations(processedConversations);
      } else {
        console.warn('用户对话列表数据格式不正确:', data);
      }
    } catch (error) {
      console.error('获取用户对话列表失败:', error);
    } finally {
      setIsLoadingConversations(false);
    }
  };

  // 选择对话
  const handleSelectConversation = async (conversationId) => {
    console.log('选择对话:', conversationId);
    if (!conversationId) return;
    
    try {
      setIsLoading(true);
      setCurrentConversationId(conversationId);
      setSessionId(conversationId); // 设置会话ID
      
      // 获取选中对话的消息
      const API_BASE_URL = process.env.NODE_ENV === 'production' ? '' : 'http://localhost:5000';
      const token = localStorage.getItem('token');
      
      console.log('获取对话消息:', `${API_BASE_URL}/api/chats/${conversationId}/messages`);
      const response = await fetch(`${API_BASE_URL}/api/chats/${conversationId}/messages`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      
      if (!response.ok) {
        throw new Error(`获取对话消息失败: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('获取到的对话消息:', data);
      
      if (data && Array.isArray(data.messages)) {
        // 处理消息数据
        const processedMessages = data.messages.map(msg => ({
          id: msg.id || `msg-${Date.now()}-${Math.random()}`,
          role: msg.role || SenderRole.USER,
          content: msg.content || '',
          type: msg.content_type || MessageType.TEXT,
          timestamp: msg.created_at || new Date().toISOString(),
          visible: true,
          metadata: msg.metadata || {}
        }));
        
        // 如果没有消息，添加一个默认的系统消息
        if (processedMessages.length === 0) {
          processedMessages.push({
            id: `system-${Date.now()}`,
            role: SenderRole.SYSTEM,
            content: '没有找到历史消息',
            type: MessageType.TEXT,
            timestamp: new Date().toISOString(),
            visible: true
          });
        }
        
        setMessages(processedMessages);
      } else {
        console.warn('对话消息数据格式不正确:', data);
        // 设置一个默认消息
        setMessages([
          {
            id: `system-${Date.now()}`,
            role: SenderRole.ASSISTANT,
            content: '你好！我是彩虹城AI，有什么我可以帮你的吗？',
            type: MessageType.TEXT,
            timestamp: new Date().toISOString(),
            visible: true
          }
        ]);
      }
    } catch (error) {
      console.error('选择对话失败:', error);
      setError(error.message || String(error));
      // 设置一个错误消息
      setMessages([
        {
          id: `error-${Date.now()}`,
          role: SenderRole.SYSTEM,
          content: `加载对话失败: ${error.message || '未知错误'}`,
          type: MessageType.TEXT,
          timestamp: new Date().toISOString(),
          visible: true,
          metadata: { error: true }
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };
  
  // 处理表单提交
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!textInput.trim() && attachments.length === 0) return;
    
    // 创建新的回合ID
    const newTurnId = generateUUID();
    setTurnId(newTurnId);
    
    // 准备用户消息
    const userMessages = [];
    
    // 处理用户消息，将文本和图片合并为一个消息
    let messageContent = textInput.trim();
    let messageType = MessageType.TEXT;
    let messageData = {};
    let imageAttachment = null;
    
    // 检查是否有图片附件
    if (attachments.length > 0) {
      for (const attachment of attachments) {
        if (attachment.type === MessageType.IMAGE) {
          imageAttachment = attachment;
          messageType = MessageType.MIXED; // 混合类型（文本+图片）
          messageData = { 
            text: messageContent,
            attachment: attachment 
          };
          break;
        }
      }
    }
    
    // 创建用户消息
    if (messageType === MessageType.MIXED) {
      // 混合消息（文本+图片）
      userMessages.push({
        ...createMessage(
          SenderRole.USER,
          messageContent,
          messageType,
          messageData
        ),
        visible: true // 确保消息可见
      });
    } else if (messageContent) {
      // 纯文本消息
      userMessages.push({
        ...createMessage(SenderRole.USER, messageContent),
        visible: true // 确保消息可见
      });
    }
    
    // 保存图片附件到永久存储
    if (imageAttachment) {
      // 检查是否已经保存过该图片
      const alreadySaved = savedAttachments.some(saved => saved.id === imageAttachment.id);
      if (!alreadySaved) {
        setSavedAttachments(prev => [...prev, imageAttachment]);
      }
    }
    
    // 添加用户消息到状态
    setMessages(prev => [...prev, ...userMessages]);
    setTextInput('');
    setAttachments([]);
    setIsLoading(true);
    setError(null);
    
    try {
      // 准备请求数据
      const visibleMessages = messages
        .filter(msg => msg.visible || msg.role === SenderRole.SYSTEM)
        .concat(userMessages)
        .map(msg => ({
          role: msg.role,
          content: msg.content,
          type: msg.type
        }));
      
      // 决定使用哪个聊天端点
      const chatEndpoint = useAgentChat ? '/api/chat/agent' : '/api/chat';
      
      let response;
      
      // 如果有文件附件且使用Agent模式，使用多部分表单提交
      if (attachments.length > 0 && useAgentChat) {
        // 获取第一个附件（目前每次只处理一个附件）
        const attachment = attachments[0];
        const formData = new FormData();
        formData.append('user_input', textInput.trim());
        formData.append('session_id', sessionId);
        formData.append('user_id', localStorage.getItem('userId') || 'anonymous');
        formData.append('ai_id', 'ai_rainbow_city');
        
        // 根据文件类型选择不同的字段名
        let fieldName = 'file';
        if (attachment.type === MessageType.IMAGE) fieldName = 'image';
        if (attachment.type === MessageType.AUDIO) fieldName = 'audio';
        if (attachment.type === MessageType.VIDEO) fieldName = 'video';
        if (attachment.type === MessageType.DOCUMENT) fieldName = 'document';
        
        // 如果有原始文件，使用原始文件
        if (attachment.file) {
          formData.append(fieldName, attachment.file);
        } 
        // 如果有预览URL，尝试转换为Blob
        else if (attachment.preview && attachment.preview.startsWith('data:')) {
          try {
            const res = await fetch(attachment.preview);
            const blob = await res.blob();
            formData.append(fieldName, blob, attachment.name || 'file');
          } catch (error) {
            console.error('Error converting preview to blob:', error);
          }
        }
        
        // 使用新的统一文件处理端点
        response = await fetch('/api/chat/agent/with_file', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}` // 添加认证令牌
          },
          body: formData
        });
      } 
      // 否则使用标准JSON请求
      else {
        response = await fetch(chatEndpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}` // 添加认证令牌
          },
          body: JSON.stringify({
            session_id: sessionId,
            turn_id: newTurnId,
            messages: visibleMessages,
            user_id: localStorage.getItem('userId') || 'anonymous',
            ai_id: 'ai_rainbow_city'
          }),
        });
      }
      
      if (!response.ok) {
        throw new Error(`服务器错误: ${response.status}`);
      }
      
      const data = await response.json();
      
      // 处理响应
      if (data.response) {
        // 创建助手消息
        const assistantMessage = {
          ...createMessage(
            SenderRole.ASSISTANT, 
            data.response.content || data.response,
            data.response.type || MessageType.TEXT,
            data.response.metadata || {}
          ),
          visible: true // 确保消息可见
        };
        
        // 重置加载状态
        setIsLoading(false);
        
        // 如果有工具调用
        if (data.tool_calls && data.tool_calls.length > 0) {
          // 处理工具调用
          setActiveTools(data.tool_calls.map(tool => ({
            id: tool.id,
            name: tool.name,
            parameters: tool.parameters
          })));
          
          // 添加工具调用消息
          const toolMessage = {
            ...createMessage(
              SenderRole.SYSTEM,
              `正在使用工具: ${data.tool_calls.map(t => t.name).join(', ')}`,
              MessageType.TOOL_OUTPUT,
              { tool_calls: data.tool_calls }
            ),
            visible: true // 确保消息可见
          };
          
          // 使用回调函数形式更新消息，确保基于最新的状态
          setMessages(prevMessages => {
            const updatedMessages = [...prevMessages, assistantMessage, toolMessage];
            
            // 如果用户已登录，自动保存对话
            if (isLoggedIn) {
              // 直接保存对话，不使用setTimeout
              console.log('直接调用saveConversation保存对话...');
              // 立即保存对话并等待完成
              (async () => {
                try {
                  const savedId = await saveConversation(updatedMessages, currentConversationId);
                  console.log('对话保存完成，ID:', savedId);
                } catch (saveError) {
                  console.error('保存对话时出错:', saveError);
                }
              })();
            }
            
            return updatedMessages;
          });
        } else {
          // 使用回调函数形式更新消息，确保基于最新的状态
          setMessages(prevMessages => {
            const updatedMessages = [...prevMessages, assistantMessage];
            
            // 如果用户已登录，自动保存对话
            if (isLoggedIn) {
              console.log('直接调用saveConversation保存对话...');
              (async () => {
                try {
                  const savedId = await saveConversation(updatedMessages, currentConversationId);
                  console.log('对话保存完成，ID:', savedId);
                } catch (saveError) {
                  console.error('保存对话时出错:', saveError);
                }
              })();
            }
            
            return updatedMessages;
          });
        }
      } else if (data.error) {
        throw new Error(data.error);
      } else {
        throw new Error('未知响应格式');
      }
    } catch (err) {
      console.error('Chat error:', err);
      // 重置加载状态
      setIsLoading(false);
      setError(err.message || String(err));
      
      // 添加错误消息
      const errorMessage = createMessage(
        SenderRole.SYSTEM,
        `错误: ${err.message || '未知错误'}`,
        MessageType.TEXT,
        { error: true }
      );
      
      setMessages(prev => [...prev, errorMessage]);
      
      // 如果发送失败，将最近使用的图片附件添加回附件列表
      if (imageAttachment) {
        setAttachments([imageAttachment]);
      }
} finally {
  setIsLoading(false);
}
};

// 处理工具调用
const handleToolAction = (toolId, action) => {
  // 如果是导航到其他页面
  if (action === 'navigate') {
    const toolRoutes = {
      'frequency_generator': '/frequency-generator',
      'ai_id_generator': '/ai-id-generator',
      'relationship_manager': '/ai-relationships'
    };
    
    if (toolRoutes[toolId]) {
      navigate(toolRoutes[toolId]);
    }
  }
};

// 保存对话到数据库
const saveConversation = async (messageList, conversationId = null) => {
  console.log('===== saveConversation 开始执行 =====');
  // ...
};

// 渲染消息内容
const renderMessageContent = (message) => {
    // 准备要显示的内容，如果在打字中则使用displayedContent
    const contentToShow = message.isTyping ? message.displayedContent : message.content;
    
    switch (message.type) {
      case MessageType.MIXED:
        // 混合消息（文本+图片）
        return (
          <div className="message-mixed">
            {/* 先显示文本部分 */}
            {contentToShow && contentToShow.trim() !== '' && (
              <div className="message-text">
                {contentToShow.split('\n').map((line, i) => (
                  <p key={i}>{line || ' '}</p>
                ))}
              </div>
            )}
            
            {/* 然后显示图片部分 */}
            {message.data && message.data.attachment && (
              <div className="message-image-container">
                <img 
                  src={message.data.attachment.preview || message.data.attachment.url || message.data.attachment.content} 
                  alt="图片附件" 
                  className="mixed-message-image"
                />
              </div>
            )}
          </div>
        );
      case MessageType.IMAGE:
        return (
          <div className="message-image">
            <img src={message.content} alt="图片附件" className="standalone-image" />
            {message.attachment && <div className="image-caption">{message.attachment.name}</div>}
          </div>
        );
      case MessageType.AUDIO:
        return (
          <div className="message-audio">
            <audio controls src={message.content}>
              您的浏览器不支持音频元素。
            </audio>
            {message.attachment && <div className="audio-caption">{message.attachment.name}</div>}
          </div>
        );
      case MessageType.TOOL_OUTPUT:
        return (
          <div className="message-tool">
            <div className="tool-content">{contentToShow}</div>
            {message.tool_calls && (
              <div className="tool-actions">
                {message.tool_calls.map((tool, index) => (
                  <button 
                    key={`${message.id}_${tool.name}_${index}`}
                    className="tool-action-button"
                    onClick={() => handleToolAction(tool.id, 'navigate')}
                  >
                    打开 {tool.name}
                  </button>
                ))}
              </div>
            )}
          </div>
        );
      case MessageType.TEXT:
      default:
        return (
          <div className="message-content">
            {contentToShow}
          </div>
        );
    }
  };

  // 渲染附件预览
  const renderAttachmentPreviews = () => {
    if (attachments.length === 0) return null;
    
    return (
      <div className="attachments-preview">
        {attachments.map(attachment => (
          <div key={attachment.id} className="attachment-item">
            {attachment.type === MessageType.IMAGE && (
              <div className="attachment-image-wrapper">
                <img src={attachment.preview} alt={attachment.name} className="attachment-preview" />
              </div>
            )}
            {attachment.type === MessageType.AUDIO && (
              <div className="audio-attachment-preview">
                <i className="audio-icon"></i>
                <span>{attachment.name}</span>
              </div>
            )}
            <button 
              type="button" 
              className="remove-attachment" 
              onClick={() => removeAttachment(attachment.id)}
            >
              &times;
            </button>
          </div>
        ))}
      </div>
    );
  };

  // 渲染已保存的图片
  const renderSavedImages = () => {
    if (savedAttachments.length === 0) return null;
    
    return (
      <div className="saved-images-container">
        <h4 className="saved-images-title">最近上传的图片</h4>
        <div className="saved-images-grid">
          {savedAttachments.map(attachment => (
            <div key={attachment.id} className="saved-image-item">
              <img 
                src={attachment.preview} 
                alt={attachment.name} 
                className="saved-image-preview" 
                onClick={() => {
                  // 点击已保存的图片时，将其添加到当前附件中
                  if (!attachments.some(a => a.id === attachment.id)) {
                    setAttachments(prev => [...prev, attachment]);
                  }
                }}
              />
              <button 
                type="button" 
                className="remove-saved-image" 
                onClick={() => {
                  // 从已保存的图片中移除
                  setSavedAttachments(prev => prev.filter(a => a.id !== attachment.id));
                }}
              >
                &times;
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="ai-chat-container">
      <ChatSidebar 
        conversations={conversations}
        onSelectConversation={handleSelectConversation}
        onCreateNewChat={handleCreateNewChat}
        isLoading={isLoadingConversations}
      />
      <div className="messages-container">
        {messages
          .filter(message => message.visible)
          .map((message) => (
            <div 
              key={message.id} 
              className={`message-wrapper ${message.role === SenderRole.ASSISTANT ? 'assistant-wrapper' : 
                         message.role === SenderRole.USER ? 'user-wrapper' : 'system-wrapper'}`}
            >
              <div 
                className={`message ${message.role === SenderRole.ASSISTANT ? 'assistant' : 
                           message.role === SenderRole.USER ? 'user' : 'system'} 
                           ${message.error ? 'error' : ''}`}
              >
                <div className="message-role">
                  {message.role === SenderRole.USER ? '你' : 
                   message.role === SenderRole.ASSISTANT ? '彩虹城AI' : 
                   '系统'}
                  <span className="message-time">
                    {new Date(message.timestamp).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'})}
                  </span>
                </div>
                {renderMessageContent(message)}
              </div>
            </div>
        ))}
        
        {isLoading && (
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
                  onClick={() => handleToolAction(tool.id, 'navigate')}
                >
                  打开
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {renderSavedImages()}
      
      <form onSubmit={handleSubmit} className="input-form">
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
        
        {renderAttachmentPreviews()}
        
        <div className="input-controls">
          <div 
            className="upload-container"
            onMouseEnter={() => setIsUploadHovered(true)}
            onMouseLeave={() => setIsUploadHovered(false)}
          >
            <button 
              type="button" 
              className="attachment-button"
              disabled={isLoading}
            >
              <i className="attachment-icon"></i>
            </button>
            
            {/* 悬停时显示的上传选项 */}
            <div className={`upload-options ${isUploadHovered ? 'visible' : ''}`}>
              {/* 图片上传 */}
              <button 
                type="button" 
                className="upload-option-button image-upload"
                onClick={() => imageInputRef.current.click()}
                title="上传图片"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#a18cd1">
                  <path d="M21 17h-2v-4h-4v-2h4V7h2v4h4v2h-4v4z"/>
                  <path d="M16 21H5c-1.1 0-2-.9-2-2V8c0-1.1.9-2 2-2h11c1.1 0 2 .9 2 2v13h-2zm-11-2h9V8H5v11z"/>
                  <path d="M7 17l2.5-3 1.5 2 2-2.5 3 3.5H7z"/>
                  <circle cx="8.5" cy="10.5" r="1.5"/>
                </svg>
              </button>
              
              {/* 音频上传 */}
              <button 
                type="button" 
                className="upload-option-button audio-upload"
                onClick={() => audioInputRef.current.click()}
                title="上传音频"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#a18cd1">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                  <path d="M15 5.5c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5.67 1.5 1.5 1.5 1.5-.67 1.5-1.5z"/>
                  <path d="M12 3c-.55 0-1 .45-1 1s.45 1 1 1 1-.45 1-1-.45-1-1-1z"/>
                  <path d="M19 11h2c0 4.97-4.03 9-9 9s-9-4.03-9-9h2c0 3.87 3.13 7 7 7s7-3.13 7-7z"/>
                </svg>
              </button>
              
              {/* 视频上传 */}
              <button 
                type="button" 
                className="upload-option-button video-upload"
                onClick={() => videoInputRef.current.click()}
                title="上传视频"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#a18cd1">
                  <path d="M17 10.5V7c0-.55-.45-1-1-1H4c-.55 0-1 .45-1 1v10c0 .55.45 1 1 1h12c.55 0 1-.45 1-1v-3.5l4 4v-11l-4 4z"/>
                </svg>
              </button>
              
              {/* 文档上传 */}
              <button 
                type="button" 
                className="upload-option-button document-upload"
                onClick={() => documentInputRef.current.click()}
                title="上传文档"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#a18cd1">
                  <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/>
                </svg>
              </button>
            </div>
          </div>
          
          {/* 隐藏的文件输入 */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            style={{ display: 'none' }}
            multiple
            accept="image/*,audio/*,application/*,text/*"
          />
          
          <input
            type="file"
            ref={imageInputRef}
            onChange={handleImageUpload}
            style={{ display: 'none' }}
            multiple
            accept="image/*"
          />
          
          <input
            type="file"
            ref={audioInputRef}
            onChange={handleAudioUpload}
            style={{ display: 'none' }}
            multiple
            accept="audio/*"
          />
          
          <input
            type="file"
            ref={videoInputRef}
            onChange={handleVideoUpload}
            style={{ display: 'none' }}
            multiple
            accept="video/*"
          />
          
          <input
            type="file"
            ref={documentInputRef}
            onChange={handleDocumentUpload}
            style={{ display: 'none' }}
            multiple
            accept="application/*,text/*,.pdf,.doc,.docx,.txt,.xls,.xlsx,.ppt,.pptx"
          />
          
          <input
            value={textInput}
            onChange={handleInputChange}
            placeholder="输入您的问题..."
            className="chat-input"
            disabled={isLoading}
          />
          
          <button 
            type="submit" 
            disabled={isLoading || (!textInput.trim() && attachments.length === 0)} 
            className="send-button"
          >
            发送
          </button>
        </div>
      </form>
    </div>
  );
}

export default AiChat;
