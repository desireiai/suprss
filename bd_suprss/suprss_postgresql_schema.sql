-- =====================================================
-- SCRIPT DE CRÉATION DU SCHÉMA SUPRSS - PostgreSQL
-- =====================================================

-- Création de la base de données (optionnel)
-- CREATE DATABASE suprss_db;
-- \c suprss_db;

-- Extensions utiles
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================
-- TYPES ÉNUMÉRÉS
-- =====================================================

CREATE TYPE role_membre AS ENUM (
    'proprietaire',
    'administrateur', 
    'moderateur',
    'membre'
);

CREATE TYPE format_export_import AS ENUM (
    'OPML',
    'JSON', 
    'CSV'
);

-- =====================================================
-- TABLE UTILISATEUR
-- =====================================================

CREATE TABLE utilisateur (
    id SERIAL PRIMARY KEY,
    nom_utilisateur VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    mot_de_passe_hash VARCHAR(255),
    prenom VARCHAR(100),
    nom VARCHAR(100),
    avatar_url TEXT,
    email_verifie BOOLEAN DEFAULT FALSE,
    token_verification_email VARCHAR(255),
    email_verifie_le TIMESTAMP,
    token_reset_password VARCHAR(255),
    token_reset_expire_le TIMESTAMP,
    fournisseur_oauth VARCHAR(50),
    id_oauth VARCHAR(100),
    est_actif BOOLEAN DEFAULT TRUE,
    mode_sombre BOOLEAN DEFAULT FALSE,
    taille_police VARCHAR(20) DEFAULT 'medium',
    derniere_connexion TIMESTAMP,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifie_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimisation des requêtes
CREATE INDEX idx_utilisateur_email ON utilisateur(email);
CREATE INDEX idx_utilisateur_nom_utilisateur ON utilisateur(nom_utilisateur);
CREATE INDEX idx_utilisateur_oauth ON utilisateur(fournisseur_oauth, id_oauth);
CREATE INDEX idx_utilisateur_token_verification ON utilisateur(token_verification_email);
CREATE INDEX idx_utilisateur_token_reset ON utilisateur(token_reset_password);

-- =====================================================
-- TABLE UTILISATEUR_OAUTH
-- =====================================================

CREATE TABLE utilisateur_oauth (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,

    -- Informations du provider
    provider VARCHAR(50) NOT NULL,             -- Exemple: 'google', 'github', 'microsoft'
    provider_user_id VARCHAR(255) NOT NULL,    -- ID unique du compte côté provider
    provider_email VARCHAR(255),
    provider_username VARCHAR(255),

    -- Tokens éventuels
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,

    -- Métadonnées
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    derniere_utilisation TIMESTAMP,

    -- Contraintes de relation et unicité
    CONSTRAINT fk_utilisateur_oauth_utilisateur
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id)
        ON DELETE CASCADE,

    CONSTRAINT uq_provider_user
        UNIQUE (provider, provider_user_id),

    CONSTRAINT uq_user_provider
        UNIQUE (utilisateur_id, provider)
);

-- Index pour optimisation
CREATE INDEX idx_utilisateur_oauth_utilisateur ON utilisateur_oauth(utilisateur_id);
CREATE INDEX idx_utilisateur_oauth_provider ON utilisateur_oauth(provider);
CREATE INDEX idx_utilisateur_oauth_provider_user ON utilisateur_oauth(provider, provider_user_id);
CREATE INDEX idx_utilisateur_oauth_cree_le ON utilisateur_oauth(cree_le DESC);


-- =====================================================
-- TABLE COLLECTION
-- =====================================================

CREATE TABLE collection (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    description TEXT,
    est_partagee BOOLEAN DEFAULT FALSE,
    proprietaire_id INTEGER NOT NULL,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifie_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_collection_proprietaire 
        FOREIGN KEY (proprietaire_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE
);

-- Index pour optimisation
CREATE INDEX idx_collection_proprietaire ON collection(proprietaire_id);
CREATE INDEX idx_collection_nom ON collection(nom);

-- =====================================================
-- TABLE FLUX_RSS
-- =====================================================

CREATE TABLE flux_rss (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    url TEXT UNIQUE NOT NULL,
    description TEXT,
    frequence_maj_heures INTEGER DEFAULT 24 CHECK (frequence_maj_heures > 0),
    est_actif BOOLEAN DEFAULT TRUE,
    derniere_maj TIMESTAMP,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifie_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimisation
CREATE INDEX idx_flux_rss_url ON flux_rss(url);
CREATE INDEX idx_flux_rss_actif ON flux_rss(est_actif);
CREATE INDEX idx_flux_rss_derniere_maj ON flux_rss(derniere_maj);

-- =====================================================
-- TABLE CATEGORIE
-- =====================================================

CREATE TABLE categorie (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    couleur VARCHAR(7) DEFAULT '#007bff', -- Format hex color
    utilisateur_id INTEGER NOT NULL,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_categorie_utilisateur 
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_categorie_par_utilisateur 
        UNIQUE(nom, utilisateur_id)
);

-- Index pour optimisation
CREATE INDEX idx_categorie_utilisateur ON categorie(utilisateur_id);

-- =====================================================
-- TABLE ARTICLE
-- =====================================================

CREATE TABLE article (
    id SERIAL PRIMARY KEY,
    flux_id INTEGER NOT NULL,
    titre VARCHAR(500) NOT NULL,
    lien TEXT NOT NULL,
    auteur VARCHAR(255),
    contenu TEXT,
    resume TEXT,
    guid VARCHAR(500) NOT NULL,
    publie_le TIMESTAMP,
    recupere_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifie_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_article_flux 
        FOREIGN KEY (flux_id) REFERENCES flux_rss(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_guid_par_flux 
        UNIQUE(guid, flux_id)
);

-- Index pour optimisation des requêtes
CREATE INDEX idx_article_flux ON article(flux_id);
CREATE INDEX idx_article_publie_le ON article(publie_le DESC);
CREATE INDEX idx_article_titre ON article USING gin(to_tsvector('french', titre));
CREATE INDEX idx_article_contenu ON article USING gin(to_tsvector('french', contenu));
CREATE INDEX idx_article_guid ON article(guid);

-- =====================================================
-- TABLE MEMBRE_COLLECTION
-- =====================================================

CREATE TABLE membre_collection (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL,
    utilisateur_id INTEGER NOT NULL,
    role role_membre DEFAULT 'membre',
    peut_ajouter_flux BOOLEAN DEFAULT TRUE,
    peut_lire BOOLEAN DEFAULT TRUE,
    peut_commenter BOOLEAN DEFAULT TRUE,
    peut_modifier BOOLEAN DEFAULT FALSE,
    peut_supprimer BOOLEAN DEFAULT FALSE,
    rejoint_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_membre_collection_collection 
        FOREIGN KEY (collection_id) REFERENCES collection(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_membre_collection_utilisateur 
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_membre_collection 
        UNIQUE(collection_id, utilisateur_id)
);

-- Index pour optimisation
CREATE INDEX idx_membre_collection_collection ON membre_collection(collection_id);
CREATE INDEX idx_membre_collection_utilisateur ON membre_collection(utilisateur_id);

-- =====================================================
-- TABLE COLLECTION_FLUX
-- =====================================================

CREATE TABLE collection_flux (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL,
    flux_id INTEGER NOT NULL,
    ajoute_par_utilisateur_id INTEGER NOT NULL,
    ajoute_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_collection_flux_collection 
        FOREIGN KEY (collection_id) REFERENCES collection(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_collection_flux_flux 
        FOREIGN KEY (flux_id) REFERENCES flux_rss(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_collection_flux_utilisateur 
        FOREIGN KEY (ajoute_par_utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_flux_par_collection 
        UNIQUE(collection_id, flux_id)
);

-- Index pour optimisation
CREATE INDEX idx_collection_flux_collection ON collection_flux(collection_id);
CREATE INDEX idx_collection_flux_flux ON collection_flux(flux_id);

-- =====================================================
-- TABLE FLUX_CATEGORIE
-- =====================================================

CREATE TABLE flux_categorie (
    id SERIAL PRIMARY KEY,
    flux_id INTEGER NOT NULL,
    categorie_id INTEGER NOT NULL,
    
    CONSTRAINT fk_flux_categorie_flux 
        FOREIGN KEY (flux_id) REFERENCES flux_rss(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_flux_categorie_categorie 
        FOREIGN KEY (categorie_id) REFERENCES categorie(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_flux_categorie 
        UNIQUE(flux_id, categorie_id)
);

-- Index pour optimisation
CREATE INDEX idx_flux_categorie_flux ON flux_categorie(flux_id);
CREATE INDEX idx_flux_categorie_categorie ON flux_categorie(categorie_id);

-- =====================================================
-- TABLE STATUT_UTILISATEUR_ARTICLE
-- =====================================================

CREATE TABLE statut_utilisateur_article (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    article_id INTEGER NOT NULL,
    est_lu BOOLEAN DEFAULT FALSE,
    est_favori BOOLEAN DEFAULT FALSE,
    lu_le TIMESTAMP,
    mis_en_favori_le TIMESTAMP,
    
    CONSTRAINT fk_statut_utilisateur 
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_statut_article 
        FOREIGN KEY (article_id) REFERENCES article(id) 
        ON DELETE CASCADE,
    CONSTRAINT unique_statut_utilisateur_article 
        UNIQUE(utilisateur_id, article_id)
);

-- Index pour optimisation
CREATE INDEX idx_statut_utilisateur ON statut_utilisateur_article(utilisateur_id);
CREATE INDEX idx_statut_article ON statut_utilisateur_article(article_id);
CREATE INDEX idx_statut_est_lu ON statut_utilisateur_article(est_lu);
CREATE INDEX idx_statut_est_favori ON statut_utilisateur_article(est_favori);

-- =====================================================
-- TABLE COMMENTAIRE_ARTICLE
-- =====================================================

CREATE TABLE commentaire_article (
    id SERIAL PRIMARY KEY,
    article_id INTEGER NOT NULL,
    utilisateur_id INTEGER NOT NULL,
    collection_id INTEGER NOT NULL,
    contenu TEXT NOT NULL,
    commentaire_parent_id INTEGER,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifie_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_commentaire_article 
        FOREIGN KEY (article_id) REFERENCES article(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_commentaire_utilisateur 
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_commentaire_collection 
        FOREIGN KEY (collection_id) REFERENCES collection(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_commentaire_parent 
        FOREIGN KEY (commentaire_parent_id) REFERENCES commentaire_article(id) 
        ON DELETE CASCADE
);

-- Index pour optimisation
CREATE INDEX idx_commentaire_article ON commentaire_article(article_id);
CREATE INDEX idx_commentaire_utilisateur ON commentaire_article(utilisateur_id);
CREATE INDEX idx_commentaire_collection ON commentaire_article(collection_id);
CREATE INDEX idx_commentaire_parent ON commentaire_article(commentaire_parent_id);
CREATE INDEX idx_commentaire_cree_le ON commentaire_article(cree_le DESC);

-- =====================================================
-- TABLE MESSAGE_COLLECTION
-- =====================================================

CREATE TABLE message_collection (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL,
    utilisateur_id INTEGER NOT NULL,
    contenu TEXT NOT NULL,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    modifie_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_message_collection 
        FOREIGN KEY (collection_id) REFERENCES collection(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_message_utilisateur 
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE
);

-- Index pour optimisation
CREATE INDEX idx_message_collection ON message_collection(collection_id);
CREATE INDEX idx_message_utilisateur ON message_collection(utilisateur_id);
CREATE INDEX idx_message_cree_le ON message_collection(cree_le DESC);

-- =====================================================
-- TABLE JOURNAL_EXPORT
-- =====================================================

CREATE TABLE journal_export (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    format format_export_import NOT NULL,
    nom_fichier VARCHAR(255) NOT NULL,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_export_utilisateur 
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE
);

-- Index pour optimisation
CREATE INDEX idx_export_utilisateur ON journal_export(utilisateur_id);
CREATE INDEX idx_export_cree_le ON journal_export(cree_le DESC);

-- =====================================================
-- TABLE JOURNAL_IMPORT
-- =====================================================

CREATE TABLE journal_import (
    id SERIAL PRIMARY KEY,
    utilisateur_id INTEGER NOT NULL,
    format format_export_import NOT NULL,
    nom_fichier VARCHAR(255) NOT NULL,
    flux_importes INTEGER DEFAULT 0,
    cree_le TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT fk_import_utilisateur 
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateur(id) 
        ON DELETE CASCADE
);

-- Index pour optimisation
CREATE INDEX idx_import_utilisateur ON journal_import(utilisateur_id);
CREATE INDEX idx_import_cree_le ON journal_import(cree_le DESC);

-- =====================================================
-- TRIGGERS POUR MISE À JOUR AUTOMATIQUE DES TIMESTAMPS
-- =====================================================

-- Fonction pour mettre à jour le champ modifie_le
CREATE OR REPLACE FUNCTION update_modifie_le_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modifie_le = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Application des triggers sur les tables concernées
CREATE TRIGGER update_utilisateur_modifie_le 
    BEFORE UPDATE ON utilisateur 
    FOR EACH ROW EXECUTE FUNCTION update_modifie_le_column();

CREATE TRIGGER update_collection_modifie_le 
    BEFORE UPDATE ON collection 
    FOR EACH ROW EXECUTE FUNCTION update_modifie_le_column();

CREATE TRIGGER update_flux_rss_modifie_le 
    BEFORE UPDATE ON flux_rss 
    FOR EACH ROW EXECUTE FUNCTION update_modifie_le_column();

CREATE TRIGGER update_article_modifie_le 
    BEFORE UPDATE ON article 
    FOR EACH ROW EXECUTE FUNCTION update_modifie_le_column();

CREATE TRIGGER update_commentaire_article_modifie_le 
    BEFORE UPDATE ON commentaire_article 
    FOR EACH ROW EXECUTE FUNCTION update_modifie_le_column();

CREATE TRIGGER update_message_collection_modifie_le 
    BEFORE UPDATE ON message_collection 
    FOR EACH ROW EXECUTE FUNCTION update_modifie_le_column();

-- =====================================================
-- FONCTION POUR AJOUTER AUTOMATIQUEMENT LE PROPRIÉTAIRE COMME MEMBRE
-- =====================================================

CREATE OR REPLACE FUNCTION ajouter_proprietaire_comme_membre()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO membre_collection (
        collection_id, 
        utilisateur_id, 
        role, 
        peut_ajouter_flux, 
        peut_lire, 
        peut_commenter, 
        peut_modifier, 
        peut_supprimer
    ) VALUES (
        NEW.id, 
        NEW.proprietaire_id, 
        'proprietaire', 
        TRUE, 
        TRUE, 
        TRUE, 
        TRUE, 
        TRUE
    );
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger pour ajouter automatiquement le propriétaire comme membre
CREATE TRIGGER trigger_ajouter_proprietaire_membre
    AFTER INSERT ON collection
    FOR EACH ROW EXECUTE FUNCTION ajouter_proprietaire_comme_membre();

-- =====================================================
-- VUES UTILES POUR L'APPLICATION
-- =====================================================

-- Vue pour les articles avec leur statut utilisateur
CREATE VIEW vue_articles_utilisateur AS
SELECT 
    a.id,
    a.titre,
    a.lien,
    a.auteur,
    a.resume,
    a.publie_le,
    f.nom as nom_flux,
    f.id as flux_id,
    COALESCE(s.est_lu, FALSE) as est_lu,
    COALESCE(s.est_favori, FALSE) as est_favori,
    s.lu_le,
    s.mis_en_favori_le,
    s.utilisateur_id
FROM article a
JOIN flux_rss f ON a.flux_id = f.id
LEFT JOIN statut_utilisateur_article s ON a.id = s.article_id;

-- Vue pour les collections avec informations détaillées
CREATE VIEW vue_collections_detaillees AS
SELECT 
    c.id,
    c.nom,
    c.description,
    c.est_partagee,
    c.cree_le,
    u.nom_utilisateur as proprietaire,
    COUNT(DISTINCT cf.flux_id) as nombre_flux,
    COUNT(DISTINCT mc.utilisateur_id) as nombre_membres
FROM collection c
JOIN utilisateur u ON c.proprietaire_id = u.id
LEFT JOIN collection_flux cf ON c.id = cf.collection_id
LEFT JOIN membre_collection mc ON c.id = mc.collection_id
GROUP BY c.id, c.nom, c.description, c.est_partagee, c.cree_le, u.nom_utilisateur;

-- =====================================================
-- COMMENTAIRES SUR LES TABLES
-- =====================================================

COMMENT ON TABLE utilisateur IS 'Table des utilisateurs de l''application SUPRSS';
COMMENT ON TABLE collection IS 'Collections de flux RSS (personnelles ou partagées)';
COMMENT ON TABLE flux_rss IS 'Flux RSS configurés dans l''application';
COMMENT ON TABLE article IS 'Articles récupérés depuis les flux RSS';
COMMENT ON TABLE membre_collection IS 'Membres des collections avec leurs permissions';
COMMENT ON TABLE statut_utilisateur_article IS 'Statut de lecture et favoris par utilisateur';
COMMENT ON TABLE commentaire_article IS 'Commentaires sur les articles dans les collections partagées';
COMMENT ON TABLE message_collection IS 'Messages de chat dans les collections partagées';

-- =====================================================
-- DONNÉES D'EXEMPLE (OPTIONNEL)
-- =====================================================

-- Insertion d'un utilisateur administrateur par défaut
-- INSERT INTO utilisateur (nom_utilisateur, email, mot_de_passe_hash, prenom, nom, est_actif)
-- VALUES ('admin', 'admin@suprss.local', crypt('admin123', gen_salt('bf')), 'Admin', 'System', TRUE);

-- =====================================================
-- FIN DU SCRIPT
-- =====================================================

-- Message de confirmation
SELECT 'Schéma SUPRSS créé avec succès!' as message;