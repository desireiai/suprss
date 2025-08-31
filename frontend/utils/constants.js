// src/utils/constants.js

export const initialCollections = [
  { 
    id: 1, 
    name: 'Actualités Tech', 
    type: 'shared',
    unreadCount: 12, 
    emoji: '📰',
    description: 'Collection dédiée aux actualités du monde de la technologie, startups, IA et innovations.',
    category: 'Technologie',
    visibility: 'private',
    feeds: [
      { 
        id: 1, 
        name: 'Le Monde Informatique', 
        url: 'https://www.lemondeinformatique.fr/rss/rss.xml', 
        tags: ['Tech', 'Actualités'], 
        active: true 
      },
      { 
        id: 2, 
        name: 'TechCrunch', 
        url: 'https://techcrunch.com/feed/', 
        tags: ['Startup', 'International'], 
        active: true 
      },
      { 
        id: 3, 
        name: 'Hacker News', 
        url: 'https://news.ycombinator.com/rss', 
        tags: ['Dev', 'Community'], 
        active: false 
      }
    ],
    members: [
      { 
        id: 1, 
        name: 'Vous', 
        initials: 'VH', 
        role: 'creator', 
        permissions: ['read', 'add', 'edit', 'comment'] 
      },
      { 
        id: 2, 
        name: 'Jean Dupont', 
        initials: 'JD', 
        role: 'member', 
        permissions: ['read', 'add', 'comment'] 
      },
      { 
        id: 3, 
        name: 'Sophie Martin', 
        initials: 'SM', 
        role: 'reader', 
        permissions: ['read'] 
      }
    ],
    stats: { 
      totalArticles: 156, 
      weeklyArticles: 23, 
      activeFeeds: 5, 
      activeMembers: 3 
    }
  },
  { 
    id: 2, 
    name: 'Sciences', 
    unreadCount: 5, 
    emoji: '🔬',
    type: 'personal',
    description: 'Articles scientifiques et découvertes',
    category: 'Sciences',
    visibility: 'private',
    feeds: [],
    members: [
      { 
        id: 1, 
        name: 'Vous', 
        initials: 'VH', 
        role: 'creator', 
        permissions: ['read', 'add', 'edit', 'comment'] 
      }
    ],
    stats: { 
      totalArticles: 45, 
      weeklyArticles: 5, 
      activeFeeds: 2, 
      activeMembers: 1 
    }
  },
  { 
    id: 3, 
    name: 'Business', 
    unreadCount: 8, 
    emoji: '🎯',
    type: 'personal',
    description: 'Actualités business et entrepreneuriat',
    category: 'Business',
    visibility: 'private',
    feeds: [],
    members: [
      { 
        id: 1, 
        name: 'Vous', 
        initials: 'VH', 
        role: 'creator', 
        permissions: ['read', 'add', 'edit', 'comment'] 
      }
    ],
    stats: { 
      totalArticles: 78, 
      weeklyArticles: 8, 
      activeFeeds: 3, 
      activeMembers: 1 
    }
  }
];

export const sharedCollections = [
  { 
    id: 4, 
    name: 'Équipe Dev', 
    unreadCount: 3, 
    emoji: '👥' 
  },
  { 
    id: 5, 
    name: 'Startup News', 
    unreadCount: 7, 
    emoji: '🚀' 
  }
];

export const initialArticles = [
  {
    id: 1,
    title: "L'intelligence artificielle révolutionne le développement web",
    source: 'Le Monde Informatique',
    author: 'Jean Dupont',
    time: 'Il y a 2h',
    excerpt: "Les nouvelles technologies d'IA commencent à transformer radicalement la façon dont nous développons des applications web. Entre génération de code automatique et optimisation des performances...",
    tags: ['IA', 'Développement', 'Web'],
    unread: true,
    favorite: false,
    collectionId: 1
  },
  {
    id: 2,
    title: 'Les startups françaises lèvent des fonds records en 2025',
    source: 'TechCrunch',
    author: 'Sarah Connor',
    time: 'Il y a 4h',
    excerpt: "Le secteur tech français bat tous les records avec plus de 8 milliards d'euros levés au premier semestre 2025. Une croissance portée par l'IA et la deeptech...",
    tags: ['Startup', 'France', 'Financement'],
    unread: false,
    favorite: true,
    collectionId: 1
  },
  {
    id: 3,
    title: 'Docker 25.0 : les nouvelles fonctionnalités qui changent tout',
    source: 'Hacker News',
    author: 'Alex Smith',
    time: 'Il y a 6h',
    excerpt: "La nouvelle version majeure de Docker apporte des améliorations significatives en matière de sécurité, performance et facilité d'utilisation. Découvrez les features qui vont impacter votre workflow...",
    tags: ['Docker', 'DevOps', 'Containers'],
    unread: true,
    favorite: false,
    collectionId: 1
  },
  {
    id: 4,
    title: 'Découverte majeure en physique quantique',
    source: 'Science Daily',
    author: 'Marie Curie',
    time: 'Il y a 1 jour',
    excerpt: "Des chercheurs ont réussi à maintenir un état de superposition quantique pendant plus de 10 minutes, ouvrant la voie à des ordinateurs quantiques plus stables...",
    tags: ['Quantique', 'Physique', 'Innovation'],
    unread: true,
    favorite: false,
    collectionId: 2
  },
  {
    id: 5,
    title: 'Le marché de la tech en Europe dépasse les attentes',
    source: 'Financial Times',
    author: 'John Market',
    time: 'Il y a 8h',
    excerpt: "Les valorisations des entreprises tech européennes atteignent des sommets historiques, portées par l'innovation et les investissements internationaux...",
    tags: ['Business', 'Europe', 'Tech'],
    unread: true,
    favorite: false,
    collectionId: 3
  }
];

export const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:3001/api';

export const FEED_REFRESH_INTERVAL = 5 * 60 * 1000; // 5 minutes

export const CATEGORIES = [
  'Technologie',
  'Sciences',
  'Business',
  'Actualités',
  'Lifestyle',
  'Culture',
  'Sport',
  'Santé'
];

export const PERMISSIONS = {
  READ: 'read',
  ADD: 'add',
  EDIT: 'edit',
  COMMENT: 'comment',
  DELETE: 'delete',
  ADMIN: 'admin'
};

export const USER_ROLES = {
  CREATOR: 'creator',
  ADMIN: 'admin',
  MODERATOR: 'moderator',
  CONTRIBUTOR: 'contributor',
  MEMBER: 'member',
  READER: 'reader'
};