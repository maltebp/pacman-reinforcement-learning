from enum import Enum, auto
import math
import time
import pickle
from typing import Dict, List
from constants import *
from ghosts import Ghost
from nodes import Node
from pacman import Pacman
from player import Player
from run import GameController 
from run import FRAMERATE 

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
    def generateStateString(self, game: GameController) -> str:
        pacman = game.pacman
        pacman_target = game.nodes.getPixelsFromNode(game.pacman.target)
        pacman_source = game.nodes.getPixelsFromNode(game.pacman.node)
        ghosts = game.ghosts.ghosts 

        def isGhostTargetingNode(node: Node) -> bool:
            nonlocal game
            return any(ghost.target is node for ghost in game.ghosts.ghosts)
        
        def isGhostTargetingNodeFromNode(source: Node, target: Node):
            return any(ghost.node is source and ghost.target is target for ghost in game.ghosts.ghosts)
        
        def isGhostTargetingNodeNotFromNode(invalidSource: Node, target) -> bool:
            nonlocal game
            return any(ghost.node is not invalidSource and ghost.target is target for ghost in game.ghosts.ghosts)
        
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
            for ghost in game.ghosts.ghosts:
                
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


        closest_ghost = self.getClosestGhostDirection(ghosts, pacman_target)

        return str([ ghost_targeted_directions ]) 
    
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

            previousGhostNodes: Dict[Ghost, Node] = { }
            for ghost in game.ghosts.ghosts:
                previousGhostNodes[ghost] = ghost.node                

            while True:

                numFrames += 1

                ghostChangedNode = False
                for ghost in game.ghosts.ghosts:
                    if previousGhostNodes[ghost] is not ghost.node:
                        ghostChangedNode = True
                    previousGhostNodes[ghost] = ghost.node     

                currentState = self.generateStateString(game)

                isAtNewState = pacman.isAtNode or currentState != previousState

                #print(pacman.direction)
                if isAtNewState:
                    # We're at a new state

                    #print(f"New state: {currentState}")
                    #print(f"  isAtNode={pacman.isAtNode}")

                    valid_directions = self.getValidRelativeDirections(pacman)

                    if self.isTraining and not isFirstState:
                        # Update Q-value of previous state
                        
                        # ghostDistances = [
                        #     ghost.position.distanceTo(game.pacman.position)
                        #     for ghost in game.ghosts.ghosts
                        # ]
                        # ghostDistanceReward = sum(d**1.5 if d < 150 else 0 for d in ghostDistances )
                        stateScore = 0 #1000 * game.lives #+ ghostDistanceReward
                        reward = stateScore - previousStateScore
 
                        self.p1.updateQValueOfLastState(currentState, reward, valid_directions)
                        previousStateScore = stateScore 

                    if len(valid_directions) > 0:
                        # Take action
                        chosenDirection = self.p1.chooseAction(currentState, valid_directions)
                        game.pacman.learntDirection = chosenDirection.toActualDirection(pacman.direction)
                        isFirstState = False 
                        #print(f"  action={chosenDirection}")

                    previousState = currentState

                    
                game.update()

                if not pacman.alive:

                    if not isFirstState:
                        # Update Q-value of previous state
                        state = self.generateStateString(game)
                        reward = -1000
                        self.p1.updateQValueOfLastState(state, reward, [])
                    
                    if not game.levelLost:
                        isFirstState = True
                        self.p1.resetStateHistory()
                        game.resetLevel()
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