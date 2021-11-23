from argparse import ArgumentParser
from time import time, sleep
from random import choice
import sys

FINGER = 5

def trivial_win(attack, defend):
    return defend[0] == 0 and attack[1] + defend[1] >= FINGER


def swap(x,y):
    if x > y:
        return y, x
    return x, y


def hit(a, d):
    if a + d >= FINGER:
        return 0
    return a+d


def find_next(attack, defend):
    next_states = set()
    # 1. HIT
    for a in attack:
        for j in range(2):
            d0, d1 = defend[j], defend[1-j]
            if a>0 and d0 > 0:
                next_states.add(
                    (swap(hit(a, d0), d1), attack, f'H[{a},{d0}]'))
    # 2. SPLIT
    a0, a1 = 0, sum(attack)
    for _ in range(sum(attack)):
        if a1 < FINGER and (a0, a1) != attack:
            next_states.add(
                (defend, (a0, a1), f'S[{a0},{a1}]'))
        a0 += 1
        a1 -= 1
        if a0 > a1:
            break
    return next_states


class State(object):
    def __init__(self, attack, defend):
        self.attack = swap(*attack)
        self.defend = swap(*defend)
        self.prev_states = []
        # If current State is a winning state for attacker,...
        if trivial_win(attack, defend):
            self.win_or_lose = 'win'
            self.strategy = [f'H[{attack[1]},{defend[1]}]']
            self.next_states =  [((0,0), attack, f'H[{attack[1]},{defend[1]}]')]
        else:
            self.win_or_lose = None
            self.strategy = []
            self.next_states = sorted(find_next(attack, defend))


def all_hands():
    hands = []
    for left in range(FINGER):
        for right in range(left, FINGER):
            if left + right > 0:
                hands.append((left, right))
    return hands


def main(display=True):
    hands = all_hands()
    board_of_states = {attack: {defend: State(attack, defend) for defend in hands} for attack in hands}

    # Print board of states
    if display:
        print("Board of states + Next states + Actions:")
        for attack in hands:
            for defend in hands:
                state = board_of_states[attack][defend]
                print('A', attack, 'D', defend, state.next_states)

    t_init = time()
    # Find Previous States
    print("Finding previous states.....")
    states_to_search = []
    for attack in hands:
        for defend in hands:
            state = board_of_states[attack][defend]
            if trivial_win(attack, defend):
                states_to_search.append((attack, defend))
                continue
            for next_attack, next_defend, action in state.next_states:
                board_of_states[next_attack][next_defend].prev_states.append((attack, defend, action))

    # Breadth-First Search: Win or Lose
    print("Finding Winning/Losing states with BFS......")
    check_no_progress = 0
    while len(states_to_search) > check_no_progress:  # 더 이상 탐색의 여지가 없으면 terminate
        attack, defend = states_to_search.pop(0)
        state = board_of_states[attack][defend]
        if state.win_or_lose is None:
            # 1. 더 이상 나아갈 state가 없으면(4에서 next state가 지워진 경우) lose, 그리로 향하는 state를 이다음에 search
            if len(state.next_states) == 0:
                state.win_or_lose = 'lose'
                check_no_progress = 0
                for prev_attack, prev_defend, _ in state.prev_states:
                    if (prev_attack, prev_defend) not in states_to_search:
                        states_to_search.append((prev_attack, prev_defend))
            # 2. 아직 나아갈 next state 있는 경우, 그것 중 losing state 있으면 이 state는 win.
            for next_attack, next_defend, action in state.next_states:
                if board_of_states[next_attack][next_defend].win_or_lose == 'lose':
                    state.win_or_lose = 'win'
                    check_no_progress = 0
                    state.strategy.append(action)
        # 3. 아직 나아갈 next state 있어도 그 중 losing state 없으면 일단 보류.
        if state.win_or_lose is None:
            states_to_search.append((attack, defend))
            check_no_progress += 1
        # 4. winning state로 향하는 화살표(prev state들의 next state) 제거, 그리로 향하는 state를 이다음에 search
        elif state.win_or_lose == 'win':
            for prev_attack, prev_defend, action in state.prev_states[::-1]:
                board_of_states[prev_attack][prev_defend].next_states.remove((attack, defend, action))
                state.prev_states.remove((prev_attack, prev_defend, action))
                if (prev_attack, prev_defend) not in states_to_search:
                    states_to_search.append((prev_attack, prev_defend))

    # Tied states
    print("Processing Tied states......")
    for attack in hands:
        for defend in hands:
            state = board_of_states[attack][defend]
            if state.win_or_lose is None:
                state.win_or_lose = 'tie'
                for next_attack, next_defend, action in state.next_states:
                    if board_of_states[next_attack][next_defend].win_or_lose != 'win':
                        state.strategy.append(action+'*')
    t_fin = time()

    # print strategy table
    if display:
        print()
        if type(display) == str: # path of text file
            f = open(display, 'w')
        else:
            f = sys.stdout
        print("Strategy Table:", file=f)
        print("  H[x,y]  : attacker hits defender's y-hand with its x-hand", file=f)
        print("  S[x1,x2]: attacker splits its hand into (x1,x2)", file=f)
        win_lose_list = [0,0,0]
        for attack in hands:
            for defend in hands:
                state = board_of_states[attack][defend]
                print('A', attack, 'D', defend, state.win_or_lose, state.strategy, file=f)
                if state.win_or_lose == 'win':
                    win_lose_list[0] += 1
                elif state.win_or_lose == 'lose':
                    win_lose_list[1] += 1
                elif state.win_or_lose == 'tie':
                    win_lose_list[2] += 1
        print("\n Time to finding all strategies : %.4f seconds" % (t_fin-t_init), file=f)
        print(f"\n Win: {win_lose_list[0]} states || Lose: {win_lose_list[1]} states || Tie: {win_lose_list[2]} states", file=f)
        print("\n Side Note: Win_or_Lose of A(1,1) D(1,1) is", board_of_states[(1, 1)][(1, 1)].win_or_lose.upper(), file=f)
        f.close()
    return board_of_states


def do_action(attack, defend, action):
    action_type = action[0]
    hand1, hand2 = list(map(int, action[2:-1].split(',')))
    if action_type == 'H':  # Hit
        for i, j in [(1,1), (1,0), (0,1), (0,0)]:
            if attack[i] == hand1 and  defend[j] == hand2:
                new_defend = list(defend)
                new_defend[j] = hit(hand1, hand2)
                return attack, tuple(new_defend)
    elif action[0] == 'S':
        return (hand1, hand2), defend

def play_chopsticks(board_strategy):
    hands = all_hands()
    board_of_states = {attack: {defend: State(attack, defend) for defend in hands} for attack in hands}

    def ask_yesno(prompt):
        enter = input(prompt)
        while enter.lower() not in ['y', 'yes', 'n', 'no']:
            print("::Wrong Input::")
            enter = input(prompt)
        return enter.lower() in ['y', 'yes']

    while True:
        print("\nWelcome to Chopsticks Game: you CANNOT beat this.\n")
        print("*** Notation Alert! (about actions) ***")
        print("  H[x,y]  : attacker HITS defender's y-hand with one's x-hand")
        print("  S[x1,x2]: attacker SPLITS one's hands into x1 & x2")
        print()

        round = 1
        Computer = (1,1)
        Player = (1,1)
        Turn = 'YOUR'
        while (Computer != (0,0) and (Player) != (0,0)):
            print("######################################")
            print("Round", round, ": It is", Turn, "turn.")
            print("Computer:", Computer)
            print("You     :", Player)
            print()
            if Turn == 'YOUR':
                state = board_of_states[swap(*Player)][swap(*Computer)]
                actions = [action for _, _, action in state.next_states]
                print(Turn, "Available Actions:")
                for i, act in enumerate(actions):
                    print("   ", i+1, ":", act)
                act_num = input("Which action do you want to do? (Enter a number) : ")
                while (not act_num.isdigit()) or int(act_num) not in range(1, len(actions)+1):
                    print("::Wrong Input::")
                    act_num = input("Which action do you want to do? (Enter a number) : ")
                action = actions[int(act_num)-1]
                print(Turn, "Action is", action)
                Player, Computer = do_action(Player, Computer, action)
                Turn = "Computer's"
                sleep(2)
            else:  # Turn == "Computer's"
                state = board_of_states[swap(*Computer)][swap(*Player)]
                strategy_info = board_strategy[swap(*Computer)][swap(*Player)].strategy
                if len(strategy_info) == 0:  # Computer is losing
                    strategy_info = [action for _, _, action in state.next_states]
                action = choice(strategy_info)
                if action[-1] == '*':
                    action = action[:-1]
                for next_attack, next_defend, act in state.next_states:
                    if act == action:
                        Computer, Player = do_action(Computer, Player, action)
                print(Turn, "Action is", action)
                Turn = "YOUR"
                sleep(5)
            round += 1
            print()
        print("######################################")
        print("THE END:")
        print("Computer:", Computer)
        print("You     :", Player)
        print()
        if Player == (0,0):
            print("You LOST. \n\n")
            sleep(3)
        elif Computer == (0,0):
            print("You WON. How dare you?! \n\n")
            sleep(3)
        if not ask_yesno("Would you play another game? (y/n): "):
            break


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--n', default=5, type=int)
    parser.add_argument('--game', action='store_true')
    parser.add_argument('--txt', action='store_true')
    args = parser.parse_args()
    if args.n != 5:
        FINGER = args.n
    if args.game:
        play_chopsticks(main(False))
    else:
        main(str(FINGER)+'_fingers.txt' if args.txt else True)

