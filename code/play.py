from player import *
from state import *


if __name__ == "__main__":
    
    player = Player("Demo", exploration_rho=0, lr_alpha=0)
    player.loadPolicy("trained_controller_2500_backup")

    state = State(player)    
    state.play()