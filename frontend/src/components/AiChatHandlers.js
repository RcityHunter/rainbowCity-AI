import axios from 'axios';
import { API_CONFIG, fetchWithTimeout, sendChatRequest } from './AiChatConfig';

// 导出生成UUID函数
export function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0, v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

// 检查登录状态
export const checkLoginStatus = ({ setIsLoggedIn, setUser }) => {
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');
  
  if (token && userId) {
    setIsLoggedIn(true);
    setUser({
      id: userId,
      name: localStorage.getItem('userName') || '用户'
    });
  } else {
    setIsLoggedIn(false);
    setUser(null);
  }
};

// 获取用户对话历史
export const fetchUserConversations = async ({ 
  setIsLoadingConversations, setConversations, setError, setCurrentConversationId, setSessionId, setMessages, navigate
}) => {
  setIsLoadingConversations(true);
  
  try {
    // 获取用户令牌
    const token = localStorage.getItem('token');
    if (!token) {
      console.error('[ERROR] 获取对话历史失败: 未登录或令牌不存在');
      throw new Error('未登录或会话已过期，请重新登录');
    }
    
    console.log('[DEBUG] 开始获取对话历史，令牌长度:', token.length);
    
    // 使用API_CONFIG中的getFullUrl函数获取完整URL
    const endpoint = API_CONFIG.getFullUrl(API_CONFIG.ENDPOINTS.CONVERSATIONS);
    console.log('[DEBUG] 请求对话历史端点:', endpoint);
    
    // 添加随机查询参数避免浏览器缓存
    const cacheBuster = `_t=${Date.now()}`;
    const finalEndpoint = endpoint.includes('?') ? `${endpoint}&${cacheBuster}` : `${endpoint}?${cacheBuster}`;
    
    const response = await fetch(finalEndpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache'
      }
    });
    
    console.log('[DEBUG] 对话历史响应状态:', response.status);
    
    if (!response.ok) {
      if (response.status === 404) {
        console.error('[ERROR] 获取对话历史失败: API端点不存在');
        throw new Error('对话历史API端点不存在，请联系管理员');
      } else if (response.status === 401) {
        console.error('[ERROR] 获取对话历史失败: 未授权或令牌已过期');
        throw new Error('登录已过期，请重新登录');
      } else {
        console.error('[ERROR] 获取对话历史失败:', response.status);
        throw new Error(`获取对话历史失败: ${response.status}`);
      }
    }
    
    const data = await response.json();
    console.log('[DEBUG] 成功获取对话历史:', data);
    const conversations = data.conversations || [];
    
    // 检查是否有对话历史
    if (conversations.length === 0) {
      console.log('[DEBUG] 没有找到对话历史');
    } else {
      console.log('[DEBUG] 找到', conversations.length, '个对话');
      conversations.forEach((conv, index) => {
        console.log(`[DEBUG] 对话${index + 1}: ID=${conv.id}, 标题=${conv.title}, 时间=${conv.last_updated || conv.created_at}`);
      });
    }
    
    // 更新对话列表
    setConversations(conversations);
    
    // 如果有对话历史，自动连接到最近的对话
    if (conversations.length > 0) {
      // 按时间排序，获取最近的对话
      const sortedConversations = [...conversations].sort((a, b) => {
        const dateA = new Date(a.last_updated || a.created_at || 0);
        const dateB = new Date(b.last_updated || b.created_at || 0);
        return dateB - dateA;
      });
      
      const mostRecentConversation = sortedConversations[0];
      console.log('[DEBUG] 自动连接到最近对话:', mostRecentConversation.id, '标题:', mostRecentConversation.title);
      
      // 设置当前对话ID和会话ID
      setCurrentConversationId(mostRecentConversation.id);
      setSessionId(mostRecentConversation.session_id || mostRecentConversation.id);
      
      // 加载对话内容
      if (navigate) {
        navigate(`/chat/${mostRecentConversation.id}`);
      }
      
      // 获取对话内容并加载到聊天窗口
      try {
        const conversationEndpoint = API_CONFIG.getFullUrl(`${API_CONFIG.ENDPOINTS.CONVERSATIONS}/${mostRecentConversation.id}`);
        const conversationResponse = await fetch(conversationEndpoint, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (conversationResponse.ok) {
          const conversationData = await conversationResponse.json();
          console.log('[DEBUG] 成功加载对话内容:', conversationData);
          
          // 设置消息历史
          if (conversationData.conversation && conversationData.conversation.messages) {
            setMessages(conversationData.conversation.messages);
          }
        } else {
          console.error('[ERROR] 加载对话内容失败:', conversationResponse.status);
        }
      } catch (convErr) {
        console.error('[ERROR] 获取对话内容时出错:', convErr);
      }
    } else {
      console.log('[DEBUG] 无历史对话，等待用户发送第一条消息');
    }
  } catch (err) {
    console.error('[ERROR] 获取对话历史时出错:', err);
    setError(`无法加载对话历史: ${err.message}`);
    setConversations([]);
  } finally {
    setIsLoadingConversations(false);
  }
};

// 保存对话
export const saveConversation = async (messages, conversationId = null) => {
  try {
    // 过滤掉系统消息和不可见消息
    const visibleMessages = messages.filter(msg => msg.visible !== false);
    
    // 提取对话标题（使用第一条用户消息作为标题）
    const firstUserMessage = visibleMessages.find(msg => msg.role === 'user');
    const title = firstUserMessage ? 
      (firstUserMessage.content.length > 30 ? 
        firstUserMessage.content.substring(0, 30) + '...' : 
        firstUserMessage.content) : 
      '新对话';
    
    const requestBody = {
      title,
      messages: visibleMessages,
      user_id: localStorage.getItem('userId')
    };
    
    // 如果有对话ID，则更新现有对话
    const url = conversationId ? 
      `/api/conversations/${conversationId}` : 
      '/api/conversations';
    
    const method = conversationId ? 'PUT' : 'POST';
    
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
      throw new Error(`保存对话失败: ${response.status}`);
    }
    
    const data = await response.json();
    return data.id; // 返回对话ID
  } catch (err) {
    console.error('保存对话时出错:', err);
    throw err;
  }
};

// 选择对话
export const handleSelectConversation = async (conversationId, {
  setIsLoading, setError, setCurrentConversationId, setMessages, setSessionId,
  navigate, generateUUID
}) => {
  if (!conversationId) return;
  
  console.log('[DEBUG] 选择对话:', conversationId);
  setIsLoading(true);
  setError(null);
  
  try {
    // 设置当前对话ID
    setCurrentConversationId(conversationId);
    
    // 清空当前消息，确保对话隔离
    setMessages([]);
    
    // 获取对话内容
    const token = localStorage.getItem('token');
    if (!token) {
      throw new Error('未登录或会话已过期，请重新登录');
    }
    
    // 使用API_CONFIG中的getFullUrl函数获取完整URL
    const endpoint = API_CONFIG.getFullUrl(`${API_CONFIG.ENDPOINTS.CONVERSATIONS}/${conversationId}`);
    console.log('[DEBUG] 请求对话内容端点:', endpoint);
    
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    });
    
    if (!response.ok) {
      throw new Error(`获取对话内容失败: ${response.status}`);
    }
    
    const data = await response.json();
    console.log('[DEBUG] 成功获取对话内容:', data);
    
    // 设置会话ID
    if (data.conversation && data.conversation.session_id) {
      setSessionId(data.conversation.session_id);
    } else if (data.session_id) {
      setSessionId(data.session_id);
    } else {
      // 如果没有会话ID，使用对话ID作为会话ID
      setSessionId(conversationId);
    }
    
    // 设置消息历史
    if (data.conversation && data.conversation.messages) {
      setMessages(data.conversation.messages);
    } else if (data.messages && Array.isArray(data.messages)) {
      setMessages(data.messages);
    } else {
      // 如果没有消息，显示默认消息
      setMessages([{
        id: generateUUID ? generateUUID() : Date.now().toString(),
        role: 'assistant',
        content: '此对话暂无内容。',
        type: 'text',
        timestamp: new Date().toISOString(),
        visible: true
      }]);
    }
    
    // 更新URL
    if (navigate) {
      navigate(`/chat/${conversationId}`);
    }
  } catch (err) {
    console.error('选择对话时出错:', err);
    setError('无法加载对话');
  } finally {
    setIsLoading(false);
  }
};

// 处理文件附件上传
export const handleFileUpload = (e, fileType = 'any', { setAttachments, MessageType }) => {
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
      file.type.startsWith('application/') || 
      file.type.startsWith('text/') ||
      file.name.endsWith('.pdf') ||
      file.name.endsWith('.doc') ||
      file.name.endsWith('.docx') ||
      file.name.endsWith('.txt')
    );
  }
  
  // 为每个文件创建预览
  const newAttachments = filteredFiles.map(file => {
    const id = generateUUID();
    let type = MessageType.DOCUMENT;
    
    if (file.type.startsWith('image/')) {
      type = MessageType.IMAGE;
    } else if (file.type.startsWith('audio/')) {
      type = MessageType.AUDIO;
    } else if (file.type.startsWith('video/')) {
      type = MessageType.VIDEO;
    }
    
    // 创建文件预览URL
    const preview = URL.createObjectURL(file);
    
    return {
      id,
      file,
      name: file.name,
      type,
      preview,
      size: file.size
    };
  });
  
  setAttachments(prev => [...prev, ...newAttachments]);
};

// 处理不同类型的文件上传
export const handleImageUpload = (e, { boundHandleFileUpload }) => boundHandleFileUpload(e, 'image');
export const handleAudioUpload = (e, { boundHandleFileUpload }) => boundHandleFileUpload(e, 'audio');
export const handleVideoUpload = (e, { boundHandleFileUpload }) => boundHandleFileUpload(e, 'video');
export const handleDocumentUpload = (e, { boundHandleFileUpload }) => boundHandleFileUpload(e, 'document');

// 删除附件
export const removeAttachment = (attachmentId, { setAttachments }) => {
  setAttachments(prev => prev.filter(attachment => attachment.id !== attachmentId));
};

// 处理表单提交
export const handleSubmit = async (e, {
  textInput, setTextInput, attachments, setAttachments, messages, setMessages,
  sessionId, turnId, setTurnId, generateUUID, useAgentChat, setIsLoading,
  setError, savedAttachments, setSavedAttachments, isLoggedIn,
  saveConversation, currentConversationId, setCurrentConversationId, setActiveTools, SenderRole,
  MessageType, createMessage, boundFetchUserConversations, navigate
}) => {
  e.preventDefault();
  
  // 声明变量，用于后续清除超时计时器和处理附件
  let loadingTimeoutId;
  let safetyTimeoutId;
  let imageAttachment = null;
  
  if (!textInput.trim() && attachments.length === 0) return;
  
  // 创建新的回合ID
  const newTurnId = generateUUID();
  setTurnId(newTurnId);
  
  // 准备用户消息
  const userMessages = [];
  
  // 定义会话ID和新对话标记
  let sessionIdToUse;
  let isNewConversation = false;
  
  // 处理用户消息，将文本和图片合并为一个消息
  let messageContent = textInput.trim();
  let messageType = MessageType.TEXT;
  let messageData = {};
  
  // 处理附件
  if (attachments.length > 0) {
    const currentAttachments = [...attachments];
    
    // 检查是否有图片附件
    if (currentAttachments.length > 0) {
      for (const attachment of currentAttachments) {
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
  
  // 在状态更新前创建当前消息的本地副本
  const currentMessages = [...messages];
  
  // 添加用户消息到状态
  const updatedMessages = [...currentMessages, ...userMessages];
  setMessages(updatedMessages);
  setTextInput('');
  setAttachments([]);
  setIsLoading(true);
  setError(null);
  
  // 添加全局超时保护，确保即使请求卡住也会重置加载状态
  const SAFETY_TIMEOUT = 30000; // 30秒安全超时
  
  // 检查是否有图片附件
  if (attachments.length > 0) {
    imageAttachment = attachments[0];
  }
  
  safetyTimeoutId = setTimeout(() => {
    console.error('[ERROR] 安全超时触发，强制重置加载状态');
    setIsLoading(false);
    setError('请求处理时间过长，已自动取消。请检查网络连接后重试。');
    
    // 添加错误消息到聊天
    const timeoutMessage = createMessage(
      SenderRole.SYSTEM,
      '请求超时，已自动取消。请检查网络连接后重试。',
      MessageType.TEXT,
      { error: true }
    );
    setMessages(prev => [...prev, timeoutMessage]);
  }, SAFETY_TIMEOUT);
  
  try {
    // 添加API超时保护
    loadingTimeoutId = setTimeout(() => {
      console.error('[ERROR] 请求处理时间过长，强制重置加载状态');
      setIsLoading(false);
      setError('请求处理时间过长，请重试或检查网络连接');
    }, API_CONFIG.TIMEOUT + 5000); // 比API超时多5秒，确保API超时有机会先触发
    
    // 准备请求数据 - 使用本地副本而不是依赖状态
    const visibleMessages = updatedMessages
      .filter(msg => msg.visible || msg.role === SenderRole.SYSTEM)
      .map(msg => ({
        role: msg.role,
        content: msg.content,
        type: msg.type
      }));
    
    // 决定使用哪个聊天端点
    const chatEndpoint = useAgentChat ? '/api/chat/agent' : '/api/chat';
    console.log(`[DEBUG] 选择的聊天端点: ${chatEndpoint}, Agent模式: ${useAgentChat}`); 
    
    let response;
    
    // 如果有文件附件且使用Agent模式，使用多部分表单提交
    if (imageAttachment && useAgentChat) {
      console.log('[DEBUG] 准备发送图片附件请求...');
      
      const formData = new FormData();
      formData.append('user_input', messageContent);
      formData.append('session_id', sessionId);
      formData.append('user_id', localStorage.getItem('userId') || 'anonymous');
      formData.append('ai_id', 'ai_rainbow_city');
      
      // 根据文件类型选择不同的字段名
      let fieldName = 'image'; // 默认为图片
      
      // 如果有原始文件，使用原始文件
      if (imageAttachment.file) {
        formData.append(fieldName, imageAttachment.file);
      } 
      // 如果有预览URL，尝试转换为Blob
      else if (imageAttachment.preview && imageAttachment.preview.startsWith('data:')) {
        try {
          const res = await fetch(imageAttachment.preview);
          const blob = await res.blob();
          formData.append(fieldName, blob, imageAttachment.name || 'image');
        } catch (error) {
          console.error('Error converting preview to blob:', error);
          throw new Error('无法处理图片附件: ' + error.message);
        }
      }
      
      // 使用新的统一文件处理端点
      const apiEndpoint = API_CONFIG.ENDPOINTS.FILE_UPLOAD;
      const fullUrl = API_CONFIG.getFullUrl(apiEndpoint);
      console.log('[DEBUG] 发送文件请求到:', fullUrl, '附件类型:', imageAttachment.type, '附件大小:', imageAttachment.file ? imageAttachment.file.size : '未知');
      
      // 创建超时控制器
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.TIMEOUT); // 使用配置的超时时间
      
      try {
        response = await fetch(fullUrl, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}` // 添加认证令牌
          },
          body: formData,
          signal: controller.signal
        });
        clearTimeout(timeoutId);
        console.log('[DEBUG] 收到图片请求响应状态码:', response.status, '响应类型:', response.headers.get('content-type'));
      } catch (fetchError) {
        clearTimeout(timeoutId);
        if (fetchError.name === 'AbortError') {
          console.error('[ERROR] 文件上传请求超时');
          throw new Error(API_CONFIG.ERROR_MESSAGES.TIMEOUT);
        }
        console.error('[ERROR] 文件上传失败:', fetchError);
        throw fetchError;
      }
    } 
    // 否则使用标准JSON请求
    else {
      // 使用API_CONFIG中的配置端点
      const apiEndpoint = useAgentChat ? API_CONFIG.ENDPOINTS.AGENT_CHAT : API_CONFIG.ENDPOINTS.CHAT;
      console.log('[DEBUG] 准备发送文本请求到:', apiEndpoint);
      
      // 检测当前聊天窗口并确保会话ID的一致性
      
      // 定义变量
      let sessionIdToUse;
      let isNewConversation = false;
      
      // 如果已有当前对话ID，则使用该ID对应的会话ID
      if (currentConversationId) {
        console.log('[DEBUG] 当前对话已有ID:', currentConversationId);
        // 使用与当前对话关联的会话ID
        sessionIdToUse = sessionId;
      } 
      // 如果是新对话，但有传入的会话ID
      else if (sessionId && sessionId.length === 36) {
        console.log('[DEBUG] 新对话使用现有会话ID:', sessionId);
        sessionIdToUse = sessionId;
        isNewConversation = true;
      }
      // 如果没有有效的会话ID，生成一个新的
      else {
        sessionIdToUse = generateUUID();
        console.log('[DEBUG] 生成新的会话ID:', sessionIdToUse);
        isNewConversation = true;
      }
      
      // 验证会话ID的完整性
      if (!sessionIdToUse || sessionIdToUse.length !== 36) {
        console.error('[ERROR] 会话ID无效或长度不正确，应为36位的UUID格式，实际长度:', sessionIdToUse ? sessionIdToUse.length : 0);
        // 生成一个新的有效会话ID
        sessionIdToUse = generateUUID();
        console.log('[DEBUG] 生成新的有效会话ID:', sessionIdToUse);
      }
      
      const requestBody = {
        session_id: sessionIdToUse,
        turn_id: newTurnId,
        messages: visibleMessages,
        user_id: localStorage.getItem('userId') || 'anonymous',
        ai_id: 'ai_rainbow_city'
      };
      
      // 添加调试信息
      console.log('[DEBUG] 会话ID:', sessionIdToUse, '(长度:', sessionIdToUse.length, ')用户ID:', requestBody.user_id);
      
      console.log('[DEBUG] 请求体:', JSON.stringify(requestBody, null, 2));
      
      try {
        // 使用统一的sendChatRequest函数发送请求
        const rawResponse = await fetch(API_CONFIG.getFullUrl(apiEndpoint), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify(requestBody)
        });
        
        // 获取原始响应文本
        const responseText = await rawResponse.text();
        console.log('[DEBUG] 原始响应文本:', responseText);
        
        // 尝试解析JSON
        let rawData;
        try {
          rawData = JSON.parse(responseText);
        } catch (e) {
          console.error('[ERROR] 解析JSON失败:', e);
          rawData = { response: responseText };
        }
        
        // 直接提取纯文本响应
        let responseContent = '';
        
        if (rawData && rawData.response) {
          if (typeof rawData.response === 'string') {
            // 如果响应是字符串，尝试检查是否是JSON
            try {
              const possibleJson = JSON.parse(rawData.response);
              if (possibleJson && typeof possibleJson === 'object') {
                responseContent = possibleJson.content || 
                                 possibleJson.text || 
                                 possibleJson.message || 
                                 possibleJson.response || 
                                 rawData.response;
              } else {
                responseContent = rawData.response;
              }
            } catch (e) {
              // 不是JSON，直接使用原始字符串
              responseContent = rawData.response;
            }
          } else if (typeof rawData.response === 'object') {
            responseContent = rawData.response.content || 
                             rawData.response.text || 
                             rawData.response.message || 
                             Object.values(rawData.response).find(v => typeof v === 'string') || 
                             'AI助手响应';
          }
        }
        
        console.log('[DEBUG] 提取的纯文本响应:', responseContent);
        
        // 创建一个新的简化数据对象
        const data = {
          response: responseContent,
          session_id: rawData.session_id,
          has_tool_calls: rawData.has_tool_calls || false,
          tool_calls: rawData.tool_calls || [],
          tool_results: rawData.tool_results || []
        };
        
        response = {
          ok: true,
          json: () => Promise.resolve(data),
          text: () => Promise.resolve(responseContent),
          status: 200,
          headers: new Headers({
            'content-type': 'application/json'
          })
        };
      } catch (fetchError) {
        console.error('[ERROR] 文本请求失败:', fetchError);
        throw fetchError;
      }
    }
    
    // 如果是文件上传请求，需要处理原始响应
    let data;
    if (imageAttachment) {
      if (!response.ok) {
        throw new Error(`服务器错误: ${response.status}`);
      }
      
      // 使用try-catch包裹JSON解析，避免解析错误导致整个请求失败
      try {
        // 先尝试获取响应文本以便调试
        const responseText = await response.text();
        console.log('[DEBUG] 文件上传响应内容:', responseText.substring(0, 500) + (responseText.length > 500 ? '...' : ''));
        
        // 然后解析JSON
        try {
          data = JSON.parse(responseText);
        } catch (parseError) {
          console.error('[ERROR] 解析响应JSON失败:', parseError);
          throw new Error(`无法解析服务器响应: ${parseError.message}\n响应内容: ${responseText.substring(0, 100)}...`);
        }
      } catch (jsonError) {
        console.error('[ERROR] 读取响应内容失败:', jsonError);
        throw new Error(`无法读取服务器响应: ${jsonError.message}`);
      }
    } else {
      // 文本请求已经通过sendChatRequest函数获取并解析了数据
      // 直接使用模拟Response对象中的数据
      data = await response.json();
      console.log('[DEBUG] 处理文本请求响应数据:', data);
    }
    
    // 只提取并显示JSON中的response字段
    let responseContent = '';
    
    // 如果有数据，只提取response字段
    if (data) {
      console.log('[DEBUG] 原始数据格式:', typeof data);
      
      // 如果是对象，直接提取response字段
      if (typeof data === 'object' && data.response) {
        // 直接返回JSON格式的字符串
        responseContent = JSON.stringify({
          "response": data.response,
          "session_id": data.session_id || "",
          "has_tool_calls": data.tool_calls && data.tool_calls.length > 0
        });
        console.log('[DEBUG] 提取并返回response字段');
      }
      // 如果是字符串，尝试解析为JSON后提取response
      else if (typeof data === 'string') {
        const trimmed = data.trim();
        if (trimmed.startsWith('{')) {
          try {
            const parsed = JSON.parse(trimmed);
            if (parsed && parsed.response) {
              // 提取response并返回JSON格式
              responseContent = JSON.stringify({
                "response": parsed.response,
                "session_id": parsed.session_id || "",
                "has_tool_calls": parsed.tool_calls && parsed.tool_calls.length > 0
              });
              console.log('[DEBUG] 从字符串提取并返回response字段');
            } else {
              // 如果没有response字段，返回原始JSON
              responseContent = trimmed;
            }
          } catch (e) {
            console.log('[ERROR] 解析JSON失败:', e);
            responseContent = trimmed; // 如果解析失败，使用原始数据
          }
        } else {
          // 不是JSON格式，直接使用
          responseContent = trimmed;
        }
      }
      // 如果是其他类型的数据，转换为字符串
      else {
        responseContent = String(data);
      }
    }
    
    // 如果没有提取到内容，使用默认回复
    if (!responseContent) {
      responseContent = '你好！有什么可以帮助你的吗？';
    }
    
    console.log('[DEBUG] 最终提取的响应内容:', responseContent.substring(0, 100) + (responseContent.length > 100 ? '...' : ''));
    
    // 创建一个助手消息对象，只包含响应内容
    const assistantMessage = {
      id: generateUUID(),
      sender: SenderRole.ASSISTANT,
      content: responseContent, // 直接使用提取的响应内容
      type: MessageType.TEXT,
      timestamp: new Date().toISOString(),
      isTyping: true,
      displayedContent: '', // 初始为空，将通过打字机效果逐字显示
      visible: true
    };
      
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
            // 使用单独的异步函数处理保存操作，避免阻塞主流程
            (async () => {
              try {
                const savedId = await saveConversation(updatedMessages, currentConversationId);
                console.log('[DEBUG] 对话保存完成，ID:', savedId);
              } catch (saveError) {
                console.error('[ERROR] 保存对话时出错:', saveError);
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
            // 使用单独的异步函数处理保存操作，避免阻塞主流程
            (async () => {
              try {
                // 如果是新对话，创建新对话并保存到数据库
                if (isNewConversation) {
                  try {
                    console.log('[DEBUG] 创建新对话，会话ID:', sessionIdToUse);
                    
                    // 从消息中提取标题
                    const firstUserMessage = updatedMessages.find(msg => msg.role === SenderRole.USER);
                    const assistantReply = updatedMessages.find(msg => msg.role === SenderRole.ASSISTANT && msg.type === MessageType.TEXT);
                    
                    // 结合用户消息和AI回复生成更有意义的标题
                    let title = '新对话';
                    
                    if (firstUserMessage && assistantReply) {
                      // 尝试从用户问题和AI回答中提取关键信息生成标题
                      const userContent = firstUserMessage.content.trim();
                      const aiContent = assistantReply.content.trim();
                      
                      // 如果用户问题是一个问句，直接使用它
                      if (userContent.endsWith('?') || userContent.endsWith('？')) {
                        title = userContent.length > 30 ? userContent.substring(0, 30) + '...' : userContent;
                      } 
                      // 如果用户问题很短，直接使用
                      else if (userContent.length < 20) {
                        title = userContent;
                      }
                      // 否则尝试结合AI回复生成标题
                      else {
                        // 从用户问题中提取前15个字符
                        const userPrefix = userContent.substring(0, 15);
                        // 从AI回复中提取前15个字符
                        const aiPrefix = aiContent.substring(0, 15);
                        title = `${userPrefix}... - ${aiPrefix}...`;
                      }
                    } else if (firstUserMessage) {
                      // 如果只有用户消息，使用用户消息作为标题
                      title = firstUserMessage.content.length > 30 ? 
                        firstUserMessage.content.substring(0, 30) + '...' : 
                        firstUserMessage.content;
                    }
                    
                    // 创建新对话
                    const createConversationEndpoint = API_CONFIG.getFullUrl(API_CONFIG.ENDPOINTS.CONVERSATIONS);
                    const createResponse = await fetch(createConversationEndpoint, {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                      },
                      body: JSON.stringify({
                        title: title,
                        session_id: sessionIdToUse,
                        messages: updatedMessages
                      })
                    });
                    
                    if (createResponse.ok) {
                      const createData = await createResponse.json();
                      console.log('[DEBUG] 新对话创建成功:', createData);
                      
                      // 更新当前对话ID
                      const newConversationId = createData.conversation_id || createData.id;
                      console.log('[DEBUG] 设置新对话ID:', newConversationId);
                      setCurrentConversationId(newConversationId);
                      
                      // 确保新对话显示在历史记录中
                      console.log('[DEBUG] 刷新对话列表');
                      
                      // 等待一下再刷新对话列表，确保后端数据已更新
                      setTimeout(() => {
                        if (boundFetchUserConversations) {
                          console.log('[DEBUG] 执行刷新对话列表');
                          boundFetchUserConversations();
                        } else {
                          console.warn('[WARN] boundFetchUserConversations不可用');
                        }
                      }, 500); // 等待500毫秒再刷新
                      
                      // 更新URL
                      if (navigate) {
                        console.log('[DEBUG] 导航到新对话:', `/chat/${newConversationId}`);
                        navigate(`/chat/${newConversationId}`);
                      }
                      
                      return newConversationId;
                    } else {
                      console.error('[ERROR] 创建新对话失败:', createResponse.status);
                      // 使用更安全的错误处理方式
                      const errorMsg = `创建对话失败: ${createResponse.status}`;
                      setError(errorMsg);
                      return null;
                    }
                  } catch (createError) {
                    console.error('[ERROR] 创建新对话时出错:', createError);
                    return null;
                  }
                } else {
                  // 如果不是新对话，更新现有对话
                  try {
                    const savedId = await saveConversation(updatedMessages, currentConversationId);
                    console.log('[DEBUG] 对话更新完成，ID:', savedId);
                    return savedId;
                  } catch (updateError) {
                    console.error('[ERROR] 更新对话时出错:', updateError);
                    return null;
                  }
                }
              } catch (saveError) {
                console.error('[ERROR] 保存对话时出错:', saveError);
                return null;
              }
            })();
          }
          
          return updatedMessages;
        });
      }
      
      // 如果没有有效响应数据，处理错误情况
      if (!data || !data.response) {
        console.error('[ERROR] 服务器响应格式错误');
        setError('服务器响应格式错误');
        
        // 使用函数式更新来确保正确处理状态
        setMessages(prevMessages => {
          const formatErrorMessage = createMessage(
            SenderRole.SYSTEM,
            '服务器响应格式错误，请重试',
            MessageType.TEXT,
            { error: true }
          );
          return [...prevMessages, formatErrorMessage];
        });
      }
    } catch (error) {
      console.error('[ERROR] 处理响应时出错:', error);
    }
  }
  
  try {
    // Additional code if needed
  } catch (err) {
    console.error('[ERROR] 请求处理错误:', err);
    
    // 创建错误消息
    const errorMessage = createMessage(
      SenderRole.SYSTEM,
      `错误: ${err.message || '未知错误'}`,
      MessageType.TEXT,
      { error: true }
    );
    
    setMessages(prev => [...prev, errorMessage]);
  } finally {
    // 清除所有超时计时器
    if (loadingTimeoutId) {
      clearTimeout(loadingTimeoutId);
    }
    
    // 清除安全超时计时器
    if (safetyTimeoutId) {
      clearTimeout(safetyTimeoutId);
    }
    
    console.log('[DEBUG] 请求处理完成，重置加载状态');
    // 重置加载状态
    setIsLoading(false);
  }
};

// 处理工具调用
export const handleToolAction = (toolId, action, { navigate, availableTools }) => {
  const tool = availableTools.find(t => t.id === toolId);
  if (!tool) return;
  
  if (action === 'navigate') {
    // 导航到工具页面
    navigate(`/tools/${toolId}`);
  }
};

// 创建新聊天
export const handleCreateNewChat = ({
  setMessages, setSessionId, setTurnId, generateUUID, setCurrentConversationId,
  SenderRole, MessageType
}) => {
  // 重置会话状态
  const newSessionId = generateUUID();
  setSessionId(newSessionId);
  setTurnId(generateUUID());
  setCurrentConversationId(null);
  
  // 重置消息
  setMessages([
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
      visible: true
    }
  ]);
};

// Export other necessary functions
export { handleToolAction, handleCreateNewChat };
