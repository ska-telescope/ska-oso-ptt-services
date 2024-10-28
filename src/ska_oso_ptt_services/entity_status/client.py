import time
from random import choice
from kafka import KafkaProducer


producer = KafkaProducer(bootstrap_servers=['localhost:9092'])

topic = 'status_topic'

choice_list = ['Submitted', 'Ready', 'Failed']

def create_sbd():
    producer.send(topic, value=b'create_sbd')
    producer.flush()


def update_sbd_status(message):

    producer.send(topic, key=b'sbd-123', value=message.encode())
    producer.flush()


while True:

    create_sbd()

    # chc = choice(choice_list)

    update_sbd_status(choice_list[0])

    time.sleep(5)

    update_sbd_status(choice_list[1])

    time.sleep(5)

    update_sbd_status(choice_list[2])

    time.sleep(15)


