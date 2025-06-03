import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Modal, InputNumber, Form, Tag, message, Spin, Typography, Divider } from 'antd';
import { CheckOutlined, CloseOutlined, UserOutlined, TeamOutlined } from '@ant-design/icons';
import axios from 'axios';
import './Admin.css';

const { Title, Text } = Typography;

/**
 * 推广用户申请管理组件
 * 管理员用于审核推广用户申请
 */
const PromoterApplications = ({ user }) => {
  const [loading, setLoading] = useState(false);
  const [applications, setApplications] = useState([]);
  const [approveModalVisible, setApproveModalVisible] = useState(false);
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [currentApplication, setCurrentApplication] = useState(null);
  const [approving, setApproving] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [form] = Form.useForm();

  // 获取推广用户申请列表
  const fetchApplications = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/promoter/applications');
      if (response.data.success) {
        setApplications(response.data.applications);
      }
    } catch (err) {
      message.error('获取推广用户申请列表失败');
      console.error('获取推广用户申请列表失败:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  // 打开审核通过模态框
  const showApproveModal = (application) => {
    setCurrentApplication(application);
    setApproveModalVisible(true);
    form.setFieldsValue({ commission_rate: 0.1 }); // 默认佣金比例10%
  };

  // 打开拒绝申请模态框
  const showRejectModal = (application) => {
    setCurrentApplication(application);
    setRejectModalVisible(true);
  };

  // 审核通过申请
  const handleApprove = async (values) => {
    if (!currentApplication) return;
    
    setApproving(true);
    try {
      const response = await axios.post(`/api/promoter/approve/${currentApplication.user_id}`, {
        commission_rate: values.commission_rate
      });
      
      if (response.data.success) {
        message.success('已通过推广用户申请');
        setApproveModalVisible(false);
        fetchApplications(); // 重新获取申请列表
      } else {
        message.error(response.data.message || '操作失败');
      }
    } catch (err) {
      message.error(err.response?.data?.message || '操作失败');
      console.error('审核通过推广用户申请失败:', err);
    } finally {
      setApproving(false);
    }
  };

  // 拒绝申请
  const handleReject = async () => {
    if (!currentApplication) return;
    
    setRejecting(true);
    try {
      const response = await axios.post(`/api/promoter/reject/${currentApplication.user_id}`);
      
      if (response.data.success) {
        message.success('已拒绝推广用户申请');
        setRejectModalVisible(false);
        fetchApplications(); // 重新获取申请列表
      } else {
        message.error(response.data.message || '操作失败');
      }
    } catch (err) {
      message.error(err.response?.data?.message || '操作失败');
      console.error('拒绝推广用户申请失败:', err);
    } finally {
      setRejecting(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '用户ID',
      dataIndex: 'user_id',
      key: 'user_id',
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '显示名称',
      dataIndex: 'display_name',
      key: 'display_name',
    },
    {
      title: 'VIP等级',
      dataIndex: 'vip_level',
      key: 'vip_level',
      render: (text) => <Tag color="gold">{text}</Tag>,
    },
    {
      title: '推广类型',
      dataIndex: 'promoter_type',
      key: 'promoter_type',
      render: (text) => {
        if (text === 'individual') {
          return <Tag icon={<UserOutlined />} color="blue">个人推广</Tag>;
        } else if (text === 'institution') {
          return <Tag icon={<TeamOutlined />} color="purple">机构推广</Tag>;
        }
        return text;
      },
    },
    {
      title: '申请时间',
      dataIndex: 'application_date',
      key: 'application_date',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <div className="promoter-action-buttons">
          <Button
            type="primary"
            icon={<CheckOutlined />}
            onClick={() => showApproveModal(record)}
          >
            通过
          </Button>
          <Button
            danger
            icon={<CloseOutlined />}
            onClick={() => showRejectModal(record)}
          >
            拒绝
          </Button>
        </div>
      ),
    },
  ];

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

  return (
    <div className="admin-container">
      <Card title="推广用户申请管理" extra={<Button onClick={fetchApplications}>刷新</Button>}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin tip="加载中..." />
          </div>
        ) : (
          <Table
            columns={columns}
            dataSource={applications}
            rowKey="user_id"
            pagination={{ pageSize: 10 }}
            className="promoter-application-table"
          />
        )}
      </Card>

      {/* 审核通过模态框 */}
      <Modal
        title="通过推广用户申请"
        visible={approveModalVisible}
        onCancel={() => setApproveModalVisible(false)}
        footer={null}
      >
        <Form form={form} layout="vertical" onFinish={handleApprove}>
          <Form.Item
            name="commission_rate"
            label="佣金比例"
            rules={[
              { required: true, message: '请设置佣金比例' },
              { type: 'number', min: 0.01, max: 0.5, message: '佣金比例必须在1%到50%之间' }
            ]}
            extra="请设置该推广用户的佣金比例，范围为1%到50%"
          >
            <InputNumber
              min={0.01}
              max={0.5}
              step={0.01}
              precision={2}
              style={{ width: '100%' }}
              formatter={(value) => `${(value * 100).toFixed(1)}%`}
              parser={(value) => value.replace('%', '') / 100}
            />
          </Form.Item>

          <div style={{ textAlign: 'right' }}>
            <Button style={{ marginRight: 8 }} onClick={() => setApproveModalVisible(false)}>
              取消
            </Button>
            <Button type="primary" htmlType="submit" loading={approving}>
              确认通过
            </Button>
          </div>
        </Form>
      </Modal>

      {/* 拒绝申请模态框 */}
      <Modal
        title="拒绝推广用户申请"
        visible={rejectModalVisible}
        onCancel={() => setRejectModalVisible(false)}
        onOk={handleReject}
        okText="确认拒绝"
        cancelText="取消"
        okButtonProps={{ loading: rejecting, danger: true }}
      >
        <p>您确定要拒绝该用户的推广申请吗？</p>
        {currentApplication && (
          <div>
            <p><strong>用户ID:</strong> {currentApplication.user_id}</p>
            <p><strong>用户名:</strong> {currentApplication.username}</p>
            <p><strong>推广类型:</strong> {currentApplication.promoter_type === 'individual' ? '个人推广' : '机构推广'}</p>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default PromoterApplications;
