import React, { useEffect, useState, useRef } from 'react';
import { getAllRelationships } from '../services/relationship_service';
import './RelationshipNetwork.dark.css';

const RelationshipNetwork = () => {
  const [relationships, setRelationships] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const svgRef = useRef(null);
  const [simulation, setSimulation] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);

  // 模拟关系数据
  const mockRelationships = [
    {
      relationship_id: 'rel-001',
      ai_id: 'RC-AI-1234567',
      human_id: 'user-001',
      status: 'active',
      ris: 8,
      created_at: new Date().toISOString()
    },
    {
      relationship_id: 'rel-002',
      ai_id: 'RC-AI-1234567',
      human_id: 'user-002',
      status: 'cooling',
      ris: 5,
      created_at: new Date().toISOString()
    },
    {
      relationship_id: 'rel-003',
      ai_id: 'RC-AI-7654321',
      human_id: 'user-001',
      status: 'silent',
      ris: 3,
      created_at: new Date().toISOString()
    },
    {
      relationship_id: 'rel-004',
      ai_id: 'RC-AI-7654321',
      human_id: 'user-003',
      status: 'active',
      ris: 7,
      created_at: new Date().toISOString()
    },
    {
      relationship_id: 'rel-005',
      ai_id: 'RC-AI-9876543',
      human_id: 'user-002',
      status: 'broken',
      ris: 2,
      created_at: new Date().toISOString()
    }
  ];

  // 加载关系数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        let response;
        
        try {
          // 尝试从 API 获取数据
          response = await getAllRelationships();
        } catch (apiError) {
          console.warn('无法从 API 获取关系数据，使用模拟数据代替:', apiError);
          // 使用模拟数据
          response = mockRelationships;
        }
        
        setRelationships(response);
        
        // 处理数据以创建节点和连接
        processRelationshipData(response);
        setLoading(false);
      } catch (err) {
        console.error('处理关系数据时出错:', err);
        setError('无法加载关系数据');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  // 处理关系数据，创建节点和连接
  const processRelationshipData = (relationships) => {
    const nodesMap = new Map();
    const linksArray = [];
    
    // 创建节点
    relationships.forEach(rel => {
      if (!nodesMap.has(rel.ai_id)) {
        nodesMap.set(rel.ai_id, {
          id: rel.ai_id,
          type: 'ai',
          relations: 0,
          x: Math.random() * 800,
          y: Math.random() * 600
        });
      }
      
      if (!nodesMap.has(rel.human_id)) {
        nodesMap.set(rel.human_id, {
          id: rel.human_id,
          type: 'human',
          relations: 0,
          x: Math.random() * 800,
          y: Math.random() * 600
        });
      }
      
      // 更新关系计数
      const aiNode = nodesMap.get(rel.ai_id);
      const humanNode = nodesMap.get(rel.human_id);
      aiNode.relations += 1;
      humanNode.relations += 1;
      
      // 创建连接
      linksArray.push({
        source: rel.ai_id,
        target: rel.human_id,
        strength: rel.ris || 5, // 默认强度为5
        status: rel.status,
        id: rel.relationship_id
      });
    });
    
    setNodes(Array.from(nodesMap.values()));
    setLinks(linksArray);
  };

  // 当节点或连接更新时，更新力导向图
  useEffect(() => {
    if (!nodes.length || !links.length || !svgRef.current) return;

    // 模拟力导向图布局
    const simulateForceLayout = () => {
      const svg = svgRef.current;
      const width = svg.clientWidth;
      const height = svg.clientHeight;
      
      // 创建力导向图
      const sim = {
        nodes: [...nodes],
        links: [...links.map(link => ({
          ...link,
          source: nodes.find(n => n.id === link.source),
          target: nodes.find(n => n.id === link.target)
        }))],
        tick: function() {
          // 简单的力导向算法
          this.links.forEach(link => {
            const dx = link.target.x - link.source.x;
            const dy = link.target.y - link.source.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            const strength = link.strength / 10;
            
            if (distance > 0) {
              const forceX = dx * strength / distance;
              const forceY = dy * strength / distance;
              
              link.source.x += forceX;
              link.source.y += forceY;
              link.target.x -= forceX;
              link.target.y -= forceY;
            }
          });
          
          // 边界检查
          this.nodes.forEach(node => {
            node.x = Math.max(50, Math.min(width - 50, node.x));
            node.y = Math.max(50, Math.min(height - 50, node.y));
          });
          
          // 更新节点位置
          setNodes([...this.nodes]);
        }
      };
      
      setSimulation(sim);
      
      // 运行模拟
      const interval = setInterval(() => {
        sim.tick();
      }, 30);
      
      return () => clearInterval(interval);
    };
    
    const cleanup = simulateForceLayout();
    return cleanup;
  }, [nodes.length, links.length]);

  // 处理节点点击
  const handleNodeClick = (node) => {
    setSelectedNode(node);
  };

  // 获取节点颜色
  const getNodeColor = (node) => {
    if (node.type === 'ai') {
      return '#6e45e2';
    } else {
      return '#88d3ce';
    }
  };

  // 获取连接颜色
  const getLinkColor = (link) => {
    switch (link.status) {
      case 'active':
        return '#4caf50';
      case 'cooling':
        return '#ff9800';
      case 'silent':
        return '#9e9e9e';
      case 'broken':
        return '#f44336';
      default:
        return '#aaaaaa';
    }
  };

  // 渲染加载状态
  if (loading) {
    return <div className="loading">加载关系网络中...</div>;
  }

  // 渲染错误状态
  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="relationship-network">
      <svg 
        ref={svgRef} 
        width="100%" 
        height="500px" 
        className="network-svg"
      >
        {/* 绘制连接 */}
        {links.map(link => {
          const source = nodes.find(n => n.id === link.source);
          const target = nodes.find(n => n.id === link.target);
          if (!source || !target) return null;
          
          return (
            <line 
              key={`link-${link.id}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke={getLinkColor(link)}
              strokeWidth={Math.max(1, link.strength / 2)}
              strokeOpacity="0.6"
            />
          );
        })}
        
        {/* 绘制节点 */}
        {nodes.map(node => (
          <g 
            key={`node-${node.id}`}
            transform={`translate(${node.x}, ${node.y})`}
            onClick={() => handleNodeClick(node)}
            style={{ cursor: 'pointer' }}
          >
            <circle
              r={Math.max(5, node.relations * 3)}
              fill={getNodeColor(node)}
              stroke="#ffffff"
              strokeWidth="1"
            />
            <text
              textAnchor="middle"
              y={-10}
              fill="#ffffff"
              fontSize="10"
              opacity="0.8"
            >
              {node.id.substring(0, 8)}...
            </text>
          </g>
        ))}
      </svg>
      
      {/* 显示选中节点的详情 */}
      {selectedNode && (
        <div className="node-details">
          <h4>{selectedNode.type === 'ai' ? 'AI' : '用户'} 详情</h4>
          <p>ID: {selectedNode.id}</p>
          <p>关系数量: {selectedNode.relations}</p>
          <button onClick={() => setSelectedNode(null)}>关闭</button>
        </div>
      )}
    </div>
  );
};

export default RelationshipNetwork;
