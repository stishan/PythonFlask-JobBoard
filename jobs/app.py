from flask import Flask, render_template, url_for, g, request, redirect
import datetime
import sqlite3

PATH = "db/jobs.sqlite"
app = Flask(__name__)

#Database related
def open_connection():
	connection = getattr(g, "_connection", None)

	if connection is None:
		connection = g._connection = sqlite3.connect(PATH)
	connection.row_factory = sqlite3.Row

	return connection


def execute_sql(sql, values = (), commit = False, single = False):
	connection = open_connection()

	cursor = connection.execute(sql, values)

	if commit:
		results = connection.commit()
	else:
		results = cursor.fetchone() if single else cursor.fetchall()

	cursor.close()
	return results

@app.teardown_appcontext
def close_connection(exception):
	connection = getattr(g, "_connection", None)

	if connection is not None:
		connection.close()

#Job route
@app.route('/job/<job_id>')
def job(job_id):
	job = execute_sql('SELECT job.id, job.title, job.description, job.salary, employer.id as employer_id, employer.name as employer_name FROM job JOIN employer ON employer.id = job.employer_id WHERE job.id = ?', [job_id], single=True)
	return render_template('job.html', job=job)

#Employer route
@app.route('/employer/<employer_id>')
def employer(employer_id):
	employer = execute_sql('SELECT * FROM employer WHERE id=?', [employer_id], single=True)

	jobs = execute_sql('SELECT job.id, job.title, job.description, job.salary FROM job JOIN employer ON employer.id = job.employer_id WHERE employer.id = ?', [employer_id])

	reviews = execute_sql('SELECT review, rating, title, date, status FROM review JOIN employer ON employer.id = review.employer_id WHERE employer.id = ?', [employer_id])
	return render_template('employer.html', employer=employer, jobs=jobs, reviews=reviews)

#Review route
@app.route('/employer/<employer_id>/review', methods=('GET', 'POST'))
def review(employer_id):

	if request.method == 'POST':
		review = request.form['review']
		rating = request.form['rating']
		title = request.form['title']
		status = request.form['status']

		date = datetime.datetime.now().strftime("%m/%d/%Y")

		execute_sql('INSERT INTO review (review, rating, title, date, status, employer_id) VALUES (?, ?, ?, ?, ?, ?)', (review, rating, title, date, status, employer_id), commit=True)

		return redirect(url_for('employer', employer_id=employer_id))

	return render_template('review.html', employer_id=employer_id)

#Application route
@app.route('/job/<job_id>/application', methods=('GET', 'POST'))
def application(job_id):
	job = execute_sql('SELECT job.id, job.title, job.description, job.salary, employer.id as employer_id, employer.name as employer_name FROM job JOIN employer ON employer.id = job.employer_id WHERE job.id = ?', [job_id], single=True)

	if request.method == 'POST':
		application_type = request.form['application_type']
		info = request.form['info']
		status = request.form['status']
		notice = request.form['notice']

		date = datetime.datetime.now().strftime("%m/%d/%Y")

		execute_sql('INSERT INTO applications(application_type, text, employment_status, terms_of_notice, job_id, application_date) VALUES (?, ?, ?, ?, ?, ?)', (application_type, info, status, notice, job_id, date), commit=True)

		return redirect(url_for('job', job_id=job_id))

	return render_template('application.html', job=job)


#Application
@app.route('/')
@app.route('/jobs')
def jobs():
	jobs = execute_sql('SELECT job.id, job.title, job.description, job.salary, employer.id as employer_id, employer.name as employer_name FROM job JOIN employer ON employer.id = job.employer_id')
	return render_template('index.html', jobs=jobs)

