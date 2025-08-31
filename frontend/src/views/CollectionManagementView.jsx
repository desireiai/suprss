// src/views/CollectionManagementView.jsx
import React, { useState } from 'react';
import { Settings, Rss, Users, BarChart } from 'lucide-react';
import { useApp } from '../hooks/useApp';
import Tab from '../components/Common/Tab';
import CollectionForm from '../components/Collections/CollectionForm';
import FeedsList from '../components/Collections/FeedsList';
import MembersList from '../components/Collections/MembersList';
import CollectionStats from '../components/Collections/CollectionStats';

const CollectionManagementView = () => {
  const { activeCollection } = useApp();
  const [activeTab, setActiveTab] = useState('general');

  const tabs = [
    { 
      id: 'general', 
      label: 'Paramètres généraux', 
      icon: Settings 
    },
    { 
      id: 'feeds', 
      label: `Flux RSS (${activeCollection?.feeds?.length || 0})`, 
      icon: Rss 
    },
    { 
      id: 'members', 
      label: `Membres (${activeCollection?.members?.length || 0})`, 
      icon: Users 
    },
    { 
      id: 'stats', 
      label: 'Statistiques', 
      icon: BarChart 
    }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general':
        return <CollectionForm collection={activeCollection} />;
      case 'feeds':
        return <FeedsList collection={activeCollection} />;
      case 'members':
        return <MembersList collection={activeCollection} />;
      case 'stats':
        return <CollectionStats collection={activeCollection} />;
      default:
        return null;
    }
  };

  return (
    <div className="main-container">
      <div className="page-header">
        <h1 className="page-title">Gestion de Collection</h1>
        <p className="page-subtitle">
          Configurez votre collection "{activeCollection?.name}" et gérez ses membres
        </p>
      </div>

      <div className="tabs">
        {tabs.map(tab => (
          <Tab
            key={tab.id}
            active={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
            icon={tab.icon}
          >
            {tab.label}
          </Tab>
        ))}
      </div>

      <div className="tab-content active">
        {renderTabContent()}
      </div>
    </div>
  );
};

export default CollectionManagementView;