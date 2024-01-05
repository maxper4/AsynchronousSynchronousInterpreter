import random

# It will be our "synchronous language"
# We assume every variable is of type int
# We assume states, inputs and outputs are dictionaries of variables ~= valuation function
class MealyMachine():
    def __init__(self, state, output, next_state, inputs_variables, outputs_variables):
        self.initial_state = state
        self.state = state
        self.output = output
        self.next_state = next_state
        self.states_variables = state.keys()
        self.inputs_variables = inputs_variables
        self.outputs_variables = outputs_variables

    # run the machine with the given input once: update the state and return the output
    def run(self, input):
        output = self.output(self.state, input)
        next_state = self.next_state(self.state, input)
        self.state = next_state
        return output
    
    # run the machine multiple times with the given input sequence
    def run_sequence(self, input_sequence):
        output_sequence = []
        for input in input_sequence:
            output_sequence.append(self.run(input))
        return output_sequence

    # compose two machines in parallel
    def compose(self, other):
        this_dependances = [x for x in other.outputs_variables if x in self.inputs_variables]
        other_dependances = [x for x in self.outputs_variables if x in other.inputs_variables]

        # this is a basic cycle detection, it is not perfect but it is enough for the purpose of asynchronisation in synchronous language
        if len([x for x in this_dependances if x in other_dependances]) > 0:
            raise Exception("Cycle detected in composed machine")
    
        def composed_output(state, input):
            temp_ouput = self.output(state, input)
            for key in other_dependances:
                input[key] = temp_ouput[key]
            other_output = other.output(state, input)
            if other_output == "bot":
                return temp_ouput
            if temp_ouput == "bot":
                return other_output
            
            for key in other.outputs_variables:
                temp_ouput[key] = other_output[key]
            return temp_ouput

        def composed_next_state(state, input):
            init_state = state.copy()    # to prevent state variable to disappear if there is a bot
            state = {**init_state, **self.next_state(state, input) }
            temp_ouput = self.output(state, input)
            for key in other_dependances:
                input[key] = temp_ouput[key]
            temp_state = other.next_state(state, input)
            for key, value in temp_state.items():
                state[key] = value 
            return state
        
        return MealyMachine({**self.initial_state, **other.initial_state}, composed_output, composed_next_state, 
                            self.inputs_variables + other.inputs_variables, self.outputs_variables + other.outputs_variables)
    
    # asynchronise the machine with respect to the given variable
    def asynchronise(self, var):
        new_output = lambda state, input: self.output(state, input) if input[var] == 1 else "bot"
        new_next_state = lambda state, input: self.next_state(state, input) if input[var] == 1 else state

        return MealyMachine(self.initial_state, new_output, new_next_state, self.inputs_variables + [var], self.outputs_variables)
 
 # It will be a scheduler to run asynchronously machines in the synchronous language
class AsynchronousScheduler():
    def __init__(self, machines, oracle):
        self.machines = machines
        self.oracle = oracle

        self.system = self.machines[0]
        for i in range(1, len(machines)):
            self.system = self.system.compose(machines[i].asynchronise("c" + str(i)))

    # run the whole system with the given input once
    def run(self, input):
        activations = self.oracle.get_activations()
        return self.system.run({**input, **activations})
    
    # run the whole system with the given input sequence
    def run_sequence(self, input_sequence):
        output_sequence = []
        for input in input_sequence:
            output_sequence.append(self.run(input))
        return output_sequence
    
# It will be an oracle to activate variables in the asynchronous language
class Oracle():
    def get_activations(self):
        return {}
    
# It will be a random oracle to activate variables with a given probability at each step
class RandomOracle(Oracle):
    def __init__(self, nbVariables, probability):
        self.nbVariables = nbVariables
        self.probability = probability
    
    def get_activations(self):
        activations = {}
        for i in range(self.nbVariables):
            activations["c" + str(i)] = 1 if random.random() < self.probability else 0
        return activations

additioner = MealyMachine({ "s": 0 }, lambda state, input: { "s": state["s"] + input["sum"]}, 
                          lambda state, input: { "s": state["s"] + input["sum"] },
                          ["sum"], ["s"]
                          )

pre = MealyMachine({"prev": 0 }, 
                   lambda state, input: { "prev": state["prev"] }, 
                   lambda state, input: { "prev": input["i"] }, 
                   ["i"], ["prev"])     # prev(i) of Lustre

def sampler_fct(state, input):
    (i, b) = (input["i"], input["b"])
    if b == 1:
        return i
    else:
        return state

sampler = MealyMachine({}, sampler_fct, sampler_fct,
                        ["i", "b"], ["val"])        # current(i when b) of Lustre

compose1 = additioner.compose(pre)
compose2 = additioner.compose(sampler)

print(additioner.run_sequence([{"sum": 1}, {"sum": 2}, {"sum": 1}, {"sum": 2}, {"sum": 1}]))
print(sampler.run_sequence([{"i": {"val": 1}, "b": 1}, {"i": {"val": 2}, "b": 0}, {"i": {"val": 3}, "b": 1}, {"i": {"val": 4}, "b": 0}, {"i": {"val": 5}, "b": 1}]))
print(pre.run_sequence([{"i": 1}, {"i": 2}, {"i": 3}, {"i": 4}, {"i": 5}]))
print(compose1.run_sequence([{"sum": 1, "i": 1}, {"sum": 2, "i": 2}, {"sum": 1, "i": 3}, {"sum": 2, "i": 4}, {"sum": 1, "i": 5}]))
print(compose2.run_sequence([{"sum": 1, "i": {"val": 1}, "b": 1}, {"sum": 2, "i": {"val": 2}, "b": 0}, {"sum": 1, "i": {"val": 3}, "b": 1}, {"sum": 2, "i": {"val": 4}, "b": 0}, {"sum": 1, "i": {"val": 5}, "b": 1}]))

async_additioner = additioner.asynchronise("c1")
print(async_additioner.run_sequence([{"sum": 1, "c1": 1}, {"sum": 2, "c1": 0}, {"sum": 1, "c1": 1}, {"sum": 2, "c1": 0}, {"sum": 1, "c1": 1}]))

async_pre = pre.asynchronise("c2")
print(async_pre.run_sequence([{"i": 1, "c2": 1}, {"i": 2, "c2": 0}, {"i": 3, "c2": 1}, {"i": 4, "c2": 0}, {"i": 5, "c2": 1}]))

compose_async = async_additioner.compose(async_pre)
print(compose_async.run_sequence([{"sum": 1, "i": 1, "c1": 1, "c2": 1}, 
                                  {"sum": 2, "i": 2, "c1": 0, "c2": 1}, 
                                  {"sum": 1, "i": 3, "c1": 1, "c2": 0}, 
                                  {"sum": 2, "i": 4, "c1": 0, "c2": 0}, 
                                  {"sum": 1, "i": 5, "c1": 1, "c2": 1}]))

scheduler = AsynchronousScheduler([additioner, pre], RandomOracle(2, 0.5))
print(scheduler.run_sequence([{"sum": 1, "i": 1}, {"sum": 2, "i": 2}, {"sum": 1, "i": 3}, {"sum": 2, "i": 4}, {"sum": 1, "i": 5}]))