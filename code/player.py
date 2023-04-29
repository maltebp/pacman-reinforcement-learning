import pickle
from typing import Callable, List
import numpy as np
import random 
from Counter import Counter
from run import GameController


class Player:

    def __init__(self, name, policy_name: str, exploration_rho=0.3, lr_alpha=0.2, discount_rate_gamma=0.9, walk_len_nu=0.2):
        self.name = name
        self.exploration_rho = exploration_rho
        self.lr_alpha = lr_alpha
        self.discount_rate_gamma = discount_rate_gamma
        self.walk_len_nu = walk_len_nu
        self.policy_name = policy_name
                
        # Q-table
        self.states_value = Counter()  # state -> value
        
        # current score
        self.old_score = 0
        
        # last state
        self.lastState = []

        # last action
        self.lastAction = []

        self.numIterations = 0
        

    # Get Q(s,a).
    def getQValue(self, state, action):
        return self.states_value[str([state,action])]

    # Return the maximum Q value of a given state.
    def getMaxQ(self, state, possible_directions):
        q_list = []
        for action in possible_directions:
            q = self.getQValue(state,action)
            q_list.append(q)
        if len(q_list) ==0:
            return 0
        return max(q_list)

    # update Q value
    def updateQ(self, state, action, reward, qmax):
        q = self.getQValue(state,action)
        self.states_value[str([state,action])] = (1 - self.lr_alpha)*q + self.lr_alpha*(reward + self.discount_rate_gamma*qmax - q)
    
    # Return the action that maximises Q of state.
    def takeBestAction(self, state, possible_directions):
        tmp = Counter()
        for action in possible_directions:
          tmp[action] = self.getQValue(state, action)
        # print(tmp)
        return tmp.argMax()
    

    def updateQValueOfLastState(self, state, stateScore, possible_directions):
        # Update Q-value of last state
        reward = stateScore - self.old_score
        if len(self.lastState) > 0:
            last_state = self.lastState[-1]
            last_action = self.lastAction[-1]
            max_q = self.getMaxQ(state, possible_directions)
            self.updateQ(last_state, last_action, reward, max_q)
        self.old_score = stateScore
    
    
    # The main method required by the game. Called every time that
    # Pacman is expected to move.
    def chooseAction(self, state: List, possibleActions):

        # (Explore vs Exploit)
        # Check if random action should be taken.
        rand_rho = random.uniform(0,1)
        if rand_rho < self.exploration_rho:
            # take random action
            action = np.random.choice(possibleActions) 
        else:
            # take the best action
            action =  self.takeBestAction(state, possibleActions)

        # Update attributes.
        self.lastState.append(state)
        self.lastAction.append(action)

        return action


    # This is called by the game after a win or a loss.
    def final(self):
        # Reset attributes.
        self.old_score = 0
        self.lastState = []
        self.lastAction = []

    # Saves the Q-table.
    def savePolicy(self):
        assert self.policy_name is not None and len(self.policy_name) > 0
        fw = open(self.policy_name, 'wb')
        pickle.dump(self.states_value, fw)
        pickle.dump(self.numIterations, fw)
        fw.close()

    # Loads a Q-table.
    def loadPolicy(self, file: str):
        fr = open(file, 'rb')
        self.states_value = pickle.load(fr)
        self.numIterations = pickle.load(fr)
        fr.close()