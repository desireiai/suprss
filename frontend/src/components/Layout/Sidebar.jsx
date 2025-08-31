// src/components/Layout/Sidebar.jsx
import React from 'react';
import { Menu, Plus, Settings } from 'lucide-react';
import { useApp } from '../../hooks/useApp';

const Sidebar = () => {
  const { 
    collections, 
    sharedCollections, 
    activeCollection, 
    setActiveCollection, 
    setActiveView,
    sidebarOpen,
    setSidebarOpen
  } = useApp();

  const handleCollectionClick = (collection) => {
    setActiveCollection(collection);
    setSidebarOpen(false);
  };

  const handleSettingsClick = (e, collection) => {
    e.stopPropagation();
    setActiveCollection(collection);
    setActiveView('manage');
    setSidebarOpen(false);
  };

  return (
    <>
      <button 
        className="sidebar-toggle mobile-only"
        onClick={() => setSidebarOpen(!sidebarOpen)}
      >
        <Menu size={20} />
      </button>

      <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
        <h3>Mes Collections</h3>
        {collections.map(collection => (
          <div
            key={collection.id}
            className={`collection-item ${activeCollection?.id === collection.id ? 'active' : ''}`}
            onClick={() => handleCollectionClick(collection)}
          >
            <div className="collection-header">
              <div className="collection-name">
                {collection.emoji} {collection.name}
              </div>
              {collection.id === activeCollection?.id && (
                <Settings 
                  size={16} 
                  className="collection-settings"
                  onClick={(e) => handleSettingsClick(e, collection)}
                />
              )}
            </div>
            <div className="collection-count">
              {collection.unreadCount} articles non lus
            </div>
          </div>
        ))}
        
        <div className="add-collection">
          <Plus size={16} /> Nouvelle collection
        </div>

        <h3 style={{ marginTop: '2rem' }}>Collections Partagées</h3>
        {sharedCollections.map(collection => (
          <div
            key={collection.id}
            className="collection-item"
            onClick={() => handleCollectionClick(collection)}
          >
            <div className="collection-name">
              {collection.emoji} {collection.name}
            </div>
            <div className="collection-count">
              {collection.unreadCount} articles non lus
            </div>
          </div>
        ))}
      </aside>
    </>
  );
};

export default Sidebar;