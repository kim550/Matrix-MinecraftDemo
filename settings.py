import math

class Settings:
    ticks_per_sec = 60
    sector_size = 16
    walking_speed = 5.0
    flying_speed = 15.0
    gravity = 20.0
    max_jump_height = 1.1
    jump_speed = math.sqrt(2 * gravity * max_jump_height)
    player_height = 2
    tree_seed = 100
    texture_path = 'images/textures/'
    image_path = 'images/images/'
    record_path = 'records/'
    gamemode = 1
    faces = [
        ( 0, 1, 0),
        ( 0,-1, 0),
        (-1, 0, 0),
        ( 1, 0, 0),
        ( 0, 0, 1),
        ( 0, 0,-1),
    ]
    window = None
    images = {}
