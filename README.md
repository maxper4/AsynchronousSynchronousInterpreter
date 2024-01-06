# Asynchronously Synchronous playground
Small experimentation about embedding asynchronous agents in a synchronous language. This is possible thanks to an activation condition added to each asynchronous agent. Hence, at each step we have to possibility to activate or not agents. We can then use a scheduler that works with a random oracle to simulate an asynchronous system.

# How to
This playground is in python and can be ran using `python MealyMachine.py`.

# Implementation
We assume every variable is of type int and the string value "bot" is used as a special value. We assume states, inputs and outputs are dictionaries of variables to model valuation functions.
## Mealy Machines
We made the choice to use Mealy Machines as an abstract synchronous machine. They benefit from several features:
- run: execute a single step of the defined machine.
- run_sequence: execute multiples steps of the machine.
- compose: compose a machine with another, which produces a synchronous composition.
- asynchronise: add a special variable to the machine which will act as an activation condition for the machine.

## Asynchronous Scheduler
This is a structure that takes synchronous agents (Mealy Machines here) and an oracle as a source of non-determinism and act as a whole asynchronous system. It can run a single step or a sequence as if it was a Mealy Machine.

## Oracle
It is a source of non-determinism for the activation of agents at each step for the scheduler. Can be inherited to model different types of oracle: fully random, constant, ...
