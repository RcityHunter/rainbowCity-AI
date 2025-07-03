import axios from 'axios';

// 使用绝对路径，直接指向后端服务器
// 更新为 FastAPI 的 API 前缀，使用端口5001

// 从环境变量获取API基础URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5001/api';
const API_URL = `${API_BASE_URL}/auth/`;
const OAUTH_URL = `${API_BASE_URL}/oauth/`;

// 设置请求拦截器，在每个请求中添加认证令牌
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      // 确保令牌格式正确，与 FastAPI 的 OAuth2PasswordBearer 兼容
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    // 添加withCredentials以支持跨域请求中的凭证
    // 注意：当使用withCredentials=true时，服务器必须返回具体的Origin而不是通配符*
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
    
    const response = await axios.post(API_URL + 'register', userData, {
      headers: {
        'Content-Type': 'application/json'
      },
      withCredentials: true // 确保在注册请求中也发送凭证
    });
    
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
    // 使用 FastAPI OAuth2 格式发送登录请求
    const formData = new URLSearchParams();
    formData.append('username', email);  // FastAPI OAuth2 使用 username 字段
    formData.append('password', password);
    
    const response = await axios.post(API_URL + 'login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      withCredentials: true // 确保在登录请求中也发送凭证
    });
    
    console.log('Login response:', response.data);
    
    // FastAPI OAuth2 返回 access_token 而不是 token
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
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

// 获取Google认证URL
export const getGoogleAuthUrl = async () => {
  try {
    const response = await axios.get(OAUTH_URL + 'google/auth');
    return response.data.auth_url;
  } catch (error) {
    console.error('Error getting Google auth URL:', error);
    throw error.response?.data?.error || '获取Google认证URL失败';
  }
};

// 获取GitHub认证URL
export const getGithubAuthUrl = async () => {
  try {
    const response = await axios.get(OAUTH_URL + 'github/auth');
    return response.data.auth_url;
  } catch (error) {
    console.error('Error getting GitHub auth URL:', error);
    throw error.response?.data?.error || '获取GitHub认证URL失败';
  }
};

// 处理Google OAuth回调
export const handleGoogleCallback = async (code) => {
  try {
    console.log('Processing Google OAuth callback with code:', code);
    const response = await axios.post(OAUTH_URL + 'google/callback', { code });
    
    console.log('Google OAuth response:', response.data);
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      
      if (response.data.user && response.data.user.id) {
        console.log('Storing user ID from Google OAuth:', response.data.user.id);
        localStorage.setItem('userId', response.data.user.id);
      }
    }
    
    return response.data;
  } catch (error) {
    console.error('Google OAuth callback error:', error);
    throw error.response?.data?.error || 'Google登录失败';
  }
};

// 处理GitHub OAuth回调
export const handleGithubCallback = async (code) => {
  try {
    console.log('Processing GitHub OAuth callback with code:', code.substring(0, 5) + '...');
    console.log('Code length:', code.length);
    
    // 添加请求超时设置，防止长时间等待
    const response = await axios.post(OAUTH_URL + 'github/callback', { code }, {
      timeout: 15000, // 15秒超时
      validateStatus: function (status) {
        // 只将 2xx 状态码视为成功，避免混淆
        return status >= 200 && status < 300;
      }
    });
    
    console.log('GitHub OAuth response status:', response.status);
    console.log('GitHub OAuth response data:', response.data);
    
    // 检查响应中是否有 access_token
    if (response.data && response.data.access_token) {
      console.log('GitHub OAuth successful, received access token');
      localStorage.setItem('token', response.data.access_token);
      
      // 检查响应中是否有用户信息
      if (response.data.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        if (response.data.user.id) {
          console.log('Storing user ID from GitHub OAuth:', response.data.user.id);
          localStorage.setItem('userId', response.data.user.id);
        }
      } else {
        console.warn('GitHub OAuth response missing user data');
      }
      
      return response.data;
    } else {
      console.error('GitHub OAuth response missing access_token:', response.data);
      throw new Error('GitHub认证响应缺少访问令牌');
    }
  } catch (error) {
    console.error('GitHub OAuth callback error:', error);
    
    // 检查是否有详细的错误响应
    if (error.response && error.response.data) {
      console.error('Error response data:', error.response.data);
      
      // 检查是否是授权码过期错误
      if (error.response.data.error === 'oauth_token_error' || 
          (error.response.data.details && error.response.data.details.error_type === 'bad_verification_code')) {
        throw new Error('授权码已过期或无效，请重新登录');
      }
      
      // 如果有错误消息，直接抛出
      if (error.response.data.message) {
        throw new Error(error.response.data.message);
      }
      
      // 如果有错误代码，抛出错误
      if (error.response.data.error) {
        throw new Error(`GitHub登录失败: ${error.response.data.error}`);
      }
    }
    
    // 如果是超时错误
    if (error.code === 'ECONNABORTED') {
      throw new Error('GitHub登录超时，请检查网络连接并重试');
    }
    
    // 其他错误
    throw error.response?.data?.error || error.message || 'GitHub登录失败，请稍后再试';
  }
};
