import imaplib, datetime, random, email, os, configparser
from webdav3.client import Client
from os import listdir
from os.path import isfile, join

os.chdir("/opt/app")

config = configparser.ConfigParser()
config.read('settings.ini')

class Mailer:
    """Handles the requests with the mail server
    """
    def __init__(self,server, user, password ):
        """Initializes the connection to the mail server

        Args:
            server (string): mail server host (imap)
            user (string): imap user name
            password (string): imap user password
        """
        try:
            self.m = imaplib.IMAP4_SSL(server)
            self.user = user
            self.password=password
            self.m.login(self.user, self.password)
        except Exception as e:
            print(e)
            print("Could not connect to mail server")
            self.m=False
            raise Exception("Could not connect to mail server")

    def downloaAttachmentsInEmail(self, emailid):
        """Downloads the attachments to a local disk

        Args:
            emailid (int): received mail identifier one on a time
        """
        resp, data = self.m.fetch(emailid, "(BODY.PEEK[])")
        email_body = data[0][1]
        mail = email.message_from_bytes(email_body)
        if mail.get_content_maintype() != 'multipart':
            return
        for part in mail.walk():
            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                open("attachments" + '/' + part.get_filename(), 'wb').write(part.get_payload(decode=True))

    def run(self):
        try:
            
            self.m.select()
            self.m.select("Inbox")
            typ, msgs = self.m.search(None, 'UnSeen')
        except Exception as e:
            print(e)
            print("Could not connect to mail server")
            raise Exception("Could not connect to mail server")
            return False
        msgs = msgs[0].split()
        for emailid in msgs:
            response, data = self.m.store(emailid, '+FLAGS','\\Seen')
            self.downloaAttachmentsInEmail(emailid)
        #self.m.logout()

class Dav:
    """A class to handle webdav request for uploading the mail attachments
    """
    def __init__(self, host, user, password):
        """initializes a webdav connection

        Args:
            host (string): host url
            user (string): dav user name
            password (string): dav password
        """

        self.options = {
        'webdav_hostname': host,
        'webdav_login':    user,
        'webdav_password': password
        }
        self.client=Client(self.options)

    def uploadAll(self, dir):
        files = [f for f in listdir("attachments") if isfile(join("attachments", f))]
        year = datetime.datetime.now().strftime("%Y")
        date = datetime.datetime.now().strftime("%m-%d")
        if not year in self.client.list(dir):
            try:
                self.client.mkdir(dir+"/"+year)
            except Exception as e:
                print(e)
                return False
        if not date in self.client.list(dir+"/"+year):
            try:
                self.client.mkdir(dir+"/"+year+"/"+date)
            except Exception as e:
                print(e)
                return False

        for f in files:
            try:
                self.client.upload_sync(remote_path=dir+"/"+year+"/"+date+"/"+str(random.randint(10000,100000))+"_"+f, local_path="attachments/"+f)
                os.remove("attachments/"+f)
            except Exception as e:
                print(e)


ma = Mailer(config['email']['imap_host'], config['email']['imap_user'], config['email']['imap_password'])
d = Dav(config['dav']['host'], config['dav']['user'], config['dav']['password'])
last = datetime.datetime.now()-datetime.timedelta(days=1)

while True:
    if datetime.datetime.now()-last > datetime.timedelta(minutes=1):
        print("run")
        last = datetime.datetime.now()
        try:
            ma.run()
            d.uploadAll(config['dav']['save_path'])
        except Exception as e:
            print(e)
            ma = Mailer(config['email']['imap_host'], config['email']['imap_user'], config['email']['imap_password'])
            d = Dav(config['dav']['host'], config['dav']['user'], config['dav']['password'])


