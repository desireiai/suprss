# SUPRSS - Système Unifié de Partage RSS

Une application React moderne pour gérer et partager des flux RSS avec une interface intuitive et des fonctionnalités de collaboration.

## 📋 Prérequis

- Node.js (version 14 ou supérieure)
- npm ou yarn
- Un éditeur de code (VS Code recommandé)



### 4. Copier les fichiers

Copiez tous les fichiers fournis dans leurs dossiers respectifs selon cette structure :

```
src/
├── index.js
├── App.jsx
├── contexts/
│   └── AppContext.jsx
├── components/
│   ├── Layout/
│   │   ├── Header.jsx
│   │   └── Sidebar.jsx
│   ├── Articles/
│   │   ├── ArticleCard.jsx
│   │   └── ArticleFilters.jsx
│   ├── Collections/
│   │   ├── CollectionForm.jsx
│   │   ├── FeedsList.jsx
│   │   ├── MembersList.jsx
│   │   └── CollectionStats.jsx
│   └── Common/
│       ├── Button.jsx
│       ├── Card.jsx
│       ├── Tab.jsx
│       ├── Input.jsx
│       └── SearchBar.jsx
├── views/
│   ├── FeedView.jsx
│   └── CollectionManagementView.jsx
├── hooks/
│   └── useApp.js
├── utils/
│   └── constants.js
└── styles/
    ├── index.css
    └── variables.css
```



L'application sera accessible sur `http://localhost:3000`

## 🎯 Fonctionnalités

### Actuelles
- ✅ Gestion de collections de flux RSS
- ✅ Interface de lecture d'articles
- ✅ Système de favoris et marquage lu/non-lu
- ✅ Gestion des membres et permissions
- ✅ Interface responsive (mobile/desktop)
- ✅ Filtres et recherche d'articles
- ✅ Statistiques des collections


## 🛠️ Technologies utilisées

- **React 18** - Framework UI
- **Lucide React** - Icônes
- **Context API** - Gestion d'état
- **CSS3** - Styles avec variables CSS
- **LocalStorage** - Persistance des données

## 📁 Structure du code

### Contextes
- `AppContext.jsx` : État global de l'application

### Composants
- **Layout** : Composants de structure (Header, Sidebar)
- **Articles** : Gestion et affichage des articles
- **Collections** : Gestion des collections et flux RSS
- **Common** : Composants réutilisables

### Vues
- `FeedView` : Page principale de lecture
- `CollectionManagementView` : Page de gestion des collections

### Hooks
- `useApp` : Hook pour accéder au contexte global

### Utils
- `constants.js` : Données initiales et constantes

## 🔧 Configuration

### Variables d'environnement

Créez un fichier `.env` à la racine du projet :

```env
REACT_APP_API_URL=http://localhost:3001/api
REACT_APP_REFRESH_INTERVAL=300000
```

### Personnalisation des styles

Les couleurs et variables CSS sont définies dans `src/styles/variables.css` :

```css
--primary-purple: #4A1A5C;
--light-purple: #6B2C7A;
--hover-purple: #5D2168;
```


## 🤝 Contribution

1. Fork le projet
2. Créez votre branche (`git checkout -b feature/AmazingFeature`)
3. Committez vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrez une Pull Request

## 📄 Licence

Ce projet est sous licence MIT

## 👥 Auteur

Votre nom - MENSAH YAO OLIVIER DESIRE

