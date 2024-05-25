import logging
import requests

class SolarWindsAPI:
    def __init__(self, api_token):
        self.api_url = "https://api.solarwinds.com/v1"  # Example base API URL, replace with actual
        self.api_token = api_token
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    def fetch_user_requests(self):
        try:
            url = f"{self.api_url}/requests"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to fetch user requests: {e}")
            return []

    def update_ticket(self, ticket_id, note):
        try:
            url = f"{self.api_url}/requests/{ticket_id}"
            payload = {"note": note}
            response = requests.put(url, headers=self.headers, json=payload)
            response.raise_for_status()
            logging.info(f"Updated ticket {ticket_id}")
        except Exception as e:
            logging.error(f"Failed to update ticket {ticket_id}: {e}")

    def get_manager_email(self, ticket):
        try:
            # Assuming the ticket data contains a 'customFields' dictionary with manager email
            custom_fields = ticket.get('customFields', [])
            for field in custom_fields:
                if field.get('name') == 'ManagerEmail':
                    return field.get('value', 'manager@default.com')
            logging.warning(f"Manager email not found in ticket {ticket.get('id', 'unknown')}")
            return 'manager@default.com'
        except Exception as e:
            logging.error(f"Failed to extract manager email: {e}")
            return 'manager@default.com'
