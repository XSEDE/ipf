


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

class ReadDocumentError(IpfError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class WriteDocumentError(IpfError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class AgentError(IpfError):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
