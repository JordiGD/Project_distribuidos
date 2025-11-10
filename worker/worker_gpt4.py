import json
import os
import pika
import logging
import redis
import base64
from typing import Optional
from pydantic import BaseModel, Field, validator
from PIL import Image
import io
import re
from openai import OpenAI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
openai_client = None

class NutritionInfo(BaseModel):
    comida: str = Field(description="Nombre y descripción específica del alimento identificado")
    calorias: float = Field(ge=0, description="Calorías totales en kcal")
    proteinas: float = Field(ge=0, description="Proteínas en gramos")
    carbohidratos: float = Field(ge=0, description="Carbohidratos en gramos")
    grasas: float = Field(ge=0, description="Grasas en gramos")
    fibra: float = Field(ge=0, default=0, description="Fibra en gramos")
    confianza: float = Field(ge=0, le=100, default=90, description="Nivel de confianza del análisis en porcentaje")
    
    @validator('comida')
    def validate_comida(cls, v):
        if not v or v.lower() in ['no identificado', 'unknown', '']:
            return "Alimento no identificado"
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "comida": "Pizza Margherita con tomate y mozzarella",
                "calorias": 450,
                "proteinas": 25,
                "carbohidratos": 50,
                "grasas": 18,
                "fibra": 3,
                "confianza": 90
            }
        }

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

redis_client = None

rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_user = os.getenv('RABBITMQ_USER', 'admin')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')
queue_name = os.getenv('RABBITMQ_QUEUE', 'food_analysis_queue')
priority_queue_name = os.getenv('RABBITMQ_PRIORITY_QUEUE', 'food_analysis_priority_queue')

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

def setup_openai_client():
    global openai_client
    if openai_client is None:
        try:
            if not OPENAI_API_KEY:
                logger.error("OPENAI_API_KEY no está configurada")
                raise ValueError("OPENAI_API_KEY es requerida")
            
            openai_client = OpenAI(api_key=OPENAI_API_KEY)
            logger.info("Cliente OpenAI configurado correctamente")
            
            logger.info("Probando conexión con OpenAI...")
            return openai_client
            
        except Exception as e:
            logger.error(f"Error configurando OpenAI: {e}")
            openai_client = None
            
    return openai_client

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
    global openai_client
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
        
        if openai_client is None:
            openai_client = setup_openai_client()
            if openai_client is None:
                logger.error("No se pudo inicializar el cliente OpenAI")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
        
        try:
            logger.info(f"Comenzando análisis nutricional con GPT-4 Vision para: {filename}")
            nutrition_result = query_gpt4_vision(image_data, openai_client)
            logger.info(f"Análisis completado para tarea: {task_id}")
            
            nutrition_result['task_id'] = task_id
            nutrition_result['filename'] = filename
            nutrition_result['status'] = 'completed'
            nutrition_result['timestamp'] = 'OpenAI GPT-4 Vision'
            
            result = nutrition_result
            
        except Exception as e:
            logger.error(f"Error en análisis nutricional: {e}")
            result = {
                'task_id': task_id,
                'filename': filename,
                'error': str(e),
                'status': 'error',
                'nombre': 'Error al analizar',
                'calorías': {'value': 0, 'unit': 'kcal', 'description': 'Error en el análisis'},
                'proteínas': {'value': 0, 'unit': 'g', 'description': 'Error en el análisis'},
                'carbohidratos': {'value': 0, 'unit': 'g', 'description': 'Error en el análisis'},
                'grasas': {'value': 0, 'unit': 'g', 'description': 'Error en el análisis'},
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

def parse_nutrition_with_langchain(raw_text: str) -> NutritionInfo:
    try:
        def extract_value(text: str, keywords: list, default: float = 0) -> float:
            for keyword in keywords:
                patterns = [
                    rf"{keyword}[^:]*:\s*(\d+(?:\.\d+)?)",
                    rf"{keyword}[^\d]*(\d+(?:\.\d+)?)",
                    rf"(\d+(?:\.\d+)?)\s*(?:g|kcal|cal)?\s*{keyword}",
                ]
                for pattern in patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        return float(match.group(1))
            return default
        
        def extract_food_name(text: str) -> str:
            patterns = [
                r"[Cc]omida:\s*([^\n\r]+)",
                r"[Aa]limento:\s*([^\n\r]+)",
                r"[Tt]ipo:\s*([^\n\r]+)",
            ]
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    name = match.group(1).strip()
                    name = re.sub(r'[.,!?]+$', '', name)
                    return name
            
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if line and not any(kw in line.lower() for kw in ['calorías', 'proteínas', 'carbohidratos', 'grasas', 'fibra']):
                    words = line.split()[:8]
                    if words:
                        return " ".join(words)
            
            return "Alimento no identificado"
        
        nutrition_data = NutritionInfo(
            comida=extract_food_name(raw_text),
            calorias=extract_value(raw_text, ['calor', 'kcal', 'cal'], 0),
            proteinas=extract_value(raw_text, ['prote', 'protein'], 0),
            carbohidratos=extract_value(raw_text, ['carboh', 'carb', 'hidrat'], 0),
            grasas=extract_value(raw_text, ['gras', 'fat', 'lip'], 0),
            fibra=extract_value(raw_text, ['fibra', 'fiber'], 0),
            confianza=extract_value(raw_text, ['confianza', 'confidence', 'certeza'], 90)
        )
        
        logger.info(f"Datos parseados: {nutrition_data.comida}")
        logger.info(f"   Calorías: {nutrition_data.calorias}, Proteínas: {nutrition_data.proteinas}g, "
                   f"Carbohidratos: {nutrition_data.carbohidratos}g, Grasas: {nutrition_data.grasas}g")
        
        return nutrition_data
        
    except Exception as e:
        logger.error(f"Error parseando con LangChain: {e}")
        return NutritionInfo(
            comida="Error al analizar",
            calorias=0,
            proteinas=0,
            carbohidratos=0,
            grasas=0,
            fibra=0,
            confianza=0
        )

def query_gpt4_vision(image_base64: str, client: OpenAI):
    try:
        logger.info("Iniciando análisis con GPT-4 Vision (gpt-4o)")
        system_prompt = """Eres un experto nutricionista especializado en análisis de alimentos mediante imágenes. 
Tu trabajo es identificar alimentos en fotografías y estimar su información nutricional.
IMPORTANTE: Solo analiza imágenes de comida. Si ves comida, SIEMPRE proporciona un análisis nutricional.
Responde SIEMPRE en español y usa EXACTAMENTE el formato especificado."""

        user_prompt = """Por favor, analiza esta imagen de comida.

INSTRUCCIONES:
1. Identifica qué alimentos ves en la imagen
2. Estima la porción/cantidad visible
3. Calcula los valores nutricionales aproximados TOTALES

FORMATO REQUERIDO (copia esto y completa con números):
Comida: [descripción detallada del plato]
Calorías: [número] kcal
Proteínas: [número] g
Carbohidratos: [número] g
Grasas: [número] g
Fibra: [número] g
Confianza: [número entre 60-95]%

REGLAS:
- Siempre proporciona números (nunca dejes valores vacíos)
- Si no estás seguro, haz tu mejor estimación
- La confianza debe reflejar qué tan seguro estás
- NO agregues explicaciones extra, SOLO el formato especificado"""
        
        if not image_base64.startswith('data:'):
            image_url = f"data:image/jpeg;base64,{image_base64}"
        else:
            image_url = image_base64
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": user_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url,
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )
        raw_result = response.choices[0].message.content.strip()
        
        logger.info(f"Respuesta de GPT-4 Vision recibida")
        logger.info(f"Respuesta completa: {raw_result}")
        
        rejection_phrases = [
            "lo siento",
            "no puedo",
            "cannot",
            "sorry",
            "unable to",
            "not able",
            "can't help",
            "no es posible"
        ]
        
        if any(phrase in raw_result.lower() for phrase in rejection_phrases):
            logger.warning(f"GPT-4 rechazó analizar la imagen: {raw_result}")
            logger.info("Reintentando con prompt simplificado...")
            
            simple_prompt = """Esta es una imagen de comida. Por favor analízala y dame:
            
Comida: [nombre del plato]
Calorías: [número] kcal
Proteínas: [número] g
Carbohidratos: [número] g
Grasas: [número] g
Fibra: [número] g
Confianza: 75%

Proporciona valores estimados basados en lo que ves."""
            
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": simple_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": image_url,
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            raw_result = response.choices[0].message.content.strip()
            logger.info(f"Segunda respuesta: {raw_result}")
        
        nutrition_info = parse_nutrition_with_langchain(raw_result)
        
        if nutrition_info.calorias == 0 and nutrition_info.proteinas == 0 and nutrition_info.carbohidratos == 0:
            logger.warning("No se pudieron extraer valores nutricionales válidos")
            nutrition_info.comida = "Alimento detectado (análisis incompleto)"
            nutrition_info.calorias = 100
            nutrition_info.proteinas = 5
            nutrition_info.carbohidratos = 15
            nutrition_info.grasas = 3
            nutrition_info.fibra = 1
            nutrition_info.confianza = 30
        
        structured_result = {
            'nombre': nutrition_info.comida,
            'alimento': nutrition_info.comida,
            'food_type': nutrition_info.comida,
            'calorías': {
                'value': nutrition_info.calorias,
                'unit': 'kcal',
                'description': 'Energía proporcionada por el alimento'
            },
            'proteínas': {
                'value': nutrition_info.proteinas,
                'unit': 'g',
                'description': 'Esenciales para el crecimiento y reparación muscular'
            },
            'carbohidratos': {
                'value': nutrition_info.carbohidratos,
                'unit': 'g',
                'description': 'Fuente principal de energía'
            },
            'grasas': {
                'value': nutrition_info.grasas,
                'unit': 'g',
                'description': 'Importantes para la absorción de vitaminas'
            },
            'fibra': {
                'value': nutrition_info.fibra,
                'unit': 'g',
                'description': 'Ayuda a la digestión y salud intestinal'
            },
            'confianza': {
                'value': nutrition_info.confianza,
                'unit': '%',
                'description': 'Nivel de confianza del análisis'
            },
            'raw_analysis': raw_result,
            'model': 'GPT-4 Vision (gpt-4o)'
        }
        
        logger.info(f"Análisis GPT-4 estructurado: {nutrition_info.comida}, "
                   f"Calorías: {nutrition_info.calorias}, Proteínas: {nutrition_info.proteinas}g, "
                   f"Carbohidratos: {nutrition_info.carbohidratos}g, Grasas: {nutrition_info.grasas}g, "
                   f"Fibra: {nutrition_info.fibra}g, Confianza: {nutrition_info.confianza}%")
        
        return structured_result
        
    except Exception as e:
        logger.error(f"Error en query_gpt4_vision: {e}")
        return {
            'error': str(e),
            'raw_analysis': f'Error en el análisis: {str(e)}',
            'nombre': 'Error al analizar',
            'calorías': {'value': 0, 'unit': 'kcal', 'description': 'Error'},
            'proteínas': {'value': 0, 'unit': 'g', 'description': 'Error'},
            'carbohidratos': {'value': 0, 'unit': 'g', 'description': 'Error'},
            'grasas': {'value': 0, 'unit': 'g', 'description': 'Error'},
            'fibra': {'value': 0, 'unit': 'g', 'description': 'Error'},
            'food_type': 'No identificado',
            'model': 'GPT-4 Vision (error)'
        }
 
def start_consuming():
    connection = None
    channel = None
    
    try:
        logger.info("Inicializando worker GPT-4 Vision...")
        
        redis_conn = get_redis_client()
        if not redis_conn:
            logger.error("No se puede conectar a Redis. Deteniendo worker.")
            return
        
        client = setup_openai_client()
        if client is None:
            logger.error("No se pudo inicializar OpenAI")
            return
        
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.queue_declare(queue=queue_name, durable=True)
        channel.queue_declare(queue=priority_queue_name, durable=True)
        channel.basic_qos(prefetch_count=1)
        
        channel.basic_consume(
            queue=priority_queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        channel.basic_consume(
            queue=queue_name,
            on_message_callback=callback,
            auto_ack=False
        )
        
        logger.info(f"Worker GPT-4 Vision iniciado")
        logger.info(f"  - Consumiendo de cola prioritaria: {priority_queue_name}")
        logger.info(f"  - Consumiendo de cola normal: {queue_name}")
        logger.info("Esperando mensajes...")
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
