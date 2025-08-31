# frontend/Dockerfile

# === OPTION 1: PRODUCTION (avec Nginx) ===
# Étape 1 : Build de l'application
FROM node:18-alpine AS build

WORKDIR /app

# Copier les fichiers de dépendances
COPY package*.json ./

# Installer les dépendances
RUN npm ci --only=production

# Copier le code source
COPY . .

# Build de l'application (Create React App génère un dossier 'build', pas 'dist')
RUN npm run build

# Étape 2 : Serveur Nginx pour servir l'application
FROM nginx:alpine

# Copier le build depuis l'étape précédente (ATTENTION: c'est 'build' pas 'dist')
COPY --from=build /app/build /usr/share/nginx/html

# Copier la configuration Nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Exposer le port 80
EXPOSE 80

# Démarrer Nginx
CMD ["nginx", "-g", "daemon off;"]