import simplejson as json
from django.conf import settings
from django.utils import timezone
from kafka import KafkaConsumer

from .models import Message


def check_for_new_messages(topic):
    consumer = KafkaConsumer(
        group_id='notary-service',
        bootstrap_servers=settings.KAFKA_SERVERS,
        key_deserializer=lambda m: json.loads(m.decode('ascii')),
        value_deserializer=lambda m: json.loads(m.decode('ascii')),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        consumer_timeout_ms=1000,
    )
    consumer.subscribe([topic])

    for message in consumer:
        # message value and key are raw bytes -- decode if necessary!
        # e.g., for unicode: `message.value.decode('utf-8')`
        print("%s:%d:%d: key=%s value=%s" % (message.topic, message.partition,
                                             message.offset, message.key,
                                             message.value))
        create_ns_message(message)

    consumer.close()
    pass


def create_ns_message(kafka_message):
    print(kafka_message.value['ns-message'])
    if kafka_message.value['ns-message']:
        if not Message.objects.filter(
                kafka_topic=kafka_message.topic,
                kafka_partition=kafka_message.partition,
                kafka_offset=kafka_message.offset,
                kafka_key=kafka_message.key,
        ).exists():
            msg_dict = kafka_message.value['ns-message']
            message = Message.objects.create(
                subject=msg_dict['subject'],
                body=msg_dict['body'],
                is_active=True,
                created_by='System Account',
                created_date=timezone.now(),
                modified_by='System Account',
                modified_date=timezone.now(),
                kafka_topic=kafka_message.topic,
                kafka_partition=kafka_message.partition,
                kafka_offset=kafka_message.offset,
                kafka_key=kafka_message.key,
            )
            if msg_dict['reference_url']:
                message.reference_url = msg_dict['reference_url']
            else:
                message.reference_url = None
            message.save()
            print(message)
