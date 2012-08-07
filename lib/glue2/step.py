
import ConfigParser

from ipf.step import Step

#######################################################################################################################

class GlueStep(Step):
    def __init__(self):
        Step.__init__(self)

    def _includeQueue(self, queue_name, no_queue_name_return=False):
        if queue_name == None:
            return no_queue_name_return
        if queue_name == "":
            return no_queue_name_return

        try:
            expression = self.params["queues"]
        except KeyError:
            return True

        toks = expression.split()
        goodSoFar = False
        for tok in toks:
            if tok[0] == '+':
                queue = tok[1:]
                if (queue == "*") or (queue == queue_name):
                    goodSoFar = True
            elif tok[0] == '-':
                queue = tok[1:]
                if (queue == "*") or (queue == queue_name):
                    goodSoFar = False
            else:
                self.warning("can't parse part of Queues expression: "+tok)
        return goodSoFar
