import json
from kafka import KafkaConsumer
from ska_db_oda.rest.api.resources import post_sbds
from ska_db_oda.rest.api.resources import put_sbd_history
from ska_oso_ptt_services.entity_status.status_entity import StatusStateMachine 


ptt_consumer = KafkaConsumer(bootstrap_servers='minikube:9092')

ptt_consumer.subscribe(['status_topic'])


for msg in ptt_consumer:

    # msg.value

    if msg.headers[0][1] == b'create_sbd':

        print("Create SBD")
        # sbd_data = json.load(open("/home/sagar/Projects/ska-db-oda/tests/files/testfile_sample_mid_sb.json"))

        # sbd_status = post_sbds(sbd_data)

        # sbd = StatusStateMachine(sbd_status.sbd_id)

    if msg.headers[0][1] == b'update_status':

        print("Update SBD Status")

        # sbd_status = put_sbd_history(self.sbd_id, {"current_status": self.state, "previous_status": self.previous_state})



# sbd = StatusStateMachine("sbd-123")

# print(sbd.sbd_id)

# print(sbd.state)
# sbd.ready_for_submission()
# print(sbd.state)
# sbd.ready_for_observed()
# print(sbd.state)
# # sbd.sdp_success()
# # print(sbd.state)
# sbd.failed()
# print(sbd.state)