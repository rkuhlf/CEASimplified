class PresetException(Exception):
    pass

class UserInputException(Exception):
    pass

class CEAException(Exception):
    pass

class UnknownCEAException(CEAException):
    pass