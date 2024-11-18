import json
import time
import requests
from kafka import KafkaConsumer
from transitions import MachineError
from ska_oso_ptt_services.entity_status.status_entity import StatusStateMachine 

topic = "status_topic"

sbd_create_url = "http://0.0.0.0:8000/ska-db-oda/oda/api/v6/sbds"
sbd_status_url = "http://0.0.0.0:8000/ska-db-oda/oda/api/v6/status/sbds"

sbd_status_data = {
    "current_status": "Draft",
    "sbd_ref": "sbd-mvp01-20220923-00001",
    "sbd_version": 1, 
    "metadata": {
        "version": 1,
      "created_by": "DefaultUser",
      "created_on": "2024-04-14T11:51:16.367278+05:30",
      "last_modified_by": "DefaultUser",
      "last_modified_on": "2024-04-14T11:51:16.367278+05:30",
      "pdm_version": "15.4.0",
    },
    "previous_status": "Draft"
  }

headers = {
    "Content-Type": "application/json"
}

def read_file(path):
    with open(path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)
    

def print_response(response):

    if response.status_code == 200:
        response_data = response.json()
        print("@" * 50)
        print(f"Entity SBD ID {response_data['sbd_ref']} \nPrevious Status {response_data['previous_status']} \nCurrent Status {response_data['current_status']}")
        print("@" * 50)
    else:
        print("Request failed with status code:", response.status_code)
        print("Response:", response.text)

def update_status_data(sbd_id, sbd_status_data, sbd_state_machine):

    sbd_status_data["current_status"] = sbd_state_machine.state.value
    sbd_status_data["sbd_ref"] = sbd_id
    sbd_status_data["previous_status"] = sbd_state_machine.previous_state.value


ptt_consumer = KafkaConsumer(bootstrap_servers=['localhost:9092'],
                            auto_offset_reset='latest',
                            # enable_auto_commit=True,
                            group_id='my-status-group')

ptt_consumer.subscribe(topic)

sbd_data = read_file("/home/sagar/Projects/ska-db-oda/tests/files/testfile_sample_mid_sb.json")

for msg in ptt_consumer:

    print(f"Message Received {msg.value.decode()}")

    if msg.value == b'create_sbd':

        response = requests.post(sbd_create_url, json=sbd_data, headers=headers)
       
        if response.status_code == 200:

            sbd_response_data = response.json()
            sbd_id = sbd_response_data['sbd_id']

            sbd = StatusStateMachine(sbd_id)

            print(f"Initial Status of SBD {sbd_id} {sbd.state}")

        else:

            print("Request failed with status code:", response.status_code)
            print("Response:", response.text)

        time.sleep(2)

    if msg.key is not None:

        if msg.value == b'Submitted':

            sbd.ready_for_submission()
            update_status_data(sbd_id, sbd_status_data, sbd)
            response = requests.put(f"{sbd_status_url}/{sbd_id}", json=sbd_status_data, headers=headers)

            print_response(response)

            time.sleep(2)

        elif msg.value == b'Ready':

            sbd.ready_for_observed()
            update_status_data(sbd_id, sbd_status_data, sbd)
            response = requests.put(f"{sbd_status_url}/{sbd_id}", json=sbd_status_data, headers=headers)

            print_response(response)

            time.sleep(2)

        elif msg.value == b'Failed':

            try:
            
                # sbd.failed()
                sbd.sdp_success()
                update_status_data(sbd_id, sbd_status_data, sbd)
                response = requests.put(f"{sbd_status_url}/{sbd_id}", json=sbd_status_data, headers=headers)

                print_response(response)

                time.sleep(2)
            
            except MachineError as e:

                print(f"Machine Error", e)
            
        elif msg.value == b'Success':

            sbd.sdp_success()

            update_status_data(sbd_id, sbd_status_data, sbd)
            response = requests.put(f"{sbd_status_url}/{sbd_id}", json=sbd_status_data, headers=headers)

            print_response(response)

            time.sleep(2)

    time.sleep(2)