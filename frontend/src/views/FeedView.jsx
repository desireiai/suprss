// src/views/FeedView.jsx
import React from 'react';
import { Plus } from 'lucide-react';
import { useApp } from '../hooks/useApp';
import ArticleCard from '../components/Articles/ArticleCard';
import ArticleFilters from '../components/Articles/ArticleFilters';
import SearchBar from '../components/Common/SearchBar';

const FeedView = () => {
  const { activeCollection, getFilteredArticles } = useApp();
  const filteredArticles = getFilteredArticles();

  return (
    <main className="content">
      <div className="content-header">
        <h1 className="content-title">{activeCollection?.name || 'Mes Flux'}</h1>
        <SearchBar className="desktop-only" />
      </div>

      <SearchBar className="mobile-only" />
      
      <ArticleFilters />

      <div className="articles-grid">
        {filteredArticles.length > 0 ? (
          filteredArticles.map(article => (
            <ArticleCard key={article.id} article={article} />
          ))
        ) : (
          <div className="no-articles">
            <p>Aucun article trouvé</p>
            <p className="text-muted">
              Essayez de modifier vos filtres ou d'ajouter de nouveaux flux RSS
            </p>
          </div>
        )}
      </div>

      <button className="floating-add" title="Ajouter un flux">
        <Plus size={24} />
      </button>
    </main>
  );
};

export default FeedView;