import React, { useState, useEffect } from 'react';
import { Card, Button, Badge, Row, Col, Alert, Modal } from 'react-bootstrap';
import { getUserProfile } from '../../services/user_service';
import { upgradeVIP } from '../../services/vip_service';
import { Link } from 'react-router-dom';
import './VIPMembership.css';

const VIPMembership = () => {
  const [userProfile, setUserProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState(null);

  useEffect(() => {
    const fetchUserProfile = async () => {
      try {
        setLoading(true);
        const profile = await getUserProfile();
        setUserProfile(profile);
      } catch (err) {
        setError('获取用户信息失败，请稍后再试');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, []);

  const handleUpgradeClick = (plan) => {
    setSelectedPlan(plan);
    setShowUpgradeModal(true);
  };

  const handleUpgradeConfirm = async () => {
    try {
      await upgradeVIP(selectedPlan.id);
      // 刷新用户信息
      const profile = await getUserProfile();
      setUserProfile(profile);
      setShowUpgradeModal(false);
      // 显示成功提示
      alert(`成功升级到 ${selectedPlan.name} 会员！`);
    } catch (err) {
      setError('升级失败，请稍后再试');
      console.error(err);
    }
  };

  const vipPlans = [
    {
      id: 'free',
      name: 'Free',
      price: '0',
      features: [
        '每日10次AI对话',
        '1个AI伴侣',
        '不支持LIO频道',
        '不支持唤醒AI',
        '每周10次邀请码'
      ],
      color: 'secondary'
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '39',
      features: [
        '每日50次AI对话',
        '3个AI伴侣',
        '每日10次LIO对话',
        '可唤醒1个AI',
        '每周20次邀请码',
        '可申请推广权限'
      ],
      color: 'info'
    },
    {
      id: 'premium',
      name: 'Premium',
      price: '99',
      features: [
        '每日100次AI对话',
        '5个AI伴侣',
        '每日30次LIO对话',
        '可唤醒2个AI',
        '每周30次邀请码',
        '可申请推广权限'
      ],
      color: 'warning'
    },
    {
      id: 'ultimate',
      name: 'Ultimate',
      price: '199',
      features: [
        '无限AI对话',
        '10个AI伴侣',
        '无限LIO对话',
        '可唤醒5个AI',
        '无限邀请码',
        '可申请推广权限'
      ],
      color: 'danger'
    },
    {
      id: 'team',
      name: 'Team',
      price: '599',
      features: [
        '无限AI对话',
        '20个AI伴侣',
        '无限LIO对话',
        '可唤醒10个AI',
        '无限邀请码',
        '可申请推广权限',
        '团队共享功能'
      ],
      color: 'primary'
    }
  ];

  if (loading) {
    return <div className="text-center p-5">加载中...</div>;
  }

  if (error) {
    return <Alert variant="danger">{error}</Alert>;
  }

  const currentVipLevel = userProfile?.vip_level || 'free';
  const isVip = userProfile?.is_vip || false;
  const vipExpiry = userProfile?.vip_expiry ? new Date(userProfile.vip_expiry) : null;
  const isPromoter = userProfile?.is_promoter || false;
  const canApplyForPromoter = isVip && !isPromoter && ['pro', 'premium', 'ultimate', 'team'].includes(currentVipLevel);
  
  // 检查VIP是否即将到期（30天内）
  const isVipExpiringSoon = vipExpiry && ((new Date(vipExpiry) - new Date()) / (1000 * 60 * 60 * 24) < 30);

  return (
    <div className="vip-membership-container">
      <h2 className="text-center mb-4">VIP会员等级</h2>
      
      {isVip && (
        <Alert variant="success" className="mb-4">
          <strong>当前会员等级：{currentVipLevel}</strong>
          {vipExpiry && (
            <div>到期时间：{vipExpiry.toLocaleDateString()}</div>
          )}
          {isVipExpiringSoon && (
            <div className="mt-2 text-danger">
              <strong>注意：</strong> 您的VIP会员即将到期，请及时续费以保持会员权益和推广资格。
            </div>
          )}
        </Alert>
      )}
      
      {/* 推广权限状态 */}
      {isVip && (
        <Alert variant={isPromoter ? "info" : "warning"} className="mb-4">
          <strong>推广权限状态：</strong> {isPromoter ? "已获得推广权限" : "尚未获得推广权限"}
          {canApplyForPromoter && !isPromoter && (
            <div className="mt-2">
              <Link to="/promoter/apply" className="btn btn-primary btn-sm">
                立即申请推广权限
              </Link>
              <small className="d-block mt-1">
                成为推广用户可以获得用户转化佣金，增加额外收入！
              </small>
            </div>
          )}
          {isPromoter && (
            <div className="mt-2">
              <Link to="/promoter/dashboard" className="btn btn-primary btn-sm">
                进入推广中心
              </Link>
            </div>
          )}
        </Alert>
      )}
      
      <Row className="g-4">
        {vipPlans.map((plan) => (
          <Col key={plan.id} md={6} lg={4}>
            <Card 
              className={`vip-card ${currentVipLevel === plan.id ? 'current-plan' : ''}`}
              border={currentVipLevel === plan.id ? plan.color : ''}
            >
              <Card.Header className={`bg-${plan.color} text-white`}>
                <h3>{plan.name}</h3>
                {currentVipLevel === plan.id && (
                  <Badge bg="light" text="dark">当前等级</Badge>
                )}
              </Card.Header>
              <Card.Body>
                <Card.Title className="price">
                  ¥{plan.price}<span className="period">/月</span>
                </Card.Title>
                <ul className="feature-list">
                  {plan.features.map((feature, index) => (
                    <li key={index}>{feature}</li>
                  ))}
                </ul>
                <Button 
                  variant={plan.color} 
                  className="w-100"
                  disabled={currentVipLevel === plan.id || plan.id === 'free'}
                  onClick={() => handleUpgradeClick(plan)}
                >
                  {currentVipLevel === plan.id ? '当前等级' : '升级'}
                </Button>
              </Card.Body>
            </Card>
          </Col>
        ))}
      </Row>

      {/* 推广权益说明 */}
      {!isPromoter && (
        <div className="mt-5">
          <h3 className="text-center mb-3">推广用户特权</h3>
          <Card className="promoter-benefits">
            <Card.Body>
              <Row>
                <Col md={4} className="text-center mb-3 mb-md-0">
                  <div className="benefit-icon">💰</div>
                  <h5>佣金收入</h5>
                  <p>获得用户转化佣金，最高可达订单金额的30%</p>
                </Col>
                <Col md={4} className="text-center mb-3 mb-md-0">
                  <div className="benefit-icon">🔗</div>
                  <h5>专属推广链接</h5>
                  <p>创建和管理您的专属推广链接，轻松追踪转化</p>
                </Col>
                <Col md={4} className="text-center">
                  <div className="benefit-icon">📊</div>
                  <h5>数据分析</h5>
                  <p>查看详细的推广数据和佣金统计，优化您的推广策略</p>
                </Col>
              </Row>
              {canApplyForPromoter && (
                <div className="text-center mt-4">
                  <Link to="/promoter/apply" className="btn btn-primary">
                    立即申请推广权限
                  </Link>
                </div>
              )}
              {!isVip && (
                <div className="text-center mt-4">
                  <p className="text-muted">升级到VIP会员后即可申请推广权限</p>
                </div>
              )}
            </Card.Body>
          </Card>
        </div>
      )}

      <Modal show={showUpgradeModal} onHide={() => setShowUpgradeModal(false)}>
        <Modal.Header closeButton>
          <Modal.Title>确认升级</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          您确定要升级到 <strong>{selectedPlan?.name}</strong> 会员吗？
          <p className="mt-2">价格：¥{selectedPlan?.price}/月</p>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowUpgradeModal(false)}>
            取消
          </Button>
          <Button variant="primary" onClick={handleUpgradeConfirm}>
            确认升级
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
};

export default VIPMembership;
