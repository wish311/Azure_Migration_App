import requests
import logging
from uuid import uuid4
import time

# Configure logging
logging.basicConfig(level=logging.INFO)

class DataMigration:
    def __init__(self, source_tenant_id, target_tenant_id, client_id, client_secret, credential, target_domain):
        self.source_tenant_id = source_tenant_id
        self.target_tenant_id = target_tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.credential = credential
        self.target_domain = target_domain

    def _make_request(self, method, url, token, **kwargs):
        try:
            headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
            if not token:
                logging.error("Access token is empty")
            response = requests.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            logging.info(f"Response from {url}: {response.text[:200]}")  # Log the first 200 characters of the response
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
            if response is not None:
                logging.error(f"Response content: {response.text}")
            return None
        except Exception as err:
            logging.error(f"Other error occurred: {err}")
            if response is not None:
                logging.error(f"Response content: {response.text}")
            return None

    def get_users(self):
        token = self._get_token()
        if not token:
            logging.error("Failed to get token for fetching users")
            return None
        return self._get_users(token)

    def _get_token(self):
        try:
            token = self.credential.get_token("https://graph.microsoft.com/.default").token
            logging.info(f"Obtained access token: {token[:50]}...")  # Log part of the token for debugging
            return token
        except Exception as e:
            logging.error(f"Failed to obtain access token: {e}")
            return None

    def _get_users(self, token):
        url = 'https://graph.microsoft.com/v1.0/users'
        response = self._make_request('GET', url, token)
        return response.get('value', []) if response else None

    def get_verified_domains(self):
        token = self._get_token()
        if not token:
            logging.error("Failed to get token for fetching verified domains")
            return None
        url = 'https://graph.microsoft.com/v1.0/domains'
        response = self._make_request('GET', url, token)
        return [domain['id'] for domain in response.get('value', [])] if response else None

    def migrate_user(self, user):
        token = self._get_token()
        if not token:
            logging.error("Failed to get token for migrating user")
            return None

        mail_nickname = user.get('mailNickname', '')
        if not mail_nickname or len(mail_nickname) < 1 or len(mail_nickname) > 64:
            mail_nickname = user.get('userPrincipalName', '').split('@')[0]

        # Verify that the selected domain is in the list of verified domains
        logging.info(f"Using target domain: {self.target_domain}")

        # Use original userPrincipalName but with the new target domain
        original_upn = user.get('userPrincipalName', '')
        unique_upn = f"{original_upn.split('@')[0]}@{self.target_domain}"
        logging.info(f"Generated userPrincipalName: {unique_upn}")

        # Check if the UPN already exists in the target tenant
        if self._upn_exists_in_target_tenant(unique_upn, token):
            logging.error(f"UPN {unique_upn} already exists in the target tenant.")
            return None

        user_params = {
            'accountEnabled': user.get('accountEnabled', True),
            'displayName': user.get('displayName', ''),
            'mailNickname': mail_nickname,
            'userPrincipalName': unique_upn,
            'passwordProfile': {
                'password': 'TemporaryPassword123!',
                'forceChangePasswordNextSignIn': True
            }
        }
        created_user = self._create_user(token, user_params)
        if created_user:
            logging.info(f"User {user.get('displayName')} migrated successfully.")
            # Verify user in target tenant
            if self._verify_user_in_target_tenant(unique_upn):
                logging.info(f"User {user.get('displayName')} verified in target tenant.")
            else:
                logging.error(f"User {user.get('displayName')} not found in target tenant after migration.")
            return created_user
        return None

    def _create_user(self, token, user_params):
        url = 'https://graph.microsoft.com/v1.0/users'
        return self._make_request('POST', url, token, json=user_params)

    def _verify_user_in_target_tenant(self, user_principal_name, max_retries=5, delay=5):
        for attempt in range(max_retries):
            token = self._get_token()
            if not token:
                logging.error("Failed to get token for verifying user")
                return False
            users = self._get_users_paginated(token)
            for user in users:
                if user['userPrincipalName'] == user_principal_name:
                    return True
            logging.info(f"User not found, retrying... ({attempt + 1}/{max_retries})")
            time.sleep(delay)
        return False

    def _get_users_paginated(self, token):
        users = []
        url = 'https://graph.microsoft.com/v1.0/users'
        while url:
            response = self._make_request('GET', url, token)
            if not response:
                break
            users.extend(response.get('value', []))
            url = response.get('@odata.nextLink', None)
        return users

    def _upn_exists_in_target_tenant(self, user_principal_name, token):
        users = self._get_users_paginated(token)
        for user in users:
            if user['userPrincipalName'] == user_principal_name:
                return True
        return False

    def remove_user(self, user_id):
        token = self._get_token()
        if not token:
            logging.error("Failed to get token for removing user")
            return None
        url = f'https://graph.microsoft.com/v1.0/users/{user_id}'
        response = self._make_request('DELETE', url, token)
        if response is None:
            logging.error(f"Failed to delete user with ID {user_id} from source tenant.")
        else:
            logging.info(f"User with ID {user_id} removed from source tenant.")
