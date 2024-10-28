from transitions import Machine
from ska_oso_pdm.entity_status_history import SBDStatus

# sbd_status = ['Draft', 'Submitted', 'Ready', 'In Progress', 'Observed', 'Suspended', 'Failed Processing', 'Complete']

class StatusStateMachine:

    def __init__(self, sbd_id = None):

        self.sbd_id = sbd_id

        self.machine = Machine(model=self, states=SBDStatus, queued=True, initial=SBDStatus.DRAFT)

        self.previous_state = self.state

        self.machine.add_transition(trigger='ready_for_submission', source=SBDStatus.DRAFT, dest=SBDStatus.SUBMITTED, before=['update_previous_status'])
        self.machine.add_transition(trigger='ready_for_observed', source=SBDStatus.SUBMITTED, dest=SBDStatus.READY, before=['update_previous_status'])
        self.machine.add_transition('sdp_success', [SBDStatus.IN_PROGRESS, SBDStatus.OBSERVED], dest=SBDStatus.COMPLETE, before=['update_previous_status'])
        self.machine.add_transition('failed', '*', dest=SBDStatus.FAILED_PROCESSING, before=['update_previous_status'])

    def update_previous_status(self):

        self.previous_state = self.state
        
        






