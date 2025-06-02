import React, { useState } from 'react';
import { login } from '../../services/auth_service';
import './AuthForms.css';

const LoginForm = ({ onLoginSuccess, onSwitchToSignup }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
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
          />
        </div>
        <button type="submit" className="auth-button" disabled={loading}>
          {loading ? '登录中...' : '登录'}
        </button>
      </form>
      <div className="auth-links">
        <p>
          还没有账号？{' '}
          <button className="text-button" onClick={onSwitchToSignup}>
            立即注册
          </button>
        </p>
      </div>
    </div>
  );
};

export default LoginForm;