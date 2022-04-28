from collections import defaultdict
import random
from typing import List, Set, Tuple
from consts import *
from pyswip import Prolog


def getSymbol(val, symbol, default_to='.'):
    return symbol if val else default_to


def getDir(dirIdx: int):
    direction = DIR_MAP[dirIdx]
    dir = []
    # think in terms of X, Y
    # not i, j
    if direction == RNORTH:
        dir = [0, 1]
    elif direction == RSOUTH:
        dir = [0, -1]
    elif direction == REAST:
        dir = [1, 0]
    else:
        dir = [-1, 0]

    return dir

# for formatting output purposes
class Cell:
    """
        9 information for a cell
    """

    # for symbol 5
    translate = {
        WUMPUS: 'W',
        CONFUNDUS_PORTAL: 'O',
        WUMPUS_AND_CONFUNDUS: 'U',
        RNORTH: '^',
        RSOUTH: 'V',
        REAST: '>',
        RWEST: '<',
        NOT_VISITED_SAFE: 's',
        VISITED_SAFE: 'S',
        UNKNOWN: '?',
    }

    is_wall = False
    confounded = False
    stench = False
    tingle = False
    isOccupied = False
    agentKnowledge = None  # the agent's deduction on this cell
    coinIsOn = False
    bump = False
    scream = False

    def __init__(self, cell_info=[False, False, False, False, UNKNOWN, False, False, False, False], is_wall=False):
        self.confounded = cell_info[0]
        self.stench = cell_info[1]
        self.tingle = cell_info[2]
        self.isOccupied = cell_info[3]
        self.agentKnowledge = cell_info[4]
        self.isOccupied = cell_info[5]
        self.coinIsOn = cell_info[6]
        self.bump = cell_info[7]
        self.scream = cell_info[8]

        self.is_wall = is_wall

    def format_print_string(self) -> List[str]:
        if self.is_wall:
            return ['###', '###', '###']

        return [f"{getSymbol(self.confounded, '%')}{getSymbol(self.stench, '=')}{getSymbol(self.tingle, 'T')}", f"{getSymbol(self.isOccupied, '-', ' ')}{getSymbol(True, self.translate[self.agentKnowledge])}{getSymbol(self.isOccupied, '-', ' ')}", f"{getSymbol(self.coinIsOn, '*')}{getSymbol(self.bump, 'B')}{getSymbol(self.scream, '@')}"]

    def format_sensory_list(self):
        return [self.confounded, self.stench, self.tingle, self.coinIsOn, self.bump, self.scream]

class Sensory:
    """
        Percepts: Prior to any movement, the Agent receives an vector of sensory indicators: Confounded, Stench,
        Tingle, Glitter, Bump, Scream. All indicators are Off, except in the following situations:
        • Confounded indicator is On at the start of the game and after the Agent stepped into a cell with a Confundus
        Portal.
        • Stench indicator is On in the cell next to one inhabited by the Wumpus.
        • Tingle indicator is On in the cell next to one inhabited by a Confundus Portal.
        • Glitter is On in the cell inhabited by a Coin.
        • Bump is On if the Agent attempted an action Forward and the next cell in that direction contained a Wall.
        • Scream indicator is On after the Agent shot an arrow and the Wumpus was in the direction of the shot.
        Notice that the agent does not perceive its exact location on the grid
    """
    confounded = False
    stench = False
    tingle = False
    glitter = False
    bump = False
    scream = False

    translate = {
        0: 'Confounded',
        1: 'Stench',
        2: 'Tingle',
        3: 'Glitter',
        4: 'Bump',
        5: 'Scream'
    }

    def __init__(self, inputs):
        self.confounded, self.stench, self.tingle, self.glitter, self.bump, self.scream = inputs

    def as_bool_list(self):
        inputs = [self.confounded, self.stench, self.tingle, self.glitter, self.bump, self.scream]
        return inputs
    
    def as_display_list(self):
        return '-'.join([self.translate[idx] if on else self.translate[idx][0] for idx, on in enumerate(self.as_bool_list())])

    def as_str_list(self):
        """
            returns self as [on, on, off, etc...]
        """
        inputs = self.as_bool_list()
        a = ['on' if i else 'off' for i in inputs]
        return f"[{','.join(a)}]"


# the driver class
class Driver:

    abs_map = None
    agent_position = None
    agent_direction_string = None
    prolog = None
    has_arrow = True
    death_count = None
    wumpus_killed = False

    def __init__(self, abs_map: defaultdict(dict), agent_origin, agent_direction_string, prolog: Prolog, coins: List[Tuple[int]], f) -> None:
        """
            abs_map: the absolute map in [X][Y] notation, populated with the npcs
            agent_origin: the initial position where the agent spawns
            agent_direction_string: the relative direciton where agent is initially facing, relative to the absolute map,
            prolog: the prolog device
            coins: the initial coins position (in abs XY terms)
            f: the file to write logs to 
            this relative string while appears to be the same as prolog agent, is relative to 2 different things
            thus, relative north in prolog might refer to relative south in absolute terms
        """
        self.abs_map = abs_map # note we use [X][Y] notation
        self.spawn_point = agent_origin
        self.agent_position = agent_origin
        self.agent_direction_string = agent_direction_string
        self.prolog = prolog

        self.has_arrow = True

        # track initial coins positions for resetting
        self.total_coins = len(coins)
        self.coins_collected = 0
        self.coins_positions = coins
        self.death_count = 0
        self.wumpus_killed = False
        
        self.f = f

    def build_abs_map(self, display_confounded=False):
        res = defaultdict(dict)
        x_keys = list(self.abs_map.keys())
        for X in x_keys:
            y_keys = list(self.abs_map[X].keys())
            for Y in y_keys:
                value = self.abs_map[X].get(Y)
                
                cell = Cell()
                
                # populate indicators that are dependent on the surrounding, any thing of interest
                sur = self.check_surrounding(X, Y)

                # Stench indicator is On in the cell next to one inhabited by the Wumpus.
                if WUMPUS in sur:
                    cell.stench = True

                # Tingle indicator is On in the cell next to one inhabited by a Confundus Portal.
                if CONFUNDUS_PORTAL in sur:
                    cell.tingle = True

                # anything other than empty or wall is an npc
                if (self.agent_position[0] == X and self.agent_position[1] == Y) or (value != EMPTY and value != WALL):
                    cell.isOccupied = True
                
                # the abs map has perfect driver knowledge to use for symbol 5
                if value == WUMPUS:
                    cell.agentKnowledge = WUMPUS
                elif value == CONFUNDUS_PORTAL:
                    cell.agentKnowledge = CONFUNDUS_PORTAL
                elif self.agent_position[0] == X and self.agent_position[1] == Y:
                    cell.agentKnowledge = self.agent_direction_string
                    # Confounded indicator is On at the start of the game and after the Agent stepped into a cell with a Confundus Portal.
                    if display_confounded: 
                        cell.confounded = True
                elif value != WALL:
                    cell.agentKnowledge = NOT_VISITED_SAFE
                
                # symbol 7, note we skip 6, it is the same as 4
                if value == COIN:
                    cell.coinIsOn = True

                # ignore symbol 8 and 9 for absolute map, no transitory flags for initial absolute map

                # build the cell corresponding to this coord of X, Y in the abs map
                if value == WALL:
                    cell.is_wall = True

                res[X][Y] = cell

        return res

    def check_surrounding(self, X, Y) -> Set[str]:
        """
            Returns things of interest in the 4 directions where applicable
            Can be walls, coins, wumpus, portals. Does not return the exact count,
            it simply returns a set of distinct npcs' names.
        """
        dirs = [[0, 1], [1, 0],[-1, 0], [0, -1]]
        res = set()
        for dir in dirs:
            val = self.abs_map[X+dir[0]].get(Y+dir[1])
            if val and val != WALL and val != EMPTY:
                res.add(val)
        
        return res

    def _get_current_sensory(self) -> Sensory:
        """
            Gets the current sensory indicators based on where the agent currently is located on the abs map.
            This is a passive check, no actions are assumed to be taken, thus bump and scream will be False by default.
        """
        confounded = False
        stench = False
        tingle = False
        glitter = False
        bump = False
        scream = False

        curX, curY = self.agent_position
        sur = self.check_surrounding(curX, curY)
        val = self.abs_map[curX][curY]
        if val == CONFUNDUS_PORTAL:
            confounded = True
        if WUMPUS in sur:
            stench = True
        if CONFUNDUS_PORTAL in sur:
            tingle = True
        if val == COIN:
            glitter = True
        
        return Sensory([confounded, stench, tingle, glitter, bump, scream])

    def _get_cell_infront(self):
        curX, curY = self.agent_position
        if self.agent_direction_string == RNORTH:
            return self.abs_map[curX][curY+1]
        elif self.agent_direction_string == RSOUTH:
            return self.abs_map[curX][curY-1]
        elif self.agent_direction_string == REAST:
            return self.abs_map[curX+1][curY]
        elif self.agent_direction_string == RWEST:
            return self.abs_map[curX-1][curY]
        
        # should never run
        print('illegal direction:', self.agent_position)
        return None 

    def do_reborn(self):
        self.f.write('agent is reborning...\n')
        # make sure the abs_map returns back to its original state
        self.agent_position = self.spawn_point
        for coin_xy in self.coins_positions:
            x, y = coin_xy
            self.abs_map[x][y] = COIN
        self.coins_collected = 0
        self.death_count += 1
        
        # tell prolog agent to reborn also
        list(self.prolog.query('reborn'))

    def _is_safe_cell(self, X, Y) -> bool:
        val = self.abs_map[X][Y]
        return val == EMPTY or val == COIN

    def get_random_safe_pos(self):
        while True:
            randomX = random.choice(list(self.abs_map.keys()))
            ys = list(self.abs_map[randomX].keys())
            if ys:
                randomY = random.choice(ys)
                if self._is_safe_cell(randomX, randomY):
                    return [randomX, randomY]
    
    def do_reposition(self):
        self.f.write('agent is repositioning...\n')
        self.agent_position = self.get_random_safe_pos()
        sensory = self._get_current_sensory()
        sensory.confounded = True

        # tell prolog agent to reposition and feed in new random spot's sensory
        list(self.prolog.query(f'reposition({sensory.as_str_list()})'))

    def do_move_forward(self):
        # this step is assured to be safe, no walls, wumpus or portals, just move forward
        if self.agent_direction_string == RNORTH:
            self.agent_position[1] += 1
        elif self.agent_direction_string == RSOUTH:
            self.agent_position[1] -= 1
        elif self.agent_direction_string == REAST:
            self.agent_position[0] += 1
        elif self.agent_direction_string == RWEST:
            self.agent_position[0] -= 1

    def do_turn_left(self):
        if self.agent_direction_string == RNORTH:
            self.agent_direction_string = RWEST
        elif self.agent_direction_string == RSOUTH:
            self.agent_direction_string = REAST
        elif self.agent_direction_string == REAST:
            self.agent_direction_string = RNORTH
        elif self.agent_direction_string == RWEST:
            self.agent_direction_string = RSOUTH
    
    def do_turn_right(self):
        if self.agent_direction_string == RNORTH:
            self.agent_direction_string = REAST
        elif self.agent_direction_string == RSOUTH:
            self.agent_direction_string = RWEST
        elif self.agent_direction_string == REAST:
            self.agent_direction_string = RSOUTH
        elif self.agent_direction_string == RWEST:
            self.agent_direction_string = RNORTH

    def do_pickup(self) -> bool:
        """
            attempts to pick up a coin, returns if agent is successfull
            i.e. if there is a coin
        """
        curX, curY = self.agent_position
        val = self.abs_map[curX][curY]
        if val == COIN:
            self.abs_map[curX][curY] = EMPTY
            return True
        
        return False

    def do_shoot(self) -> bool:
        """
            attempts to shoot in the direction of the agent
            shot goes through all obstacles
            reports if the wumpus is killed,
            i.e. if the wumpus lies in the path of the shot
        """
        xOffset, yOffset = [-1,-1]
        if self.agent_direction_string == RNORTH:
            xOffset, yOffset = [0, 1]
        elif self.agent_direction_string == RSOUTH:
            xOffset, yOffset = [0, -1]
        elif self.agent_direction_string == REAST:
            xOffset, yOffset = [1, 0]
        elif self.agent_direction_string == RWEST:
            xOffset, yOffset = [-1, 0]
        
        curX, curY = self.agent_position
        while curX in self.abs_map and curY in self.abs_map[curX]:
            val = self.abs_map[curX][curY]
            if val == WUMPUS:
                self.abs_map[curX][curY] = EMPTY
                return True
            
            curX += xOffset
            curY += yOffset
        
        return False
                

    def do_action(self, action) -> Sensory:
        """
            The driver will determine the agent's sensory indicators from the agent's position and intended action
            
            action: the action the agent has chosen
        """
        current_sensory = self._get_current_sensory()

        if action == MOVE_FORWARD:
            cell_in_front = self._get_cell_infront()
            if cell_in_front == WALL:
                current_sensory.bump = True
                return current_sensory
            elif cell_in_front == WUMPUS:
                # agent stepped into wumpus
                self.f.write('agent stepped into wumpus\n')
                self.do_reborn()
                return self._get_current_sensory()
            elif cell_in_front == CONFUNDUS_PORTAL:
                self.f.write('agent stepped into portal\n')
                self.do_reposition()
                sensory = self._get_current_sensory()
                sensory.confounded = True
                return sensory
            
            # can move forward with no weird interactions
            self.do_move_forward()

            return self._get_current_sensory()

        elif action == TURN_LEFT or action == TURN_RIGHT:
            if action == TURN_LEFT:
                self.do_turn_left()
            else:
                self.do_turn_right()

            return current_sensory # no need to retake sensory test
        
        elif action == PICKUP:
            success = self.do_pickup()
            if success:
                self.f.write('agent picked up a coin!\n')
                self.coins_collected += 1
                if self.coins_collected == self.total_coins:
                    self.f.write('agent collected all the coins possible!\n')
            else:
                self.f.write('agent picked up nothing\n')

            return self._get_current_sensory()
        
        elif action == SHOOT:
            success = False
            if self.has_arrow:
                success = self.do_shoot()
                if success:
                    self.f.write('agent shot the wumpus!\n')
                    self.wumpus_killed = True
                else:
                    self.f.write('agent shot but missed\n')
            else:
                self.f.write('agent wants to shoot but has no arrow, ignoring...\n')

            new_sensory = self._get_current_sensory()
            new_sensory.scream = success # indicate scream if applicable
            return new_sensory

        else:
            print('illegal action, not recognised:', action)
            return current_sensory


def build_relative_map(prolog: Prolog, confounded, bump, scream):
    """
        Some indicators are not remembered by the agent but should be displayed when they are passed as 
        sensory inputs such as confounded, bump and scream
    """
    res = defaultdict(dict)
    
    # first mark all sensory inputs that are passed in
    # agent doesnt actually remember them but we need to display
    # nonetheless
    agent_current = list(prolog.query('current(X,Y,D)'))
    cur = agent_current[0]

    X, Y, D = cur['X'], cur['Y'], cur['D']
    res[X][Y] = Cell()
    # agent's current cell is always special
    # symbol 1, 8, 9
    res[X][Y].confounded = confounded
    res[X][Y].bump = bump
    res[X][Y].scream = scream
    res[X][Y].agentKnowledge = D
    res[X][Y].isOccupied = True

    # walls
    wallsXY = list(prolog.query('wall(X,Y)'))
    for xy in wallsXY:
        x, y = xy['X'], xy['Y']
        cell = res[x].get(y)
        if not cell:
            cell = Cell()
        cell.is_wall = True
        res[x][y] = cell

    # symbol 2 - stench
    stenchsXY = list(prolog.query('stench(X,Y)'))
    for xy in stenchsXY:
        x, y = xy['X'], xy['Y']
        cell = res[x].get(y)
        if not cell:
            cell = Cell()
        cell.stench = True
        res[x][y] = cell
    
    # symbol 3 - tingle
    tinglesXY = list(prolog.query('tingle(X,Y)'))
    for xy in tinglesXY:
        x, y = xy['X'], xy['Y']
        cell = res[x].get(y)
        if not cell:
            cell = Cell()
        cell.tingle = True
        res[x][y] = cell

    # symbol 4 and 6 (isOccupied) are handled among others, agent, wumpus, coins, portals

    # symbol 5 - agent knowledge/inference
    wumpusXY = list(prolog.query('wumpus(X,Y)'))
    for xy in wumpusXY:
        x, y = xy['X'], xy['Y']
        cell = res[x].get(y)
        if not cell:
            cell = Cell()
        cell.agentKnowledge = WUMPUS
        cell.isOccupied = True
        res[x][y] = cell

    confundusXY = list(prolog.query('confundus(X,Y)'))
    for xy in confundusXY:
        x, y = xy['X'], xy['Y']
        cell = res[x].get(y)
        if not cell:
            cell = Cell()
        if cell.agentKnowledge == WUMPUS:
            cell.agentKnowledge = WUMPUS_AND_CONFUNDUS
        else:
            cell.agentKnowledge = CONFUNDUS_PORTAL
        cell.isOccupied = True
        res[x][y] = cell
    
    safesXY = list(prolog.query('safe(X,Y)'))
    visitedsXY = list(prolog.query('visited(X,Y)'))

    for xy in safesXY:
        x, y = xy['X'], xy['Y']
        if x == X and y == Y:
            continue # without the Agent inhabiting it
        cell = res[x].get(y)
        if not cell:
            cell = Cell()
        # check if visited
        visited = False
        for xy2 in visitedsXY:
            x2, y2 = xy2['X'], xy2['Y']
            if x2 == x and y2 == y:
                visited = True
                break
        
        if visited:
            cell.agentKnowledge = VISITED_SAFE
        else:
            cell.agentKnowledge = NOT_VISITED_SAFE
        res[x][y] = cell
    
    # symbol 7
    glittersXY = list(prolog.query('glitter(X,Y)'))
    for xy in glittersXY:
        x, y = xy['X'], xy['Y']
        cell = res[x].get(y)
        if not cell:
            cell = Cell()
        cell.coinIsOn = True
        cell.isOccupied = True
        res[x][y] = cell

    return res