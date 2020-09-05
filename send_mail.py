   # importing libraries 
from flask import Flask, url_for
from flask_mail import Mail, Message 
from itsdangerous import URLSafeTimedSerializer

s = URLSafeTimedSerializer('Thisisasecret!')

def send_mail(email,app,token):


   mail = Mail(app) # instantiate the mail class 
   
# configuration of mail 
   app.config['MAIL_SERVER']='smtp.gmail.com'
   app.config['MAIL_PORT'] = 465
   app.config['MAIL_USERNAME'] = 'infinitytestmanagement@gmail.com'
   app.config['MAIL_PASSWORD'] = 'assiljaber'
   app.config['MAIL_USE_TLS'] = False
   app.config['MAIL_USE_SSL'] = True
   mail = Mail(app) 
# message object mapped to a particular URL ‘/’ 
   try:  

        link = url_for('confirm_email',token=token, mail=email , _external=True)
        msg = Message( 
		'Email de confirmation', 
		sender ='assil.jaber@esprit.tn', 
		recipients = [email] 
			 ) 
        msg.body = 'Merci de confirmez votre mail en cliquent {}'.format(link)
        mail.send(msg) 
   except Exception as e:
        	print(str(e))
   
