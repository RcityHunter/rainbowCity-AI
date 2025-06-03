import React, { useState, useEffect } from 'react';
import { getVIPPlans, createCheckoutSession } from '../../services/vip_service';
import { getUserProfile } from '../../services/auth_service';
import './VIPPlans.css';

const VIPPlans = () => {
  const [plans, setPlans] = useState([]);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [selectedInterval, setSelectedInterval] = useState('monthly');
  const [processingPayment, setProcessingPayment] = useState(false);

  // 加载VIP计划和用户信息
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // 先获取用户信息
        let userData;
        try {
          userData = await getUserProfile();
          console.log('User profile loaded:', userData);
          setUser(userData);
        } catch (userErr) {
          console.error('获取用户信息失败:', userErr);
          // 继续加载VIP计划，即使用户信息加载失败
        }
        
        // 然后获取VIP计划
        try {
          const plansData = await getVIPPlans();
          console.log('VIP plans loaded:', plansData);
          
          // 确保plansData是数组
          const plansArray = Array.isArray(plansData) ? plansData : [];
          setPlans(plansArray);
          
          // 默认选择比当前用户VIP等级高一级的计划
          if (userData && plansArray.length > 0) {
            const currentLevel = userData.vip_level || 'free';
            const levels = ['free', 'basic', 'pro', 'premium'];
            const currentIndex = levels.indexOf(currentLevel);
            
            if (currentIndex < levels.length - 1) {
              const nextLevel = levels[currentIndex + 1];
              const nextPlan = plansArray.find(plan => plan.level === nextLevel);
              if (nextPlan) {
                setSelectedPlan(nextPlan);
              } else {
                setSelectedPlan(plansArray[0]);
              }
            } else {
              setSelectedPlan(plansArray[0]);
            }
          } else if (plansArray.length > 0) {
            setSelectedPlan(plansArray[0]);
          }
        } catch (plansErr) {
          console.error('获取VIP计划失败:', plansErr);
          setError('无法加载VIP计划信息，请稍后再试');
        }
      } catch (err) {
        setError('获取VIP计划信息失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);

  // 处理计划选择
  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan);
  };

  // 处理时间间隔选择
  const handleIntervalChange = (interval) => {
    setSelectedInterval(interval);
  };

  // 处理支付
  const handleCheckout = async () => {
    if (!selectedPlan) return;
    
    try {
      setProcessingPayment(true);
      const checkoutUrl = await createCheckoutSession(selectedPlan.level, selectedInterval);
      window.location.href = checkoutUrl;
    } catch (err) {
      setError('创建支付会话失败');
      console.error(err);
      setProcessingPayment(false);
    }
  };

  // 计算节省金额（年付相比月付）
  const calculateSavings = (plan) => {
    if (!plan || !plan.prices) return 0;
    
    const monthlyPrice = plan.prices.monthly / 100;
    const yearlyPrice = plan.prices.yearly / 100;
    const monthlyCost = monthlyPrice * 12;
    
    return (monthlyCost - yearlyPrice).toFixed(2);
  };

  // 渲染价格
  const renderPrice = (amount) => {
    return `¥${(amount / 100).toFixed(2)}`;
  };

  // 渲染加载状态
  if (loading) {
    return <div className="loading-container">加载中...</div>;
  }

  // 渲染错误状态
  if (error) {
    return <div className="error-container">{error}</div>;
  }

  return (
    <div className="vip-plans-container">
      <div className="vip-header">
        <h1>升级您的彩虹城体验</h1>
        <p className="vip-subtitle">选择适合您的VIP计划，解锁更多功能和权限</p>
      </div>
      
      {user && user.vip_level && user.vip_level !== 'free' && (
        <div className="current-plan-info">
          <div className="current-plan-badge">
            当前计划: <span>{user.vip_level.toUpperCase()} VIP</span>
          </div>
          {user.vip_expiry && (
            <div className="expiry-info">
              到期时间: {new Date(user.vip_expiry).toLocaleDateString()}
            </div>
          )}
        </div>
      )}
      
      <div className="interval-selector">
        <button 
          className={selectedInterval === 'monthly' ? 'active' : ''}
          onClick={() => handleIntervalChange('monthly')}
        >
          月付
        </button>
        <button 
          className={selectedInterval === 'yearly' ? 'active' : ''}
          onClick={() => handleIntervalChange('yearly')}
        >
          年付
          <span className="save-badge">省钱</span>
        </button>
      </div>
      
      <div className="plans-grid">
        {plans.filter(plan => plan.level !== 'free').map((plan) => (
          <div 
            key={plan.level}
            className={`plan-card ${selectedPlan?.level === plan.level ? 'selected' : ''} ${plan.level}`}
            onClick={() => handlePlanSelect(plan)}
          >
            <div className="plan-header">
              <h2>{plan.name}</h2>
              <div className="plan-price">
                <span className="price">{renderPrice(plan.prices[selectedInterval])}</span>
                <span className="interval">/{selectedInterval === 'monthly' ? '月' : '年'}</span>
              </div>
              {selectedInterval === 'yearly' && (
                <div className="savings">节省 ¥{calculateSavings(plan)}</div>
              )}
            </div>
            
            <div className="plan-features">
              <h3>包含功能</h3>
              <ul>
                {plan.features.map((feature, index) => (
                  <li key={index}>
                    <span className="feature-icon">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>
            </div>
            
            <div className="plan-limits">
              <div className="limit-item">
                <span className="limit-label">AI伴侣上限</span>
                <span className="limit-value">{plan.ai_companions_limit}</span>
              </div>
              <div className="limit-item">
                <span className="limit-label">可唤醒AI上限</span>
                <span className="limit-value">{plan.ai_awakener_limit}</span>
              </div>
              <div className="limit-item">
                <span className="limit-label">每日对话次数</span>
                <span className="limit-value">
                  {plan.daily_chat_limit === Infinity ? '无限' : plan.daily_chat_limit}
                </span>
              </div>
              <div className="limit-item">
                <span className="limit-label">每日LIO使用</span>
                <span className="limit-value">
                  {plan.daily_lio_limit === Infinity ? '无限' : plan.daily_lio_limit}
                </span>
              </div>
              <div className="limit-item">
                <span className="limit-label">每周邀请码</span>
                <span className="limit-value">{plan.weekly_invite_limit}</span>
              </div>
            </div>
            
            <button 
              className={`select-plan-button ${selectedPlan?.level === plan.level ? 'selected' : ''}`}
              onClick={(e) => {
                e.stopPropagation();
                handlePlanSelect(plan);
              }}
            >
              {selectedPlan?.level === plan.level ? '已选择' : '选择计划'}
            </button>
          </div>
        ))}
      </div>
      
      {selectedPlan && (
        <div className="checkout-section">
          <div className="selected-plan-summary">
            <div className="summary-header">
              <h3>已选择: {selectedPlan.name}</h3>
              <div className="summary-price">
                {renderPrice(selectedPlan.prices[selectedInterval])} / {selectedInterval === 'monthly' ? '月' : '年'}
              </div>
            </div>
            
            <div className="summary-details">
              <p>
                {selectedInterval === 'monthly' ? '月付订阅' : '年付订阅'}，随时可取消。
                {user && user.vip_level && user.vip_level !== 'free' ? 
                  ' 您当前的计划将被新计划替代，新计划将在当前计划到期后生效。' : 
                  ' 订阅将在付款后立即生效。'}
              </p>
            </div>
          </div>
          
          <button 
            className="checkout-button"
            onClick={handleCheckout}
            disabled={processingPayment}
          >
            {processingPayment ? '处理中...' : '立即购买'}
          </button>
        </div>
      )}
      
      <div className="vip-faq">
        <h2>常见问题</h2>
        
        <div className="faq-item">
          <h3>如何取消订阅？</h3>
          <p>您可以随时在个人资料页面取消订阅。取消后，您的VIP权益将持续到当前结算周期结束。</p>
        </div>
        
        <div className="faq-item">
          <h3>支持哪些支付方式？</h3>
          <p>我们支持微信支付、支付宝以及主流信用卡支付。</p>
        </div>
        
        <div className="faq-item">
          <h3>升级或降级计划如何处理？</h3>
          <p>升级计划将立即生效，并按比例收取差价。降级计划将在当前结算周期结束后生效。</p>
        </div>
        
        <div className="faq-item">
          <h3>VIP权益有什么用？</h3>
          <p>VIP权益可以让您拥有更多的AI伴侣、更高的每日使用限制，以及独家功能如LIO通道和高级AI唤醒能力。</p>
        </div>
      </div>
    </div>
  );
};

export default VIPPlans;
