#!/usr/bin/env python
# -*- coding: utf-8 -*-

from functools import update_wrapper, WRAPPER_ASSIGNMENTS, WRAPPER_UPDATES


def disable(func):
    '''
    Disable a decorator by re-assigning the decorator's name
    to this function. For example, to turn off memoization:

    # >>> memo = disable

    '''
    return func


def decorator(wrapped):
    '''
    Decorate a decorator so that it inherits the docstrings
    and stuff from the function it's decorating.
    '''
    def decorator_wrapper(wrapper):
        return update_wrapper(wrapper, wrapped, assigned=WRAPPER_ASSIGNMENTS + ('__dict__',), updated=())

    return decorator_wrapper


def countcalls(func):
    '''Decorator that counts calls made to the function decorated.'''
    @decorator(func)
    def wrapper(*args):
        wrapper.calls += 1
        return func(*args)
    wrapper.calls = 0
    return wrapper


def memo(func):
    '''
    Memoize a function so that it caches all return values for
    faster future lookups.
    '''
    cache = dict()

    @decorator(func)
    def wrapper(*args):
        try:
            return cache[args]
        except KeyError:
            cache[args] = result = func(*args)
            return result
        except TypeError:
            # some element of args can't be a dict key
            return func(args)

    # print(f"memo {wrapper}, __dict__ {wrapper.__dict__}")
    return wrapper

def n_ary(func):
    '''
    Given binary function f(x, y), return an n_ary function such
    that f(x, y, z) = f(x, f(y,z)), etc. Also allow f(x) = x.
    '''
    @decorator(func)
    def n_ary_f(x, *args):
        return x if not args else func(x, n_ary_f(*args))
    return n_ary_f


def trace(indent):
    '''Trace calls made to function decorated.

    @trace("____")
    def fib(n):
        ....

    # >>> fib(3)
    #  --> fib(3)
    # ____ --> fib(2)
    # ________ --> fib(1)
    # ________ <-- fib(1) == 1
    # ________ --> fib(0)
    # ________ <-- fib(0) == 1
    # ____ <-- fib(2) == 2
    # ____ --> fib(1)
    # ____ <-- fib(1) == 1
    #  <-- fib(3) == 3

    '''
    def decorate(func):
        @decorator(func)
        def wrapper(*args):
            signature = '%s(%s)' % (func.__name__, ', '.join([str(a) for a in args]))
            print('%s--> %s' % (decorate.level*indent, signature))
            decorate.level += 1
            try:
                result = func(*args)
                print('%s<-- %s == %s' % ((decorate.level-1)*indent, signature, result))
            finally:
                decorate.level -= 1
            return result
        decorate.level = 0
        return wrapper
    return decorate


@memo
@countcalls
@n_ary
def foo(a, b):
    return a + b


@countcalls
@memo
@n_ary
def bar(a, b):
    return a * b


@countcalls
@memo
@trace("####")
def fib(n):
    """Some doc"""
    return 1 if n <= 1 else fib(n-1) + fib(n-2)


def main():
    print(foo(4, 3))
    print(foo(4, 3, 2))
    print(foo(4, 3))
    print("foo was called", foo.calls, "times")

    print(bar(4, 3))
    print(bar(4, 3, 2))
    print(bar(4, 3, 2, 1))
    print("bar was called", bar.calls, "times")

    print(fib.__doc__)
    fib(3)
    print(fib.calls, 'calls made')


if __name__ == '__main__':
    main()
