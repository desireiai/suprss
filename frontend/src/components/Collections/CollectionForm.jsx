import React, { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import Card from '../Common/Card';
import Button from '../Common/Button';
import Input from '../Common/Input';

const CollectionForm = ({ collection }) => {
  const { updateCollection } = useApp();
  const [formData, setFormData] = useState({
    name: collection?.name || '',
    type: collection?.type || 'shared',
    description: collection?.description || '',
    category: collection?.category || 'Technologie',
    visibility: collection?.visibility || 'private'
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = () => {
    if (collection?.id) {
      updateCollection(collection.id, formData);
      alert('Collection mise à jour avec succès !');
    }
  };

  const handleCancel = () => {
    setFormData({
      name: collection?.name || '',
      type: collection?.type || 'shared',
      description: collection?.description || '',
      category: collection?.category || 'Technologie',
      visibility: collection?.visibility || 'private'
    });
  };

  return (
    <Card>
      <div className="card-header">
        <h3 className="card-title">Informations de la collection</h3>
      </div>
      
      <div className="form-container">
        <div className="form-grid">
          <div className="form-group">
            <Input
              label="Nom de la collection"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Type de collection</label>
            <select
              name="type"
              className="form-input form-select"
              value={formData.type}
              onChange={handleInputChange}
            >
              <option value="personal">Personnelle</option>
              <option value="shared">Partagée</option>
            </select>
          </div>
          
          <div className="form-group full-width">
            <label className="form-label">Description</label>
            <textarea
              name="description"
              className="form-input form-textarea"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Décrivez le contenu de cette collection..."
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Catégorie principale</label>
            <select
              name="category"
              className="form-input form-select"
              value={formData.category}
              onChange={handleInputChange}
            >
              <option value="Technologie">Technologie</option>
              <option value="Sciences">Sciences</option>
              <option value="Business">Business</option>
              <option value="Actualités">Actualités</option>
              <option value="Lifestyle">Lifestyle</option>
            </select>
          </div>
          
          <div className="form-group">
            <label className="form-label">Visibilité</label>
            <select
              name="visibility"
              className="form-input form-select"
              value={formData.visibility}
              onChange={handleInputChange}
            >
              <option value="private">Privée (sur invitation)</option>
              <option value="public">Publique (découvrable)</option>
            </select>
          </div>
        </div>
        
        <div className="form-actions">
          <Button variant="secondary" onClick={handleCancel}>
            Annuler
          </Button>
          <Button variant="primary" onClick={handleSubmit}>
            Sauvegarder
          </Button>
        </div>
      </div>
    </Card>
  );
};

export default CollectionForm;