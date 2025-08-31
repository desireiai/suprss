// src/components/Articles/ArticleFilters.jsx
import React from 'react';
import { useApp } from '../../hooks/useApp';

const ArticleFilters = () => {
  const { activeFilter, setActiveFilter } = useApp();

  const filters = [
    { id: 'all', label: 'Tous' },
    { id: 'unread', label: 'Non lus' },
    { id: 'favorites', label: 'Favoris' },
    { id: 'today', label: "Aujourd'hui" },
    { id: 'week', label: 'Cette semaine' }
  ];

  return (
    <div className="filters">
      {filters.map(filter => (
        <button
          key={filter.id}
          className={`filter-btn ${activeFilter === filter.id ? 'active' : ''}`}
          onClick={() => setActiveFilter(filter.id)}
        >
          {filter.label}
        </button>
      ))}
    </div>
  );
};

export default ArticleFilters;