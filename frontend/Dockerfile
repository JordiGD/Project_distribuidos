# Usar imagen base de Node.js
FROM node:18-alpine

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install

# Copiar código fuente
COPY . .

# Argumento para la URL de la API
ARG REACT_APP_API_URL=http://identical.localhost
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# Construir la aplicación
RUN npm run build

# Instalar serve para servir archivos estáticos
RUN npm install -g serve

# Exponer puerto 3000
EXPOSE 3000

# Comando para ejecutar la aplicación
CMD ["serve", "-s", "build", "-l", "3000"]
