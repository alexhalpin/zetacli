import random
import argparse
import time
import math
import curses
import multiprocess as mp


def add_builder(args):
    a1 = random.randint(args.a1_min, args.a1_max)
    a2 = random.randint(args.a2_min, args.a2_max)
    s = a1 + a2

    return a1, a2, s


def sub_builder(args):
    s2, d, s1 = add_builder(args)

    return s1, s2, d


def mult_builder(args):
    m1 = random.randint(args.m1_min, args.m1_max)
    m2 = random.randint(args.m2_min, args.m2_max)
    p = m1 * m2

    return m1, m2, p


def div_builder(args):
    d2, q, d1 = mult_builder(args)

    return d1, d2, q


op_map = {
    '+': add_builder,
    '-': sub_builder,
    '*': mult_builder,
    '/': div_builder
}


def eq_builder(args):
    rand_op = random.choice(args.ops)

    o1, o2, ans = op_map[rand_op](args)

    return o1, o2, ans, f'{o1} {rand_op} {o2} = '


def key_listener(stdscr, input_stack, stack_lock):
    while (1):
        k = stdscr.getch()

        with stack_lock:
            # if number add to input stack
            if k >= 48 and k <= 57:
                input_stack.append(chr(k))

            # if backspace remove one from stack
            elif k == 127 and len(input_stack) > 0:
                input_stack.pop()


def update_ui(stdscr, input_stack, rem_time, score, equation, debug=None):
    height, width = stdscr.getmaxyx()
    eq_row = math.floor(2/3 * height)
    time_score_row = math.ceil(1/3 * height)
    eq_col = math.floor(1/2 * width - ((len(equation)+5)/2))
    time_col = math.floor(1/3 * width)
    score_col = math.floor(2/3 * width)

    stdscr.erase()
    stdscr.addstr(time_score_row, time_col, f'{rem_time}s')
    stdscr.addstr(time_score_row, score_col, str(score))
    stdscr.addstr(eq_row, eq_col,
                  f'{equation} {"".join(input_stack)}')
    if debug is not None:
        stdscr.addstr(0, 0, debug)
    stdscr.refresh()


def game_loop(stdscr, args):
    curses.noecho()
    curses.cbreak()
    stdscr.clear()

    proc_manager = mp.Manager()
    input_stack = proc_manager.list()
    stack_lock = proc_manager.Lock()

    rem_time = args.time
    score = 0
    start_time = time.perf_counter()
    _, _, correct_answer, eq_str = eq_builder(args)

    update_ui(stdscr, input_stack,
              rem_time, score, eq_str)

    # launch key listener
    key_process = mp.Process(target=key_listener,
                             args=(stdscr, input_stack, stack_lock))
    key_process.start()

    # while time remains
    while rem_time > 0:
        # if the input stack is equal to answer
        with stack_lock:
            if ''.join(input_stack) == str(correct_answer):
                input_stack[:] = []
                score += 1
                _, _, correct_answer, eq_str = eq_builder(args)

        # logic for keeping track of remaining time
        rem_time = args.time - \
            math.floor(time.perf_counter() - start_time)

        update_ui(stdscr, input_stack,
                  rem_time, score, eq_str)

    key_process.terminate()

    while key_process.is_alive():
        pass

    return score


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-a1', '--a1_min', dest='a1_min', type=int,
                        default=2, help="minimum value for first addend")
    parser.add_argument('-a2', '--a1_max', dest='a1_max', type=int,
                        default=100, help="maximum value for first addend")
    parser.add_argument('-a3', '--a2_min', dest='a2_min', type=int,
                        default=2, help="minimum value for second addend")
    parser.add_argument('-a4', '--a2_max', dest='a2_max', type=int,
                        default=100, help="maximum value for second addend")

    parser.add_argument('-m1', '--m1_min', dest='m1_min', type=int,
                        default=2, help="minimum value for first factor")
    parser.add_argument('-m2', '--m1_max', dest='m1_max', type=int,
                        default=12, help="maximum value for first factor")
    parser.add_argument('-m3', '--m2_min', dest='m2_min', type=int,
                        default=2, help="minimum value for second factor")
    parser.add_argument('-m4', '--m2_max', dest='m2_max', type=int,
                        default=100, help="maximum value for second factor")

    parser.add_argument('-o', '--operators', dest='ops',
                        type=str, default='+-*/', help="some non-empty subset of '+-*/'")

    parser.add_argument('-t', '--time', dest='time', type=int,
                        default=120, help="game duration in seconds")

    args = parser.parse_args()

    for k, v in vars(args).items():
        if type(v) == int:
            assert v > 0, f'{k} must be greater than 0'

    assert args.a1_min <= args.a1_max, 'invalid operand range (a1)'
    assert args.a2_min <= args.a2_max, 'invalid operand range (a2)'
    assert args.m1_min <= args.m1_max, 'invalid operand range (m1)'
    assert args.m2_min <= args.m2_max, 'invalid operand range (m2)'

    assert len(args.ops) <= 4 and len(
        args.ops) > 0, 'invalid number of operations'
    assert set(args.ops).issubset(set('+-*/')), 'invalid operation detected'

    score = curses.wrapper(game_loop, args)

    print(f'Score: {score}')
