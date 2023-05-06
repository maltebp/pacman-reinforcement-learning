from enum import Enum, auto
from typing import Self
from constants import *

class RelativeDirection(Enum):
    FORWARD = auto(),
    BACKWARD = auto(),
    RIGHT = auto(),
    LEFT = auto()

    def toActualDirection(self, baseDirection: int) -> int:
        
        if baseDirection == STOP:
            # Default to UP if actual direction is STOP
            baseDirection = UP

        if self == RelativeDirection.FORWARD: return baseDirection
        if self == RelativeDirection.BACKWARD: return baseDirection * -1

        if baseDirection == UP:
            if self == RelativeDirection.RIGHT: return RIGHT
            if self == RelativeDirection.LEFT: return LEFT
        
        if baseDirection == DOWN:
            if self == RelativeDirection.RIGHT: return LEFT
            if self == RelativeDirection.LEFT: return RIGHT

        if baseDirection == RIGHT:
            if self == RelativeDirection.RIGHT: return DOWN
            if self == RelativeDirection.LEFT: return UP
        
        if baseDirection == LEFT:
            if self == RelativeDirection.RIGHT: return UP
            if self == RelativeDirection.LEFT: return DOWN
        
        assert f"Invald pacman direction {baseDirection}"

    def isOppositeDirection(self, otherDirection: Self):
        if self == RelativeDirection.FORWARD and otherDirection == RelativeDirection.BACKWARD: return True
        if self == RelativeDirection.BACKWARD and otherDirection == RelativeDirection.FORWARD: return True
        if self == RelativeDirection.LEFT and otherDirection == RelativeDirection.RIGHT: return True
        if self == RelativeDirection.RIGHT and otherDirection == RelativeDirection.LEFT: return True
        return False        

    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.name

    @classmethod
    def fromActualDirection(cls, baseDirection: int, actualDirection: int):
        if baseDirection == STOP:
            # Default to UP if actual direction is STOP
            baseDirection = UP

        if baseDirection == actualDirection: return RelativeDirection.FORWARD
        if baseDirection == actualDirection * -1: return RelativeDirection.BACKWARD
        
        if baseDirection == UP:
            if actualDirection == RIGHT: return RelativeDirection.RIGHT
            if actualDirection == LEFT: return RelativeDirection.LEFT

        if baseDirection == DOWN:
            if actualDirection == RIGHT: return RelativeDirection.LEFT
            if actualDirection == LEFT: return RelativeDirection.RIGHT

        if baseDirection == RIGHT:
            if actualDirection == UP: return RelativeDirection.LEFT
            if actualDirection == DOWN: return RelativeDirection.RIGHT

        if baseDirection == LEFT:
            if actualDirection == UP: return RelativeDirection.RIGHT
            if actualDirection == DOWN: return RelativeDirection.LEFT

        assert f'Invalid direction {baseDirection}'