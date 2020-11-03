# Mail-to-Cloud
Copy your email attachments to a WebDAV Cloud. 

Features:
* Pushover notification for new uploads
* Imap connection to the mail server
* Auto-delete of emails after 7 days
* Upload via WebDAV

## Installation

### manual installation

1. Install all dependencies python 3 and `pip install webdavclient3` will be the mostly needed ones
2. Adapt the `os.chdir` in the beginning of the `run.py` to the current folder
3. Make a subdirectory called `attachments`
4. Fill the `settings.ini` 
5. Run the `run.py` it will scan the mails all 2 minutes

### installation via docker-compose

1. Make a directory where you want
2. Add a `settings.ini` and fill it with your data (example is here in the repository)
3. Make a `docker-compose.yml` like this:
```
version: '2'

services:
  mailtocloud:
    image: 'cubicrootxyz/mail-to-cloud:latest'
    volumes:
      - ./settings.ini:/opt/app/settings.ini
    restart: always
```
4. Run `docker-compose up -d`

## Settings

### DAV

This section is related to the WebDAV connection

`host:` the WebDAV host domain or IP, use `https` for SSL encryption

`user`: the WebDAV username

`password`: password for the WebDAV user

`save_path`: path where the subfolder structure (year -> month-day -> file) is created and the attachments are uploaded

### Email

`imap_host`: host for the IMAP connection

`imap_user`: usernamen for the IMAP connection

`imap_password`: password the the IMAP user

### pushover

`use`: use `yes` if you want to use pushover notifications, else `no`

`token`: Pushover token

`user`: Pushover user
