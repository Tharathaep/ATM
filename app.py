from flask import Flask, render_template, request, redirect, url_for
import mysql.connector

app = Flask(__name__)

# เชื่อมต่อกับฐานข้อมูล
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="atm_app"
)
cursor = db.cursor()

# สร้างหมายเลขบัญชี
def generate_account_number():
    cursor.execute("SELECT COUNT(*) FROM accounts")
    count = cursor.fetchone()[0]
    return str(count + 1).zfill(8)

# ฟังก์ชันช่วยเหลือเพื่อค้นหาบัญชีจากหมายเลขบัญชีหรือชื่อผู้ใช้
def find_account(identifier):
    if identifier.isdigit():  # กรณีเป็นหมายเลขบัญชี
        cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (identifier,))
        account = cursor.fetchone()
        if account:
            return account[0], {'username': account[1], 'balance': account[2]}
    else:  # กรณีเป็นชื่อผู้ใช้
        cursor.execute("SELECT * FROM accounts WHERE username = %s", (identifier,))
        account = cursor.fetchone()
        if account:
            return account[0], {'username': account[1], 'balance': account[2]}
    return None, None  # ถ้าไม่พบบัญชี

# หน้าแรก
@app.route('/')
def index():
    return render_template('index.html')

# สร้างบัญชีผู้ใช้
@app.route('/create_account', methods=['GET', 'POST'])
def create_account():
    if request.method == 'POST':
        username = request.form['username']
        initial_balance = float(request.form['initial_balance'])
        account_number = generate_account_number()
        cursor.execute("INSERT INTO accounts (account_number, username, balance) VALUES (%s, %s, %s)",
                       (account_number, username, initial_balance))
        db.commit()
        return redirect(url_for('account', account_number=account_number))
    return render_template('create.html')

# ดูยอดเงินในบัญชี
@app.route('/account/<account_number>')
def account(account_number):
    account_number, account = find_account(account_number)
    if account:
        return render_template('account.html', account_number=account_number, account=account)
    return 'Account not found', 404

# ตรวจสอบยอดเงินในบัญชี
@app.route('/check_balance', methods=['GET', 'POST'])
def check_balance():
    if request.method == 'POST':
        account_number = request.form.get('account_number')  # รับหมายเลขบัญชี
        if account_number:
            cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
            account = cursor.fetchone()
            if account:
                return render_template('account.html', account_number=account_number, account={
                    'username': account[1],
                    'balance': account[2]
                })
            return 'Account not found', 404
        return 'Invalid request', 400
    return render_template('check_balance.html')



# ฝากเงินเข้าบัญชี
@app.route('/deposit', methods=['GET', 'POST'])
def deposit():
    if request.method == 'POST':
        account_number = request.form.get('account_number')  # รับหมายเลขบัญชี
        amount = float(request.form.get('amount', 0))  # รับจำนวนเงิน
        if account_number and amount > 0:
            cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
            account = cursor.fetchone()
            if account:
                cursor.execute("UPDATE accounts SET balance = balance + %s WHERE account_number = %s",
                               (amount, account_number))
                db.commit()
                return redirect(url_for('account', account_number=account_number))
            return 'Account not found', 404
        return 'Invalid amount or account not found', 400
    return render_template('deposit.html')


# ถอนเงินจากบัญชี
@app.route('/withdraw', methods=['GET', 'POST'])
def withdraw():
    if request.method == 'POST':
        account_number = request.form.get('account_number')  # รับหมายเลขบัญชี
        amount = float(request.form.get('amount', 0))  # รับจำนวนเงิน
        if account_number and amount > 0:
            cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
            account = cursor.fetchone()
            if account and account[2] >= amount:  # ตรวจสอบยอดเงินในบัญชี
                cursor.execute("UPDATE accounts SET balance = balance - %s WHERE account_number = %s",
                               (amount, account_number))
                db.commit()
                return redirect(url_for('account', account_number=account_number))
            return 'Insufficient balance or account not found', 400
        return 'Invalid amount or account not found', 400
    return render_template('withdraw.html')


# ลบบัญชีผู้ใช้
@app.route('/delete_account', methods=['GET', 'POST'])
def delete_account():
    if request.method == 'POST':
        account_number = request.form.get('account_number')
        
        if not account_number:
            return render_template('delete_account.html', error="Please provide a valid account number.")
        
        # Validate account number format, e.g., must be numeric or a specific length
        if not account_number.isdigit():
            return render_template('delete_account.html', error="Account number should be numeric.")
        
        cursor.execute("SELECT * FROM accounts WHERE account_number = %s", (account_number,))
        account = cursor.fetchone()
        
        if account:
            cursor.execute("DELETE FROM accounts WHERE account_number = %s", (account_number,))
            db.commit()
            return render_template('delete_account.html', success="Account deleted successfully.")
        else:
            return render_template('delete_account.html', error="Account not found.")
    
    return render_template('delete_account.html')




if __name__ == '__main__':
    app.run(debug=True)
