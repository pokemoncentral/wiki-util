import logging

class RenderEntry:
    '''Class to represent a single render entry.'''

    # GEN_KEYS are shifted by one: index i correspond to gen i+1
    GEN_KEYS = [["Y"], ["C"], ["FRLG", "E"], ["HGSS", "PtHGSS"], ["B2W2"], ["ORAS"], ["USUL", "LGPE"], []]

    @staticmethod
    def has_right_delims(s):
        return s.startswith("[[€") and s.endswith("£]]")

    @staticmethod
    def print_named_param(k, v):
        '''Print a named parameter given its key and value.'''
        return str(k) + "=" + str(v)

    def __init__(self, param_string):
        '''
        param_string can be
            - a string or something that can be transformed into it.
                In this case should be a render entry and MUST contain
                generation and ndex.
        '''
        # Make sure that param_string is a string
        param_string = str(param_string).strip()
        if not self.has_right_delims(param_string):
            logging.error("entry string not surronded by the right delimiters:\n%s", param_string)
            raise ValueError("Entry string not surronded by the right delimiters: \"" + param_string + "\"")
        # Positional args of the entry
        self.pos_args = []
        # Named arguments of the entry
        self.named_args = {}
        for arg in param_string[3:-3].split('|'):
            i = arg.find('=')
            if i == -1:
                self.pos_args.append(arg.strip())
            else:
                self.named_args[arg[:i]] = arg[i + 1:].strip()

    @classmethod
    def new_empty(cls, move_gen, ndex, curr_gen):
        '''Create a new, empty entry.

        move_gen  is the move in which the gen was introduced
        ndex      is the ndex of the entry
        curr_gen  is current generation, required to fill with empty values
                  the entry
        '''
        self = cls.__new__(cls)
        g = str(move_gen)
        ndex = str(ndex).zfill(3)
        # Positional args of the entry
        self.pos_args = [g, ndex]
        for g in range(move_gen, curr_gen + 1):
            self.__add_arg("no")
        # Named arguments of the entry
        self.named_args = {}
        return self

    def __print_named_args(self):
        res = []
        for k, v in self.named_args.items():
            res.append(str(k) + "=" + str(v))
        return '|'.join(res)

    def __str__(self):
        '''Get the string representation to be put back in the result.'''
        params = self.pos_args[0:2]
        for gen, val in enumerate(self.pos_args[2:]):
            params.append(val)
            for key in self.GEN_KEYS[gen - self.get_gen() - 1]:
                if key in self.named_args:
                    params.append(self.print_named_param(key, self.named_args[key]))
        ALL_GAME_KEYS = [game for gen in RenderEntry.GEN_KEYS for game in gen]
        params.extend([self.print_named_param(k, v)
                         for k, v in self.named_args.items()
                         if k not in ALL_GAME_KEYS])

        return "[[€" + '|'.join(params) + "£]]"


    def get_gen(self):
        '''Get the gen of the entry.'''
        return int(self.pos_args[0])

    def get_ndex(self):
        '''Get the ndex of the entry as a string.'''
        return self.pos_args[1]

    def get_ndex_num(self):
        '''Get the ndex of the entry (either a number or a string).'''
        try:
            return int(self.get_ndex())
        except ValueError:
            return self.get_ndex()

    def __get_gen_n_index(self, g):
        '''Get the index at which gen g value is found.'''
        # 2 indices fixed, then g - self_gen
        return 2 + g - self.get_gen()

    def has_gen_n(self, g):
        '''Check whether the entry has values for gen g or not.'''
        # The expected idx should be withing the list and not one of the
        # first two (reserved) parameters
        return 2 <= self.__get_gen_n_index(g) < len(self.pos_args)

    def update_gen_n(self, g, newval):
        '''Update the value for gen g.'''
        self.pos_args[self.__get_gen_n_index(g)] = newval

    def __add_arg(self, value, key=None):
        '''Add an arg to the entry.

        if key is specified is added with that key (possibly overriding).
        Otherwise is added as the last positional argument.
        '''
        if key:
            self.named_args[key] = value
        else:
            self.pos_args.append(value)

# class TutorEntry(RenderEntry):
#     '''Class to represent a single tutor render entry.'''
#
#     TUTOR_INDICES = [0, 0, 1, 2, 5, 8, 10, 12, 15, 17]
#
#     @classmethod
#     def new_empty(cls, move_gen, ndex, curr_gen):
#         '''Create a new, empty entry.
#
#         move_gen  is the move in which the gen was introduced
#         ndex      is the ndex of the entry
#         curr_gen  is current generation, required to fill with empty values
#                   the entry
#         '''
#         self = cls.__new__(cls)
#         ndex = str(ndex).zfill(3)
#         # Positional args of the entry
#         self.pos_args = [ndex]
#         for _ in range(1, self.TUTOR_INDICES[move_gen]):
#             self.pos_args.append("X")
#         for _ in range(self.TUTOR_INDICES[move_gen], self.TUTOR_INDICES[curr_gen + 1]):
#             self.pos_args.append("no")
#         # Named arguments of the entry
#         self.named_args = {}
#         return self
#
#     def get_gen(self):
#         '''Get the gen of the entry.'''
#         return -1
#
#     def get_ndex(self):
#         '''Get the ndex of the entry as a string.'''
#         return self.pos_args[0]
#
#     def has_gen_n(self, g):
#         '''Check whether the entry has values for gen g or not.'''
#         return len(self.pos_args) > self.TUTOR_INDICES[g]
#
#     def update_gen_n(self, g, newval):
#         '''Update the value for gen g.'''
#         # expected_len = self.TUTOR_INDICES[g + 1] - self.TUTOR_INDICES[g]
#         # assert(len(newval) == expected_len)
#         self.pos_args[self.TUTOR_INDICES[g]:self.TUTOR_INDICES[g + 1]] = newval
