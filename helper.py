from collections import defaultdict
from consts import *
from pyswip import Prolog

from models import Cell

def pretty_format(cells):
    allXs = cells.keys()
    allYs = set()
    for x in allXs:
        allYs.update(cells[x].keys())
    allYs = list(allYs)

    allXs = sorted(allXs)
    allYs = sorted(allYs, reverse=True)

    rowStrs = defaultdict(lambda: '')
    for y in allYs:
        for x in allXs:
            cell = cells[x].get(y)
            if not cell:
                cell = Cell()
            strs = cell.format_print_string()
            for i in range(3):
                rowStrs[y * 3 + i] += f' {strs[i]}'
    
    res = ''
    ys = sorted(list(rowStrs.keys()), reverse=True)
    strs = [rowStrs[y] for y in ys]
    
    for idx, s in enumerate(strs):
        res += s
        res += '\n'
        if idx != 0 and (idx + 1) % 3 == 0:
            res += '\n'

    return res

def create_abs_map(n, m, wumpusXY, coinsXY, portalsXY, extraWallsXY) -> defaultdict(dict):
    abs_map = defaultdict(lambda: dict())
    for X in range(m):
        for Y in range (n):
            abs_map[X][Y] = EMPTY

            # bounding walls
            if X == 0 or X == m-1 or Y == 0 or Y == n-1:
                abs_map[X][Y] = WALL

    abs_map[wumpusXY[0]][wumpusXY[1]] = WUMPUS
    for idx, locs in enumerate([coinsXY, portalsXY, extraWallsXY]):
        for xy in locs:
            if idx == 0:
                abs_map[xy[0]][xy[1]] = COIN
            elif idx == 1:
                abs_map[xy[0]][xy[1]] = CONFUNDUS_PORTAL
            else:
                abs_map[xy[0]][xy[1]] = WALL

    return abs_map

def doQuery(prolog: Prolog, cmd: str, *args):
    s = ','.join(args)
    if s:
        s = f'({s})'
    query = f'{cmd}{s}'

    return list(prolog.query(query))

# simple wrapper to instruct abs and relatve agent
def do_action_all(driver, action):
    sensory = driver.do_action(action)
    driver.f.write(sensory.as_display_list() + '\n')
    L = sensory.as_str_list()
    return doQuery(driver.prolog, 'move', action, L), sensory