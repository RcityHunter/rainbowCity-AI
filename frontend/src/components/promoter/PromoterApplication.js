import React, { useState, useEffect } from 'react';
import { Card, Button, Form, Radio, Alert, Spin, Typography, Divider } from 'antd';
import { UserOutlined, TeamOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import './Promoter.css';

const { Title, Paragraph, Text } = Typography;

/**
 * 推广用户申请组件
 * 允许VIP用户申请成为推广用户，选择个人推广或机构推广
 */
const PromoterApplication = ({ user }) => {
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [promoterStatus, setPromoterStatus] = useState(null);
  const [form] = Form.useForm();

  // 获取推广用户状态
  useEffect(() => {
    const fetchPromoterStatus = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/promoter/status');
        if (response.data.success) {
          setPromoterStatus(response.data.promoter_status);
        }
      } catch (err) {
        setError('获取推广用户状态失败，请稍后再试');
        console.error('获取推广用户状态失败:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchPromoterStatus();
  }, []);

  // 提交申请
  const handleSubmit = async (values) => {
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await axios.post('/api/promoter/apply', values);
      if (response.data.success) {
        setSuccess(response.data.message);
        // 重新获取推广状态
        const statusResponse = await axios.get('/api/promoter/status');
        if (statusResponse.data.success) {
          setPromoterStatus(statusResponse.data.promoter_status);
        }
      } else {
        setError(response.data.message || '申请失败，请稍后再试');
      }
    } catch (err) {
      setError(err.response?.data?.message || '申请失败，请稍后再试');
      console.error('提交推广用户申请失败:', err);
    } finally {
      setSubmitting(false);
    }
  };

  // 渲染申请表单
  const renderApplicationForm = () => (
    <Form form={form} layout="vertical" onFinish={handleSubmit}>
      <Form.Item
        name="promoter_type"
        label="推广类型"
        rules={[{ required: true, message: '请选择推广类型' }]}
      >
        <Radio.Group>
          <Radio.Button value="individual">
            <UserOutlined /> 个人推广
          </Radio.Button>
          <Radio.Button value="institution">
            <TeamOutlined /> 机构推广
          </Radio.Button>
        </Radio.Group>
      </Form.Item>

      <Form.Item>
        <Button 
          type="primary" 
          htmlType="submit" 
          loading={submitting}
          disabled={!user.is_vip}
        >
          提交申请
        </Button>
        {!user.is_vip && (
          <Text type="danger" style={{ marginLeft: 10 }}>
            只有VIP用户才能申请成为推广用户
          </Text>
        )}
      </Form.Item>
    </Form>
  );

  // 渲染申请状态
  const renderApplicationStatus = () => {
    if (!promoterStatus) return null;

    if (promoterStatus.is_promoter) {
      return (
        <Alert
          message="推广用户申请已通过"
          description={
            <>
              <p>您已成为{promoterStatus.promoter_type === 'individual' ? '个人' : '机构'}推广用户</p>
              <p>佣金比例: {(promoterStatus.commission_rate * 100).toFixed(1)}%</p>
              <p>累计收益: ¥{promoterStatus.total_earnings.toFixed(2)}</p>
              <p>可提现余额: ¥{promoterStatus.available_balance.toFixed(2)}</p>
              <Button type="primary" href="/promoter/dashboard">
                进入推广中心
              </Button>
            </>
          }
          type="success"
          showIcon
          icon={<CheckCircleOutlined />}
        />
      );
    } else if (promoterStatus.promoter_type) {
      return (
        <Alert
          message="推广用户申请审核中"
          description={
            <>
              <p>您的{promoterStatus.promoter_type === 'individual' ? '个人' : '机构'}推广用户申请正在审核中</p>
              <p>申请时间: {new Date(promoterStatus.application_date).toLocaleString()}</p>
              <p>请耐心等待审核结果，审核通过后您将收到通知</p>
            </>
          }
          type="info"
          showIcon
        />
      );
    }

    return null;
  };

  // 渲染推广用户说明
  const renderPromoterInfo = () => (
    <div className="promoter-info">
      <Title level={4}>推广用户权益</Title>
      <Divider />
      
      <Title level={5}>个人推广</Title>
      <Paragraph>
        <ul>
          <li>获得专属推广链接和推广码</li>
          <li>每成功邀请一位用户注册可获得积分奖励</li>
          <li>邀请用户成为付费会员可获得佣金</li>
          <li>推广佣金可随时提现至您的账户</li>
        </ul>
      </Paragraph>
      
      <Title level={5}>机构推广</Title>
      <Paragraph>
        <ul>
          <li>获得批量推广码和机构专属后台</li>
          <li>更高的佣金比例和更多的推广工具</li>
          <li>专属客户经理一对一服务</li>
          <li>可定制专属推广方案和活动</li>
        </ul>
      </Paragraph>
      
      <Alert
        message="申请条件"
        description="推广用户申请需要您是VIP会员。VIP会员过期后，推广权限将暂时冻结，重新开通VIP后可恢复。"
        type="warning"
      />
    </div>
  );

  if (loading) {
    return (
      <div className="promoter-application-container">
        <Spin tip="加载中..." />
      </div>
    );
  }

  return (
    <div className="promoter-application-container">
      <Card title="推广用户申请" className="promoter-card">
        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}
        {success && <Alert message={success} type="success" showIcon style={{ marginBottom: 16 }} />}
        
        {renderApplicationStatus()}
        
        {!promoterStatus?.is_promoter && !promoterStatus?.promoter_type && renderApplicationForm()}
        
        {renderPromoterInfo()}
      </Card>
    </div>
  );
};

export default PromoterApplication;
