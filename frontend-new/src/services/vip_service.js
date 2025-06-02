import axios from 'axios';

const API_URL = 'http://localhost:5000/vip/';

// 获取所有VIP套餐信息
export const getVIPPlans = async () => {
  try {
    console.log('Fetching VIP plans from:', API_URL + 'plans');
    const response = await axios.get(API_URL + 'plans', { withCredentials: true });
    console.log('VIP plans response:', response.data);
    
    // 验证返回的数据格式
    if (response.data && response.data.plans) {
      // 确保返回的是数组
      if (Array.isArray(response.data.plans)) {
        return response.data.plans;
      } else {
        // 如果是对象，转换为数组
        const plansArray = Object.values(response.data.plans);
        return plansArray;
      }
    }
    
    // 如果数据格式不符合预期，返回空数组
    console.warn('Invalid VIP plans data format:', response.data);
    return [];
  } catch (error) {
    console.error('Error fetching VIP plans:', error);
    if (error.response) {
      console.error('Response status:', error.response.status);
      console.error('Response data:', error.response.data);
    }
    throw error.response?.data?.error || '获取VIP套餐信息失败';
  }
};

// 获取当前用户的VIP状态
export const getVIPStatus = async () => {
  try {
    const response = await axios.get(API_URL + 'status', { withCredentials: true });
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || '获取VIP状态失败';
  }
};

// 创建结账会话
export const createCheckoutSession = async (plan, interval) => {
  try {
    const response = await axios.post(API_URL + 'checkout', { plan, interval });
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || '创建结账会话失败';
  }
};

// 处理支付成功
export const handlePaymentSuccess = async (sessionId) => {
  try {
    const response = await axios.get(`${API_URL}success?session_id=${sessionId}`);
    return response.data;
  } catch (error) {
    throw error.response?.data?.error || '处理支付失败';
  }
};

// 获取VIP等级对应的AI伴侣数量上限
export const getAICompanionsLimit = (vipLevel) => {
  const limits = {
    'Free': 1,
    'Pro': 3,
    'Premium': 5,
    'Ultimate': 7,
    'Team': 35
  };
  return limits[vipLevel] || 1;
};

// 获取VIP等级对应的可唤醒AI数量上限
export const getAIAwakenerLimit = (vipLevel) => {
  const limits = {
    'Free': 0,
    'Pro': 1,
    'Premium': 3,
    'Ultimate': 5,
    'Team': 25
  };
  return limits[vipLevel] || 0;
};

// 获取VIP等级对应的每日对话次数上限
export const getDailyChatLimit = (vipLevel) => {
  const limits = {
    'Free': 10,
    'Pro': 50,
    'Premium': 100,
    'Ultimate': Infinity,
    'Team': Infinity
  };
  return limits[vipLevel] || 10;
};

// 获取VIP等级对应的每日LIO对话次数上限
export const getDailyLIOLimit = (vipLevel) => {
  const limits = {
    'Free': 0,
    'Pro': 50,
    'Premium': 100,
    'Ultimate': Infinity,
    'Team': Infinity
  };
  return limits[vipLevel] || 0;
};

// 获取VIP等级对应的每周邀请码使用次数上限
export const getWeeklyInviteLimit = (vipLevel) => {
  const limits = {
    'Free': 10,
    'Pro': 100,
    'Premium': 200,
    'Ultimate': Infinity,
    'Team': Infinity
  };
  return limits[vipLevel] || 10;
};

// 格式化价格显示（分转换为元）
export const formatPrice = (priceInCents) => {
  return `$${(priceInCents / 100).toFixed(2)}`;
};

// 检查用户是否可以使用特定功能
export const canUseFeature = (user, feature) => {
  if (!user) return false;
  
  switch (feature) {
    case 'chat':
      return user.daily_chat_count < user.daily_chat_limit;
    case 'lio':
      return user.daily_lio_limit > 0 && user.daily_lio_count < user.daily_lio_limit;
    case 'add_ai_companion':
      return user.ai_companions_count < user.ai_companions_limit;
    case 'awaken_ai':
      return user.ai_awakened_count < user.ai_awakener_limit;
    case 'use_invite_code':
      return user.is_activated && user.weekly_invite_count < user.weekly_invite_limit;
    default:
      return false;
  }
};
