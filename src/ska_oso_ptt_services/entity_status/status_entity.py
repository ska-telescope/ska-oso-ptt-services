from transitions import Machine
from ska_oso_pdm.entity_status_history import SBDStatus
from ska_db_oda.rest.api.resources import post_sbds

# sbd_status = ['Draft', 'Submitted', 'Ready', 'In Progress', 'Observed', 'Suspended', 'Failed Processing', 'Complete']

class StatusStateMachine:

    def __init__(self, sbd_id = None):

        self.sbd_id = sbd_id

        self.machine = Machine(model=self, states=SBDStatus, queued=True, initial=SBDStatus.DRAFT)

        self.previous_state = self.state

        self.machine.add_transition(trigger='ready_for_submission', source=SBDStatus.DRAFT, dest=SBDStatus.SUBMITTED, after=['update_previous_status', 'update_status'])
        self.machine.add_transition(trigger='ready_for_observed', source=SBDStatus.SUBMITTED, dest=SBDStatus.READY, after=['update_previous_status', 'update_status'])
        self.machine.add_transition('sdp_success', [SBDStatus.IN_PROGRESS, SBDStatus.OBSERVED], dest=SBDStatus.COMPLETE, after=['update_previous_status', 'update_status'])
        self.machine.add_transition('failed', '*', dest=SBDStatus.FAILED_PROCESSING, after=['update_previous_status', 'update_status'])

    def update_previous_status(self):

        self.previous_state = self.state

    def update_status(self):

        # sbd_status = put_sbd_history(self.sbd_id, {"current_status": self.state, "previous_status": self.previous_state})

        print(f"Updating {self.sbd_id} Status in ODA DB {self.state} Previous State {self.previous_state}")
        
        

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

# class StatusStateMachine:

#     def __init__(self):

#         self.machine = Machine(model=self, states=ProjectStatus, initial=ProjectStatus.DRAFT)

#         self.machine.add_transition(trigger='ready_for_submission', source=ProjectStatus.DRAFT, dest=ProjectStatus.SUBMITTED)
#         self.machine.add_transition(trigger='ready_for_observed', source=ProjectStatus.SUBMITTED, dest=ProjectStatus.OBSERVED)
#         # self.machine.add_transition(trigger='sdp_success', source=ProjectStatus.OBSERVED, dest=ProjectStatus.COMPLETE)
#         self.machine.add_transition('sdp_success', [ProjectStatus.IN_PROGRESS, ProjectStatus.OBSERVED], dest=ProjectStatus.COMPLETE)
#         self.machine.add_transition('failed', [ProjectStatus.READY, ProjectStatus.IN_PROGRESS], dest=ProjectStatus.CANCELLED)


# prj = StatusStateMachine()

# print(prj.state)

# prj.ready_for_submission()
# prj.ready_for_observed()
# prj.sdp_success()

# print(prj.state)




