from flask import Flask,render_template,request,redirect,url_for,session
import pyodbc
from werkzeug.security import generate_password_hash, check_password_hash
app=Flask(__name__)
app.secret_key = "secret123"
def connection():
    return pyodbc.connect("Driver={SQL SERVER};"
                            r"SERVER=LAPTOP-836IPRD3\SQLEXPRESS01;"
                            "DATABASE=library;"
                            "Trusted_connection=yes;")
@app.route("/")
def home():
    if "user" not in session:
        return redirect(url_for("register"))
    return render_template("home.html")

@app.route("/books.html")
def books():
    if "user" not in session:
        return redirect(url_for("login"))
    db = connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM books")
    data = cursor.fetchall()
    db.close()
    return render_template("books.html", books=data)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role")
        if not id or not username or not password:
            return "Please fill all fields"
        password_hash = generate_password_hash(password)
        db = connection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO users (username, password,role) VALUES (?, ?,?)",
                       (username.strip(), password_hash,role))
        db.commit()
        db.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/admin")
def admin():
    if "user" not in session or session.get("role") != "admin":
        return "Access denied"
    db = connection()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.execute("SELECT * FROM books")
    books = cursor.fetchall()
    cursor.execute("SELECT * FROM lending")
    lending = cursor.fetchall()
    db.close()
    return render_template("admin.html", users=users, books=books, lending=lending)

@app.route("/login1", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            return "Form not submitted correctly"
        username = username.strip()
        db = connection()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE LTRIM(RTRIM(username)) = ?", (username,))
        user = cursor.fetchone()
        db.close()
        if user is None:
            return "No valid account"
        if check_password_hash(user[1], password):
            session["user"] = username
            session["role"] = user[2]
            return redirect(url_for("home"))
        else:
            return "Incorrect username or password"
    return render_template("login1.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/search",methods=["POST"])
def search():
    id=request.form["id"]
    db=connection()
    cursor=db.cursor()
    cursor.execute("select * from books where b_id=? or name=?",(id,id))
    data=cursor.fetchall()
    db.commit()
    db.close()
    return render_template("search1.html",data=data)

@app.route("/borrow",methods=["POST"])
def borrow():
    if "user" not in session:
        return redirect(url_for("login"))
    username = session["user"]
    b_id = request.form["b_id"]
    today_date = request.form["date"]
    returned = "NO"
    db = connection()
    cursor = db.cursor()
    cursor.execute("select sum(no_of_books) from books where b_id=?", (b_id,))
    data = cursor.fetchone()
    if data[0] is None or data[0] == 0:
        db.close()
        return render_template("no_books.html")
    cursor.execute(
        "insert into lending (b_id,issue_date,returned,username) values (?,?,?,?)",
        (b_id, today_date, returned, username)
    )
    cursor.execute(
        "update books set no_of_books=no_of_books-1 where b_id=?",
        (b_id,)
    )
    db.commit()
    db.close()
    return redirect(url_for("books"))

@app.route("/update", methods=["POST"])
def update():
    b_id = request.form["b_id"]
    username = session["user"]
    db = connection()
    cursor = db.cursor()
    cursor.execute(" UPDATE lending SET returned='YES' WHERE b_id=? AND username=? AND returned='NO'", (b_id, username))
    cursor.execute("UPDATE books SET no_of_books = no_of_books + 1WHERE b_id=?", (b_id,))
    db.commit()
    db.close()
    return redirect(url_for("my_books"))

@app.route("/add_books",methods=["POST"])
def add_books():
    b_id=request.form["b_id"]
    book_name=request.form["book_name"]
    Author=request.form["Author"]
    category=request.form["category"]
    Quantity=request.form["Quantity"]
    db=connection()
    cursor=db.cursor()
    cursor.execute("select * from books where name=?",(book_name))
    data=cursor.fetchone()
    if data==None:
        cursor.execute("insert into books values(?,?,?,?,?)",(b_id,book_name,Author,category,Quantity))
    else:
        cursor.execute("update books set no_of_books=no_of_books+? where name=?",(Quantity,book_name))
    db.commit()
    db.close()
    return redirect(url_for('books'))

@app.route("/my_books") 
def my_books():
     if "user" not in session: 
        return redirect(url_for("login")) 
     username = session["user"] 
     db = connection() 
     cursor = db.cursor() 
     cursor.execute(" SELECT l.b_id, b.name, l.issue_date, l.returned FROM lending l JOIN books b ON l.b_id = b.b_id WHERE l.username = ? ", (username,))
     data = cursor.fetchall() 
     db.close() 
     return render_template("My_books.html", data=data)

@app.route("/books_quantity",methods=["POST"])
def books_quantity():
    id=request.form["id"]
    quan=request.form["quantity"]
    db=connection()
    cursor=db.cursor()
    cursor.execute("update books set Quantity=Quantity+? where id =? or name=?",(quan,id,id))
    db.commit()
    db.close()
    return redirect(url_for('books'))
if __name__ == "__main__":
    app.run(debug=True)

