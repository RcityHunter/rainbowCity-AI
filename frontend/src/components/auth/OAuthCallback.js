import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { handleGoogleCallback, handleGithubCallback } from '../../services/auth_service';
import LoadingSpinner from '../common/LoadingSpinner';
import './OAuthCallback.css';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadingStage, setLoadingStage] = useState(0); // 0: 初始化, 1: 验证中, 2: 获取用户信息, 3: 完成
  const [provider, setProvider] = useState(null);

  // 使用 useRef 来跟踪授权码是否已经被处理，防止重复处理
  const codeProcessed = useRef(false);

  useEffect(() => {
    // 防止重复处理授权码
    if (codeProcessed.current) {
      console.log('Authorization code already processed, skipping');
      return;
    }
    
    const processOAuthCallback = async () => {
      try {
        // 阶段 0: 初始化 - 立即获取授权码，减少延迟
        const searchParams = new URLSearchParams(location.search);
        const code = searchParams.get('code');
        const error = searchParams.get('error');
        const errorDescription = searchParams.get('error_description');
        
        // 标记授权码已处理，防止重复处理
        codeProcessed.current = true;
        console.log('Marking authorization code as processed to prevent duplicate processing');
        
        const currentProvider = location.pathname.includes('google') ? 'google' : 
                              location.pathname.includes('github') ? 'github' : null;
        
        setProvider(currentProvider);

        // 检查 GitHub 或 Google 直接返回的错误
        if (error) {
          console.error(`OAuth provider returned error: ${error}`, errorDescription);
          throw new Error(errorDescription || `认证服务返回错误: ${error}`);
        }

        if (!code || !currentProvider) {
          throw new Error('缺少必要的授权参数');
        }
        
        // 记录授权码信息（不记录完整授权码）
        console.log(`Received ${currentProvider} authorization code: ${code.substring(0, 5)}...`);
        console.log(`Authorization code length: ${code.length}`);
        
        // 优先处理：立即发送授权码到后端，减少授权码过期风险
        let userData;
        try {
          console.log(`立即处理${currentProvider}授权码，避免过期`);
          // 立即处理授权码，不等待动画
          if (currentProvider === 'google') {
            userData = await handleGoogleCallback(code);
          } else if (currentProvider === 'github') {
            userData = await handleGithubCallback(code);
          }
          
          if (!userData) {
            throw new Error('未能获取用户信息');
          }
          
          // 授权码处理成功后，再显示UI动画
          // 阶段 1: 验证授权码 (已完成，但为了UI流畅性显示动画)
          setLoadingStage(1);
          await new Promise(resolve => setTimeout(resolve, 400)); // 减少延迟时间
          
          // 阶段 2: 获取用户信息 (已完成，但为了UI流畅性显示动画)
          setLoadingStage(2);
          await new Promise(resolve => setTimeout(resolve, 400)); // 减少延迟时间
          
        } catch (callbackError) {
          console.error(`${currentProvider} callback error:`, callbackError);
          
          // 检查是否是授权码过期或无效的错误
          if (callbackError.response && callbackError.response.data) {
            const errorData = callbackError.response.data;
            
            if (errorData.error === 'oauth_token_error' || 
                errorData.details?.error_type === 'bad_verification_code') {
              throw new Error('授权码已过期或无效，请重新登录');
            }
            
            if (errorData.message) {
              throw new Error(errorData.message);
            }
          }
          
          throw callbackError;
        }
        
        // 阶段 3: 完成登录
        setLoadingStage(3);
        await new Promise(resolve => setTimeout(resolve, 600)); // 减少延迟时间

        // 登录成功，重定向到首页
        navigate('/', { replace: true });
      } catch (err) {
        console.error('OAuth callback error:', err);
        
        // 提取错误消息
        let errorMessage;
        if (typeof err === 'string') {
          errorMessage = err;
        } else if (err.message) {
          errorMessage = err.message;
        } else if (err.response && err.response.data && err.response.data.message) {
          errorMessage = err.response.data.message;
        } else {
          errorMessage = '第三方登录失败，请稍后再试';
        }
        
        setError(errorMessage);
        
        // 登录失败，3秒后重定向到登录页
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 3000);
      } finally {
        setLoading(false);
      }
    };

    processOAuthCallback();
  }, [location, navigate]);
  
  // 根据加载阶段获取显示消息
  const getLoadingMessage = () => {
    switch(loadingStage) {
      case 0:
        return '正在初始化登录流程...';
      case 1:
        return `正在验证${provider === 'google' ? 'Google' : 'GitHub'}授权码...`;
      case 2:
        return '正在获取用户信息...';
      case 3:
        return '登录成功，即将进入系统...';
      default:
        return '登录中，请稍候...';
    }
  };

  return (
    <div className="oauth-callback-container">
      {loading ? (
        <div className="oauth-loading-content">
          <div className="oauth-logo-container">
            {provider && (
              <div className={`oauth-provider-logo ${provider}`}>
                {provider === 'google' ? (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12.545,10.239v3.821h5.445c-0.712,2.315-2.647,3.972-5.445,3.972c-3.332,0-6.033-2.701-6.033-6.032s2.701-6.032,6.033-6.032c1.498,0,2.866,0.549,3.921,1.453l2.814-2.814C17.503,2.988,15.139,2,12.545,2C7.021,2,2.543,6.477,2.543,12s4.478,10,10.002,10c8.396,0,10.249-7.85,9.426-11.748L12.545,10.239z"/>
                  </svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                )}
              </div>
            )}
            <div className="app-logo">彩虹城</div>
          </div>
          
          <div className="loading-message">{getLoadingMessage()}</div>
          
          <div className="loading-progress">
            <div className="progress-container">
              <div className="progress-bar" style={{ width: `${(loadingStage + 1) * 25}%` }}></div>
            </div>
            <div className="loading-spinner-container">
              <LoadingSpinner size="large" color="primary" />
            </div>
          </div>
          
          <div className="loading-steps">
            <div className={`loading-step ${loadingStage >= 0 ? 'active' : ''} ${loadingStage > 0 ? 'completed' : ''}`}>
              <div className="step-indicator">1</div>
              <div className="step-label">初始化</div>
            </div>
            <div className={`loading-step ${loadingStage >= 1 ? 'active' : ''} ${loadingStage > 1 ? 'completed' : ''}`}>
              <div className="step-indicator">2</div>
              <div className="step-label">验证授权</div>
            </div>
            <div className={`loading-step ${loadingStage >= 2 ? 'active' : ''} ${loadingStage > 2 ? 'completed' : ''}`}>
              <div className="step-indicator">3</div>
              <div className="step-label">获取信息</div>
            </div>
            <div className={`loading-step ${loadingStage >= 3 ? 'active' : ''}`}>
              <div className="step-indicator">4</div>
              <div className="step-label">完成登录</div>
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="oauth-error-message">
          <div className="error-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
          </div>
          <h2>登录失败</h2>
          <p className="error-details">{error}</p>
          <p className="redirect-message">即将返回登录页面...</p>
          <div className="loading-spinner-small">
            <LoadingSpinner size="small" color="primary" />
          </div>
        </div>
      ) : (
        <div className="oauth-success-message">
          <div className="success-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <h2>登录成功</h2>
          <p className="success-details">身份验证已完成</p>
          <p className="redirect-message">正在跳转到首页...</p>
          <div className="loading-spinner-small">
            <LoadingSpinner size="small" color="primary" />
          </div>
        </div>
      )}
    </div>
  );
};

export default OAuthCallback;
