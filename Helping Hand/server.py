from flask import Flask, request, render_template, redirect, url_for, flash,session
import os
from werkzeug.utils import secure_filename
import pymysql
from flask_mysqldb import *

app = Flask(__name__)
mysql=MySQL(app)
app.secret_key = "your_secret_key"

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed extensions for file upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


# MySQL Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'sshawn7820@'
app.config['MYSQL_DB'] = 'helpinghand'

# Function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# Volunteer registration route
@app.route('/volunteer', methods=['GET', 'POST'])
def volunteer():
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        age = request.form.get('age')
        gender = request.form.get('req')
        address = request.form.get('add')
        phone = request.form.get('phone')
        password = request.form.get('password')

        # Handle image upload
        file = request.files['image']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            flash('Invalid image file. Please upload a valid image.')
            return redirect(request.url)

        # Save data to database
        try:
            conn = db.connect()
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO volunteer (image, name, age, phone, address, password)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                cursor.execute(sql, (filename, name, age, phone, address, password))
            conn.commit()
            flash('Your account request is now pending for approval. Please wait for confirmation.')
        except Exception as e:
            flash(f"An error occurred: {e}")
        finally:
            conn.close()

        return redirect(url_for('volunteer'))

    return render_template('volunteer.html')

@app.route('/donor', methods=['GET', 'POST'])
def donor_login():
    if request.method == 'POST':
        username = request.form.get('name')
        password = request.form.get('pass')

        try:
            conn = db_connection()
            with conn.cursor() as cursor:
                sql = "SELECT * FROM donor WHERE username=%s AND password=%s"
                cursor.execute(sql, (username, password))
                result = cursor.fetchone()

                if result:
                    session['user'] = result['username']
                    flash('Login successful!', 'success')
                    return redirect(url_for('donor_dashboard'))
                else:
                    flash('Incorrect username or password. Please try again.', 'danger')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        finally:
            conn.close()

    return render_template('donor.html')

@app.route('/donor/dashboard')
def donor_dashboard():
    if 'user' in session:
        return f"Welcome, {session['user']}! This is your dashboard."
    else:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('donor_login'))

@app.route('/agent', methods=['GET', 'POST'])
def agent_login():
    if request.method == 'POST':
        name = request.form.get('name')
        password = request.form.get('password')

        try:
            conn = db_connection()
            with conn.cursor() as cursor:
                sql = "SELECT agent_id, name, password FROM agent WHERE name=%s AND password=%s"
                cursor.execute(sql, (name, password))
                agent = cursor.fetchone()

                if agent:
                    session['agent_id'] = agent['agent_id']
                    flash('Login successful!', 'success')
                    return redirect(url_for('agent_profile', agent_id=agent['agent_id']))
                else:
                    flash('Incorrect username or password. Please try again.', 'danger')
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        finally:
            conn.close()

    return render_template('agent.html')


@app.route("/admin")
def login():
   return render_template("admin.html")


@app.route("/admin", methods=['post'])
def createsession():
   username = request.form['username']
   password = request.form['password']
   dbconn = mysql.connect
   cursor = dbconn.cursor()
   cursor.execute('select username, password from admin where username = %s and password = %s', (username, password,))
   user = cursor.fetchone()
   if user:
      session['loggedin'] = True
      session['username'] = user[0]
      return render_template("admin_profile.html", message = 'Logged in successfully.')
   else:
      return render_template("admin.html", message = 'Incorrect username or password.')


@app.route("/showpage")
def showpage():
    if 'loggedin' in session:
        return render_template("showpage.html", username=session['username'])
    else:
        flash("Please log in first!")
        return redirect(url_for("login_page"))    
   
@app.route("/admin_profile")
def admin_profile():
    if 'loggedin' in session:
        return render_template("admin_profile.html", username=session['username'])
    else:
        flash("Please log in first!")
        return redirect(url_for("admin"))


# Route for Agent Profile
@app.route('/agent/profile/<int:agent_id>')
def agent_profile(agent_id):
    if 'agent_id' in session and session['agent_id'] == agent_id:
        try:
            conn = db_connection()
            with conn.cursor() as cursor:
                sql = "SELECT * FROM agent WHERE agent_id=%s"
                cursor.execute(sql, (agent_id,))
                agent = cursor.fetchone()
                if agent:
                    return render_template('agent_profile.html', agent=agent)
        except Exception as e:
            flash(f"An error occurred: {e}", 'danger')
        finally:
            conn.close()

    flash('Unauthorized access. Please log in first.', 'warning')
    return redirect(url_for('agent.html'))

# Route to Logout
@app.route('/logout')
def logout():
    session.pop('agent_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('agent.html'))


if __name__ == '__main__':
    app.run(debug=True)
