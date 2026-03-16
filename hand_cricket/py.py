from flask import Flask, render_template, request, redirect, url_for, session
import random
import pyodbc
app = Flask(__name__)
app.secret_key = "cricket"
def connection():
    return pyodbc.connect("Driver={SQL SERVER};"
                            r"SERVER=LAPTOP-836IPRD3\SQLEXPRESS01;"
                            "DATABASE=hand_cricket;"
                            "Trusted_connection=yes;")
@app.route("/")
def home():
    return render_template("py.html")

# -------- TOSS --------
@app.route("/toss", methods=["POST"])
def toss():

    player_choice = request.form["toss"]
    toss = random.choice(["H","T"])

    if player_choice == toss:
        session["toss_win"] = True
        return render_template("choose.html")
    else:
        session["toss_win"] = False
        comp = random.choice(["bat","bowl"])
        session["computer_choice"] = comp
        return redirect(url_for("game"))

# -------- CHOOSE BAT/BOWL --------
@app.route("/choose", methods=["POST"])
def choose():

    session["player_choice"] = request.form["choice"]
    return redirect(url_for("game"))

# -------- GAME PAGE --------
@app.route("/game")
def game():

    if "player_score" not in session:
        session["player_score"] = 0
        session["computer_score"] = 0
        session["target"] = None
        session["innings"] = 1

    return render_template("game.html",
                           p=session["player_score"],
                           c=session["computer_score"],
                           target=session["target"])

# -------- PLAY BALL --------
@app.route("/play", methods=["POST"])
def play():

    player = int(request.form["run"])
    comp = random.randint(1,10)
    pscore = session["player_score"]
    cscore = session["computer_score"]
    innings = session["innings"]
    # PLAYER BATTING
    if session.get("player_choice") == "bat":
        if innings == 1:
            if player == comp:
                session["target"] = pscore + 1
                session["innings"] = 2
            else:
                session["player_score"] = pscore + player
        else:
            if player == comp:
                return redirect(url_for("result"))
            else:
                session["computer_score"] = cscore + comp
                if session["computer_score"] >= session["target"]:
                    return redirect(url_for("result"))
    # PLAYER BOWLING
    else:
        if innings == 1:
            if player == comp:
                session["target"] = cscore + 1
                session["innings"] = 2
            else:
                session["computer_score"] = cscore + comp
        else:
            if player == comp:
                return redirect(url_for("result"))
            else:
                session["player_score"] = pscore + player
                if session["player_score"] >= session["target"]:
                    return redirect(url_for("result"))
    return redirect(url_for("game"))

# -------- RESULT --------
@app.route("/result")
def result():
    db=connection()
    cursor=db.cursor()
    p = session["player_score"]
    c = session["computer_score"]

    if p > c:
        winner = "PLAYER WINS"
    else:
        winner = "COMPUTER WINS"
    cursor.execute("insert into LAST_GAMES VALUES(?,?,?)",(p,c,winner))
    cursor.execute("DELETE FROM LAST_GAMES WHERE ID NOT IN ( SELECT TOP 10 ID FROM LAST_GAMES ORDER BY ID DESC)")
    session.pop("player_score", None)
    session.pop("computer_score", None)
    session.pop("target", None)
    session.pop("innings", None)
    db.commit()
    db.close()

    return render_template("result.html",p=p,c=c,winner=winner)
@app.route("/highest")
def highest():
    db=connection()
    cursor=db.cursor()
    cursor.execute("SELECT Top 10 * FROM LAST_GAMES")
    data=cursor.fetchall()
    cursor.execute(" SELECT max(PLAYER_SCORE) FROM LAST_GAMES WHERE WINNER='PLAYER WINS'")
    high=cursor.fetchone()[0]
    db.commit()
    db.close()
    return render_template("high.html",data=data,top=high)

if __name__ == "__main__":
    app.run(debug=True)