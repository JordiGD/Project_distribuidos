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
                virtual_host='/',
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
                connection_attempts=3,
                retry_delay=2
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
                torch.cuda.empty_cache()
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU disponible: {gpu_name}")
                analyzer = AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2",
                    revision="2025-06-21",
                    trust_remote_code=True,
                    torch_dtype=torch.float16,
                    device_map={'': 0},
                    low_cpu_mem_usage=True,
                    max_memory={0: "3.5GB"},
                )
                
                model_device = next(analyzer.parameters()).device
                logger.info(f"Modelo cargado en dispositivo: {model_device}")
                
                devices = set(param.device for param in analyzer.parameters())
                if len(devices) > 1:
                    logger.warning(f"Modelo tiene parámetros en múltiples dispositivos: {devices}")
                    analyzer = analyzer.cuda(0)
                    logger.info("Modelo movido completamente a GPU 0")
                
            else:
                logger.info("GPU no disponible, cargando modelo en CPU...")
                analyzer = AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2",
                    revision="2025-06-21", 
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                    device_map={'': 'cpu'},
                    low_cpu_mem_usage=True,
                )
                
                model_device = next(analyzer.parameters()).device
                logger.info(f"Modelo cargado en dispositivo: {model_device}")
            
            device = "GPU" if torch.cuda.is_available() else "CPU"
            logger.info(f"Analizador listo en {device}")
            
        except Exception as e:
            logger.error(f"Error cargando el analizador de nutrición: {e}")
            try:
                analyzer = AutoModelForCausalLM.from_pretrained(
                    "vikhyatk/moondream2",
                    revision="2025-06-21",
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                )
                analyzer = analyzer.to('cpu')
                logger.info("Modelo cargado exitosamente en CPU como fallback")
                
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
        patterns = [
            rf"{nutrient_keyword}[^:]*:\s*(\d+(?:\.\d+)?)\s*(?:g|kcal|cal)?",
            rf"{nutrient_keyword}[^0-9]*(\d+(?:\.\d+)?)\s*(?:g|kcal|cal)?",
            rf"(\d+(?:\.\d+)?)\s*(?:g|kcal|cal)?\s*{nutrient_keyword}",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = float(match.group(1))
                logger.debug(f"Extraído {nutrient_keyword}: {value}")
                return value
        
        logger.debug(f"No se pudo extraer valor para {nutrient_keyword} del texto: {text}")
        return 0.0
    except Exception as e:
        logger.debug(f"Error extrayendo {nutrient_keyword}: {e}")
        return 0.0

def extract_food_type(text: str) -> str:
    try:
        import re
        patterns = [
            r"comida:\s*([^\n\r]+)",
            r"alimento:\s*([^\n\r]+)",
            r"tipo:\s*([^\n\r]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                food_name = match.group(1).strip()
                food_name = re.sub(r'[.,!?]+$', '', food_name)
                logger.debug(f"Tipo de comida extraído: {food_name}")
                return food_name
        
        lines = text.split('\n')
        for line in lines:
            if line.strip() and not any(keyword in line.lower() for keyword in ['calorías', 'proteínas', 'carbohidratos', 'grasas']):
                words = line.strip().split()[:4]
                if words:
                    result = " ".join(words)
                    logger.debug(f"Tipo de comida inferido: {result}")
                    return result
        
        logger.debug("No se pudo extraer tipo de comida")
        return "Alimento no identificado"
    except Exception as e:
        logger.debug(f"Error extrayendo tipo de comida: {e}")
        return "Alimento no identificado"

def query_nutrition_analyzer(image: Image.Image, analyzer):
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        model_device = next(analyzer.parameters()).device
        device_name = "GPU" if model_device.type == 'cuda' else "CPU"
        logger.info(f"Iniciando análisis en {device_name} (device: {model_device})")
        
        question = "¿Qué comida ves en esta imagen? Describe los alimentos y estima las calorías, proteínas, carbohidratos y grasas."
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info(f"Imagen para análisis - Tamaño: {image.size}, Modo: {image.mode}")
        
        try:
            with torch.no_grad():
                logger.info(f"Realizando consulta con modelo en: {next(analyzer.parameters()).device}")
                
                if model_device.type == 'cuda':
                    with torch.cuda.device(model_device):
                        raw_result = analyzer.query(image, question=question)
                else:
                    raw_result = analyzer.query(image, question=question)
                    
        except RuntimeError as e:
            if "Expected all tensors to be on the same device" in str(e):
                logger.warning(f"Error de dispositivo detectado: {e}")
                logger.info("Intentando mover el modelo completamente a CPU como fallback...")
                
                analyzer_cpu = analyzer.cpu()
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
                
                with torch.no_grad():
                    raw_result = analyzer_cpu.query(image, question=question)
                
                if torch.cuda.is_available():
                    try:
                        analyzer = analyzer_cpu.cuda()
                        logger.info("Modelo movido de vuelta a GPU")
                    except:
                        logger.warning("No se pudo mover el modelo de vuelta a GPU")
            else:
                raise e
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(f"Análisis completado")
        logger.info(f"Resultado bruto del modelo: {raw_result}")
        
        if isinstance(raw_result, dict) and 'answer' in raw_result:
            analysis_text = raw_result['answer']
            logger.info(f"Texto extraído para análisis: {analysis_text}")
        else:
            analysis_text = str(raw_result)
        
        calories = extract_nutrition_value(analysis_text, 'calor')
        proteins = extract_nutrition_value(analysis_text, 'prote') 
        carbohydrates = extract_nutrition_value(analysis_text, 'carboh')
        fats = extract_nutrition_value(analysis_text, 'gras')
        food_type = extract_food_type(analysis_text)
        
        structured_result = {
            'raw_analysis': raw_result,
            'calories': calories,
            'proteins': proteins, 
            'carbohydrates': carbohydrates,
            'fats': fats,
            'food_type': food_type
        }
        
        logger.info(f"Análisis estructurado - Comida: {food_type}, Calorías: {calories}, Proteínas: {proteins}g, Carbohidratos: {carbohydrates}g, Grasas: {fats}g")
        
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
                on_message_callback=callback,
                auto_ack=False
            )
        
        setup_analyzer()
            
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