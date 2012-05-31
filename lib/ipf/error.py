


##############################################################################################################

class IpfError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ParseError(IpfError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class DocumentError(IpfError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ReadDocumentError(DocumentError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class WriteDocumentError(DocumentError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class StepError(IpfError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class NoMoreInputsError(StepError):
    def __init__(self, value="no more inputs"):
        StepError.__init__(self,value)
        pass
    def __str__(self):
        return repr(self.value)

class WorkflowError(IpfError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
