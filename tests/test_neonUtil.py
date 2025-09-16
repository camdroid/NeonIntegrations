import pytest
import mock_config_call
from mock_neon_users import MockNeonUserBuilder
import neonUtil

class TestNeonUtil:
    def test_valid_subscriber_has_facility_access(self):
        account = (MockNeonUserBuilder()
                   .with_valid_membership()
                   .with_facility_tour_date('2025-08-08')
                   .with_waiver_date('2025-08-09')
                   .build())

        assert neonUtil.subscriberHasFacilityAccess(account)

    def test_missing_waiver_loses_access(self):
        account = (MockNeonUserBuilder()
                   .with_valid_membership()
                   .with_facility_tour_date('2025-08-08')
                   .build())

        assert not neonUtil.subscriberHasFacilityAccess(account)

    def test_subscriber_has_ceramics_access(self):
        account = (MockNeonUserBuilder()
                   .with_valid_membership()
                   .with_facility_tour_date('2025-08-08')
                   .with_waiver_date('2025-08-09')
                   .with_ceramics_membership()
                   .with_csi_date('2025-08-08')
                   .build())

        assert neonUtil.subscriberHasCeramicsAccess(account)
