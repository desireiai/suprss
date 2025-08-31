// src/components/Articles/ArticleCard.jsx
import React, { useState } from 'react';
import { Eye, Star, Share2 } from 'lucide-react';
import { useApp } from '../../hooks/useApp';

const ArticleCard = ({ article }) => {
  const { markArticleAsRead, toggleFavorite } = useApp();
  const [isRead, setIsRead] = useState(!article.unread);
  const [isFavorite, setIsFavorite] = useState(article.favorite);

  const handleMarkAsRead = () => {
    setIsRead(!isRead);
    markArticleAsRead(article.id);
  };

  const handleToggleFavorite = () => {
    setIsFavorite(!isFavorite);
    toggleFavorite(article.id);
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: article.title,
        text: article.excerpt,
        url: window.location.href,
      }).catch(console.error);
    } else {
      // Fallback: copier le lien
      navigator.clipboard.writeText(window.location.href);
      alert('Lien copié dans le presse-papier !');
    }
  };

  return (
    <article className="article-card">
      <div className="article-meta">
        <span className="article-source">{article.source}</span>
        <span>•</span>
        <span>{article.time}</span>
        <span>•</span>
        <span>Par {article.author}</span>
      </div>
      
      <h2 className="article-title">
        {!isRead && <span className="unread-indicator"></span>}
        <a href="#">{article.title}</a>
      </h2>
      
      <p className="article-excerpt">{article.excerpt}</p>
      
      <div className="article-actions">
        <div className="article-tags">
          {article.tags.map(tag => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
        
        <div className="article-buttons">
          <button 
            className={`icon-btn ${isRead ? 'active' : ''}`}
            onClick={handleMarkAsRead}
            title="Marquer comme lu"
          >
            <Eye size={18} />
          </button>
          <button 
            className={`icon-btn ${isFavorite ? 'active' : ''}`}
            onClick={handleToggleFavorite}
            title="Ajouter aux favoris"
          >
            <Star size={18} />
          </button>
          <button 
            className="icon-btn" 
            onClick={handleShare}
            title="Partager"
          >
            <Share2 size={18} />
          </button>
        </div>
      </div>
    </article>
  );
};

export default ArticleCard;