import base64
import json
import uuid
import pika
import os
import redis
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
from typing import Optional

app = FastAPI(title="IdentiCal", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'password')
RABBITMQ_QUEUE = 'food_analysis_queue'

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))

redis_client = None

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)

def get_redis_client():
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            redis_client.ping()
        except Exception as e:
            print(f"Error conectando a Redis: {e}")
            redis_client = None
    return redis_client


def setup_rabbitmq():
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        connection.close()
        print("RabbitMQ configurado correctamente")
        return True
    except Exception as e:
        print(f"Error configurando RabbitMQ: {e}")
        return False

@app.post("/api/analyze-food")
async def analyze_food(image: UploadFile = File(...)):
    try:
        if not image.filename:
            raise HTTPException(status_code=400, detail="No se seleccionó archivo")
        
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_extension = image.filename.rsplit('.', 1)[1].lower() if '.' in image.filename else ''
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")
        
        try:
            image_bytes = await image.read()
            image_pil = Image.open(io.BytesIO(image_bytes))
            image_pil.verify()
        except Exception as e:
            raise HTTPException(status_code=400, detail="Imagen corrupta o no válida")
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        task_id = str(uuid.uuid4())
        message = {
            'task_id': task_id,
            'image_data': image_base64,
            'filename': image.filename,
            'content_type': image.content_type
        }
        
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        connection.close()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Imagen enviada para análisis", 
                "task_id": task_id,
                "estimated_time": "30-60 segundos"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/api/probe")
async def probe():
    try:
        # Cargar la imagen de prueba desde el sistema de archivos
        image_path = "/app/imagenprueba.jpg"  # Ruta dentro del contenedor
        filename = "imagenprueba.jpg"
        
        # Verificar extensión
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Formato de imagen no válido")
        
        try:
            # Leer la imagen desde el sistema de archivos
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Verificar que la imagen es válida
            image_pil = Image.open(io.BytesIO(image_bytes))
            image_pil.verify()
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Imagen de prueba no encontrada")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Imagen corrupta o no válida: {str(e)}")
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        task_id = str(uuid.uuid4())
        message = {
            'task_id': task_id,
            'image_data': image_base64,
            'filename': filename,
            'content_type': 'image/jpeg'
        }
        
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
            )
        )
        connection.close()
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "Imagen enviada para análisis", 
                "task_id": task_id,
                "estimated_time": "30-60 segundos"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/api/results/{task_id}")
async def get_analysis_results(task_id: str):
    try:
        redis_conn = get_redis_client()
        if not redis_conn:
            raise HTTPException(status_code=503, detail="Base de datos no disponible")
        
        result_key = f"analysis:{task_id}"
        result_data = redis_conn.get(result_key)
        
        if not result_data:
            return JSONResponse(
                status_code=202,
                content={
                    "task_id": task_id,
                    "status": "processing",
                    "message": "Análisis en proceso..."
                }
            )
        nutrition_data = json.loads(result_data)
        
        return JSONResponse(
            status_code=200,
            content={
                "task_id": task_id,
                "status": "completed",
                "results": nutrition_data
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/api/health")
async def health_check():
    redis_conn = get_redis_client()
    redis_status = "connected" if redis_conn else "disconnected"
    
    return {
        "status": "healthy", 
        "service": "food-analysis-backend",
        "redis_status": redis_status
    }

@app.on_event("startup")
async def startup_event():
    setup_rabbitmq()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)