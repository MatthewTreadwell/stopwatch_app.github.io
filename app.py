from flask import Flask, render_template, request, session, make_response, redirect, url_for
import json
from datetime import datetime, timedelta
import bcrypt
from dotenv import load_dotenv
import os
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("SECRET_KEY")

@app.route("/")
def home():
    return render_template("login_screen.html")

@app.route("/create_account", methods=["POST"])
def create_account():
    username = request.form["new_username"]
    password = request.form["new_password"].encode('utf-8')
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    if username not in [user['username'] for user in file]:
        s = bcrypt.gensalt()
        h = bcrypt.hashpw(password, s)
        item = {'username' : username, 'password_hash' : h.decode('utf-8'), 'projects' : [], 'sessions' : []}
        file.append(item)
        with open(os.path.join(basedir, "Users.json"), "w") as f:
            json.dump(file, f)
        with open(os.path.join(basedir, "Users.json"), "r") as f:
            file = json.load(f)
        username_list = [user['username'] for user in file]
        session["user_index"] = username_list.index(username)
        return redirect(url_for("return_to_dash"))
    else:
         return render_template("login_screen.html", userError="That username already exists. Please select 'log in' or choose another username.")

@app.route("/login", methods=["POST"])
def login():
    username = request.form["user"]
    password = request.form["pass"].encode('utf-8')
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
        username_list = [user['username'] for user in file]
        if username in [user['username'] for user in file]:
            session["user_index"] = username_list.index(username)
            if bcrypt.checkpw(password, file[session["user_index"]]['password_hash'].encode('utf-8')):
                return redirect(url_for("return_to_dash"))
            else:
                return render_template("login_screen.html", passError="Incorrect password. Please try again.")
        else:
            return render_template("login_screen.html", userNotFoundError="That username doesn't exist. Please select 'create account' or enter another username.")

@app.route("/create_new_project", methods=["POST"]) 
def create_project():
    project_name = request.form["name"]
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    item = {'name' : project_name, 'total_time' : 0, 'formatted_time' : "00:00:00", 'work_sessions' : 0}
    file[session["user_index"]]['projects'].insert(0, item)
    with open(os.path.join(basedir, "Users.json"), "w") as f:
        json.dump(file, f)
    return render_template("project_dashboard.html", confirmation="New project created successfully!", projects=file[session["user_index"]]['projects'], username=file[session["user_index"]]["username"])

@app.route("/stopwatch/<int:project_index>")
def project(project_index):
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    return render_template("project_page.html", project_names="", project_choices="", project=file[session["user_index"]]["projects"][project_index], project_index=project_index, username=file[session["user_index"]]["username"], additional_stopwatch=False)

@app.route("/additional_stopwatch/<int:project_index>")
def additional_project(project_index):
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    projects = file[session["user_index"]]["projects"]
    project_names = [i['name'] for i in projects]
    project_choices = [i['name'] for i in projects]
    project_choices.pop(project_index)
    return render_template("project_page.html", project_names=project_names, project_choices=project_choices, username=file[session["user_index"]]["username"], project_index=project_index, additional_stopwatch=True)


@app.route("/save_session", methods=["POST"])
def save_session():
    data = request.get_json()
    session_seconds = data["seconds"]
    project_index = data["project_index"]
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    project = file[session["user_index"]]["projects"][project_index]
    project["total_time"] += session_seconds 
    project["work_sessions"] += 1
    project["formatted_time"] = str(timedelta(seconds=project["total_time"]))
    session_item = {'name' : project['name'], 
                    'date' : datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    'length' : str(timedelta(seconds=session_seconds)), 
                    'cumulative_time' : project['formatted_time'],
                    'number' : project['work_sessions']}
    file[session["user_index"]]["sessions"].append(session_item)
    with open(os.path.join(basedir, "Users.json"), "w") as f:
        json.dump(file, f)
    return {"status": "ok", "total_time": project["formatted_time"]}

@app.route("/dashboard", methods=["GET"])
def endwork_to_dash():
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    return render_template("project_dashboard.html", confirmation="Work session logged successfully!", projects=file[session["user_index"]]['projects'], username=file[session["user_index"]]["username"])

@app.route("/dashboard_return", methods=["GET"])
def return_to_dash():
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    return render_template("project_dashboard.html", projects=file[session["user_index"]]['projects'], username=file[session["user_index"]]["username"])

@app.route("/delete_project/<int:project_index>")
def delete_project(project_index):
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    file[session["user_index"]]['projects'].pop(project_index)
    with open(os.path.join(basedir, "Users.json"), "w") as f:
        json.dump(file, f)
    return render_template("project_dashboard.html", projects=file[session["user_index"]]['projects'], username=file[session["user_index"]]["username"])

@app.route("/work_log")
def to_work_log():
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    return render_template("exports.html", projects=file[session["user_index"]]['projects'], sessions=file[session["user_index"]]['sessions'], username=file[session["user_index"]]["username"])

@app.route("/export_stats_csv")
def export_stats_csv():
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    projects = file[session["user_index"]]['projects']
    lines = ['Project Name,Total Work Time,Total Work Sessions']
    for project in projects:
        lines.append(f"{project['name']},{project['formatted_time']},{project['work_sessions']}")
    csv = '\n'.join(lines)
    response = make_response(csv)
    response.headers['Content-Disposition'] = 'attachment; filename=project_stats.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route("/export_stats_pdf")
def export_stats_pdf():
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    projects = file[session["user_index"]]['projects']
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    data = [['Project Name', 'Total Work Time', 'Total Work Sessions']]
    for project in projects:
        data.append([project['name'], project['formatted_time'], project['work_sessions']])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),  
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cccccc')),
        ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
    ]))
    styles = getSampleStyleSheet()
    styles['Heading2'].fontName = 'Times-Bold'
    doc.build([
        Paragraph("Project Stats", styles['Heading2']),
        Spacer(1, 12),  
        table])
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=project_stats.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response

@app.route("/export_log_csv")
def export_log_csv():
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    sessions = file[session["user_index"]]['sessions']
    lines = ['Project Name,Session Date,Session Length,Cumulative Time,Project Session Number']
    for sesh in sessions:
        lines.append(f"{sesh['name']},{sesh['date']},{sesh['length']},{sesh['cumulative_time']},{sesh['number']}")
    csv = '\n'.join(lines)
    response = make_response(csv)
    response.headers['Content-Disposition'] = 'attachment; filename=work_log.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

@app.route("/export_log_pdf")
def export_log_pdf():
    with open(os.path.join(basedir, "Users.json"), "r") as f:
        file = json.load(f)
    sessions = file[session["user_index"]]['sessions']
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    data = [['Project Name', 'Session Date', 'Session Length', 'Cumulative Time', 'Project Session Number']]
    for sesh in sessions:
        data.append([sesh['name'], sesh['date'], sesh['length'], sesh['cumulative_time'], sesh['number']])
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f2f2f2')),  
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#cccccc')),
        ('FONTNAME', (0,0), (-1,-1), 'Times-Roman'),
        ('FONTNAME', (0,0), (-1,0), 'Times-Bold'),
    ]))
    styles = getSampleStyleSheet()
    styles['Heading2'].fontName = 'Times-Bold'
    doc.build([
        Paragraph("Project Stats", styles['Heading2']),
        Spacer(1, 12),  
        table])
    response = make_response(buffer.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=work_log.pdf'
    response.headers['Content-Type'] = 'application/pdf'
    return response

if __name__ == "__main__":
    app.run(debug=True)

#line to run in terminal: python -m flask --app "app.py" run