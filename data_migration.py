import msal
import requests

class DataMigration:
    def __init__(self, source_tenant_id, target_tenant_id, client_id, client_secret):
        self.source_tenant_id = source_tenant_id
        self.target_tenant_id = target_tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.source_access_token = self._get_access_token(source_tenant_id)
        self.target_access_token = self._get_access_token(target_tenant_id)

    def _get_access_token(self, tenant_id):
        authority = f'https://login.microsoftonline.com/{tenant_id}'
        app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=authority
        )
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            return result["access_token"]
        else:
            raise Exception("Could not acquire access token")

    def _make_request(self, method, url, token, **kwargs):
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        response = requests.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    def migrate_data(self, data_types):
        for data_type in data_types:
            if data_type == 'Users':
                self.migrate_users()
            elif data_type == 'Groups':
                self.migrate_groups()
            elif data_type == 'Files':
                self.migrate_files()

    def migrate_users(self):
        source_users = self._get_users(self.source_access_token)
        for user in source_users:
            user_params = {
                'accountEnabled': user['accountEnabled'],
                'displayName': user['displayName'],
                'mailNickname': user['mailNickname'],
                'userPrincipalName': user['userPrincipalName'],
                'passwordProfile': {
                    'password': 'TemporaryPassword123!',
                    'forceChangePasswordNextSignIn': True
                }
            }
            try:
                self._create_user(self.target_access_token, user_params)
                print(f"User {user['displayName']} migrated successfully.")
            except Exception as e:
                print(f"Failed to migrate user {user['displayName']}: {e}")

    def _get_users(self, token):
        url = 'https://graph.microsoft.com/v1.0/users'
        response = self._make_request('GET', url, token)
        return response['value']

    def _create_user(self, token, user_params):
        url = 'https://graph.microsoft.com/v1.0/users'
        self._make_request('POST', url, token, json=user_params)

    def migrate_groups(self):
        source_groups = self._get_groups(self.source_access_token)
        for group in source_groups:
            group_params = {
                'displayName': group['displayName'],
                'mailNickname': group['mailNickname'],
                'mailEnabled': group['mailEnabled'],
                'securityEnabled': group['securityEnabled']
            }
            try:
                self._create_group(self.target_access_token, group_params)
                print(f"Group {group['displayName']} migrated successfully.")
            except Exception as e:
                print(f"Failed to migrate group {group['displayName']}: {e}")

    def _get_groups(self, token):
        url = 'https://graph.microsoft.com/v1.0/groups'
        response = self._make_request('GET', url, token)
        return response['value']

    def _create_group(self, token, group_params):
        url = 'https://graph.microsoft.com/v1.0/groups'
        self._make_request('POST', url, token, json=group_params)

    def migrate_files(self):
        source_files = self._get_files(self.source_access_token)
        for file in source_files:
            file_content = self._download_file_content(self.source_access_token, file)
            self._upload_file_content(self.target_access_token, file, file_content)
            print(f"File {file['name']} migrated successfully.")

    def _get_files(self, token):
        url = 'https://graph.microsoft.com/v1.0/me/drive/root/children'
        response = self._make_request('GET', url, token)
        return response['value']

    def _download_file_content(self, token, file):
        response = requests.get(file['@microsoft.graph.downloadUrl'], headers={'Authorization': f'Bearer {token}'})
        response.raise_for_status()
        return response.content

    def _upload_file_content(self, token, file, content):
        url = f'https://graph.microsoft.com/v1.0/me/drive/root:/{file["name"]}:/content'
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/octet-stream'}
        response = requests.put(url, headers=headers, data=content)
        response.raise_for_status()
