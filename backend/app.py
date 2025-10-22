import base64
import json
import uuid
import pika
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image
import io

app = FastAPI(title="Food Analysis API", version="1.0.0")

RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'admin')
RABBITMQ_PASS = os.getenv('RABBITMQ_PASS', 'password')
RABBITMQ_QUEUE = 'food_analysis_queue'

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASS)
    parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=5672,
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)


def setup_rabbitmq():
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)
        
        connection.close()
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
            content={"message": "Imagen enviada para análisis", "task_id": task_id}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
  
@app.get("/probe")  
async def probe():
    task_id = str(uuid.uuid4())
    message = {
        'task_id': task_id,
        'image_data': 'test_image_data',
        'filename': 'test.jpg',
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
            content={"message": "Imagen enviada para análisis", "task_id": task_id}
        )
        
 
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "food-analysis-backend"}

@app.on_event("startup")
async def startup_event():
    setup_rabbitmq()

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5000)