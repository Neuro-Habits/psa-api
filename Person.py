class Person():
    def __init__(self,
                 email,
                 firstname=None,
                 lastname=None,
                 score=None):
        
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.score = score