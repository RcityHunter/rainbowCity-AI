import React from 'react';
import LoadingSpinner from './LoadingSpinner';
import './LoadingSpinner.css';

const LoadingOverlay = ({ message = '请稍候...' }) => {
  return (
    <div className="loading-overlay">
      <div className="spinner-container">
        <LoadingSpinner size="large" color="white" />
        <div className="spinner-text">{message}</div>
      </div>
    </div>
  );
};

export default LoadingOverlay;
