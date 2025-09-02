// frontend/src/components/Auth/OAuthCallback.jsx
import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const OAuthCallback = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Récupérer le code et le provider depuis l'URL
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const state = urlParams.get('state');
    const error = urlParams.get('error');

    if (error) {
      // Rediriger vers login avec erreur
      navigate('/login?error=oauth_denied');
      return;
    }

    if (code && state) {
      // Rediriger vers login avec le code
      navigate(`/login?code=${code}&state=${state}`);
    } else {
      navigate('/login');
    }
  }, [navigate]);

  return (
    <div className="oauth-loading-overlay">
      <div className="oauth-loading-content">
        <div className="oauth-loading-spinner"></div>
        <p className="oauth-loading-text">Connexion en cours...</p>
      </div>
    </div>
  );
};

export default OAuthCallback;