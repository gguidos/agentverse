import logging

logger = logging.getLogger(__name__)

def start_rabbitmq_consumer(container):
    """Function to start consuming from RabbitMQ user authentication queue"""