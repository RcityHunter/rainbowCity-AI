import React from 'react';

const SvgPatterns = () => {
  return (
    <svg 
      width="0" 
      height="0" 
      style={{ position: 'absolute' }}
    >
      <defs>
        {/* 渐变定义 */}
        <linearGradient id="primaryGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#6e45e2" />
          <stop offset="100%" stopColor="#88d3ce" />
        </linearGradient>
        
        {/* 网格图案 */}
        <pattern id="gridPattern" width="20" height="20" patternUnits="userSpaceOnUse">
          <rect width="20" height="20" fill="none" />
          <path d="M 20 0 L 0 0 0 20" stroke="rgba(136, 211, 206, 0.1)" strokeWidth="1" fill="none" />
        </pattern>
        
        {/* 点状图案 */}
        <pattern id="dotPattern" width="20" height="20" patternUnits="userSpaceOnUse">
          <circle cx="10" cy="10" r="1" fill="rgba(110, 69, 226, 0.2)" />
        </pattern>
        
        {/* 波浪图案 */}
        <pattern id="wavePattern" width="100" height="20" patternUnits="userSpaceOnUse">
          <path 
            d="M0,10 C30,15 70,5 100,10" 
            fill="none" 
            stroke="rgba(136, 211, 206, 0.2)" 
            strokeWidth="1"
          />
        </pattern>
        
        {/* 滤镜效果 */}
        <filter id="glow">
          <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
          <feMerge>
            <feMergeNode in="coloredBlur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        
        {/* 噪点滤镜 */}
        <filter id="noise">
          <feTurbulence 
            type="fractalNoise" 
            baseFrequency="0.65" 
            numOctaves="3" 
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
          <feComponentTransfer>
            <feFuncA type="table" tableValues="0 0.05" />
          </feComponentTransfer>
          <feBlend in="SourceGraphic" mode="multiply" />
        </filter>
      </defs>
    </svg>
  );
};

export default SvgPatterns;
