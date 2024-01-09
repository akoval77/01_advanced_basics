#!/usr/bin/env python
# -*- coding: utf-8 -*-

# -----------------
# Реализуйте функцию best_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. У каждой карты есть масть(suit) и
# ранг(rank)
# Масти: трефы(clubs, C), пики(spades, S), червы(hearts, H), бубны(diamonds, D)
# Ранги: 2, 3, 4, 5, 6, 7, 8, 9, 10 (ten, T), валет (jack, J), дама (queen, Q), король (king, K), туз (ace, A)
# Например: AS - туз пик (ace of spades), TH - дестяка черв (ten of hearts), 3C - тройка треф (three of clubs)

# Задание со *
# Реализуйте функцию best_wild_hand, которая принимает на вход
# покерную "руку" (hand) из 7ми карт и возвращает лучшую
# (относительно значения, возвращаемого hand_rank)
# "руку" из 5ти карт. Кроме прочего в данном варианте "рука"
# может включать джокера. Джокеры могут заменить карту любой
# масти и ранга того же цвета, в колоде два джокерва.
# Черный джокер '?B' может быть использован в качестве треф
# или пик любого ранга, красный джокер '?R' - в качестве черв и бубен
# любого ранга.

# Одна функция уже реализована, сигнатуры и описания других даны.
# Вам наверняка пригодится itertools.
# Можно свободно определять свои функции и т.п.
# -----------------

import itertools

RANK_VALUES = {
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5,
    '6': 6,
    '7': 7,
    '8': 8,
    '9': 9,
    'T': 10,
    'J': 11,
    'Q': 12,
    'K': 13,
    'A': 14,
}

def hand_rank(hand):
    """Возвращает значение определяющее ранг 'руки'"""
    ranks = card_ranks(hand)
    if straight(ranks) and flush(hand):
        return (8, max(ranks))
    elif kind(4, ranks):
        return (7, kind(4, ranks), kind(1, ranks))
    elif kind(3, ranks) and kind(2, ranks):
        return (6, kind(3, ranks), kind(2, ranks))
    elif flush(hand):
        return (5, ranks)
    elif straight(ranks):
        return (4, max(ranks))
    elif kind(3, ranks):
        return (3, kind(3, ranks), ranks)
    elif two_pair(ranks):
        return (2, two_pair(ranks), ranks)
    elif kind(2, ranks):
        return (1, kind(2, ranks), ranks)
    else:
        return (0, ranks)


def card_ranks(hand):
    """Возвращает список рангов (его числовой эквивалент),
    отсортированный от большего к меньшему"""
    return sorted([RANK_VALUES[c[0]] for c in hand], reverse=True)


def flush(hand):
    """Возвращает True, если все карты одной масти"""
    return len({c[1] for c in hand}) == 1


def straight(ranks):
    """Возвращает True, если отсортированные ранги формируют последовательность 5ти,
    где у 5ти карт ранги идут по порядку (стрит)"""

    ranks_len = 5

    if len(ranks) != ranks_len:
        return False
    return ranks == list(range(ranks[0], ranks[0]-ranks_len, -1))


def kind(n, ranks):
    """Возвращает первый ранг, который n раз встречается в данной руке.
    Возвращает None, если ничего не найдено"""
    curr_rank = ranks[0]
    c = 0

    for rank in ranks:
        if rank == curr_rank:
            c += 1
        else:
            if c == n:
                return curr_rank
            curr_rank = rank
            c = 1

    if c == n:
        return curr_rank

    return None


def two_pair(ranks):
    """Если есть две пары, то возврщает два соответствующих ранга,
    иначе возвращает None"""
    pairs = []
    prev_rank = ranks[0]
    for rank in ranks[1:]:
        if rank == prev_rank:
            pairs.append(rank)
            if len(pairs) == 2:
                break
            prev_rank = None
        else:
            prev_rank = rank

    if len(pairs) == 2:
        return pairs[0], pairs[1]
    else:
        return None


def best_hand(hand):
    """Из "руки" в 7 карт возвращает лучшую "руку" в 5 карт """
    # print(sorted(((c, hand_rank(c)) for c in itertools.combinations(hand, 5)), key=lambda x: x[1], reverse=True))
    return sorted(((c, hand_rank(c)) for c in itertools.combinations(hand, 5)), key=lambda x: x[1], reverse=True)[0][0]


def joker_hands(hand, jocker_type, suites):
    try:
        i = hand.index(jocker_type)
        for suite, rank in itertools.product(suites, RANK_VALUES.keys()):
            h = hand[:]
            h[i:i + 1] = (f"{rank}{suite}",)
            yield h
    except ValueError:
        yield hand


def best_wild_hand(hand):
    """best_hand но с джокерами"""
    best_hands = []
    for hb in joker_hands(hand, '?B', 'SC'):
        for h in joker_hands(hb, '?R', 'HD'):
            best_hands.append(
                sorted(
                    ((c, hand_rank(c)) for c in itertools.combinations(h, 5)),
                    key=lambda x: x[1],
                    reverse=True
                )[0]
            )
    return sorted(best_hands, key=lambda x: x[1], reverse=True)[0][0]


def test_best_hand():
    print("test_best_hand...")
    assert (sorted(best_hand("6C 7C 8C 9C TC 5C JS".split()))
            == ['6C', '7C', '8C', '9C', 'TC'])
    assert (sorted(best_hand("TD TC TH 7C 7D 8C 8S".split()))
            == ['8C', '8S', 'TC', 'TD', 'TH'])
    assert (sorted(best_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


def test_best_wild_hand():
    print("test_best_wild_hand...")
    assert (sorted(best_wild_hand("6C 7C 8C 9C TC 5C ?B".split()))
            == ['7C', '8C', '9C', 'JC', 'TC'])
    assert (sorted(best_wild_hand("TD TC 5H 5C 7C ?R ?B".split()))
            == ['7C', 'TC', 'TD', 'TH', 'TS'])
    assert (sorted(best_wild_hand("JD TC TH 7C 7D 7S 7H".split()))
            == ['7C', '7D', '7H', '7S', 'JD'])
    print('OK')


if __name__ == '__main__':
    test_best_hand()
    test_best_wild_hand()
