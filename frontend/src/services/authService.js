// frontend/src/services/authService.js

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

class AuthService {
  /**
   * Connexion classique avec email/mot de passe
   */
  async login(email, password) {
    const formData = new FormData();
    formData.append('username', email); // FastAPI OAuth2PasswordRequestForm attend 'username'
    formData.append('password', password);

    const response = await fetch(`${API_URL}/api/users/login`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur de connexion');
    }

    const data = await response.json();
    this.saveTokens(data);
    return data;
  }

  /**
   * Inscription
   */
  async register(userData) {
    const response = await fetch(`${API_URL}/api/users/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: userData.email,
        mot_de_passe: userData.password,
        nom_utilisateur: userData.username,
        prenom: userData.firstName,
        nom: userData.lastName
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur lors de l\'inscription');
    }

    return await response.json();
  }

  /**
   * Connexion OAuth2
   */
  async loginWithOAuth(provider, code, redirectUri) {
    const response = await fetch(`${API_URL}/api/users/oauth2/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        provider,
        token: code,
        redirect_uri: redirectUri
      })
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur de connexion OAuth');
    }

    const data = await response.json();
    this.saveTokens(data);
    return data;
  }

  /**
   * Récupère le profil de l'utilisateur actuel
   */
  async getCurrentUser() {
    const token = this.getToken();
    if (!token) {
      throw new Error('Non authentifié');
    }

    const response = await fetch(`${API_URL}/api/users/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expiré, essayer de rafraîchir
        await this.refreshToken();
        return this.getCurrentUser();
      }
      throw new Error('Erreur lors de la récupération du profil');
    }

    return await response.json();
  }

  /**
   * Rafraîchit le token d'accès
   */
  async refreshToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('Pas de refresh token');
    }

    const response = await fetch(`${API_URL}/api/users/refresh-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        refresh_token: refreshToken
      })
    });

    if (!response.ok) {
      this.logout();
      throw new Error('Session expirée');
    }

    const data = await response.json();
    this.saveTokens(data);
    return data;
  }

  /**
   * Déconnexion
   */
  logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    window.location.href = '/login';
  }

  /**
   * Sauvegarde les tokens et infos utilisateur
   */
  saveTokens(data) {
    if (data.access_token) {
      localStorage.setItem('token', data.access_token);
    }
    if (data.refresh_token) {
      localStorage.setItem('refresh_token', data.refresh_token);
    }
    if (data.user) {
      localStorage.setItem('user', JSON.stringify(data.user));
    }
  }

  /**
   * Récupère le token d'accès
   */
  getToken() {
    return localStorage.getItem('token');
  }

  /**
   * Vérifie si l'utilisateur est authentifié
   */
  isAuthenticated() {
    return !!this.getToken();
  }

  /**
   * Récupère les infos utilisateur stockées
   */
  getStoredUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  }

  /**
   * Configure les headers pour les requêtes authentifiées
   */
  getAuthHeaders() {
    const token = this.getToken();
    return token ? { 'Authorization': `Bearer ${token}` } : {};
  }

  /**
   * Intercepteur pour les requêtes API
   */
  async apiRequest(url, options = {}) {
    const token = this.getToken();
    
    const defaultOptions = {
      headers: {
        ...options.headers,
        ...(token && { 'Authorization': `Bearer ${token}` })
      }
    };

    const response = await fetch(`${API_URL}${url}`, {
      ...options,
      ...defaultOptions
    });

    // Si 401, essayer de rafraîchir le token
    if (response.status === 401 && token) {
      try {
        await this.refreshToken();
        // Réessayer la requête avec le nouveau token
        return this.apiRequest(url, options);
      } catch (error) {
        this.logout();
        throw error;
      }
    }

    return response;
  }

  /**
   * Demande de réinitialisation de mot de passe
   */
  async requestPasswordReset(email) {
    const response = await fetch(`${API_URL}/api/users/password-reset/request`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ email })
    });

    if (!response.ok && response.status !== 204) {
      throw new Error('Erreur lors de la demande de réinitialisation');
    }

    return true;
  }

  /**
   * Réinitialise le mot de passe avec le token
   */
  async resetPassword(token, newPassword) {
    const response = await fetch(`${API_URL}/api/users/password-reset/confirm`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        token,
        nouveau_mot_de_passe: newPassword
      })
    });

    if (!response.ok && response.status !== 204) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur lors de la réinitialisation');
    }

    return true;
  }

  /**
   * Change le mot de passe de l'utilisateur connecté
   */
  async changePassword(oldPassword, newPassword) {
    const response = await this.apiRequest('/api/users/me/change-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        ancien_mot_de_passe: oldPassword,
        nouveau_mot_de_passe: newPassword
      })
    });

    if (!response.ok && response.status !== 204) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur lors du changement de mot de passe');
    }

    return true;
  }

  /**
   * Met à jour le profil utilisateur
   */
  async updateProfile(profileData) {
    const response = await this.apiRequest('/api/users/me', {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(profileData)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Erreur lors de la mise à jour du profil');
    }

    const updatedUser = await response.json();
    localStorage.setItem('user', JSON.stringify(updatedUser));
    return updatedUser;
  }

  /**
   * Récupère les statistiques de l'utilisateur
   */
  async getUserStats() {
    const response = await this.apiRequest('/api/users/me/stats');

    if (!response.ok) {
      throw new Error('Erreur lors de la récupération des statistiques');
    }

    return await response.json();
  }
}

// Créer une instance unique (singleton)
const authService = new AuthService();

export default authService;