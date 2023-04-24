from datetime import datetime
from player import *
from state import *


if __name__ == "__main__":
    
    #### PARAMETERS:
    # ALPHA -> Learning Rate
    # controls how much influence the current feedback value has over the stored Q-value.
    LEARNING_RATE = 0.2

    # GAMMA -> Discount Rate
    # how much an action’s Q-value depends on the Q-value at the state (or states) it leads to.
    DISCOUNT_RATE = 0.9

    # RHO -> Randomness of Exploration
    # how often the algorithm will take a random action, rather than the best action it knows so far.
    EXPLORATION_RATE = 0.3

    # NU: The Length of Walk
    # number of iterations that will be carried out in a sequence of connected actions.    
    WALK_LENGTH = 0.2

    ITERATIONS = 10000

    print("Starting training")

    policy_name = f"policies/temp/policy-{datetime.now().strftime('%y-%m-%d-%H-%M-%S-%f')}"
    
    player = Player("Player", policy_name, EXPLORATION_RATE, LEARNING_RATE, DISCOUNT_RATE, WALK_LENGTH)
    state = State(player, True)
    state.play()