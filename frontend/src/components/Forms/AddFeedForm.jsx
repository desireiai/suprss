// frontend/src/components/Forms/AddFeedForm.jsx
import React, { useState, useEffect } from 'react';
import { Rss, Link, Tag, Folder, Clock, AlertCircle, Check, X } from 'lucide-react';

const AddFeedForm = ({ onSubmit, onCancel, collections = [], initialData = null }) => {
  const [formData, setFormData] = useState({
    url: initialData?.url || '',
    nom: initialData?.nom || '',
    collection_id: initialData?.collection_id || '',
    categorie: initialData?.categorie || '',
    frequence_maj: initialData?.frequence_maj || 60,
    tags: initialData?.tags || [],
    actif: initialData?.actif !== undefined ? initialData.actif : true,
    notifications: initialData?.notifications || false
  });

  const [errors, setErrors] = useState({});
  const [isValidating, setIsValidating] = useState(false);
  const [urlValid, setUrlValid] = useState(null);
  const [feedInfo, setFeedInfo] = useState(null);
  const [tagInput, setTagInput] = useState('');

  // Catégories prédéfinies
  const categories = [
    'Technologie', 'Science', 'Business', 'Actualités', 
    'Sport', 'Culture', 'Santé', 'Éducation', 'Divertissement'
  ];

  // Fréquences de mise à jour
  const updateFrequencies = [
    { value: 15, label: 'Toutes les 15 minutes' },
    { value: 30, label: 'Toutes les 30 minutes' },
    { value: 60, label: 'Toutes les heures' },
    { value: 180, label: 'Toutes les 3 heures' },
    { value: 360, label: 'Toutes les 6 heures' },
    { value: 720, label: 'Toutes les 12 heures' },
    { value: 1440, label: 'Une fois par jour' }
  ];

  // Validation de l'URL RSS
  const validateRSSUrl = async () => {
    if (!formData.url) {
      setUrlValid(null);
      return;
    }

    setIsValidating(true);
    try {
      // Appel API pour valider et récupérer les infos du flux
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/feeds/validate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ url: formData.url })
      });

      if (response.ok) {
        const data = await response.json();
        setUrlValid(true);
        setFeedInfo(data);
        
        // Auto-remplir le nom si vide
        if (!formData.nom && data.title) {
          setFormData(prev => ({ ...prev, nom: data.title }));
        }
      } else {
        setUrlValid(false);
        setFeedInfo(null);
      }
    } catch (error) {
      console.error('Erreur validation RSS:', error);
      setUrlValid(false);
      // En dev, simuler une validation réussie
      if (process.env.NODE_ENV === 'development') {
        setUrlValid(true);
        setFeedInfo({
          title: 'Flux RSS de test',
          description: 'Description du flux',
          articles_count: 25
        });
      }
    } finally {
      setIsValidating(false);
    }
  };

  // Valider l'URL quand elle change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.url) {
        validateRSSUrl();
      }
    }, 1000);

    return () => clearTimeout(timer);
  }, [formData.url]);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Effacer l'erreur du champ
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleAddTag = (e) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!formData.tags.includes(tagInput.trim())) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, tagInput.trim()]
        }));
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.url) {
      newErrors.url = 'L\'URL du flux RSS est requise';
    } else if (!urlValid && urlValid !== null) {
      newErrors.url = 'L\'URL n\'est pas un flux RSS valide';
    }

    if (!formData.nom) {
      newErrors.nom = 'Le nom du flux est requis';
    }

    if (!formData.collection_id) {
      newErrors.collection_id = 'Veuillez sélectionner une collection';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const feedData = {
      ...formData,
      tags: formData.tags.join(',') // Convertir les tags en string pour l'API
    };

    if (onSubmit) {
      await onSubmit(feedData);
    }
  };

  return (
    <div className="feed-form-container">
      <div className="feed-form">
        <h2 className="form-title">
          <Rss size={24} />
          {initialData ? 'Modifier le flux RSS' : 'Ajouter un nouveau flux RSS'}
        </h2>

        {/* URL du flux */}
        <div className="form-group">
          <label className="form-label">
            <Link size={16} />
            URL du flux RSS
          </label>
          <div className="input-with-validation">
            <input
              type="url"
              name="url"
              value={formData.url}
              onChange={handleInputChange}
              className={`form-input ${errors.url ? 'error' : ''} ${urlValid === true ? 'valid' : ''}`}
              placeholder="https://example.com/rss.xml"
              disabled={initialData !== null} // Ne pas modifier l'URL en édition
            />
            {isValidating && (
              <span className="validation-icon loading">⏳</span>
            )}
            {urlValid === true && !isValidating && (
              <span className="validation-icon success">
                <Check size={20} />
              </span>
            )}
            {urlValid === false && !isValidating && (
              <span className="validation-icon error">
                <X size={20} />
              </span>
            )}
          </div>
          {errors.url && (
            <span className="error-message">{errors.url}</span>
          )}
          {feedInfo && (
            <div className="feed-preview">
              <p className="feed-preview-title">{feedInfo.title}</p>
              <p className="feed-preview-desc">{feedInfo.description}</p>
              <p className="feed-preview-count">
                {feedInfo.articles_count} articles disponibles
              </p>
            </div>
          )}
        </div>

        {/* Nom personnalisé */}
        <div className="form-group">
          <label className="form-label">
            Nom du flux
          </label>
          <input
            type="text"
            name="nom"
            value={formData.nom}
            onChange={handleInputChange}
            className={`form-input ${errors.nom ? 'error' : ''}`}
            placeholder="Mon flux RSS"
          />
          {errors.nom && (
            <span className="error-message">{errors.nom}</span>
          )}
        </div>

        {/* Collection */}
        <div className="form-group">
          <label className="form-label">
            <Folder size={16} />
            Collection
          </label>
          <select
            name="collection_id"
            value={formData.collection_id}
            onChange={handleInputChange}
            className={`form-input form-select ${errors.collection_id ? 'error' : ''}`}
          >
            <option value="">Sélectionner une collection</option>
            {collections.map(collection => (
              <option key={collection.id} value={collection.id}>
                {collection.emoji} {collection.name}
              </option>
            ))}
          </select>
          {errors.collection_id && (
            <span className="error-message">{errors.collection_id}</span>
          )}
        </div>

        <div className="form-row">
          {/* Catégorie */}
          <div className="form-group">
            <label className="form-label">Catégorie</label>
            <select
              name="categorie"
              value={formData.categorie}
              onChange={handleInputChange}
              className="form-input form-select"
            >
              <option value="">Sans catégorie</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Fréquence de mise à jour */}
          <div className="form-group">
            <label className="form-label">
              <Clock size={16} />
              Fréquence de mise à jour
            </label>
            <select
              name="frequence_maj"
              value={formData.frequence_maj}
              onChange={handleInputChange}
              className="form-input form-select"
            >
              {updateFrequencies.map(freq => (
                <option key={freq.value} value={freq.value}>
                  {freq.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Tags */}
        <div className="form-group">
          <label className="form-label">
            <Tag size={16} />
            Tags
          </label>
          <input
            type="text"
            value={tagInput}
            onChange={(e) => setTagInput(e.target.value)}
            onKeyDown={handleAddTag}
            className="form-input"
            placeholder="Entrez un tag et appuyez sur Entrée"
          />
          {formData.tags.length > 0 && (
            <div className="tags-list">
              {formData.tags.map(tag => (
                <span key={tag} className="tag-item">
                  {tag}
                  <button
                    type="button"
                    onClick={() => handleRemoveTag(tag)}
                    className="tag-remove"
                  >
                    <X size={14} />
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Options */}
        <div className="form-options">
          <label className="checkbox-label">
            <input
              type="checkbox"
              name="actif"
              checked={formData.actif}
              onChange={handleInputChange}
            />
            <span>Flux actif</span>
          </label>

          <label className="checkbox-label">
            <input
              type="checkbox"
              name="notifications"
              checked={formData.notifications}
              onChange={handleInputChange}
            />
            <span>Recevoir des notifications pour les nouveaux articles</span>
          </label>
        </div>

        {/* Actions */}
        <div className="form-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
          >
            Annuler
          </button>
          <button
            type="submit"
            className="btn btn-primary"
            onClick={handleSubmit}
            disabled={isValidating}
          >
            {initialData ? 'Mettre à jour' : 'Ajouter le flux'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AddFeedForm;