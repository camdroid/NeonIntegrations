from typing import Self
import string
import random

##### Needed for importing script files (as opposed to classes)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
##### End block

import neonUtil

class MockNeonUserBuilder():
    def __init__(self):
        self.reset()

    def random_alphanumeric(self, length):
        characters = string.ascii_letters + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

    def reset(self):
        # TODO: Determine whether Neon IDs are alphanumeric or just numeric
        self._id = self.random_alphanumeric(6)
        self._name = "John Doe"
        self._email = "john@example.com"
        self._individual_types = []
        self._open_path_id = random.randint(1, 100000)
        self._valid_membership = False
        self._paid_regular = False
        self._paid_ceramics = False
        self._waiver_date = None
        self._facility_tour_date = None
        self._ceramics_membership = False
        self._csi_date = None
        return self

    def with_type(self, neon_type):
        self._individual_types.append({'name': neon_type})
        return self

    def with_alta_id(self, alta_id: int) -> Self:
        self._open_path_id = alta_id
        return self

    def with_valid_membership(self, val=True) -> Self:
        self._valid_membership = val
        return self

    def with_paid_regular(self, val: bool = True) -> Self:
        self._paid_regular = val
        return self

    def with_paid_ceramics(self, val: bool = True) -> Self:
        self._paid_ceramics = val
        return self

    def with_waiver_date(self, date) -> Self:
        self._waiver_date = date
        return self

    def with_facility_tour_date(self, date) -> Self:
        self._facility_tour_date = date
        return self

    def with_ceramics_membership(self, val: bool = True) -> Self:
        self._ceramics_membership = val
        return self

    def with_csi_date(self, date) -> Self:
        self._csi_date = date
        return self

    def build(self):
        return {
            'id': self._id,
            'name': self._name,
            'email': self._email,
            'individualTypes': self._individual_types,
            'OpenPathID': self._open_path_id,
            'validMembership': self._valid_membership,
            'paidRegular': self._paid_regular,
            'paidCeramics': self._paid_ceramics,
            'WaiverDate': self._waiver_date,
            'FacilityTourDate': self._facility_tour_date,
            'ceramicsMembership': self._ceramics_membership,
            'CsiDate': self._csi_date,
        }
