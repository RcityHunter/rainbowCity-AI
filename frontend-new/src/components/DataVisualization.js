import React, { useEffect, useRef } from 'react';

const DataVisualization = ({ data = [], width = 500, height = 300 }) => {
  const canvasRef = useRef(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    
    // 设置canvas尺寸
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.scale(dpr, dpr);
    
    // 如果没有数据，生成一些随机数据用于展示
    const chartData = data.length > 0 ? data : Array.from({ length: 30 }, () => Math.random() * 100);
    
    // 清除画布
    ctx.clearRect(0, 0, width, height);
    
    // 绘制背景
    ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
    ctx.fillRect(0, 0, width, height);
    
    // 绘制网格
    ctx.strokeStyle = 'rgba(136, 211, 206, 0.1)';
    ctx.lineWidth = 1;
    
    // 水平网格线
    const gridStepY = height / 5;
    for (let i = 1; i < 5; i++) {
      const y = i * gridStepY;
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }
    
    // 垂直网格线
    const gridStepX = width / 10;
    for (let i = 1; i < 10; i++) {
      const x = i * gridStepX;
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    
    // 绘制数据线
    const dataPoints = chartData.map((value, index) => ({
      x: (index / (chartData.length - 1)) * width,
      y: height - (value / 100) * (height - 40)
    }));
    
    // 获取CSS变量
    const primaryColor = getComputedStyle(document.documentElement).getPropertyValue('--primary-color').trim();
    const secondaryColor = getComputedStyle(document.documentElement).getPropertyValue('--secondary-color').trim();
    
    // 创建渐变
    const gradient = ctx.createLinearGradient(0, 0, width, 0);
    gradient.addColorStop(0, primaryColor || '#6e45e2');
    gradient.addColorStop(1, secondaryColor || '#88d3ce');
    
    // 绘制线条
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 3;
    ctx.lineJoin = 'round';
    ctx.beginPath();
    dataPoints.forEach((point, index) => {
      if (index === 0) {
        ctx.moveTo(point.x, point.y);
      } else {
        // 使用贝塞尔曲线使线条更平滑
        const prevPoint = dataPoints[index - 1];
        const cpx1 = prevPoint.x + (point.x - prevPoint.x) / 2;
        const cpx2 = prevPoint.x + (point.x - prevPoint.x) / 2;
        ctx.bezierCurveTo(cpx1, prevPoint.y, cpx2, point.y, point.x, point.y);
      }
    });
    ctx.stroke();
    
    // 绘制区域填充
    ctx.lineTo(dataPoints[dataPoints.length - 1].x, height);
    ctx.lineTo(dataPoints[0].x, height);
    ctx.closePath();
    
    const fillGradient = ctx.createLinearGradient(0, 0, 0, height);
    fillGradient.addColorStop(0, `rgba(${parseInt(primaryColor.slice(1, 3), 16)}, ${parseInt(primaryColor.slice(3, 5), 16)}, ${parseInt(primaryColor.slice(5, 7), 16)}, 0.3)`);
    fillGradient.addColorStop(1, `rgba(${parseInt(secondaryColor.slice(1, 3), 16)}, ${parseInt(secondaryColor.slice(3, 5), 16)}, ${parseInt(secondaryColor.slice(5, 7), 16)}, 0.05)`);
    ctx.fillStyle = fillGradient;
    ctx.fill();
    
    // 绘制数据点
    dataPoints.forEach((point) => {
      ctx.fillStyle = '#88d3ce';
      ctx.beginPath();
      ctx.arc(point.x, point.y, 4, 0, Math.PI * 2);
      ctx.fill();
      
      ctx.fillStyle = '#6e45e2';
      ctx.beginPath();
      ctx.arc(point.x, point.y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
    
    // 添加标签
    ctx.fillStyle = 'rgba(224, 224, 224, 0.8)';
    ctx.font = '12px Inter, sans-serif';
    ctx.textAlign = 'center';
    
    // 添加一些随机标签
    const labels = ['AI-ID', '频率', '关系', '互动', '情感', '协作'];
    for (let i = 0; i < 6; i++) {
      const x = (i / 5) * width;
      ctx.fillText(labels[i], x, height - 10);
    }
    
    // 添加Y轴标签
    ctx.textAlign = 'right';
    for (let i = 0; i <= 5; i++) {
      const y = height - (i / 5) * (height - 40);
      ctx.fillText(`${i * 20}%`, 30, y + 4);
    }
    
    // 添加标题
    ctx.fillStyle = '#88d3ce';
    ctx.font = '14px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Rainbow City 数据分析', width / 2, 20);
    
  }, [data, width, height]);
  
  return (
    <div className="data-visualization">
      <canvas
        ref={canvasRef}
        style={{
          width: `${width}px`,
          height: `${height}px`,
          borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)'
        }}
      />
    </div>
  );
};

export default DataVisualization;
