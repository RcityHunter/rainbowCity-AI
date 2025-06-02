import axios from 'axios';

// 使用绝对路径，直接指向后端服务器
const API_URL = 'http://localhost:5000/auth/';

// 设置请求拦截器，在每个请求中添加认证令牌
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    // 添加withCredentials以支持跨域请求中的凭证
    config.withCredentials = true;
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 注册新用户
export const register = async (userData) => {
  try {
    console.log('Registering user with data:', { ...userData, password: '***' });
    console.log('Registration endpoint:', API_URL + 'register');
    
    const response = await axios.post(API_URL + 'register', userData);
    console.log('Registration response:', response.data);
    
    // 注册成功后，如果返回了token，存储到本地
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      // 确保单独存储userId，用于对话功能
      if (response.data.user && response.data.user.id) {
        console.log('Storing user ID:', response.data.user.id);
        localStorage.setItem('userId', response.data.user.id);
      } else {
        console.warn('User ID not found in registration response');
      }
    }
    
    return response.data;
  } catch (error) {
    console.error('Registration error:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error.response?.data?.error || '注册失败，请稍后再试';
  }
};

// 用户登录
export const login = async (email, password) => {
  try {
    console.log('Attempting login for:', email);
    const response = await axios.post(API_URL + 'login', { email, password });
    console.log('Login response:', response.data);
    
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      // 确保单独存储userId，用于对话功能
      if (response.data.user && response.data.user.id) {
        console.log('Storing user ID:', response.data.user.id);
        localStorage.setItem('userId', response.data.user.id);
      } else {
        console.warn('User ID not found in response');
      }
    }
    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error.response?.data?.error || '登录失败，请检查邮箱和密码';
  }
};

// 用户登出
export const logout = () => {
  console.log('Logging out user');
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  localStorage.removeItem('userId');
  console.log('All user data cleared from localStorage');
};

// 获取当前用户信息
export const getCurrentUser = () => {
  const userStr = localStorage.getItem('user');
  if (userStr) return JSON.parse(userStr);
  return null;
};

// 获取用户详细信息（从服务器刷新）
export const getUserProfile = async () => {
  try {
    console.log('Fetching user profile from:', API_URL + 'profile');
    const token = localStorage.getItem('token');
    console.log('Using token:', token ? `${token.substring(0, 10)}...` : 'No token found');
    
    const response = await axios.get(API_URL + 'profile', {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    console.log('User profile response:', response.data);
    // 更新本地存储的用户信息
    localStorage.setItem('user', JSON.stringify(response.data));
    return response.data;
  } catch (error) {
    console.error('Error fetching user profile:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error.response?.data?.error || '获取用户信息失败';
  }
};

// 更新用户个人资料
export const updateUserProfile = async (profileData) => {
  try {
    const response = await axios.put(API_URL + 'profile', profileData);
    // 更新本地存储的用户信息
    localStorage.setItem('user', JSON.stringify(response.data.user));
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || '更新个人资料失败';
  }
};

// 修改密码
export const changePassword = async (currentPassword, newPassword) => {
  try {
    const response = await axios.post(API_URL + 'change-password', {
      current_password: currentPassword,
      new_password: newPassword
    });
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || '修改密码失败';
  }
};

// 验证邀请码
export const verifyInviteCode = async (code) => {
  try {
    const response = await axios.post(API_URL + 'verify-invite-code', { code });
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || '无效的邀请码';
  }
};

// 获取用户的邀请码
export const getUserInviteCodes = async () => {
  try {
    const response = await axios.get(API_URL + 'invite-codes');
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || '获取邀请码失败';
  }
};

// 检查用户是否已登录
export const isAuthenticated = () => {
  return localStorage.getItem('token') !== null;
};

// 检查用户是否是VIP
export const isVIP = () => {
  const user = getCurrentUser();
  return user && user.is_vip;
};

// 检查用户是否有特定角色
export const hasRole = (role) => {
  const user = getCurrentUser();
  return user && user.roles && user.roles.includes(role);
};
