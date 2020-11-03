# Great thanks to the sources I gathered some code from:
# - http://radtek.ca/blog/delete-old-email-messages-programatically-using-python-imaplib/
# - https://stackoverflow.com/questions/6225763/downloading-multiple-attachments-using-imaplib
# - https://stackoverflow.com/questions/43857002/script-in-python-to-download-email-attachments

import imaplib, datetime, random, email, os, configparser, time, requests
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
            self.server = server
            self.user = user
            self.password=password
        except Exception as e:
            print(e)
            print("Could not connect to mail server")
            self.m=False
            raise Exception("Could not connect to mail server")

    def start(self):
        """Starts the connection to the mailserver

        Raises:
            Exception: Could not connect to mail server
        """
        try:
            self.m = imaplib.IMAP4_SSL(self.server)
            self.m.login(self.user, self.password)
        except Exception as e:
            print(e)
            print("Could not connect to mail server")
            raise Exception("Could not connect to mail server")
    
    def stop(self):
        """Stops the connection to the mailserver
        """
        self.m.close()
        self.m.logout()

    def downloadAttachmentsInEmail(self, emailid):
        """Downloads the attachments to a local disk

        Args:
            emailid (int): received mail identifier one on a time
        """
        resp, data = self.m.fetch(emailid, "(BODY.PEEK[])")
        email_body = data[0][1]
        mail = email.message_from_bytes(email_body)
        filenames = ""

        if mail.get_content_maintype() != 'multipart':
            return
        for part in mail.walk():
            if part.get_content_maintype() != 'multipart' and part.get('Content-Disposition') is not None:
                open("attachments" + '/' + part.get_filename(), 'wb').write(part.get_payload(decode=True))
                filenames+=part.get_filename()+"<br>"

        if config['pushover']['use'] == "yes":
            msg="New files uploaded via Mail from <br>"
            msg+=str(mail["from"])
            msg+="<br><br>"
            msg+=filenames

            self.sendToPushover(msg, 0, config['pushover']['token'], config['pushover']['user'])


    def run(self):
        """Runner for the attachment download, call this function

        Returns:
            False: if there is an exception
        """
        try:
            self.start()
        except:
            return False
        self.m.select()
        self.m.select("Inbox")
        typ, msgs = self.m.search(None, 'UnSeen')
        msgs = msgs[0].split()
        for emailid in msgs:
            response, data = self.m.store(emailid, '+FLAGS','\\Seen')
            self.downloadAttachmentsInEmail(emailid)
        self.stop()

    def move_to_trash_before_date(self,days_before):
        """Deletes old mails in the inbox

        Args:
            days_before (int): mails since this day before today will be deleted

        Returns:
            False: if there is an exception
        """
        try:
            self.start()
        except:
            return False
        self.m.select()
        self.m.select("Inbox")
        before_date = (datetime.date.today() - datetime.timedelta(days_before)).strftime("%d-%b-%Y")  # date string, 04-Jan-2013
        typ, data = self.m.search(None, '(SINCE {0})'.format(before_date))  # search pointer for msgs before before_date
        msgs = data[0].split()
        for emailid in msgs:
            response, data = self.m.store(emailid, '+FLAGS','\\Deleted')
        self.m.expunge()
        self.stop()

    def sendToPushover(self, message, cnt, token, user):
        url="https://api.pushover.net/1/messages.json" #url to push to
        cnt2 = 0 
        if len(message) > 1000:
            length = len(message)
            message2 = message[0:length-1000]
            cnt2 = 1
            message = message[length-1000:length]
            title2 = title
            title = '+ ' + str(title)
        payload = {'token': token, 'user': user, 'message': message, 'html': 1, 'title': "New file uploaded", 'priority': 0}
        try:
            response = requests.post(url, data=payload)
        except:
            return False

        if cnt2 > 0:
            cnt = 1
            self.sendToPushover(message2, title2, '', '', 0, cnt)


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
        """Uploads all attachments to the cloud

        Args:
            dir (string): existing directory to save the files to

        Returns:
            False: if something went wrong
        """
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
    if datetime.datetime.now()-last > datetime.timedelta(minutes=2):
        print("run")
        last = datetime.datetime.now()
        try:
            ma.run()
            d.uploadAll(config['dav']['save_path'])
            ma.move_to_trash_before_date(7)
        except Exception as e:
            print(e)
            ma = Mailer(config['email']['imap_host'], config['email']['imap_user'], config['email']['imap_password'])
            d = Dav(config['dav']['host'], config['dav']['user'], config['dav']['password'])
        time.sleep(120)


