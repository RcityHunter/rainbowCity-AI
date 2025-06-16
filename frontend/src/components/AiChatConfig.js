// API配置和超时设置
export const API_CONFIG = {
  // 后端服务器URL
  BACKEND_URL: 'http://localhost:5000',
  
  // API请求超时时间（毫秒）
  TIMEOUT: 60000, // 增加到60秒超时，给后端足够的处理时间
  
  // API端点
  ENDPOINTS: {
    CHAT: '/api/chat',
    AGENT_CHAT: '/api/chat/agent',
    HEALTH: '/api/chat/health',
    CONVERSATIONS: '/api/conversations',
    FILE_UPLOAD: '/api/chat/agent/with_file'
  },
  
  // 获取完整的API URL
  getFullUrl: function(endpoint) {
    return `${this.BACKEND_URL}${endpoint}`;
  },
  
  // 错误消息
  ERROR_MESSAGES: {
    TIMEOUT: '请求超时，服务器处理时间过长。请稍后重试。',
    SERVER_ERROR: '服务器错误，请联系管理员。',
    CONNECTION_ERROR: '无法连接到服务器，请检查网络连接。',
    UNKNOWN_ERROR: '发生未知错误，请重试。',
    SESSION_ERROR: '会话ID无效或已过期，已创建新会话。'
  }
};

// 创建带超时的fetch请求
export const fetchWithTimeout = async (url, options = {}, timeout = API_CONFIG.TIMEOUT) => {
  const controller = new AbortController();
  const signal = controller.signal;
  
  const timeoutId = setTimeout(() => {
    controller.abort();
    console.error(`[ERROR] 请求超时: ${url}`);
  }, timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal
    });
    
    clearTimeout(timeoutId);
    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error(API_CONFIG.ERROR_MESSAGES.TIMEOUT);
    }
    
    throw error;
  }
};

// 安全的JSON解析
export const safeJsonParse = async (response) => {
  try {
    return await response.json();
  } catch (error) {
    console.error('[ERROR] JSON解析错误:', error);
    throw new Error('服务器返回的数据格式错误');
  }
};

// 格式化错误消息
export const formatErrorMessage = (error) => {
  if (!error) return API_CONFIG.ERROR_MESSAGES.UNKNOWN_ERROR;
  
  if (error.message) {
    return error.message;
  }
  
  if (typeof error === 'string') {
    return error;
  }
  
  return API_CONFIG.ERROR_MESSAGES.UNKNOWN_ERROR;
};

// 专门的聊天API请求处理函数
export const sendChatRequest = async (endpointPath, data, options = {}) => {
  const controller = new AbortController();
  const signal = controller.signal;
  
  // 获取完整URL
  const fullUrl = API_CONFIG.getFullUrl(endpointPath);
  
  // 设置超时
  const timeoutId = setTimeout(() => {
    controller.abort();
    console.error(`[ERROR] 请求超时: ${fullUrl}`);
  }, options.timeout || API_CONFIG.TIMEOUT);
  
  try {
    // 验证会话ID
    if (data.session_id && data.session_id.length !== 36) {
      console.error(`[ERROR] 会话ID长度不正确: ${data.session_id} (长度: ${data.session_id.length})`);
    }
    
    // 添加认证信息
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    };
    
    // 发送请求
    console.log(`[DEBUG] 发送请求到: ${fullUrl}`);
    console.log(`[DEBUG] 请求数据:`, data);
    
    const response = await fetch(fullUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(data),
      signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      throw new Error(`服务器响应错误: ${response.status} ${response.statusText}`);
    }
    
    return await safeJsonParse(response);
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error.name === 'AbortError') {
      throw new Error(API_CONFIG.ERROR_MESSAGES.TIMEOUT);
    }
    
    console.error(`[ERROR] 请求失败: ${fullUrl}`, error);
    throw error;
  }
};
