import sys
import glob

from player import *
from state import *


if __name__ == "__main__":
    
    player = Player("Demo", "", exploration_rho=0, lr_alpha=0)

    if len(sys.argv) == 2:
        print(f"Loading policy from command line: '{sys.argv[1]}'")
        player.loadPolicy(sys.argv[1])            
    
    else:
        policies = sorted(glob.glob("policies/temp/policy-*"), key=str.lower)
        assert len(policies) > 0

        print(f"Loading latest policy: '{policies[0]}'")
        player.loadPolicy(policies[1])            
        print(f"Policy iterations: {player.numIterations}")

    state = State(player, False)    
    state.play()