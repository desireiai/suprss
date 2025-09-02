// frontend/src/views/LoginView.jsx
import React, { useState, useEffect } from 'react';
import { Mail, Lock, Eye, EyeOff, Rss, Github, Chrome } from 'lucide-react';

// Icône Microsoft personnalisée
const MicrosoftIcon = () => (
  <svg width="20" height="20" viewBox="0 0 21 21" xmlns="http://www.w3.org/2000/svg">
    <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
    <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
    <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
    <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
  </svg>
);

const LoginView = ({ onLogin }) => {
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    firstName: '',
    lastName: '',
    username: ''
  });
  const [errors, setErrors] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [oauthLoading, setOauthLoading] = useState(null);

  // Configuration OAuth2
  const OAUTH_CONFIG = {
    google: {
      clientId: process.env.REACT_APP_GOOGLE_CLIENT_ID || 'your-google-client-id',
      redirectUri: `${window.location.origin}/auth/callback/google`,
      authUrl: 'https://accounts.google.com/o/oauth2/v2/auth',
      scope: 'openid email profile'
    },
    microsoft: {
      clientId: process.env.REACT_APP_MICROSOFT_CLIENT_ID || 'your-microsoft-client-id',
      redirectUri: `${window.location.origin}/auth/callback/microsoft`,
      authUrl: 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
      scope: 'openid email profile'
    },
    github: {
      clientId: process.env.REACT_APP_GITHUB_CLIENT_ID || 'your-github-client-id',
      redirectUri: `${window.location.origin}/auth/callback/github`,
      authUrl: 'https://github.com/login/oauth/authorize',
      scope: 'user:email'
    }
  };

  // Gérer le callback OAuth2
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');
      const state = urlParams.get('state');
      
      if (code && state) {
        try {
          const provider = state; // Le provider est stocké dans le state
          await handleOAuthLogin(provider, code);
        } catch (error) {
          console.error('OAuth callback error:', error);
          setErrors({ oauth: 'Erreur lors de la connexion OAuth' });
        }
      }
    };

    handleOAuthCallback();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Email validation
    if (!formData.email) {
      newErrors.email = 'L\'email est requis';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email invalide';
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Le mot de passe est requis';
    } else if (formData.password.length < 6) {
      newErrors.password = 'Le mot de passe doit contenir au moins 6 caractères';
    }

    // Additional validation for registration
    if (!isLoginMode) {
      if (!formData.username) {
        newErrors.username = 'Le nom d\'utilisateur est requis';
      }
      if (!formData.firstName) {
        newErrors.firstName = 'Le prénom est requis';
      }
      if (!formData.lastName) {
        newErrors.lastName = 'Le nom est requis';
      }
      if (!formData.confirmPassword) {
        newErrors.confirmPassword = 'Confirmez votre mot de passe';
      } else if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Les mots de passe ne correspondent pas';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      const endpoint = isLoginMode ? '/api/users/login' : '/api/users/register';
      
      // Pour la connexion, utiliser FormData pour OAuth2PasswordRequestForm
      let body;
      let headers = {};
      
      if (isLoginMode) {
        // FastAPI OAuth2PasswordRequestForm attend un form-data
        const formData = new FormData();
        formData.append('username', formData.email); // username est l'email
        formData.append('password', formData.password);
        body = formData;
      } else {
        // Pour l'inscription, envoyer du JSON
        headers = { 'Content-Type': 'application/json' };
        body = JSON.stringify({
          email: formData.email,
          mot_de_passe: formData.password,
          nom_utilisateur: formData.username,
          prenom: formData.firstName,
          nom: formData.lastName
        });
      }

      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}${endpoint}`, {
        method: 'POST',
        headers,
        body
      });

      const data = await response.json();

      if (response.ok) {
        // Stocker le token et les infos utilisateur
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        if (onLogin) {
          onLogin(data.user);
        }
      } else {
        // Gérer les erreurs
        if (data.detail) {
          if (data.detail.includes('email')) {
            setErrors({ email: data.detail });
          } else if (data.detail.includes('mot de passe')) {
            setErrors({ password: data.detail });
          } else {
            setErrors({ general: data.detail });
          }
        } else {
          setErrors({ general: 'Une erreur est survenue' });
        }
      }
    } catch (error) {
      console.error('Erreur de connexion:', error);
      setErrors({ general: 'Erreur de connexion au serveur' });
    } finally {
      setIsLoading(false);
    }
  };

  const initiateOAuth = (provider) => {
    setOauthLoading(provider);
    
    const config = OAUTH_CONFIG[provider];
    const params = new URLSearchParams({
      client_id: config.clientId,
      redirect_uri: config.redirectUri,
      response_type: 'code',
      scope: config.scope,
      state: provider // Stocker le provider dans le state
    });

    // Rediriger vers la page d'autorisation OAuth
    window.location.href = `${config.authUrl}?${params.toString()}`;
  };

  const handleOAuthLogin = async (provider, code) => {
    setOauthLoading(provider);
    
    try {
      // Échanger le code contre un token avec votre backend
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/users/oauth2/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          provider,
          token: code, // Votre backend devra échanger ce code contre un token
          redirect_uri: OAUTH_CONFIG[provider].redirectUri
        })
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        localStorage.setItem('user', JSON.stringify(data.user));
        
        if (onLogin) {
          onLogin(data.user);
        }
      } else {
        setErrors({ oauth: data.detail || 'Erreur de connexion OAuth' });
      }
    } catch (error) {
      console.error('OAuth login error:', error);
      setErrors({ oauth: 'Erreur lors de la connexion OAuth' });
    } finally {
      setOauthLoading(null);
    }
  };

  const toggleMode = () => {
    setIsLoginMode(!isLoginMode);
    setFormData({
      email: '',
      password: '',
      confirmPassword: '',
      firstName: '',
      lastName: '',
      username: ''
    });
    setErrors({});
  };

  return (
    <div className="login-container">
      <div className="login-left">
        <div className="login-brand">
          <div className="login-logo">
            <Rss size={40} />
          </div>
          <h1 className="login-title">SUPRSS</h1>
          <p className="login-subtitle">Système Unifié de Partage RSS</p>
        </div>
        
        <div className="login-features">
          <div className="feature-item">
            <div className="feature-icon">📰</div>
            <div className="feature-text">
              <h3>Centralisez vos flux RSS</h3>
              <p>Regroupez tous vos flux d'actualités en un seul endroit</p>
            </div>
          </div>
          <div className="feature-item">
            <div className="feature-icon">👥</div>
            <div className="feature-text">
              <h3>Partagez vos collections</h3>
              <p>Collaborez avec votre équipe sur des collections thématiques</p>
            </div>
          </div>
          <div className="feature-item">
            <div className="feature-icon">🚀</div>
            <div className="feature-text">
              <h3>Restez informé</h3>
              <p>Ne manquez plus aucune actualité importante de votre secteur</p>
            </div>
          </div>
        </div>
      </div>

      <div className="login-right">
        <div className="login-form-container">
          <div className="login-form-header">
            <h2>{isLoginMode ? 'Connexion' : 'Créer un compte'}</h2>
            <p>
              {isLoginMode 
                ? 'Connectez-vous pour accéder à vos flux RSS' 
                : 'Inscrivez-vous pour commencer à utiliser SUPRSS'}
            </p>
          </div>

          {/* Erreurs générales */}
          {errors.general && (
            <div className="error-banner">
              {errors.general}
            </div>
          )}

          {errors.oauth && (
            <div className="error-banner">
              {errors.oauth}
            </div>
          )}

          {/* Boutons OAuth2 */}
          <div className="oauth-buttons">
            <button
              type="button"
              className="oauth-btn google"
              onClick={() => initiateOAuth('google')}
              disabled={oauthLoading === 'google'}
            >
              {oauthLoading === 'google' ? (
                <span className="loading-spinner">⏳</span>
              ) : (
                <>
                  <Chrome size={20} />
                  <span>Continuer avec Google</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="oauth-btn microsoft"
              onClick={() => initiateOAuth('microsoft')}
              disabled={oauthLoading === 'microsoft'}
            >
              {oauthLoading === 'microsoft' ? (
                <span className="loading-spinner">⏳</span>
              ) : (
                <>
                  <MicrosoftIcon />
                  <span>Continuer avec Microsoft</span>
                </>
              )}
            </button>

            <button
              type="button"
              className="oauth-btn github"
              onClick={() => initiateOAuth('github')}
              disabled={oauthLoading === 'github'}
            >
              {oauthLoading === 'github' ? (
                <span className="loading-spinner">⏳</span>
              ) : (
                <>
                  <Github size={20} />
                  <span>Continuer avec GitHub</span>
                </>
              )}
            </button>
          </div>

          <div className="divider">
            <span>ou</span>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            {!isLoginMode && (
              <>
                <div className="form-group">
                  <label htmlFor="username">Nom d'utilisateur</label>
                  <input
                    type="text"
                    id="username"
                    name="username"
                    value={formData.username}
                    onChange={handleInputChange}
                    className={`form-input ${errors.username ? 'error' : ''}`}
                    placeholder="johndoe"
                  />
                  {errors.username && (
                    <span className="error-message">{errors.username}</span>
                  )}
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="firstName">Prénom</label>
                    <input
                      type="text"
                      id="firstName"
                      name="firstName"
                      value={formData.firstName}
                      onChange={handleInputChange}
                      className={`form-input ${errors.firstName ? 'error' : ''}`}
                      placeholder="John"
                    />
                    {errors.firstName && (
                      <span className="error-message">{errors.firstName}</span>
                    )}
                  </div>

                  <div className="form-group">
                    <label htmlFor="lastName">Nom</label>
                    <input
                      type="text"
                      id="lastName"
                      name="lastName"
                      value={formData.lastName}
                      onChange={handleInputChange}
                      className={`form-input ${errors.lastName ? 'error' : ''}`}
                      placeholder="Doe"
                    />
                    {errors.lastName && (
                      <span className="error-message">{errors.lastName}</span>
                    )}
                  </div>
                </div>
              </>
            )}

            <div className="form-group">
              <label htmlFor="email">Email</label>
              <div className="input-with-icon">
                <Mail size={20} className="input-icon" />
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`form-input with-icon ${errors.email ? 'error' : ''}`}
                  placeholder="john.doe@example.com"
                />
              </div>
              {errors.email && (
                <span className="error-message">{errors.email}</span>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="password">Mot de passe</label>
              <div className="input-with-icon">
                <Lock size={20} className="input-icon" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  className={`form-input with-icon ${errors.password ? 'error' : ''}`}
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                </button>
              </div>
              {errors.password && (
                <span className="error-message">{errors.password}</span>
              )}
            </div>

            {!isLoginMode && (
              <div className="form-group">
                <label htmlFor="confirmPassword">Confirmer le mot de passe</label>
                <div className="input-with-icon">
                  <Lock size={20} className="input-icon" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    className={`form-input with-icon ${errors.confirmPassword ? 'error' : ''}`}
                    placeholder="••••••••"
                  />
                </div>
                {errors.confirmPassword && (
                  <span className="error-message">{errors.confirmPassword}</span>
                )}
              </div>
            )}

            {isLoginMode && (
              <div className="form-options">
                <label className="checkbox-label">
                  <input type="checkbox" />
                  <span>Se souvenir de moi</span>
                </label>
                <a href="#" className="forgot-password">Mot de passe oublié ?</a>
              </div>
            )}

            <button 
              type="submit" 
              className="btn-submit"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="loading-spinner">⏳</span>
              ) : (
                isLoginMode ? 'Se connecter' : 'Créer mon compte'
              )}
            </button>
          </form>

          <div className="login-footer">
            <p>
              {isLoginMode ? "Pas encore de compte ?" : "Déjà un compte ?"}
              <button 
                type="button"
                className="link-button"
                onClick={toggleMode}
              >
                {isLoginMode ? "S'inscrire" : "Se connecter"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginView;