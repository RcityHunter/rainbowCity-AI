import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Table, Tabs, Alert, Spin, Typography, Divider, Menu } from 'antd';
import { 
  UserOutlined, 
  TeamOutlined, 
  DollarOutlined, 
  RiseOutlined,
  MessageOutlined,
  AppstoreOutlined,
  SettingOutlined,
  BarsOutlined
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import axios from 'axios';
import './Admin.css';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

/**
 * 管理员仪表盘组件
 * 显示系统概览和各种管理功能入口
 */
const AdminDashboard = ({ user }) => {
  const [loading, setLoading] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [error, setError] = useState(null);

  // 获取仪表盘数据
  useEffect(() => {
    const fetchDashboardData = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/admin/dashboard');
        if (response.data.success) {
          setDashboardData(response.data.dashboard);
        }
      } catch (err) {
        setError('获取仪表盘数据失败，请稍后再试');
        console.error('获取仪表盘数据失败:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  // 渲染统计卡片
  const renderStatsCards = () => {
    if (!dashboardData) return null;

    return (
      <Row gutter={16} className="admin-stats-row">
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="总用户数"
              value={dashboardData.total_users}
              prefix={<UserOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="VIP用户数"
              value={dashboardData.vip_users}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="推广用户数"
              value={dashboardData.promoters}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="转化率"
              value={(dashboardData.vip_users / dashboardData.total_users * 100).toFixed(1)}
              suffix="%"
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染岗位特定数据
  const renderPositionData = () => {
    if (!dashboardData || !dashboardData.position_data) return null;

    // 根据管理员岗位显示不同的数据
    const { position_data } = dashboardData;
    
    if (user.admin_position === 'marketing') {
      // 市场部门数据
      return (
        <Card title="市场数据" className="admin-position-card">
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="今日新增用户" value={position_data.new_users_today} />
            </Col>
            <Col span={8}>
              <Statistic 
                title="转化率" 
                value={position_data.conversion_rate * 100} 
                precision={2}
                suffix="%" 
              />
            </Col>
            <Col span={8}>
              <Statistic title="活动数量" value={position_data.marketing_campaigns.length} />
            </Col>
          </Row>
        </Card>
      );
    } else if (user.admin_position === 'operations') {
      // 运营部门数据
      return (
        <Card title="运营数据" className="admin-position-card">
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="活跃用户" value={position_data.active_users} />
            </Col>
            <Col span={8}>
              <Statistic 
                title="留存率" 
                value={position_data.retention_rate * 100} 
                precision={2}
                suffix="%" 
              />
            </Col>
            <Col span={8}>
              <Statistic title="功能使用量" value={Object.keys(position_data.feature_usage).length} />
            </Col>
          </Row>
        </Card>
      );
    } else if (user.admin_position === 'customer_service') {
      // 客服部门数据
      return (
        <Card title="客服数据" className="admin-position-card">
          <Row gutter={16}>
            <Col span={8}>
              <Statistic title="待处理工单" value={position_data.open_tickets} />
            </Col>
            <Col span={8}>
              <Statistic 
                title="平均响应时间" 
                value={position_data.avg_response_time} 
                suffix="分钟" 
              />
            </Col>
            <Col span={8}>
              <Statistic 
                title="满意度" 
                value={position_data.satisfaction_rate * 100} 
                precision={1}
                suffix="%" 
              />
            </Col>
          </Row>
        </Card>
      );
    } else if (user.admin_position === 'technical') {
      // 技术部门数据
      return (
        <Card title="技术数据" className="admin-position-card">
          <Row gutter={16}>
            <Col span={8}>
              <Statistic 
                title="系统状态" 
                value={position_data.system_status} 
                valueStyle={{ 
                  color: position_data.system_status === 'normal' ? '#52c41a' : '#f5222d' 
                }}
              />
            </Col>
            <Col span={8}>
              <Statistic title="API调用量" value={Object.values(position_data.api_usage).reduce((a, b) => a + b, 0)} />
            </Col>
            <Col span={8}>
              <Statistic 
                title="错误率" 
                value={Object.values(position_data.error_rates).reduce((a, b) => a + b, 0) * 100} 
                precision={2}
                suffix="%" 
              />
            </Col>
          </Row>
        </Card>
      );
    }

    return null;
  };

  // 渲染管理菜单
  const renderAdminMenu = () => {
    return (
      <Card title="管理功能" className="admin-menu-card">
        <Menu mode="vertical">
          <Menu.Item key="users" icon={<UserOutlined />}>
            <Link to="/admin/users">用户管理</Link>
          </Menu.Item>
          <Menu.Item key="promoters" icon={<RiseOutlined />}>
            <Link to="/admin/promoters">推广用户管理</Link>
          </Menu.Item>
          <Menu.Item key="content" icon={<BarsOutlined />}>
            <Link to="/admin/content">内容管理</Link>
          </Menu.Item>
          <Menu.Item key="messages" icon={<MessageOutlined />}>
            <Link to="/admin/messages">消息管理</Link>
          </Menu.Item>
          <Menu.Item key="system" icon={<SettingOutlined />}>
            <Link to="/admin/system">系统设置</Link>
          </Menu.Item>
          <Menu.Item key="apps" icon={<AppstoreOutlined />}>
            <Link to="/admin/apps">应用管理</Link>
          </Menu.Item>
        </Menu>
      </Card>
    );
  };

  // 检查用户是否有管理权限
  if (!user.is_admin) {
    return (
      <div className="admin-container">
        <Card>
          <Title level={4}>权限不足</Title>
          <Text>您没有管理员权限，无法访问此页面。</Text>
        </Card>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="admin-container">
        <Spin tip="加载中..." />
      </div>
    );
  }

  return (
    <div className="admin-container">
      <Title level={3}>管理员仪表盘</Title>
      <Paragraph>
        欢迎回来，{user.display_name || user.username}！您的管理岗位是：
        {user.admin_position === 'marketing' && '市场'}
        {user.admin_position === 'operations' && '运营'}
        {user.admin_position === 'customer_service' && '客服'}
        {user.admin_position === 'technical' && '技术'}
        {user.admin_position === 'management' && '管理员'}
      </Paragraph>
      
      {error && <Alert message={error} type="error" showIcon className="admin-alert" />}
      
      <Divider />
      
      {renderStatsCards()}
      
      <Row gutter={16}>
        <Col xs={24} md={16}>
          {renderPositionData()}
        </Col>
        <Col xs={24} md={8}>
          {renderAdminMenu()}
        </Col>
      </Row>
      
      <Card title="待处理事项" className="admin-tasks-card">
        <Tabs defaultActiveKey="1">
          <TabPane tab="推广用户申请" key="1">
            <div style={{ padding: '10px 0' }}>
              <Alert
                message="有新的推广用户申请待审核"
                description="目前有3个推广用户申请等待您的审核，请及时处理。"
                type="info"
                showIcon
                action={
                  <Button size="small" type="primary">
                    <Link to="/admin/promoters">立即处理</Link>
                  </Button>
                }
              />
            </div>
          </TabPane>
          <TabPane tab="系统通知" key="2">
            <div style={{ padding: '10px 0' }}>
              <Alert
                message="系统更新通知"
                description="系统将于今晚22:00-23:00进行例行维护，请提前做好准备。"
                type="warning"
                showIcon
              />
            </div>
          </TabPane>
          <TabPane tab="用户反馈" key="3">
            <div style={{ padding: '10px 0' }}>
              <Alert
                message="新的用户反馈"
                description="有5条新的用户反馈需要您查看和回复。"
                type="info"
                showIcon
                action={
                  <Button size="small" type="primary">
                    <Link to="/admin/feedback">查看反馈</Link>
                  </Button>
                }
              />
            </div>
          </TabPane>
        </Tabs>
      </Card>
    </div>
  );
};

export default AdminDashboard;
