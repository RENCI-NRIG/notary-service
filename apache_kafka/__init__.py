import simplejson as json
from django.conf import settings
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_SERVERS,
    key_serializer=lambda m: json.dumps(m).encode('ascii'),
    value_serializer=lambda m: json.dumps(m).encode('ascii'),
    retries=5
)
