#!/usr/bin/env python3

class StateMachine:
    def __init__(self, name, states, events, initial_state, transition_table):
        """
        Example of State machine transition table:

        {'S1':{'e1':'S2', 
               'e2':'S1', 
               'e3':'S3'},
        'S2':{'e1':'S2',
              'e2':'S3'},
        'S3':{'e1':'S1', 
              'e2':'S2', 
              'e3':'S3'}}
        """
        self.name = name
        self.states = states
        self.events = events
        self.initial_state = initial_state
        self.current_state = self.initial_state
        self.transition_table = transition_table
        self.validity_check()

    def transition(self, event):
        try:
            self.current_state =  self.transition_table[self.current_state][event]
        except KeyError:
            print(f"Error, event not present in the event set for current state{self.current_state}")

    def get_current_state(self): return self.current_state

    def set_current_state(self, state):  self.current_state = state if state in self.states else self.current_state

    def add_event(self, event): self.events+=event 

    def add_state(self, state): self.states+=state 

    def remove_event(self, event):
        try:
            self.events.remove(event)
            for S in self.transition_table.keys():
                if event in self.transition_table[S]:
                    self.transition_table[S].pop(event)
        except:
            pass

    def remove_state(self, state):
        try:
            self.states.remove(state)
            self.transition_table.pop(state)
            for S in self.transition_table.keys():
                for pair in self.transition_table[S].items():
                    if state == pair[1]:
                        self.transition_table[S].pop(pair[0])
        except:
            pass

    def add_transition(self, initial_state,event, final_state):
        try:
            if initial_state in self.states and event in self.events and final_state in self.events:
                self.transition_table[initial_state][event]=final_state
        except:
            print("Error, transition could not be added!")

    def validity_check(self):
        states = self.transition_table.keys()
        try:
            assert self.current_state in states
        except AssertionError:
            print("Error, initial state not present in the state set!")
        try:
            for S in states:
                if S not in self.states:
                    raise ValueError
        except ValueError:
            print("Error, state not present in the state set is present in the transition table!")

        events = [list(self.transition_table[S].keys())[:] for S in states]
        events2 = []
        for e in events: events2+=e
        
        try:        
            for e in set(events2):
                if e not in self.events:
                    raise ValueError
        except ValueError:
            print("Error, event not present in the event set is present in the transition table!")
    
    def reset(self):
        self.current_state = self.initial_state