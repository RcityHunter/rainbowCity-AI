import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Button, Table, Input, Tabs, Form, InputNumber, Alert, Spin, Typography, Divider, message } from 'antd';
import { CopyOutlined, LinkOutlined, UserAddOutlined, DollarOutlined, LineChartOutlined } from '@ant-design/icons';
import axios from 'axios';
import './Promoter.css';

const { Title, Paragraph, Text } = Typography;
const { TabPane } = Tabs;

/**
 * 推广用户仪表盘组件
 * 显示推广数据统计、推广链接管理和佣金提现功能
 */
const PromoterDashboard = ({ user }) => {
  const [loading, setLoading] = useState(false);
  const [promoterStatus, setPromoterStatus] = useState(null);
  const [promoterStats, setPromoterStats] = useState(null);
  const [withdrawing, setWithdrawing] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [withdrawForm] = Form.useForm();

  const [links, setLinks] = useState([]);
  const [loadingLinks, setLoadingLinks] = useState(false);
  const [commissions, setCommissions] = useState([]);
  const [loadingCommissions, setLoadingCommissions] = useState(false);
  const [withdrawals, setWithdrawals] = useState([]);
  const [loadingWithdrawals, setLoadingWithdrawals] = useState(false);
  const [newLinkName, setNewLinkName] = useState('');
  const [creatingLink, setCreatingLink] = useState(false);
  
  // 获取推广用户状态和统计数据
  useEffect(() => {
    const fetchPromoterData = async () => {
      setLoading(true);
      try {
        // 获取推广用户状态
        const statusResponse = await axios.get('/api/promoter/status');
        if (statusResponse.data.success) {
          setPromoterStatus(statusResponse.data.promoter_status);
        }

        // 获取推广统计数据
        const statsResponse = await axios.get('/api/promoter/stats');
        if (statsResponse.data.success) {
          setPromoterStats(statsResponse.data.stats);
        }
        
        // 获取推广链接
        await fetchPromoterLinks();
        
        // 获取佣金记录
        await fetchCommissions();
        
        // 获取提现记录
        await fetchWithdrawals();
      } catch (err) {
        setError('获取推广数据失败，请稍后再试');
        console.error('获取推广数据失败:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPromoterData();
  }, []);
  
  // 获取推广链接
  const fetchPromoterLinks = async () => {
    setLoadingLinks(true);
    try {
      const response = await axios.get('/api/promoter/links');
      if (response.data.success) {
        setLinks(response.data.links);
      }
    } catch (err) {
      console.error('获取推广链接失败:', err);
    } finally {
      setLoadingLinks(false);
    }
  };
  
  // 获取佣金记录
  const fetchCommissions = async () => {
    setLoadingCommissions(true);
    try {
      const response = await axios.get('/api/promoter/commissions');
      if (response.data.success) {
        setCommissions(response.data.commissions);
      }
    } catch (err) {
      console.error('获取佣金记录失败:', err);
    } finally {
      setLoadingCommissions(false);
    }
  };
  
  // 获取提现记录
  const fetchWithdrawals = async () => {
    setLoadingWithdrawals(true);
    try {
      const response = await axios.get('/api/promoter/withdrawals');
      if (response.data.success) {
        setWithdrawals(response.data.withdrawals);
      }
    } catch (err) {
      console.error('获取提现记录失败:', err);
    } finally {
      setLoadingWithdrawals(false);
    }
  };
  
  // 创建新的推广链接
  const createNewLink = async () => {
    if (!newLinkName.trim()) {
      message.error('请输入推广链接名称');
      return;
    }
    
    setCreatingLink(true);
    try {
      const response = await axios.post('/api/promoter/links', {
        name: newLinkName.trim()
      });
      
      if (response.data.success) {
        message.success('推广链接创建成功');
        setNewLinkName('');
        await fetchPromoterLinks();
      }
    } catch (err) {
      message.error(err.response?.data?.message || '创建推广链接失败');
      console.error('创建推广链接失败:', err);
    } finally {
      setCreatingLink(false);
    }
  };
  
  // 更新推广链接状态
  const updateLinkStatus = async (linkId, isActive) => {
    try {
      const response = await axios.put(`/api/promoter/links/${linkId}`, {
        is_active: isActive
      });
      
      if (response.data.success) {
        message.success(`推广链接已${isActive ? '激活' : '停用'}`);
        await fetchPromoterLinks();
      }
    } catch (err) {
      message.error(err.response?.data?.message || '更新推广链接失败');
      console.error('更新推广链接失败:', err);
    }
  };
  
  // 删除推广链接
  const deleteLink = async (linkId) => {
    try {
      const response = await axios.delete(`/api/promoter/links/${linkId}`);
      
      if (response.data.success) {
        message.success('推广链接已删除');
        await fetchPromoterLinks();
      }
    } catch (err) {
      message.error(err.response?.data?.message || '删除推广链接失败');
      console.error('删除推广链接失败:', err);
    }
  };

  // 复制推广链接
  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(
      () => {
        message.success('已复制到剪贴板');
      },
      () => {
        message.error('复制失败，请手动复制');
      }
    );
  };

  // 提交提现申请
  const handleWithdraw = async (values) => {
    setWithdrawing(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/api/promoter/withdraw', values);
      if (response.data.success) {
        setSuccess(response.data.message);
        // 更新推广用户状态
        const statusResponse = await axios.get('/api/promoter/status');
        if (statusResponse.data.success) {
          setPromoterStatus(statusResponse.data.promoter_status);
        }
        withdrawForm.resetFields();
      } else {
        setError(response.data.message || '提现申请失败，请稍后再试');
      }
    } catch (err) {
      setError(err.response?.data?.message || '提现申请失败，请稍后再试');
      console.error('提交提现申请失败:', err);
    } finally {
      setWithdrawing(false);
    }
  };

  // 渲染统计数据卡片
  const renderStatsCards = () => {
    if (!promoterStats) return null;

    return (
      <Row gutter={16} className="promoter-stats-card">
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="推广链接点击"
              value={promoterStats.clicks}
              prefix={<LinkOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="注册用户数"
              value={promoterStats.registrations}
              prefix={<UserAddOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="本月收益"
              value={promoterStats.earnings_this_month}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6}>
          <Card>
            <Statistic
              title="累计收益"
              value={promoterStats.earnings_total}
              precision={2}
              prefix={<DollarOutlined />}
              suffix="元"
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 渲染推广链接表格
  const renderLinksTable = () => {
    const columns = [
      {
        title: '名称',
        dataIndex: 'name',
        key: 'name',
      },
      {
        title: '推广码',
        dataIndex: 'code',
        key: 'code',
      },
      {
        title: '推广链接',
        key: 'url',
        render: (_, record) => {
          const url = `${window.location.origin}/api/promoter/r/${record.code}`;
          return (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Input value={url} readOnly style={{ width: '200px' }} />
              <Button
                icon={<CopyOutlined />}
                onClick={() => copyToClipboard(url)}
                type="text"
                className="promoter-link-copy"
              />
            </div>
          );
        },
      },
      {
        title: '点击数',
        dataIndex: 'clicks',
        key: 'clicks',
      },
      {
        title: '注册数',
        dataIndex: 'registrations',
        key: 'registrations',
      },
      {
        title: '转化数',
        dataIndex: 'conversions',
        key: 'conversions',
      },
      {
        title: '状态',
        dataIndex: 'is_active',
        key: 'is_active',
        render: (isActive) => (
          <Tag color={isActive ? 'green' : 'red'}>
            {isActive ? '活跃' : '停用'}
          </Tag>
        ),
      },
      {
        title: '操作',
        key: 'action',
        render: (_, record) => (
          <div>
            {record.is_active ? (
              <Button 
                size="small" 
                danger 
                onClick={() => updateLinkStatus(record.id, false)}
              >
                停用
              </Button>
            ) : (
              <Button 
                size="small" 
                type="primary" 
                onClick={() => updateLinkStatus(record.id, true)}
              >
                激活
              </Button>
            )}
            <Button 
              size="small" 
              danger 
              style={{ marginLeft: 8 }}
              onClick={() => deleteLink(record.id)}
            >
              删除
            </Button>
          </div>
        ),
      },
    ];

    return (
      <Card 
        title="推广链接管理" 
        className="promoter-links-card"
        extra={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <Input 
              placeholder="输入推广链接名称" 
              value={newLinkName}
              onChange={(e) => setNewLinkName(e.target.value)}
              style={{ width: 200, marginRight: 8 }}
            />
            <Button 
              type="primary" 
              onClick={createNewLink} 
              loading={creatingLink}
            >
              创建新链接
            </Button>
          </div>
        }
      >
        <Table
          columns={columns}
          dataSource={links}
          rowKey="id"
          pagination={false}
          size="middle"
          loading={loadingLinks}
        />
      </Card>
    );
  };

  // 渲染佣金记录表格
  const renderCommissionsTable = () => {
    const columns = [
      {
        title: '时间',
        dataIndex: 'created_at',
        key: 'created_at',
        render: (text) => new Date(text).toLocaleString(),
      },
      {
        title: '来源用户',
        dataIndex: 'source_user_name',
        key: 'source_user_name',
      },
      {
        title: '订单金额',
        dataIndex: 'order_amount',
        key: 'order_amount',
        render: (text) => `¥${text.toFixed(2)}`,
      },
      {
        title: '佣金金额',
        dataIndex: 'commission_amount',
        key: 'commission_amount',
        render: (text) => `¥${text.toFixed(2)}`,
      },
      {
        title: '佣金率',
        dataIndex: 'commission_rate',
        key: 'commission_rate',
        render: (text) => `${(text * 100).toFixed(1)}%`,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        render: (status) => {
          let color = 'blue';
          let text = '处理中';
          
          if (status === 'completed') {
            color = 'green';
            text = '已完成';
          } else if (status === 'failed') {
            color = 'red';
            text = '失败';
          } else if (status === 'pending') {
            color = 'orange';
            text = '待处理';
          }
          
          return <Tag color={color}>{text}</Tag>;
        },
      },
    ];

    return (
      <Card title="佣金记录" className="promoter-commissions-card">
        <Table
          columns={columns}
          dataSource={commissions}
          rowKey="id"
          pagination={{ pageSize: 5 }}
          size="middle"
          loading={loadingCommissions}
        />
      </Card>
    );
  };
  
  // 渲染提现记录表格
  const renderWithdrawalsTable = () => {
    const columns = [
      {
        title: '申请时间',
        dataIndex: 'created_at',
        key: 'created_at',
        render: (text) => new Date(text).toLocaleString(),
      },
      {
        title: '金额',
        dataIndex: 'amount',
        key: 'amount',
        render: (text) => `¥${text.toFixed(2)}`,
      },
      {
        title: '状态',
        dataIndex: 'status',
        key: 'status',
        render: (status) => {
          let color = 'blue';
          let text = '处理中';
          
          if (status === 'completed') {
            color = 'green';
            text = '已完成';
          } else if (status === 'rejected') {
            color = 'red';
            text = '被拒绝';
          } else if (status === 'pending') {
            color = 'orange';
            text = '待处理';
          }
          
          return <Tag color={color}>{text}</Tag>;
        },
      },
      {
        title: '完成时间',
        dataIndex: 'completed_at',
        key: 'completed_at',
        render: (text) => text ? new Date(text).toLocaleString() : '-',
      },
      {
        title: '备注',
        dataIndex: 'remark',
        key: 'remark',
        render: (text) => text || '-',
      },
    ];

    return (
      <Card title="提现记录" className="promoter-withdrawals-card">
        <Table
          columns={columns}
          dataSource={withdrawals}
          rowKey="id"
          pagination={{ pageSize: 5 }}
          size="middle"
          loading={loadingWithdrawals}
        />
      </Card>
    );
  };
  
  // 渲染提现表单
  const renderWithdrawForm = () => {
    if (!promoterStatus) return null;

    return (
      <Card title="佣金提现" className="promoter-withdraw-card">
        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}
        {success && <Alert message={success} type="success" showIcon style={{ marginBottom: 16 }} />}
        
        <div style={{ marginBottom: 16 }}>
          <Text>可提现余额: </Text>
          <Text strong>¥{promoterStatus.available_balance.toFixed(2)}</Text>
        </div>
        
        <Form
          form={withdrawForm}
          layout="vertical"
          onFinish={handleWithdraw}
          className="promoter-withdraw-form"
        >
          <Form.Item
            name="amount"
            label="提现金额"
            rules={[
              { required: true, message: '请输入提现金额' },
              {
                validator: (_, value) => {
                  if (value > 0 && value <= promoterStatus.available_balance) {
                    return Promise.resolve();
                  }
                  return Promise.reject('提现金额必须大于0且不超过可提现余额');
                }
              }
            ]}
          >
            <InputNumber
              min={0.01}
              max={promoterStatus.available_balance}
              precision={2}
              style={{ width: '100%' }}
              placeholder="请输入提现金额"
              prefix="¥"
            />
          </Form.Item>
          
          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={withdrawing}
              disabled={promoterStatus.available_balance <= 0}
              className="promoter-withdraw-button"
              block
            >
              申请提现
            </Button>
          </Form.Item>
        </Form>
      </Card>
    );
  };

  // 渲染推广说明
  const renderPromoterGuide = () => (
    <Card title="推广指南" className="promoter-guide-card">
      <Title level={5}>如何有效推广？</Title>
      <Paragraph>
        <ol>
          <li>分享您的推广链接到社交媒体、博客或个人网站</li>
          <li>向朋友和同事介绍彩虹城AI的优势和特点</li>
          <li>制作教程或评测视频，展示彩虹城AI的功能</li>
          <li>在相关社区和论坛中适当分享您的推广链接</li>
        </ol>
      </Paragraph>
      
      <Title level={5}>推广规则</Title>
      <Paragraph>
        <ul>
          <li>禁止使用欺骗性手段获取点击和注册</li>
          <li>禁止发布虚假或夸大的宣传内容</li>
          <li>禁止在不适当的场合或违反平台规则的情况下推广</li>
          <li>违反推广规则可能导致推广资格被取消</li>
        </ul>
      </Paragraph>
      
      <Alert
        message="佣金结算规则"
        description={`佣金按月结算，每月1日自动计入可提现余额。提现申请审核通过后，款项将在3-5个工作日内转入您的账户。最低提现金额为100元。`}
        type="info"
        showIcon
      />
    </Card>
  );

  if (loading) {
    return (
      <div className="promoter-dashboard">
        <Spin tip="加载中..." />
      </div>
    );
  }

  if (!promoterStatus?.is_promoter) {
    return (
      <div className="promoter-dashboard">
        <Alert
          message="您不是推广用户"
          description="您尚未成为推广用户或推广权限已被冻结，请先申请成为推广用户。"
          type="warning"
          showIcon
          action={
            <Button type="primary" href="/promoter/apply">
              申请成为推广用户
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div className="promoter-dashboard">
      <Title level={3}>推广中心</Title>
      <Paragraph>
        欢迎来到推广中心，您是{promoterStatus.promoter_type === 'individual' ? '个人' : '机构'}推广用户，
        当前佣金比例为{(promoterStatus.commission_rate * 100).toFixed(1)}%
      </Paragraph>
      
      <Divider />
      
      {renderStatsCards()}
      
      <Tabs defaultActiveKey="1">
        <TabPane tab="推广链接" key="1">
          {renderLinksTable()}
        </TabPane>
        <TabPane tab="佣金记录" key="2">
          {renderCommissionsTable()}
        </TabPane>
        <TabPane tab="提现记录" key="3">
          {renderWithdrawalsTable()}
        </TabPane>
        <TabPane tab="佣金提现" key="4">
          {renderWithdrawForm()}
        </TabPane>
        <TabPane tab="推广指南" key="5">
          {renderPromoterGuide()}
        </TabPane>
      </Tabs>
    </div>
  );
};

export default PromoterDashboard;
