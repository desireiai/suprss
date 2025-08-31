// src/components/Layout/Header.jsx
import React, { useState } from 'react';
import { ChevronRight, Plus, X, Menu } from 'lucide-react';
import { useApp } from '../../hooks/useApp';
import Button from '../Common/Button';

const Header = () => {
  const { activeCollection, activeView, setActiveView } = useApp();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavClick = (view) => {
    setActiveView(view);
    setMobileMenuOpen(false);
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="logo">SUPRSS</div>
        
        <nav className="header-nav desktop-only">
          <a 
            href="#" 
            className="nav-link" 
            onClick={(e) => {
              e.preventDefault();
              setActiveView('feed');
            }}
          >
            Mes flux
          </a>
          <a href="#" className="nav-link">Collections partagées</a>
          <a href="#" className="nav-link">Favoris</a>
        </nav>

        {activeView === 'manage' && (
          <div className="breadcrumb desktop-only">
            <a 
              href="#" 
              onClick={(e) => {
                e.preventDefault();
                setActiveView('feed');
              }}
            >
              Accueil
            </a>
            <ChevronRight size={16} />
            <a href="#">Collections</a>
            <ChevronRight size={16} />
            <span>{activeCollection?.name || 'Collection'}</span>
          </div>
        )}

        <div className="user-menu">
          {activeView === 'manage' ? (
            <a 
              href="#" 
              className="nav-link" 
              onClick={(e) => {
                e.preventDefault();
                setActiveView('feed');
              }}
            >
              Retour aux flux
            </a>
          ) : (
            <>
              <Button variant="secondary" className="desktop-only">
                <Plus size={16} /> Nouveau flux
              </Button>
              <a href="#" className="nav-link desktop-only">Profil</a>
            </>
          )}
          <button 
            className="mobile-menu-btn mobile-only"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {mobileMenuOpen && (
        <div className="mobile-menu">
          <a 
            href="#" 
            className="nav-link" 
            onClick={(e) => {
              e.preventDefault();
              handleNavClick('feed');
            }}
          >
            Mes flux
          </a>
          <a href="#" className="nav-link">Collections partagées</a>
          <a href="#" className="nav-link">Favoris</a>
          <a href="#" className="nav-link">Profil</a>
        </div>
      )}
    </header>
  );
};

export default Header;