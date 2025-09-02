// frontend/src/components/Layout/Header.jsx
import React, { useState } from 'react';
import { ChevronRight, Plus, X, Menu, User, LogOut } from 'lucide-react';
import { useApp } from '../../hooks/useApp';
import Button from '../Common/Button';

const Header = ({ user, onLogout }) => {
  const { activeCollection, activeView, setActiveView } = useApp();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleNavClick = (view) => {
    setActiveView(view);
    setMobileMenuOpen(false);
  };

  const handleLogout = () => {
    if (onLogout) {
      onLogout();
    }
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
              
              {/* Menu utilisateur */}
              <div className="user-dropdown desktop-only">
                <button 
                  className="user-button"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                  <div className="user-avatar">
                    {user?.firstName ? user.firstName[0].toUpperCase() : 'U'}
                  </div>
                  <span className="user-name">
                    {user?.firstName || user?.email?.split('@')[0] || 'Utilisateur'}
                  </span>
                </button>
                
                {userMenuOpen && (
                  <div className="user-dropdown-menu">
                    <div className="dropdown-header">
                      <div className="user-info">
                        <div className="user-full-name">
                          {user?.firstName} {user?.lastName}
                        </div>
                        <div className="user-email">{user?.email}</div>
                      </div>
                    </div>
                    <div className="dropdown-divider"></div>
                    <a href="#" className="dropdown-item">
                      <User size={16} />
                      Mon profil
                    </a>
                    <a href="#" className="dropdown-item">
                      Paramètres
                    </a>
                    <div className="dropdown-divider"></div>
                    <button 
                      className="dropdown-item logout"
                      onClick={handleLogout}
                    >
                      <LogOut size={16} />
                      Déconnexion
                    </button>
                  </div>
                )}
              </div>
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
          <div className="mobile-user-info">
            <div className="user-avatar">
              {user?.firstName ? user.firstName[0].toUpperCase() : 'U'}
            </div>
            <div>
              <div className="user-name">
                {user?.firstName} {user?.lastName}
              </div>
              <div className="user-email">{user?.email}</div>
            </div>
          </div>
          <div className="dropdown-divider"></div>
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
          <a href="#" className="nav-link">Mon profil</a>
          <div className="dropdown-divider"></div>
          <button 
            className="nav-link logout-mobile"
            onClick={handleLogout}
          >
            <LogOut size={16} /> Déconnexion
          </button>
        </div>
      )}
    </header>
  );
};

export default Header;