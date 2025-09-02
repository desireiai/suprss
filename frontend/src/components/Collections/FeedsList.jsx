// frontend/src/components/Collections/FeedsList.jsx
import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import { useApp } from '../../hooks/useApp';
import Card from '../Common/Card';
import Button from '../Common/Button';

const FeedsList = ({ collection }) => {
  const { addFeedToCollection, updateCollection } = useApp();
  const [showAddForm, setShowAddForm] = useState(false);
  const [newFeed, setNewFeed] = useState({
    name: '',
    url: '',
    tags: ''
  });

  const handleAddFeed = () => {
    if (newFeed.name && newFeed.url) {
      const feed = {
        ...newFeed,
        tags: newFeed.tags.split(',').map(tag => tag.trim()).filter(Boolean),
        active: true
      };
      addFeedToCollection(collection.id, feed);
      setNewFeed({ name: '', url: '', tags: '' });
      setShowAddForm(false);
    }
  };

  const handleDeleteFeed = (feedId) => {
    const updatedFeeds = collection.feeds.filter(feed => feed.id !== feedId);
    updateCollection(collection.id, { 
      feeds: updatedFeeds,
      stats: {
        ...collection.stats,
        activeFeeds: updatedFeeds.filter(f => f.active).length
      }
    });
  };

  const handleToggleFeedStatus = (feedId) => {
    const updatedFeeds = collection.feeds.map(feed =>
      feed.id === feedId ? { ...feed, active: !feed.active } : feed
    );
    updateCollection(collection.id, { 
      feeds: updatedFeeds,
      stats: {
        ...collection.stats,
        activeFeeds: updatedFeeds.filter(f => f.active).length
      }
    });
  };

  return (
    <Card>
      <div className="card-header">
        <h3 className="card-title">Flux RSS de la collection</h3>
        <Button 
          variant="primary" 
          size="small"
          onClick={() => setShowAddForm(!showAddForm)}
        >
          <Plus size={16} /> Ajouter un flux
        </Button>
      </div>
      
      {showAddForm && (
        <div className="add-feed-form">
          <div className="form-grid">
            <div className="form-group">
              <input
                type="text"
                className="form-input"
                placeholder="Nom du flux"
                value={newFeed.name}
                onChange={(e) => setNewFeed({ ...newFeed, name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <input
                type="url"
                className="form-input"
                placeholder="URL du flux RSS"
                value={newFeed.url}
                onChange={(e) => setNewFeed({ ...newFeed, url: e.target.value })}
              />
            </div>
            <div className="form-group full-width">
              <input
                type="text"
                className="form-input"
                placeholder="Tags (séparés par des virgules)"
                value={newFeed.tags}
                onChange={(e) => setNewFeed({ ...newFeed, tags: e.target.value })}
              />
            </div>
          </div>
          <div className="form-actions">
            <Button 
              variant="secondary" 
              size="small"
              onClick={() => {
                setShowAddForm(false);
                setNewFeed({ name: '', url: '', tags: '' });
              }}
            >
              Annuler
            </Button>
            <Button 
              variant="primary" 
              size="small"
              onClick={handleAddFeed}
            >
              Ajouter
            </Button>
          </div>
        </div>
      )}
      
      <div className="flux-list">
        {collection?.feeds?.length > 0 ? (
          collection.feeds.map(feed => (
            <div key={feed.id} className="flux-item">
              <div className="flux-info">
                <div className="flux-name">{feed.name}</div>
                <div className="flux-url">{feed.url}</div>
                <div className="flux-tags">
                  {feed.tags?.map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
              </div>
              <div className="flux-status">
                <div className={`status-indicator ${feed.active ? 'status-active' : 'status-inactive'}`}></div>
                <span>{feed.active ? 'Actif' : 'Inactif'}</span>
              </div>
              <div className="flux-actions">
                <Button 
                  variant="secondary" 
                  size="small"
                  onClick={() => handleToggleFeedStatus(feed.id)}
                >
                  {feed.active ? 'Désactiver' : 'Activer'}
                </Button>
                <Button 
                  variant="danger" 
                  size="small"
                  onClick={() => handleDeleteFeed(feed.id)}
                >
                  Supprimer
                </Button>
              </div>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <p>Aucun flux RSS dans cette collection</p>
            <p className="text-muted">Cliquez sur "Ajouter un flux" pour commencer</p>
          </div>
        )}
      </div>
    </Card>
  );
};

export default FeedsList;