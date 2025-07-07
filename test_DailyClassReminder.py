from dailyClassReminder import *
from helpers import gmail
from email.mime.multipart import MIMEMultipart
import pytest
import pytest_mock
from helpers import neon

class TestDailyClassReminder:
    def test_compose_email(self):
        send_reminder_email('test@test.com', 'classes@asmbly.org', 'Test Subject', EMAIL_TEMPLATE)

    def test_prettify_registrant(self, mocker):
        test_registrant = {
            'registrantAccountId': 1,
            'tickets': [
                {
                    'attendees': [{
                        'firstName': 'Cam',
                        'lastName': 'Herringshaw',
                    }],
                },
            ],
        }
        example_account_individual = {
            'individualAccount': {
                'primaryContact': {
                    'email1': 'test@test.com',
                    'addresses': [
                        { 'phone1': '5551234567' },
                    ]
                }
            }
        }

        stub = mocker.patch('helpers.neon.getAccountIndividual', return_value=example_account_individual)
        prettify_registrant(test_registrant)
