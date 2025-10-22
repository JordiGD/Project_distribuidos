import json
import os
import pika
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

rabbitmq_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
rabbitmq_user = os.getenv('RABBITMQ_USER', 'admin')
rabbitmq_pass = os.getenv('RABBITMQ_PASS', 'password')
queue_name = 'food_analysis_queue'

def get_rabbitmq_connection():
    credentials = pika.PlainCredentials(rabbitmq_user, rabbitmq_pass)
    parameters = pika.ConnectionParameters(
        host=rabbitmq_host,
        port=5672,
        credentials=credentials
    )
    return pika.BlockingConnection(parameters)


def callback(ch, method, properties, body):
    try:
        message = json.loads(body.decode('utf-8'))
        task_id = message['task_id']
        image_data = message['image_data']
            
        logger.info(f"Procesando tarea: {task_id}")
    
        # Aquí iría el procesamiento de la imagen (análisis de alimentos)
        # Simulamos el procesamiento con un log
        logger.info(f"Análisis de imagen completado para la tarea: {task_id}")
            
        ch.basic_ack(delivery_tag=method.delivery_tag)
            
    except Exception as e:
        logger.error(f"Error procesando mensaje: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
def start_consuming():
    try:
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
        channel.stop_consuming()
        connection.close()
    except Exception as e:
        logger.error(f"Error en worker: {e}")
        
if __name__ == "__main__":
    start_consuming()