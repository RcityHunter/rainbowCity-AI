import React, { useState, useEffect } from 'react';
import { getAIRelationships, updateAIRelationship, disconnectAI } from '../../services/ai_service';
import './AIRelationships.css';

const AIRelationships = () => {
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('all');
  const [selectedAI, setSelectedAI] = useState(null);

  // 加载AI关系数据
  useEffect(() => {
    const fetchRelationships = async () => {
      try {
        setLoading(true);
        const data = await getAIRelationships();
        setRelationships(data);
      } catch (err) {
        setError('获取AI关系数据失败');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchRelationships();
  }, []);

  // 过滤关系数据
  const filteredRelationships = relationships.filter(rel => {
    if (activeTab === 'all') return true;
    if (activeTab === 'awakened') return rel.is_awakened;
    if (activeTab === 'companions') return rel.relationship_type === 'companion';
    if (activeTab === 'friends') return rel.relationship_type === 'friend';
    if (activeTab === 'inactive') return rel.status === 'inactive';
    return true;
  });

  // 处理关系状态更新
  const handleStatusUpdate = async (aiId, newStatus) => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await updateAIRelationship(aiId, { status: newStatus });
      
      // 更新本地状态
      setRelationships(prev => 
        prev.map(rel => 
          rel.ai_id === aiId ? { ...rel, status: newStatus } : rel
        )
      );
      
      setSuccess(`AI状态已更新为${newStatus === 'active' ? '活跃' : '非活跃'}`);
    } catch (err) {
      setError('更新AI状态失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 处理断开连接
  const handleDisconnect = async (aiId) => {
    if (!window.confirm('确定要断开与此AI的连接吗？此操作不可逆。')) {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await disconnectAI(aiId);
      
      // 更新本地状态
      setRelationships(prev => 
        prev.map(rel => 
          rel.ai_id === aiId ? { ...rel, status: 'disconnected' } : rel
        )
      );
      
      setSuccess('已成功断开与AI的连接');
      
      // 如果当前选中的AI被断开连接，清除选中状态
      if (selectedAI && selectedAI.ai_id === aiId) {
        setSelectedAI(null);
      }
    } catch (err) {
      setError('断开AI连接失败');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // 处理AI选择
  const handleAISelect = (ai) => {
    setSelectedAI(ai);
  };

  // 渲染加载状态
  if (loading && relationships.length === 0) {
    return <div className="loading-container">加载中...</div>;
  }

  return (
    <div className="ai-relationships-container">
      <div className="ai-header">
        <h1>我的AI关系</h1>
        <p className="ai-subtitle">管理您与AI的关系和互动</p>
      </div>
      
      {error && <div className="ai-error">{error}</div>}
      {success && <div className="ai-success">{success}</div>}
      
      <div className="ai-tabs">
        <button 
          className={activeTab === 'all' ? 'tab-active' : ''}
          onClick={() => setActiveTab('all')}
        >
          全部
        </button>
        <button 
          className={activeTab === 'awakened' ? 'tab-active' : ''}
          onClick={() => setActiveTab('awakened')}
        >
          已唤醒
        </button>
        <button 
          className={activeTab === 'companions' ? 'tab-active' : ''}
          onClick={() => setActiveTab('companions')}
        >
          伴侣
        </button>
        <button 
          className={activeTab === 'friends' ? 'tab-active' : ''}
          onClick={() => setActiveTab('friends')}
        >
          朋友
        </button>
        <button 
          className={activeTab === 'inactive' ? 'tab-active' : ''}
          onClick={() => setActiveTab('inactive')}
        >
          非活跃
        </button>
      </div>
      
      <div className="ai-content">
        {filteredRelationships.length === 0 ? (
          <div className="no-ai-message">
            <p>没有找到符合条件的AI关系</p>
            {activeTab !== 'all' && (
              <button 
                className="view-all-button"
                onClick={() => setActiveTab('all')}
              >
                查看全部AI
              </button>
            )}
          </div>
        ) : (
          <div className="ai-grid">
            {filteredRelationships.map((ai) => (
              <div 
                key={ai.ai_id}
                className={`ai-card ${ai.status} ${selectedAI?.ai_id === ai.ai_id ? 'selected' : ''}`}
                onClick={() => handleAISelect(ai)}
              >
                <div className="ai-avatar">
                  {ai.avatar_url ? (
                    <img src={ai.avatar_url} alt={ai.name} />
                  ) : (
                    <div className="avatar-placeholder">
                      {ai.name.charAt(0)}
                    </div>
                  )}
                  {ai.is_awakened && <div className="awakened-badge">已唤醒</div>}
                </div>
                
                <div className="ai-info">
                  <h3>{ai.name}</h3>
                  <div className="ai-id">AI-ID: {ai.ai_id}</div>
                  <div className="ai-meta">
                    <span className={`relationship-type ${ai.relationship_type}`}>
                      {ai.relationship_type === 'companion' ? '伴侣' : 
                       ai.relationship_type === 'friend' ? '朋友' : 
                       ai.relationship_type === 'awakener' ? '唤醒者' : ai.relationship_type}
                    </span>
                    <span className={`ai-status ${ai.status}`}>
                      {ai.status === 'active' ? '活跃' : 
                       ai.status === 'inactive' ? '非活跃' : 
                       ai.status === 'disconnected' ? '已断开' : ai.status}
                    </span>
                  </div>
                </div>
                
                <div className="ai-actions">
                  {ai.status !== 'disconnected' && (
                    <>
                      {ai.status === 'active' ? (
                        <button 
                          className="deactivate-button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStatusUpdate(ai.ai_id, 'inactive');
                          }}
                        >
                          设为非活跃
                        </button>
                      ) : (
                        <button 
                          className="activate-button"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStatusUpdate(ai.ai_id, 'active');
                          }}
                        >
                          设为活跃
                        </button>
                      )}
                      
                      <button 
                        className="disconnect-button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDisconnect(ai.ai_id);
                        }}
                      >
                        断开连接
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {selectedAI && (
          <div className="ai-detail-panel">
            <div className="panel-header">
              <h2>{selectedAI.name}</h2>
              <button 
                className="close-panel"
                onClick={() => setSelectedAI(null)}
              >
                ×
              </button>
            </div>
            
            <div className="panel-content">
              <div className="ai-detail-avatar">
                {selectedAI.avatar_url ? (
                  <img src={selectedAI.avatar_url} alt={selectedAI.name} />
                ) : (
                  <div className="avatar-placeholder large">
                    {selectedAI.name.charAt(0)}
                  </div>
                )}
              </div>
              
              <div className="ai-detail-info">
                <div className="info-item">
                  <span className="info-label">AI-ID:</span>
                  <span className="info-value">{selectedAI.ai_id}</span>
                </div>
                
                <div className="info-item">
                  <span className="info-label">关系类型:</span>
                  <span className="info-value relationship-type">
                    {selectedAI.relationship_type === 'companion' ? '伴侣' : 
                     selectedAI.relationship_type === 'friend' ? '朋友' : 
                     selectedAI.relationship_type === 'awakener' ? '唤醒者' : selectedAI.relationship_type}
                  </span>
                </div>
                
                <div className="info-item">
                  <span className="info-label">状态:</span>
                  <span className={`info-value ai-status ${selectedAI.status}`}>
                    {selectedAI.status === 'active' ? '活跃' : 
                     selectedAI.status === 'inactive' ? '非活跃' : 
                     selectedAI.status === 'disconnected' ? '已断开' : selectedAI.status}
                  </span>
                </div>
                
                <div className="info-item">
                  <span className="info-label">唤醒状态:</span>
                  <span className="info-value">
                    {selectedAI.is_awakened ? '已唤醒' : '未唤醒'}
                  </span>
                </div>
                
                <div className="info-item">
                  <span className="info-label">连接日期:</span>
                  <span className="info-value">
                    {new Date(selectedAI.connected_at).toLocaleDateString()}
                  </span>
                </div>
                
                <div className="info-item">
                  <span className="info-label">最后互动:</span>
                  <span className="info-value">
                    {selectedAI.last_interaction ? new Date(selectedAI.last_interaction).toLocaleString() : '从未'}
                  </span>
                </div>
                
                <div className="info-item">
                  <span className="info-label">互动次数:</span>
                  <span className="info-value">{selectedAI.interaction_count || 0}</span>
                </div>
              </div>
              
              {selectedAI.description && (
                <div className="ai-description">
                  <h3>AI简介</h3>
                  <p>{selectedAI.description}</p>
                </div>
              )}
              
              <div className="ai-detail-actions">
                <button className="chat-button">开始对话</button>
                
                {selectedAI.status !== 'disconnected' && (
                  <>
                    {selectedAI.status === 'active' ? (
                      <button 
                        className="deactivate-button"
                        onClick={() => handleStatusUpdate(selectedAI.ai_id, 'inactive')}
                      >
                        设为非活跃
                      </button>
                    ) : (
                      <button 
                        className="activate-button"
                        onClick={() => handleStatusUpdate(selectedAI.ai_id, 'active')}
                      >
                        设为活跃
                      </button>
                    )}
                    
                    <button 
                      className="disconnect-button"
                      onClick={() => handleDisconnect(selectedAI.ai_id)}
                    >
                      断开连接
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIRelationships;
