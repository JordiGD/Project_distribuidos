<div align="center">

# 🍎 IdentiCal

### Identificador Inteligente de Calorías y Valores Nutricionales

Sube una imagen de tu comida y obtén un análisis nutricional completo utilizando IA

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.0-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)

</div>

---

## 📋 Tabla de Contenidos

- [Características](#-características)
- [Tecnologías](#-tecnologías)
- [Arquitectura](#-arquitectura)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación y Configuración](#-instalación-y-configuración)
- [Uso](#-uso)
- [Estructura del Proyecto](#-estructura-del-proyecto)
- [Variables de Entorno](#-variables-de-entorno)
- [Deployment](#-deployment)
- [Autores](#-autores)

---

## ✨ Características

- 📸 **Análisis de Imágenes**: Sube fotos de alimentos y obtén análisis nutricional automático
- 🤖 **IA Avanzada**: Utiliza modelos de visión por computadora y LLMs para identificación precisa
- ⚡ **Procesamiento Asíncrono**: Sistema de colas con RabbitMQ para manejar múltiples solicitudes
- 💾 **Caché Inteligente**: Redis para respuestas rápidas y reducción de costos de API
- 🎯 **Información Detallada**: Calorías, macronutrientes, micronutrientes y porciones
- 🔄 **Tiempo Real**: WebSocket para actualizaciones instantáneas del estado de procesamiento
- 🐳 **Containerizado**: Fácil despliegue con Docker Compose
- 🌐 **API RESTful**: Backend modular y escalable con FastAPI
- 🎨 **UI Moderna**: Interfaz React intuitiva y responsiva

---

## 🛠️ Tecnologías

### Backend
- **FastAPI** - Framework web moderno y rápido
- **Python 3.9+** - Lenguaje principal
- **Pika** - Cliente RabbitMQ para mensajería
- **Redis** - Sistema de caché en memoria
- **Pillow** - Procesamiento de imágenes
- **Uvicorn** - Servidor ASGI

### Frontend
- **React 18.2** - Librería UI
- **Axios** - Cliente HTTP
- **React Scripts 5.0** - Herramientas de desarrollo

### Worker / IA
- **PyTorch 2.0+** - Framework de deep learning
- **Transformers** - Modelos pre-entrenados de Hugging Face
- **LangChain** - Framework para aplicaciones con LLMs
- **GPT-4 Vision** - Modelo de visión multimodal (variante opcional)
- **Accelerate** - Optimización de modelos
- **Bitsandbytes** - Cuantización de modelos

### Infraestructura
- **Docker & Docker Compose** - Containerización
- **Traefik** - Reverse proxy y load balancer
- **RabbitMQ** - Message broker
- **Redis** - Cache y almacenamiento en memoria

---
## 🏗️ Arquitectura

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Frontend  │────▶│   Backend   │─────▶│  RabbitMQ   │
│   (React)   │      │  (FastAPI)  │      │   (Queue)   │
└─────────────┘      └─────────────┘      └─────────────┘
                           │                      │
                           ▼                      ▼
                     ┌─────────────┐      ┌─────────────┐
                     │    Redis    │      │   Worker    │
                     │   (Cache)   │      │  (AI/ML)    │
                     └─────────────┘      └─────────────┘
```

1. **Frontend** envía imagen al backend
2. **Backend** valida y encola la solicitud en RabbitMQ
3. **Worker** procesa la imagen con modelos de IA
4. **Redis** cachea resultados para consultas futuras
5. **Backend** retorna resultados al frontend



## 📦 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:

- **Docker** (v20.10+) y **Docker Compose** (v2.0+)
- **Git** para clonar el repositorio
- **Mínimo 8GB RAM** (recomendado 16GB para el worker con modelos grandes)
- **Espacio en disco**: ~10GB para imágenes Docker y modelos



## 🚀 Instalación y Configuración

### 1. Clonar el Repositorio

```bash
git clone https://github.com/JordiGD/Project_distribuidos.git calories-counter-ia
cd calories-counter-ia
```

### 2. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto:

```bash
# RabbitMQ
RABBITMQ_USER=admin
RABBITMQ_PASS=tu_password_seguro

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# API Keys (si usas GPT-4)
OPENAI_API_KEY=tu_openai_api_key
HUGGINGFACE_TOKEN=tu_huggingface_token

# Configuración del Worker
WORKER_TYPE=local  # local o gpt4
```

### 3. Construir y Levantar los Servicios

```bash
# Construir las imágenes
docker-compose build

# Levantar todos los servicios
docker-compose up -d
```

### 4. Verificar que los Servicios Estén Corriendo

```bash
docker-compose ps
```

Deberías ver todos los servicios como `running`:
- `traefik_proxy`
- `rabbitmq_broker`
- `redis_cache`
- `backend_api`
- `frontend_app`
- `worker_processor`

---

## 💡 Uso

### Acceso a la Aplicación

Una vez que todos los servicios estén corriendo:

- **Frontend**: [http://localhost](http://localhost) o [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost/api](http://localhost/api)
- **API Docs**: [http://localhost/api/docs](http://localhost/api/docs) (Swagger UI)
- **RabbitMQ Management**: [http://localhost:15672](http://localhost:15672) (usuario: `admin`)
- **Traefik Dashboard**: [http://localhost:8080](http://localhost:8080)

### Flujo de Uso

1. Abre la aplicación en tu navegador
2. Haz clic en "Subir Imagen" o arrastra una foto de comida
3. Espera el procesamiento (puede tomar 10-30 segundos)
4. Visualiza los resultados nutricionales detallados

---

## 📁 Estructura del Proyecto
```
root/
├── 📄 docker-compose.yml     # Orquestación de contenedores Docker
├── 📄 README.md              # Documentación del proyecto
├── 📂 backend/               # API Backend (FastAPI)
│   ├── 📄 app.py             # Aplicación principal del API
│   ├── 📄 Dockerfile         # Imagen Docker para el backend
│   └── 📄 requirements.txt   # Dependencias Python del backend
├── 📂 frontend/              # Aplicación web React
│   ├── 📄 Dockerfile         # Imagen Docker para el frontend
│   ├── 📄 package.json       # Dependencias y scripts npm
│   ├── 📂 public/            # Archivos estáticos públicos
│   │   └── 📄 index.html     # HTML principal
│   └── 📂 src/               # Código fuente React
│       ├── 📄 App.js         # Componente principal
│       ├── 📄 index.js       # Punto de entrada
│       ├── 📄 index.css      # Estilos globales
│       ├── 📂 components/    # Componentes React
│       │   ├── 📄 DetailedNutrition.js
│       │   ├── 📄 ErrorDisplay.js
│       │   ├── 📄 ImageUploader.js
│       │   ├── 📄 IndexView.js
│       │   ├── 📄 LoadingAnimation.js
│       │   ├── 📄 NutritionResults.js
│       │   └── 📄 ResultView.js
│       └── 📂 services/      # Servicios y lógica de negocio
│           └── 📄 api.js     # Cliente API
└── 📂 worker/                # Worker para procesamiento de imágenes
    ├── 📄 worker.py          # Worker principal
    ├── 📄 worker_gpt4.py     # Worker con GPT-4
    ├── 📄 NutritionInfo.py   # Lógica de análisis nutricional
    ├── 📄 Dockerfile         # Imagen Docker para worker
    ├── 📄 Dockerfile.gpt4    # Imagen Docker para worker GPT-4
    ├── 📄 requirements.txt   # Dependencias del worker
    └── 📄 requirements_gpt4.txt # Dependencias para GPT-4
```

---

## 🌍 Variables de Entorno

El proyecto utiliza las siguientes variables de entorno. Crea un archivo `.env` en la raíz del proyecto:

| Variable | Descripción | Valor por Defecto | Requerido |
|----------|-------------|-------------------|-----------|
| `RABBITMQ_USER` | Usuario de RabbitMQ | `admin` | ✅ |
| `RABBITMQ_PASS` | Contraseña de RabbitMQ | `password` | ✅ |
| `REDIS_HOST` | Host de Redis | `redis` | ✅ |
| `REDIS_PORT` | Puerto de Redis | `6379` | ✅ |
| `REDIS_DB` | Base de datos Redis | `0` | ❌ |
| `OPENAI_API_KEY` | API Key de OpenAI (para GPT-4) | - | ⚠️ Solo si usas GPT-4 |
| `HUGGINGFACE_TOKEN` | Token de Hugging Face | - | ⚠️ Opcional |
| `WORKER_TYPE` | Tipo de worker (`local` o `gpt4`) | `local` | ❌ |

### Ejemplo de archivo `.env`:

```env
# RabbitMQ Configuration
RABBITMQ_USER=admin
RABBITMQ_PASS=MiPasswordSuperSeguro123!

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# AI/ML Configuration (opcional)
OPENAI_API_KEY=sk-...
HUGGINGFACE_TOKEN=hf_...
WORKER_TYPE=local
```

---

## 🚀 Deployment

### Desarrollo Local

Para ejecutar el proyecto en modo desarrollo:

```bash
# Levantar todos los servicios
docker-compose up

# Ver logs en tiempo real
docker-compose logs -f

# Detener los servicios
docker-compose down
```

### Producción

Para desplegar en producción:

```bash
# Construir y levantar en modo detached
docker-compose up -d --build

# Ver estado de los contenedores
docker-compose ps

# Ver logs de un servicio específico
docker-compose logs -f backend

# Reiniciar un servicio
docker-compose restart worker

# Detener y eliminar todo (incluyendo volúmenes)
docker-compose down -v
```

### Comandos Útiles

```bash
# Reconstruir un servicio específico
docker-compose up -d --build backend

# Escalar workers
docker-compose up -d --scale worker=3

# Ver uso de recursos
docker stats

# Limpiar imágenes no usadas
docker system prune -a
```

---
## 👥 Autores

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/JordiGD">
        <img src="https://github.com/JordiGD.png" width="100px;" alt="Jorge Gonzales"/>
        <br />
        <sub><b>Jorge Gonzales</b></sub>
      </a>
      <br />
      <sub>Backend & DevOps</sub>
    </td>
    <td align="center">
      <a href="https://github.com/MajoBlanco">
        <img src="https://github.com/MajoBlanco.png" width="100px;" alt="Majo Blanco"/>
        <br />
        <sub><b>Majo Blanco</b></sub>
      </a>
      <br />
      <sub>Frontend & UI/UX</sub>
    </td>
  </tr>
</table>

<div align="center">

</div>
