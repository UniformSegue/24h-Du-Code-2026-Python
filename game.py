import pygame
import sqlite3
import sys
import os
import time

from api import ApiJoin
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
TILE_SIZE = 40
DB_NAME = "world.db"

COLORS = {
    'SAND': (240, 190, 0),
    'SEA': (0, 0, 255),
    'VOID': (20, 20, 20),
}
PLAYER_COLOR = (255, 50, 50)
VISITED_COLOR = (50, 200, 50)  # Un beau vert pour les îles visitées
BG_COLOR = (15, 15, 15)
GRID_COLOR = (40, 40, 40)
def fetch_data():
    """Récupère les tuiles (avec le nom de l'île) et la position du joueur."""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT x, y, type, island_name FROM tiles")
        tiles = cursor.fetchall()

        cursor.execute("SELECT x, y FROM player WHERE id = 1")
        player_pos = cursor.fetchone()

        conn.close()
        return tiles, player_pos
    except sqlite3.Error as e:
        print(f"⚠️ En attente de la base de données... ({e})")
        return [], None


def fetch_api_details_cache(api_instance):
    """
    Interroge l'API UNE SEULE FOIS pour récupérer la liste de TOUTES
    les îles visitées et les renvoie sous forme d'ensemble (set).
    """
    print("📡 Récupération de l'état des îles depuis le serveur...")
    visited = set()
    data = api_instance.connect_get("/players/details")

    if data and isinstance(data, dict):
        islands_list = data.get("discoveredIslands", [])
        print(islands_list)
        for island in islands_list:
            if island["islandState"] == "KNOWN":
                visited.add(island["island"]["name"])
        available_moves = data.get("availableMove", 0)
    return visited, available_moves


def map_to_screen_coords(tile_x, tile_y, player_x, player_y, screen_center_x, screen_center_y):
    rel_x = tile_x - player_x
    rel_y = tile_y - player_y
    pixel_x = rel_x * TILE_SIZE
    pixel_y = rel_y * TILE_SIZE
    return pixel_x + screen_center_x - (TILE_SIZE // 2), pixel_y + screen_center_y - (TILE_SIZE // 2)
def main(api_instance):
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"Radar du Bateau - Temps Réel")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    ctx, cty = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    print("📡 Récupération de la vitesse du bateau...")
    move_cooldown = 0.8  # Valeur par défaut de 1 seconde au cas où l'API échoue
    data = api_instance.connect_get("/players/details")

    if data and isinstance(data, dict):
        level_info = data.get("level", {})
        vitesse = level_info.get("speed")  # ⚠️ Modifie "speed" si le nom est différent dans l'OAS
        if vitesse:
            # Si c'est un délai en secondes, garde : vitesse
            move_cooldown = float(vitesse)
            print(f"🚤 Vitesse trouvée ! Délai entre chaque mouvement : {move_cooldown} secondes.")

    last_move_time = 0  # Enregistre l'heure du dernier mouvement
    last_modified_time = 0
    cached_tiles = []
    cached_player_pos = (0, 0)

    visited_islands, available_moves = fetch_api_details_cache(api_instance)
    running = True
    while running:
        current_time = time.time()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                temps_ecoule = current_time - last_move_time

                if temps_ecoule >= move_cooldown:
                    if event.key == pygame.K_UP:
                        print("⬆️ Envoi de l'ordre : NORD")
                        data = api_instance.move("N")
                        print(data)
                        last_move_time = time.time()  # On reset le timer

                    elif event.key == pygame.K_DOWN:
                        print("⬇️ Envoi de l'ordre : SUD")
                        data = api_instance.move("S")
                        print(data)
                        last_move_time = time.time()

                    elif event.key == pygame.K_RIGHT:
                        print("➡️ Envoi de l'ordre : EST")
                        data = api_instance.move("E")
                        print(data)
                        last_move_time = time.time()

                    elif event.key == pygame.K_LEFT:
                        print("⬅️ Envoi de l'ordre : OUEST")
                        data = api_instance.move("W")
                        print(data)
                        last_move_time = time.time()
                else:
                    temps_restant = move_cooldown - temps_ecoule
                    print(f"⏳ Bateau en rechargement ! Attends encore {temps_restant:.1f} secondes.")
        if os.path.exists(DB_NAME):
            current_modified_time = os.path.getmtime(DB_NAME)
            if current_modified_time > last_modified_time:
                cached_tiles, new_player_pos = fetch_data()
                if new_player_pos:
                    cached_player_pos = new_player_pos
                visited_islands, available_moves = fetch_api_details_cache(api_instance)
                last_modified_time = current_modified_time
                print("🔄 Base de données actualisée, mise à jour de l'affichage !")

        px, py = cached_player_pos
        screen.fill(BG_COLOR)
        for tx, ty, ttype, island_name in cached_tiles:
            screen_x, screen_y = map_to_screen_coords(tx, ty, px, py, ctx, cty)
            tile_rect = pygame.Rect(screen_x, screen_y, TILE_SIZE, TILE_SIZE)
            if screen.get_rect().colliderect(tile_rect):
                # NOUVEAU : Logique de couleur !
                if island_name in visited_islands:
                    color = VISITED_COLOR
                else:
                    color = COLORS.get(ttype, (255, 0, 255))

                pygame.draw.rect(screen, color, tile_rect)
                pygame.draw.rect(screen, GRID_COLOR, tile_rect, 1)
        player_rect = pygame.Rect(ctx - (TILE_SIZE // 4), cty - (TILE_SIZE // 4), TILE_SIZE // 2, TILE_SIZE // 2)
        pygame.draw.rect(screen, PLAYER_COLOR, player_rect)
        temps_ecoule = time.time() - last_move_time
        if temps_ecoule >= move_cooldown:
            status_text = "🟢 PRÊT À NAVIGUER"
            status_color = (50, 255, 50)
        else:
            status_text = f"🔴 COOLDOWN : {move_cooldown - temps_ecoule:.1f}s"
            status_color = (255, 50, 50)
        info_text = font.render(f"Pos: ({px}, {py}) | Tuiles: {len(cached_tiles)} | Iles: {len(visited_islands)}", True,
                                (255, 255, 255))
        screen.blit(info_text, (10, 10))

        cooldown_surface = font.render(status_text, True, status_color)
        screen.blit(cooldown_surface, (10, 35))
        if available_moves > 0:
            energy_text = f"⚡ Énergie : {available_moves} déplacements restants"
            energy_color = (255, 215, 0)  # Doré
        else:
            energy_text = "⚡ ÉNERGIE VIDE !"
            energy_color = (255, 50, 50)  # Rouge alerte

        energy_surface = font.render(energy_text, True, energy_color)
        screen.blit(energy_surface, (10, 60))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()



mon_api = ApiJoin("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjb2RpbmdnYW1lIiwic3ViIjoiMGEyNzcwODItYjZlNi00Y2E3LWJlMTItZGE4OGU1N2Q4NmI4Iiwicm9sZXMiOlsiVVNFUiJdfQ.9lmC6AZsJktL3F92Zm2dj8SEdAGfzeWk08g13hB4qRE")
main(mon_api)