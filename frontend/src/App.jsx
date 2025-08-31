// src/App.jsx
import React from 'react';
import { AppProvider } from './contexts/AppContext';
import { useApp } from './hooks/useApp';
import Header from './components/Layout/Header';
import Sidebar from './components/Layout/Sidebar';
import FeedView from './views/FeedView';
import CollectionManagementView from './views/CollectionManagementView';
import './styles/index.css';

function AppContent() {
  const { activeView } = useApp();

  return (
    <div className="app">
      <Header />
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