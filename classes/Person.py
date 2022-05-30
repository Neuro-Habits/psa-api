class Person():
    def __init__(self,
                 email,
                 firstname=None,
                 lastname=None,
                 **kwargs):

        self.firstname = firstname
        self.lastname = lastname
        self.email = email

        self.__dict__.update(kwargs)