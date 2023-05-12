import time
from typing import List
from constants import *
from pacman import Pacman
from player import Player
from run import GameController 
from run import FRAMERATE
from relative_direction import RelativeDirection
from state_generation import generateStateString, getPacmanPreviousRelativeDirection


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

                currentState = generateStateString(game, previousActualDirection)
                isAtNewState = pacman.isAtNode or currentState != previousState

                if isAtNewState:

                    valid_directions = self.getValidRelativeDirections(pacman)

                    if self.isTraining and not isFirstState:
                        stateScore = game.pellets.numEaten * 100
                        reward = stateScore - previousStateScore
                        if choseReverseOfPreviousActualDirection: 
                            reward -= 100
                        self.p1.updateQValueOfLastState(currentState, reward, valid_directions)
                        previousStateScore = stateScore 

                    if len(valid_directions) > 0:
                        # Take action
                        chosenDirection = self.p1.chooseAction(currentState, valid_directions)
                        game.pacman.learntDirection = chosenDirection.toActualDirection(pacman.direction)
                        previousRelativeDirection = getPacmanPreviousRelativeDirection(pacman, previousActualDirection)
                        choseReverseOfPreviousActualDirection = chosenDirection.isOppositeDirection(previousRelativeDirection)
                        isFirstState = False 
                    else:
                        game.pacman.learntDirection = STOP
                    
                    previousState = currentState

                previousActualDirection = pacman.direction

                game.update()

                if not pacman.alive:

                    if not isFirstState and self.isTraining:
                        # Update Q-value of previous state
                        state = generateStateString(game, previousActualDirection)
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


    def getValidRelativeDirections(self, pacman: Pacman) -> List[RelativeDirection]:
        valid_directions = pacman.getValidDirections()
        if len(valid_directions) == 0: return [ ]
        
        valid_relative_directions = [
            RelativeDirection.fromActualDirection(pacman.direction, actualDirection)
            for actualDirection in valid_directions    
        ]
        assert len(valid_relative_directions) > 0

        return valid_relative_directions
    

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