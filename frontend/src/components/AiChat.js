import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { isAuthenticated, getCurrentUser } from '../services/auth_service';
import './AiChat.dark.css';
import ChatSidebar from './ChatSidebar';
import MemoryContext from './MemoryContext';

// 获取API基础URL，使用React环境变量或默认值
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';

// 格式化消息时间戳的工具函数
const formatMessageTime = (timestamp) => {
  try {
    if (typeof timestamp === 'string') {
      if (timestamp.includes('T')) {
        // 处理ISO格式时间戳，如 "2023-06-19T09:40:29.123Z"
        const timePart = timestamp.split('T')[1];
        let hours = 0;
        let minutes = 0;
        
        if (timePart && timePart.includes('+')) {
          // 带有时区偏移的时间，如 "09:40:29+08:00"
          const timeWithoutOffset = timePart.split('+')[0];
          const timeParts = timeWithoutOffset.split(':');
          if (timeParts.length >= 2) {
            hours = parseInt(timeParts[0], 10) || 0;
            minutes = parseInt(timeParts[1], 10) || 0;
          }
        } else if (timePart && timePart.includes('Z')) {
          // UTC时间，如 "09:40:29.123Z"
          const timeWithoutZ = timePart.split('Z')[0];
          const timeParts = timeWithoutZ.split(':');
          if (timeParts.length >= 2) {
            hours = parseInt(timeParts[0], 10) || 0;
            minutes = parseInt(timeParts[1], 10) || 0;
          }
          
          // 调整为当前时区
          const offset = new Date().getTimezoneOffset();
          const offsetHours = Math.floor(Math.abs(offset) / 60);
          const offsetMinutes = Math.abs(offset) % 60;
          
          if (offset < 0) { // 东部时区，如亚洲
            hours += offsetHours;
            minutes += offsetMinutes;
          } else { // 西部时区，如美洲
            hours -= offsetHours;
            minutes -= offsetMinutes;
          }
        } else if (timePart) {
          // 无时区信息，如 "09:40:29"
          const timeParts = timePart.split(':');
          if (timeParts.length >= 2) {
            hours = parseInt(timeParts[0], 10) || 0;
            minutes = parseInt(timeParts[1], 10) || 0;
          }
        }
        
        // 处理进位和溢出
        if (minutes >= 60) {
          hours += 1;
          minutes -= 60;
        } else if (minutes < 0) {
          hours -= 1;
          minutes += 60;
        }
         
        if (hours >= 24) hours -= 24;
        else if (hours < 0) hours += 24;
        
        // 格式化为两位数字
        const formattedHours = hours.toString().padStart(2, '0');
        const formattedMinutes = minutes.toString().padStart(2, '0');
        return `${formattedHours}:${formattedMinutes}`;
      }
      
      // 如果不是ISO格式或处理失败，使用Date对象格式化
      const date = new Date(timestamp);
      if (!isNaN(date.getTime())) {
        return date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
      }
    }
    
    return ''; // 无法解析的时间戳
  } catch (e) {
    console.error('时间格式化错误:', e);
    return ''; // 出错时不显示时间
  }
};

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
  
  // 记忆系统状态
  const [userMemories, setUserMemories] = useState([]);
  const [sessionSummary, setSessionSummary] = useState(null);
  const [showMemoryContext, setShowMemoryContext] = useState(true);
  
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
  const [loadingError, setLoadingError] = useState(null);
  
  // 打字机效果状态 - 单独管理
  const [typingState, setTypingState] = useState({});
  // 格式: { messageId: { isTyping: true, displayedContent: '部分内容' } }
  
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
  
  // 全新打字机效果实现 - 使用单独的状态管理
  useEffect(() => {
    // 检查是否有新的AI消息需要添加到打字机状态中
    const aiMessages = messages.filter(m => m.role === SenderRole.ASSISTANT);
    
    // 对于每个AI消息，如果它不在typingState中，则添加它
    aiMessages.forEach(message => {
      if (!typingState[message.id] && message.content) {
        console.log(`发现新的AI消息，添加到打字机状态: ${message.id.substring(0, 6)}`);
        setTypingState(prev => ({
          ...prev,
          [message.id]: {
            isTyping: true,
            displayedContent: '',
            fullContent: extractResponseContent(message.content)
          }
        }));
      }
    });
  }, [messages, typingState]);
  
  // 处理打字机效果的核心逻辑
  useEffect(() => {
    // 找出所有正在打字的消息
    const typingMessageIds = Object.keys(typingState).filter(id => 
      typingState[id].isTyping && 
      typingState[id].displayedContent !== typingState[id].fullContent
    );
    
    if (typingMessageIds.length > 0) {
      console.log(`当前有 ${typingMessageIds.length} 条消息正在打字:`, 
        typingMessageIds.map(id => id.substring(0, 6)));
    }
    
    // 为每个正在打字的消息创建定时器
    const timers = typingMessageIds.map(id => {
      return setTimeout(() => {
        setTypingState(prev => {
          const messageState = prev[id];
          if (!messageState) return prev;
          
          // 如果已经打字完成，则停止打字
          if (messageState.displayedContent === messageState.fullContent) {
            console.log(`消息 ${id.substring(0, 6)} 打字完成`);
            return {
              ...prev,
              [id]: {
                ...messageState,
                isTyping: false
              }
            };
          }
          
          // 添加下一个字符
          const nextChar = messageState.fullContent.charAt(messageState.displayedContent.length);
          const newDisplayedContent = messageState.displayedContent + nextChar;
          
          console.log(`消息 ${id.substring(0, 6)} 添加字符: '${nextChar}', 进度: ${newDisplayedContent.length}/${messageState.fullContent.length}`);
          
          return {
            ...prev,
            [id]: {
              ...messageState,
              displayedContent: newDisplayedContent,
              isTyping: newDisplayedContent !== messageState.fullContent
            }
          };
        });
      }, 30); // 每30毫秒添加一个字符
    });
    
    // 清除定时器
    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [typingState]);
  
  // 当消息更新时，尝试获取最新的记忆上下文
  useEffect(() => {
    // 当消息数量增加且是对话进行中时，每5条消息更新一次记忆上下文
    if (isLoggedIn && sessionId && messages.length > 0 && messages.length % 5 === 0) {
      fetchMemoryContext();
    }
  }, [messages.length, isLoggedIn, sessionId]);
  
  // 获取用户记忆和会话摘要
  const fetchMemoryContext = async () => {
    if (!sessionId || !isLoggedIn) return;
    
    try {
      // 获取用户记忆
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
      console.log('内存API基础URL:', API_BASE_URL);
      const memoriesResponse = await fetch(`${API_BASE_URL}/memory/user/${localStorage.getItem('userId')}?limit=5`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (memoriesResponse.ok) {
        const memoriesData = await memoriesResponse.json();
        setUserMemories(memoriesData.memories || []);
      }
      
      // 获取会话摘要
      const summaryResponse = await fetch(`${API_BASE_URL}/memory/summary/${sessionId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (summaryResponse.ok) {
        const summaryData = await summaryResponse.json();
        setSessionSummary(summaryData.summary || null);
      }
    } catch (error) {
      console.error('获取记忆上下文失败:', error);
    }
  };
  
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

  // 按时间戳对消息进行排序
  const sortMessagesByTimestamp = (messages) => {
    // 首先检查是否有消息
    if (!messages || messages.length === 0) {
      return [];
    }
    
    // 深拷贝消息数组，避免修改原始数组
    const sortedMessages = [...messages];
    
    // 打印每条消息的时间戳信息，便于调试
    console.log('排序前的消息时间戳:', sortedMessages.map(m => {
      // 安全地处理content，可能不是字符串
      let contentPreview = '';
      if (m.content !== undefined && m.content !== null) {
        if (typeof m.content === 'string') {
          contentPreview = m.content.substring(0, 20) + (m.content.length > 20 ? '...' : '');
        } else {
          contentPreview = JSON.stringify(m.content).substring(0, 20) + '...';
        }
      }
      
      return {
        role: m.role,
        content: contentPreview,
        timestamp: m.timestamp,
        parsed: m.timestamp ? new Date(m.timestamp).toISOString() : 'invalid'
      };
    }));
    
    // 按时间戳升序排序（从早到晚）
    const result = sortedMessages.sort((a, b) => {
      // 尝试解析时间戳，处理可能的无效时间戳
      let timeA, timeB;
      
      try {
        timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
        if (isNaN(timeA)) timeA = 0;
      } catch (e) {
        console.error('无法解析时间戳A:', a.timestamp, e);
        timeA = 0;
      }
      
      try {
        timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
        if (isNaN(timeB)) timeB = 0;
      } catch (e) {
        console.error('无法解析时间戳B:', b.timestamp, e);
        timeB = 0;
      }
      
      // 升序排列，早的在前，晚的在后
      return timeA - timeB;
    });
    
    // 打印排序后的消息时间戳，便于调试
    console.log('排序后的消息时间戳:', result.map(m => {
      // 安全地处理content，可能不是字符串
      let contentPreview = '';
      if (m.content !== undefined && m.content !== null) {
        if (typeof m.content === 'string') {
          contentPreview = m.content.substring(0, 20) + (m.content.length > 20 ? '...' : '');
        } else {
          contentPreview = JSON.stringify(m.content).substring(0, 20) + '...';
        }
      }
      
      return {
        role: m.role,
        content: contentPreview,
        timestamp: m.timestamp,
        parsed: m.timestamp ? new Date(m.timestamp).toISOString() : 'invalid'
      };
    }));
    
    return result;
  };
  
  // 创建新的消息对象
  const createMessage = (role, content, type = MessageType.TEXT, additionalData = {}, timestamp = null) => {
    // 提取additionalData中的属性，但不包括打字机相关属性
    const { isTyping: additionalIsTyping, displayedContent: additionalDisplayedContent, ...otherAdditionalData } = additionalData;
    
    // 创建基本消息对象
    const message = {
      id: additionalData.id || generateUUID(),
      role,
      content,
      type,
      // 如果提供了时间戳，使用提供的时间戳，否则使用当前时间
      timestamp: timestamp || additionalData.timestamp || new Date().toISOString(),
      visible: true,
      // 助手消息默认启用打字机效果
      isTyping: role === SenderRole.ASSISTANT || additionalIsTyping === true,
      // 助手消息初始显示内容为空，其他消息显示完整内容
      displayedContent: role === SenderRole.ASSISTANT ? '' : content,
    };
    
    // 如果是混合消息，确保数据结构正确
    if (type === MessageType.MIXED && additionalData.attachment) {
      message.data = {
        attachment: additionalData.attachment
      };
    }
    
    // 合并其他附加数据，但不覆盖打字机相关属性
    const result = { ...message, ...otherAdditionalData };
    
    // 打印新创建的消息信息，包括打字机状态
    console.log('创建新消息:', {
      id: result.id.substring(0, 6),
      role: result.role,
      isTyping: result.isTyping,
      displayedContent: result.displayedContent ? '长度:' + result.displayedContent.length : '空',
      content: result.content ? '长度:' + result.content.length : '空'
    });
    
    return result;
  };
  
  // 创建新聊天
  const handleCreateNewChat = () => {
    // 创建新的会话ID
    const newSessionId = generateUUID();
    setSessionId(newSessionId);
    setCurrentConversationId(null);
    
    // 创建时间戳，确保助手消息时间早于系统消息
    const assistantTime = new Date();
    const systemTime = new Date(assistantTime.getTime() + 1000); // 系统消息晚1秒
    
    // 重置消息列表
    const initialMessages = [
      {
        id: generateUUID(),
        role: SenderRole.ASSISTANT,
        content: '你好！我是彩虹城AI，有什么我可以帮你的吗？',
        type: MessageType.TEXT,
        timestamp: assistantTime.toISOString(),
        visible: true,
        isTyping: true,
        displayedContent: '' // 初始为空字符串，将逐字显示
      },
      {
        id: generateUUID(),
        role: SenderRole.SYSTEM,
        content: '你是彩虹城系统的AI助手，专门解答关于彩虹城系统、频率编号和关系管理的问题。',
        type: MessageType.SYSTEM,
        timestamp: systemTime.toISOString(),
        visible: false
      }
    ];
    
    // 应用排序函数确保消息按时间戳排序
    setMessages(sortMessagesByTimestamp(initialMessages));
    
    // 创建新的对话记录
    const newConversation = {
      id: newSessionId,
      title: '新对话 ' + new Date().toLocaleString('zh-CN'),
      preview: '你好！我是彩虹城AI，有什么我可以帮你的吗？',
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
    // 使用全局定义的API_BASE_URL变量
    const token = localStorage.getItem('token');
    
    // 检查token是否存在
    if (!token) {
      console.error('未找到用户认证令牌，请重新登录');
      // 可能需要重定向到登录页
      return;
    }
    
    console.log('获取用户对话列表:', `${API_BASE_URL}/chats`);
    console.log('使用的认证令牌:', `Bearer ${token.substring(0, 10)}...`);
    
    const response = await fetch(`${API_BASE_URL}/chats`, {
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
      throw new Error(`获取对话列表失败: ${response.status}`);
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
      setSessionId(conversationId);
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_BASE_URL}/chats/${conversationId}/messages`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Cache-Control': 'no-cache',
          'Pragma': 'no-cache'
        }
      });
      if (!response.ok) throw new Error(`获取对话消息失败: ${response.status}`);
      const data = await response.json();
      if (data && Array.isArray(data.messages)) {
        // 对于从后端加载的历史消息，我们需要确保它们不会触发打字机效果
        // 创建一个修改版的createMessage函数，强制isTyping为false
        const createHistoricalMessage = (role, content, type, additionalData, timestamp) => {
          const msg = createMessage(role, content, type, additionalData, timestamp);
          // 确保历史消息不会触发打字机效果
          msg.isTyping = false;
          msg.displayedContent = content; // 立即显示完整内容
          return msg;
        };
        
        const processedMessages = data.messages.map(msg => {
          // 首先处理消息内容，确保我们得到纯文本
          let processedContent = msg.content || '';
          
          // 如果是字符串形式的JSON，尝试解析
          if (typeof processedContent === 'string' && 
              ((processedContent.startsWith('{') && processedContent.endsWith('}')) || 
               (processedContent.startsWith('[') && processedContent.endsWith(']')))) {
            try {
              const parsedContent = JSON.parse(processedContent);
              console.log('解析历史消息内容成功:', parsedContent);
              
              // 如果解析成功并包含响应字段
              if (parsedContent && parsedContent.response) {
                processedContent = typeof parsedContent.response === 'string' ? 
                  parsedContent.response : 
                  JSON.stringify(parsedContent.response);
              }
            } catch (e) {
              console.log('历史消息内容不是JSON格式，使用原始字符串');
              // 保持原始内容
            }
          }
          // 如果是对象，提取response或content字段
          else if (typeof processedContent === 'object' && processedContent !== null) {
            if (processedContent.response) {
              processedContent = typeof processedContent.response === 'string' ? 
                processedContent.response : 
                JSON.stringify(processedContent.response);
            } else if (processedContent.content) {
              processedContent = typeof processedContent.content === 'string' ? 
                processedContent.content : 
                JSON.stringify(processedContent.content);
            } else {
              processedContent = JSON.stringify(processedContent);
            }
          }
          
          return createHistoricalMessage(
            msg.role || SenderRole.USER,
            processedContent,
            msg.content_type || msg.type || MessageType.TEXT,
            { id: msg.id || `msg-${Date.now()}-${Math.random()}`, metadata: msg.metadata || {}, visible: true },
            msg.timestamp || msg.created_at || new Date().toISOString()
          );
        });
        
        // 检查是否已经有欢迎消息
        const hasWelcomeMessage = processedMessages.some(msg => 
          msg.role === SenderRole.ASSISTANT && 
          msg.content && 
          typeof msg.content === 'string' &&
          msg.content.includes('你好！我是彩虹城AI')
        );
      
      // 如果没有欢迎消息，添加一个欢迎消息，并设置极早的时间戳
      if (!hasWelcomeMessage && processedMessages.length > 0) {
        // 找到最早的消息时间戳
        let earliestTimestamp = Number.MAX_SAFE_INTEGER;
        processedMessages.forEach(msg => {
          try {
            const msgTime = new Date(msg.timestamp).getTime();
            if (!isNaN(msgTime) && msgTime < earliestTimestamp) {
              earliestTimestamp = msgTime;
            }
          } catch (e) {
            console.error('解析时间戳错误:', e, msg.timestamp);
          }
        });
        
        // 创建比最早消息早一天的欢迎消息，确保它始终在最前面
        const welcomeTimestamp = new Date(earliestTimestamp - 86400000).toISOString(); // 减去24小时
        console.log('欢迎消息时间戳:', welcomeTimestamp, '最早消息时间戳:', new Date(earliestTimestamp).toISOString());
        
        // 使用createHistoricalMessage确保欢迎消息不会触发打字机效果
        const welcomeMessage = createHistoricalMessage(
          SenderRole.ASSISTANT,
          '你好！我是彩虹城AI，有什么我可以帮你的吗？',
          MessageType.TEXT,
          {
            id: `welcome-${Date.now()}`,
            visible: true
          },
          welcomeTimestamp
        );
        
        processedMessages.push(welcomeMessage);
      }
      
      // 如果没有消息，添加一个默认的欢迎消息
      if (processedMessages.length === 0) {
        processedMessages.push(createHistoricalMessage(
          SenderRole.ASSISTANT,
          '你好！我是彩虹城AI，有什么我可以帮你的吗？',
          MessageType.TEXT,
          {
            id: `welcome-${Date.now()}`,
            visible: true
          },
          new Date().toISOString()
        ));
      }
      
      // 打印排序前后的消息顺序，便于调试
      console.log('排序前的消息:', processedMessages.map(m => ({ role: m.role, content: typeof m.content === 'string' ? m.content.substring(0, 20) : 'non-string', timestamp: m.timestamp })));
      const sortedMessages = sortMessagesByTimestamp(processedMessages);
      console.log('排序后的消息:', sortedMessages.map(m => ({ role: m.role, content: typeof m.content === 'string' ? m.content.substring(0, 20) : 'non-string', timestamp: m.timestamp })));
      
      // 按时间戳排序后设置消息
      setMessages(sortedMessages);
      } else {
        console.warn('对话消息数据格式不正确:', data);
        // 设置一个默认消息，不触发打字机效果
        const defaultMessage = createMessage(
          SenderRole.ASSISTANT,
          '你好！我是彩虹城AI，有什么我可以帮你的吗？',
          MessageType.TEXT,
          {
            id: `system-${Date.now()}`,
            visible: true
          },
          new Date().toISOString()
        );
        // 默认消息不需要打字机效果
        // 使用新的打字机状态管理方式，不需要设置isTyping和displayedContent
        
        setMessages([defaultMessage]);
      }
    } catch (error) {
      console.error('选择对话失败:', error);
      setError(error.message || String(error));
      
      // 添加错误消息
      const errorMessage = createMessage(
        SenderRole.SYSTEM,
        `错误: ${error.message || '未知错误'}`,
        MessageType.TEXT,
        { error: true }
      );
      
      setMessages(prev => sortMessagesByTimestamp([...prev, errorMessage]));
      
      // 发送失败时不需要特殊处理附件
      // 附件状态已经在attachments中维护
    } finally {
      setIsLoading(false);
    }
  };
  
  // 根据用户消息生成对话标题
  const generateConversationTitle = (messages) => {
    // 过滤出用户消息
    const userMessages = messages.filter(msg => msg.role === SenderRole.USER);
    
    if (userMessages.length === 0) {
      // 如果没有用户消息，使用默认标题
      const formattedDate = new Date().toLocaleString('zh-CN');
      return `新对话 ${formattedDate}`;
    }
    
    // 获取最新的用户消息
    const latestUserMessage = userMessages[userMessages.length - 1];
    let content = latestUserMessage.content;
    
    // 如果内容是对象，尝试提取文本
    if (typeof content !== 'string') {
      try {
        content = JSON.stringify(content);
      } catch (e) {
        content = '新对话';
      }
    }
    
    // 截取前20个字符作为标题，如果太长就加省略号
    let title = content.trim().substring(0, 20);
    if (content.length > 20) {
      title += '...';
    }
    
    // 添加日期
    const formattedDate = new Date().toLocaleString('zh-CN');
    return `${title} ${formattedDate}`;
  };
  
  // 保存对话到后端
  const saveConversation = async (messageList, conversationId = null) => {
    // 创建消息的深拷贝，以便我们可以修改它们而不影响原始消息
    const messageListCopy = JSON.parse(JSON.stringify(messageList));
    try {
      const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
      const token = localStorage.getItem('token');
      const userId = localStorage.getItem('userId');
      
      if (!token || !userId) {
        console.error('未找到用户认证信息，无法保存对话');
        return null;
      }
      
      // 准备要保存的消息数据
    const messagesToSave = messageListCopy.filter(msg => 
        msg.role !== SenderRole.SYSTEM && msg.visible !== false
      ).map(msg => {
        // 确保content是字符串类型
        let content = msg.content;
        if (content !== null && content !== undefined && typeof content !== 'string') {
          content = JSON.stringify(content);
        }
        return {
          role: msg.role,
          content: content || '',
          type: msg.type,
          timestamp: msg.timestamp
        };
      });
      
      if (messagesToSave.length === 0) {
        console.log('没有可保存的消息');
        return null;
      }
      
      // 确定API端点
      const endpoint = conversationId 
        ? `${API_BASE_URL}/chats/${conversationId}/messages` 
        : `${API_BASE_URL}/chats`;
      
      console.log('保存对话到:', endpoint);
      console.log('保存的消息数量:', messagesToSave.length);
      
      // 准备请求数据
      let requestData;
      
      if (conversationId) {
        // 如果是向现有对话添加消息，只发送最新的一条消息
        if (messagesToSave.length > 0) {
          // 取最新的一条消息，并确保包含必需的role和content字段
          const latestMessage = messagesToSave[messagesToSave.length - 1];
          
          // 确保content是字符串类型
          let content = latestMessage.content;
          if (content !== null && content !== undefined && typeof content !== 'string') {
            content = JSON.stringify(content);
          }
          
          requestData = {
            role: latestMessage.role,
            content: content || '',
            type: latestMessage.type || 'text'
          };
          
          // 如果有时间戳，也包含进去
          if (latestMessage.timestamp) {
            requestData.timestamp = latestMessage.timestamp;
          }
          
          // 如果是用户消息，更新对话标题
          if (latestMessage.role === SenderRole.USER) {
            // 生成新标题
            const newTitle = generateConversationTitle([...messageList]);
            requestData.title = newTitle;
          }
          
          console.log('发送单条消息到现有对话:', requestData);
        } else {
          console.log('没有消息可发送');
          return null;
        }
      } else {
        // 如果是创建新对话，发送全部消息
        // 使用生成的标题
        const title = generateConversationTitle(messageList);
        requestData = { 
          title: title,
          messages: messagesToSave
        };
        console.log('创建新对话并发送所有消息:', requestData);
      }
      
      // 发送请求
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(requestData)
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('对话保存成功:', data);
        
        // 如果是新创建的对话，将其添加到侧边栏列表中
        if (!conversationId && data.chat) {
          const newConversation = {
            id: data.chat.id,
            title: data.chat.title || `对话 ${new Date().toLocaleString('zh-CN')}`,
            preview: messagesToSave.length > 0 ? 
              (typeof messagesToSave[0].content === 'string' ? messagesToSave[0].content.substring(0, 30) + '...' : JSON.stringify(messagesToSave[0].content).substring(0, 30) + '...') : 
              '新对话',
            lastUpdated: new Date().toISOString(),
            messages: sortMessagesByTimestamp(messageList) // 确保消息按时间戳排序
          };
          
          // 更新对话列表状态
          setConversations(prev => {
            // 删除之前可能添加的临时对话
            const filteredPrev = prev.filter(conv => conv.id !== sessionId);
            return [newConversation, ...filteredPrev];
          });
          
          // 更新当前会话ID
          setSessionId(data.chat.id);
          setCurrentConversationId(data.chat.id);
          
          console.log('新对话已添加到侧边栏:', newConversation);
          
          // 确保消息列表也按时间戳排序
          setMessages(sortMessagesByTimestamp(messageList));
        } 
        // 如果是更新现有对话，更新侧边栏中的对话预览
        else if (conversationId && messagesToSave.length > 0) {
          const latestMessage = messagesToSave[messagesToSave.length - 1];
          
          setConversations(prev => prev.map(conv => {
            if (conv.id === conversationId) {
              // 更新对话预览和时间
              const updates = {
                preview: typeof latestMessage.content === 'string' ? latestMessage.content.substring(0, 30) + '...' : JSON.stringify(latestMessage.content).substring(0, 30) + '...',
                lastUpdated: new Date().toISOString(),
                messages: sortMessagesByTimestamp(messageList) // 确保消息按时间戳排序
              };
              
              // 如果响应中包含新标题，也更新标题
              if (data.title) {
                updates.title = data.title;
              } else if (latestMessage.role === SenderRole.USER) {
                // 如果是用户消息且服务器没有返回新标题，尝试生成一个
                const allMessages = [...prev.find(c => c.id === conversationId).messages || [], latestMessage];
                updates.title = generateConversationTitle(allMessages);
              }
              
              return {
                ...conv,
                ...updates
              };
            }
            return conv;
          }));
          
          console.log('侧边栏对话已更新:', conversationId);
        }
        
        return data.chat?.id || data.id;
      } else {
        const errorData = await response.json().catch(() => ({}));
        console.error('保存对话失败:', response.status, errorData);
        return null;
      }
    } catch (error) {
      console.error('保存对话时发生错误:', error);
      return null;
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
    
    // 确保每条消息都有时间戳
    const messagesWithTimestamp = userMessages.map(msg => {
      if (!msg.timestamp) {
        return {
          ...msg,
          timestamp: new Date().toISOString()
        };
      }
      return msg;
    });
    
    // 添加到消息列表并排序
    setMessages(prev => sortMessagesByTimestamp([...prev, ...messagesWithTimestamp]));
    console.log('添加用户消息后的消息列表:', messagesWithTimestamp);
    setTextInput('');
    setAttachments([]);
    setIsLoading(true);
    
    // 如果是新对话（没有currentConversationId），立即更新侧边栏
    if (!currentConversationId && isLoggedIn) {
      // 创建一个临时对话项，显示在侧边栏中
      const tempConversation = {
        id: sessionId, // 使用当前会话ID
        title: generateConversationTitle(sortMessagesByTimestamp([...messages, ...userMessages])),
        preview: typeof messageContent === 'string' ? messageContent.substring(0, 30) + (messageContent.length > 30 ? '...' : '') : JSON.stringify(messageContent).substring(0, 30) + '...',
        lastUpdated: new Date().toISOString(),
        messages: []
      };
      
      // 立即更新对话列表，不等待API响应
      setConversations(prev => [tempConversation, ...prev]);
    }
    setError(null);
    
    try {
      // 准备请求数据
      // 使用函数形式获取最新的messages状态
      let allMessages = [];
      // 深拷贝当前消息列表，避免引用问题
      allMessages = JSON.parse(JSON.stringify(messages));
      // 确保消息按时间戳排序
      allMessages = sortMessagesByTimestamp(allMessages);
      
      // 限制发送给后端的消息历史数量，只发送最近的消息和系统消息
      const visibleMessages = allMessages
        .filter(msg => msg.visible || msg.role === SenderRole.SYSTEM)
        // 只保留系统消息和最近的4条消息（不包括当前用户消息）
        .filter((msg, index, array) => {
          // 始终保留系统消息
          if (msg.role === SenderRole.SYSTEM) return true;
          // 计算非系统消息的位置
          const nonSystemMessages = array.filter(m => m.role !== SenderRole.SYSTEM);
          const msgIndex = nonSystemMessages.indexOf(msg);
          // 只保留最近的4条非系统消息
          return msgIndex >= nonSystemMessages.length - 4;
        })
        .concat(userMessages)
        .map(msg => ({
          role: msg.role,
          content: msg.content,
          type: msg.type
        }));
      
      console.log('发送给后端的消息数量:', visibleMessages.length);
      
      // 决定使用哪个聊天端点
      // 使用完整的API URL
      const chatEndpoint = `${API_BASE_URL}${useAgentChat ? '/chat-agent' : '/chat'}`;
      console.log('使用API端点:', chatEndpoint);
      console.log('API_BASE_URL:', API_BASE_URL);
      console.log('环境变量REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
      
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
        
        // 获取token
        const token = localStorage.getItem('token');
        
        // 准备请求头
        const headers = {};
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        // 使用新的统一文件处理端点，带完整API URL
        response = await fetch(`${API_BASE_URL}/chat-agent/with_file`, {
          method: 'POST',
          headers: headers,
          body: formData
        });
      } 
      // 否则使用标准JSON请求
      else {
        // 创建AbortController用于超时处理
        const controller = new AbortController();
        // 增加超时时间到60秒，给后端更多处理时间
        const timeoutId = setTimeout(() => {
          console.log('请求超时，正在中止...');
          controller.abort();
        }, 60000); // 60秒超时
        
        try {
          // 获取用户信息
          const token = localStorage.getItem('token');
          const userId = localStorage.getItem('userId') || 'anonymous';
          
          // 调试日志：显示请求详情
          console.log('发送聊天请求到:', chatEndpoint);
          console.log('用户登录状态:', token ? '已登录' : '未登录');
          console.log('请求头:', {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          });
          
          const requestBody = {
            session_id: sessionId,
            turn_id: newTurnId,
            messages: visibleMessages,
            user_id: userId,
            ai_id: 'ai_rainbow_city'
          };
          console.log('请求体:', JSON.stringify(requestBody));
          console.log('请求体大小:', JSON.stringify(requestBody).length, '字节');
          console.log('消息数量:', visibleMessages.length);
          
          // 准备请求头
          const headers = {
            'Content-Type': 'application/json'
          };
          
          // 只有当token存在时才添加Authorization头
          if (token) {
            headers['Authorization'] = `Bearer ${token}`;
          }
          
          response = await fetch(chatEndpoint, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(requestBody),
            signal: controller.signal
          });
          
          clearTimeout(timeoutId); // 请求成功后清除超时
        } catch (error) {
          if (error.name === 'AbortError') {
            throw new Error('请求超时（30秒）：服务器响应时间过长。可能原因：\n1. 数据库查询阻塞\n2. 服务器负载过高\n3. 网络连接问题\n\n请稍后重试，或联系管理员查看服务器日志。');
          }
          throw error;
        }
      }
      
      // 调试日志：显示响应状态
      console.log('收到响应状态码:', response.status);
      console.log('响应头:', [...response.headers.entries()]);
      
      // 打印响应类型信息
      console.log('响应类型:', response.type);
      console.log('响应URL:', response.url);
      console.log('响应重定向状态:', response.redirected);
      
      if (!response.ok) {
        console.error(`服务器错误状态码: ${response.status}`);
        const errorText = await response.text();
        console.error('错误响应内容:', errorText);
        
        // 根据状态码提供更具体的错误信息
        let errorMessage = '';
        switch(response.status) {
          case 400:
            errorMessage = `请求格式错误: ${errorText}`;
            break;
          case 401:
            errorMessage = '认证失败：请重新登录';
            break;
          case 403:
            errorMessage = '权限不足：无法访问此资源';
            break;
          case 404:
            errorMessage = '请求的资源不存在';
            break;
          case 408:
            errorMessage = '服务器请求超时：数据库查询可能耗时过长';
            break;
          case 500:
            errorMessage = `服务器内部错误: ${errorText.includes('database') ? '数据库操作失败' : '服务器处理异常'}`;
            break;
          case 503:
            errorMessage = '服务暂时不可用：服务器可能正在维护或过载';
            break;
          default:
            errorMessage = `服务器错误: ${response.status} - ${errorText}`;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      console.log('响应数据:', data);
      
      // 处理响应
      if (data.response) {
        // 如果响应中包含记忆上下文数据
        if (data.memory_context) {
          if (data.memory_context.user_memories) {
            setUserMemories(data.memory_context.user_memories);
          }
          if (data.memory_context.session_summary) {
            setSessionSummary(data.memory_context.session_summary);
          }
        }
        
        // 创建助手消息
        // 处理响应数据，确保我们得到纯文本内容
        let responseContent = '';
        let responseType = MessageType.TEXT;
        let responseMetadata = {};
        
        console.log('原始响应数据类型:', typeof data.response);
        console.log('原始响应数据:', data.response);
        
        // 处理字符串响应
        if (typeof data.response === 'string') {
          try {
            // 尝试解析JSON字符串
            const parsedResponse = JSON.parse(data.response);
            console.log('解析响应字符串成功:', parsedResponse);
            
            // 如果解析成功并包含响应字段
            if (parsedResponse && parsedResponse.response) {
              responseContent = typeof parsedResponse.response === 'string' ? 
                parsedResponse.response : 
                JSON.stringify(parsedResponse.response);
            } else {
              // 如果没有response字段，使用整个解析后的对象
              responseContent = JSON.stringify(parsedResponse);
            }
          } catch (e) {
            // 如果不是JSON，直接使用原始字符串
            console.log('响应不是JSON格式，使用原始字符串');
            responseContent = data.response;
          }
        } 
        // 处理对象响应
        else if (typeof data.response === 'object') {
          console.log('响应是对象类型:', data.response);
          
          // 如果对象有response字段
          if (data.response.response) {
            responseContent = typeof data.response.response === 'string' ? 
              data.response.response : 
              JSON.stringify(data.response.response);
          }
          // 如果对象有content字段
          else if (data.response.content) {
            responseContent = typeof data.response.content === 'string' ? 
              data.response.content : 
              JSON.stringify(data.response.content);
          } 
          // 如果都没有，将整个对象转换为字符串
          else {
            responseContent = JSON.stringify(data.response);
          }
          
          // 获取其他元数据
          responseType = data.response.type || MessageType.TEXT;
          responseMetadata = data.response.metadata || {};
        }
        
        console.log('处理后的响应内容:', responseContent);
        
        // 创建助手消息
        const assistantMessage = {
          id: generateUUID(),
          role: SenderRole.ASSISTANT,
          content: responseContent,
          type: responseType,
          timestamp: new Date().toISOString(),
          visible: true,             // 确保消息可见
          ...responseMetadata
        };
        
        // 将新消息添加到打字机状态中
        setTypingState(prev => ({
          ...prev,
          [assistantMessage.id]: {
            isTyping: true,
            displayedContent: '',
            fullContent: typeof responseContent === 'string' ? 
              responseContent : 
              JSON.stringify(responseContent)
          }
        }));
        
        console.log('创建的AI消息已添加到打字机状态:', {
          id: assistantMessage.id,
          content: typeof responseContent === 'string' ? 
            responseContent.substring(0, 20) + '...' : 
            'non-string content'
        });
        
        console.log('创建的AI消息状态:', {
          id: assistantMessage.id,
          isTyping: assistantMessage.isTyping,
          displayedContent: assistantMessage.displayedContent ? '空' : '空字符串',
          contentLength: assistantMessage.content ? assistantMessage.content.length : 0
        });
        
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
          const toolMessage = createMessage(
            SenderRole.SYSTEM,
            `正在使用工具: ${data.tool_calls.map(t => t.name).join(', ')}`,
            MessageType.TOOL_OUTPUT,
            { 
              tool_calls: data.tool_calls,
              visible: true // 确保消息可见
            }
          );
          
          // 系统消息不需要打字机效果
          // 使用新的打字机状态管理方式，不需要设置isTyping和displayedContent
          
          // 使用回调函数形式更新消息，确保基于最新的状态
          setMessages(prevMessages => {
            // 添加新消息，不使用排序以避免状态丢失
            const updatedMessages = [...prevMessages, assistantMessage, toolMessage];
              
            // 打印添加消息后的状态
            console.log('添加AI消息后状态:', updatedMessages.filter(m => m.id === assistantMessage.id).map(m => ({
              id: m.id.substring(0, 6),
              isTyping: m.isTyping,
              displayedContent: m.displayedContent === '' ? '空字符串' : m.displayedContent,
              contentLength: m.content ? m.content.length : 0
            })));
            
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
            // 添加新消息，不使用排序以避免状态丢失
            const updatedMessages = [...prevMessages, assistantMessage];
              
            // 打印添加消息后的状态
            console.log('添加AI消息后状态:', updatedMessages.filter(m => m.id === assistantMessage.id).map(m => ({
              id: m.id.substring(0, 6),
              isTyping: m.isTyping,
              displayedContent: m.displayedContent === '' ? '空字符串' : m.displayedContent,
              contentLength: m.content ? m.content.length : 0
            })));
            
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
      let errorContent = err.message || '未知错误';
      
      // 增强错误消息的可读性和可操作性
      if (errorContent.includes('请求超时')) {
        // 超时错误已经在上面的catch块中格式化过了
      } else if (errorContent.includes('数据库')) {
        errorContent = `数据库操作错误: ${errorContent}\n建议: 请稍后重试，或联系管理员检查数据库状态。`;
      } else if (errorContent.includes('认证失败') || errorContent.includes('权限不足')) {
        errorContent = `${errorContent}\n建议: 请尝试重新登录。`;
      } else if (errorContent.includes('服务器内部错误')) {
        errorContent = `${errorContent}\n建议: 请联系管理员查看服务器日志。`;
      }
      
      // 添加错误消息到聊天界面并按时间戳排序
      setMessages(prevMessages => sortMessagesByTimestamp([
        ...prevMessages,
        {
          id: generateUUID(),
          role: SenderRole.ASSISTANT,
          content: errorContent,
          timestamp: new Date().toISOString(),
          error: true
        }
      ]));
    }
  }
  
  // 处理工具操作
  const handleToolAction = (toolId, action) => {
    console.log(`处理工具操作: ${action} 工具ID: ${toolId}`);
    // 根据工具ID和操作类型执行相应的操作
    if (action === 'navigate') {
      // 这里可以添加导航到工具页面的逻辑
      // 例如: navigate(`/tools/${toolId}`);
    }
  };
  
  // 渲染消息内容
  // 提取消息内容中的response字段
const extractResponseContent = (content) => {
  // 处理null或undefined
  if (content === null || content === undefined) {
    return '';
  }
  
  // 处理对象类型
  if (typeof content === 'object') {
    console.log('处理对象类型的消息:', content);
    
    // 先检查response字段
    if (content.response) {
      if (typeof content.response === 'string') {
        return content.response;
      } else if (typeof content.response === 'object' && content.response.content) {
        return typeof content.response.content === 'string' ?
          content.response.content : JSON.stringify(content.response.content);
      } else {
        return JSON.stringify(content.response);
      }
    } else if (content.content) {
      return typeof content.content === 'string' ?
        content.content : JSON.stringify(content.content);
    } else {
      // 如果没有这些字段，尝试转换为JSON字符串
      try {
        return JSON.stringify(content, null, 2);
      } catch (e) {
        return '[无法显示的内容类型]';
      }
    }
  }
  
  // 处理字符串类型，检查是否是JSON字符串
  if (typeof content === 'string') {
    if ((content.startsWith('{') && content.endsWith('}')) || 
        (content.startsWith('[') && content.endsWith(']'))) {
      try {
        const parsedContent = JSON.parse(content);
        console.log('解析消息内容成功:', parsedContent);
        
        // 处理各种可能的字段
        if (parsedContent && parsedContent.response) {
          if (typeof parsedContent.response === 'string') {
            return parsedContent.response;
          } else if (typeof parsedContent.response === 'object') {
            if (parsedContent.response.content) {
              return typeof parsedContent.response.content === 'string' ?
                parsedContent.response.content :
                JSON.stringify(parsedContent.response.content);
            } else {
              return JSON.stringify(parsedContent.response);
            }
          }
        } else if (parsedContent && parsedContent.content) {
          return typeof parsedContent.content === 'string' ?
            parsedContent.content :
            JSON.stringify(parsedContent.content);
        }
        // 如果没有这些字段，保持原始字符串
        return content;
      } catch (e) {
        // 如果解析失败，使用原始字符串
        console.log('消息内容不是JSON格式或解析失败:', e);
        return content;
      }
    }
    return content;
  }
  
  // 其他类型转换为字符串
  return String(content);
};

const renderMessageContent = (message) => {
    // 检查消息是否在打字机状态中
    const messageTypingState = typingState[message.id];
    const isTypingMessage = messageTypingState && messageTypingState.isTyping;
    
    // 调试：打印消息渲染状态
    if (message.role === SenderRole.ASSISTANT) {
      console.log('渲染AI消息:', {
        id: message.id.substring(0, 6),
        hasTypingState: !!messageTypingState,
        isTyping: isTypingMessage,
        content: message.content ? (typeof message.content === 'string' ? message.content.substring(0, 20) + '...' : 'non-string') : 'empty',
        displayedContent: messageTypingState ? messageTypingState.displayedContent.substring(0, 20) + '...' : 'no typing state'
      });
    }
    
    // 准备要显示的内容，如果在打字中则使用typingState中的displayedContent
    let contentToShow = '';
    
    try {
      // 如果消息在打字中，使用打字机状态中的内容
      if (isTypingMessage && messageTypingState && messageTypingState.displayedContent) {
        contentToShow = messageTypingState.displayedContent;
      } 
      // 否则使用消息的完整内容，并提取response字段
      else if (message && message.content) {
        contentToShow = extractResponseContent(message.content);
      }
      
      // 确保contentToShow始终是字符串
      if (contentToShow === null || contentToShow === undefined) {
        contentToShow = '';
      } else if (typeof contentToShow !== 'string') {
        contentToShow = String(contentToShow);
      }
    } catch (error) {
      console.error('渲染消息内容时出错:', error);
      contentToShow = '[消息内容渲染错误]';
    }
    
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
        // 确保文本消息正确渲染，处理换行符
        return (
          <div className="message-content">
            {contentToShow && contentToShow.split('\n').map((line, i) => {
              // 处理长行，确保每一行都能正确换行显示
              return (
                <p key={i} style={{ 
                  margin: '0 0 0.5em 0',
                  maxWidth: '100%',
                  overflowWrap: 'break-word',
                  wordBreak: 'break-word'
                }}>
                  {line || ' '}
                </p>
              );
            })}
            {(!contentToShow || contentToShow.trim() === '') && (
              <p>[空消息]</p>
            )}
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
      <div className="chat-main-container">
        {/* 记忆上下文组件 */}
        <MemoryContext 
          memories={userMemories} 
          sessionSummary={sessionSummary} 
          isVisible={showMemoryContext && (userMemories.length > 0 || sessionSummary !== null)}
        />
        
        {/* 聊天消息区域 */}
        <div className="chat-messages" ref={messagesEndRef}>
          {(() => {
            // 首先按时间戳排序
            const sortedMessages = sortMessagesByTimestamp(messages).filter(message => message.visible);
            
            // 找出欢迎消息
            let welcomeMessage = null;
            let otherMessages = [];
            
            // 分离欢迎消息和其他消息
            sortedMessages.forEach(msg => {
              if (msg.role === SenderRole.ASSISTANT && 
                  typeof msg.content === 'string' && 
                  msg.content.includes('你好！我是彩虹城AI')) {
                welcomeMessage = msg;
              } else {
                otherMessages.push(msg);
              }
            });
            
            // 如果没有欢迎消息，创建一个
            if (!welcomeMessage) {
              welcomeMessage = {
                id: `welcome-${Date.now()}`,
                role: SenderRole.ASSISTANT,
                content: '你好！我是彩虹城AI，有什么我可以帮你的吗？',
                type: MessageType.TEXT,
                timestamp: new Date(0).toISOString(), // 使用最早的时间戳
                visible: true
              };
            }
            
            // 将其他消息按照用户和AI交替的方式分组
            const userMessages = otherMessages.filter(m => m.role === SenderRole.USER);
            const assistantMessages = otherMessages.filter(m => m.role === SenderRole.ASSISTANT);
            const systemMessages = otherMessages.filter(m => m.role === SenderRole.SYSTEM);
            
            // 创建问答对
            const qaGroups = [];
            
            // 先将所有消息按时间戳排序
            const allSortedMessages = [...userMessages, ...assistantMessages].sort((a, b) => {
              // 安全地解析时间戳
              let timeA = 0;
              let timeB = 0;
              
              try {
                timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
                if (isNaN(timeA)) timeA = 0;
              } catch (e) {
                console.error('无法解析时间戳A:', a.timestamp, e);
              }
              
              try {
                timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
                if (isNaN(timeB)) timeB = 0;
              } catch (e) {
                console.error('无法解析时间戳B:', b.timestamp, e);
              }
              
              // 升序排列，早的在前，晚的在后
              return timeA - timeB;
            });
            
            // 调试日志，显示所有消息的时间戳
            console.log('消息排序后的时间戳:', allSortedMessages.map(m => ({
              id: m.id,
              role: m.role,
              timestamp: m.timestamp,
              parsed: m.timestamp ? new Date(m.timestamp).toISOString() : 'invalid'
            })));
            
            // 创建一个映射来跟踪已使用的消息
            const usedMessages = new Set();
            
            // 处理所有消息，尝试匹配问答对
            for (let i = 0; i < allSortedMessages.length; i++) {
              const currentMsg = allSortedMessages[i];
              
              // 如果消息已经被使用，跳过
              if (usedMessages.has(currentMsg.id)) continue;
              
              // 标记消息为已使用
              usedMessages.add(currentMsg.id);
              
              if (currentMsg.role === SenderRole.USER) {
                // 如果是用户消息，尝试找到下一条助手消息
                let foundAssistant = false;
                
                // 向前查找下一条助手消息
                for (let j = i + 1; j < allSortedMessages.length; j++) {
                  const nextMsg = allSortedMessages[j];
                  if (nextMsg.role === SenderRole.ASSISTANT && !usedMessages.has(nextMsg.id)) {
                    // 创建问答对
                    qaGroups.push({ user: currentMsg, assistant: nextMsg });
                    usedMessages.add(nextMsg.id);
                    foundAssistant = true;
                    break;
                  }
                }
                
                // 如果没有找到匹配的助手消息
                if (!foundAssistant) {
                  qaGroups.push({ user: currentMsg });
                }
              } else if (currentMsg.role === SenderRole.ASSISTANT) {
                // 如果是助手消息，尝试找到前一条用户消息
                let foundUser = false;
                
                // 向后查找前一条用户消息
                for (let j = i - 1; j >= 0; j--) {
                  const prevMsg = allSortedMessages[j];
                  if (prevMsg.role === SenderRole.USER && !usedMessages.has(prevMsg.id)) {
                    // 创建问答对
                    qaGroups.push({ user: prevMsg, assistant: currentMsg });
                    usedMessages.add(prevMsg.id);
                    foundUser = true;
                    break;
                  }
                }
                
                // 如果没有找到匹配的用户消息
                if (!foundUser) {
                  qaGroups.push({ assistant: currentMsg });
                }
              }
            }
            
            // 按时间戳对问答对进行排序
            qaGroups.sort((a, b) => {
              // 安全地获取时间戳
              let timeA = 0;
              let timeB = 0;
              
              try {
                if (a.user && a.user.timestamp) {
                  timeA = new Date(a.user.timestamp).getTime();
                  if (isNaN(timeA)) timeA = 0;
                } else if (a.assistant && a.assistant.timestamp) {
                  timeA = new Date(a.assistant.timestamp).getTime();
                  if (isNaN(timeA)) timeA = 0;
                }
              } catch (e) {
                console.error('无法解析问答对时间戳A:', a, e);
              }
              
              try {
                if (b.user && b.user.timestamp) {
                  timeB = new Date(b.user.timestamp).getTime();
                  if (isNaN(timeB)) timeB = 0;
                } else if (b.assistant && b.assistant.timestamp) {
                  timeB = new Date(b.assistant.timestamp).getTime();
                  if (isNaN(timeB)) timeB = 0;
                }
              } catch (e) {
                console.error('无法解析问答对时间戳B:', b, e);
              }
              
              // 升序排列，早的在前，晚的在后
              return timeA - timeB;
            });
            
            // 调试日志，显示问答对排序结果
            console.log('问答对排序后:', qaGroups.map(g => ({
              user: g.user ? { id: g.user.id, timestamp: g.user.timestamp } : null,
              assistant: g.assistant ? { id: g.assistant.id, timestamp: g.assistant.timestamp } : null
            })));
            
            // 处理重复的问答对
            const uniqueGroups = [];
            const seenUserIds = new Set();
            const seenAssistantIds = new Set();
            
            for (const group of qaGroups) {
              let shouldAdd = true;
              
              if (group.user && seenUserIds.has(group.user.id)) {
                shouldAdd = false;
              }
              
              if (group.assistant && seenAssistantIds.has(group.assistant.id)) {
                shouldAdd = false;
              }
              
              if (shouldAdd) {
                if (group.user) seenUserIds.add(group.user.id);
                if (group.assistant) seenAssistantIds.add(group.assistant.id);
                uniqueGroups.push(group);
              }
            }
            
            // 使用去重后的问答对
            const finalGroups = uniqueGroups;
            
            // 再次按时间戳对最终问答对进行排序，确保顺序正确
            finalGroups.sort((a, b) => {
              // 安全地获取时间戳
              let timeA = 0;
              let timeB = 0;
              
              try {
                if (a.user && a.user.timestamp) {
                  timeA = new Date(a.user.timestamp).getTime();
                  if (isNaN(timeA)) timeA = 0;
                } else if (a.assistant && a.assistant.timestamp) {
                  timeA = new Date(a.assistant.timestamp).getTime();
                  if (isNaN(timeA)) timeA = 0;
                }
              } catch (e) {
                console.error('无法解析最终问答对时间戳A:', a, e);
              }
              
              try {
                if (b.user && b.user.timestamp) {
                  timeB = new Date(b.user.timestamp).getTime();
                  if (isNaN(timeB)) timeB = 0;
                } else if (b.assistant && b.assistant.timestamp) {
                  timeB = new Date(b.assistant.timestamp).getTime();
                  if (isNaN(timeB)) timeB = 0;
                }
              } catch (e) {
                console.error('无法解析最终问答对时间戳B:', b, e);
              }
              
              // 升序排列，早的在前，晚的在后
              return timeA - timeB;
            });
            
            // 渲染消息列表
            return (
              <div className="seamless-messages-container">
                {/* 欢迎消息 */}
                <div className="message-wrapper assistant-message">
                  <div className="message">
                    {renderMessageContent(welcomeMessage)}
                  </div>
                </div>
                
                {/* 渲染问答对 */}
                {finalGroups.map((group, index) => (
                  <React.Fragment key={`qa-group-${index}`}>
                    {group.user && (
                      <div className="message-wrapper user-message">
                        <div className="message">
                          {renderMessageContent(group.user)}
                        </div>
                      </div>
                    )}
                    {group.assistant && (
                      <div className="message-wrapper assistant-message">
                        <div className="message">
                          {renderMessageContent(group.assistant)}
                        </div>
                        {group.assistant.isTyping && (
                          <div className="thinking">
                            <div className="thinking-dots">
                              <span></span>
                              <span></span>
                              <span></span>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            );
          })()}
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
              disabled={isLoading || (textInput.trim() === '' && attachments.length === 0)}
              className="send-button"
            >
              <i className="send-icon"></i>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AiChat;
