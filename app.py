######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import time
import datetime

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!


#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'SierraLeone1!'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users") 
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
    try:
        firstname=request.form.get('fname')
        lastname=request.form.get('lname')
        dob=request.form.get('dob')
        email=request.form.get('email')
        password=request.form.get('password')
    except:
        print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test =  isEmailUnique(email)
    if test:
        print cursor.execute("INSERT INTO Users (firstname, lastname, birthDate, email, password) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(firstname, lastname, dob, email, password))
        conn.commit()
        #log user in
        user = User()
        user.id = email
        flask_login.login_user(user)
        return render_template('hello.html', name=email, message='Account Created!')
    else:
        print "couldn't find all tokens"
        return flask.redirect(flask.url_for('register'))
    
def getAlbumPhotos(aid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE albumid = '{0}'".format(aid))
	return cursor.fetchall() #NOTE list of tuples, [(imgdata, pid), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]
 
def getAlbumNameFromAid(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT aname FROM Albums WHERE albumid = '{0}'".format(aid))
    return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
  
def getAlbums(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT albumid, aname, created  FROM Albums WHERE uid = '{0}'".format(uid))
	return cursor.fetchall()
 
def getFriends(uid):
    cursor = conn.cursor()
    cursor.execute("(SELECT user2, nickname FROM Friends WHERE user1 = '{0}')".format(uid))
    return cursor.fetchall()
    
def getName(uid):
    cursor = conn.cursor()
    cursor.execute("(SELECT firstName FROM Users WHERE user_id = '{0}')".format(uid))
    return cursor.fetchone()[0]
    
app.jinja_env.globals.update(getName=getName)
    
def getComments(pid):
    cursor = conn.cursor()
    cursor.execute("(SELECT commenter, body, dp FROM Comments WHERE pid = '{0}')".format(pid))
    data = cursor.fetchall()
    return data
#end login code

@app.route('/myprofile')
@flask_login.login_required
def protected():
	return render_template('hello.html', message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        aid = request.form.get('album')
        imgfile = request.files['photo']
        caption = request.form.get('caption')
        print caption
        photo_data = base64.standard_b64encode(imgfile.read())
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, albumid) VALUES ('{0}', '{1}', '{2}', '{3}' )".format(photo_data,uid, caption, aid))
        conn.commit()
        return render_template('albums.html', message='Photo uploaded!', albums = getAlbums(getUserIdFromEmail(flask_login.current_user.id)))
        #The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('upload.html', albums = getAlbums(getUserIdFromEmail(flask_login.current_user.id)))
#end photo uploading code 
@app.route('/albumcreate', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
    if request.method == 'POST':
        uid = getUserIdFromEmail(flask_login.current_user.id)
        aname = request.form.get('aname')
        print aname
        date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Albums (aname, uid, created) VALUES ('{0}', '{1}', '{2}' )".format(aname, uid, date))
        conn.commit()
        return render_template('hello.html', message='Album Created', albums=getAlbums(uid))
        #The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('createalbum.html')
#end photo uploading code 


#default page  
@app.route("/", methods=['GET'])
def hello():
    return render_template('open.html', message = None)
    
@app.route("/home", methods=['GET'])
@flask_login.login_required
def home():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    return render_template('hello.html', message='Welecome to Photoshare', albums=getAlbums(uid))

@app.route("/album", methods=['GET', 'POST'])
def display_album():
    if request.method == 'POST':
        pid = request.form.get('photo')
        return render_template('comments.html', comments = getComments(pid))
    else:
        aid = request.form.get('album')
        return render_template('albumview.html', photos = getAlbumPhotos(aid), aname = getAlbumNameFromAid(aid))    

@app.route('/myalbums', methods=['GET', 'POST'])
@flask_login.login_required
def my_albums():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    if request.method == 'POST':
        aid = request.form.get('album')
        return render_template('albumview.html', photos=getAlbumPhotos(aid), aname=getAlbumNameFromAid(aid))
        #The method is GET so we return a  HTML form to upload the a photo.
    else:
        return render_template('albums.html', albums = getAlbums(uid))
        
@app.route('/myfriends', methods=['GET', 'POST'])
@flask_login.login_required
def my_friends():
    if request.method == 'POST':
        uid = request.form.get('user')
        return render_template('profile.html', albums=getAlbums(uid), aname = getName(uid))
    else:
        return render_template('friends.html', friends = getFriends(getUserIdFromEmail(flask_login.current_user.id)))

@app.route('/addfriend', methods=['GET', 'POST'])
@flask_login.login_required
def add_friend():
    if request.method == 'POST':
        user1 = getUserIdFromEmail(flask_login.current_user.id)
        email = request.form.get('email')
        user2 = getUserIdFromEmail(email)
        nickname = request.form.get('nickname')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Friends (user1, user2, nickname) VALUES ('{0}', '{1}', '{2}')".format(user1, user2, nickname))
        return render_template('friends.html', message = 'Friend added!', friends = getFriends(getUserIdFromEmail(flask_login.current_user.id)))
    else:
        return render_template('addfriend.html', friends = getFriends(getUserIdFromEmail(flask_login.current_user.id)))
        
@app.route('/profile', methods=['POST'])
def profile():
        aid = request.form.get('album')
        return render_template('albumview.html', aname = getAlbumNameFromAid(aid), photos = getAlbumPhotos(aid))

@app.route('/post_comment', methods=['POST'])
def post_comment():
    uid = getUserIdFromEmail(flask_login.current_user.id)
    pid = request.form.get('photo')
    comment = request.form.get('comment')
    date = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO Comments (commenter, pid, body, dp) VALUES ('{0}', '{1}', '{2}', '{3}')".format(uid, pid, comment, date))
    return render_template('comments.html', message = 'Comment Posted!', comments = getComments(pid))

    
if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
