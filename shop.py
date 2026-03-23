import requests


class MarketAPI:
    def __init__(self, api_key, team_name="gatitos"):
        self.base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"
        self.headers = {"codinggame-id": api_key}
        self.team_name = team_name.lower()  # On garde le nom de l'équipe pour les filtres
    def get_all_offers(self):
        """Récupère toutes les offres actuellement sur le marché."""
        endpoint = f"{self.base_url}/marketplace/offers"
        response = requests.get(endpoint, headers=self.headers)

        if response.status_code == 200:
            return response.json()
        else:
            print(response)
            print(f"❌ Erreur {response.status_code} lors de la récupération des offres.")
            return None
    def buy(self, offer_id, quantity):
        endpoint = f"{self.base_url}/marketplace/purchases"
        body = {
            "quantity": quantity,
            "offerId": offer_id
        }
        response = requests.post(endpoint, headers=self.headers, json=body)
        if response.status_code in [200, 201]:
            print(f"✅ Achat effectué. Code: {response.status_code}")
            return response.json()
        else:
            print(response)
            print(f"❌ Échec de l'achat. Erreur {response.status_code}")
            return None
    def sell(self, resource_type, quantity, price):

        endpoint = f"{self.base_url}/marketplace/offers"
        body = {
            "resourceType": resource_type,
            "quantityIn": int(quantity),
            "pricePerResource": int(price)
        }

        response = requests.post(endpoint, headers=self.headers, json=body)
        if response.status_code in [200, 201]:
            print(f"✅ Offre créée avec succès (Code {response.status_code})")
            return response.json()
        else:
            print(f"❌ Erreur API Vente: {response.status_code}")
            print(response.json())

            return None
    def get_my_offers(self):
        """Récupère uniquement les offres de ton équipe."""
        all_offers = self.get_all_offers()
        if all_offers is None:
            return []

        mes_offres = [o for o in all_offers if o.get("owner", {}).get("name", "").lower() == self.team_name]
        return mes_offres
    def delete_offer(self, offer_id):
        """Supprime une offre spécifique (doit t'appartenir)."""
        offer_id = str(offer_id).strip()
        endpoint = f"{self.base_url}/marketplace/offers/{offer_id}"

        response = requests.delete(endpoint, headers=self.headers)

        if response.status_code in [200, 204]:  # 204 est le succès standard pour DELETE
            print(f"🗑️ Offre {offer_id} supprimée avec succès.")
            return True
        else:
            print(f"❌ Erreur {response.status_code} sur suppression.")
            try:
                print(f"Message serveur : {response.json()}")
            except:
                print(f"Corps de la réponse : {response.text}")
            return False
    def update_offer(self, offer_id, resource_type, new_quantity, new_price):
        endpoint = f"{self.base_url}/marketplace/offers/{offer_id}"
        body = {
            "resourceType": resource_type.upper(),
            "quantityIn": int(new_quantity),
            "pricePerResource": int(new_price)
        }

        response = requests.patch(endpoint, headers=self.headers, json=body)

        if response.status_code in [200, 204]:
            return response.json() if response.text else True
        else:
            print(response)
            print(f"❌ Erreur {response.status_code} : {response.text}")
            return None