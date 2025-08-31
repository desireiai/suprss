// src/contexts/AppContext.jsx
import React, { createContext, useState, useEffect } from 'react';
import { initialCollections, initialArticles, sharedCollections } from '../utils/constants';

export const AppContext = createContext();

export const AppProvider = ({ children }) => {
  const [collections, setCollections] = useState(initialCollections);
  const [articles, setArticles] = useState(initialArticles);
  const [activeCollection, setActiveCollection] = useState(initialCollections[0]);
  const [activeView, setActiveView] = useState('feed');
  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Charger les données depuis localStorage au montage
  useEffect(() => {
    const savedCollections = localStorage.getItem('suprss_collections');
    if (savedCollections) {
      try {
        setCollections(JSON.parse(savedCollections));
      } catch (error) {
        console.error('Erreur lors du chargement des collections:', error);
      }
    }
  }, []);

  // Sauvegarder les collections dans localStorage
  useEffect(() => {
    localStorage.setItem('suprss_collections', JSON.stringify(collections));
  }, [collections]);

  // Fonction pour ajouter une nouvelle collection
  const addCollection = (collection) => {
    const newCollection = {
      ...collection,
      id: Date.now(),
      unreadCount: 0,
      feeds: [],
      members: [
        {
          id: 1,
          name: 'Vous',
          initials: 'VH',
          role: 'creator',
          permissions: ['read', 'add', 'edit', 'comment']
        }
      ],
      stats: {
        totalArticles: 0,
        weeklyArticles: 0,
        activeFeeds: 0,
        activeMembers: 1
      }
    };
    setCollections([...collections, newCollection]);
  };

  // Fonction pour mettre à jour une collection
  const updateCollection = (collectionId, updates) => {
    setCollections(collections.map(col => 
      col.id === collectionId ? { ...col, ...updates } : col
    ));
  };

  // Fonction pour supprimer une collection
  const deleteCollection = (collectionId) => {
    setCollections(collections.filter(col => col.id !== collectionId));
    if (activeCollection?.id === collectionId) {
      setActiveCollection(collections[0]);
    }
  };

  // Fonction pour ajouter un flux RSS à une collection
  const addFeedToCollection = (collectionId, feed) => {
    setCollections(collections.map(col => 
      col.id === collectionId 
        ? { 
            ...col, 
            feeds: [...(col.feeds || []), { ...feed, id: Date.now() }],
            stats: {
              ...col.stats,
              activeFeeds: (col.stats?.activeFeeds || 0) + 1
            }
          }
        : col
    ));
  };

  // Fonction pour marquer un article comme lu
  const markArticleAsRead = (articleId) => {
    setArticles(articles.map(article =>
      article.id === articleId ? { ...article, unread: false } : article
    ));
  };

  // Fonction pour ajouter/retirer des favoris
  const toggleFavorite = (articleId) => {
    setArticles(articles.map(article =>
      article.id === articleId 
        ? { ...article, favorite: !article.favorite } 
        : article
    ));
  };

  // Fonction pour filtrer les articles
  const getFilteredArticles = () => {
    let filtered = [...articles];

    // Filtrer par terme de recherche
    if (searchTerm) {
      filtered = filtered.filter(article =>
        article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        article.excerpt.toLowerCase().includes(searchTerm.toLowerCase()) ||
        article.source.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filtrer par type
    switch (activeFilter) {
      case 'unread':
        filtered = filtered.filter(article => article.unread);
        break;
      case 'favorites':
        filtered = filtered.filter(article => article.favorite);
        break;
      case 'today':
        // Filtrer les articles d'aujourd'hui
        filtered = filtered.filter(article => 
          article.time.includes('h') || article.time.includes('minute')
        );
        break;
      case 'week':
        // Filtrer les articles de cette semaine
        filtered = filtered.filter(article => 
          !article.time.includes('mois') && !article.time.includes('année')
        );
        break;
      default:
        // 'all' - pas de filtre
        break;
    }

    return filtered;
  };

  // Fonction pour ajouter un membre à une collection
  const addMemberToCollection = (collectionId, member) => {
    setCollections(collections.map(col => 
      col.id === collectionId 
        ? { 
            ...col, 
            members: [...(col.members || []), { ...member, id: Date.now() }],
            stats: {
              ...col.stats,
              activeMembers: (col.stats?.activeMembers || 0) + 1
            }
          }
        : col
    ));
  };

  // Fonction pour mettre à jour les permissions d'un membre
  const updateMemberPermissions = (collectionId, memberId, permissions) => {
    setCollections(collections.map(col => 
      col.id === collectionId 
        ? { 
            ...col, 
            members: col.members.map(member =>
              member.id === memberId 
                ? { ...member, permissions }
                : member
            )
          }
        : col
    ));
  };

  const value = {
    // État
    collections,
    sharedCollections,
    articles,
    activeCollection,
    activeView,
    searchTerm,
    activeFilter,
    sidebarOpen,
    
    // Setters
    setCollections,
    setActiveCollection,
    setActiveView,
    setSearchTerm,
    setActiveFilter,
    setSidebarOpen,
    
    // Actions
    addCollection,
    updateCollection,
    deleteCollection,
    addFeedToCollection,
    markArticleAsRead,
    toggleFavorite,
    getFilteredArticles,
    addMemberToCollection,
    updateMemberPermissions
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};