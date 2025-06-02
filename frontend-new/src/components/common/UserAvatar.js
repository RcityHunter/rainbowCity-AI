import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { logout, getCurrentUser } from '../../services/auth_service';
import ReactDOM from 'react-dom';
import './UserAvatar.css';

const UserAvatar = () => {
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState(null);
  const menuRef = useRef(null);
  const avatarRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    // 获取当前用户信息
    const currentUser = getCurrentUser();
    setUser(currentUser);

    // 点击外部关闭菜单
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const toggleMenu = () => {
    setMenuOpen(!menuOpen);
  };

  const handleLogout = () => {
    logout();
    navigate('/');
    window.location.reload(); // 刷新页面以更新登录状态
  };

  // 如果没有用户信息，返回null
  if (!user) return null;

  // 获取用户头像或使用默认头像
  const userInitial = user.name ? user.name.charAt(0).toUpperCase() : 'U';
  const avatarUrl = user.avatar_url;

  // 创建下拉菜单渲染函数
  const renderMenu = () => {
    if (!menuOpen || !avatarRef.current) return null;
    
    // 获取头像元素的位置信息
    const avatarRect = avatarRef.current.getBoundingClientRect();
    
    // 计算下拉菜单的位置
    const menuStyle = {
      position: 'fixed',
      top: avatarRect.bottom + 8,
      right: window.innerWidth - avatarRect.right,
      zIndex: 9999,
      width: '200px',
      padding: 0,
      boxSizing: 'border-box',
      overflowX: 'hidden',
      backgroundColor: '#202123',
      borderRadius: '6px',
      boxShadow: '0 2px 10px rgba(0, 0, 0, 0.5)',
      border: '1px solid #4d4d4f',
      maxHeight: 'calc(100vh - 100px)',
      overflowY: 'auto'
    };
    
    // 使用Portal将菜单渲染到body下，完全脱离文档流
    return ReactDOM.createPortal(
      <div className="user-menu user-menu-fixed" style={menuStyle} ref={menuRef}>
        <ul className="menu-items full-width">
          <li className="user-email-item">
            <div className="user-email">{user.email}</div>
          </li>
          <div className="menu-divider"></div>
          <li className="menu-item-container">
            <Link to="/dashboard" className="menu-item">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <circle cx="12" cy="12" r="4"></circle>
                </svg>
              </span>
              <span className="menu-text">开始套餐</span>
            </Link>
          </li>
          <li>
            <Link to="/dashboard/ai-relationships" className="menu-item">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path>
                  <circle cx="9" cy="7" r="4"></circle>
                  <path d="M22 21v-2a4 4 0 0 0-3-3.87"></path>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                </svg>
              </span>
              自定义彩虹城 AI
            </Link>
          </li>
          <li>
            <Link to="/dashboard/profile" className="menu-item">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="3"></circle>
                  <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
                </svg>
              </span>
              设置
            </Link>
          </li>
          <li>
            <Link to="/dashboard/vip" className="menu-item">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect>
                  <path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01M8 12h.01M12 12h.01M16 12h.01M7 16h10"></path>
                </svg>
              </span>
              键盘快捷方式
            </Link>
          </li>
          <li>
            <button className="menu-item text-button">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              </span>
              帮助与常见问题解答
            </button>
          </li>
          <li>
            <button className="menu-item text-button">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
              </span>
              发行说明
            </button>
          </li>
          <li>
            <button className="menu-item text-button">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                </svg>
              </span>
              条款与政策
            </button>
          </li>
          <li>
            <button className="menu-item text-button">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"></circle>
                  <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                </svg>
              </span>
              获取彩虹城 AI 搜索扩展程序
            </button>
          </li>
          
          <div className="menu-divider"></div>
          
          <li>
            <button onClick={handleLogout} className="menu-item text-button">
              <span className="menu-icon-box">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                  <polyline points="16 17 21 12 16 7"></polyline>
                  <line x1="21" y1="12" x2="9" y2="12"></line>
                </svg>
              </span>
              注销
            </button>
          </li>
        </ul>
      </div>,
      document.body
    );
  };

  return (
    <div className="user-avatar-container">
      <div className="avatar-wrapper" onClick={toggleMenu} ref={avatarRef}>
        {avatarUrl ? (
          <img src={avatarUrl} alt="User Avatar" className="user-avatar" />
        ) : (
          <div className="user-avatar-placeholder">
            {userInitial}
          </div>
        )}
      </div>
      
      {renderMenu()}
    </div>
  );
};

export default UserAvatar;
