from flask import Flask,url_for,render_template,request,flash,redirect,session
import re
import pymysql
import bcrypt
import base64

import os


app=Flask(__name__)
app.secret_key='hospital'

# app.config['MYSQL_HOST']='localhost'
# app.config['MYSQL_USER']='root'
# app.config['MYSQL_PASSWORD']=''
# app.config['MYSQL_DB']='hospital'


connection=pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='Hospital'
)


# mysql=MySQL(app)


# @app.route('/')
# def home():
#     return render_template('index.html')


@app.route('/register',methods=['POST','GET'])
def register():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        password=request.form['password']
        confirm=request.form['confirm']
        choice=request.form['choices']
        if username==''or email==''or password==''or confirm=='' or choice=='':
            flash('All fields are required','danger')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif password!=confirm:
            flash('Passwords do not match','danger')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif len(password)<8:
            flash('Password should be more than 8 characters','danger')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif not re.search("[a-z]",password):
            flash('Password should contain small letters','danger')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        elif not re.search("[A-Z]", password):
            flash('Password should contain capital letters','danger')
            return render_template('register.html',username=username,email=email,password=password,confirm=confirm)
        else:
            hashed_password=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cur=connection.cursor()
            cur.execute("INSERT INTO users(username,email,password,choice)VALUES(%s,%s,%s,%s)",(username,email,hashed_password,choice))
            connection.commit()
            cur.close()
            flash(f"Account created  for {username}",'success')
            return redirect(url_for('login'))
    return render_template('register.html')



@app.route('/login',methods=['POST','GET'])
def login():
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']

        cur=connection.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s",(username,))
        connection.commit()
        user=cur.fetchone()
        cur.close()
        if user is not None:
            hashed_password=user[3].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                session['loggedin']=True
                session['username']=user[1]
                session['user_id']=user[0]
                flash(f"You are logged in as {username} ",'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password','danger')
                return render_template('login.html',username=username,password=password)
        else:
            flash('Incorrect username','danger')
            return render_template('login.html',username=username,password=password)
    return render_template('login.html')




@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        user_id = session['user_id']
        cur = connection.cursor()

        cur.execute("SELECT choice FROM users WHERE id=%s", (user_id,))
        result = cur.fetchone()[0]

        cur.execute("SELECT * FROM schedule WHERE user_id=%s", (user_id,))
        data = cur.fetchall()

        if result == 'Doctor':
            doctor = session['username']
            cur.execute("SELECT * FROM appointment WHERE doctor=%s", (doctor,))
            appointment = cur.fetchall()
            cur.close()
            return render_template('dashboard.html', result=result, data=data, appointment=appointment)
        
        elif result == 'Patient':
            username = session['username']
            cur.execute("SELECT * FROM appointment WHERE username=%s", (username,))
            history = cur.fetchall()

            cur.execute("SELECT * FROM schedule")
            data = cur.fetchall()

            cur.close()
            return render_template('dashboard.html', result=result, data=data, history=history)

        cur.close()
        return render_template('dashboard.html', result=result, data=data)

@app.route('/add',methods=['POST','GET'])
def add():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        user_id=session['user_id']
        doctor=session['username']
        if request.method=='POST':
            day=request.form['day']
            early=request.form['early']
            morning=request.form['morning']
            afternoon=request.form['afternoon']
            evening=request.form['evening']
            cur=connection.cursor()
            cur.execute("INSERT INTO schedule(user_id,doctor,day,early,morning,afternoon,evening)VALUES(%s,%s,%s,%s,%s,%s,%s)",(user_id,doctor,day,early,morning,afternoon,evening))
            connection.commit()
            flash('Schedule added successfuly','success')
            return redirect(url_for('dashboard'))
    return render_template('add.html')



@app.route('/update/<id>', methods=['POST', 'GET'])
def update(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            day = request.form['day']
            early = request.form['early']
            morning = request.form['morning']
            afternoon = request.form['afternoon']
            evening = request.form['evening']
            cur = connection.cursor()
            cur.execute("UPDATE schedule SET day=%s, early=%s, morning=%s, afternoon=%s, evening=%s WHERE id=%s",
                        (day, early, morning, afternoon, evening,id,))
            connection.commit()
            cur.close()
            flash('Schedule updated successfully', 'success')
            return redirect(url_for('dashboard'))
        
        cur = connection.cursor()
        cur.execute("SELECT * FROM schedule WHERE id=%s", (id,))
        results = cur.fetchone()
        connection.commit()
        cur.close()
        
        if results is not None:
            day = results[3]
            early = results[4]
            morning = results[5]
            afternoon = results[6]
            evening = results[7]
            return render_template('update.html', day=day, early=early, morning=morning, afternoon=afternoon, evening=evening)
        else:
            flash('No schedule found', 'error')
            return redirect(url_for('dashboard'))
    return render_template('update.html')


@app.route('/delete/<id>')
def delete(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        cur = connection.cursor()
        cur.execute("DELETE  FROM schedule WHERE id=%s", (id,))
        connection.commit()
        cur.close()
        flash('Schedule deleted successfully', 'success')
        return redirect(url_for('dashboard'))


@app.route('/book/<id>', methods=['POST', 'GET'])
def book(id):
    if 'user_id' and 'username' not in session:
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            doctor=request.form['doctor']
            name=request.form['name']
            email=request.form['email']
            phone=request.form['phone']
            time=request.form['time']
            address=request.form['address']
            cur = connection.cursor()
            username=session['username']
            cur.execute("INSERT INTO appointment(doctor,username,name,email,phone,time,address)VALUES(%s,%s,%s,%s,%s,%s,%s)",(doctor,username,name,email,phone,time,address))
            connection.commit()
            flash('Appointment made successfully', 'success')
            return redirect(url_for('dashboard'))
        user_id=session['user_id']
        cur = connection.cursor()
        cur.execute("SELECT * FROM schedule WHERE id=%s",(id,))
        data = cur.fetchone()
        cur.close()
        if data is not None:
            doctor=data[2]
        return render_template('book.html',doctor=doctor)


@app.route('/profile', methods=['POST', 'GET'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            user_id = session['user_id']
            username = request.form['username']
            email = request.form['email']
            address = request.form['address']
            address2 = request.form['address2']
            city = request.form['city']
            state = request.form['state']
            zipcode = request.form['zip']

            file=request.files['image']
            if file:
                cur = connection.cursor()
                cur.execute("UPDATE users SET image=%s WHERE id=%s",(file.read() ,user_id))
                connection.commit()
                cur.close() 
            
            cur = connection.cursor()
            cur.execute("UPDATE users SET username=%s,email=%s,address=%s, address2=%s, city=%s, state=%s, zipcode=%s WHERE id=%s",
                        (username,email,address, address2, city, state, zipcode, user_id))
            connection.commit()
            cur.close()
            
            flash('Details updated successfully', 'success')
            
        user_id = session['user_id']
        cur = connection.cursor()
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone() 
        cur.close()
        
        if user:
            username = user[1]
            email = user[2]
            address = user[5]
            address2 = user[6]
            city = user[7]
            state = user[8]
            zipcode = user[9]
            image=user[10]
            image_base64=base64.b64encode(image).decode('utf-8')
            return render_template('profile.html', username=username, email=email, address=address, address2=address2,
                               city=city, state=state, zipcode=zipcode,image_base64=image_base64)
    
    return render_template('profile.html')

@app.route('/approve/<id>',methods=['POST','GET'])
def approve(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            user_id=request.form['id']
            action=request.form['action']
            cur = connection.cursor()
            cur.execute("UPDATE appointment SET action=%s WHERE id=%s",(action,id,))
            connection.commit()
            cur.close()
            flash('Action updated successfully', 'success')
            return redirect(url_for('dashboard'))
        username=session['username']
        cur = connection.cursor()
        cur.execute("SELECT * FROM schedule")
        data = cur.fetchall()
        cur.execute("SELECT * FROM appointment WHERE id=%s",(id,))
        data = cur.fetchone()
        cur.close()
        if data is not None:
            email=data[4]
            name=data[3]
            user_id=data[0]
            return render_template('approve.html',email=email,name=name,user_id=user_id)
        
        
    
        
    return render_template('approve.html')


@app.route('/labtest/<id>',methods=['POST','GET'])
def labtest(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        if request.method=='POST':
            testname=request.form['name']
            allergies=request.form['allergies']
            medication=request.form['medication']
            testmethod=request.form['method']
            testcost=request.form['cost']
            cur = connection.cursor()
            cur.execute("UPDATE appointment SET testname=%s,allergies=%s,medication=%s,testmethod=%s,testcost=%s WHERE id=%s",(testname,allergies,medication,testmethod,testcost,id,))
            connection.commit()
            cur.close()
            flash('Labtest sent successfully', 'success')
            return redirect(url_for('dashboard'))
        username=session['username']
        cur = connection.cursor()
        cur.execute("SELECT * FROM schedule")
        data = cur.fetchall()
        cur.execute("SELECT * FROM appointment WHERE id=%s",(id,))
        data = cur.fetchone()
        cur.close()
        if data is not None:
            email=data[4]
            name=data[3]
            user_id=data[0]
            return render_template('lab.html',email=email,name=name,user_id=user_id)
        
        
    
        
    return render_template('approve.html')

@app.route('/delete_appointment/<id>')
def del_appointment(id):
    if 'username' not in session:
        return redirect(url_for('login'))
    else:
        cur=connection.cursor()
        cur.execute("DELETE  FROM appointment WHERE id=%s",(id,))
        connection.commit()
        cur.close()
        flash('Appointment deleted successfully','success')
        return redirect(url_for('dashboard'))


@app.route('/logout')
def logout():
    if 'username' in session:
        session.pop('loggedin',None)
        session.pop('username',None)
        session.pop('user_id',None)
        flash('You have been logged out','warning')
    return redirect(url_for('login'))


if __name__=='__main__':
    app.run(debug=True)