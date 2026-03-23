import pika
import json
import ssl
HOST = "b-a5095b9b-3c4d-4fe7-8df1-8031e8808618.mq.eu-west-3.on.aws"
PORT = 5671
USER = "Gatitos"
PASS = "0a277082-b6e6-4ca7-be12-da88e57d86b8"
QUEUE_NAME = f"user.{PASS}"


def on_message_received(ch, method, properties, body):
    try:
        raw_data = body.decode()
        data = json.loads(raw_data)

        print("\n" + "=" * 50)
        print(f"📥 MESSAGE REÇU À : {json.dumps(data.get('type', 'SANS_TYPE'))}")
        print("-" * 50)
        print(json.dumps(data, indent=4))
        print("=" * 50)

    except Exception as e:
        print(f"❌ Erreur de décodage : {e}")
        print(f"Contenu brut : {body}")
print(f"📡 ÉCOUTE TOTALE LANCÉE sur la queue : {QUEUE_NAME}")
print("Fais une action en jeu (crée une offre, achète, etc.) et copie-colle le résultat ici.")

context = ssl.create_default_context()
cp = pika.ConnectionParameters(
    host=HOST,
    port=PORT,
    virtual_host='/',
    credentials=pika.PlainCredentials(USER, PASS),
    ssl_options=pika.SSLOptions(context)
)

try:
    connection = pika.BlockingConnection(cp)
    channel = connection.channel()
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message_received, auto_ack=True)
    channel.start_consuming()
except KeyboardInterrupt:
    print("\nArrêt de l'écoute.")
except Exception as e:
    print(f"💥 Erreur de connexion : {e}")