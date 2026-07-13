############### Asmbly NeonCRM API Integrations ##################
#      Neon API docs - https://developer.neoncrm.com/api-v2/     #
##################################################################

import base64
import os
import requests


N_baseURL = "https://api.neoncrm.com/v2"


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

    def _get(self, url):
        response = requests.get(url, headers=self.get_headers())
        if response.status_code != 200:
            raise ValueError(f"Get {url} returned status code {response.status_code}: {response.text}")
        return response

    def _patch(self, url, data):
        response = requests.patch(url, json=data, headers=self.get_headers())
        if response.status_code != 200:
            raise ValueError(f"Patch {url} returned status code {response.status_code}")
        return response

    def get_memberships(self, account_id):
        url = N_baseURL + f'/accounts/{account_id}/memberships'
        return self._get(url)

    def get_account(self, account_id):
        url = N_baseURL + f"/accounts/{account_id}"
        return self._get(url)

    def patch_account(self, account_id, data):
        url = N_baseURL + f'/accounts/{account_id}'
        return self._patch(url, data)
