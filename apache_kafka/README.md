# Kafka messages

**What is Kafka?**

Apache Kafka is a distributed streaming platform. What exactly does that mean?

- A streaming platform has three key capabilities:
    - Publish and subscribe to streams of records, similar to a message queue or enterprise messaging system.
    - Store streams of records in a fault-tolerant durable way.
    - Process streams of records as they occur.
- More information at [https://kafka.apache.org](https://kafka.apache.org)

This project uses the [kafka-python](https://kafka-python.readthedocs.io/en/master/) package

## Django model

### Basic model

Required message elements are `subject` and `body`

```python
class Message(models.Model):
    subject = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    body = models.TextField()
    reference_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=255, default='System Account')
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.CharField(max_length=255, default='System Account')
    modified_date = models.DateTimeField(blank=True, null=True)
    kafka_topic = models.CharField(max_length=255, blank=True, null=True)
    kafka_partition = models.IntegerField(blank=True, null=True)
    kafka_offset = models.IntegerField(blank=True, null=True)
    kafka_key = models.CharField(max_length=255, blank=True, null=True)
    
    def __str__(self):
        return self.subject
```

### Sending a message

**Example**: Send User welcome message 


```python
# generate welcome message
subject = 'Welcome'
body = 'Hello ' + str(user.name) + ', welcome to the Notary Service!'
reference_url = 'https://ns-dev-1.cyberimpact.us'
is_active = True
ns_message = {
    "ns-message": {'subject': subject, 'body': body, 'reference_url': reference_url, 'is_active': is_active}}
print('topic: ' + str(user.uuid) + ', message: ' + str(ns_message))
send_ns_message(str(user.uuid), ns_message) # expects topic and message as arguments
```

### Receiving a message

**Example**: create new ns_message object

Check for new messages

```python
from apache_kafka.consumer import check_for_new_messages

# check for new messages
check_for_new_messages(str(request.user.uuid)) # expect topic as argument
```

On new message discovery, a new ns_message object is created

```python
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
```
