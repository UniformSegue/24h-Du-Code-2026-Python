import pika
import json
import ssl
import os
import requests
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb2RpbmdnYW1lIiwic3ViIjoiMGEyNzcwODItYjZlNi00Y2E3LWJlMTItZGE4OGU1N2Q4NmI4Iiwicm9sZXMiOlsiVVNFUiJdfQ.9lmC6AZsJktL3F92Zm2dj8SEdAGfzeWk08g13hB4qRE"  # Nécessaire pour le scan initial
HOST = "b-a5095b9b-3c4d-4fe7-8df1-8031e8808618.mq.eu-west-3.on.aws"
PORT = 5671
USER = "Gatitos"
PASS = "0a277082-b6e6-4ca7-be12-da88e57d86b8"
QUEUE_NAME = f"user.{PASS}"
JSON_FILE = "market_data.json"
def sync_initial_market():
    print("🔄 Synchronisation initiale du marché via l'API...")
    url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443/marketplace/offers"  # Vérifie l'URL exacte de ton épreuve
    headers = {"codinggame-id": API_KEY}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            offers_list = response.json()
            market_map = {
                off["id"]: {
                    "res": off["resourceType"],
                    "qty": off["quantityIn"],
                    "price": off["pricePerResource"],
                    "owner": off.get("playerName") or "Anonyme"
                } for off in offers_list
            }
            save_json(market_map)
            print(f"✅ {len(market_map)} offres récupérées. Le JSON est prêt.")
        else:
            print(f"⚠️ Erreur API ({response.status_code}): Impossible de pré-remplir le JSON.")
    except Exception as e:
        print(f"❌ Erreur lors du scan initial : {e}")


def save_json(data):
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_json():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}
def on_message_received(ch, method, properties, body):
    try:
        data = json.loads(body)
        event_type = data.get("type")
        msg_content = data.get("message", {})
        market = load_json()
        if event_type == "OFFRE":
            offer_id = msg_content.get("id")

            proprio = msg_content.get("owner")

            market[offer_id] = {
                "res": msg_content.get("resourceType"),
                "qty": msg_content.get("quantityIn"),
                "price": msg_content.get("pricePerResource"),
                "owner": proprio
            }

            print(f"✨ [AJOUT BROKER] {msg_content.get('resourceType')} par {proprio}")
            save_json(market)


        elif event_type == "ACHAT":

            offer_id = msg_content.get("offerId")
            if offer_id in market:
                del market[offer_id]
                print(f"💰 [ACHAT BROKER] L'offre {offer_id[:8]} a été retirée.")
                save_json(market)

    except Exception as e:
        print(f"❌ Erreur Broker : {e}")
if __name__ == "__main__":
    sync_initial_market()
    print(f"📡 Connexion au Broker pour les mises à jour en direct...")
    context = ssl.create_default_context()
    cp = pika.ConnectionParameters(
        host=HOST, port=PORT, virtual_host='/',
        credentials=pika.PlainCredentials(USER, PASS),
        ssl_options=pika.SSLOptions(context)
    )

    try:
        connection = pika.BlockingConnection(cp)
        channel = connection.channel()
        channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message_received, auto_ack=True)
        channel.start_consuming()
    except Exception as e:
        print(f"💥 Erreur de connexion Broker : {e}")