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