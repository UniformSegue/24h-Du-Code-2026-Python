import requests

base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"

api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb2RpbmdnYW1lIiwic3ViIjoiMGEyNzcwODItYjZlNi00Y2E3LWJlMTItZGE4OGU1N2Q4NmI4Iiwicm9sZXMiOlsiVVNFUiJdfQ.9lmC6AZsJktL3F92Zm2dj8SEdAGfzeWk08g13hB4qRE"

headers = {
    "codinggame-id": api_key
}

print("==============")
print("SHOP : 1")
print("VENTE : 2")
print("EFFACER : 3")
print("MODIFIER : 4")
print("MES OFFRES : 5")
print("==============")

action = input("Action: ")


if action == "1":
    endpoint = f"{base_url}/marketplace/offers"
    response = requests.get(endpoint, headers=headers)

    data = response.json()
    counter = 0
    for item in data:
        print("===============",item["resourceType"],"=================")
        print("Owner : ",end="")
        print(item["owner"]["name"])
        print("Quantity : ",end="")
        print(item["quantityIn"])
        print("Price : ",end="")
        print(item["pricePerResource"])
        print("ID :", counter)
        counter += 1

    achat = int(input("Achat : "))
    print(data[achat])
    nombre = int(input("Nombres : "))

    endpoint = f"{base_url}/marketplace/purchases"
    headers = {
        "codinggame-id": api_key
    }
    buy={
        "quantity": nombre,
        "offerId": data[achat]["id"]
    }

    response = requests.post(endpoint, headers=headers,json = buy)

    if response.status_code == 200:
        print(response.json())
        print("Achat effectuer")
    else:
        print(response.json())

if action == "2":
    print("============")
    print("CHARBONIUM : 1")
    print("BOISIUM : 2")
    print("FERONIUM : 3")
    print("============")

    MATERIAL = {
        1: 'CHARBONIUM',  # Beige
        2: 'BOISIUM',  # Bleu    # Marron
        3: 'FERONIUM',  # Presque noir (vide)
    }

    action = int(input("Action: "))

    mat = MATERIAL.get(action, "None")

    quantity = int(input("Quantity : "))

    price = int(input("Price: "))

    body = {
        "resourceType": mat,
        "quantityIn": quantity,
        "pricePerResource": price
    }
    endpoint = f"{base_url}/marketplace/offers"
    response = requests.post(endpoint, headers=headers,json=body)


    data = response.json()

    print(response.json())

if action == "3":
    endpoint_list = f"{base_url}/marketplace/offers"
    response_list = requests.get(endpoint_list, headers=headers)

    if response_list.status_code == 200:
        toutes_les_offres = response_list.json()
        # On utilise .lower() pour éviter les erreurs de majuscules
        mes_offres = [o for o in toutes_les_offres if o.get("owner", {}).get("name", "").lower() == "gatitos"]

        if not mes_offres:
            print("\nAucune offre en ligne pour l'équipe 'gatitos'.")
        else:
            print(f"\n--- Vos offres en cours ({len(mes_offres)}) ---")
            for index, item in enumerate(mes_offres):
                print(
                    f"[{index}] {item['resourceType']} | Qté: {item['quantityIn']} | Prix: {item['pricePerResource']} | ID: {item['id']}")
            try:
                choix = int(input("\nEntrez le numéro de l'offre 'gatitos' à supprimer : "))
                if 0 <= choix < len(mes_offres):
                    id_offre = mes_offres[choix]["id"]

                    endpoint_delete = f"{base_url}/marketplace/offers/{id_offre}"
                    response_delete = requests.delete(endpoint_delete, headers=headers)

                    if response_delete.status_code == 204:
                        print(f"Succès : L'offre de {item['resourceType']} a été supprimée.")
                    else:
                        print(f"Erreur {response_delete.status_code} : Impossible de supprimer.")
                else:
                    print("Index invalide.")
            except ValueError:
                print("Veuillez entrer un nombre valide.")
    else:
        print("Erreur lors de la récupération des offres.")

if action == "4":
    endpoint_list = f"{base_url}/marketplace/offers"
    response_list = requests.get(endpoint_list, headers=headers)

    if response_list.status_code == 200:
        toutes_les_offres = response_list.json()
        mes_offres = [o for o in toutes_les_offres if o.get("owner", {}).get("name", "").lower() == "gatitos"]

        if not mes_offres:
            print("\nAucune offre 'gatitos' à modifier.")
        else:
            print("\n--- Vos offres modifiables ---")
            for index, item in enumerate(mes_offres):
                print(
                    f"[{index}] {item['resourceType']} | Qté actuelle: {item['quantityIn']} | Prix actuel: {item['pricePerResource']}")
            try:
                choix = int(input("\nNuméro de l'offre à modifier : "))
                if 0 <= choix < len(mes_offres):
                    offre_choisie = mes_offres[choix]
                    id_offre = offre_choisie["id"]
                    print(f"Modification de l'offre {id_offre} ({offre_choisie['resourceType']})")
                    nouvelle_qte = int(input(f"Nouvelle quantité (actuel {offre_choisie['quantityIn']}) : "))
                    nouveau_prix = float(input(f"Nouveau prix (actuel {offre_choisie['pricePerResource']}) : "))
                    body_update = {
                        "resourceType": offre_choisie["resourceType"],
                        "quantityIn": nouvelle_qte,
                        "pricePerResource": nouveau_prix
                    }
                    endpoint_patch = f"{base_url}/marketplace/offers/{id_offre}"
                    response_patch = requests.patch(endpoint_patch, headers=headers, json=body_update)

                    if response_patch.status_code == 200:
                        print("Succès : L'offre a été mise à jour !")
                        print(response_patch.json())
                    else:
                        print(f"Erreur {response_patch.status_code}")
                        print(response_patch.json())
                else:
                    print("Index invalide.")
            except ValueError:
                print("Entrée invalide. Veuillez saisir des nombres.")
    else:
        print("Erreur de connexion à l'API.")

if action == "5":
    print("\n--- Récupération de vos offres (Equipe: gatitos) ---")
    endpoint = f"{base_url}/marketplace/offers"
    response = requests.get(endpoint, headers=headers)

    if response.status_code == 200:
        toutes_les_offres = response.json()
        mes_offres = [o for o in toutes_les_offres if o.get("owner", {}).get("name", "").lower() == "gatitos"]

        if not mes_offres:
            print("Vous n'avez aucune offre en ligne actuellement.")
        else:
            print(f"Vous avez {len(mes_offres)} offre(s) active(s) :")
            print("-" * 50)
            for item in mes_offres:
                print(f"Ressource : {item['resourceType']}")
                print(f"Quantité  : {item['quantityIn']}")
                print(f"Prix Unit : {item['pricePerResource']}")
                print(f"ID        : {item['id']}")
                print("-" * 50)
    else:
        print(f"Erreur API ({response.status_code}) : Impossible de récupérer les offres.")

