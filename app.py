import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///devpulse.db")

def login_required(f):
    """
    Decorate routes to require login.
    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():
    # 1. Total Active Projects
    project_count = db.execute("SELECT COUNT(*) AS count FROM projects WHERE owner_id = ? AND status = 'Active'", 
                               session["user_id"])[0]["count"]

    # 2. Total Pending Tasks (across all user projects)
    task_count = db.execute("""
        SELECT COUNT(*) AS count FROM tasks 
        JOIN projects ON tasks.project_id = projects.id 
        WHERE projects.owner_id = ? AND tasks.status != 'Done'
    """, session["user_id"])[0]["count"]

    # 3. THE POLISH: Total Completed Projects
    completed_count = db.execute("SELECT COUNT(*) AS count FROM projects WHERE owner_id = ? AND status = 'Completed'", 
                                 session["user_id"])[0]["count"]

    # Pass all three counts to the dashboard
    return render_template("dashboard.html", 
                           project_count=project_count, 
                           task_count=task_count, 
                           completed_count=completed_count)


@app.route("/delete_project/<int:project_id>", methods=["POST"])
@login_required
def delete_project(project_id):
    # Security check: ensure user owns the project
    db.execute("DELETE FROM tasks WHERE project_id = ?", project_id) # Clean up tasks first
    db.execute("DELETE FROM projects WHERE id = ? AND owner_id = ?", project_id, session["user_id"])
    return redirect("/projects")

@app.route("/complete_project/<int:project_id>", methods=["POST"])
@login_required
def complete_project(project_id):
    db.execute("UPDATE projects SET status = 'Completed' WHERE id = ? AND owner_id = ?", 
               project_id, session["user_id"])
    return redirect("/projects")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or password != confirmation:
            return "Check inputs", 400

        hash = generate_password_hash(password)
        try:
            # Insert user and automatically log them in
            user_id = db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hash)
            session["user_id"] = user_id
            session["username"] = username
            return redirect("/")
        except:
            return "Username taken", 400
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if not user or not check_password_hash(user[0]["hash"], password):
            return "Invalid login", 401
            
        session["user_id"] = user[0]["id"]
        session["username"] = user[0]["username"]
        return redirect("/")
    return render_template("login.html")

@app.route("/projects", methods=["GET", "POST"])
@login_required
def projects():
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        db.execute("INSERT INTO projects (name, description, owner_id) VALUES (?, ?, ?)", 
                   name, description, session["user_id"])
        return redirect("/projects")

    # Fetch projects
    rows = db.execute("""
        SELECT p.*, 
        (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id) AS total_tasks,
        (SELECT COUNT(*) FROM tasks t WHERE t.project_id = p.id AND t.status = 'Done') AS done_tasks
        FROM projects p 
        WHERE p.owner_id = ? 
        ORDER BY p.created_at DESC
    """, session["user_id"])

    for row in rows:
        if row["total_tasks"] > 0:
            row["progress"] = int((row["done_tasks"] / row["total_tasks"]) * 100)
        else:
            row["progress"] = 0
    
    print("DEBUG: Rendering Projects Page") 
    
    return render_template("projects.html", projects=rows)

@app.route("/project/<int:project_id>")
@login_required
def project_workspace(project_id):
    # 1. Fetch project details
    project = db.execute("SELECT * FROM projects WHERE id = ? AND owner_id = ?", 
                         project_id, session["user_id"])
    
    if not project:
        return "Project not found or access denied", 404

    # 2. Fetch tasks for this project (we'll build the task creation next)
    tasks = db.execute("SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at DESC", project_id)
    
    return render_template("workspace.html", project=project[0], tasks=tasks)

@app.route("/add_task", methods=["POST"])
@login_required
def add_task():
    title = request.form.get("title")
    project_id = request.form.get("project_id")
    status = request.form.get("status")

    if not title or not project_id:
        return "Missing data", 400

    # Insert task into the database
    db.execute(
        "INSERT INTO tasks (project_id, title, status) VALUES (?, ?, ?)",
        project_id, title, status
    )

    # Redirect back to the specific project workspace
    return redirect(f"/project/{project_id}")

@app.route("/update_task_status", methods=["POST"])
@login_required
def update_task_status():
    task_id = request.form.get("task_id")
    new_status = request.form.get("status")
    project_id = request.form.get("project_id")

    if not task_id or not new_status:
        return "Invalid request", 400

    # Update the status in the database
    db.execute("UPDATE tasks SET status = ? WHERE id = ?", new_status, task_id)

    # Redirect back to the workspace
    return redirect(f"/project/{project_id}")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to home page (which will now show the landing page)
    return redirect("/")



if __name__ == "__main__":
    app.run(debug=True)