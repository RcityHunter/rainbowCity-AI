import React, { useState } from 'react';
import { register, verifyInviteCode } from '../../services/auth_service';
import './AuthForms.css';

const SignupForm = ({ onSignupSuccess, onSwitchToLogin }) => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    inviteCode: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inviteCodeValid, setInviteCodeValid] = useState(null);
  const [inviteCodeChecking, setInviteCodeChecking] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // 如果修改了邀请码，重置验证状态
    if (name === 'inviteCode') {
      setInviteCodeValid(null);
    }
  };

  const checkInviteCode = async () => {
    if (!formData.inviteCode) return;
    
    setInviteCodeChecking(true);
    try {
      const result = await verifyInviteCode(formData.inviteCode);
      setInviteCodeValid(result.valid);
    } catch (err) {
      setInviteCodeValid(false);
    } finally {
      setInviteCodeChecking(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // 验证密码
    if (formData.password !== formData.confirmPassword) {
      setError('两次输入的密码不一致');
      setLoading(false);
      return;
    }

    // 验证密码强度
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$/;
    if (!passwordRegex.test(formData.password)) {
      setError('密码必须至少8个字符，包含大小写字母和数字');
      setLoading(false);
      return;
    }

    try {
      // 如果有邀请码，先验证邀请码
      if (formData.inviteCode && inviteCodeValid !== true) {
        await checkInviteCode();
        if (inviteCodeValid === false) {
          setError('无效的邀请码');
          setLoading(false);
          return;
        }
      }

      // 提交注册
      const data = await register({
        email: formData.email,
        username: formData.username,
        password: formData.password,
        invite_code: formData.inviteCode || undefined
      });

      setLoading(false);
      if (onSignupSuccess) {
        onSignupSuccess(data);
      }
    } catch (err) {
      setLoading(false);
      setError(typeof err === 'string' ? err : '注册失败，请稍后再试');
    }
  };

  return (
    <div className="auth-form-container">
      <h2>注册</h2>
      {error && <div className="auth-error">{error}</div>}
      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="email">邮箱 *</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            required
            placeholder="请输入您的邮箱"
          />
        </div>
        <div className="form-group">
          <label htmlFor="username">用户名</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            placeholder="请输入您的用户名（可选）"
          />
        </div>
        <div className="form-group">
          <label htmlFor="password">密码 *</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            placeholder="至少8个字符，包含大小写字母和数字"
          />
        </div>
        <div className="form-group">
          <label htmlFor="confirmPassword">确认密码 *</label>
          <input
            type="password"
            id="confirmPassword"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            required
            placeholder="请再次输入密码"
          />
        </div>
        <div className="form-group">
          <label htmlFor="inviteCode">邀请码</label>
          <div className="input-with-button">
            <input
              type="text"
              id="inviteCode"
              name="inviteCode"
              value={formData.inviteCode}
              onChange={handleChange}
              placeholder="如有邀请码请输入"
            />
            {formData.inviteCode && (
              <button 
                type="button" 
                className="verify-button" 
                onClick={checkInviteCode}
                disabled={inviteCodeChecking}
              >
                {inviteCodeChecking ? '验证中...' : '验证'}
              </button>
            )}
          </div>
          {inviteCodeValid === true && (
            <div className="invite-code-valid">邀请码有效</div>
          )}
          {inviteCodeValid === false && (
            <div className="invite-code-invalid">邀请码无效</div>
          )}
        </div>
        <button type="submit" className="auth-button" disabled={loading}>
          {loading ? '注册中...' : '注册'}
        </button>
      </form>
      <div className="auth-links">
        <p>
          已有账号？{' '}
          <button className="text-button" onClick={onSwitchToLogin}>
            立即登录
          </button>
        </p>
      </div>
    </div>
  );
};

export default SignupForm;