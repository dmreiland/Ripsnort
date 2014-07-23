#!/usr/bin/env python
# -*- coding: utf-8 -*-


import smtplib
from email.mime.text import MIMEText

class EmailSMTP:
    def __init__(self,params):
        self.server = params['smtp_server']
        self.username = params['smtp_username']
        self.password = params['smtp_password']
        self.port = params['smtp_port']
        self.destination_email = params['smtp_destination_email']
        self.source_email = params['smtp_source_email']
        
        self.smtp = smtplib.SMTP_SSL(self.server,self.port)
        self.smtp.login(self.username,self.password)
        
    def __del__(self):
        self.smtp.quit()
    
    def notifyEvent(self,title,message):
        m = MIMEText(message)

        m['Subject'] = title
        m['From'] = self.source_email
        m['To'] = self.destination_email

        self.smtp.sendmail(self.source_email,self.destination_email,m.as_string())
