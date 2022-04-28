from consts import *
from models import *
from helper import *

from pyswip import Prolog

prolog_filename = "Gerald-Agent.pl"  # replace with path to prolog file

prolog = Prolog()
prolog.consult(prolog_filename)

def test_check(expectedXYs, rawQuery):
    actualXYs = [[item['X'], item['Y']] for item in list(prolog.query(rawQuery))]
    ok = True
    for expected in expectedXYs:
        found = False
        for actual in actualXYs:
            if actual[0] == expected[0] and actual[1] == expected[1]:
                found = True
                break
        if not found:
            ok = False
            break
    
    return ok

"""

    The structure of the driver's test.
    The driver runs 5 tests:

    1. test_agent_localisation_and_mapping
        This is the most basic test case where an agent's localisation and mapping abilities are tested.
        The driver instructs the agent's movements and the agent should correctly map its position on its relative map.
        The output can be read and verified from test1.txt.
    
    2. test_agent_sensory_inference
        This tests if the agent can recall the sensory inference occurence and map it to the relative X, Y coords correctly.
        The output can be read and verified from test2.txt.

    3. test_agent_memory_management
        Similar to test 2 but adds a portal step through test. The agent should not remember previous information.
        The output can be read and verified form test3.txt.

    4. test_agent_explore
        Creates a feedback loop with the agent and allows the agent to decide its steps.
        Checks the agent generates a correct and safe path and terminates at a non-visited or origin.
        The output can be read and verified form test4.txt.
    
    5. test_agent_end_game_reset
        Runs 2 consecutive maps. Both should pass. Reborn step is called in between.

"""
def test_agent_localisation_and_mapping():
    """
    Correctness of Agent’s localisation and mapping abilities
        – by asking the Agent to perform a test-sequence of actions
        – using localisation and mapping terms to confirm that the Agent correctly represents its relative position
        on its relative map.

        A short summary of the below test.
        1. The agent is directed to bump into walls and turn a few times. (in an attempt to confuse the agent).
        2. The agent should correctly remember all the walls positions.

        THe test case asserts that the agent should have successfully recalled all the walls it bumped into.
    """
    OUTPUT_FILE = 'test1.txt'
    # prepare output file
    f = open(OUTPUT_FILE, 'w+')
    f.truncate(0) # need '0' when using r+

    n, m = 7, 6 # 7x6
    wumpusXY = [2, 2]
    coinsXY = [[3, 4]]
    portalsXY = [[4, 1], [4, 2], [4, 4]]
    extraWalls = [[2, 1]]
    abs_map = create_abs_map(n, m, wumpusXY, coinsXY, portalsXY, extraWalls)
    driver = Driver(abs_map, [1,1], RWEST, prolog, coinsXY, f)

    cells = driver.build_abs_map(display_confounded=True)
    
    f.write("Conducting localization and mapping test\n")
    f.write('Displaying initial absolute map\n')
    f.write(pretty_format(cells) + '\n')

    f.write('Displaying intial relative map\n')
    doQuery(prolog, 'reborn')
    sensory = driver._get_current_sensory()
    sensory.confounded = True
    doQuery(prolog, 'reposition', sensory.as_str_list())
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')


    for _ in range(3):
        f.write('agent move forward\n')
        _, sensory = do_action_all(driver, MOVE_FORWARD)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

        f.write('agent turn left\n')
        _, sensory = do_action_all(driver, TURN_LEFT)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    for _ in range(4):
        f.write('agent move forward\n')
        _, sensory = do_action_all(driver, MOVE_FORWARD)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    f.write('agent turn right\n')
    _, sensory = do_action_all(driver, TURN_RIGHT)
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    for _ in range(4):
        f.write('agent move forward\n')
        _, sensory = do_action_all(driver, MOVE_FORWARD)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    expectedWallsXY = [[0, 1], [-1, 0], [0, -1], [4, -4]]
    wallsOk = test_check(expectedWallsXY, 'wall(X,Y)')

    f.write(f"Concluding test one.\n")
    f.write(f"Agent should recall all relative position of walls. TEST RESULT: {'PASS' if wallsOk else 'FAIL'}\n")

    f.close()

    return wallsOk


def test_agent_sensory_inference():
    """
    Correctness of Agent’s sensory inference
        – by asking the Agent to perform a test-sequence of (actions, observations)
        – using localisation and mapping terms to confirm that the Agent correctly absorbed and interpreted its
        sensory input

        A short summary of what happens:
        1. The agent is walked right infront of a wumpus. Along the way, the agent also encounters a tingle and a glitter.
        2. The agent then turns 180, i.e. turns left twice.
        3. The agent walk all the way forward and bumps into a wall.

        Four sensory states should be remembered and will be checked.
        The stench, tingle, glitter and wall.
    """
    OUTPUT_FILE = 'test2.txt'
    # prepare output file
    f = open(OUTPUT_FILE, 'w+')
    f.truncate(0) # need '0' when using r+

    n, m = 7, 6 # 7x6
    wumpusXY = [2, 2]
    coinsXY = [[2, 4]]
    portalsXY = [[4, 1], [4, 2], [3, 4]]
    extraWalls = [[2, 1]]
    abs_map = create_abs_map(n, m, wumpusXY, coinsXY, portalsXY, extraWalls)
    driver = Driver(abs_map, [2, 5], RSOUTH, prolog, coinsXY, f)

    cells = driver.build_abs_map(display_confounded=True)
    
    f.write("Conducting agent sensory test\n")
    f.write('Displaying initial absolute map\n')
    f.write(pretty_format(cells) + '\n')

    f.write('Displaying intial relative map\n')
    doQuery(prolog, 'reborn')
    sensory = driver._get_current_sensory()
    sensory.confounded = True
    doQuery(prolog, 'reposition', sensory.as_str_list())
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')


    for _ in range(2):
        f.write('agent move forward\n')
        _, sensory = do_action_all(driver, MOVE_FORWARD)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    for _ in range(2):
        f.write('agent turn left\n')
        _, sensory = do_action_all(driver, TURN_LEFT)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    for _ in range(3):
        f.write('agent move forward\n')
        _, sensory = do_action_all(driver, MOVE_FORWARD)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    # check the agent's sensory memory
    tingle_ok = test_check([[0, 1]], 'tingle(X,Y)')
    glitter_ok = test_check([[0, 1]], 'glitter(X,Y)')
    stench_ok = test_check([[0, 2]], 'stench(X,Y)')
    bump_ok = test_check([[0, -1]], 'wall(X,Y)')
    ok = tingle_ok and glitter_ok and stench_ok and bump_ok

    f.write(f"Concluding test two.\n")
    f.write(f"Agent should have correct sensory memory. TEST RESULT: {'PASS' if ok else 'FAIL'}\n")

    f.close()

    return ok

def test_agent_memory_management():
    """
    Correctness of Agent’s memory management in response to stepping though a Confundus Portal.
        – by feeding the Agent an (action,observation) sequence that creates a non-trivial map within the Agent’s
        knowledge.
        – ask the Agent to reset as if it stepped through a Confundus Portal (reposition/1 call)
        – confirming that the knowledge base of the Agent has been correctly cleaned via the use of localisation
        and mapping terms.
    """
    OUTPUT_FILE = 'test3.txt'
    # prepare output file
    f = open(OUTPUT_FILE, 'w+')
    f.truncate(0) # need '0' when using r+

    n, m = 7, 6 # 7x6
    wumpusXY = [2, 2]
    coinsXY = [[2, 4]]
    portalsXY = [[4, 1], [4, 2], [3, 4]]
    extraWalls = [[2, 1]]
    abs_map = create_abs_map(n, m, wumpusXY, coinsXY, portalsXY, extraWalls)
    driver = Driver(abs_map, [2, 5], RSOUTH, prolog, coinsXY, f)

    cells = driver.build_abs_map(display_confounded=True)
    
    f.write("Conducting agent memory test\n")
    f.write('Displaying initial absolute map\n')
    f.write(pretty_format(cells) + '\n')

    f.write('Displaying intial relative map\n')
    doQuery(prolog, 'reborn')
    sensory = driver._get_current_sensory()
    sensory.confounded = True
    doQuery(prolog, 'reposition', sensory.as_str_list())
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')


    for _ in range(2):
        f.write('agent move forward\n')
        _, sensory = do_action_all(driver, MOVE_FORWARD)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    for _ in range(2):
        f.write('agent turn left\n')
        _, sensory = do_action_all(driver, TURN_LEFT)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    for _ in range(1):
        f.write('agent move forward\n')
        _, sensory = do_action_all(driver, MOVE_FORWARD)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')
    
    f.write('agent turn right\n')
    _, sensory = do_action_all(driver, TURN_RIGHT)
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    # check the agent's sensory memory before entering portal
    before_tingle_ok = test_check([[0, 1]], 'tingle(X,Y)')
    before_glitter_ok = test_check([[0, 1]], 'glitter(X,Y)')
    before_stench_ok = test_check([[0, 2]], 'stench(X,Y)')
    before_ok = before_tingle_ok and before_glitter_ok and before_stench_ok

    f.write('agent move forward\n')
    _, sensory = do_action_all(driver, MOVE_FORWARD)
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    after_tingle_ok = test_check([], 'tingle(X,Y)')
    after_glitter_ok = test_check([], 'glitter(X,Y)')
    after_stench_ok = test_check([], 'stench(X,Y)')
    after_ok = after_tingle_ok and after_glitter_ok and after_stench_ok
    ok = before_ok and after_ok

    f.write(f"Concluding test three.\n")
    f.write(f"Agent should start afresh after stepping through portal. TEST RESULT: {'PASS' if ok else 'FAIL'}\n")

    f.close()

    return ok


def test_agent_explore():
    """
    Correctness of Agent’s exploration capabilities
        – Repeatedly call explore(L), confirm the generated path correctness (safe and ends at a non-visited
        location or Origin).
        – Feed the exploration plan back to the Agent via a sequence of move(A,L) calls
        – If the newly found cell contains a Coin, order the Agent to pick it up
        – Confirm that the Agent returns and stays at the origin once there are no more safely accessible unvisited parts of the map and all discovered coins have been collected.
    """
    OUTPUT_FILE = 'test4.txt'
    # prepare output file
    f = open(OUTPUT_FILE, 'w+')
    f.truncate(0) # need '0' when using r+

    n, m = 9, 9
    wumpusXY = [3, 2]
    coinsXY = [[5, 2]]
    portalsXY = [[3, 6], [4, 1], [6, 4]]
    extraWalls = [[2, 1], [2, 4]]
    abs_map = create_abs_map(n, m, wumpusXY, coinsXY, portalsXY, extraWalls)
    driver = Driver(abs_map, [1, 1], RNORTH, prolog, coinsXY, f)

    cells = driver.build_abs_map(display_confounded=True)
    
    f.write("Conducting agent explore test\n")
    f.write('Displaying initial absolute map\n')
    f.write(pretty_format(cells) + '\n')

    f.write('Displaying intial relative map\n')
    doQuery(prolog, 'reborn')
    sensory = driver._get_current_sensory()
    sensory.confounded = True
    doQuery(prolog, 'reposition', sensory.as_str_list())
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    while True:
        action = list(prolog.query('explore(L)'))
        if not action:
            break
        action = action[0]['L'][0]
        f.write(f'agent {action}\n')
        _, sensory = do_action_all(driver, action)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')


    f.write(f"Concluding test four.\n")
    f.write(f"Agent should collect all coins. TEST RESULT: {'PASS' if driver.coins_collected == driver.total_coins else 'FAIL'}\n")
    f.write(f"Agent should not have died. TEST RESULT: {'PASS' if driver.death_count == 0 else 'FAIL'}\n")
    f.write(f"Agent should kill wumpus. TEST RESULT: {'PASS' if driver.wumpus_killed else 'FAIL'}\n")
    f.write(f"Agent should return to origin. TEST RESULT: {'PASS' if driver.agent_position == driver.spawn_point else 'FAIL'}\n")

    f.close()

    ok = driver.coins_collected == driver.total_coins and driver.death_count == 0 and driver.wumpus_killed and driver.agent_position == driver.spawn_point

    return ok

def test_agent_end_game_reset():
    OUTPUT_FILE = 'test5.txt'
    # prepare output file
    f = open(OUTPUT_FILE, 'w+')
    f.truncate(0) # need '0' when using r+

    n, m = 9, 9
    wumpusXY = [3, 2]
    coinsXY = [[5, 2]]
    portalsXY = [[3, 6], [4, 1], [6, 4]]
    extraWalls = [[2, 1], [2, 4]]
    abs_map = create_abs_map(n, m, wumpusXY, coinsXY, portalsXY, extraWalls)
    driver = Driver(abs_map, [1, 1], RNORTH, prolog, coinsXY, f)

    cells = driver.build_abs_map(display_confounded=True)
    
    f.write("Conducting agent end game test\n")
    f.write("Conducing test one of two\n")
    f.write('Displaying initial absolute map\n')
    f.write(pretty_format(cells) + '\n')

    f.write('Displaying intial relative map\n')
    doQuery(prolog, 'reborn')
    sensory = driver._get_current_sensory()
    sensory.confounded = True
    doQuery(prolog, 'reposition', sensory.as_str_list())
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    while True:
        action = list(prolog.query('explore(L)'))
        if not action:
            break
        action = action[0]['L'][0]
        f.write(f'agent {action}\n')
        _, sensory = do_action_all(driver, action)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    first_run_pass = driver.coins_collected == driver.total_coins and driver.death_count == 0 and driver.wumpus_killed and driver.agent_position == driver.spawn_point

    # perform reborn on the same map
    prolog.query('reborn')
    abs_map = create_abs_map(n, m, wumpusXY, coinsXY, portalsXY, extraWalls)
    driver = Driver(abs_map, [1, 1], RNORTH, prolog, coinsXY, f)

    f.write("Conducing test two of two\n")
    f.write('Displaying initial absolute map\n')
    f.write(pretty_format(cells) + '\n')

    f.write('Displaying intial relative map\n')
    doQuery(prolog, 'reborn')
    sensory = driver._get_current_sensory()
    sensory.confounded = True
    doQuery(prolog, 'reposition', sensory.as_str_list())
    f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    while True:
        action = list(prolog.query('explore(L)'))
        if not action:
            break
        action = action[0]['L'][0]
        f.write(f'agent {action}\n')
        _, sensory = do_action_all(driver, action)
        f.write(pretty_format(build_relative_map(prolog, sensory.confounded, sensory.bump, sensory.scream)) + '\n')

    second_run_pass = driver.coins_collected == driver.total_coins and driver.death_count == 0 and driver.wumpus_killed and driver.agent_position == driver.spawn_point

    f.write(f"Concluding test five.\n")
    f.write(f"Agent can handle after reborn. TEST RESULT: {'PASS' if first_run_pass and second_run_pass else 'FAIL'}\n")

    f.close()
    ok = first_run_pass and second_run_pass

    return ok


if __name__ == '__main__':
    print(f"Running test 1...")
    ok1 = test_agent_localisation_and_mapping()
    print(f"Test 1 result: {'PASS' if ok1 else 'FAIL'}")

    print(f"Running test 2...")
    ok2 = test_agent_sensory_inference()
    print(f"Test 2 result: {'PASS' if ok2 else 'FAIL'}")

    print(f"Running test 3...")
    ok3 = test_agent_memory_management()
    print(f"Test 3 result: {'PASS' if ok3 else 'FAIL'}")

    print(f"Running test 4, it might take anywhere from 1-5 minutes...")
    ok4 = test_agent_explore()
    print(f"Test 4 result: {'PASS' if ok4 else 'FAIL'}")

    print(f"Running test 5, it might take anywhere from 2-10 minutes..")
    ok5 = test_agent_end_game_reset()
    print(f"Test 5 result: {'PASS' if ok5 else 'FAIL'}")

    # copy final
    FINAL_OUTPUT_FILE = "Gerald-testPrinout-Self-Self.txt"
    final = open(FINAL_OUTPUT_FILE, 'w+')
    final.truncate(0)

    for i in range(1, 6):
        with open(f'test{i}.txt') as f:
            final.write(f.read())
        final.write('\n\n\n')
    
    final.close()
