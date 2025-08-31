// ===================================
// src/components/Common/Tab.jsx
import React from 'react';

const Tab = ({ children, active, onClick, icon: Icon }) => {
  return (
    <button
      className={`tab ${active ? 'active' : ''}`}
      onClick={onClick}
    >
      {Icon && <Icon size={16} className="tab-icon" />}
      {children}
    </button>
  );
};

export default Tab;
