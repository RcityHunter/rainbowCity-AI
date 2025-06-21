import React, { useEffect, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { handleGoogleCallback, handleGithubCallback } from '../../services/auth_service';

const OAuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const processOAuthCallback = async () => {
      try {
        const searchParams = new URLSearchParams(location.search);
        const code = searchParams.get('code');
        const provider = location.pathname.includes('google') ? 'google' : 
                        location.pathname.includes('github') ? 'github' : null;

        if (!code || !provider) {
          throw new Error('缺少必要的授权参数');
        }

        let userData;
        if (provider === 'google') {
          userData = await handleGoogleCallback(code);
        } else if (provider === 'github') {
          userData = await handleGithubCallback(code);
        }

        // 登录成功，重定向到首页
        navigate('/', { replace: true });
      } catch (err) {
        console.error('OAuth callback error:', err);
        setError(typeof err === 'string' ? err : '第三方登录失败，请稍后再试');
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

  return (
    <div className="oauth-callback-container" style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: '#121212',
      color: '#fff'
    }}>
      {loading ? (
        <div className="loading-spinner">
          <div style={{ fontSize: '24px', marginBottom: '20px' }}>登录中，请稍候...</div>
          <div className="spinner" style={{
            width: '50px',
            height: '50px',
            border: '5px solid rgba(255, 255, 255, 0.3)',
            borderRadius: '50%',
            borderTop: '5px solid #fff',
            animation: 'spin 1s linear infinite'
          }}></div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>
      ) : error ? (
        <div className="error-message" style={{ color: '#ff6b6b', textAlign: 'center', padding: '20px' }}>
          <h2>登录失败</h2>
          <p>{error}</p>
          <p>即将返回登录页面...</p>
        </div>
      ) : (
        <div className="success-message" style={{ textAlign: 'center', padding: '20px' }}>
          <h2>登录成功</h2>
          <p>正在跳转到首页...</p>
        </div>
      )}
    </div>
  );
};

export default OAuthCallback;
