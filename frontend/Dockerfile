# Usar imagen base de Node.js
FROM node:18-alpine

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias
COPY package*.json ./

# Instalar dependencias
RUN npm install --omit=dev

# Copiar código fuente
COPY . .

# Construir la aplicación
RUN npm run build

# Instalar serve para servir archivos estáticos
RUN npm install -g serve

# Exponer puerto 3000
EXPOSE 3000

# Comando para ejecutar la aplicación
CMD ["serve", "-s", "build", "-l", "3000"]
