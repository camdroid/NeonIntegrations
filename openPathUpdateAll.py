###############################################################################
#Fetch all member records from Neon and update OpenPath as necessary for all
#* Run me at least once a day to catch subscription expirations

import neonUtil
import openPathUtil
import logging
import json
from email.mime.text import MIMEText
from AsmblyMessageFactory import commonMessageFooter
import gmailUtil

logging.basicConfig(
         format='%(asctime)s %(levelname)-8s %(message)s',
         level=logging.INFO,
         datefmt='%Y-%m-%d %H:%M:%S')

class MembershipStats:
    def __init__(self):
        self.subscriberCount = 0
        self.ceramicsCount = 0
        self.facilityUserCount = 0
        self.ceramicsFacilityCount = 0
        self.paidRegulars = 0
        self.paidCeramics = 0

        self.warningUsers = []
        self.missingTourSubscribers = {}
        self.missingWaiverSubscribers = {}
        self.missingCsiSubscribers = {}
        self.compedSubscribers = []
        self.compedLeaders = []

def getWarningText(warningUsers):
    if len(warningUsers) == 0:
        return ""

    list_separator = '\n      '
    return f'''
    WARNING: {len(warningUsers)} USER{'S HAVE' if len(warningUsers) > 1 else ' HAS'} FACILITY ACCESS WITHOUT A SIGNED WAIVER:
      {list_separator.join(warningUsers)}'''

def openPathUpdateAll(neonAccounts, mailSummary = False):
    opUsers = openPathUtil.getAllUsers()
    stats = MembershipStats()

    for account in neonAccounts:
        if not neonAccounts[account].get("paidRegular") and not neonAccounts[account].get("paidCeramics") and not neonUtil.accountIsType(neonAccounts[account], neonUtil.STAFF_TYPE):
            #Accounts that are neither paid nor staff might still have access
            if neonUtil.accountIsType(neonAccounts[account], neonUtil.LEAD_TYPE):
                stats.compedLeaders.append(f'''{neonAccounts[account].get("fullName")} ({neonAccounts[account].get("Email 1")})''')
            elif neonAccounts[account].get("compedRegular") or neonAccounts[account].get("compedCeramics"):
                stats.compedSubscribers.append(f'''{neonAccounts[account].get("fullName")} ({neonAccounts[account].get("Email 1")})''')

        if neonAccounts[account].get("validMembership"):
            stats.subscriberCount += 1
            if neonAccounts[account].get("ceramicsMembership"):
                stats.ceramicsCount += 1

            #accounts with concurrent paid regular and ceramics memberships are most likely
            #upgrades that should be only counted as ceramics members
            if neonAccounts[account].get("paidCeramics"):
                stats.paidCeramics += 1
            elif neonAccounts[account].get("paidRegular"):
                stats.paidRegulars += 1

        if neonAccounts[account].get("paidRegular") and neonAccounts[account].get("paidCeramics"):
            logging.info(f'''{neonAccounts[account].get("fullName")} ({neonAccounts[account].get("Email 1")}) has concurrent paid memberships.''')

        if neonUtil.subscriberHasFacilityAccess(neonAccounts[account]):
            stats.facilityUserCount += 1

        if neonUtil.subscriberHasCeramicsAccess(neonAccounts[account]):
            stats.ceramics_facility_count += 1

        if neonAccounts[account].get("OpenPathID"):
            openPathUtil.updateGroups(neonAccounts[account], 
                                        openPathGroups=opUsers.get(int(neonAccounts[account].get("OpenPathID"))).get("groups"))
            #note that this isn't necessarily 100% accurate, because we have Neon users with provisioned OpenPath IDs and no access groups
            #assuming that typical users who gained and lost openPath access have a signed waiver
            if not neonAccounts[account].get("WaiverDate"):
                stats.warningUsers.append(f'''{neonAccounts[account].get("fullName")} ({neonAccounts[account].get("Email 1")})''')
        elif neonUtil.accountHasFacilityAccess(neonAccounts[account]):
            neonAccounts[account] = openPathUtil.createUser(neonAccounts[account])
            openPathUtil.updateGroups(neonAccounts[account],
                                        openPathGroups=[]) #pass empty groups list to skip the http get
            openPathUtil.createMobileCredential(neonAccounts[account])
        elif neonAccounts[account].get("validMembership"):
            startDate = neonAccounts[account].get("Membership Start Date")
            if not neonAccounts[account].get("WaiverDate"):
                stats.missingWaiverSubscribers[account] = f'''{neonAccounts[account].get("fullName")} ({neonAccounts[account].get("Email 1")}) - since {startDate}'''
            if not neonAccounts[account].get("FacilityTourDate"):
                stats.missingTourSubscribers[account] = f'''{neonAccounts[account].get("fullName")} ({neonAccounts[account].get("Email 1")}) - since {startDate}'''

        #an account might be missing CSI but still have regular facility access stuff handled
        if neonAccounts[account].get("ceramicsMembership") and not neonAccounts[account].get("CsiDate"):
            stats.missingCsiSubscribers[account] = f'''{neonAccounts[account].get("fullName")} ({neonAccounts[account].get("Email 1")}) - since {neonAccounts[account].get("Ceramics Start Date")}'''

    list_separator = '\n            '
    compedSubscriberString = ""
    compedSubscriberDetails =""
    compedLeaderDetails = ""
    if (len(stats.compedSubscribers)+len(stats.compedLeaders) > 0):
        compedSubscriberString = f''' plus {len(stats.compedSubscribers)+len(stats.compedLeaders)} complimentary memberships'''
        if (len(stats.compedLeaders) > 0):
            compedLeaderDetails = f'''
        Comped Volunteer Leaders:
            {list_separator.join(stats.compedLeaders[x] for x in range(len(stats.compedLeaders)))}
'''
        if (len(stats.compedSubscribers) > 0):
            compedSubscriberDetails = f'''
        Other Comped Memberships:
            {list_separator.join(stats.compedSubscribers[x] for x in range(len(stats.compedSubscribers)))}
'''

    msg = MIMEText(f'''
    Today Asmbly has {stats.paidRegulars} regular and {stats.paidCeramics} ceramics subscribers{compedSubscriberString}.

    Of those:
        {stats.facilityUserCount} have facility access and {stats.ceramicsFacilityCount} have ceramics access
        {len(stats.missingWaiverSubscribers)} are missing the waiver{':' if len(stats.missingWaiverSubscribers) > 0 else ' (yay!)'}
            {list_separator.join(stats.missingWaiverSubscribers[x] for x in sorted(stats.missingWaiverSubscribers, reverse=True))}
        {len(stats.missingTourSubscribers)} are missing orientation{':' if len(stats.missingTourSubscribers) > 0 else ' (yay!)'}
            {list_separator.join(stats.missingTourSubscribers[x] for x in sorted(stats.missingTourSubscribers, reverse=True))}
        {len(stats.missingCsiSubscribers)} are missing Ceramics Introduction{':' if len(stats.missingCsiSubscribers) > 0 else ' (yay!)'}
            {list_separator.join(stats.missingCsiSubscribers[x] for x in sorted(stats.missingCsiSubscribers, reverse=True))}
{getWarningText(stats.warningUsers)}
{compedLeaderDetails}
{compedSubscriberDetails}
{commonMessageFooter}
''')
    msg['To'] = "membership@asmbly.org"
    msg['Subject'] = "Asmbly Daily Subscriber Update"

    summaryMsg = MIMEText(f'''
    Today Asmbly has {stats.paidRegulars} regular and {stats.paidCeramics} ceramics paid subscribers.

    Additionally:
        {len(stats.compedLeaders)} Asmbly leaders have free memberships.
        {len(stats.compedSubscribers)} other Asmbly volunteers have free memberships.

    {stats.facilityUserCount} users have facility access and {stats.ceramicsFacilityCount} have ceramics access
    {len(stats.missingWaiverSubscribers)} are missing the waiver.
    {len(stats.missingTourSubscribers)} are missing orientation.
    {len(stats.missingCsiSubscribers)} are missing Ceramics Introduction.

{commonMessageFooter}
''')
    summaryMsg['To'] = "membership.committee@asmbly.org"
    summaryMsg['Subject'] = "Asmbly Daily Subscriber Summary"

    if mailSummary:
        gmailUtil.sendMIMEmessage(msg)
        gmailUtil.sendMIMEmessage(summaryMsg)

    logging.info(msg.get_payload())
    print(summaryMsg.get_payload())

#begin standalone script functionality -- pull neonAccounts and call our function
def main():
    neonAccounts = {}

    #For real use, just get neon accounts directly
    #Be aware this takes a long time (2+ minutes)
    neonAccounts = neonUtil.getRealAccounts()

    # Testing goes a lot faster if we're working with a cache of accounts
    #with open("Neon/neonAccounts.json") as neonFile:
    #    neonAccountJson = json.load(neonFile)
    #    for account in neonAccountJson:
    #        neonAccounts[neonAccountJson[account]["Account ID"]] = neonAccountJson[account]

    openPathUpdateAll(neonAccounts)

if __name__ == "__main__":
    main()
