import React, { useState, useRef } from 'react';
import { generateAiId } from '../services/ai_service';
import './AIIDGenerator.css';

const AIIDGenerator = () => {
  const [aiId, setAiId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [visibleNumber, setVisibleNumber] = useState('');
  const [useCustomNumber, setUseCustomNumber] = useState(false);
  const aiIdRef = useRef(null);

  const handleGenerateAiId = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let numberToUse = null;
      
      if (useCustomNumber && visibleNumber) {
        // 验证输入是否为有效数字
        const parsedNumber = parseInt(visibleNumber, 10);
        if (isNaN(parsedNumber) || parsedNumber <= 0) {
          throw new Error('请输入有效的正整数');
        }
        numberToUse = parsedNumber;
      } else {
        // 生成随机的7位数字
        numberToUse = Math.floor(Math.random() * 9000000) + 1000000;
      }
      
      // 使用API生成AI_ID
      const newAiId = await generateAiId(numberToUse);
      setAiId(newAiId);
    } catch (error) {
      console.error('生成AI-ID时出错:', error);
      setError(typeof error === 'string' ? error : '生成AI-ID失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyAiId = () => {
    if (!aiId) return;
    
    navigator.clipboard.writeText(aiId.id)
      .then(() => {
        // 创建复制成功通知
        showNotification('AI-ID已复制到剪贴板');
      })
      .catch(err => {
        console.error('复制文本失败:', err);
        showNotification('复制AI-ID失败', true);
      });
  };

  const showNotification = (message, isError = false) => {
    const notification = document.createElement('div');
    notification.className = `notification ${isError ? 'error' : 'success'}`;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // 2秒后移除通知
    setTimeout(() => {
      notification.classList.add('fade-out');
      setTimeout(() => document.body.removeChild(notification), 300);
    }, 2000);
  };

  return (
    <div className="aiid-generator-container">
      <div className="generator-header">
        <h1>AI-ID 生成器</h1>
        <p className="generator-subtitle">生成一个唯一的AI身份标识符</p>
      </div>
      
      <div className="generator-card">
        <div className="generator-options">
          <div className="option-toggle">
            <label className="toggle-label">
              <input 
                type="checkbox" 
                checked={useCustomNumber} 
                onChange={() => setUseCustomNumber(!useCustomNumber)}
                className="toggle-checkbox"
              />
              <span className="toggle-switch"></span>
              使用自定义编号
            </label>
          </div>
          
          {useCustomNumber && (
            <div className="number-input-container">
              <label htmlFor="visible-number">可视编号:</label>
              <input
                id="visible-number"
                type="number"
                value={visibleNumber}
                onChange={(e) => setVisibleNumber(e.target.value)}
                placeholder="输入正整数"
                min="1"
                className="number-input"
              />
            </div>
          )}
          
          <button 
            className="generate-button" 
            onClick={handleGenerateAiId}
            disabled={loading}
          >
            {loading ? '生成中...' : '生成 AI-ID'}
          </button>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        {aiId && (
          <div className="result-section">
            <h2>生成的 AI-ID</h2>
            <div 
              className="aiid-display" 
              ref={aiIdRef} 
              onClick={handleCopyAiId}
              title="点击复制"
            >
              {aiId.id}
              <span className="copy-icon">📋</span>
            </div>
            <p className="copy-hint">点击上方复制到剪贴板</p>
            
            <div className="aiid-details">
              <div className="detail-item">
                <span className="detail-label">可视编号:</span>
                <span className="detail-value">{aiId.visibleNumber}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">创建时间:</span>
                <span className="detail-value">
                  {new Date(aiId.createdAt).toLocaleString()}
                </span>
              </div>
              {aiId.parts && (
                <>
                  <div className="detail-item">
                    <span className="detail-label">前缀:</span>
                    <span className="detail-value">{aiId.parts.prefix}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">序列号:</span>
                    <span className="detail-value">{aiId.parts.sequenceNumber}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">UUID部分:</span>
                    <span className="detail-value">{aiId.parts.uuid}</span>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
      
      <div className="generator-info">
        <h3>什么是AI-ID?</h3>
        <p>
          AI-ID是彩虹城中每个AI实体的唯一标识符。它由前缀、可视编号和唯一标识符组成，
          确保每个AI在系统中都有独特的身份。生成AI-ID是创建新AI实体的第一步。
        </p>
        
        <h3>如何使用AI-ID?</h3>
        <p>
          生成AI-ID后，您可以将其用于：
        </p>
        <ul>
          <li>创建AI关系</li>
          <li>生成频率编号</li>
          <li>唤醒AI实体</li>
          <li>在彩虹城系统中识别和引用AI</li>
        </ul>
      </div>
    </div>
  );
};

export default AIIDGenerator;
