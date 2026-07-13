############### Asmbly NeonCRM API Integrations ##################
#      Neon API docs - https://developer.neoncrm.com/api-v2/     #
##################################################################

import base64
import os


class NeonClient:
    N_headers = None

    def __init__(self):
        if os.environ.get("USER") == "ec2-user" or os.environ.get("LAMBDA_TASK_ROOT"):
            from aws_ssm import N_APIkey, N_APIuser
        else:
            from config import N_APIkey, N_APIuser

        # Neon Account Info
        N_auth = f"{N_APIuser}:{N_APIkey}"
        N_baseURL = "https://api.neoncrm.com/v2"
        N_signature = base64.b64encode(bytearray(N_auth.encode())).decode()
        self.N_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {N_signature}",
        }

    def get_headers(self):
        return self.N_headers
