import React from 'react';
import { BrowserRouter as Router, Route, Routes, Navigate } from 'react-router-dom';

// 布局组件
import MainLayout from './layouts/MainLayout';
import AuthLayout from './layouts/AuthLayout';

// 页面组件
import Home from './pages/Home';
import AIIDGenerator from './pages/AIIDGenerator';
import FrequencyGenerator from './pages/FrequencyGenerator';

// 认证组件
import LoginForm from './components/auth/LoginForm';
import SignupForm from './components/auth/SignupForm';

// 用户组件
import UserProfile from './components/user/UserProfile';
import VIPPlans from './components/vip/VIPPlans';
import AIRelationships from './components/ai/AIRelationships';
import PromoterDashboard from './components/promoter/PromoterDashboard';
import PromoterApplication from './components/promoter/PromoterApplication';

// AI聊天组件
import AiChat from './components/AiChat';

// 认证服务
import { isAuthenticated } from './services/auth_service';

// 受保护的路由组件
const ProtectedRoute = ({ children }) => {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

// 游客路由组件（已登录用户会被重定向到首页）
const GuestRoute = ({ children }) => {
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }
  return children;
};

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        {/* 认证路由 */}
        <Route path="/login" element={
          <GuestRoute>
            <AuthLayout>
              <LoginForm />
            </AuthLayout>
          </GuestRoute>
        } />
        <Route path="/signup" element={
          <GuestRoute>
            <AuthLayout>
              <SignupForm />
            </AuthLayout>
          </GuestRoute>
        } />
        
        {/* 公开路由 - 不需要登录 */}
        <Route path="/" element={<Home />} />
        <Route path="/ai-chat" element={<AiChat />} />
        
        {/* 需要登录的路由 */}
        <Route path="/dashboard" element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }>
          <Route index element={<Home />} />
          <Route path="ai-id-generator" element={<AIIDGenerator />} />
          <Route path="frequency-generator" element={<FrequencyGenerator />} />
          <Route path="profile" element={<UserProfile />} />
          <Route path="vip" element={<VIPPlans />} />
          <Route path="ai-relationships" element={<AIRelationships />} />
          <Route path="promoter/dashboard" element={<PromoterDashboard />} />
          <Route path="promoter/apply" element={<PromoterApplication />} />
        </Route>
        
        {/* 404路由 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default AppRoutes;