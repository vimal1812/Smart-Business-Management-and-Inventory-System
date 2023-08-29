
import mysql.connector
from flask import Flask, render_template, url_for, request, redirect, flash, session

app=Flask(__name__)
app.secret_key = 'mysecretkey123'

db = mysql.connector.connect(
    host='database-2.cvoqfr3fpxww.ap-south-1.rds.amazonaws.com',
    user='admin',
    password='awsuser123',
    database='app',
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login',methods=["GET","POST"])
def login():
    if request.method=='POST':
        username = request.form['username']
        password = request.form['password']
        con = db.cursor(buffered=True)
        con.execute("SELECT * FROM Company WHERE username=%s AND password=%s", (username, password))
        res = con.fetchone()

        if res:
            session["username"] = res[1]
            session["password"] = res[4]
            session["user_id"] = res[0]
            session["cash_balance"] = res[3]
            return redirect("Dashboard")
        else:
            flash("Invalid Username or Password","danger")
    return redirect(url_for("index"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        try:
            company_name = request.form['company_name']
            username = request.form['username']
            password = request.form['password']
            cash = request.form['cash']
            con = db.cursor(buffered=True)
            con.execute("INSERT INTO Company(company_name, username, password, cash_balance) VALUES (%s, %s, %s, %s)",(company_name, username, password, cash))
            db.commit()
            flash("Registered Successfully")
        except:
            flash("Error in insert operation", "danger")
        finally:
            con.close()
            return redirect(url_for("index"))

    return render_template('register.html')


@app.route('/Dashboard')
def Dashboard():
    if "user_id" in session:
        user_id = session["user_id"]
        con=db.cursor(buffered=True)
        con.execute("SELECT company_name, cash_balance FROM Company WHERE user_id = %s", (user_id,))
        company_data = con.fetchone()
        con.execute("SELECT * FROM Item WHERE user_id = %s", (user_id,))
        item_data = con.fetchall()


        return render_template("Dashboard.html", company_data=company_data, datas=item_data)
    else:
        return redirect(url_for("index"))


#add items
@app.route("/addItem", methods=['GET', 'POST'])
def addItem():
    con = db.cursor(buffered=True)
    user_id = session["user_id"]
    if request.method == 'POST':
        item_name = request.form.get('item_name')
        # Check if the item_name already exists for the user
        con.execute("SELECT * FROM Item WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        existing_item = con.fetchone()

        if existing_item:
            flash("Item is already add another item.", "danger")
            con.close()
            return redirect(url_for("addItem"))

        sql = "INSERT INTO Item (user_id, item_name) VALUES (%s, %s)"
        con.execute(sql, (user_id, item_name))
        db.commit()
        con.close()

        return redirect(url_for("Dashboard"))

    con.execute("SELECT * FROM Item WHERE user_id = %s", (user_id,))
    item_data = con.fetchall()
    con.execute("SELECT company_name, cash_balance FROM Company WHERE user_id = %s", (user_id,))
    company_data = con.fetchone()
    return render_template("addItem.html", datas=item_data, company_data=company_data)

# Add Purchase
@app.route('/purchase/<string:item_name>', methods=['GET', 'POST'])
def purchase(item_name):
    conn=db.cursor(buffered=True)
    user_id = session["user_id"]
    if request.method == 'POST':
        qty = int(request.form.get('qty'))
        rate = int(request.form.get('cost'))
        cost = qty * rate
        conn.execute("SELECT cash_balance FROM Company WHERE user_id = %s", (user_id,))
        cash_balance = conn.fetchone()[0]
        conn.execute("update Company set cash_balance = cash_balance-%s", (cash_balance,))

        conn.execute("UPDATE Item SET qty = qty + %s WHERE item_name = %s", (qty, item_name))

        conn.execute("INSERT INTO Purchase (item_name, qty, rate, amount) VALUES (%s, %s, %s, %s)",(item_name, qty, rate, cost))

        return redirect(url_for("Dashboard"))

    sql = "select * from Item where item_name=%s "
    conn.execute(sql, [item_name])
    res = conn.fetchone()
    return render_template("purchase.html",datas=res)




#sell
@app.route('/sell/<string:item_name>', methods=['GET', 'POST'])
def sell(item_name):
    conn=db.cursor(buffered=True)
    user_id = session["user_id"]
    if request.method == 'POST':
        qty = int(request.form.get('qty'))
        rate = int(request.form.get('cost'))

        conn.execute("SELECT * FROM Item WHERE item_name = %s ", (item_name,))
        res = conn.fetchone()

        total_cost = int(qty) * int(rate)

        if res[2] < int(qty):
            flash("Insufficient balance to purchase.", "error")

            return redirect(url_for("Dashboard"))
        else:
            conn.execute("UPDATE Company SET cash_balance = cash_balance + %s", (total_cost,))
            conn.execute("UPDATE Item SET qty = qty - %s WHERE item_name = %s", (qty, item_name,))

            conn.execute("INSERT INTO Sales (item_name, qty, rate, amount) VALUES (%s, %s, %s, %s)",(item_name, qty, rate, total_cost,))

            return redirect(url_for("Dashboard"))

    sql = "select * from Item where item_name=%s "
    conn.execute(sql, (item_name,))
    res = conn.fetchone()
    return render_template("sell.html",datas=res)

@app.route('/purchase_history')
def purchase_history():
    username = session["username"]
    con = db.cursor(buffered=True)
    con.execute("SELECT company_name, cash_balance FROM Company WHERE username  = %s", (username,))
    company_data = con.fetchone()
    con.fetchall()
    con.execute("SELECT * FROM Purchase" )
    purchase_history = con.fetchall()
    con.close()
    return render_template("purchase_history.html", purchase_history=purchase_history, company_data=company_data)

@app.route('/sell_history')
def sell_history():
    username = session["username"]
    con = db.cursor(buffered=True)
    con.execute("SELECT company_name, cash_balance FROM Company WHERE username  = %s", (username,))
    company_data = con.fetchone()
    con.fetchall()
    con.execute("SELECT * FROM Sales" )
    sell_history = con.fetchall()
    con.close()
    return render_template("sell_history.html", sell_history=sell_history, company_data=company_data)

@app.route('/delete_item/<string:item_name>', methods=['POST'])
def delete_item(item_name):
    if "user_id" in session:
        user_id = session["user_id"]
        con = db.cursor(buffered=True)
        con.execute("DELETE FROM Item WHERE user_id = %s AND item_name = %s", (user_id, item_name))
        db.commit()
        con.close()
    return redirect(url_for('Dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("index"))


if(__name__=='__main__'):
    app.run(debug=True)