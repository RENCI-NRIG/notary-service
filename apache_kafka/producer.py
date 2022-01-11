import datetime
import logging as log

import simplejson as json
from django.conf import settings
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=settings.KAFKA_SERVERS,
    key_serializer=lambda m: json.dumps(m).encode('ascii'),
    value_serializer=lambda m: json.dumps(m).encode('ascii'),
    retries=5
)


def on_send_success(record_metadata):
    timestamp = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    information = 'topic: ' + str(record_metadata.topic) \
                  + ', partition: ' + str(record_metadata.partition) \
                  + ', offset: ' + str(record_metadata.offset)
    print('[' + timestamp + '] ' + information)


def on_send_error(excp):
    log.error('errback', exc_info=excp)
    # handle exception


def send_ns_message(topic, message):
    producer.send(
        topic,
        key=settings.KAFKA_SEND_KEY,
        value=message
    ).add_callback(on_send_success).add_errback(on_send_error)
    producer.flush()
