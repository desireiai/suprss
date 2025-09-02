// frontend/src/App.jsx
import React, { useState, useEffect } from 'react';
import { AppProvider } from './contexts/AppContext';
import { useApp } from './hooks/useApp';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import FeedView from './views/FeedView';
import CollectionManagementView from './views/CollectionManagementView';
import LoginView from './views/LoginView';
import './styles/index.css';
import './styles/login.css'; // Import des styles de login

function AppContent() {
  const { activeView } = useApp();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // Vérifier si l'utilisateur est déjà connecté au chargement
  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser);
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('Erreur lors du chargement de l\'utilisateur:', error);
        localStorage.removeItem('user');
      }
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
  };

  // Écran de chargement
  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner-container">
          <div className="loading-spinner">⏳</div>
          <p>Chargement...</p>
        </div>
      </div>
    );
  }

  // Si pas authentifié, afficher la page de login
  if (!isAuthenticated) {
    return <LoginView onLogin={handleLogin} />;
  }

  // Application principale
  return (
    <div className="app">
      <Header user={user} onLogout={handleLogout} />
      {activeView === 'feed' ? (
        <div className="main-container">
          <Sidebar />
          <FeedView />
        </div>
      ) : (
        <CollectionManagementView />
      )}
    </div>
  );
}

function App() {
  return (
    <AppProvider>
      <AppContent />
    </AppProvider>
  );
}

export default App;