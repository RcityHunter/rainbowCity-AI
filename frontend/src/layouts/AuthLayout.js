import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import SignupForm from '../components/auth/SignupForm';
import './AuthLayout.css';

const AuthLayout = ({ children }) => {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();
  const location = useLocation();

  // 根据当前路径设置初始状态
  React.useEffect(() => {
    if (location.pathname === '/login') {
      setIsLogin(true);
    } else if (location.pathname === '/signup') {
      setIsLogin(false);
    }
  }, [location.pathname]);

  const handleLoginSuccess = (user) => {
    // 登录成功后跳转到主页
    navigate('/');
  };

  const handleSignupSuccess = () => {
    // 注册成功后切换到登录页面
    setIsLogin(true);
    navigate('/login');
  };

  const switchToLogin = () => {
    setIsLogin(true);
    navigate('/login');
  };

  const switchToSignup = () => {
    setIsLogin(false);
    navigate('/signup');
  };

  return (
    <div className="auth-layout">
      <div className="auth-background">
        <div className="auth-stars"></div>
        <div className="auth-stars2"></div>
        <div className="auth-stars3"></div>
      </div>
      
      <div className="auth-container">
        <div className="auth-header">
          <Link to="/" className="auth-logo">
            彩虹城
          </Link>
          <div className="auth-subtitle">AI共生社区</div>
        </div>
        
        <div className="auth-content">
          {isLogin ? (
            <LoginForm 
              onLoginSuccess={handleLoginSuccess} 
              onSwitchToSignup={switchToSignup} 
            />
          ) : (
            <SignupForm 
              onSignupSuccess={handleSignupSuccess} 
              onSwitchToLogin={switchToLogin} 
            />
          )}
        </div>
        
        <div className="auth-footer">
          <p>© {new Date().getFullYear()} 彩虹城 Rainbow City. 保留所有权利。</p>
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
