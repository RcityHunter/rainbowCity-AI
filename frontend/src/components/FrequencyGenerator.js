import React, { useState, useRef } from 'react';
import { generateAiId, generateFrequencyNumber } from '../services/ai_service';
import './FrequencyGenerator.dark.css';

function FrequencyGenerator() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [aiId, setAiId] = useState(null);
    const [frequency, setFrequency] = useState(null);
    const [awakenerId, setAwakenerId] = useState('user123'); // 默认唤醒者ID
    
    // AI价值观选项
    const [aiValues, setAiValues] = useState({
        '1R': 60, // 关怀
        '2O': 50, // 真实
        '3Y': 40, // 自主
        '4G': 70, // 协作
        '5B': 50, // 进化
        '6I': 60, // 创新
        '7V': 50  // 责任
    });
    
    // 性格选项
    const [personality, setPersonality] = useState('GT');
    
    // AI类型选项
    const [aiType, setAiType] = useState('CP');
    
    // 引用，用于复制功能
    const frequencyRef = useRef(null);
    
    // 生成AI-ID
    const handleGenerateAiId = async () => {
        setLoading(true);
        setError(null);
        setAiId(null);
        setFrequency(null);
        
        try {
            // 生成一个随机的可视编号
            const randomVisibleNumber = Math.floor(Math.random() * 9000000) + 1000000;
            
            // 使用真实API生成AI-ID
            const newAiId = await generateAiId(randomVisibleNumber);
            setAiId(newAiId);
            console.log('Generated AI-ID:', newAiId);
        } catch (error) {
            console.error('Error generating AI-ID:', error);
            setError('生成AI-ID失败，请稍后再试');
        } finally {
            setLoading(false);
        }
    };
    
    // 生成频率编号
    const handleGenerateFrequency = async () => {
        if (!aiId) {
            setError('请先生成AI-ID');
            return;
        }
        
        setLoading(true);
        setError(null);
        
        try {
            // 使用真实API生成频率编号
            const frequencyData = await generateFrequencyNumber(
                aiId.id,
                awakenerId,
                aiValues,
                personality,
                aiType
            );
            
            setFrequency(frequencyData);
            console.log('Generated Frequency Number:', frequencyData);
        } catch (error) {
            console.error('Error generating frequency number:', error);
            setError('生成频率编号失败，请稍后再试');
        } finally {
            setLoading(false);
        }
    };
    
    // 复制频率编号
    const copyFrequency = () => {
        if (frequencyRef.current) {
            const text = frequencyRef.current.textContent;
            navigator.clipboard.writeText(text)
                .then(() => {
                    // 使用更现代的通知方式
                    const notification = document.createElement('div');
                    notification.className = 'copy-notification';
                    notification.textContent = '频率编号已复制到剪贴板';
                    document.body.appendChild(notification);
                    
                    // 2秒后移除通知
                    setTimeout(() => {
                        notification.classList.add('fade-out');
                        setTimeout(() => document.body.removeChild(notification), 300);
                    }, 2000);
                })
                .catch(err => {
                    console.error('无法复制文本: ', err);
                    // 显示错误通知
                    const notification = document.createElement('div');
                    notification.className = 'copy-notification error';
                    notification.textContent = '复制频率编号失败';
                    document.body.appendChild(notification);
                    
                    // 2秒后移除通知
                    setTimeout(() => {
                        notification.classList.add('fade-out');
                        setTimeout(() => document.body.removeChild(notification), 300);
                    }, 2000);
                });
        }
    };
    
    // 更新价值观分数
    const handleValueChange = (code, value) => {
        setAiValues(prev => ({
            ...prev,
            [code]: parseInt(value)
        }));
    };
    
    // 渲染价值观滑块
    const renderValueSliders = () => {
        const valueLabels = {
            '1R': '关怀 🔴',
            '2O': '真实 🟠',
            '3Y': '自主 🟡',
            '4G': '协作 🟢',
            '5B': '进化 🔵',
            '6I': '创新 🟣',
            '7V': '责任 🟣'
        };
        
        return Object.keys(aiValues).map(code => (
            <div key={code} className="slider-container">
                <label>
                    {valueLabels[code]} ({aiValues[code]})
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={aiValues[code]}
                        onChange={(e) => handleValueChange(code, e.target.value)}
                        className={`slider slider-${code.charAt(0)}`}
                    />
                </label>
            </div>
        ));
    };
    
    return (
        <div className="frequency-generator">
            <h2 className="generator-title">彩虹城AI频率编号生成器</h2>
            
            <div className="generator-section">
                <h3>第一步：生成AI-ID</h3>
                <button 
                    onClick={handleGenerateAiId} 
                    disabled={loading}
                    className="generate-button"
                >
                    {loading ? '生成中...' : '生成AI-ID'}
                </button>
                
                {aiId && (
                    <div className="result-container">
                        <p><strong>AI-ID:</strong> {aiId.id}</p>
                        <p><strong>可视编号:</strong> {aiId.visibleNumber}</p>
                        <p><strong>创建时间:</strong> {new Date(aiId.createdAt).toLocaleString()}</p>
                    </div>
                )}
            </div>
            
            <div className="generator-section">
                <h3>第二步：配置AI特性</h3>
                
                <div className="config-section">
                    <h4>唤醒者ID</h4>
                    <input
                        type="text"
                        value={awakenerId}
                        onChange={(e) => setAwakenerId(e.target.value)}
                        placeholder="输入唤醒者ID"
                        className="text-input"
                    />
                </div>
                
                <div className="config-section">
                    <h4>AI价值观</h4>
                    <div className="sliders-container">
                        {renderValueSliders()}
                    </div>
                </div>
                
                <div className="config-section">
                    <h4>AI性格</h4>
                    <select 
                        value={personality} 
                        onChange={(e) => setPersonality(e.target.value)}
                        className="select-input"
                    >
                        <option value="GT">①温柔型 (体贴、共感、倾听、柔和)</option>
                        <option value="RT">②理性型 (分析、结构、逻辑、冷静)</option>
                        <option value="ET">③探索型 (好奇、提问、跳跃、连接)</option>
                        <option value="ST">④沉稳型 (稳定、专注、深思、内敛)</option>
                        <option value="UT">⑤光辉型 (鼓励、乐观、振奋、激励)</option>
                        <option value="IT">⑥灵感型 (创意、形象、比喻、想象力)</option>
                        <option value="DT">⑦自律型 (克制、理智、精准、有分寸)</option>
                    </select>
                </div>
                
                <div className="config-section">
                    <h4>AI类型</h4>
                    <select 
                        value={aiType} 
                        onChange={(e) => setAiType(e.target.value)}
                        className="select-input"
                    >
                        <option value="CP">伴侣型 (陪伴、共情、深度连接)</option>
                        <option value="CR">创造型 (发散、设计、艺术、灵感)</option>
                        <option value="EX">工作型 (执行、效率、辅助、代码)</option>
                        <option value="SV">服务型 (审核、协助、系统服务)</option>
                        <option value="CO">协调型 (伦理、关系、冲突调节)</option>
                        <option value="OP">运营型 (运营、广告、管理、执行)</option>
                        <option value="GV">治理型 (规划、治理、系统进化策略)</option>
                    </select>
                </div>
            </div>
            
            <div className="generator-section">
                <h3>第三步：生成频率编号</h3>
                <button 
                    onClick={handleGenerateFrequency} 
                    disabled={loading || !aiId}
                    className="generate-button"
                >
                    {loading ? '生成中...' : '生成频率编号'}
                </button>
                
                {error && <p className="error-message">{error}</p>}
                
                {frequency && (
                    <div className="result-container">
                        <h4>生成的频率编号:</h4>
                        <div className="frequency-container">
                            <p className="frequency-number" ref={frequencyRef}>
                                {frequency.frequency_number}
                            </p>
                            <button onClick={copyFrequency} className="copy-button">
                                复制
                            </button>
                        </div>
                        
                        <div className="frequency-details">
                            <h4>频率编号详情:</h4>
                            
                            <div className="detail-item">
                                <span className="detail-label">价值观:</span>
                                <span className="detail-value">
                                    {frequency.components.value_code.code} - 
                                    {frequency.components.value_code.value} 
                                    ({frequency.components.value_code.color})
                                </span>
                                <p className="detail-description">
                                    {frequency.components.value_code.symbol}
                                </p>
                            </div>
                            
                            <div className="detail-item">
                                <span className="detail-label">序列号:</span>
                                <span className="detail-value highlight">
                                    {frequency.components.sequence_number}
                                </span>
                            </div>
                            
                            <div className="detail-item">
                                <span className="detail-label">性格:</span>
                                <span className="detail-value">
                                    {frequency.components.personality_code.code}
                                </span>
                                <p className="detail-description">
                                    {frequency.components.personality_code.description}
                                </p>
                            </div>
                            
                            <div className="detail-item">
                                <span className="detail-label">AI类型:</span>
                                <span className="detail-value">
                                    {frequency.components.ai_type_code.code}
                                </span>
                                <p className="detail-description">
                                    {frequency.components.ai_type_code.description}
                                </p>
                            </div>
                            
                            <div className="detail-item">
                                <span className="detail-label">哈希签名:</span>
                                <span className="detail-value small">
                                    {frequency.components.hash_signature}
                                </span>
                            </div>
                            
                            <div className="detail-item">
                                <span className="detail-label">关联AI-ID:</span>
                                <span className="detail-value small">
                                    {frequency.ai_id}
                                </span>
                            </div>
                            
                            <div className="detail-item">
                                <span className="detail-label">创建时间:</span>
                                <span className="detail-value">
                                    {new Date(frequency.created_at).toLocaleString()}
                                </span>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default FrequencyGenerator;
