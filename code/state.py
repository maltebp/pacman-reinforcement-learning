from enum import Enum, auto
import math
import sys
import time
import pickle
from typing import Dict, Iterable, List, Self, Tuple
from constants import *
from ghosts import Ghost
from nodes import Node
from pacman import Pacman
from pellets import Pellet
from player import Player
from run import GameController 
from run import FRAMERATE
from vector import Vector2 

class RelativeDirection(Enum):
    FORWARD = auto(),
    BACKWARD = auto(),
    RIGHT = auto(),
    LEFT = auto()

    def toActualDirection(self, pacmanCurrentActualDirection: int) -> int:
        
        if pacmanCurrentActualDirection == STOP:
            # Default to UP if actual direction is STOP
            pacmanCurrentActualDirection = UP

        if self == RelativeDirection.FORWARD: return pacmanCurrentActualDirection
        if self == RelativeDirection.BACKWARD: return pacmanCurrentActualDirection * -1

        if pacmanCurrentActualDirection == UP:
            if self == RelativeDirection.RIGHT: return RIGHT
            if self == RelativeDirection.LEFT: return LEFT
        
        if pacmanCurrentActualDirection == DOWN:
            if self == RelativeDirection.RIGHT: return LEFT
            if self == RelativeDirection.LEFT: return RIGHT

        if pacmanCurrentActualDirection == RIGHT:
            if self == RelativeDirection.RIGHT: return DOWN
            if self == RelativeDirection.LEFT: return UP
        
        if pacmanCurrentActualDirection == LEFT:
            if self == RelativeDirection.RIGHT: return UP
            if self == RelativeDirection.LEFT: return DOWN
        
        assert f"Invald pacman direction {pacmanCurrentActualDirection}"

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
    def fromActualDirection(cls, pacmanCurrentActualDirection: int, actualDirection: int):
        if pacmanCurrentActualDirection == STOP:
            # Default to UP if actual direction is STOP
            pacmanCurrentActualDirection = UP

        if pacmanCurrentActualDirection == actualDirection: return RelativeDirection.FORWARD
        if pacmanCurrentActualDirection == actualDirection * -1: return RelativeDirection.BACKWARD
        
        if pacmanCurrentActualDirection == UP:
            if actualDirection == RIGHT: return RelativeDirection.RIGHT
            if actualDirection == LEFT: return RelativeDirection.LEFT

        if pacmanCurrentActualDirection == DOWN:
            if actualDirection == RIGHT: return RelativeDirection.LEFT
            if actualDirection == LEFT: return RelativeDirection.RIGHT

        if pacmanCurrentActualDirection == RIGHT:
            if actualDirection == UP: return RelativeDirection.LEFT
            if actualDirection == DOWN: return RelativeDirection.RIGHT

        if pacmanCurrentActualDirection == LEFT:
            if actualDirection == UP: return RelativeDirection.RIGHT
            if actualDirection == DOWN: return RelativeDirection.LEFT

        assert f'Invalid direction {pacmanCurrentActualDirection}'



class Statistic:

    def __init__(self):
        self.numValues = 0
        self.max = None
        self.min = None
        self.average = None
    
    def report(self, value):
        
        if self.max is None or value > self.max:
            self.max = value
        
        if self.min is None or value < self.min:
            self.min = value

        self.numValues += 1
        if self.average is None:
            self.average = float(value)
        else:
            self.average -= self.average / self.numValues
            self.average += float(value) / self.numValues

    def string(self):
        return f'{self.average:.2f},{self.min},{self.max}'
        

class State:
    def __init__(self, p1: Player, isTraining: bool, isBenchmarking: bool):
        self.p1 = p1
        self.isEnd = False
        self.finalScore = 0
        self.isTraining = isTraining

        # Statistics for benchmarking
        self.isBenchmarking = isBenchmarking
        self.numGames = 0
        self.numWins = 0
        self.pelletsStatistic = Statistic()
        self.scoreStatistic = Statistic()
        self.timeStatistic = Statistic()
        self.ghostsKilledStatistic = Statistic()
        self.livesStatistic = Statistic()

    # Returns the direction of the closest ghost relative to pacman
    # if the ghost is within a certain range. Else, returns None.
    def getClosestGhostDirection(self, ghosts, pacman_target):
        closest_ghost = None
        closest_distance = 0
        for ghost in ghosts:
            distance = math.sqrt((pacman_target[0] - ghost.position.x)**2 + (pacman_target[1] - ghost.position.y)**2)
            if closest_ghost is None or distance < closest_distance:
                closest_ghost = ghost
                closest_distance = distance
        
        if closest_distance <= 80:
            vec = (closest_ghost.position.x - pacman_target[0], closest_ghost.position.y - pacman_target[1])
            if abs(vec[1]) >= abs(vec[0]): 
                if vec[1] >= 0:
                    return DOWN
                else:
                    return UP
            else: 
                if vec[0] >= 0:
                    return RIGHT
                else:
                    return LEFT
        else: 
            return None

    # Updates the state with the current game world's information.
    def generateStateString(self, game: GameController, previousActualDirection: int) -> str:

        pacman = game.pacman

        ghost_targeted_directions = State.getGhostTargetedDirections(game)

        directions_has_pellets = State.getDirectionsPelletState(game)

        # Compute direction to closest pellet
        direction_to_closest_pellet: RelativeDirection = None
        if any(directions_has_pellets.values()):
            # Closest pellet is on pacmans edge or the edge of the node that pacman is one,
            # so just find closest to pacmans position
            direction_to_closest_pellet = State.directionToClosestPellet(pacman, game.pellets.pelletList)
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
                closestPellet, closestPelletDistance = State.getClosestPellet(node.position, game.pellets.pelletList)
                closestPelletDistance += pacman.position.manhattanDistanceTo(node.position)
                if closestPelletDistance < shortestDistance:
                    shortestDistance = closestPelletDistance
                    direction_to_closest_pellet = RelativeDirection.fromActualDirection(pacman.direction, nodeDirection)

        return str([ State.getPacmanPreviousRelativeDirection(game.pacman, previousActualDirection), ghost_targeted_directions, directions_has_pellets, direction_to_closest_pellet]) 
    

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
        closestPellet, closestPelletDistance = State.getClosestPellet(pacman.position, pellets)
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
            manhattenDistance = abs(pellet.position.x - position.x) + abs(pellet.position.y - position.y)
            if manhattenDistance < closestPelletDistance:
                closestPellet = pellet
                closestPelletDistance = manhattenDistance

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
                directions_has_pellets[relativeDirection] = State.edgeHasPellet(pacman.node.position, directionNode.position, pellets)
        else:

            # Check if forward has pellets
            directions_has_pellets[RelativeDirection.FORWARD] = (
                    State.edgeHasPellet(pacman.position, pacman.target.position, pellets)
            )

            # Check if backward has pellets
            directions_has_pellets[RelativeDirection.BACKWARD] = (
                    State.edgeHasPellet(pacman.position, pacman.node.position, pellets)
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


    def getPacmanPreviousRelativeDirection(pacman: Pacman, previousActualDirection: int):        
        if pacman.isAtNode:
            return RelativeDirection.fromActualDirection(pacman.direction, previousActualDirection)
        else:
            return RelativeDirection.FORWARD

    # Checks if game is over i.e. level completed or all lives lost.
    def gameEnded(self, game):
        if game.lives <= 0 :
            self.isEnd = True
            self.finalScore = game.score
            return 0
        if game.level > self.level:
            return 1
        else:
            return None
    
    # Checks if game is paused i.e. after one life is lost or at the
    # beginning of new game. If it is, resumes it.
    def resumseIfPaused(self, game):
        if game.pause.paused:
            if game.pacman.alive:
                game.pause.setPause(playerPaused=True)
                if not game.pause.paused:
                    game.textgroup.hideText()
                    game.showEntities()

    def getValidRelativeDirections(self, pacman: Pacman) -> List[RelativeDirection]:
        valid_directions = pacman.getValidDirections()
        if len(valid_directions) == 0: return [ ]
        
        valid_relative_directions = [
            RelativeDirection.fromActualDirection(pacman.direction, actualDirection)
            for actualDirection in valid_directions    
        ]
        assert len(valid_relative_directions) > 0

        return valid_relative_directions

    # Main method for training.
    def play(self):

        startTime = time.perf_counter_ns()
        
        iteration = 0
        while True:
            iteration += 1    
            if self.isTraining:
                if iteration % 100 == 0:
                    print(f"Iterations: {iteration}, Q-Table size: {len(self.p1.states_value)}")
                    iterationsPerSec = (iteration / (time.perf_counter_ns() - startTime)) * 1_000_000_000
                    print(f"Iterations/second: {iterationsPerSec:.3f}")
                    self.p1.numIterations += 0 if iteration == 0 else 100
                    self.p1.savePolicy()
                    for state in self.p1.states_value:
                        print(f'  {state}: {self.p1.states_value[state]}')
                        
            skipRender = self.isTraining or self.isBenchmarking
            game = GameController(skipRender)
            game.startGame()
            game.update()
            pacman = game.pacman
            numFrames = 0
            self.p1.resetStateHistory()
            isFirstState = True
            previousState = None
            previousStateScore = 0

            previousActualDirection = LEFT # Pacman always starts to move left
            choseReverseOfPreviousActualDirection = False

            while True:

                numFrames += 1

                currentState = self.generateStateString(game, previousActualDirection)
                isAtNewState = pacman.isAtNode or currentState != previousState

                if isAtNewState:

                    # print(f"New state: {currentState}")
                    # print(f"  isAtNode={pacman.isAtNode}")
                    # print(f"  position={pacman.position}")
                    # print(f"  direction={pacman.direction}")
                    # print(f"  source={pacman.node.position}")
                    # print(f"  targetNode={pacman.target.position}")
                
                    valid_directions = self.getValidRelativeDirections(pacman)

                    if self.isTraining and not isFirstState:
                        stateScore = game.score
                        reward = (stateScore - previousStateScore) * 10
                        if choseReverseOfPreviousActualDirection: 
                            reward -= 100
                        self.p1.updateQValueOfLastState(currentState, reward, valid_directions)
                        previousStateScore = stateScore 

                    if len(valid_directions) > 0:
                        # Take action
                        chosenDirection = self.p1.chooseAction(currentState, valid_directions)
                        game.pacman.learntDirection = chosenDirection.toActualDirection(pacman.direction)
                        previousRelativeDirection = State.getPacmanPreviousRelativeDirection(pacman, previousActualDirection)
                        choseReverseOfPreviousActualDirection = chosenDirection.isOppositeDirection(previousRelativeDirection)

                        # print(f"  action={chosenDirection}")
                        isFirstState = False 
                    else:
                        game.pacman.learntDirection = STOP
                    
                    previousState = currentState

                previousActualDirection = pacman.direction

                game.update()

                if not pacman.alive:

                    if not isFirstState and self.isTraining:
                        # Update Q-value of previous state
                        state = self.generateStateString(game, previousActualDirection)
                        reward = -1000
                        self.p1.updateQValueOfLastState(state, reward, [])
                    
                    attemptsRemaining = not game.levelLost
                    if attemptsRemaining:
                        game.resetLevel()
                        previousState = None 
                        isFirstState = True
                        self.p1.resetStateHistory()
                        continue                    

                gameHasEnded = game.levelLost or game.levelWon
                if gameHasEnded:                
                    if self.isBenchmarking:
                        self.reportStatistics(game, game.levelWon, numFrames)        
                    break

            del game


    def reportStatistics(self, game: GameController, levelWon: bool, numFrames: int):
        self.numGames += 1
        if levelWon > 0: self.numWins += 1

        self.livesStatistic.report(game.lives)
        self.scoreStatistic.report(game.score)
        self.pelletsStatistic.report(game.pellets.numEaten)
        self.ghostsKilledStatistic.report(game.ghostsKilled)
        gameTime = float(numFrames) / FRAMERATE
        self.timeStatistic.report(gameTime)

        print(
            f'{self.numGames},' +
            f'{float(self.numWins / self.numGames):.2f},' +
            f'{self.livesStatistic.string()},' +
            f'{self.scoreStatistic.string()},' +
            f'{self.pelletsStatistic.string()},' +
            f'{self.ghostsKilledStatistic.string()},' +
            f'{self.timeStatistic.string()}'
        )