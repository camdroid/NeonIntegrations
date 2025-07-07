################## Asmbly NeonCRM & Gmail API Integrations ##################
#   Neon API docs - https://developer.neoncrm.com/api-v2/                   #
#  Gmail API docs - https://developers.google.com/gmail/api/reference/rest  #
#############################################################################
#############################################################################
#  This helper script grabs Event data from Neon and cross references a     #
#  json file with teachers' email addresses in order to send reminder       #
#  emails each week about scheduled classes.                                #
#############################################################################

# Outside of the following imports, this script relies on teachers.json file
# containing teacher names and emails which is expected in the same directory
# as this script.

# Currently this script is set to run on a daily basis

import json
import datetime
import logging

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from helpers.gmail import sendMIMEmessage

from helpers import neon

logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%H:%S",
)

TODAY = datetime.date.today()

EMAIL_TEMPLATE ="""
Hi {teacher_first_name},

This is an automated email to remind you of the upcoming classes you are scheduled to teach at Asmbly.
Thank you for sharing your knowledge with the community!

{pretty_events}

Please note these are the registrations as of the time of this email and may not reflect final registrations for your class.
You can see more details about these events and registrants in your Neon backend account.  
The login URL is https://asmbly.z2systems.com/np/admin/content/contentList.do
Email classes@asmbly.org if you have any questions about the above schedule.

\t* Note: Some registrants are purchased under a single account and thus end up with the same email and phone number.


Thanks again!
Asmbly AdminBot
"""


NEON_EVENT_OUTPUT_FIELDS = [
    "Event Name",
    "Event ID",
    "Event Topic",
    "Event Start Date",
    "Event Start Time",
    "Event End Date",
    "Event End Time",
    "Event Registration Attendee Count",
    "Registrants",
    "Hold To Waiting List",
    "Waiting List Status",
]


def get_neon_events_in_next_2_days(n_days):
    delta_days = (TODAY + datetime.timedelta(days=2)).isoformat()
    search_fields = [
        {
            "field": "Event Start Date",
            "operator": "GREATER_AND_EQUAL",
            "value": TODAY.isoformat(),
        },
        {"field": "Event Start Date", "operator": "LESS_AND_EQUAL", "value": delta_days},
        {"field": "Event Archived", "operator": "EQUAL", "value": "No"},
    ]

    return neon.postEventSearch(search_fields, NEON_EVENT_OUTPUT_FIELDS)['searchResults']


def load_teacher_contact_info():
    # Import teacher contact info
    contact_info = "teachers.json"
    with open(contact_info, "r", encoding="utf-8") as f:
        TEACHER_EMAILS = json.load(f)


# Find all events for each teacher
def get_events_by_teacher(all_events):

    # Remove duplicates in the list of teachers
    teachers = {item.get("Event Topic") for item in all_events}

    events_by_teacher = {}
    for teacher in teachers:
        events = list(filter(
            lambda x, teach=teacher: x["Event Topic"] == teach,
            all_events,
        ))
        sorted_events = sorted(
            events, key=lambda x: datetime.datetime.fromisoformat(x["Event Start Date"])
        )
        events_by_teacher[teacher] = sorted_events
    return events_by_teacher


# Retrieve email and phone associated with this account ID
# Registrations with multiple attendees may have different emails listed in the UI
# but these aren't accessible from the API, so we will just use the info from the main account
def prettify_registrant(registrant):
    acct_info = neon.getAccountIndividual(registrant['registrantAccountId'])
    primary_contact = acct_info['individualAccount']['primaryContact']
    email = primary_contact['email1']

    phone = [addr['phone1'] for addr in primary_contact['addresses'] if addr['phone1']][0]
    if not phone:
        phone = "N/A"

    results = ''
    for attendee in registrant['tickets'][0]['attendees']:
        results += f'\t{attendee["firstName"]} {attendee["lastName"]}: {email}, {phone}\n\t'
    return results


def send_reminder_email(to_addr, cc_addr, subject, content):
    mime_message = MIMEMultipart()
    mime_message["To"] = to_addr
    if cc_addr:
        mime_message['CC'] = cc_addr
    mime_message["Subject"] = subject

    mime_message.attach(MIMEText(content, "plain"))
    sendMIMEmessage(mime_message)


# Build up formatted event info for email body
def format_event_info(event, pretty_registrants):
    raw_time = event["Event Start Time"]
    raw_date = event["Event Start Date"]

    datetime_date = datetime.datetime.strptime(raw_date, "%Y-%m-%d").date()
    formatted_date = datetime.date.strftime(datetime_date, "%B %d")
    start_time = datetime.datetime.strptime(raw_time, "%H:%M:%S").strftime(
        "%I:%M %p"
    )
    if datetime_date == TODAY:
        date_string = f"TODAY - {formatted_date}"
    elif datetime_date == TODAY + datetime.timedelta(days=1):
        date_string = f"Tomorrow - {formatted_date}"
    else:
        date_string = formatted_date
    info = f"""
    {event["Event Name"]}
    Date: {date_string}
    Time: {start_time}
    Number of registrants: {event["Registrants"]}
        {pretty_registrants}
    """
    return info


def compose_and_send_email(teacher, pretty_events):
    if not teacher:
        logging.info("WARNING: No teacher assigned!")
        teacher_first_name = "N/A"
        to_addr = 'classes@asmbly.org'
        cc_addr = None
        subject = f'Failed Class Reminder - {teacher}'
    else:
        teacher_first_name = teacher[: teacher.index(" ")]
        to_addr = TEACHER_EMAILS[teacher]
        cc_addr = 'classes@asmbly.org'
        subject = 'Your upcoming classes at Asmbly'

    email_msg = EMAIL_TEMPLATE.format(
        teacher_first_name=teacher_first_name, pretty_events=pretty_events
    )
    send_reminder_email(to_addr, cc_addr, subject, email_msg)


def get_successful_registrants(event_registration):
    return [r for r in event_registration
            if r['tickets'][0]['attendees'][0]['registrationStatus'] == 'SUCCEEDED']


def prettify_registrants(registrants, attendee_count):
    result = ""
    if registrants and attendee_count > 0:
       # Iterate over response to add registrant account IDs to
       # dictionary organized by registration status
       for registrant in registants:
           result += prettify_registrant(registrant)
    else:
        result += "\tNo attendees registered currently. Check Neon for updates as event approaches.\n\t"
    return result


def main():
    # Get events for the next 2 days
    logging.info("\n\n----- Beginning class reminders for %s -----\n\n", TODAY.isoformat())
    load_teacher_contact_info()

    all_events = get_neon_events_in_next_2_days()

    # Begin gathering data for emailing each teacher
    # Send each teacher an email reminder about classes they are scheduled to teach
    events_by_teacher = get_events_by_teacher(all_events)
    for teacher, events in events_by_teacher.items():
        logging.info(f"\n\n_____\n\nEmailing {teacher} about {len(event)} event(s)...")

        # Reformat event data so it looks nice in email
        pretty_events = ""
        for event in events_by_teacher[teacher]:
            event_id = event["Event ID"]
            logging.info(event_id)
            logging.info(event["Event Name"])

            individual_event_reg = neon.getEventRegistrants(event_id)

            # Get total number of attendees (doesn't always coincide with number of account IDs)
            registration = individual_event_reg['eventRegistrations']
            attendee_count = neon.getEventRegistrantCount(registration)
            logging.info(attendee_count)

            # Registrant info formatted for email
            successful_registrants = get_successful_registrants(registration)
            pretty_registrants = prettify_registrants(successful_registrants, attendee_count)
            pretty_events += format_event_info(event, pretty_registrants)

        compose_and_send_email(teacher, pretty_events)

if __name__ == '__main__':
    main()
