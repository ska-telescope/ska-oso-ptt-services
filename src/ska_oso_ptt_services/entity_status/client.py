from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='minikube:9092')

kafka_topic = 'status-topic'

# >>> import json
# >>> producer = KafkaProducer(value_serializer=lambda v: json.dumps(v).encode('utf-8'))
# >>> producer.send('fizzbuzz', {'foo': 'bar'})


def create_sbd():
    producer.send(kafka_topic, key=b'create_sbd', value=b'create_sbd')


def update_sbd_status():

    producer.send(kafka_topic, key=b'sbd-123', value=b'Ready')


# create_sbd()
# update_sbd_status()
