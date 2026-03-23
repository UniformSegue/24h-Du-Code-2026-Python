def get_relative_coords(player_x, player_y, target_x, target_y):
    """
    Convertit des coordonnées absolues en coordonnées relatives
    centrées sur le joueur (0, 0).
    """
    rel_x = target_x - player_x
    rel_y = target_y - player_y
    return rel_x, rel_y