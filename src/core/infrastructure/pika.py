import pika
import json
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class PikaClient:
    def __init__(self, rabbitmq_host):
        self.rabbitmq_host = rabbitmq_host
        self.connect()

    def connect(self):
        """Connect to RabbitMQ."""
        try:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.rabbitmq_host,
                    heartbeat=600  # Set a heartbeat to keep connection alive
                )
            )
            self.channel = self.connection.channel()
            logger.info("RabbitMQ connection and channel established successfully.")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            raise HTTPException(status_code=500, detail="Failed to connect to RabbitMQ")

    def declare_queue(self, queue_name):
        """Declare a RabbitMQ queue if not already existing."""
        try:
            self.channel.queue_declare(queue=queue_name, durable=True)
            logger.info(f"Declared queue: {queue_name}")
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.error(f"Channel closed by broker during queue declare: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to declare RabbitMQ queue")
        except pika.exceptions.AMQPConnectionError:
            # If connection is lost, reconnect and try again
            logger.warning("RabbitMQ connection lost. Reconnecting...")
            self.connect()
            self.declare_queue(queue_name)
        except Exception as e:
            logger.error(f"Unexpected error while declaring queue: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to declare RabbitMQ queue: {e}")

    def basic_publish(self, queue_name, message):
        """Publish a message to a specific RabbitMQ queue."""
        try:
            # Ensure the queue is declared before publishing
            self.declare_queue(queue_name)

            # Publish message
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            logger.info(f"Published message to queue '{queue_name}'")
        except pika.exceptions.ChannelClosedByBroker as e:
            logger.error(f"Channel closed by broker during publish: {e}")
            raise HTTPException(status_code=500, detail=f"Channel closed: {e}")
        except pika.exceptions.AMQPConnectionError:
            # If connection is lost, reconnect and try again
            logger.warning("RabbitMQ connection lost. Reconnecting...")
            self.connect()
            self.basic_publish(queue_name, message)
        except Exception as e:
            logger.error(f"Unexpected error while publishing to RabbitMQ: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to publish message to RabbitMQ: {e}")

    def consume_messages(self, queue_name, on_message_callback, auto_ack=False):
        """Consume messages from a specific RabbitMQ queue"""
        try:
            # Ensure connection is open before consuming
            if not self.connection or self.connection.is_closed:
                logger.info("RabbitMQ connection is closed. Reconnecting...")
                self._connect()
            
            # Declare the queue to ensure it exists
            self.declare_queue(queue_name)
            
            # Set QoS to control message flow (one message at a time)
            self.channel.basic_qos(prefetch_count=1)

            # Start consuming messages
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message_callback,
                auto_ack=auto_ack
            )
            logger.info(f"Started consuming messages from queue '{queue_name}'")
            self.channel.start_consuming()
        except Exception as e:
            logger.error(f"Error consuming messages from RabbitMQ queue '{queue_name}': {e}")
            raise HTTPException(status_code=500, detail="Failed to consume messages from RabbitMQ queue")

    def close_connection(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error(f"Error while closing RabbitMQ connection: {e}")

