import requests
from shop import MarketAPI
from api import ApiJoin
import time

while(True):
    api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb2RpbmdnYW1lIiwic3ViIjoiMGEyNzcwODItYjZlNi00Y2E3LWJlMTItZGE4OGU1N2Q4NmI4Iiwicm9sZXMiOlsiVVNFUiJdfQ.9lmC6AZsJktL3F92Zm2dj8SEdAGfzeWk08g13hB4qRE"

    api = ApiJoin(api_key)
    market = MarketAPI(api_key, team_name="Gatitos")
    ressource = api.resources()
    data = api.connect_get("/players/details")
    inventaire = {
        "CHARBONIUM": {
            "actuel": ressource["CHARBONIUM"],
            "max": data["storage"]["maxResources"]["CHARBONIUM"]
        },
        "FERONIUM": {
            "actuel": ressource["FERONIUM"],
            "max": data["storage"]["maxResources"]["FERONIUM"]
        },
        "BOISIUM": {
            "actuel": ressource["BOISIUM"],
            "max": data["storage"]["maxResources"]["BOISIUM"]
        }
    }
    def gerer_surplus(nom_ressource, quantite_actuelle, quantite_max, market_instance):
        """Vérifie si une ressource est presque pleine et la met en vente si besoin."""
        limite_alerte = 1000  # On vend quand on est à (max - 100)
        quantite_a_vendre = quantite_max - 1000  # Combien on met sur le marché d'un coup
        prix_de_vente = 10  # Ton prix unitaire

        if quantite_actuelle >= quantite_max - limite_alerte:
            print(f"\n⚠️ Alerte : {nom_ressource} presque plein ({quantite_actuelle}/{quantite_max}).")

            mes_offres = market_instance.get_my_offers()
            offre_existante = None
            if mes_offres:
                for offre in mes_offres:
                    if offre["resourceType"] == nom_ressource:
                        offre_existante = offre
                        break

            if offre_existante:
                nouvelle_quantite = offre_existante["quantityIn"] + quantite_a_vendre
                id_offre = offre_existante["id"]
                print(f"🔄 Mise à jour de l'offre existante. Nouvelle quantité totale : {nouvelle_quantite}")
                market_instance.update_offer(id_offre, nom_ressource, nouvelle_quantite, prix_de_vente)
            else:
                print(f"➕ Création d'une nouvelle offre sur le marché pour le {nom_ressource}.")
                market_instance.sell(nom_ressource, quantite_a_vendre, prix_de_vente)

        else:
            print(f"✅ {nom_ressource} OK ({quantite_actuelle}/{quantite_max}).")
    print("--- VÉRIFICATION DE LA CALE DU BATEAU ---")
    for nom, infos in inventaire.items():
        gerer_surplus(nom_ressource=nom,
                      quantite_actuelle=infos["actuel"],
                      quantite_max=infos["max"],
                      market_instance=market)

    print("-----------------------------------------")
    time.sleep(60)