from flask import Flask, render_template, request, jsonify , session , flash , redirect, logging  
from flask_sqlalchemy import SQLAlchemy
from send_mail import send_mail, s
from flask_cors import CORS, cross_origin
from flask_marshmallow import Marshmallow
from werkzeug.utils import secure_filename
from passlib.hash import  sha256_crypt
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.utils import secure_filename
from uploadfile import upload_file


import urllib.request 
import os


UPLOAD_FOLDER = '/uploads'



app = Flask(__name__) 
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
CORS(app,resources={r"/api/*": {"origins": "*"}})
# Create a directory in a known location to save files to.

uploads_dir = os.path.join('InfinityManagement/src/assets')
os.makedirs(uploads_dir, exist_ok=True)

ENV  = 'dev'



if ENV == 'dev':
    app.debug = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost/infinitymanagement'

else:
    app.debug = False
    app.config['SQLALCHEMY_DATABASE_URI'] = ''

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

ma = Marshmallow(app)

class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30))
    password = db.Column(db.String(30))

    def __init__(self,nom,password):
          self.nom = nom
          self.password = password

class AdminSchema(ma.Schema):
    class Meta:
        fields = ('id','nom','password')

admin_schema = AdminSchema()
admins_schema = AdminSchema(many=True)


class Candidat(db.Model):
    __tablename__ = 'candidat'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(30))
    prenom = db.Column(db.String(30))
    email = db.Column(db.String(200))
    dateNaissance = db.Column(db.Date)
    NumTel = db.Column(db.String(8))
    disponibilite = db.Column(db.Float)
    experience = db.Column(db.Integer)
    CV = db.Column(db.String(200))
    message = db.Column(db.Text())
    etat = db.Column(db.String(30))
    statue = db.Column(db.String(10))

                
    def __init__(self,nom,prenom,email,dateNaissance,NumTel,disponibilite,experience,CV,message,etat,statue):
        self.nom = nom
        self.prenom = prenom
        self.email = email
        self.dateNaissance = dateNaissance
        self.NumTel = NumTel
        self.disponibilite = disponibilite
        self.experience = experience 
        self.CV = CV
        self.message = message
        self.etat= etat
        self.statue = statue
    
#Feedback Schema
class CandidatSchema(ma.Schema):
    class Meta:
        fields = ('id', 'nom','prenom', 'email', 'dateNaissance', 'NumTel','disponibilite','experience','CV','message','etat','statue')

#Init Schema
candidat_schema = CandidatSchema()
candidats_schema = CandidatSchema(many=True)

ALLOWED_EXTENSIONS = set(['txt', 'pdf'])









@app.route('/confirm_email/<token>/<mail>')
def confirm_email(token,mail):
    try:
        candidat = Candidat.query.filter_by(email=str(mail)).first()
      
        candidat.statue = "Confirme"
    
        db.session.commit()


        email = s.loads(token, salt="email_confirm",max_age=3600)
    except SignatureExpired: 
        return '<h1>The token is expired!</h1>'
    return "Email confirmer avec succès "
    
    


@app.route('/api/register', methods=['POST','GET'])
def register_admin():
    if request.method == 'POST':
        userName = request.form['nom']
        print(userName)
        password = sha256_crypt.encrypt(str(request.form['password']))

        new_admin = Admin(userName,password)

        db.session.add(new_admin)
        db.session.commit()

        return admin_schema.jsonify(new_admin)
    
@app.route('/api/login',methods=["GET","POST"])
def login():
    if request.method == "POST":
        #GET from fields
        nom = request.json['nom']
        password_admin = request.json['password']

        #create Cursor

        #Get Admin par identfient
        
        result =  Admin.query.filter_by(nom=nom).count()

        if result > 0:
            
            data = Admin.query.filter_by(nom=nom).first()
            verify = sha256_crypt.verify(password_admin , data.password)

            if verify:
                return jsonify('password matched')

            else:
                return jsonify('password not matched')

        if result == 0:
            return jsonify("Admin not found")
             

@app.route('/api/new', methods=['POST'])
def add_candidat():
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    dateNaissance = request.form['dateNaissance']
    NumTel = request.form['numTel']
    disponibilite = request.form['disponibilite']
    experience = request.form['experience']
    CV = request.files['cv']
    message = request.form['message']
    filename = secure_filename(CV.filename)

    etat = 'Nouvelle'
    statue = 'NonConfirme'
    token = s.dumps(email,salt="email_confirm")
    file = filename
    resultat = Candidat.query.filter_by(email=email).count()
    if resultat > 0:
        return jsonify("email est déjà utiliser")
    
    new_candidat = Candidat(nom,prenom,email,dateNaissance,NumTel,disponibilite,experience,filename,message,etat,statue)
    upload_file(CV)
    CV.save(os.path.join(uploads_dir,CV.filename))
    db.session.add(new_candidat)
    send_mail(email,app,token)
    db.session.commit()
    
    return jsonify("Candidature déposer veuiller confirmer votre email") 




@app.route('/api/getAll', methods=["GET"])
def get_feedbacks():
    all_candidats = Candidat.query.all()
    result = candidats_schema.dump(all_candidats)
    return jsonify(result)

@app.route('/api/get/<id>', methods=["GET"])
def get_candidat(id):
    candidat = Candidat.query.get(id)
    return candidat_schema.jsonify(candidat)

@app.route('/api/triEtat/<etat>',methods=["GET"])
def get_candidatTri(etat):
        candidats = Candidat.query.filter_by(etat=etat).all()

        return candidats_schema.jsonify(candidats)
    
@app.route('/api/triNom/<nom>',methods=["GET"])
def get_candidatNom(nom):
        candidats = Candidat.query.filter_by(nom=nom).all()

        return candidats_schema.jsonify(candidats)


@app.route('/api/triPrenom/<prenom>',methods=["GET"])
def get_candidatPrenom(prenom):
        candidats = Candidat.query.filter_by(prenom=prenom).all()

        return candidats_schema.jsonify(candidats)

@app.route('/api/triMail/<statue>',methods=["GET"])
def get_candidatStatue(statue):
        candidats = Candidat.query.filter_by(statue=statue).all()

        return candidats_schema.jsonify(candidats)
@app.route('/api/confirm/<id>',methods=["PUT"])
def confirm_candidat(id):
    candidat = Candidat.query.get(id)

    nom = request.json['nom']
    prenom = request.json['prenom']
    email = request.json['email']
    dateNaissance = request.json['dateNaissance']
    NumTel = request.json['NumTel']
    disponibilite = request.json['disponibilite']
    experience = request.json['experience']
    CV = request.json['CV']
    message = request.json['message']
    etat = request.json['etat']
    candidat.nom = nom
    candidat.prenom = prenom
    candidat.email = email
    candidat.dateNaissance = dateNaissance
    candidat.NumTel = NumTel
    candidat.disponibilite = disponibilite
    candidat.experience = experience 
    candidat.CV = CV
    candidat.message = message 
    candidat.etat = etat
    
    db.session.commit()

    return candidat_schema.jsonify(candidat)

@app.route('/api/update/<id>',methods=["PUT"])
def update_candidat(id):
    candidat = Candidat.query.get(id)

    nom = request.json['nom']
    prenom = request.json['prenom']
    email = request.json['email']
    dateNaissance = request.json['dateNaissance']
    NumTel = request.json['NumTel']
    disponibilite = request.json['disponibilite']
    experience = request.json['experience']
    CV = request.json['CV']
    message = request.json['message']
    etat = request.json['etat']


    candidat.nom = nom
    candidat.prenom = prenom
    candidat.email = email
    candidat.dateNaissance = dateNaissance
    candidat.NumTel = NumTel
    candidat.disponibilite = disponibilite
    candidat.experience = experience 
    candidat.CV = CV
    candidat.message = message
    candidat.etat = etat

    db.session.commit()

    return candidat_schema.jsonify(candidat)

@app.route('/api/delete/<id>', methods=["DELETE"])
def delete_feedback(id):
    feedback = Feedback.query.get(id)
    db.session.delete(feedback)
    db.session.commit()
    return feedback_schema.jsonify(feedback)


 
        

if __name__ == '__main__':     
       app.run()