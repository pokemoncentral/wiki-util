import logging

class RenderEntry:
    '''Class to represent a single render entry.'''

    @staticmethod
    def has_right_delims(s):
        return s.startswith("[[€") and s.endswith("£]]")

    def __init__(self, param_string):
        '''
        param_string can be
            - a string or something that can be transformed into it.
                In this case should be a render entry and MUST contain
                generation and ndex.
        '''
        # Make sure that param_string is a string
        param_string = str(param_string).strip()
        if not RenderEntry.has_right_delims(param_string):
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

    def _print_named_args(self):
        res = []
        for k, v in self.named_args.items():
            res.append(str(k) + "=" + str(v))
        return '|'.join(res)

    def __str__(self):
        '''Get the string representation to be put back in the result.'''
        if self.named_args:
            return ("[[€"
                    + '|'.join(self.pos_args)
                    + '|'
                    + self._print_named_args()
                    + "£]]")
        else:
            return ("[[€"
                    + '|'.join(self.pos_args)
                    + "£]]")


    def get_gen(self):
        '''Get the gen of the entry.'''
        return int(self.pos_args[0])

    def get_ndex(self):
        '''Get the ndex of the entry.'''
        return self.pos_args[1]

    def has_gen_n(self, g):
        '''Check whether the entry has values for gen g or not.'''
        # len >= 3 + j -> has self_gen + j
        # j = g - self_gen
        if g < self.get_gen():
            return False
        return len(self.pos_args) >= 3 + g - self.get_gen()

    def add_arg(self, value, key=None):
        '''Add an arg to the entry.

        if key is specified is added with that key (possibly overriding).
        Otherwise is added as the last positional argument.
        '''
        if key:
            self.named_args[key] = value
        else:
            self.pos_args.append(value)
