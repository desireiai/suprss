// frontend/src/components/Forms/ImportOPMLForm.jsx
import React, { useState } from 'react';
import { Upload, Download, FileText, Check, X, AlertCircle, Folder } from 'lucide-react';

const ImportOPMLForm = ({ collections = [], onImport, onExport }) => {
  const [mode, setMode] = useState('import'); // 'import' ou 'export'
  const [file, setFile] = useState(null);
  const [parsedFeeds, setParsedFeeds] = useState([]);
  const [selectedFeeds, setSelectedFeeds] = useState([]);
  const [targetCollection, setTargetCollection] = useState('');
  const [createNewCollection, setCreateNewCollection] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [errors, setErrors] = useState({});
  const [importStats, setImportStats] = useState(null);

  // Options d'export
  const [exportOptions, setExportOptions] = useState({
    includeCategories: true,
    includeMetadata: true,
    selectedCollections: []
  });

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.name.endsWith('.opml')) {
      setFile(selectedFile);
      parseOPMLFile(selectedFile);
      setErrors({});
    } else {
      setErrors({ file: 'Veuillez sélectionner un fichier OPML valide' });
    }
  };

  const parseOPMLFile = async (file) => {
    setIsProcessing(true);
    try {
      const text = await file.text();
      const parser = new DOMParser();
      const xmlDoc = parser.parseFromString(text, 'text/xml');
      
      const outlines = xmlDoc.querySelectorAll('outline[xmlUrl]');
      const feeds = [];
      
      outlines.forEach((outline) => {
        const feed = {
          title: outline.getAttribute('title') || outline.getAttribute('text'),
          url: outline.getAttribute('xmlUrl'),
          htmlUrl: outline.getAttribute('htmlUrl'),
          category: outline.parentElement.getAttribute('text') || 'Non catégorisé',
          selected: true
        };
        feeds.push(feed);
      });
      
      setParsedFeeds(feeds);
      setSelectedFeeds(feeds.map((_, index) => index));
      
      if (feeds.length === 0) {
        setErrors({ parse: 'Aucun flux RSS trouvé dans le fichier OPML' });
      }
    } catch (error) {
      console.error('Erreur parsing OPML:', error);
      setErrors({ parse: 'Erreur lors de la lecture du fichier OPML' });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleFeedToggle = (index) => {
    if (selectedFeeds.includes(index)) {
      setSelectedFeeds(selectedFeeds.filter(i => i !== index));
    } else {
      setSelectedFeeds([...selectedFeeds, index]);
    }
  };

  const handleSelectAll = () => {
    if (selectedFeeds.length === parsedFeeds.length) {
      setSelectedFeeds([]);
    } else {
      setSelectedFeeds(parsedFeeds.map((_, index) => index));
    }
  };

  const handleImport = async () => {
    if (selectedFeeds.length === 0) {
      setErrors({ import: 'Veuillez sélectionner au moins un flux' });
      return;
    }

    if (!createNewCollection && !targetCollection) {
      setErrors({ collection: 'Veuillez sélectionner une collection' });
      return;
    }

    if (createNewCollection && !newCollectionName) {
      setErrors({ collection: 'Veuillez entrer un nom pour la nouvelle collection' });
      return;
    }

    setIsProcessing(true);
    
    try {
      const feedsToImport = parsedFeeds.filter((_, index) => selectedFeeds.includes(index));
      
      const importData = {
        feeds: feedsToImport,
        collection_id: createNewCollection ? null : targetCollection,
        new_collection_name: createNewCollection ? newCollectionName : null
      };
      
      const result = await onImport(importData);
      
      setImportStats({
        total: feedsToImport.length,
        success: result.success || feedsToImport.length,
        failed: result.failed || 0
      });
      
      // Reset form après import réussi
      setTimeout(() => {
        setFile(null);
        setParsedFeeds([]);
        setSelectedFeeds([]);
        setImportStats(null);
      }, 5000);
      
    } catch (error) {
      console.error('Erreur import:', error);
      setErrors({ import: 'Erreur lors de l\'import des flux' });
    } finally {
      setIsProcessing(false);
    }
  };

  const handleExport = async () => {
    if (exportOptions.selectedCollections.length === 0) {
      setErrors({ export: 'Veuillez sélectionner au moins une collection' });
      return;
    }

    setIsProcessing(true);
    
    try {
      const exportData = await onExport(exportOptions);
      
      // Créer le fichier OPML
      const opmlContent = generateOPML(exportData);
      const blob = new Blob([opmlContent], { type: 'text/xml' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `suprss_export_${new Date().toISOString().split('T')[0]}.opml`;
      a.click();
      URL.revokeObjectURL(url);
      
    } catch (error) {
      console.error('Erreur export:', error);
      setErrors({ export: 'Erreur lors de l\'export des flux' });
    } finally {
      setIsProcessing(false);
    }
  };

  const generateOPML = (data) => {
    const date = new Date().toUTCString();
    
    let opml = `<?xml version="1.0" encoding="UTF-8"?>
<opml version="2.0">
  <head>
    <title>SUPRSS Export</title>
    <dateCreated>${date}</dateCreated>
    <dateModified>${date}</dateModified>
  </head>
  <body>`;

    if (exportOptions.includeCategories) {
      // Grouper par catégorie
      const categories = {};
      data.feeds.forEach(feed => {
        const category = feed.category || 'Non catégorisé';
        if (!categories[category]) {
          categories[category] = [];
        }
        categories[category].push(feed);
      });

      Object.entries(categories).forEach(([category, feeds]) => {
        opml += `\n    <outline text="${category}">`;
        feeds.forEach(feed => {
          opml += `\n      <outline type="rss" text="${feed.title}" title="${feed.title}" xmlUrl="${feed.url}" htmlUrl="${feed.htmlUrl || ''}" />`;
        });
        opml += `\n    </outline>`;
      });
    } else {
      // Export plat
      data.feeds.forEach(feed => {
        opml += `\n    <outline type="rss" text="${feed.title}" title="${feed.title}" xmlUrl="${feed.url}" htmlUrl="${feed.htmlUrl || ''}" />`;
      });
    }

    opml += `\n  </body>\n</opml>`;
    return opml;
  };

  return (
    <div className="opml-form-container">
      <div className="opml-form">
        <div className="form-header">
          <h2>Import / Export OPML</h2>
          <div className="mode-switcher">
            <button
              className={`mode-btn ${mode === 'import' ? 'active' : ''}`}
              onClick={() => setMode('import')}
            >
              <Upload size={18} />
              Importer
            </button>
            <button
              className={`mode-btn ${mode === 'export' ? 'active' : ''}`}
              onClick={() => setMode('export')}
            >
              <Download size={18} />
              Exporter
            </button>
          </div>
        </div>

        {/* Mode Import */}
        {mode === 'import' && (
          <div className="import-section">
            {!parsedFeeds.length ? (
              <div className="file-upload-zone">
                <input
                  type="file"
                  id="opml-file"
                  accept=".opml"
                  onChange={handleFileSelect}
                  className="file-input-hidden"
                />
                <label htmlFor="opml-file" className="file-upload-label">
                  <FileText size={48} />
                  <h3>Sélectionner un fichier OPML</h3>
                  <p>Glissez-déposez ou cliquez pour parcourir</p>
                  <span className="file-format">Format supporté: .opml</span>
                </label>
                
                {errors.file && (
                  <div className="error-message">
                    <AlertCircle size={16} />
                    {errors.file}
                  </div>
                )}
              </div>
            ) : (
              <div className="import-preview">
                <div className="preview-header">
                  <h3>
                    {parsedFeeds.length} flux trouvés dans {file.name}
                  </h3>
                  <button
                    className="btn-text"
                    onClick={() => {
                      setFile(null);
                      setParsedFeeds([]);
                      setSelectedFeeds([]);
                    }}
                  >
                    Changer de fichier
                  </button>
                </div>

                <div className="feeds-selection">
                  <div className="selection-header">
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={selectedFeeds.length === parsedFeeds.length}
                        onChange={handleSelectAll}
                      />
                      <span>Tout sélectionner ({selectedFeeds.length}/{parsedFeeds.length})</span>
                    </label>
                  </div>

                  <div className="feeds-list">
                    {parsedFeeds.map((feed, index) => (
                      <div key={index} className="feed-item">
                        <label className="checkbox-label">
                          <input
                            type="checkbox"
                            checked={selectedFeeds.includes(index)}
                            onChange={() => handleFeedToggle(index)}
                          />
                          <div className="feed-info">
                            <span className="feed-title">{feed.title}</span>
                            <span className="feed-category">{feed.category}</span>
                            <span className="feed-url">{feed.url}</span>
                          </div>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="collection-selection">
                  <h4>Destination</h4>
                  
                  <div className="radio-group">
                    <label className="radio-label">
                      <input
                        type="radio"
                        name="destination"
                        checked={!createNewCollection}
                        onChange={() => setCreateNewCollection(false)}
                      />
                      <span>Collection existante</span>
                    </label>
                    
                    {!createNewCollection && (
                      <select
                        className="form-input form-select"
                        value={targetCollection}
                        onChange={(e) => setTargetCollection(e.target.value)}
                      >
                        <option value="">Sélectionner une collection</option>
                        {collections.map(col => (
                          <option key={col.id} value={col.id}>
                            {col.emoji} {col.name}
                          </option>
                        ))}
                      </select>
                    )}
                  </div>

                  <div className="radio-group">
                    <label className="radio-label">
                      <input
                        type="radio"
                        name="destination"
                        checked={createNewCollection}
                        onChange={() => setCreateNewCollection(true)}
                      />
                      <span>Nouvelle collection</span>
                    </label>
                    
                    {createNewCollection && (
                      <input
                        type="text"
                        className="form-input"
                        placeholder="Nom de la nouvelle collection"
                        value={newCollectionName}
                        onChange={(e) => setNewCollectionName(e.target.value)}
                      />
                    )}
                  </div>
                </div>

                {errors.collection && (
                  <div className="error-message">
                    <AlertCircle size={16} />
                    {errors.collection}
                  </div>
                )}

                {errors.import && (
                  <div className="error-message">
                    <AlertCircle size={16} />
                    {errors.import}
                  </div>
                )}

                {importStats && (
                  <div className="import-stats">
                    <div className="stat-item success">
                      <Check size={20} />
                      {importStats.success} flux importés
                    </div>
                    {importStats.failed > 0 && (
                      <div className="stat-item error">
                        <X size={20} />
                        {importStats.failed} échecs
                      </div>
                    )}
                  </div>
                )}

                <div className="form-actions">
                  <button
                    className="btn btn-primary"
                    onClick={handleImport}
                    disabled={isProcessing || selectedFeeds.length === 0}
                  >
                    {isProcessing ? 'Import en cours...' : `Importer ${selectedFeeds.length} flux`}
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Mode Export */}
        {mode === 'export' && (
          <div className="export-section">
            <h3>Sélectionner les collections à exporter</h3>
            
            <div className="collections-selection">
              {collections.map(collection => (
                <label key={collection.id} className="checkbox-label collection-option">
                  <input
                    type="checkbox"
                    checked={exportOptions.selectedCollections.includes(collection.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setExportOptions(prev => ({
                          ...prev,
                          selectedCollections: [...prev.selectedCollections, collection.id]
                        }));
                      } else {
                        setExportOptions(prev => ({
                          ...prev,
                          selectedCollections: prev.selectedCollections.filter(id => id !== collection.id)
                        }));
                      }
                    }}
                  />
                  <div className="collection-info">
                    <span className="collection-name">
                      {collection.emoji} {collection.name}
                    </span>
                    <span className="collection-count">
                      {collection.feeds?.length || 0} flux
                    </span>
                  </div>
                </label>
              ))}
            </div>

            <div className="export-options">
              <h4>Options d'export</h4>
              
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={exportOptions.includeCategories}
                  onChange={(e) => setExportOptions(prev => ({
                    ...prev,
                    includeCategories: e.target.checked
                  }))}
                />
                <span>Inclure les catégories</span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={exportOptions.includeMetadata}
                  onChange={(e) => setExportOptions(prev => ({
                    ...prev,
                    includeMetadata: e.target.checked
                  }))}
                />
                <span>Inclure les métadonnées</span>
              </label>
            </div>

            {errors.export && (
              <div className="error-message">
                <AlertCircle size={16} />
                {errors.export}
              </div>
            )}

            <div className="form-actions">
              <button
                className="btn btn-primary"
                onClick={handleExport}
                disabled={isProcessing || exportOptions.selectedCollections.length === 0}
              >
                {isProcessing ? 'Export en cours...' : 'Exporter en OPML'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ImportOPMLForm;