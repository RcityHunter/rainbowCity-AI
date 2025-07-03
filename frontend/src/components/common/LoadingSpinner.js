import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ size = 'medium', color = 'primary', text = null }) => {
  const sizeClass = `spinner-${size}`;
  const colorClass = `spinner-${color}`;

  return (
    <div className="spinner-container">
      <div className={`spinner ${sizeClass} ${colorClass}`}>
        <div className="spinner-circle"></div>
        <div className="spinner-circle"></div>
        <div className="spinner-circle"></div>
      </div>
      {text && <div className="spinner-text">{text}</div>}
    </div>
  );
};

export default LoadingSpinner;
