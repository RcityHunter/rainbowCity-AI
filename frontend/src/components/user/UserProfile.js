import React, { useState, useEffect } from 'react';
import { getUserProfile, updateUserProfile, changePassword } from '../../services/auth_service';
import { getVIPStatus } from '../../services/vip_service';
import './UserProfile.css';

const UserProfile = () => {
  const [user, setUser] = useState(null);
  const [vipStatus, setVipStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('profile');
  
  // 个人资料表单数据
  const [profileData, setProfileData] = useState({
    username: '',
    display_name: '',
    bio: '',
    avatar_url: ''
  });
  
  // 密码修改表单数据
  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: ''
  });
  
  // 加载用户数据
  useEffect(() => {
    const fetchUserData = async () => {
      try {
        setLoading(true);
        
        // 获取用户信息
        try {
          const userData = await getUserProfile();
          setUser(userData);
          setProfileData({
            username: userData.username || '',
            display_name: userData.display_name || '',
            bio: userData.bio || '',
            avatar_url: userData.avatar_url || ''
          });
          console.log('用户信息获取成功:', userData);
        } catch (userErr) {
          console.error('获取用户信息失败:', userErr);
          setError('获取用户信息失败: ' + (userErr.message || '未知错误'));
          // 如果是认证错误，可以重定向到登录页面
          if (userErr.response && userErr.response.status === 401) {
            console.log('认证失败，请重新登录');
            // 可以在这里添加重定向到登录页面的逻辑
            // navigate('/login');
          }
        }
        
        // 获取VIP状态
        try {
          const vipData = await getVIPStatus();
          setVipStatus(vipData);
          console.log('VIP状态获取成功:', vipData);
        } catch (vipErr) {
          console.error('获取VIP状态失败:', vipErr);
          // VIP状态获取失败不影响用户资料的显示
        }
      } catch (err) {
        setError('获取数据失败');
        console.error('获取数据失败:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserData();
  }, []);
  
  // 处理个人资料表单变化
  const handleProfileChange = (e) => {
    const { name, value } = e.target;
    setProfileData(prev => ({ ...prev, [name]: value }));
  };
  
  // 处理密码表单变化
  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
  };
  
  // 提交个人资料更新
  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    try {
      const result = await updateUserProfile(profileData);
      setUser(result.user);
      setSuccess('个人资料已更新');
    } catch (err) {
      setError(typeof err === 'string' ? err : '更新个人资料失败');
    } finally {
      setLoading(false);
    }
  };
  
  // 提交密码修改
  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(null);
    
    // 验证新密码
    if (passwordData.new_password !== passwordData.confirm_password) {
      setError('两次输入的新密码不一致');
      setLoading(false);
      return;
    }
    
    // 验证密码强度
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    if (!passwordRegex.test(passwordData.new_password)) {
      setError('密码必须至少8个字符，包含大小写字母和数字');
      setLoading(false);
      return;
    }
    
    try {
      await changePassword(passwordData.current_password, passwordData.new_password);
      setSuccess('密码已成功修改');
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: ''
      });
    } catch (err) {
      setError(typeof err === 'string' ? err : '修改密码失败');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading && !user) {
    return <div className="loading-container">加载中...</div>;
  }
  
  return (
    <div className="user-profile-container">
      <div className="profile-header">
        <div className="profile-avatar">
          {user?.avatar_url ? (
            <img src={user.avatar_url} alt="用户头像" />
          ) : (
            <div className="avatar-placeholder">
              {user?.display_name?.charAt(0) || user?.username?.charAt(0) || user?.email?.charAt(0) || '?'}
            </div>
          )}
        </div>
        <div className="profile-info">
          <h2>{user?.display_name || user?.username || '用户'}</h2>
          <p className="profile-email">{user?.email}</p>
          {user?.is_vip && (
            <div className="vip-badge">
              {user?.vip_level} VIP
              {user?.vip_expiry && (
                <span className="vip-expiry">
                  到期时间: {new Date(user.vip_expiry).toLocaleDateString()}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="profile-tabs">
        <button 
          className={activeTab === 'profile' ? 'tab-active' : ''}
          onClick={() => setActiveTab('profile')}
        >
          个人资料
        </button>
        <button 
          className={activeTab === 'security' ? 'tab-active' : ''}
          onClick={() => setActiveTab('security')}
        >
          安全设置
        </button>
        <button 
          className={activeTab === 'stats' ? 'tab-active' : ''}
          onClick={() => setActiveTab('stats')}
        >
          使用统计
        </button>
      </div>
      
      {error && <div className="profile-error">{error}</div>}
      {success && <div className="profile-success">{success}</div>}
      
      <div className="profile-content">
        {activeTab === 'profile' && (
          <form onSubmit={handleProfileSubmit} className="profile-form">
            <div className="form-group">
              <label htmlFor="username">用户名</label>
              <input
                type="text"
                id="username"
                name="username"
                value={profileData.username}
                onChange={handleProfileChange}
                placeholder="请输入用户名"
              />
            </div>
            <div className="form-group">
              <label htmlFor="display_name">显示名称</label>
              <input
                type="text"
                id="display_name"
                name="display_name"
                value={profileData.display_name}
                onChange={handleProfileChange}
                placeholder="请输入显示名称"
              />
            </div>
            <div className="form-group">
              <label htmlFor="avatar_url">头像URL</label>
              <input
                type="url"
                id="avatar_url"
                name="avatar_url"
                value={profileData.avatar_url}
                onChange={handleProfileChange}
                placeholder="请输入头像图片URL"
              />
            </div>
            <div className="form-group">
              <label htmlFor="bio">个人简介</label>
              <textarea
                id="bio"
                name="bio"
                value={profileData.bio}
                onChange={handleProfileChange}
                placeholder="请输入个人简介"
                rows="4"
              />
            </div>
            <button type="submit" className="profile-button" disabled={loading}>
              {loading ? '保存中...' : '保存更改'}
            </button>
          </form>
        )}
        
        {activeTab === 'security' && (
          <form onSubmit={handlePasswordSubmit} className="profile-form">
            <div className="form-group">
              <label htmlFor="current_password">当前密码</label>
              <input
                type="password"
                id="current_password"
                name="current_password"
                value={passwordData.current_password}
                onChange={handlePasswordChange}
                required
                placeholder="请输入当前密码"
              />
            </div>
            <div className="form-group">
              <label htmlFor="new_password">新密码</label>
              <input
                type="password"
                id="new_password"
                name="new_password"
                value={passwordData.new_password}
                onChange={handlePasswordChange}
                required
                placeholder="至少8个字符，包含大小写字母和数字"
              />
            </div>
            <div className="form-group">
              <label htmlFor="confirm_password">确认新密码</label>
              <input
                type="password"
                id="confirm_password"
                name="confirm_password"
                value={passwordData.confirm_password}
                onChange={handlePasswordChange}
                required
                placeholder="请再次输入新密码"
              />
            </div>
            <button type="submit" className="profile-button" disabled={loading}>
              {loading ? '修改中...' : '修改密码'}
            </button>
          </form>
        )}
        
        {activeTab === 'stats' && (
          <div className="profile-stats">
            <h3>使用统计</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{user?.ai_companions_count || 0}</div>
                <div className="stat-label">AI伴侣数量</div>
                <div className="stat-limit">上限: {user?.ai_companions_limit || 0}</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{user?.ai_awakened_count || 0}</div>
                <div className="stat-label">已唤醒AI</div>
                <div className="stat-limit">上限: {user?.ai_awakener_limit || 0}</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{user?.ai_ids_generated || 0}</div>
                <div className="stat-label">生成的AI-ID</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{user?.frequencies_generated || 0}</div>
                <div className="stat-label">生成的频率编号</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{user?.invite_count || 0}</div>
                <div className="stat-label">成功邀请</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">{user?.conversation_count || 0}</div>
                <div className="stat-label">对话总轮数</div>
              </div>
            </div>
            
            <h3>今日使用情况</h3>
            <div className="usage-bars">
              <div className="usage-item">
                <div className="usage-label">对话次数</div>
                <div className="usage-bar">
                  <div 
                    className="usage-progress" 
                    style={{ 
                      width: `${Math.min(100, (user?.daily_chat_count / user?.daily_chat_limit) * 100 || 0)}%` 
                    }}
                  ></div>
                </div>
                <div className="usage-text">
                  {user?.daily_chat_count || 0} / {user?.daily_chat_limit === Infinity ? '无限' : user?.daily_chat_limit || 0}
                </div>
              </div>
              
              <div className="usage-item">
                <div className="usage-label">LIO使用</div>
                <div className="usage-bar">
                  <div 
                    className="usage-progress" 
                    style={{ 
                      width: `${Math.min(100, (user?.daily_lio_count / user?.daily_lio_limit) * 100 || 0)}%` 
                    }}
                  ></div>
                </div>
                <div className="usage-text">
                  {user?.daily_lio_count || 0} / {user?.daily_lio_limit === Infinity ? '无限' : user?.daily_lio_limit || 0}
                </div>
              </div>
            </div>
            
            {user?.personal_invite_code && (
              <div className="invite-code-section">
                <h3>我的邀请码</h3>
                <div className="invite-code-display">
                  {user.personal_invite_code}
                  <button 
                    className="copy-button"
                    onClick={() => {
                      navigator.clipboard.writeText(user.personal_invite_code);
                      setSuccess('邀请码已复制到剪贴板');
                    }}
                  >
                    复制
                  </button>
                </div>
                <p className="invite-code-info">
                  分享此邀请码给朋友，邀请他们加入彩虹城！
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default UserProfile;
