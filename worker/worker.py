import json
import os
import pika
import logging
import redis
import torch
import base64
import io
from transformers import AutoModelForCausalLM
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

analyzer = None
redis_client = None

rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_user = os.getenv('RABBITMQ_USER', 'admin')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')
queue_name = 'food_analysis_queue'

def get_rabbitmq_connection():
    import time
    max_retries = 30
    retry_interval = 2
    
    for attempt in range(max_retries):
        try:
            credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
            parameters = pika.ConnectionParameters(
                host=rabbitmq_host,
                port=5672,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            connection = pika.BlockingConnection(parameters)
            logger.info(f"Conectado a RabbitMQ exitosamente (intento {attempt + 1})")
            return connection
        except Exception as e:
            logger.warning(f"Intento {attempt + 1}/{max_retries} de conexión a RabbitMQ falló: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_interval)
            else:
                logger.error("No se pudo conectar a RabbitMQ después de todos los intentos")
                raise

def setup_analyzer():
    global analyzer
    if analyzer is None:
        try:
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                
                analyzer = AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2",
                    revision="2025-06-21",
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    max_memory={0: "3.5GB"},
                )
                logger.info("Modelo cargado en GPU")
            else:
                logger.info("GPU no disponible, cargando modelo en CPU...")
                analyzer = AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2",
                    revision="2025-06-21", 
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True,
                )
                analyzer = analyzer.to('cpu')
                logger.info("Modelo cargado en CPU")
            
            device = "GPU" if torch.cuda.is_available() else "CPU"
            logger.info(f"Analizador listo en {device} - Tiempo estimado por imagen: {5-15 if torch.cuda.is_available() else '30-60'} segundos")
        except Exception as e:
            logger.error(f"Error cargando el analizador de nutrición: {e}")
            try:
                logger.info("Intentando cargar modelo sin device_map...")
                analyzer = AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2",
                    revision="2025-06-21",
                    trust_remote_code=True,
                )
                logger.info("Modelo cargado exitosamente como fallback")
            except Exception as e2:
                logger.error(f"Error en fallback: {e2}")
                analyzer = None
    return analyzer

def get_redis_client():
    global redis_client
    if redis_client is None:
        import time
        max_retries = 10
        retry_interval = 2
        
        for attempt in range(max_retries):
            try:
                redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                redis_client.ping()
                logger.info(f"Conectado a Redis exitosamente (intento {attempt + 1})")
                break
            except Exception as e:
                logger.warning(f"Intento {attempt + 1}/{max_retries} de conexión a Redis falló: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
                else:
                    logger.error("No se pudo conectar a Redis después de todos los intentos")
                    redis_client = None
    return redis_client

def callback(ch, method, properties, body):
    global analyzer
    try:
        message = json.loads(body.decode('utf-8'))
        task_id = message['task_id']
        image_data = message['image_data']
        filename = message.get('filename', 'unknown')
            
        logger.info(f"Procesando tarea: {task_id}")
        
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            
            image = Image.open(io.BytesIO(image_bytes))
            logger.info(f"Imagen decodificada exitosamente: {image.size}")
            
        except Exception as e:
            logger.error(f"Error decodificando imagen: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
        
        if analyzer is None:
            analyzer = setup_analyzer()
            if analyzer is None:
                logger.error("No se pudo cargar el analizador")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
        
        try:
            logger.info(f"Comenzando análisis nutricional para: {filename}")
            nutrition_result = query_nutrition_analyzer(image, analyzer)
            logger.info(f"Análisis completado para tarea: {task_id}")
            result = {
                'task_id': task_id,
                'filename': filename,
                'analysis': nutrition_result,
                'status': 'completed',
                'timestamp': str(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')
            }
            
        except Exception as e:
            logger.error(f"Error en análisis nutricional: {e}")
            result = {
                'task_id': task_id,
                'filename': filename,
                'error': str(e),
                'status': 'error'
            }
        try:
            redis_conn = get_redis_client()
            if redis_conn:
                redis_conn.setex(
                    f"analysis:{task_id}", 
                    3600, 
                    json.dumps(result)
                )
                logger.info(f"Resultado guardado en Redis para tarea: {task_id}")
            else:
                logger.error("No se pudo conectar a Redis")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
                
        except Exception as e:
            logger.error(f"Error guardando en Redis: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        logger.info(f"Tarea {task_id} procesada exitosamente")
        
    except Exception as e:
        logger.error(f"Error general procesando tarea: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
   
def extract_nutrition_value(text: str, nutrient_keyword: str) -> float:
    import re
    try:
        pattern = rf"{nutrient_keyword}[^0-9]*(\d+(?:\.\d+)?)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
        return 0.0
    except:
        return 0.0

def extract_food_type(text: str) -> str:
    """Extrae el tipo de comida del texto de análisis"""
    try:
        import re
        pattern = r"comida[^:]*:\s*([^,\n]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        words = text.split()[:10]
        return " ".join(words) if words else "Alimento no identificado"
    except:
        return "Alimento no identificado"

def query_nutrition_analyzer(image: Image.Image, analyzer):
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        original_size = image.size
        if torch.cuda.is_available():
            max_size = 768
            time_estimate = "5-15 segundos"
        else:
            max_size = 512
            time_estimate = "30-60 segundos"
            
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        device = "GPU" if torch.cuda.is_available() else "CPU"
        logger.info(f"Iniciando análisis en {device} (estimado: {time_estimate})...")
        
        question = "Analiza esta comida. Responde: Calorías: X, Proteínas: X g, Carbohidratos: X g, Grasas: X g, Comida: nombre"
        
        import time
        start_time = time.time()
        raw_result = analyzer.query(image, question=question)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        logger.info(f"Análisis completado en {analysis_time:.2f} segundos")
        logger.info(f"Resultado bruto: {raw_result}")
        
        structured_result = {
            'raw_analysis': raw_result,
            'calories': extract_nutrition_value(raw_result, 'calor'),
            'proteins': extract_nutrition_value(raw_result, 'prote'),
            'carbohydrates': extract_nutrition_value(raw_result, 'carboh'),
            'fats': extract_nutrition_value(raw_result, 'gras'),
            'food_type': extract_food_type(raw_result)
        }
        
        return structured_result
        
    except Exception as e:
        logger.error(f"Error en query_nutrition_analyzer: {e}")
        return {
            'error': str(e),
            'raw_analysis': 'Error en el análisis',
            'calories': 0,
            'proteins': 0,
            'carbohydrates': 0,
            'fats': 0,
            'food_type': 'No identificado'
        }
 
def start_consuming():
    connection = None
    channel = None
    
    try:
        logger.info("Inicializando worker...")
        
        setup_analyzer()
        
        redis_conn = get_redis_client()
        if not redis_conn:
            logger.error("No se puede conectar a Redis. Deteniendo worker.")
            return
        
        connection = get_rabbitmq_connection()
        channel = connection.channel()
            
        channel.queue_declare(queue=queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
            
        channel.basic_consume(
                queue=queue_name,
                on_message_callback=callback
            )
            
        logger.info("Worker iniciado. Esperando mensajes...")
        channel.start_consuming()
            
    except KeyboardInterrupt:
        logger.info("Worker detenido por el usuario")
        if channel:
            channel.stop_consuming()
        if connection:
            connection.close()
    except Exception as e:
        logger.error(f"Error en worker: {e}")
        import time
        logger.info("Reintentando en 10 segundos...")
        time.sleep(10)
        start_consuming()
        
if __name__ == "__main__":
    start_consuming()