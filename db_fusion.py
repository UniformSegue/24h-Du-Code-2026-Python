import sqlite3
import os
DB1_NAME = "world_1.db"  # Ta première base de données
DB2_NAME = "world_2.db"  # Ta deuxième base de données
MERGED_DB_NAME = "world.db"  # Le nom de la nouvelle base de données fusionnée


def setup_merged_db(db_name):
    """Crée la structure de la nouvelle base de données (tiles ET player)."""
    if os.path.exists(db_name):
        os.remove(db_name)

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

    conn.commit()
    return conn


def fetch_table_data(db_name, table_name):
    """Récupère toutes les lignes d'une table spécifique dans une base de données."""
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.OperationalError:
        print(f"❌ Erreur : Impossible de lire la table '{table_name}' dans '{db_name}'.")
        return []


def main():
    print(f"🔍 Lecture de {DB1_NAME}...")
    tiles_db1 = fetch_table_data(DB1_NAME, "tiles")
    player_db1 = fetch_table_data(DB1_NAME, "player")

    print(f"🔍 Lecture de {DB2_NAME}...")
    tiles_db2 = fetch_table_data(DB2_NAME, "tiles")
    player_db2 = fetch_table_data(DB2_NAME, "player")

    print(f"\n⚙️ Création de la nouvelle base de données : {MERGED_DB_NAME}...")
    conn_merged = setup_merged_db(MERGED_DB_NAME)
    cursor_merged = conn_merged.cursor()
    sql_insert_tiles = '''
        INSERT OR IGNORE INTO tiles (id, x, y, type, zone, island_name, island_id, island_quotient)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    cursor_merged.executemany(sql_insert_tiles, tiles_db1)
    cursor_merged.executemany(sql_insert_tiles, tiles_db2)
    sql_insert_player = '''
        INSERT OR REPLACE INTO player (id, x, y, energy, money, feronium, boisium, charbonium)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''
    if player_db1:
        cursor_merged.executemany(sql_insert_player, player_db1)
    if player_db2:
        cursor_merged.executemany(sql_insert_player, player_db2)

    conn_merged.commit()
    cursor_merged.execute("SELECT COUNT(*) FROM tiles")
    total_uniques = cursor_merged.fetchone()[0]

    cursor_merged.execute("SELECT x, y, energy FROM player WHERE id = 1")
    final_player = cursor_merged.fetchone()

    print("\n✅ FUSION TERMINÉE AVEC SUCCÈS !")
    print(f"🗺️  Carte   : La nouvelle base contient {total_uniques} tuiles uniques.")
    print(f"🗑️  Doublons évités : {(len(tiles_db1) + len(tiles_db2)) - total_uniques}")

    if final_player:
        print(
            f"🧍 Joueur : Sauvegardé en position ({final_player[0]}, {final_player[1]}) avec {final_player[2]} d'énergie.")

    conn_merged.close()


if __name__ == "__main__":
    main()