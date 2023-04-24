import random 
import numpy as np

BOARD_ROWS = 3
BOARD_COLS = 3
store = []

def QLearning(problem, iterations, alpha, gamma, rho, nu):
    state = problem.getRandomState()

    for i in range(iterations):
        rand_nu = random.uniform(0,1)
        if rand_nu < nu: 
            state = problem.getRandomState()
        
        actions = problem.getAvailableActions(state)
        
        rand_rho = random.uniform(0,1)
        if rand_rho < rho:
            action = random.choice(actions)
        else:
            action = store.getBestAction(state)

        reward, newState = problem.takeAction(state, action)
        Q = store.getQValue(state,action)
        maxQ = store.getQValue(newState, store.getBestAction(newState))

        Q = (1 - alpha) * Q + alpha * (reward + gamma * maxQ)

        store.storeQValue(state, action, Q)
        state = newState
