from typing import List
import pygame
from pygame.locals import *
from nodes import Node
from vector import Vector2
from constants import *
from entity import Entity
from sprites import PacmanSprites

class Pacman(Entity):
    def __init__(self, node):
        Entity.__init__(self, node )
        self.name = PACMAN    
        self.color = YELLOW
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.sprites = PacmanSprites(self)
        self.isAtNode = False
        self.learntDirection: int = STOP

    def reset(self):
        Entity.reset(self)
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()

    def die(self):
        self.alive = False
        self.direction = STOP

    def update(self, dt):	

        desiredDirection = self.getDesiredDirection()
        if desiredDirection != self.direction:
            if desiredDirection == STOP:
                self.target = self.node

            elif desiredDirection == self.direction * -1:
                tempTarget = self.target
                self.target = self.node
                self.node = tempTarget

            else:
                self.target = self.node.neighbors[desiredDirection]
            
            self.direction = desiredDirection

        self.sprites.update(dt)
        velocity = self.directions[self.direction] * self.speed * dt
        self.position += velocity
        
        if velocity.x != 0 or velocity.y != 0:
            self.isAtNode = False
        
        if self.overshotTarget():
            self.node = self.target
            if self.node.neighbors[PORTAL] is not None:
                self.node = self.node.neighbors[PORTAL]
            if self.direction in self.validDirectionsFromNode(self.node):
                self.target = self.node.neighbors[self.direction]
            self.setPosition()
            self.isAtNode = True

    def getDesiredDirection(self):
        if self.learntDirection in self.getValidDirections():
            return self.learntDirection
        return self.direction

    def getValidDirections(self):
        if self.isAtNode:
            return self.validDirectionsFromNode(self.node)
        return [ self.direction, self.direction * -1 ]

    def validDirectionsFromNode(self, node: Node):
        validDirections: List[int] = []
        for direction in [UP, DOWN, LEFT, RIGHT]:
            if self.name in node.access[direction]:
                if node.neighbors[direction] is not None:
                    validDirections.append(direction)
        return validDirections
    
    def getKeyboardDirection(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_UP]:
            return UP
        if key_pressed[K_DOWN]:
            return DOWN
        if key_pressed[K_LEFT]:
            return LEFT
        if key_pressed[K_RIGHT]:
            return RIGHT
        return STOP  

    def eatPellets(self, pelletList):
        for pellet in pelletList:
            if self.collideCheck(pellet):
                return pellet
        return None    
    
    def collideGhost(self, ghost):
        return self.collideCheck(ghost)

    def collideCheck(self, other):
        d = self.position - other.position
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        if dSquared <= rSquared:
            return True
        return False
