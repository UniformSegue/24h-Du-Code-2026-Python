import sqlite3

import requests as re

class ApiJoin:

    def __init__(self,apiKey):

        self.apiKey = apiKey

    def connect_get(self,endpoint):
        base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"

        api_key = self.apiKey

        endpoint = f"{base_url}{endpoint}"
        headers = {
            "codinggame-id": api_key
        }

        try:

            response = re.get(endpoint, headers=headers)

            if response.status_code == 200:

                data = response.json()
                return data

            elif response.status_code == 400:
                data = response.json()
                if data["codeError"] == "SHIP_IN_DISTRESS":
                    print("Bateau immobilisé par un événement (inconnu)")
                    return "Error"
            else:
                print(f"❌ Erreur {response.status_code} : Le serveur a refusé la requête.")
                print("Détails :", response.text)

        except re.exceptions.RequestException as e:
            print(f"❌ Impossible de se connecter au serveur : {e}")


    def connect_post(self,endpoint, body):
        base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"

        api_key = self.apiKey

        endpoint = f"{base_url}{endpoint}"

        headers = {
            "codinggame-id": api_key
        }

        try:

            response = re.post(endpoint, headers=headers, json=body)

            if response.status_code == 200:

                data = response.json()
                return data

            elif response.status_code == 400:
                data = response.json()

                if data["codeError"] == "FORBIDDEN":
                    return "Votre bateau ne peut pas encore accéder à la zone 2, faites-le évoluer au niveau 2 pour pouvoir y accéder."
                if data["codeError"] == "SHIP_IN_DISTRESS":
                    print("Bateau immobilisé par un événement (inconnu)")
                    return "Error"
            else:
                print(f"❌ Erreur {response.status_code} : Le serveur a refusé la requête.")
                print("Détails :", response.text)

        except re.exceptions.RequestException as e:
            print(f"❌ Impossible de se connecter au serveur : {e}")


    def connect_put(self,endpoint, body):
        base_url = "http://ec2-15-237-116-133.eu-west-3.compute.amazonaws.com:8443"
        api_key = self.apiKey
        endpoint = f"{base_url}{endpoint}"

        headers = {
            "codinggame-id": api_key
        }

        try:
            response = re.put(endpoint, headers=headers, json=body)
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                print(f"❌ Erreur {response.status_code} : Le serveur a refusé la requête.")
                print("Détails :", response.text)

        except re.exceptions.RequestException as e:
            print(f"❌ Impossible de se connecter au serveur : {e}")

    def init_db(self,db_name="map_3026.db"):
        """Crée la table 'tiles' avec les nouvelles colonnes pour les îles."""
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tiles (
                id TEXT PRIMARY KEY,
                x INTEGER,
                y INTEGER,
                type TEXT,
                zone INTEGER,
                island_name TEXT,
                island_id TEXT,
                island_quotient INTEGER
            )
        ''')
        conn.commit()
        print("✅ Base de données initialisée (avec island_name, island_id et island_quotient).")
        return conn

    def save_discovered_cells(self,conn, cells_list):

        cursor = conn.cursor()

        sql_query = '''
            INSERT OR REPLACE INTO tiles (id, x, y, type, zone, island_name, island_id, island_quotient)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''
        count = 0
        islands_found = 0

        for cell in cells_list:
            island_info = cell.get('island')

            island_name = None
            island_id = None
            island_quotient = None

            if island_info and isinstance(island_info, dict):
                islands_found += 1
                island_name = island_info.get('name')
                island_id = island_info.get('id')  # Au cas où l'API le renvoie en cachette
                island_quotient = island_info.get('bonusQuotient')  # Nom exact dans l'OAS


            cursor.execute(sql_query, (
                cell.get('id'),
                cell.get('x'),
                cell.get('y'),
                cell.get('type'),
                cell.get('zone', 0),
                island_name,
                island_id,
                island_quotient
            ))
            count += 1

        conn.commit()

    def init_player_table(self,conn):
        """Crée la table 'player' et insère une ligne par défaut."""
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY,
                x INTEGER,
                y INTEGER,
                energy INTEGER,
                money INTEGER,
                feronium INTEGER,
                boisium INTEGER,
                charbonium INTEGER
            )
        ''')
        cursor.execute('''
            INSERT OR IGNORE INTO player (id, x, y, energy, money, feronium, boisium, charbonium)
            VALUES (1, 0, 0, 0, 0, 0, 0, 0)
        ''')

        conn.commit()
        print("✅ Table 'player' initialisée.")

    def update_player_info(self,conn, x=None, y=None, energy=None, money=None, feronium=None, boisium=None, charbonium=None):
        """
        Met à jour UNIQUEMENT les informations fournies.
        Exemple: update_player_info(conn, energy=15, x=2) ne modifiera pas l'argent ni les ressources.
        """
        cursor = conn.cursor()

        colonnes_a_modifier = []
        valeurs = []
        if x is not None:
            colonnes_a_modifier.append("x = ?")
            valeurs.append(x)
        if y is not None:
            colonnes_a_modifier.append("y = ?")
            valeurs.append(y)
        if energy is not None:
            colonnes_a_modifier.append("energy = ?")
            valeurs.append(energy)
        if money is not None:
            colonnes_a_modifier.append("money = ?")
            valeurs.append(money)
        if feronium is not None:
            colonnes_a_modifier.append("feronium = ?")
            valeurs.append(feronium)
        if boisium is not None:
            colonnes_a_modifier.append("boisium = ?")
            valeurs.append(boisium)
        if charbonium is not None:
            colonnes_a_modifier.append("charbonium = ?")
            valeurs.append(charbonium)
        if not colonnes_a_modifier:
            return
        requete_sql = f"UPDATE player SET {', '.join(colonnes_a_modifier)} WHERE id = 1"

        cursor.execute(requete_sql, tuple(valeurs))
        conn.commit()
        print("🔄 Statut du joueur mis à jour dans la base !")

    def get_player_info(self,conn):
        """Récupère toutes les informations actuelles du joueur."""
        cursor = conn.cursor()
        cursor.execute("SELECT x, y, energy, money, feronium, boisium, charbonium FROM player WHERE id = 1")
        row = cursor.fetchone()

        if row:
            return {
                "x": row[0], "y": row[1], "energy": row[2],
                "money": row[3], "feronium": row[4],
                "boisium": row[5], "charbonium": row[6]
            }
        return None

    def move(self, direction):
        assert direction in ["N", "S", "E", "W"], """la direction dois etre "N", "S", "E", "W" """
        body = {
            "direction": direction
        }

        data = api.connect_post("/ship/move", body)
        if not data or data == "Error":
            print("❌ Déplacement annulé : impossible de lire les données.")
            print(data)
            return
        if not isinstance(data, dict):
            print(data)
            return

        db_connection = self.init_db("world.db")
        self.save_discovered_cells(db_connection, data["discoveredCells"])
        db_connection.close()

        db_conn = sqlite3.connect("world.db")
        self.init_player_table(db_conn)
        self.update_player_info(db_conn,x=data["position"]["x"],y=data["position"]["y"],energy=data["energy"])
        db_conn.close()
        print(data["position"]["x"])
        print(data["position"]["y"])

    def resources(self):
        data = api.connect_get("/players/details")

        dico = {data['resources'][0]['type']: data['resources'][0]['quantity'],
                data['resources'][1]['type']: data['resources'][1]['quantity'],
                data['resources'][2]['type']: data['resources'][2]['quantity']}

        db_conn = sqlite3.connect("world.db")
        self.init_player_table(db_conn)
        self.update_player_info(db_conn,feronium=dico["FERONIUM"],boisium=dico["BOISIUM"],charbonium=dico["CHARBONIUM"])
        db_conn.close()
        return dico

    def get_sand_blocks(self):
        conn = sqlite3.connect('world.db')
        cursor = conn.cursor()
        requete_sql = "SELECT * FROM tiles WHERE type = 'SAND';"

        try:
            cursor.execute(requete_sql)
            sand_blocks = cursor.fetchall()
            if sand_blocks:
                print(f"{len(sand_blocks)} blocs de sable trouvés :")
                liste_block = []
                for block in sand_blocks:
                    liste_block.append(((block[1], block[2]), block[5]))
                return liste_block

            else:
                print("Aucun bloc de sable n'a été trouvé dans la base de données.")

        except sqlite3.Error as e:
            print(f"Une erreur SQL est survenue : {e}")

        finally:
            conn.close()

    def get_player_position(self):
        """
        Cherche dans la table 'player' et renvoie la position sous forme de tuple (x, y).
        """
        try:
            conn = sqlite3.connect("world.db")
            cursor = conn.cursor()

            cursor.execute("SELECT x, y FROM player WHERE id = 1")
            result = cursor.fetchone()

            conn.close()

            if result:

                return (result[0], result[1])
            else:
                print("⚠️ Aucun joueur trouvé avec l'id 1 dans la base de données.")
                return None

        except sqlite3.Error as e:
            print(f"❌ Une erreur SQL est survenue : {e}")
            return None

    def is_island_visited(self, island_name):

        data = self.connect_get("/players/details")

        if not data or data == "Error":
            print("❌ Impossible de récupérer les détails du joueur.")
            return False

        islands_list = data.get("islands", [])
        for island in islands_list:
            if island.get("name") == island_name:

                etat_ile = island.get("state")

                if etat_ile == "KNOW" or etat_ile == "EXPLORED":
                    return True
                else:
                    return False

        return False

    def get_ship_speed(self):
        """
        Récupère la vitesse actuelle du bateau depuis l'endpoint /players/details.
        """
        data = self.connect_get("/players/details")

        if not data or data == "Error":
            print("❌ Impossible de récupérer les détails du joueur.")
            return None

        level_info = data.get("level", {})

        vitesse = level_info.get("speed")

        if vitesse is not None:
            print(f"🚤 La vitesse de ton bateau est actuellement de : {vitesse}")
            return vitesse
        else:
            print("❓ La clé de la vitesse est introuvable dans les données reçues.")
            print("Voici ce que contient 'level' :", level_info)
            return None



api = ApiJoin("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb2RpbmdnYW1lIiwic3ViIjoiMGEyNzcwODItYjZlNi00Y2E3LWJlMTItZGE4OGU1N2Q4NmI4Iiwicm9sZXMiOlsiVVNFUiJdfQ.9lmC6AZsJktL3F92Zm2dj8SEdAGfzeWk08g13hB4qRE")

print(api.move("N"))

