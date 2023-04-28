# Pacman Reinforcement Learning Notes

**Time**







- How is life handled in reward function?



- State
  - How to handle power pellet? (just a pool I recon)
    - Dead ghosts should maybe be part of reward function
  - Is a ghost targeting same node as pacman
  - State of nearby nodes
  - State of nodes outside that range
  - Don't care about pacman position - care about position of everything else relative to pacman
- What to do about portals?
  - We cannot consider it just as a left option
  - Just have it as a 5th action option





- Pellets
  - We need to somehow encode that an action will lead to a pellet being eaten
  - Otherwise, an action will at one point not lead to a pellet being eaten, and at another point do 



- Reward of an action is based on how you got to the current state, **not the reward of taking the action**
  - 