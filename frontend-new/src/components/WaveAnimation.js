import React, { useEffect, useRef } from 'react';

const WaveAnimation = ({ position = 'bottom', color1 = '#6e45e2', color2 = '#88d3ce', height = 100 }) => {
  const svgRef = useRef(null);
  const pathRef1 = useRef(null);
  const pathRef2 = useRef(null);
  
  useEffect(() => {
    const svg = svgRef.current;
    const path1 = pathRef1.current;
    const path2 = pathRef2.current;
    
    if (!svg || !path1 || !path2) return;
    
    let phase1 = 0;
    let phase2 = Math.PI; // 反相位
    const frequency = 0.005;
    const amplitude = height * 0.3;
    
    const updatePath = () => {
      const width = svg.clientWidth;
      
      // 更新第一个波浪
      let d1 = `M 0 ${height}`;
      for (let x = 0; x <= width; x += 10) {
        const y = Math.sin(x * frequency + phase1) * amplitude + (height * 0.7);
        d1 += ` L ${x} ${y}`;
      }
      d1 += ` L ${width} ${height} L 0 ${height} Z`;
      path1.setAttribute('d', d1);
      
      // 更新第二个波浪
      let d2 = `M 0 ${height}`;
      for (let x = 0; x <= width; x += 10) {
        const y = Math.sin(x * frequency + phase2) * amplitude + (height * 0.8);
        d2 += ` L ${x} ${y}`;
      }
      d2 += ` L ${width} ${height} L 0 ${height} Z`;
      path2.setAttribute('d', d2);
      
      // 更新相位
      phase1 += 0.01;
      phase2 += 0.015;
      
      requestAnimationFrame(updatePath);
    };
    
    const resizeHandler = () => {
      svg.setAttribute('width', window.innerWidth);
    };
    
    window.addEventListener('resize', resizeHandler);
    resizeHandler();
    
    const animationId = requestAnimationFrame(updatePath);
    
    return () => {
      window.removeEventListener('resize', resizeHandler);
      cancelAnimationFrame(animationId);
    };
  }, [height]);
  
  const positionStyle = position === 'top' 
    ? { top: 0, transform: 'rotate(180deg)' } 
    : { bottom: 0 };
  
  return (
    <svg 
      ref={svgRef}
      height={height}
      width="100%"
      style={{
        position: 'absolute',
        left: 0,
        ...positionStyle,
        zIndex: -1,
        pointerEvents: 'none',
        overflow: 'hidden'
      }}
    >
      <defs>
        <linearGradient id="waveGradient1" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={color1} stopOpacity="0.3" />
          <stop offset="100%" stopColor={color2} stopOpacity="0.3" />
        </linearGradient>
        <linearGradient id="waveGradient2" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" stopColor={color2} stopOpacity="0.2" />
          <stop offset="100%" stopColor={color1} stopOpacity="0.2" />
        </linearGradient>
      </defs>
      <path ref={pathRef1} fill="url(#waveGradient1)" />
      <path ref={pathRef2} fill="url(#waveGradient2)" />
    </svg>
  );
};

export default WaveAnimation;
