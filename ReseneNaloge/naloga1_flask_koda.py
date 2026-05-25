from flask import Flask, request, redirect, render_template_string
import hashlib  
import hmac   
#geslo = hashlib.sha256("admin123".encode()).hexdigest()
#print(geslo)
app = Flask(__name__)  

USERS = {
    # "admin": sha256("admin123")
    "admin": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
    # "alice": sha256("alice456")
    "alice": "e0d8be1e2c9b254425b0db84640d844392593ecb35129b5f756f83442f3d99c5",
}

def check_password(username: str, password: str) -> bool:

    if username not in USERS:
        hmac.compare_digest("dummy", "xxxxx")
        return False

    input_hash = hashlib.sha256(password.encode()).hexdigest()

    stored_hash = USERS[username]
    return hmac.compare_digest(input_hash, stored_hash)

LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
    <h2>Prijava</h2>
    <!-- action="" pomeni POST na isto URL (/login) -->
    <form method="POST" action="">
        <label>Uporabniško ime:</label><br>
        <!-- name="username" - ključ za request.form["username"] -->
        <input type="text" name="username" required><br><br>
        
        <label>Geslo:</label><br>
        <!-- type="password" - browser skrije vnos -->
        <input type="password" name="password" required><br><br>
        
        <button type="submit">Prijava</button>
    </form>
    {% if error %}
        <!-- Jinja2 pogojni blok - prikaže napako samo če obstaja -->
        <p style="color:red;">{{ error }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if check_password(username, password):
            return redirect(f"/success/{username}")
        else:
            return redirect("/failure")
    
    return render_template_string(LOGIN_TEMPLATE, error=None)


@app.route("/success/<username>")
def success(username):
    return f"<h1>Dobrodošel, {username}! Prijava uspešna.</h1>"

@app.route("/failure")
def failure():
    return "<h1>Napačno uporabniško ime ali geslo!</h1>", 401

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
