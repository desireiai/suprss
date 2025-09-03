// frontend/src/components/Forms/CreateCollectionForm.jsx
import React, { useState } from 'react';
import { Folder, Users, Lock, Globe, Hash, Palette, Plus, X } from 'lucide-react';

const CreateCollectionForm = ({ onSubmit, onCancel, initialData = null }) => {
  const [formData, setFormData] = useState({
    nom: initialData?.nom || '',
    description: initialData?.description || '',
    type: initialData?.type || 'personnelle',
    visibilite: initialData?.visibilite || 'privee',
    emoji: initialData?.emoji || '📁',
    couleur: initialData?.couleur || '#4A1A5C',
    tags_par_defaut: initialData?.tags_par_defaut || [],
    permissions_par_defaut: initialData?.permissions_par_defaut || {
      lecture: true,
      ajout_flux: false,
      modification: false,
      suppression: false,
      partage: false
    },
    membres_invites: []
  });

  const [errors, setErrors] = useState({});
  const [tagInput, setTagInput] = useState('');
  const [emailInput, setEmailInput] = useState('');
  const [currentStep, setCurrentStep] = useState(1);

  // Emojis disponibles pour les collections
  const availableEmojis = [
    '📁', '📰', '📚', '🔬', '💼', '🎯', 
    '🚀', '💡', '🌍', '🎨', '🏆', '⭐',
    '🔥', '💎', '🌟', '📊', '🎮', '🎬'
  ];

  // Couleurs prédéfinies
  const presetColors = [
    '#4A1A5C', '#6B2C7A', '#3B82F6', '#10B981',
    '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899',
    '#14B8A6', '#F97316', '#6366F1', '#84CC16'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handlePermissionChange = (permission) => {
    setFormData(prev => ({
      ...prev,
      permissions_par_defaut: {
        ...prev.permissions_par_defaut,
        [permission]: !prev.permissions_par_defaut[permission]
      }
    }));
  };

  const handleAddTag = (e) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!formData.tags_par_defaut.includes(tagInput.trim())) {
        setFormData(prev => ({
          ...prev,
          tags_par_defaut: [...prev.tags_par_defaut, tagInput.trim()]
        }));
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags_par_defaut: prev.tags_par_defaut.filter(tag => tag !== tagToRemove)
    }));
  };

  const handleAddEmail = () => {
    if (emailInput && /\S+@\S+\.\S+/.test(emailInput)) {
      if (!formData.membres_invites.includes(emailInput)) {
        setFormData(prev => ({
          ...prev,
          membres_invites: [...prev.membres_invites, emailInput]
        }));
      }
      setEmailInput('');
    } else {
      setErrors(prev => ({ ...prev, email: 'Email invalide' }));
    }
  };

  const handleRemoveEmail = (emailToRemove) => {
    setFormData(prev => ({
      ...prev,
      membres_invites: prev.membres_invites.filter(email => email !== emailToRemove)
    }));
  };

  const validateStep = (step) => {
    const newErrors = {};

    if (step === 1) {
      if (!formData.nom) {
        newErrors.nom = 'Le nom de la collection est requis';
      }
      if (!formData.description) {
        newErrors.description = 'La description est requise';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNextStep = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePreviousStep = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateStep(1)) {
      setCurrentStep(1);
      return;
    }

    const collectionData = {
      ...formData,
      tags_par_defaut: formData.tags_par_defaut.join(',')
    };

    if (onSubmit) {
      await onSubmit(collectionData);
    }
  };

  return (
    <div className="create-collection-form">
      <div className="form-header">
        <h2>
          <Folder size={24} />
          {initialData ? 'Modifier la collection' : 'Créer une nouvelle collection'}
        </h2>
        <div className="form-steps">
          <div className={`step ${currentStep >= 1 ? 'active' : ''}`}>
            <span>1</span>
            Informations
          </div>
          <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
            <span>2</span>
            Personnalisation
          </div>
          <div className={`step ${currentStep >= 3 ? 'active' : ''}`}>
            <span>3</span>
            Partage
          </div>
        </div>
      </div>

      <div className="form-body">
        {/* Étape 1: Informations de base */}
        {currentStep === 1 && (
          <div className="step-content">
            <h3>Informations de base</h3>
            
            <div className="form-group">
              <label className="form-label">
                Nom de la collection
              </label>
              <input
                type="text"
                name="nom"
                value={formData.nom}
                onChange={handleInputChange}
                className={`form-input ${errors.nom ? 'error' : ''}`}
                placeholder="Ma super collection"
              />
              {errors.nom && (
                <span className="error-message">{errors.nom}</span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                className={`form-input form-textarea ${errors.description ? 'error' : ''}`}
                placeholder="Décrivez le contenu et l'objectif de cette collection..."
                rows="4"
              />
              {errors.description && (
                <span className="error-message">{errors.description}</span>
              )}
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">
                  <Users size={16} />
                  Type de collection
                </label>
                <select
                  name="type"
                  value={formData.type}
                  onChange={handleInputChange}
                  className="form-input form-select"
                >
                  <option value="personnelle">Personnelle</option>
                  <option value="partagee">Partagée</option>
                  <option value="publique">Publique</option>
                </select>
                <p className="form-help">
                  {formData.type === 'personnelle' && 'Collection visible uniquement par vous'}
                  {formData.type === 'partagee' && 'Collection partagée avec des membres sélectionnés'}
                  {formData.type === 'publique' && 'Collection visible par tous les utilisateurs'}
                </p>
              </div>

              <div className="form-group">
                <label className="form-label">
                  {formData.visibilite === 'privee' ? <Lock size={16} /> : <Globe size={16} />}
                  Visibilité
                </label>
                <select
                  name="visibilite"
                  value={formData.visibilite}
                  onChange={handleInputChange}
                  className="form-input form-select"
                  disabled={formData.type === 'personnelle'}
                >
                  <option value="privee">Privée (sur invitation)</option>
                  <option value="publique">Publique (découvrable)</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                <Hash size={16} />
                Tags par défaut
              </label>
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
                className="form-input"
                placeholder="Entrez un tag et appuyez sur Entrée"
              />
              {formData.tags_par_defaut.length > 0 && (
                <div className="tags-list">
                  {formData.tags_par_defaut.map(tag => (
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
              <p className="form-help">
                Ces tags seront automatiquement ajoutés aux nouveaux flux de cette collection
              </p>
            </div>
          </div>
        )}

        {/* Étape 2: Personnalisation */}
        {currentStep === 2 && (
          <div className="step-content">
            <h3>Personnalisation</h3>
            
            <div className="form-group">
              <label className="form-label">
                Emoji de la collection
              </label>
              <div className="emoji-selector">
                {availableEmojis.map(emoji => (
                  <button
                    key={emoji}
                    type="button"
                    className={`emoji-option ${formData.emoji === emoji ? 'selected' : ''}`}
                    onClick={() => setFormData(prev => ({ ...prev, emoji }))}
                  >
                    {emoji}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                <Palette size={16} />
                Couleur de la collection
              </label>
              <div className="color-selector">
                {presetColors.map(color => (
                  <button
                    key={color}
                    type="button"
                    className={`color-option ${formData.couleur === color ? 'selected' : ''}`}
                    style={{ backgroundColor: color }}
                    onClick={() => setFormData(prev => ({ ...prev, couleur: color }))}
                  />
                ))}
                <input
                  type="color"
                  value={formData.couleur}
                  onChange={(e) => setFormData(prev => ({ ...prev, couleur: e.target.value }))}
                  className="color-picker"
                />
              </div>
            </div>

            <div className="collection-preview">
              <h4>Aperçu</h4>
              <div 
                className="preview-card"
                style={{ borderLeftColor: formData.couleur }}
              >
                <div className="preview-header">
                  <span className="preview-emoji">{formData.emoji}</span>
                  <div className="preview-info">
                    <h5>{formData.nom || 'Nom de la collection'}</h5>
                    <p>{formData.description || 'Description de la collection'}</p>
                  </div>
                </div>
                <div className="preview-stats">
                  <span className="preview-type">
                    {formData.type === 'personnelle' && '🔒 Personnelle'}
                    {formData.type === 'partagee' && '👥 Partagée'}
                    {formData.type === 'publique' && '🌍 Publique'}
                  </span>
                  <span className="preview-tags">
                    {formData.tags_par_defaut.length} tags
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Étape 3: Partage et permissions */}
        {currentStep === 3 && (
          <div className="step-content">
            <h3>Partage et permissions</h3>
            
            {formData.type !== 'personnelle' && (
              <>
                <div className="form-group">
                  <label className="form-label">
                    Permissions par défaut pour les nouveaux membres
                  </label>
                  <div className="permissions-list">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.permissions_par_defaut.lecture}
                        onChange={() => handlePermissionChange('lecture')}
                      />
                      <span>Lecture des articles</span>
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.permissions_par_defaut.ajout_flux}
                        onChange={() => handlePermissionChange('ajout_flux')}
                      />
                      <span>Ajouter des flux RSS</span>
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.permissions_par_defaut.modification}
                        onChange={() => handlePermissionChange('modification')}
                      />
                      <span>Modifier la collection</span>
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.permissions_par_defaut.suppression}
                        onChange={() => handlePermissionChange('suppression')}
                      />
                      <span>Supprimer des flux</span>
                    </label>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={formData.permissions_par_defaut.partage}
                        onChange={() => handlePermissionChange('partage')}
                      />
                      <span>Inviter d'autres membres</span>
                    </label>
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Inviter des membres (optionnel)
                  </label>
                  <div className="email-input-group">
                    <input
                      type="email"
                      value={emailInput}
                      onChange={(e) => {
                        setEmailInput(e.target.value);
                        if (errors.email) {
                          setErrors(prev => ({ ...prev, email: '' }));
                        }
                      }}
                      className={`form-input ${errors.email ? 'error' : ''}`}
                      placeholder="email@exemple.com"
                      onKeyPress={(e) => e.key === 'Enter' && handleAddEmail()}
                    />
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={handleAddEmail}
                    >
                      <Plus size={18} />
                      Ajouter
                    </button>
                  </div>
                  {errors.email && (
                    <span className="error-message">{errors.email}</span>
                  )}
                  
                  {formData.membres_invites.length > 0 && (
                    <div className="invited-members">
                      {formData.membres_invites.map(email => (
                        <div key={email} className="member-chip">
                          <span>{email}</span>
                          <button
                            type="button"
                            onClick={() => handleRemoveEmail(email)}
                            className="chip-remove"
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            )}

            {formData.type === 'personnelle' && (
              <div className="info-message">
                <p>
                  Cette collection est personnelle et ne peut pas être partagée avec d'autres utilisateurs.
                  Vous pouvez changer le type de collection pour activer le partage.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      <div className="form-footer">
        <button
          type="button"
          className="btn btn-secondary"
          onClick={onCancel}
        >
          Annuler
        </button>
        
        <div className="form-navigation">
          {currentStep > 1 && (
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handlePreviousStep}
            >
              Précédent
            </button>
          )}
          
          {currentStep < 3 ? (
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleNextStep}
            >
              Suivant
            </button>
          ) : (
            <button
              type="submit"
              className="btn btn-primary"
              onClick={handleSubmit}
            >
              {initialData ? 'Mettre à jour' : 'Créer la collection'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CreateCollectionForm;