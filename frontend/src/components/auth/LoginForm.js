import React, { useState, useEffect } from 'react';
import { login, handleGoogleCallback, handleGithubCallback } from '../../services/auth_service';
import SocialLoginButtons from './SocialLoginButtons';
import LoadingSpinner from '../common/LoadingSpinner';
import LoadingOverlay from '../common/LoadingOverlay';
import './AuthForms.css';

const LoginForm = ({ onLoginSuccess, onSwitchToSignup }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(false);
  const [error, setError] = useState(null);
  const [loadingMessage, setLoadingMessage] = useState('登录中...');
  
  // 处理OAuth回调
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const provider = urlParams.get('provider');
    
    if (code && provider) {
      const handleOAuthCallback = async () => {
        setOauthLoading(true);
        setLoadingMessage(`正在通过${provider === 'google' ? 'Google' : 'GitHub'}验证您的身份...`);
        setError(null);
        
        try {
          let data;
          if (provider === 'google') {
            data = await handleGoogleCallback(code);
          } else if (provider === 'github') {
            data = await handleGithubCallback(code);
          }
          
          setOauthLoading(false);
          if (onLoginSuccess && data?.user) {
            onLoginSuccess(data.user);
          }
          
          // 清除URL中的查询参数
          window.history.replaceState({}, document.title, window.location.pathname);
        } catch (err) {
          setOauthLoading(false);
          setError(typeof err === 'string' ? err : '第三方登录失败，请稍后再试');
        }
      };
      
      handleOAuthCallback();
    }
  }, [onLoginSuccess]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setLoadingMessage('正在验证您的登录信息...');
    setError(null);

    try {
      const data = await login(email, password);
      setLoading(false);
      if (onLoginSuccess) {
        onLoginSuccess(data.user);
      }
    } catch (err) {
      setLoading(false);
      setError(typeof err === 'string' ? err : '登录失败，请检查邮箱和密码');
    }
  };

  return (
    <div className="auth-form-container">
      {/* 全屏加载覆盖层 */}
      {(loading || oauthLoading) && <LoadingOverlay message={loadingMessage} />}
      
      <h2>登录</h2>
      {error && <div className="auth-error">{error}</div>}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="email">邮箱</label>
          <input
            type="email"
            id="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="请输入您的邮箱"
            disabled={loading || oauthLoading}
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">密码</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            placeholder="请输入您的密码"
            disabled={loading || oauthLoading}
          />
        </div>
        <button type="submit" className="auth-button" disabled={loading || oauthLoading}>
          {loading ? (
            <div className="button-loading">
              <LoadingSpinner size="small" color="white" />
              <span>登录中</span>
            </div>
          ) : '登录'}
        </button>
      </form>
      <SocialLoginButtons disabled={loading || oauthLoading} />
      
      <div className="auth-links">
        <p>
          还没有账号？{' '}
          <button className="text-button" onClick={onSwitchToSignup} disabled={loading || oauthLoading}>
            立即注册
          </button>
        </p>
      </div>
    </div>
  );
};

export default LoginForm;