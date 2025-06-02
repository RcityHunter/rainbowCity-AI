/**
 * 聊天历史记录服务
 * 提供与后端聊天历史API交互的函数
 */

// API基础URL
const API_BASE_URL = 'http://localhost:5000';

/**
 * 获取用户的所有聊天会话
 * @returns {Promise<Array>} 聊天会话列表
 */
export const getUserChats = async () => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法获取聊天会话');
    return [];
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      return [];
    }

    if (!response.ok) {
      throw new Error(`获取聊天会话失败: ${response.status}`);
    }

    const data = await response.json();
    return data.chats || [];
  } catch (error) {
    console.error('获取聊天会话失败:', error);
    return [];
  }
};

/**
 * 创建新的聊天会话
 * @param {Object} chatData 聊天会话数据
 * @returns {Promise<Object>} 创建的聊天会话
 */
export const createChat = async (chatData) => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法创建聊天会话');
    throw new Error('未登录');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(chatData)
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      throw new Error('登录已过期');
    }

    if (!response.ok) {
      throw new Error(`创建聊天会话失败: ${response.status}`);
    }

    const data = await response.json();
    return data.chat || {};
  } catch (error) {
    console.error('创建聊天会话失败:', error);
    throw error;
  }
};

/**
 * 获取特定聊天会话的详情
 * @param {string} chatId 聊天会话ID
 * @returns {Promise<Object>} 聊天会话详情
 */
export const getChatById = async (chatId) => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法获取聊天会话');
    throw new Error('未登录');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      throw new Error('登录已过期');
    }

    if (!response.ok) {
      throw new Error(`获取聊天会话失败: ${response.status}`);
    }

    const data = await response.json();
    return data.chat || {};
  } catch (error) {
    console.error(`获取聊天会话 ${chatId} 失败:`, error);
    throw error;
  }
};

/**
 * 更新聊天会话
 * @param {string} chatId 聊天会话ID
 * @param {Object} updateData 更新数据
 * @returns {Promise<Object>} 更新后的聊天会话
 */
export const updateChat = async (chatId, updateData) => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法更新聊天会话');
    throw new Error('未登录');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(updateData)
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      throw new Error('登录已过期');
    }

    if (!response.ok) {
      throw new Error(`更新聊天会话失败: ${response.status}`);
    }

    const data = await response.json();
    return data.chat || {};
  } catch (error) {
    console.error(`更新聊天会话 ${chatId} 失败:`, error);
    throw error;
  }
};

/**
 * 删除聊天会话
 * @param {string} chatId 聊天会话ID
 * @returns {Promise<boolean>} 是否删除成功
 */
export const deleteChat = async (chatId) => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法删除聊天会话');
    throw new Error('未登录');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      throw new Error('登录已过期');
    }

    if (!response.ok) {
      throw new Error(`删除聊天会话失败: ${response.status}`);
    }

    return true;
  } catch (error) {
    console.error(`删除聊天会话 ${chatId} 失败:`, error);
    throw error;
  }
};

/**
 * 获取聊天会话的消息
 * @param {string} chatId 聊天会话ID
 * @param {number} page 页码，默认1
 * @param {number} pageSize 每页大小，默认20
 * @returns {Promise<Object>} 消息列表和分页信息
 */
export const getChatMessages = async (chatId, page = 1, pageSize = 20) => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法获取聊天消息');
    throw new Error('未登录');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages?page=${page}&page_size=${pageSize}`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      throw new Error('登录已过期');
    }

    if (!response.ok) {
      throw new Error(`获取聊天消息失败: ${response.status}`);
    }

    const data = await response.json();
    return {
      messages: data.messages || [],
      total: data.total || 0,
      page: data.page || 1,
      pageSize: data.page_size || pageSize,
      totalPages: data.total_pages || 1
    };
  } catch (error) {
    console.error(`获取聊天 ${chatId} 的消息失败:`, error);
    throw error;
  }
};

/**
 * 添加消息到聊天会话
 * @param {string} chatId 聊天会话ID
 * @param {Object} messageData 消息数据
 * @returns {Promise<Object>} 添加的消息
 */
export const addChatMessage = async (chatId, messageData) => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法添加聊天消息');
    throw new Error('未登录');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(messageData)
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      throw new Error('登录已过期');
    }

    if (!response.ok) {
      throw new Error(`添加聊天消息失败: ${response.status}`);
    }

    const data = await response.json();
    return data.message || {};
  } catch (error) {
    console.error(`添加消息到聊天 ${chatId} 失败:`, error);
    throw error;
  }
};

/**
 * 批量添加消息到聊天会话
 * @param {string} chatId 聊天会话ID
 * @param {Array} messages 消息数组
 * @returns {Promise<Array>} 添加的消息数组
 */
export const addChatMessagesBatch = async (chatId, messages) => {
  const token = localStorage.getItem('token');
  if (!token) {
    console.log('未登录，无法批量添加聊天消息');
    throw new Error('未登录');
  }

  try {
    const response = await fetch(`${API_BASE_URL}/api/chats/${chatId}/messages/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ messages })
    });

    if (response.status === 401) {
      console.log('Token已过期，清除登录状态');
      localStorage.removeItem('token');
      localStorage.removeItem('userId');
      throw new Error('登录已过期');
    }

    if (!response.ok) {
      throw new Error(`批量添加聊天消息失败: ${response.status}`);
    }

    const data = await response.json();
    return data.messages || [];
  } catch (error) {
    console.error(`批量添加消息到聊天 ${chatId} 失败:`, error);
    throw error;
  }
};
