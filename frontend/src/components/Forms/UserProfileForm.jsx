// frontend/src/components/Forms/UserProfileForm.jsx
import React, { useState } from 'react';
import { User, Mail, Lock, Bell, Eye, Globe, Palette, Save, AlertCircle } from 'lucide-react';

const UserProfileForm = ({ user, onSubmit, onPasswordChange }) => {
  const [activeTab, setActiveTab] = useState('profile');
  const [formData, setFormData] = useState({
    // Informations personnelles
    nom_utilisateur: user?.nom_utilisateur || '',
    prenom: user?.prenom || '',
    nom: user?.nom || '',
    email: user?.email || '',
    bio: user?.bio || '',
    
    // Préférences
    preferences: {
      theme: user?.preferences?.theme || 'light',
      langue: user?.preferences?.langue || 'fr',
      fuseau_horaire: user?.preferences?.fuseau_horaire || 'Europe/Paris',
      format_date: user?.preferences?.format_date || 'DD/MM/YYYY',
      articles_par_page: user?.preferences?.articles_par_page || 20,
      affichage_images: user?.preferences?.affichage_images !== false,
      mode_lecture: user?.preferences?.mode_lecture || 'card',
      taille_police: user?.preferences?.taille_police || 'medium'
    },
    
    // Notifications
    notifications: {
      nouveaux_articles: user?.notifications?.nouveaux_articles !== false,
      partages_collections: user?.notifications?.partages_collections !== false,
      commentaires: user?.notifications?.commentaires !== false,
      newsletter: user?.notifications?.newsletter || false,
      frequence_resume: user?.notifications?.frequence_resume || 'daily',
      email_notifications: user?.notifications?.email_notifications !== false,
      push_notifications: user?.notifications?.push_notifications || false
    }
  });

  const [passwordData, setPasswordData] = useState({
    ancien_mot_de_passe: '',
    nouveau_mot_de_passe: '',
    confirmation: ''
  });

  const [errors, setErrors] = useState({});
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const tabs = [
    { id: 'profile', label: 'Profil', icon: User },
    { id: 'preferences', label: 'Préférences', icon: Palette },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Sécurité', icon: Lock }
  ];

  const handleInputChange = (e, section = null) => {
    const { name, value, type, checked } = e.target;
    
    if (section) {
      setFormData(prev => ({
        ...prev,
        [section]: {
          ...prev[section],
          [name]: type === 'checkbox' ? checked : value
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }

    // Effacer l'erreur
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handlePasswordChange = (e) => {
    const { name, value } = e.target;
    setPasswordData(prev => ({ ...prev, [name]: value }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateProfile = () => {
    const newErrors = {};

    if (!formData.nom_utilisateur) {
      newErrors.nom_utilisateur = 'Le nom d\'utilisateur est requis';
    }
    if (!formData.email) {
      newErrors.email = 'L\'email est requis';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email invalide';
    }

    return newErrors;
  };

  const validatePassword = () => {
    const newErrors = {};

    if (!passwordData.ancien_mot_de_passe) {
      newErrors.ancien_mot_de_passe = 'L\'ancien mot de passe est requis';
    }
    if (!passwordData.nouveau_mot_de_passe) {
      newErrors.nouveau_mot_de_passe = 'Le nouveau mot de passe est requis';
    } else if (passwordData.nouveau_mot_de_passe.length < 6) {
      newErrors.nouveau_mot_de_passe = 'Le mot de passe doit contenir au moins 6 caractères';
    }
    if (passwordData.nouveau_mot_de_passe !== passwordData.confirmation) {
      newErrors.confirmation = 'Les mots de passe ne correspondent pas';
    }

    return newErrors;
  };

  const handleSubmitProfile = async (e) => {
    e.preventDefault();
    
    const newErrors = validateProfile();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);
    try {
      await onSubmit(formData);
      setSuccessMessage('Profil mis à jour avec succès');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setErrors({ general: 'Erreur lors de la mise à jour du profil' });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitPassword = async (e) => {
    e.preventDefault();
    
    const newErrors = validatePassword();
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setIsLoading(true);
    try {
      await onPasswordChange(passwordData);
      setPasswordData({
        ancien_mot_de_passe: '',
        nouveau_mot_de_passe: '',
        confirmation: ''
      });
      setSuccessMessage('Mot de passe modifié avec succès');
      setTimeout(() => setSuccessMessage(''), 3000);
    } catch (error) {
      setErrors({ ancien_mot_de_passe: 'Mot de passe incorrect' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="profile-form-container">
      <div className="profile-tabs">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`profile-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <tab.icon size={18} />
            {tab.label}
          </button>
        ))}
      </div>

      {successMessage && (
        <div className="success-message">
          <AlertCircle size={20} />
          {successMessage}
        </div>
      )}

      {errors.general && (
        <div className="error-banner">
          <AlertCircle size={20} />
          {errors.general}
        </div>
      )}

      <div className="profile-content">
        {/* Onglet Profil */}
        {activeTab === 'profile' && (
          <div className="tab-panel">
            <h3>Informations personnelles</h3>
            
            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Prénom</label>
                <input
                  type="text"
                  name="prenom"
                  value={formData.prenom}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="John"
                />
              </div>

              <div className="form-group">
                <label className="form-label">Nom</label>
                <input
                  type="text"
                  name="nom"
                  value={formData.nom}
                  onChange={handleInputChange}
                  className="form-input"
                  placeholder="Doe"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                <User size={16} />
                Nom d'utilisateur
              </label>
              <input
                type="text"
                name="nom_utilisateur"
                value={formData.nom_utilisateur}
                onChange={handleInputChange}
                className={`form-input ${errors.nom_utilisateur ? 'error' : ''}`}
              />
              {errors.nom_utilisateur && (
                <span className="error-message">{errors.nom_utilisateur}</span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                <Mail size={16} />
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                className={`form-input ${errors.email ? 'error' : ''}`}
              />
              {errors.email && (
                <span className="error-message">{errors.email}</span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Bio</label>
              <textarea
                name="bio"
                value={formData.bio}
                onChange={handleInputChange}
                className="form-input form-textarea"
                placeholder="Parlez-nous de vous..."
                rows="4"
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={handleSubmitProfile}
              disabled={isLoading}
            >
              <Save size={18} />
              Enregistrer les modifications
            </button>
          </div>
        )}

        {/* Onglet Préférences */}
        {activeTab === 'preferences' && (
          <div className="tab-panel">
            <h3>Préférences d'affichage</h3>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">
                  <Palette size={16} />
                  Thème
                </label>
                <select
                  name="theme"
                  value={formData.preferences.theme}
                  onChange={(e) => handleInputChange(e, 'preferences')}
                  className="form-input form-select"
                >
                  <option value="light">Clair</option>
                  <option value="dark">Sombre</option>
                  <option value="auto">Automatique (système)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <Globe size={16} />
                  Langue
                </label>
                <select
                  name="langue"
                  value={formData.preferences.langue}
                  onChange={(e) => handleInputChange(e, 'preferences')}
                  className="form-input form-select"
                >
                  <option value="fr">Français</option>
                  <option value="en">English</option>
                  <option value="es">Español</option>
                  <option value="de">Deutsch</option>
                </select>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Fuseau horaire</label>
                <select
                  name="fuseau_horaire"
                  value={formData.preferences.fuseau_horaire}
                  onChange={(e) => handleInputChange(e, 'preferences')}
                  className="form-input form-select"
                >
                  <option value="Europe/Paris">Paris (GMT+1)</option>
                  <option value="Europe/London">Londres (GMT)</option>
                  <option value="America/New_York">New York (GMT-5)</option>
                  <option value="Asia/Tokyo">Tokyo (GMT+9)</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Format de date</label>
                <select
                  name="format_date"
                  value={formData.preferences.format_date}
                  onChange={(e) => handleInputChange(e, 'preferences')}
                  className="form-input form-select"
                >
                  <option value="DD/MM/YYYY">JJ/MM/AAAA</option>
                  <option value="MM/DD/YYYY">MM/JJ/AAAA</option>
                  <option value="YYYY-MM-DD">AAAA-MM-JJ</option>
                </select>
              </div>
            </div>

            <h4>Options de lecture</h4>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">
                  <Eye size={16} />
                  Mode d'affichage
                </label>
                <select
                  name="mode_lecture"
                  value={formData.preferences.mode_lecture}
                  onChange={(e) => handleInputChange(e, 'preferences')}
                  className="form-input form-select"
                >
                  <option value="card">Cartes</option>
                  <option value="list">Liste</option>
                  <option value="compact">Compact</option>
                  <option value="magazine">Magazine</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Articles par page</label>
                <input
                  type="number"
                  name="articles_par_page"
                  value={formData.preferences.articles_par_page}
                  onChange={(e) => handleInputChange(e, 'preferences')}
                  className="form-input"
                  min="10"
                  max="100"
                  step="10"
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">Taille de police</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="taille_police"
                    value="small"
                    checked={formData.preferences.taille_police === 'small'}
                    onChange={(e) => handleInputChange(e, 'preferences')}
                  />
                  <span>Petite</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="taille_police"
                    value="medium"
                    checked={formData.preferences.taille_police === 'medium'}
                    onChange={(e) => handleInputChange(e, 'preferences')}
                  />
                  <span>Normale</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="taille_police"
                    value="large"
                    checked={formData.preferences.taille_police === 'large'}
                    onChange={(e) => handleInputChange(e, 'preferences')}
                  />
                  <span>Grande</span>
                </label>
              </div>
            </div>

            <label className="checkbox-label">
              <input
                type="checkbox"
                name="affichage_images"
                checked={formData.preferences.affichage_images}
                onChange={(e) => handleInputChange(e, 'preferences')}
              />
              <span>Afficher les images dans les articles</span>
            </label>

            <button
              className="btn btn-primary"
              onClick={handleSubmitProfile}
              disabled={isLoading}
            >
              <Save size={18} />
              Enregistrer les préférences
            </button>
          </div>
        )}

        {/* Onglet Notifications */}
        {activeTab === 'notifications' && (
          <div className="tab-panel">
            <h3>Paramètres de notifications</h3>

            <div className="notification-section">
              <h4>Notifications par email</h4>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="email_notifications"
                  checked={formData.notifications.email_notifications}
                  onChange={(e) => handleInputChange(e, 'notifications')}
                />
                <span>Activer les notifications par email</span>
              </label>

              {formData.notifications.email_notifications && (
                <div className="notification-options">
                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="nouveaux_articles"
                      checked={formData.notifications.nouveaux_articles}
                      onChange={(e) => handleInputChange(e, 'notifications')}
                    />
                    <span>Nouveaux articles dans mes flux</span>
                  </label>

                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="partages_collections"
                      checked={formData.notifications.partages_collections}
                      onChange={(e) => handleInputChange(e, 'notifications')}
                    />
                    <span>Invitations à des collections partagées</span>
                  </label>

                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="commentaires"
                      checked={formData.notifications.commentaires}
                      onChange={(e) => handleInputChange(e, 'notifications')}
                    />
                    <span>Nouveaux commentaires sur mes partages</span>
                  </label>

                  <label className="checkbox-label">
                    <input
                      type="checkbox"
                      name="newsletter"
                      checked={formData.notifications.newsletter}
                      onChange={(e) => handleInputChange(e, 'notifications')}
                    />
                    <span>Newsletter SUPRSS</span>
                  </label>
                </div>
              )}
            </div>

            <div className="notification-section">
              <h4>Résumé périodique</h4>
              
              <div className="form-group">
                <label className="form-label">Fréquence des résumés</label>
                <select
                  name="frequence_resume"
                  value={formData.notifications.frequence_resume}
                  onChange={(e) => handleInputChange(e, 'notifications')}
                  className="form-input form-select"
                >
                  <option value="never">Jamais</option>
                  <option value="daily">Quotidien</option>
                  <option value="weekly">Hebdomadaire</option>
                  <option value="monthly">Mensuel</option>
                </select>
              </div>
            </div>

            <div className="notification-section">
              <h4>Notifications push</h4>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  name="push_notifications"
                  checked={formData.notifications.push_notifications}
                  onChange={(e) => handleInputChange(e, 'notifications')}
                />
                <span>Activer les notifications push (navigateur)</span>
              </label>
            </div>

            <button
              className="btn btn-primary"
              onClick={handleSubmitProfile}
              disabled={isLoading}
            >
              <Save size={18} />
              Enregistrer les notifications
            </button>
          </div>
        )}

        {/* Onglet Sécurité */}
        {activeTab === 'security' && (
          <div className="tab-panel">
            <h3>Changer le mot de passe</h3>

            <div className="form-group">
              <label className="form-label">Mot de passe actuel</label>
              <input
                type="password"
                name="ancien_mot_de_passe"
                value={passwordData.ancien_mot_de_passe}
                onChange={handlePasswordChange}
                className={`form-input ${errors.ancien_mot_de_passe ? 'error' : ''}`}
              />
              {errors.ancien_mot_de_passe && (
                <span className="error-message">{errors.ancien_mot_de_passe}</span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Nouveau mot de passe</label>
              <input
                type="password"
                name="nouveau_mot_de_passe"
                value={passwordData.nouveau_mot_de_passe}
                onChange={handlePasswordChange}
                className={`form-input ${errors.nouveau_mot_de_passe ? 'error' : ''}`}
              />
              {errors.nouveau_mot_de_passe && (
                <span className="error-message">{errors.nouveau_mot_de_passe}</span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">Confirmer le nouveau mot de passe</label>
              <input
                type="password"
                name="confirmation"
                value={passwordData.confirmation}
                onChange={handlePasswordChange}
                className={`form-input ${errors.confirmation ? 'error' : ''}`}
              />
              {errors.confirmation && (
                <span className="error-message">{errors.confirmation}</span>
              )}
            </div>

            <button
              className="btn btn-primary"
              onClick={handleSubmitPassword}
              disabled={isLoading}
            >
              <Lock size={18} />
              Modifier le mot de passe
            </button>

            <div className="security-info">
              <h4>Sessions actives</h4>
              <p className="text-muted">
                Gérez vos sessions actives et déconnectez-vous des appareils non reconnus.
              </p>
              {/* Liste des sessions actives à implémenter */}
            </div>

            <div className="danger-zone">
              <h4>Zone de danger</h4>
              <p className="text-muted">
                Actions irréversibles sur votre compte.
              </p>
              <button className="btn btn-danger">
                Supprimer mon compte
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserProfileForm;