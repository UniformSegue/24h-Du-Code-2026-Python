import requests
from api import ApiJoin

class TaxAPI:
    def __init__(self, api_key):
        self.base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"
        self.headers = {"codinggame-id": api_key}

    def get_due_taxes(self):
        """Récupère la liste des taxes impayées (DUE)."""
        endpoint = f"{self.base_url}/taxes"
        params = {"status": "DUE"}

        response = requests.get(endpoint, headers=self.headers, params=params)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erreur API Taxes ({response.status_code}): {response.text}")
            return []

    def pay_tax(self, tax_id):
        """Paye une taxe spécifique via son ID (UUID)."""
        endpoint = f"{self.base_url}/taxes/{tax_id}"
        response = requests.put(endpoint, headers=self.headers)

        if response.status_code in [200, 204]:
            print(f"✅ Taxe {tax_id} payée.")
            return True
        else:
            print(f"❌ Échec paiement taxe {tax_id} ({response.status_code})")
            return False


import requests


class UpgradeAPI:
    def __init__(self, api_key):
        self.base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"
        self.headers = {"codinggame-id": api_key}
    def get_storage_next_level(self):
        """Récupère les infos sur la prochaine amélioration de l'entrepôt."""
        endpoint = f"{self.base_url}/storage/next-level"
        response = requests.get(endpoint, headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def upgrade_storage(self):
        """Améliore l'entrepôt au prochain niveau attendu."""
        next_info = self.get_storage_next_level()
        if not next_info or "id" not in next_info:
            print("❌ Impossible de trouver le prochain niveau de stockage.")
            return None

        target_level_id = next_info["id"]  # C'est cet ID que le serveur attend
        endpoint = f"{self.base_url}/storage/upgrade"
        body = {"level": target_level_id}
        response = requests.put(endpoint, headers=self.headers, json=body)
        return response
    def get_ship_next_level(self):
        """Récupère les infos sur la prochaine amélioration du navire."""
        endpoint = f"{self.base_url}/ship/next-level"
        response = requests.get(endpoint, headers=self.headers)
        return response.json() if response.status_code == 200 else None

    def upgrade_ship(self):
        """Améliore le navire au prochain niveau attendu."""
        next_info = self.get_ship_next_level()
        if not next_info or "id" not in next_info:
            print("❌ Impossible de trouver le prochain niveau du navire.")
            return None

        target_level_id = next_info["id"]  # C'est cet ID que le serveur attend
        endpoint = f"{self.base_url}/ship/upgrade"
        body = {"level": target_level_id}
        response = requests.put(endpoint, headers=self.headers, json=body)
        return response


class TheftAPI:
    def __init__(self, api_key):
        self.base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"
        self.headers = {"codinggame-id": api_key}

    def launch_theft(self, resource_type, money_spent):
        endpoint = f"{self.base_url}/thefts/player"
        body = {"resourceType": resource_type.upper(), "moneySpent": int(money_spent)}
        response = requests.post(endpoint, headers=self.headers, json=body)
        return response.json() if response.status_code in [200, 201] else None

    def get_theft_history(self):
        endpoint = f"{self.base_url}/thefts"
        response = requests.get(endpoint, headers=self.headers)
        return response.json() if response.status_code == 200 else []