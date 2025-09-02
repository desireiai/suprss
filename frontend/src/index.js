import React from 'react';
import ReactDOM from 'react-dom/client';
import './styles/index.css';  // Import du CSS principal
import './styles/variables.css';  // Import des variables CSS (optionnel si déjà dans index.css)
import App from './App';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);