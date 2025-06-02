import React, { useRef, useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { isAuthenticated, getCurrentUser } from '../services/auth_service';
import axios from 'axios';
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
  const [user, setUser] = useState(null);
  
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
  const [error, setError] = useState(null);
  
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
  
  // 上传按钮悬停状态
  const [isUploadHovered, setIsUploadHovered] = useState(false);
  
  // 生成UUID函数
  function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
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
  
  // 选择对话
  const handleSelectConversation = (conversationId) => {
    const selectedConversation = conversations.find(conv => conv.id === conversationId);
    if (selectedConversation) {
      setSessionId(conversationId);
      // 如果有保存的消息，则加载它们
      if (selectedConversation.messages && selectedConversation.messages.length > 0) {
        setMessages(selectedConversation.messages);
      }
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
      userMessages.push(createMessage(
        SenderRole.USER,
        messageContent,
        messageType,
        messageData
      ));
    } else if (messageContent) {
      // 纯文本消息
      userMessages.push(createMessage(SenderRole.USER, messageContent));
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
        response = await fetch('/api/agent/chat/with_file', {
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
        const assistantMessage = createMessage(
          SenderRole.ASSISTANT, 
          data.response.content || data.response,
          data.response.type || MessageType.TEXT,
          data.response.metadata || {}
        );
        
        // 如果有工具调用
        if (data.tool_calls && data.tool_calls.length > 0) {
          // 处理工具调用
          setActiveTools(data.tool_calls.map(tool => ({
            id: tool.id,
            name: tool.name,
            parameters: tool.parameters
          })));
          
          // 添加工具调用消息
          const toolMessage = createMessage(
            SenderRole.SYSTEM,
            `正在使用工具: ${data.tool_calls.map(t => t.name).join(', ')}`,
            MessageType.TOOL_OUTPUT,
            { tool_calls: data.tool_calls }
          );
          
          setMessages(prev => {
            const updatedMessages = [...prev, assistantMessage, toolMessage];
            
            // 如果用户已登录，自动保存对话
            if (isLoggedIn) {
              // 使用setTimeout确保状态更新后再保存
              setTimeout(async () => {
                await saveConversation(updatedMessages, currentConversationId);
              }, 100);
            }
            
            return updatedMessages;
          });
        } else {
          setMessages(prev => {
            const updatedMessages = [...prev, assistantMessage];
            
            // 如果用户已登录，自动保存对话
            if (isLoggedIn) {
              // 使用setTimeout确保状态更新后再保存
              setTimeout(async () => {
                await saveConversation(updatedMessages, currentConversationId);
              }, 100);
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
    
    // 清除活动工具
    setActiveTools([]);
  };

  // 自动滚动到最新消息
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // 保存对话到数据库
  const saveConversation = async (messageList, conversationId = null) => {
    // 只有登录用户才保存对话
    if (!isLoggedIn) {
      console.log('未登录，不保存对话');
      return null;
    }
    
    // 确保至少有一条消息
    if (!messageList || messageList.length === 0) {
      console.log('没有消息，不保存对话');
      return null;
    }
    
    console.log('开始保存对话，当前对话ID:', conversationId || currentConversationId || '新对话');
    
    try {
      // 准备数据
      const visibleMessages = messageList.filter(msg => msg.visible !== false);
      console.log('可见消息数量:', visibleMessages.length);
      
      const lastMessage = visibleMessages[visibleMessages.length - 1];
      let title = '新对话';
      let preview = '';
      
      // 设置标题和预览
      if (visibleMessages.length > 0) {
        const firstUserMessage = visibleMessages.find(msg => msg.role === SenderRole.USER);
        if (firstUserMessage && firstUserMessage.content) {
          title = typeof firstUserMessage.content === 'string' 
            ? firstUserMessage.content.substring(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '')
            : '新对话';
        }
        
        if (lastMessage && lastMessage.content) {
          preview = typeof lastMessage.content === 'string'
            ? lastMessage.content.substring(0, 50) + (lastMessage.content.length > 50 ? '...' : '')
            : '';
        }
      }
      
      console.log('对话标题:', title);
      console.log('对话预览:', preview);
      
      // 准备请求数据
      const conversationData = {
        id: conversationId || currentConversationId || generateUUID(),
        title,
        preview,
        lastUpdated: new Date().toISOString(),
        messages: visibleMessages,
        userId: localStorage.getItem('userId')
      };
      
      console.log('保存对话数据:', conversationData);
      
      // 确定请求方法和URL
      const method = conversationId || currentConversationId ? 'PUT' : 'POST';
      const API_BASE_URL = 'http://localhost:5000';
      const url = conversationId || currentConversationId 
        ? `${API_BASE_URL}/api/conversations/${conversationId || currentConversationId}` 
        : `${API_BASE_URL}/api/conversations`;
      
      console.log(`发送${method}请求到${url}`);
      
      // 发送请求保存对话
      const response = await fetch(url, {
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(conversationData)
      });
      
      console.log('保存对话响应状态:', response.status);
      
      if (!response.ok) {
        throw new Error(`保存对话失败: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('对话保存成功:', data);
      
      // 更新当前对话 ID
      const newConversationId = data.id || data.conversation_id || (data.conversation && data.conversation.id);
      if (newConversationId && (!conversationId && !currentConversationId)) {
        console.log('设置当前对话ID:', newConversationId);
        setCurrentConversationId(newConversationId);
      }
      
      // 立即更新侧边栏
      console.log('更新侧边栏对话列表');
      await fetchUserConversations();
      
      return newConversationId;
    } catch (error) {
      console.error('保存对话失败:', error);
      return null;
    }
  };

  // 从后端获取用户对话列表
  const fetchUserConversations = async () => {
    // 只有登录用户才获取对话
    if (!isLoggedIn) {
      console.log('未登录，不获取对话列表');
      return;
    }
    
    const userId = localStorage.getItem('userId');
    if (!userId) {
      console.log('未找到用户ID，不获取对话列表');
      return;
    }
    
    console.log('开始获取用户对话列表，用户ID:', userId);
    
    try {
      setIsLoadingConversations(true);
      
      // 后端使用JWT认证，不需要显式传递userId参数
      const token = localStorage.getItem('token');
      console.log('使用token获取对话列表:', token ? '有效token' : '无效token');
      
      // 使用完整的后端API URL
      const API_BASE_URL = 'http://localhost:5000';
      console.log('请求对话列表URL:', `${API_BASE_URL}/api/conversations`);
      
      const response = await fetch(`${API_BASE_URL}/api/conversations`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('对话列表API响应状态:', response.status);
      
      if (!response.ok) {
        throw new Error(`获取对话列表失败: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('获取到的对话数据:', data);
      
      if (data && Array.isArray(data.conversations)) {
        // 确保对话数据格式正确
        const processedConversations = data.conversations.map(conv => ({
          id: conv.id || conv._id,
          title: conv.title || '新对话',
          preview: conv.preview || '无预览内容',
          lastUpdated: conv.lastUpdated || conv.last_updated || new Date().toISOString(),
          messages: conv.messages || []
        }));
        
        console.log('处理后的对话列表:', processedConversations);
        setConversations(processedConversations);
        
        // 如果有对话且没有选中当前对话，自动选择最近的对话
        if (processedConversations.length > 0 && !currentConversationId) {
          // 按时间排序，选择最近的对话
          const sortedConversations = [...processedConversations].sort((a, b) => {
            const dateA = new Date(a.lastUpdated || 0);
            const dateB = new Date(b.lastUpdated || 0);
            return dateB - dateA;
          });
          
          const latestConversation = sortedConversations[0];
          console.log('自动选择最近的对话:', latestConversation);
          await handleSelectConversation(latestConversation.id);
        }
      } else {
        console.warn('后端返回的数据格式不正确:', data);
      }  
    } catch (error) {
      console.error('获取对话列表失败:', error);
      // 如果获取失败，设置一些默认对话
      setConversations([
        {
          id: 'error-1',
          title: '新对话',
          preview: '开始一个新的对话...',
          lastUpdated: new Date().toISOString(),
          messages: []
        }
      ]);
    } finally {
      setIsLoadingConversations(false);
    }
  };
  
  // 记录消息变化
  // 检查登录状态
  useEffect(() => {
    const checkLoginStatus = () => {
      const loginStatus = isAuthenticated();
      console.log('检查登录状态:', loginStatus ? '已登录' : '未登录');
      setIsLoggedIn(loginStatus);
      
      if (loginStatus) {
        const currentUser = getCurrentUser();
        setUser(currentUser);
        
        // 确保userId存在于localStorage中
        if (currentUser && currentUser.id && !localStorage.getItem('userId')) {
          console.log('从用户对象中获取并存储用户ID:', currentUser.id);
          localStorage.setItem('userId', currentUser.id);
        } else {
          console.log('用户ID状态:', localStorage.getItem('userId') ? '已存在' : '不存在');
        }
        
        // 如果已登录，获取用户的对话列表
        fetchUserConversations();
      }
    };
    
    checkLoginStatus();
  }, []);
  
  // 使用前面定义的fetchUserConversations函数
  
  useEffect(() => {
    console.log('Messages updated:', messages);
  }, [messages]);
  
  // 实现打字机效果
  useEffect(() => {
    // 找到所有正在打字的消息
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
