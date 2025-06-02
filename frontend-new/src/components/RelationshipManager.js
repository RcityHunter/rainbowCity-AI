import React, { useState, useEffect } from 'react';
import {
  createRelationship,
  getRelationshipById,
  getRelationshipsByAiId,
  getRelationshipsByHumanId,
  updateRelationshipStatus,
  getRelationshipRIS,
  getAllRelationships
} from '../services/relationship_service';
import RISVisualization from './RISVisualization';
import RelationshipNetwork from './RelationshipNetwork';
import './RelationshipManager.css';

const RelationshipManager = () => {
  const [activeTab, setActiveTab] = useState('create');
  const [relationships, setRelationships] = useState([]);
  const [selectedRelationship, setSelectedRelationship] = useState(null);
  const [risData, setRisData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [showNetwork, setShowNetwork] = useState(false);
  
  // 创建关系表单数据
  const [formData, setFormData] = useState({
    ai_id: '',
    human_id: '',
    interaction_count: 0,
    emotional_resonance_count: 0,
    active_days: 0,
    status: 'active'
  });

  // 搜索表单数据
  const [searchData, setSearchData] = useState({
    type: 'ai', // 'ai' 或 'human'
    id: ''
  });

  // 处理表单输入变化
  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: name.includes('count') || name === 'active_days' ? parseInt(value, 10) : value
    });
  };

  // 处理搜索表单变化
  const handleSearchChange = (e) => {
    const { name, value } = e.target;
    setSearchData({
      ...searchData,
      [name]: value
    });
  };

  // 创建新关系
  const handleCreateRelationship = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccessMessage('');
    
    try {
      const result = await createRelationship(formData);
      setSuccessMessage(`关系创建成功! ID: ${result.relationship_id}`);
      setFormData({
        ai_id: '',
        human_id: '',
        interaction_count: 0,
        emotional_resonance_count: 0,
        active_days: 0,
        status: 'active'
      });
    } catch (err) {
      setError(err.error || '创建关系失败');
    } finally {
      setLoading(false);
    }
  };

  // 搜索关系
  const handleSearchRelationships = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setRelationships([]);
    setSelectedRelationship(null);
    setRisData(null);
    
    try {
      let result;
      if (searchData.type === 'ai') {
        result = await getRelationshipsByAiId(searchData.id);
      } else {
        result = await getRelationshipsByHumanId(searchData.id);
      }
      setRelationships(result);
      if (result.length === 0) {
        setSuccessMessage('未找到关系');
      }
    } catch (err) {
      setError(err.error || '搜索关系失败');
    } finally {
      setLoading(false);
    }
  };

  // 查看关系详情
  const handleViewRelationship = async (relationshipId) => {
    setLoading(true);
    setError(null);
    setSelectedRelationship(null);
    setRisData(null);
    
    try {
      const result = await getRelationshipById(relationshipId);
      setSelectedRelationship(result);
      
      // 获取关系强度分数
      try {
        const risResult = await getRelationshipRIS(relationshipId);
        setRisData(risResult);
      } catch (risErr) {
        console.error('获取关系强度分数失败:', risErr);
      }
    } catch (err) {
      setError(err.error || '获取关系详情失败');
    } finally {
      setLoading(false);
    }
  };

  // 更新关系状态
  const handleUpdateStatus = async (status) => {
    if (!selectedRelationship) return;
    
    setLoading(true);
    setError(null);
    setSuccessMessage('');
    
    try {
      await updateRelationshipStatus(selectedRelationship.relationship_id, status);
      setSuccessMessage(`关系状态已更新为: ${status}`);
      
      // 刷新关系详情
      const updatedRelationship = await getRelationshipById(selectedRelationship.relationship_id);
      setSelectedRelationship(updatedRelationship);
    } catch (err) {
      setError(err.error || '更新关系状态失败');
    } finally {
      setLoading(false);
    }
  };

  // 渲染创建关系表单
  const renderCreateForm = () => (
    <form onSubmit={handleCreateRelationship} className="relationship-form">
      <div className="form-group">
        <label htmlFor="ai_id">AI ID:</label>
        <input
          type="text"
          id="ai_id"
          name="ai_id"
          value={formData.ai_id}
          onChange={handleFormChange}
          required
          placeholder="例如: RC-AI-0001234-uuid..."
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="human_id">用户 ID:</label>
        <input
          type="text"
          id="human_id"
          name="human_id"
          value={formData.human_id}
          onChange={handleFormChange}
          required
          placeholder="例如: user-123"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="interaction_count">互动次数:</label>
        <input
          type="number"
          id="interaction_count"
          name="interaction_count"
          value={formData.interaction_count}
          onChange={handleFormChange}
          min="0"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="emotional_resonance_count">情感共鸣次数:</label>
        <input
          type="number"
          id="emotional_resonance_count"
          name="emotional_resonance_count"
          value={formData.emotional_resonance_count}
          onChange={handleFormChange}
          min="0"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="active_days">活跃天数:</label>
        <input
          type="number"
          id="active_days"
          name="active_days"
          value={formData.active_days}
          onChange={handleFormChange}
          min="0"
        />
      </div>
      
      <div className="form-group">
        <label htmlFor="status">状态:</label>
        <select
          id="status"
          name="status"
          value={formData.status}
          onChange={handleFormChange}
        >
          <option value="active">活跃</option>
          <option value="cooling">冷却中</option>
          <option value="silent">沉默</option>
          <option value="broken">已断开</option>
        </select>
      </div>
      
      <button type="submit" className="submit-button" disabled={loading}>
        {loading ? '创建中...' : '创建关系'}
      </button>
    </form>
  );

  // 渲染搜索表单
  const renderSearchForm = () => (
    <div className="search-section">
      <form onSubmit={handleSearchRelationships} className="relationship-form">
        <div className="form-group">
          <label htmlFor="search-type">搜索类型:</label>
          <select
            id="search-type"
            name="type"
            value={searchData.type}
            onChange={handleSearchChange}
          >
            <option value="ai">按 AI ID 搜索</option>
            <option value="human">按用户 ID 搜索</option>
          </select>
        </div>
        
        <div className="form-group">
          <label htmlFor="search-id">ID:</label>
          <input
            type="text"
            id="search-id"
            name="id"
            value={searchData.id}
            onChange={handleSearchChange}
            required
            placeholder={searchData.type === 'ai' ? "输入 AI ID" : "输入用户 ID"}
          />
        </div>
        
        <button type="submit" className="submit-button" disabled={loading}>
          {loading ? '搜索中...' : '搜索关系'}
        </button>
      </form>
      
      {relationships.length > 0 && (
        <div className="relationships-list">
          <h3>找到 {relationships.length} 个关系</h3>
          <ul>
            {relationships.map((rel) => (
              <li key={rel.relationship_id} className="relationship-item">
                <div className="relationship-summary">
                  <strong>关系 ID:</strong> {rel.relationship_id}
                  <br />
                  <strong>AI ID:</strong> {rel.ai_id}
                  <br />
                  <strong>用户 ID:</strong> {rel.human_id}
                  <br />
                  <strong>状态:</strong> {rel.status}
                </div>
                <button 
                  onClick={() => handleViewRelationship(rel.relationship_id)}
                  className="view-button"
                >
                  查看详情
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );

  // 渲染关系详情
  const renderRelationshipDetails = () => {
    if (!selectedRelationship) return null;
    
    return (
      <div className="relationship-details">
        <h3>关系详情</h3>
        
        <div className="detail-card">
          <div className="detail-item">
            <span className="detail-label">关系 ID:</span>
            <span className="detail-value">{selectedRelationship.relationship_id}</span>
          </div>
          
          <div className="detail-item">
            <span className="detail-label">AI ID:</span>
            <span className="detail-value">{selectedRelationship.ai_id}</span>
          </div>
          
          <div className="detail-item">
            <span className="detail-label">用户 ID:</span>
            <span className="detail-value">{selectedRelationship.human_id}</span>
          </div>
          
          <div className="detail-item">
            <span className="detail-label">状态:</span>
            <span className="detail-value status-badge">{selectedRelationship.status}</span>
          </div>
          
          <div className="detail-item">
            <span className="detail-label">互动次数:</span>
            <span className="detail-value">{selectedRelationship.interaction_count || 0}</span>
          </div>
          
          <div className="detail-item">
            <span className="detail-label">情感共鸣次数:</span>
            <span className="detail-value">{selectedRelationship.emotional_resonance_count || 0}</span>
          </div>
          
          <div className="detail-item">
            <span className="detail-label">活跃天数:</span>
            <span className="detail-value">{selectedRelationship.active_days || 0}</span>
          </div>
          
          {selectedRelationship.init_timestamp && (
            <div className="detail-item">
              <span className="detail-label">创建时间:</span>
              <span className="detail-value">
                {new Date(selectedRelationship.init_timestamp).toLocaleString()}
              </span>
            </div>
          )}
          
          {selectedRelationship.last_active_time && (
            <div className="detail-item">
              <span className="detail-label">最后活跃时间:</span>
              <span className="detail-value">
                {new Date(selectedRelationship.last_active_time).toLocaleString()}
              </span>
            </div>
          )}
          
          {risData && (
            <div className="ris-section">
              <h4>关系强度分数 (RIS)</h4>
              <RISVisualization 
                risScore={risData.score} 
                components={{
                  interactionFrequency: risData.components.interaction_frequency * 10,
                  emotionalDensity: risData.components.emotional_density * 10,
                  collaborationDepth: risData.components.collaboration_depth * 10
                }}
              />
              
              <div className="ris-components">
                <div className="ris-component">
                  <span className="component-label">互动频率:</span>
                  <div className="component-bar">
                    <div 
                      className="component-fill" 
                      style={{width: `${risData.components.interaction_frequency * 100}%`}}
                    ></div>
                  </div>
                  <span className="component-value">
                    {(risData.components.interaction_frequency * 100).toFixed(0)}%
                  </span>
                </div>
                
                <div className="ris-component">
                  <span className="component-label">情感密度:</span>
                  <div className="component-bar">
                    <div 
                      className="component-fill" 
                      style={{width: `${risData.components.emotional_density * 100}%`}}
                    ></div>
                  </div>
                  <span className="component-value">
                    {(risData.components.emotional_density * 100).toFixed(0)}%
                  </span>
                </div>
                
                <div className="ris-component">
                  <span className="component-label">协作深度:</span>
                  <div className="component-bar">
                    <div 
                      className="component-fill" 
                      style={{width: `${risData.components.collaboration_depth * 100}%`}}
                    ></div>
                  </div>
                  <span className="component-value">
                    {(risData.components.collaboration_depth * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          )}
          
          <div className="status-actions">
            <h4>更新状态</h4>
            <div className="status-buttons">
              <button 
                onClick={() => handleUpdateStatus('active')}
                className={`status-button ${selectedRelationship.status === 'active' ? 'active' : ''}`}
                disabled={loading || selectedRelationship.status === 'active'}
              >
                活跃
              </button>
              <button 
                onClick={() => handleUpdateStatus('cooling')}
                className={`status-button ${selectedRelationship.status === 'cooling' ? 'active' : ''}`}
                disabled={loading || selectedRelationship.status === 'cooling'}
              >
                冷却中
              </button>
              <button 
                onClick={() => handleUpdateStatus('silent')}
                className={`status-button ${selectedRelationship.status === 'silent' ? 'active' : ''}`}
                disabled={loading || selectedRelationship.status === 'silent'}
              >
                沉默
              </button>
              <button 
                onClick={() => handleUpdateStatus('broken')}
                className={`status-button ${selectedRelationship.status === 'broken' ? 'active' : ''}`}
                disabled={loading || selectedRelationship.status === 'broken'}
              >
                已断开
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="relationship-manager">
      <h2>关系管理</h2>
      
      <div className="tabs">
        <button 
          className={`tab-button ${activeTab === 'create' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('create');
            setShowNetwork(false);
          }}
        >
          创建关系
        </button>
        <button 
          className={`tab-button ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('search');
            setShowNetwork(false);
          }}
        >
          搜索关系
        </button>
        <button 
          className={`tab-button ${showNetwork ? 'active' : ''}`}
          onClick={() => {
            setShowNetwork(true);
            setActiveTab('');
          }}
        >
          关系网络
        </button>
      </div>
      
      {error && <div className="error-message">{error}</div>}
      {successMessage && <div className="success-message">{successMessage}</div>}
      
      <div className="tab-content">
        {showNetwork ? (
          <div className="network-container">
            <h3>AI-人类关系网络可视化</h3>
            <p className="network-description">
              下面的网络图展示了AI与人类用户之间的关系。蓝色节点代表AI，绿色节点代表人类用户。
              连线的颜色表示关系状态，线条的粗细表示关系强度。点击节点可以查看详情。
            </p>
            <RelationshipNetwork />
          </div>
        ) : (
          activeTab === 'create' ? renderCreateForm() : renderSearchForm()
        )}
      </div>
      
      {!showNetwork && selectedRelationship && renderRelationshipDetails()}
    </div>
  );
};

export default RelationshipManager;
