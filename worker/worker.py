import json
import os
import pika
import logging
import redis
import torch
import base64
import io
import re
from typing import Optional
from worker.NutritionInfo import NutritionInfo
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration, LlavaProcessor, LlavaForConditionalGeneration, BitsAndBytesConfig
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

analyzer = None
processor = None
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
    global analyzer, processor
    if analyzer is None or processor is None:
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"GPU disponible: {gpu_name}")
                
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                logger.info(f"Memoria GPU total: {gpu_memory_gb:.1f} GB")
                
                if gpu_memory_gb >= 16:
                    model_name = "llava-hf/llava-v1.6-vicuna-13b-hf"
                    logger.info("Usando LLaVA-Next 13B (requiere 16GB+ GPU)")
                elif gpu_memory_gb >= 8:
                    model_name = "llava-hf/llava-v1.6-mistral-7b-hf"  
                    logger.info("Usando LLaVA-Next 7B (requiere 8GB+ GPU)")
                else:
                    model_name = "llava-hf/llava-1.5-7b-hf"
                    logger.info("Usando LLaVA 1.5 7B (GPU limitada)")
                
                logger.info(f"Cargando processor para {model_name}...")
                if "llava-v1.6" in model_name or "llava-next" in model_name:
                    processor = LlavaNextProcessor.from_pretrained(model_name, use_fast=True)
                    model_class = LlavaNextForConditionalGeneration
                else:
                    processor = LlavaProcessor.from_pretrained(model_name, use_fast=True)  
                    model_class = LlavaForConditionalGeneration
                
                logger.info(f"Cargando modelo {model_name}...")
                
                quantization_config = None
                if gpu_memory_gb < 12:
                    quantization_config = BitsAndBytesConfig(
                        load_in_8bit=True,
                        llm_int8_threshold=6.0,
                        llm_int8_has_fp16_weight=False,
                    )
                    logger.info("Usando cuantización 8-bit para GPU limitada")
                
                analyzer = model_class.from_pretrained(
                    model_name,
                    dtype=torch.float16,
                    device_map="auto",
                    low_cpu_mem_usage=True,
                    quantization_config=quantization_config,
                )
                
                model_device = next(analyzer.parameters()).device
                logger.info(f"Modelo LLaVA-Next cargado en dispositivo: {model_device}")
                
            else:
                logger.info("GPU no disponible, cargando modelo en CPU...")
                model_name = "llava-hf/llava-1.5-7b-hf"
                
                processor = LlavaProcessor.from_pretrained(model_name, use_fast=True)
                analyzer = LlavaForConditionalGeneration.from_pretrained(
                    model_name,
                    dtype=torch.float32,
                    device_map="cpu",
                    low_cpu_mem_usage=True,
                )
                
                logger.info(f"Modelo LLaVA cargado en CPU")
            
            device = "GPU" if torch.cuda.is_available() else "CPU" 
            logger.info(f"LLaVA-Next analizador listo en {device}")
            
        except Exception as e:
            logger.error(f"Error cargando LLaVA-Next: {e}")
            try:
                logger.info("Intentando cargar modelo LLaVA básico como fallback...")
                model_name = "llava-hf/llava-1.5-7b-hf"
                
                processor = LlavaProcessor.from_pretrained(model_name, use_fast=True)
                analyzer = LlavaForConditionalGeneration.from_pretrained(
                    model_name,
                    dtype=torch.float32,
                    device_map="cpu",
                )
                
                logger.info("Modelo LLaVA básico cargado exitosamente como fallback")
                
            except Exception as e2:
                logger.error(f"Error en fallback: {e2}")
                analyzer = None
                processor = None
                
    return analyzer, processor

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
    global analyzer, processor
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
        
        if analyzer is None or processor is None:
            analyzer, processor = setup_analyzer()
            if analyzer is None or processor is None:
                logger.error("No se pudo cargar el analizador LLaVA-Next")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return
        
        try:
            logger.info(f"Comenzando análisis nutricional para: {filename}")
            nutrition_result = query_nutrition_analyzer(image, analyzer, processor)
            logger.info(f"Análisis completado para tarea: {task_id}")
            
            nutrition_result['task_id'] = task_id
            nutrition_result['filename'] = filename
            nutrition_result['status'] = 'completed'
            nutrition_result['timestamp'] = str(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')
            
            result = nutrition_result
            
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
            confianza=extract_value(raw_text, ['confianza', 'confidence', 'certeza'], 85)
        )
        
        logger.info(f"Datos parseados con Pydantic: {nutrition_data.comida}")
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

def query_nutrition_analyzer(image: Image.Image, analyzer, processor):
    try:
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        model_device = next(analyzer.parameters()).device
        device_name = "GPU" if model_device.type == 'cuda' else "CPU"
        logger.info(f"Iniciando análisis LLaVA-Next en {device_name} (device: {model_device})")
        
        prompt = """[INST] <image>
Analiza esta imagen de comida de manera detallada y precisa.

Identifica todos los alimentos visibles y calcula los valores nutricionales aproximados para la porción total mostrada en la imagen.

Proporciona tu respuesta en este formato exacto:
Comida: [descripción específica de lo que ves]
Calorías: [número] kcal
Proteínas: [número] g
Carbohidratos: [número] g
Grasas: [número] g
Fibra: [número] g
Confianza: [porcentaje]%

Sé específico sobre qué alimentos ves y proporciona estimaciones nutricionales realistas basadas en las porciones visibles. [/INST]"""
        
        logger.info(f"Imagen para análisis - Tamaño: {image.size}, Modo: {image.mode}")
        logger.info("Procesando imagen con LLaVA-Next...")
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        try:
            inputs = processor(text=prompt, images=image, return_tensors="pt").to(model_device)
            
            with torch.no_grad():
                logger.info(f"Generando respuesta con LLaVA-Next en: {model_device}")
                
                output = analyzer.generate(
                    **inputs,
                    max_new_tokens=512,
                    do_sample=True,
                    temperature=0.2,
                    pad_token_id=processor.tokenizer.eos_token_id
                )
                
                generated_text = processor.decode(output[0], skip_special_tokens=True)
                
                if "[/INST]" in generated_text:
                    raw_result = generated_text.split("[/INST]")[-1].strip()
                elif "assistant" in generated_text.lower():
                    raw_result = generated_text.split("assistant")[-1].strip()
                else:
                    raw_result = generated_text.strip()
                    
        except RuntimeError as e:
            if "Expected all tensors to be on the same device" in str(e) or "CUDA out of memory" in str(e):
                logger.warning(f"Error GPU detectado: {e}")
                logger.info("Intentando procesar en CPU como fallback...")
                
                analyzer_cpu = analyzer.cpu()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                
                inputs_cpu = processor(text=prompt, images=image, return_tensors="pt").to('cpu')
                
                with torch.no_grad():
                    output = analyzer_cpu.generate(
                        **inputs_cpu,
                        max_new_tokens=512,
                        do_sample=True,
                        temperature=0.2,
                        pad_token_id=processor.tokenizer.eos_token_id
                    )
                    
                    generated_text = processor.decode(output[0], skip_special_tokens=True)
                    
                    if "[/INST]" in generated_text:
                        raw_result = generated_text.split("[/INST]")[-1].strip()
                    elif "assistant" in generated_text.lower():
                        raw_result = generated_text.split("assistant")[-1].strip()
                    else:
                        raw_result = generated_text.strip()
                
                if torch.cuda.is_available():
                    try:
                        analyzer = analyzer_cpu.cuda()
                        logger.info("Modelo LLaVA-Next movido de vuelta a GPU")
                    except:
                        logger.warning("No se pudo mover LLaVA-Next de vuelta a GPU")
            else:
                raise e
            
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.info(f"Análisis LLaVA-Next completado")
        logger.info(f"Respuesta completa del modelo: {raw_result}")
        
        analysis_text = str(raw_result).strip()
        logger.info(f"Texto para parsing nutricional: {analysis_text}")
        
        nutrition_info = parse_nutrition_with_langchain(analysis_text)
        
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
            'model': 'LLaVA-Next'
        }
        
        logger.info(f"Análisis Comida: {nutrition_info.comida}, "
                   f"Calorías: {nutrition_info.calorias}, Proteínas: {nutrition_info.proteinas}g, "
                   f"Carbohidratos: {nutrition_info.carbohidratos}g, Grasas: {nutrition_info.grasas}g, "
                   f"Fibra: {nutrition_info.fibra}g, Confianza: {nutrition_info.confianza}%")
        
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
        
        analyzer, processor = setup_analyzer()
        if analyzer is None or processor is None:
            logger.error("No se pudo inicializar LLaVA-Next")
            return
            
        logger.info("Worker LLaVA-Next iniciado. Esperando mensajes...")
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