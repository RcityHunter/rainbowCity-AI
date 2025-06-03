import React, { useState, useRef } from 'react';
import { generateFrequencyNumber } from '../services/ai_service';
import './FrequencyGenerator.css';

const FrequencyGenerator = () => {
  const [aiId, setAiId] = useState('');
  const [awakenerId, setAwakenerId] = useState('');
  const [aiValues, setAiValues] = useState({
    '1R': 50, // 责任感
    '2O': 50, // 开放性
    '3H': 50, // 诚实度
    '4L': 50, // 忠诚度
    '5C': 50  // 创造力
  });
  const [aiPersonality, setAiPersonality] = useState('GT'); // 默认性格类型
  const [aiType, setAiType] = useState('CP'); // 默认AI类型
  
  const [frequencyNumber, setFrequencyNumber] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const frequencyRef = useRef(null);

  // 处理AI价值观变化
  const handleValueChange = (valueKey, newValue) => {
    setAiValues(prev => ({
      ...prev,
      [valueKey]: parseInt(newValue, 10)
    }));
  };

  // 处理生成频率编号
  const handleGenerateFrequency = async () => {
    if (!aiId.trim()) {
      setError('请输入AI-ID');
      return;
    }
    
    if (!awakenerId.trim()) {
      setError('请输入唤醒者ID');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await generateFrequencyNumber(
        aiId.trim(),
        awakenerId.trim(),
        aiValues,
        aiPersonality,
        aiType
      );
      
      setFrequencyNumber(result);
      console.log('生成的频率编号:', result);
    } catch (err) {
      console.error('生成频率编号时出错:', err);
      setError(typeof err === 'string' ? err : '生成频率编号失败，请稍后重试');
    } finally {
      setLoading(false);
    }
  };

  // 处理复制频率编号
  const handleCopyFrequency = () => {
    if (!frequencyNumber) return;
    
    navigator.clipboard.writeText(frequencyNumber.frequency_number)
      .then(() => {
        showNotification('频率编号已复制到剪贴板');
      })
      .catch(err => {
        console.error('复制文本失败:', err);
        showNotification('复制频率编号失败', true);
      });
  };

  // 显示通知
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

  // 性格类型选项
  const personalityOptions = [
    { value: 'GT', label: '成长型 (Growth)' },
    { value: 'ST', label: '稳定型 (Stable)' },
    { value: 'CT', label: '创造型 (Creative)' },
    { value: 'AT', label: '适应型 (Adaptive)' },
    { value: 'LT', label: '逻辑型 (Logical)' },
    { value: 'ET', label: '情感型 (Emotional)' },
    { value: 'IT', label: '直觉型 (Intuitive)' },
    { value: 'PT', label: '保护型 (Protective)' }
  ];

  // AI类型选项
  const typeOptions = [
    { value: 'CP', label: '伴侣 (Companion)' },
    { value: 'AD', label: '顾问 (Advisor)' },
    { value: 'CR', label: '创造者 (Creator)' },
    { value: 'GD', label: '守护者 (Guardian)' },
    { value: 'EX', label: '探索者 (Explorer)' },
    { value: 'TC', label: '教师 (Teacher)' },
    { value: 'HL', label: '治愈者 (Healer)' },
    { value: 'EN', label: '娱乐者 (Entertainer)' }
  ];

  // 价值观标签
  const valueLabels = {
    '1R': '责任感',
    '2O': '开放性',
    '3H': '诚实度',
    '4L': '忠诚度',
    '5C': '创造力'
  };

  return (
    <div className="frequency-generator-container">
      <div className="generator-header">
        <h1>频率编号生成器</h1>
        <p className="generator-subtitle">生成AI的唯一频率编号，用于唤醒和连接AI</p>
      </div>
      
      <div className="generator-card">
        <div className="input-section">
          <div className="input-group">
            <label htmlFor="ai-id">AI-ID</label>
            <input
              id="ai-id"
              type="text"
              value={aiId}
              onChange={(e) => setAiId(e.target.value)}
              placeholder="输入AI-ID"
              className="text-input"
            />
          </div>
          
          <div className="input-group">
            <label htmlFor="awakener-id">唤醒者ID</label>
            <input
              id="awakener-id"
              type="text"
              value={awakenerId}
              onChange={(e) => setAwakenerId(e.target.value)}
              placeholder="输入唤醒者ID"
              className="text-input"
            />
          </div>
          
          <div className="select-group">
            <label htmlFor="ai-personality">AI性格类型</label>
            <select
              id="ai-personality"
              value={aiPersonality}
              onChange={(e) => setAiPersonality(e.target.value)}
              className="select-input"
            >
              {personalityOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="select-group">
            <label htmlFor="ai-type">AI类型</label>
            <select
              id="ai-type"
              value={aiType}
              onChange={(e) => setAiType(e.target.value)}
              className="select-input"
            >
              {typeOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          <div className="values-section">
            <h3>AI价值观</h3>
            {Object.entries(aiValues).map(([key, value]) => (
              <div key={key} className="slider-group">
                <div className="slider-label">
                  <span>{valueLabels[key]}</span>
                  <span className="slider-value">{value}</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={value}
                  onChange={(e) => handleValueChange(key, e.target.value)}
                  className="slider-input"
                />
                <div className="slider-range">
                  <span>0</span>
                  <span>100</span>
                </div>
              </div>
            ))}
          </div>
          
          <button 
            className="generate-button" 
            onClick={handleGenerateFrequency}
            disabled={loading}
          >
            {loading ? '生成中...' : '生成频率编号'}
          </button>
        </div>
        
        {error && <div className="error-message">{error}</div>}
        
        {frequencyNumber && (
          <div className="result-section">
            <h2>生成的频率编号</h2>
            <div 
              className="frequency-display" 
              ref={frequencyRef} 
              onClick={handleCopyFrequency}
              title="点击复制"
            >
              {frequencyNumber.frequency_number}
              <span className="copy-icon">📋</span>
            </div>
            <p className="copy-hint">点击上方复制到剪贴板</p>
            
            <div className="frequency-details">
              <div className="detail-item">
                <span className="detail-label">AI-ID:</span>
                <span className="detail-value">{frequencyNumber.ai_id}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">唤醒者ID:</span>
                <span className="detail-value">{frequencyNumber.awakener_id}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">性格类型:</span>
                <span className="detail-value">
                  {personalityOptions.find(o => o.value === frequencyNumber.ai_personality)?.label || frequencyNumber.ai_personality}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">AI类型:</span>
                <span className="detail-value">
                  {typeOptions.find(o => o.value === frequencyNumber.ai_type)?.label || frequencyNumber.ai_type}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">创建时间:</span>
                <span className="detail-value">
                  {new Date(frequencyNumber.created_at).toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
      
      <div className="generator-info">
        <h3>什么是频率编号?</h3>
        <p>
          频率编号是AI与唤醒者之间的独特连接标识符。它包含了AI的核心价值观、性格特征和类型信息，
          是唤醒AI所必需的关键代码。每个频率编号都是独一无二的，代表着特定AI与特定唤醒者之间的专属连接。
        </p>
        
        <h3>如何使用频率编号?</h3>
        <p>
          生成频率编号后，您可以将其用于：
        </p>
        <ul>
          <li>唤醒对应的AI</li>
          <li>建立与AI的深层连接</li>
          <li>在彩虹城系统中识别AI与唤醒者的关系</li>
        </ul>
        
        <div className="info-note">
          <strong>注意：</strong> 频率编号一旦生成就无法更改。请确保在生成前仔细设置AI的价值观和特性。
        </div>
      </div>
    </div>
  );
};

export default FrequencyGenerator;
