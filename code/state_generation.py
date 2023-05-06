# Updates the state with the current game world's information.
import math
import sys
from typing import Iterable, Tuple

from pygame import Vector2
from constants import *
from nodes import Node
from pacman import Pacman
from pellets import Pellet
from relative_direction import RelativeDirection
from run import GameController


def generateStateString(game: GameController, previousActualDirection: int) -> str:

    pacman = game.pacman

    ghost_targeted_directions = getGhostTargetedDirections(game)

    directions_has_pellets = getDirectionsPelletState(game)

    # Compute direction to closest pellet
    direction_to_closest_pellet: RelativeDirection = None
    if any(directions_has_pellets.values()):
        # Closest pellet is on pacmans edge or the edge of the node that pacman is one,
        # so just find closest to pacmans position
        direction_to_closest_pellet = directionToClosestPellet(pacman, game.pellets.pelletList)
    else:

        # No pellet in pacmans edge / adjacent edges, so find direction to
        # neighboring node that is closest to a pellet            
        neighborNodes: Tuple[int, Node] = []
        if pacman.isAtNode:
            for validDirection in pacman.getValidDirections():
                directionNode = pacman.node.neighbors[validDirection]
                neighborNodes.append((validDirection, directionNode))   
        else:
            neighborNodes.append((pacman.direction, pacman.target))
            neighborNodes.append((-pacman.direction, pacman.node))

        shortestDistance = sys.float_info.max
        for nodeDirection, node in neighborNodes:
            closestPellet, closestPelletDistance = getClosestPellet(node.position, game.pellets.pelletList)
            closestPelletDistance += pacman.position.manhattanDistanceTo(node.position)
            if closestPelletDistance < shortestDistance:
                shortestDistance = closestPelletDistance
                direction_to_closest_pellet = RelativeDirection.fromActualDirection(pacman.direction, nodeDirection)

    has_power_pellet = any(ghost.mode.current == FREIGHT for ghost in game.ghosts.ghosts)

    return str([ 
        has_power_pellet,
        getPacmanPreviousRelativeDirection(game.pacman, previousActualDirection), 
        ghost_targeted_directions, 
        directions_has_pellets, 
        direction_to_closest_pellet
    ]) 


def getPacmanPreviousRelativeDirection(pacman: Pacman, previousActualDirection: int):        
        if pacman.isAtNode:
            return RelativeDirection.fromActualDirection(pacman.direction, previousActualDirection)
        else:
            return RelativeDirection.FORWARD


def getGhostTargetedDirections(game: GameController):
    pacman = game.pacman
    ghosts = game.ghosts.ghosts

    def isGhostTargetingNodeFromNode(source: Node, target: Node):
        return any(ghost.node is source and ghost.target is target for ghost in ghosts)
    
    def isGhostTargetingNodeNotFromNode(invalidSource: Node, target) -> bool:
        nonlocal game
        return any(ghost.node is not invalidSource and ghost.target is target for ghost in ghosts)
    
    ghost_targeted_directions = {
        RelativeDirection.FORWARD: False,
        RelativeDirection.BACKWARD: False,
        RelativeDirection.RIGHT: False,
        RelativeDirection.LEFT: False,
    }
    
    if pacman.isAtNode:
        for validDirection in pacman.getValidDirections():
            directionNode = pacman.node.neighbors[validDirection]
            relativeDirection = RelativeDirection.fromActualDirection(pacman.direction, validDirection)
            ghost_targeted_directions[relativeDirection] = (
                isGhostTargetingNodeNotFromNode(pacman.node, directionNode) 
                or 
                isGhostTargetingNodeFromNode(directionNode, pacman.node)
            )
    else:
        for ghost in ghosts:
            
            if ghost.target is pacman.target:
                if ghost.node is not pacman.node:
                    ghost_targeted_directions[RelativeDirection.FORWARD] = True
                else:
                    # Ghost is on same edge as pacman, moving in same direction
                    ghostDistanceToPacmanTarget = ghost.position.distanceTo(pacman.target.position)
                    pacmanDistanceToPacmanTarget = pacman.position.distanceTo(pacman.target.position)
                    if ghostDistanceToPacmanTarget > pacmanDistanceToPacmanTarget:
                        # Ghost is behind of pacman
                        ghost_targeted_directions[RelativeDirection.BACKWARD] = True

            if ghost.target is pacman.node:
                if ghost.node is not pacman.target:
                    ghost_targeted_directions[RelativeDirection.BACKWARD] = True
                else:
                    # Ghost is on same edge as pacman, moving in opposite direction
                    ghostDistanceToPacmanSource = ghost.position.distanceTo(pacman.node.position)
                    pacmanDistanceToPacmanSource = pacman.position.distanceTo(pacman.node.position)
                    if ghostDistanceToPacmanSource > pacmanDistanceToPacmanSource:
                        # Ghost is in front of pacman   
                        ghost_targeted_directions[RelativeDirection.FORWARD] = True

    return ghost_targeted_directions


def directionToClosestPellet(pacman: Pacman, pellets: Iterable[Pellet]):
    closestPellet, closestPelletDistance = getClosestPellet(pacman.position, pellets)
    if closestPellet == None:
        # This should only happen when game is done
        return RelativeDirection.FORWARD
    
    relativePelletPosition = closestPellet.position - pacman.position
    angleToPellet = math.atan2(-relativePelletPosition.y, relativePelletPosition.x)
    
    if angleToPellet <= math.pi/4 and angleToPellet >= -math.pi/4:
        return RelativeDirection.fromActualDirection(pacman.direction, RIGHT)
    
    if angleToPellet >= math.pi/4 and angleToPellet <= 3 * math.pi/4:
        return RelativeDirection.fromActualDirection(pacman.direction, UP)
    
    if angleToPellet <= -math.pi/4 and angleToPellet >= -3 * math.pi/4:
        return RelativeDirection.fromActualDirection(pacman.direction, DOWN)
    
    if angleToPellet >= 3 * math.pi/4 or angleToPellet <= 3 * -math.pi/4:
        return RelativeDirection.fromActualDirection(pacman.direction, LEFT)

    return RelativeDirection.FORWARD
    

def getClosestPellet(position: Vector2, pellets: Iterable[Pellet]):
    closestPelletDistance = sys.float_info.max
    closestPellet: Pellet = None
    for pellet in pellets:    
        distance = position.manhattanDistanceTo(pellet.position)
        if distance < closestPelletDistance:
            closestPellet = pellet
            closestPelletDistance = distance

    return closestPellet, closestPelletDistance


def getDirectionsPelletState(game: GameController):
    pacman = game.pacman
    pellets = game.pellets.pelletList

    directions_has_pellets = {
        RelativeDirection.FORWARD: False,
        RelativeDirection.BACKWARD: False,
        RelativeDirection.RIGHT: False,
        RelativeDirection.LEFT: False,
    }
    
    if pacman.isAtNode:
        for validDirection in pacman.getValidDirections():
            directionNode = pacman.node.neighbors[validDirection]
            relativeDirection = RelativeDirection.fromActualDirection(pacman.direction, validDirection)
            directions_has_pellets[relativeDirection] = edgeHasPellet(pacman.node.position, directionNode.position, pellets)
    else:

        # Check if forward has pellets
        directions_has_pellets[RelativeDirection.FORWARD] = (
                edgeHasPellet(pacman.position, pacman.target.position, pellets)
        )

        # Check if backward has pellets
        directions_has_pellets[RelativeDirection.BACKWARD] = (
                edgeHasPellet(pacman.position, pacman.node.position, pellets)
        )

    return directions_has_pellets


def edgeHasPellet(edgeStart: Vector2, edgeEnd: Vector2, pellets: Iterable[Pellet]):
    def almost_equal(f1: float, f2: float):
        return abs(f1 - f2) < sys.float_info.epsilon
    
    def is_within_interval(value: float, bound1: float, bound2: float):
        min = bound1 if bound1 < bound2 else bound2
        max = bound1 if bound1 > bound2 else bound2
        if almost_equal(value, min): return True
        if almost_equal(value, max): return True
        if value > min and value < max: return True
        return False

    startX = edgeStart.x
    startY = edgeStart.y
    endX = edgeEnd.x
    endY = edgeEnd.y

    if almost_equal(startX, endX):
        for pellet in pellets:
            pelletX = pellet.position.x
            pelletY = pellet.position.y
            pelletIsOnEdge = almost_equal(pelletX, startX) and is_within_interval(pelletY, startY, endY)
            if pelletIsOnEdge:
                return True
        
        return False

    if almost_equal(startY, endY):
        for pellet in pellets:
            pelletX = pellet.position.x
            pelletY = pellet.position.y           
            pelletIsOnEdge = almost_equal(pelletY, startY) and is_within_interval(pelletX, startX, endX)
            if pelletIsOnEdge:
                return True
        return False
    
    assert False, "Nodes are not part of same edge"