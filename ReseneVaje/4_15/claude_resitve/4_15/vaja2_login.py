# ============================================================
# VAJE 15.4 - Vaja 2: Flask Login
# ============================================================
# Pravilni username:password je martin:martin00
# Tri route-e:
#   /login          - obrazec za prijavo (GET + POST)
#   /success/<name> - pozdravna stran
#   /failure        - stran za napako
# ============================================================

from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

# -------------------------------------------------------
# HTML template za /login
# Jinja2 sintaksa: {{ spremenljivka }}, {% if pogoj %}
# -------------------------------------------------------
LOGIN_HTML = """
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
    <h2>Prijava</h2>
    <!-- method="POST": podatki gredo v HTTP body, ne v URL -->
    <form method="POST">
        <label>Uporabniško ime:</label><br>
        <!-- name="username": ključ za request.form['username'] -->
        <input type="text" name="username" required><br><br>
        
        <label>Geslo:</label><br>
        <!-- type="password": browser skrije znake -->
        <input type="password" name="password" required><br><br>
        
        <button type="submit">Prijava</button>
    </form>
</body>
</html>
"""

# -------------------------------------------------------
# Vaja zahteva preprosto primerjavo (brez varnostnih nadgradenj)
# Pravilna kombinacija je hardcoded
# -------------------------------------------------------
PRAVI_USERNAME = "martin"
PRAVO_GESLO    = "martin00"

@app.route('/login', methods=['GET', 'POST'])  # oba GET in POST
def login():
    if request.method == 'GET':
        # GET: samo prikažemo obrazec
        # render_template_string() izriše HTML iz stringa
        return render_template_string(LOGIN_HTML)
    
    if request.method == 'POST':
        # POST: preberemo podatke iz obrazca
        # request.form je slovar ImmutableMultiDict
        user = request.form['username']      # vrednost input name="username"
        password = request.form['password']  # vrednost input name="password"
        
        # Preverimo kombinacijo
        if user == PRAVI_USERNAME and password == PRAVO_GESLO:
            # redirect() pošlje HTTP 302 Found - browser gre na novo URL
            # url_for('success', name=user) generira URL /success/martin
            return redirect(url_for('success', name=user))
        else:
            # Napačna kombinacija -> /failure
            return redirect(url_for('failure'))

# -------------------------------------------------------
# /success/<name> - dinamični URL parameter
# <name> v URL-ju se preslika v parameter funkcije
# -------------------------------------------------------
@app.route('/success/<name>')
def success(name):
    # name je avtomatično izvlečen iz URL-ja npr. /success/martin -> name="martin"
    return f"<h1>Dobrodošli, {name}!</h1>"

# -------------------------------------------------------
# /failure - statična stran za napako
# -------------------------------------------------------
@app.route('/failure')
def failure():
    # 401 Unauthorized = napačne kredenciale
    return "<h1>Napačni username ali password!</h1>", 401

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=1235, debug=True, use_reloader=False)
