import pygame
import os

for file in os.listdir('.'):
    if file.endswith('.jpg') or file.endswith('.png'):
        img = pygame.image.load(file)
        if img.get_width() != 36 or img.get_height() != 36:
            img = pygame.transform.smoothscale(img, (36, 36))
            pygame.image.save(img, file)
