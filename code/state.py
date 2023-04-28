import math
import time
import pickle
from constants import *
from player import Player
from run import GameController 

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
            self.average = -self.average / self.numValues + float(value) / self.numValues

    def string(self):
        return f'{self.average:.2},{self.min},{self.max}'
        

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
    
    def availableDirections(self, pacman):
        return pacman.validDirections()

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
    def updateState(self, ghosts, pacman_target):
        closest_ghost = self.getClosestGhostDirection(ghosts, pacman_target)
        self.state = [int(pacman_target[0]), int(pacman_target[1]), closest_ghost]
    
    # Apply the chosen action (direction) to the game.
    def applyAction(self, game, direction):
        game.pacman.learntDirection = direction
        game.update()
    
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
                    print("Iterations {}".format(iteration))
                    iterationsPerSec = (iteration / (time.perf_counter_ns() - startTime)) * 1_000_000_000
                    print(f"Iterations/second: {iterationsPerSec:.3f}")
                    self.p1.numIterations += 0 if iteration == 0 else 200
                    self.p1.savePolicy()
            game = GameController()
            game.skipRender = self.isTraining or self.isBenchmarking
            game.startGame()
            game.update()
            pacman_target = game.nodes.getPixelsFromNode(game.pacman.target)
            self.updateState(game.ghosts, pacman_target)
            self.level = game.level
            while not self.isEnd:
                possible_directions = self.availableDirections(game.pacman)
                p1_action = self.p1.getAction(self.state, possible_directions, game.score)
                # take action and update board state
                self.applyAction(game, p1_action)
                pacman_target = game.nodes.getPixelsFromNode(game.pacman.target)
                self.updateState(game.ghosts, pacman_target)

                # check board status if it is end
                self.gamePaused(game)
                result = self.gameEnded(game)
                if result is not None:
                    
                    if self.isBenchmarking:
                        self.numGames += 1
                        if game.lives > 0: self.numWins += 1

                        self.livesStatistic.report(game.lives)
                        self.scoreStatistic.report(game.score)
                        self.pelletsStatistic.report(game.pellets.numEaten)
                        self.ghostsKilledStatistic.report(game.ghostsKilled)
                        gameTime = (time.perf_counter_ns() - gameStartTime) / 1_000_000_000.0
                        self.timeStatistic.report(gameTime)

                        print(
                            f'{self.numGames},' +
                            f'{float(self.numWins / self.numGames):.2f},' +
                            f'{self.livesStatistic.string()},' +
                            f'{self.scoreStatistic.string()},' +
                            f'{self.pelletsStatistic.string()},' +
                            f'{self.ghostsKilledStatistic.string()},' +
                            f'{self.livesStatistic.string()},' +
                            f'{self.timeStatistic.string()}'
                        )

                    self.p1.final(self.state, game.score)
                    game.restartGame()
                    del game
                    self.isEnd = False
                    break

                else:
                    # next frame iteration
                    continue