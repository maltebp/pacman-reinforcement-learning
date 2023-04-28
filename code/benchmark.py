import sys
import glob

from player import *
from state import *


if __name__ == "__main__":
    
    player = Player("Benchmark", "", exploration_rho=0, lr_alpha=0)

    if len(sys.argv) == 2:
        print(f"Loading policy from command line: '{sys.argv[1]}'")
        player.loadPolicy(sys.argv[1])
        

    else:
        policies = sorted(glob.glob("policies/temp/policy-*"), key=str.upper)
        assert len(policies) > 0

        print(f"Loading latest policy: '{policies[-1]}'")
        player.loadPolicy(policies[-1])            
    
    print(f"Policy iterations: {player.numIterations}")
    print(f"Policy size: {len(player.states_value)}")

    state = State(player, False, True)
    state.play()