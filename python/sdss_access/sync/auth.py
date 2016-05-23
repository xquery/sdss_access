from netrc import netrc
from getpass import getpass

""" add the following username and password to your ~/.netrc file
    and remember to chmod 600 ~/.netrc

machine data.sdss.org
    login sdss
    password ***-******
"""

class Auth:

    def __init__(self, netloc=None, public=False, verbose=False):
        self.public = public
        self.verbose = verbose
        self.set_netloc(netloc=netloc)
        self.set_netrc()
        
    def set_netrc(self):
        try: self.netrc = netrc() if not self.public else None
        except: self.netrc = None

    def set_netloc(self, netloc=None):
        self.netloc = netloc

    def set_username(self, username=None):
        self.username = username

    def set_password(self, password=None, inquire=False):
        self.password = getpass("Password: ") if inquire else password

    def ready(self):
        return self.username and self.password

    def load(self):
        if self.netloc and self.netrc:
            authenticators = self.netrc.authenticators(self.netloc)
            self.set_username(authenticators[0])
            self.set_password(authenticators[2])
            if self.verbose: print "authentication for netloc=%r set for username=%r " % (self.netloc,self.username)
        else:
            self.set_username()
            self.set_password()
