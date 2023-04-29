from enum import Enum, auto
import math
import time
import pickle
from constants import *
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

    @classmethod
    def fromActualDirection(cls, pacmanCurrentActualDirection: int, actualDirection: int):
        assert actualDirection is not STOP

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
        self.state = []
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
    def updateState(self, game: GameController):
        pacman_target = game.nodes.getPixelsFromNode(game.pacman.target)
        pacman_source = game.nodes.getPixelsFromNode(game.pacman.node)
        ghosts = game.ghosts.ghosts 
        
        closest_ghost = self.getClosestGhostDirection(ghosts, pacman_target)

        head_on_collision_danger = any([
            game.nodes.getPixelsFromNode(ghost.target) is pacman_source and game.nodes.getPixelsFromNode(ghost.node) is pacman_target
            for ghost in ghosts
        ])

        same_target_ghost = any([game.nodes.getPixelsFromNode(ghost.target) is pacman_target for ghost in ghosts])

        self.state = [closest_ghost, head_on_collision_danger, same_target_ghost]
    
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
    def gamePaused(self, game):
        if game.pause.paused:
            if game.pacman.alive:
                game.pause.setPause(playerPaused=True)
                if not game.pause.paused:
                    game.textgroup.hideText()
                    game.showEntities()

    # Main method for training.
    def play(self):

        startTime = time.perf_counter_ns()
        
        iteration = 0
        while True:
            gameStartTime = time.perf_counter_ns()
            iteration += 1    
            if self.isTraining:
                if iteration % 100 == 0:
                    print(f"Iterations: {iteration}, Q-Table size: {len(self.p1.states_value)}")
                    iterationsPerSec = (iteration / (time.perf_counter_ns() - startTime)) * 1_000_000_000
                    print(f"Iterations/second: {iterationsPerSec:.3f}")
                    self.p1.numIterations += 0 if iteration == 0 else 100
                    self.p1.savePolicy()
            game = GameController()
            game.skipRender = self.isTraining or self.isBenchmarking
            game.startGame()
            game.update()
            self.updateState(game)
            self.level = game.level
            numFrames = 0
            while not self.isEnd:
                numFrames += 1
                
                valid_directions = game.pacman.validDirections()
                valid_relative_directions = [
                    RelativeDirection.fromActualDirection(game.pacman.direction, actualDirection)
                    for actualDirection in valid_directions    
                ]
            
                adjustedScore = game.score + 1000 * game.lives
                chosenDirection = self.p1.getAction(self.state, valid_relative_directions, adjustedScore)
                game.pacman.learntDirection = chosenDirection.toActualDirection(game.pacman.direction)
                game.update()

                self.updateState(game)

                # check board status if it is end
                self.gamePaused(game)
                gameHasEnded = self.gameEnded(game) is not None
                if gameHasEnded:
                    
                    if self.isBenchmarking:

                        self.numGames += 1
                        if game.lives > 0: self.numWins += 1

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

                    adjustedScore = game.score + 1000 * game.lives
                    self.p1.final(adjustedScore)
                    game.restartGame()
                    del game
                    self.isEnd = False
                    break

                else:
                    # next frame iteration
                    continue