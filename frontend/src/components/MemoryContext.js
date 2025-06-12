import React, { useState } from 'react';
import './MemoryContext.css';

/**
 * 记忆上下文组件 - 显示与当前对话相关的记忆
 */
function MemoryContext({ memories, sessionSummary, isVisible = true }) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // 如果没有记忆或会话摘要，或者不可见，则不渲染
  if (!isVisible || (!memories?.length && !sessionSummary)) {
    return null;
  }
  
  // 记忆类型映射到中文
  const memoryTypeMap = {
    'personal_info': '个人信息',
    'preference': '偏好',
    'opinion': '观点',
    'fact': '事实',
    'plan': '计划',
    'other': '其他'
  };
  
  // 记忆重要性映射到标签
  const importanceLabels = {
    1: '低',
    2: '中',
    3: '高',
    4: '关键'
  };
  
  // 渲染记忆项
  const renderMemoryItem = (memory, index) => {
    const memoryType = memory.memory_type || 'other';
    const importance = memory.importance || 2;
    const typeLabel = memoryTypeMap[memoryType] || memoryType;
    const importanceLabel = importanceLabels[importance] || '中';
    
    return (
      <div key={memory.id || index} className={`memory-item importance-${importance}`}>
        <div className="memory-content">{memory.content}</div>
        <div className="memory-meta">
          <span className="memory-type">{typeLabel}</span>
          <span className="memory-importance">重要性: {importanceLabel}</span>
        </div>
      </div>
    );
  };
  
  return (
    <div className={`memory-context-container ${isExpanded ? 'expanded' : 'collapsed'}`}>
      <div className="memory-header" onClick={() => setIsExpanded(!isExpanded)}>
        <h3>记忆上下文</h3>
        <button className="toggle-button">
          {isExpanded ? '收起' : '展开'}
        </button>
      </div>
      
      {isExpanded && (
        <div className="memory-content-container">
          {/* 会话摘要部分 */}
          {sessionSummary && (
            <div className="session-summary">
              <h4>对话摘要</h4>
              <p>{sessionSummary.summary}</p>
              
              {sessionSummary.topics && sessionSummary.topics.length > 0 && (
                <div className="topics-container">
                  <h5>讨论话题</h5>
                  <div className="topics-list">
                    {sessionSummary.topics.map((topic, index) => (
                      <span key={index} className="topic-tag">{topic}</span>
                    ))}
                  </div>
                </div>
              )}
              
              {sessionSummary.key_points && sessionSummary.key_points.length > 0 && (
                <div className="key-points">
                  <h5>关键点</h5>
                  <ul>
                    {sessionSummary.key_points.map((point, index) => (
                      <li key={index}>{point}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
          
          {/* 用户记忆部分 */}
          {memories && memories.length > 0 && (
            <div className="user-memories">
              <h4>用户记忆</h4>
              <div className="memories-list">
                {memories.map(renderMemoryItem)}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default MemoryContext;
