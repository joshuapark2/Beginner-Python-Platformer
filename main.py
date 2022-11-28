import os
import random
import math
import pygame
from os import listdir
from os.path import isfile, join #os stuff is dynamically exporting the file assets
pygame.init()

pygame.display.set_caption("Platformer") #display window top left name of game

#Global Variables
WIDTH, HEIGHT = 1000, 800 # Width and Height of screen
FPS = 60
PLAYER_VEL = 5 #player speed

window = pygame.display.set_mode((WIDTH, HEIGHT)) # display screen of game

def flip(sprites):
    # True = flip x direction, False = don't flip in y direction
    return [pygame.transform.flip(sprite, True, False) for sprite in sprites]

# Load all different sprite sheets for character - jumping, hitting, etc.
# dir1 and dir2 allows us to load other images that aren't characters - makes it dynamic
# If we want to load multiple direction
def load_sprite_sheets(dir1, dir2, width, height, direction=False):
    # We can use join because os.path
    path = join("assets", dir1, dir2)
    # We also imported listdir up top in order to use this function
    # For loop in a list - load every single file that is inside of a directory
    images = [f for f in listdir(path) if isfile(join(path, f))]

    # Dictionary used - keys = animation style, values = images in that animation
    all_sprites = {}

    #convert_alpha() allows us to convert/get a transparent image - allows us to actually use transparent feature of images
    # First we load an image and append the path, then get transparent background
    for image in images:
        sprite_sheet = pygame.image.load(join(path, image)).convert_alpha()
        # Next we want the sprites in that images
        sprites = []
        # width is our width of individual image inside of our spritesheet - 32 pixel is width or wide
        for i in range(sprite_sheet.get_width() // width):
            #SRCALPHA allows us to load transparent images, 32 is depth to load images
            surface = pygame.Surface((width, height), pygame.SRCALPHA, 32)
            #Next create a rectangle that will tell us where in this image (sprite_sheet) which we want to take and individual image from and blit it onto the surface
            # Create a surface of individual frame, draw it onto the surface and the export it.
            rect = pygame.Rect(i * width, 0, width, height) # Draw from spritesheet location we want
            surface.blit(sprite_sheet, (0, 0), rect) #blit means draw -> Source, destination, area we want to draw
            sprites.append(pygame.transform.scale2x(surface)) # make our sprites 2x bigger 32x32 -> 64x64 now

        # If we want multi-directional animation, we need to have 2 keys to direction for every one of our animation
            # need right and left side -> strip off .png -> append _right or _left
                #_right is basic sprites and _left is opposite using flip()
        if direction:
            all_sprites[image.replace(".png", "") + "_right"] = sprites
            all_sprites[image.replace(".png", "") + "_left"] = flip(sprites)
        else:
            all_sprites[image.replace(".png", "")] = sprites
        
    return all_sprites

def get_block(size):
    # We are trying to get the specific sprite sheet in our directory and we have one called Terrain.png
    path = join("assets", "Terrain", "Terrain.png")
    image = pygame.image.load(path).convert_alpha() #convert_alpha gives us transparency
    surface = pygame.Surface((size, size), pygame.SRCALPHA, 32)
    # In the sprite sheet, we go 96 pixels in order to get the grass block
        # Column 96 and Row 0
    rect = pygame.Rect(96, 0, size, size)
    surface.blit(image, (0,0), rect) # we want to blit just the rect size
    return pygame.transform.scale2x(surface)

#! Most Complicated part is the player -> Get sprite and animation at the end
class Player(pygame.sprite.Sprite):
    # sprites allows us to do pixel perfect objects - we can use a method if sprites are colliding with each other
    COLOR = (255, 0, 0)
    GRAVITY = 1
    # Pass in MainCharacters directory in first directory under assets, then we want MaskDude specifically
        # height and width of our sprites will be 32, 32
        # Pass true because we want multi-directional sprites
    SPRITES = load_sprite_sheets("MainCharacters", "MaskDude", 32, 32, True)
    ANIMATION_DELAY = 3 # This variable shows us how fast we want to change swap between sprites 

    # width and height is image of player
    def __init__(self, x, y, width, height):
        super().__init__()
        self.rect = pygame.Rect(x, y, width, height)
        # How fast our player is going with x_vel and y_vel -> Great for gravity or jumping
        self.x_vel = 0
        self.y_vel = 0
        self.mask = None
        self.direction = "left" # We need to keep track of direction our player is facing
        self.animation_count = 0 #reset count every time we change direction and reset animation
        self.fall_count = 0 # gravity variable
        self.jump_count = 0
        self.hit = False
        self.hit_count = 0

    def jump(self):
        self.y_vel = -self.GRAVITY * 8 # negative so that we jump up in the air
        self.animation_count = 0
        self.jump_count += 1
        # If we are double jumping
        if self.jump_count == 1:
            self.fall_count = 0 # reset gravity after we jump the first time

    def move(self, dx, dy):
        # Moving left/right and up/down with positive and negative values
        # Remember that pixels start at 0,0 at top left
        self.rect.x += dx
        self.rect.y += dy

    def make_hit(self):
        self.hit = True
        self.hit_count = 0
    
    def move_left(self, vel):
        self.x_vel = -vel
        if self.direction != "left":
            self.direction = "left"
            self.animation_count = 0
        
    def move_right(self, vel):
        self.x_vel = vel
        if self.direction != "right":
            self.direction = "right"
            self.animation_count = 0
    
    # Loop will be called once every frame and it will move character in correct direction and handle animation
    def loop(self, fps):
        # if fall_count == 60, then we've been falling for 1 second as an example
        # Multiply by gravity to tell us how much to increment our velocity by - we are moving at least 1 pixel down with the min(1,__) part
        self.y_vel += min(1, (self.fall_count / fps) * self.GRAVITY)
        self.move(self.x_vel, self.y_vel)

        if self.hit:
            self.hit_count += 1
        if self.hit_count > fps * 2: #2 seconds
            self.hit = False
            self.hit_count = 0

        self.fall_count += 1
        self.update_sprite() # this will show animation

    # If we landed, we need to reset our fall counter
    def landed(self):
        self.fall_count = 0 # Stop adding gravity
        self.y_vel = 0 # stop moving us down
        self.jump_count = 0
    
    def hit_head(self):
        self.count = 0
        self.y_vel *= -1 # bounce off the block and go downwards when we hit our head

    def update_sprite(self):
        sprite_sheet = "idle" # default if we aren't being attacked or anything
        if self.hit: #important to put this at top
            sprite_sheet = "hit"
        if self.y_vel <= 0:
            if self.jump_count == 1:
                sprite_sheet = "jump"
            elif self.jump_count == 2:
                sprite_sheet = "double_jump"
        # Must have significant amount of gravity before doing fall state - self.GRAVITY * 2 is important to avoid glitch of falling when on ground
        elif self.y_vel > self.GRAVITY * 2:
            sprite_sheet = "fall"
        elif self.x_vel != 0:
            sprite_sheet = "run"
        
        sprite_sheet_name = sprite_sheet + "_" + self.direction
        sprites = self.SPRITES[sprite_sheet_name]
        # We have an animation delay of 5 frames - every 5 frames we show a different sprite
            # divide by 5 and mod by len of sprites -> Once we are on count 10, we should second sprite
            # This works for every sprites and we made it dynamic
        sprite_index = (self.animation_count // self.ANIMATION_DELAY) % len(sprites)
        self.sprite = sprites[sprite_index]
        self.animation_count += 1
        self.update()

    # Mask Function
    def update(self):
        # update the rectangle that bounds our character based on the sprite we are showing
            # Some are taller, some are pushed to left or pushed to right
            # We want consistency between sprites and rectangle
        # Depending on sprite image we have - constantly adjust rectangle (width and height)
            # keep same x and y
        self.rect = self.sprite.get_rect(topleft=(self.rect.x, self.rect.y))
        # mask is a mapping of all pixels that exists in the sprite
            # when we draw anything on screen, its a rectangle - the mask allows us to show where there are pixels
            # Allows us to perform pixel perfect hit boxes -> Collision on pixels rather than rectangles!!!
            # We must call mask because the sprite we inherited from uses the rectangle and uses the mask property when using collision
        self.mask = pygame.mask.from_surface(self.sprite)

    # win is considered window
    def draw(self, win, offset_x):
        # pygame.draw.rect(win, self.COLOR, self.rect) <- this draws a rectangle
        # Line below - "idle" is a name of our animation - accessing key, and accessing first frame which is 0
        # self.sprite = self.SPRITES["idle_" + self.direction][0] <- removed this line of code due to update_sprite function
        win.blit(self.sprite, (self.rect.x - offset_x, self.rect.y)) # Draw updated sprite on screen

#! Base class for all our objects
# This class is what we need for any valid sprites
class Object(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, name=None):
        super().__init__ # This initializes the super class
        self.rect = pygame.Rect(x, y, width, height)
        self.image = pygame.Surface((width, height), pygame.SRCALPHA) #supports transparent images
        self.width = width
        self.height = height
        self.name = name
    
    def draw(self, win, offset_x):
        win.blit(self.image, (self.rect.x - offset_x, self.rect.y))

#! Using Inheritances from Object
# Have a block class that inherits from object
class Block(Object):
    def __init__(self, x, y, size):
        super().__init__(x, y, size, size) # size is same for the width and height
        block = get_block(size)
        self.image.blit(block, (0,0)) # Blit block at 0,0
        self.mask = pygame.mask.from_surface(self.image)

class Fire(Object):
    ANIMATION_DELAY = 3

    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height, "fire") # Notice how we don't need self in the parameter
        self.fire = load_sprite_sheets("Traps", "Fire", width, height) #fire represents our fire sprite sheet
        self.image = self.fire["off"][0]
        self.mask = pygame.mask.from_surface(self.image)
        self.animation_count = 0
        self.animation_name = "off"

    def on(self):
        self.animation_name = "on"

    def off(self):
        self.animation_name = "off"
    
    def loop(self):
        sprites = self.fire[self.animation_name]
        sprite_index = (self.animation_count // 
                        self.ANIMATION_DELAY) % len(sprites)
        self.image = sprites[sprite_index]
        self.animation_count += 1

        self.rect = self.image.get_rect(topleft=(self.rect.x, self.rect.y))
        self.mask = pygame.mask.from_surface(self.image)

        if self.animation_count // self.ANIMATION_DELAY > len(sprites): # Animation count doesn't get too large
            self.animation_count = 0 # Since fire is static and sitting forever, we can get to an extremely large number that can lag our program

# 64x64 or 32x32 - we want to tile the entire background - want a grid based on our screen
    # This function will return a list of background tile we need to draw
    # Name is color of background
def get_background(name):
    #First we want to load the bg image - when running the file -> Run from directory that file exists in
    image = pygame.image.load(join("assets", "Background", name)) #this load image and join asset path
    _, _, width, height = image.get_rect() #_ _ are values we don't care about with width and height
    tiles = [] # empty list of tile

    # integer divide by width of tiles - tells us how many tiles we need on x and y direction - add 1 for no gaps
    for i in range(WIDTH // width + 1):
        for j in range(HEIGHT // height + 1):
            # pos is a tuple
            pos = (i * width, j * height) #position of top left of current tile to list - drawing in pygame draw from top left
            tiles.append(pos)

    return tiles, image

def draw(window, background, bg_image, player, objects, offset_x):
    # Loop through every tile that we have, draw background at position which is tile.
    for tile in background:
        window.blit(bg_image, tile)

    for obj in objects:
        obj.draw(window, offset_x)

    player.draw(window, offset_x)

    # Update - every frame we clear frame and draw
    pygame.display.update()

def handle_vertical_collision(player, objects, dy):
    collided_objects = []
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            # If we are moving down of the screen (hitting top of object)
            # make the bottom of our rectangle to the top of our object - Making us touch the floor
            if dy > 0:
                player.rect.bottom = obj.rect.top
                player.landed()
            elif dy < 0: # This is needed to make sure we collided the top but not go through it
                player.rect.top = obj.rect.bottom
                player.hit_head()
            
            collided_objects.append(obj)
    return collided_objects # return statement to know what exactly we are hitting

def collide(player, objects, dx):
    player.move(dx, 0) # Want to check if player moved to left or right, would they hit a block?
    player.update() # Need to update rectangle and mask before checking collision
    collided_object = None
    for obj in objects:
        if pygame.sprite.collide_mask(player, obj):
            collided_object = obj
            break
    
    player.move(-dx, 0) # move them back to original place
    player.update() # update our mask
    return collided_object


def handle_move(player, objects):
    keys = pygame.key.get_pressed()

    # player.x_vel is incredibly important in order to move only when we hold down the key
    player.x_vel = 0
    collide_left = collide(player, objects, -PLAYER_VEL * 2) # multiple by 2 because sprites shift to left or right when switching
    collide_right = collide(player, objects, PLAYER_VEL * 2)
    # Having if keys here is if we are holding down the key
    if keys[pygame.K_LEFT] and not collide_left:
        player.move_left(PLAYER_VEL)
    if keys[pygame.K_RIGHT] and not collide_right:
        player.move_right(PLAYER_VEL)
    
    vertical_collide = handle_vertical_collision(player, objects, player.y_vel)
    to_check = [collide_left, collide_right, *vertical_collide]
    for obj in to_check:
        if obj and obj.name == "fire": # if any object is collided with fire, then return hit
            player.make_hit()

# Run to start game - where event loop goes (collision, redrawing window, etc.)
def main(window):
    clock = pygame.time.Clock()
    background, bg_image = get_background("Blue.png")

    block_size = 96

    player = Player(100, 100, 50, 50)
    # Taking i and multiply by block_size to give x coordinate we want blocks to be at, HEIGHT - blocksize is bottom of screen, block_size we want as the same
    fire = Fire(100, HEIGHT - block_size - 64, 16, 32) #size is 16 by 32 sizing - not having correct size will error in terminal
    fire.on()
    floor = [Block(i * block_size, HEIGHT - block_size, block_size)
        # Create blocks that goes to the left and right of the screen (not just current screen) block_size is how many we want on the left and right
        for i in range(-WIDTH // block_size, WIDTH * 2 // block_size)]
    # Gives us single block -> blocks = [Block(0, HEIGHT - block_size, block_size)] <- # HEIGHT - block_size will create it at the bottom the of screen

    objects = [*floor, Block(0, HEIGHT - block_size * 2, block_size), 
        Block(block_size*3, HEIGHT - block_size * 4, block_size), fire] 

    offset_x = 0
    scroll_area_width = 200

    #Event Loop
    run = True
    while run:
        clock.tick(FPS) #Ensures that game will run at 60 FPS (This regulate framerate across devices)

        for event in pygame.event.get():
            #check for quit game
            if event.type == pygame.QUIT:
                run = False
                break
            
            #Having keys here tells us when whenever we released the keys (pressed once)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and player.jump_count < 2:
                    player.jump()

        # Need to call loop because that is what calls our player every single frame (reference the loop method)
        player.loop(FPS)
        fire.loop()
        handle_move(player, objects)    
        draw(window, background, bg_image, player, objects, offset_x)

        # Checking if we are moving to the right, subtract by offset that we have 
        if ((player.rect.right - offset_x >= WIDTH - scroll_area_width) and player.x_vel > 0) or (
                (player.rect.left - offset_x <= scroll_area_width) and player.x_vel < 0):
            offset_x += player.x_vel # This will offset the screen by the player's velocity

    pygame.quit()
    quit()

# call main function when we run this file directly - importing it won't run game code
if __name__ == "__main__":
    main(window)