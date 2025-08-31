// ===================================
// src/components/Common/Input.jsx
import React from 'react';

const Input = ({ 
  label, 
  type = 'text', 
  name, 
  value, 
  onChange, 
  placeholder = '', 
  required = false,
  disabled = false,
  className = ''
}) => {
  return (
    <>
      {label && (
        <label className="form-label" htmlFor={name}>
          {label}
          {required && <span className="required">*</span>}
        </label>
      )}
      <input
        type={type}
        id={name}
        name={name}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        required={required}
        disabled={disabled}
        className={`form-input ${className}`}
      />
    </>
  );
};

export default Input;