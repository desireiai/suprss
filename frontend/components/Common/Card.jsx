// src/components/Common/Card.jsx
import React from 'react';

const Card = ({ children, className = '', style = {} }) => {
  return (
    <div className={`card ${className}`} style={style}>
      {children}
    </div>
  );
};

export default Card;

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

// ===================================
// src/components/Common/SearchBar.jsx
import React from 'react';
import { Search } from 'lucide-react';
import { useApp } from '../../hooks/useApp';
import Button from './Button';

const SearchBar = ({ className = '' }) => {
  const { searchTerm, setSearchTerm } = useApp();

  const handleSearch = (e) => {
    e.preventDefault();
    // La recherche est automatique via le contexte
    console.log('Recherche:', searchTerm);
  };

  return (
    <div className={`search-bar ${className}`}>
      <input
        type="text"
        className="search-input"
        placeholder="Rechercher dans les articles..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && handleSearch(e)}
      />
      <Button variant="primary" onClick={handleSearch}>
        <Search size={16} />
        <span className="desktop-only">Rechercher</span>
      </Button>
    </div>
  );
};

export default SearchBar;