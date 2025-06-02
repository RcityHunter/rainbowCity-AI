import React, { useEffect, useRef } from 'react';

const RISVisualization = ({ risScore, components }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    if (!canvasRef.current || !components) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    // 设置canvas的实际尺寸
    canvas.width = canvas.offsetWidth * dpr;
    canvas.height = canvas.offsetHeight * dpr;
    ctx.scale(dpr, dpr);
    
    // 清除画布
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // 设置画布样式
    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;
    const centerX = width / 2;
    const centerY = height / 2;
    const radius = Math.min(width, height) * 0.4;
    
    // 绘制背景圆环
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
    ctx.lineWidth = 10;
    ctx.strokeStyle = '#1a1a1a';
    ctx.stroke();
    
    // 绘制RIS分数圆环
    const risPercentage = risScore / 10; // 假设最高分为10
    const startAngle = -0.5 * Math.PI; // 从顶部开始
    const endAngle = startAngle + (2 * Math.PI * risPercentage);
    
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, startAngle, endAngle);
    ctx.lineWidth = 10;
    
    // 创建渐变色
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, '#6e45e2');
    gradient.addColorStop(1, '#88d3ce');
    ctx.strokeStyle = gradient;
    ctx.stroke();
    
    // 绘制中心文字
    ctx.font = 'bold 24px Arial';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(risScore.toFixed(1), centerX, centerY);
    
    ctx.font = '14px Arial';
    ctx.fillStyle = '#888888';
    ctx.fillText('RIS', centerX, centerY + 25);
    
    // 绘制组件指标
    if (components) {
      const componentKeys = Object.keys(components);
      const angleStep = (2 * Math.PI) / componentKeys.length;
      
      componentKeys.forEach((key, index) => {
        const value = components[key];
        const angle = startAngle + (index * angleStep);
        
        // 计算指标点的位置
        const indicatorRadius = radius * 0.7 * (value / 10);
        const x = centerX + Math.cos(angle) * indicatorRadius;
        const y = centerY + Math.sin(angle) * indicatorRadius;
        
        // 绘制连接线
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.lineWidth = 1;
        ctx.strokeStyle = '#444444';
        ctx.stroke();
        
        // 绘制指标点
        ctx.beginPath();
        ctx.arc(x, y, 5, 0, 2 * Math.PI);
        ctx.fillStyle = gradient;
        ctx.fill();
        
        // 绘制指标标签
        const labelRadius = radius * 1.2;
        const labelX = centerX + Math.cos(angle) * labelRadius;
        const labelY = centerY + Math.sin(angle) * labelRadius;
        
        ctx.font = '12px Arial';
        ctx.fillStyle = '#aaaaaa';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        // 将长标签名转换为缩写
        const label = key === 'interactionFrequency' ? 'Interaction' : 
                     key === 'emotionalDensity' ? 'Emotion' : 
                     key === 'collaborationDepth' ? 'Collab' : key;
        
        ctx.fillText(label, labelX, labelY);
      });
    }
  }, [risScore, components]);
  
  return (
    <div className="ris-visualization">
      <canvas 
        ref={canvasRef} 
        style={{ width: '100%', height: '250px', background: '#121212' }}
      />
    </div>
  );
};

export default RISVisualization;
