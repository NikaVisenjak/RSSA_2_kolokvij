# ============================================================
# NALOGA 1: Flask login z odpravo ranljivosti
# ============================================================
# Ranljivost: Naivna implementacija primerja username in password
# direktno s == kar je ranljivo na:
#   1. Timing attack: Python's == se ustavi pri prvi razliki,
#      kar pomeni, da napadalec lahko meri čas odgovora in ugotovi
#      pravi password znak po znak.
#   2. Shranjeni plaintext passwordi (ne smemo hraniti v plaintext)
# Rešitev:
#   - Passworde shranjujemo kot HASH (bcrypt/werkzeug)
#   - Za primerjavo uporabimo hmac.compare_digest() ki vedno
#     porabi enako časa ne glede na to kje se stringova razlikujeta

from flask import Flask, request, redirect, render_template_string
import hashlib   # standardna knjižnica za hash funkcije
import hmac      # knjižnica za HMAC - vsebuje compare_digest()
geslo = hashlib.sha256("admin123".encode()).hexdigest()
print(geslo)
app = Flask(__name__)  # inicializiramo Flask aplikacijo

# -------------------------------------------------------
# "Baza" uporabnikov - v produkciji bi bil to pravi DB
# Passwordi so shranjeni kot SHA-256 hash, NE v plaintext!
# SHA-256 je enosmerna funkcija - iz hasha ne moreš dobiti
# nazaj originalnega passworda.
#
# Kako ustvariš hash: hashlib.sha256("geslo".encode()).hexdigest()
# -------------------------------------------------------
USERS = {
    # "admin": sha256("admin123")
    "admin": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
    # "alice": sha256("alice456")
    "alice": "e0d8be1e2c9b254425b0db84640d844392593ecb35129b5f756f83442f3d99c5",
}

# -------------------------------------------------------
# Pomožna funkcija za varno preverjanje gesla
# -------------------------------------------------------
def check_password(username: str, password: str) -> bool:
    """
    Varno preveri ali sta username in password pravilna.
    
    1. Preverimo ali uporabnik sploh obstaja
    2. Hashiramo vneseno geslo
    3. Primerjamo hasha z hmac.compare_digest() - ta funkcija
       vedno vzame enako časa (constant-time comparison),
       kar prepreči timing attack.
    """
    # Preverimo ali username obstaja v naši bazi
    if username not in USERS:
        # Pomembno: tudi če user ne obstaja, še vedno izvedemo
        # primerjavo (dummy), da ne razkrijemo ali user obstaja
        # (sicer bi napadalec ugotovil veljavne userje po časovni razliki)
        hmac.compare_digest("dummy", "xxxxx")
        return False
    
    # Hashiramo vneseni password - enaka funkcija kot pri shranjevanju
    # .encode() pretvori string v bytes, ker sha256 dela z bytes
    input_hash = hashlib.sha256(password.encode()).hexdigest()
    
    # compare_digest(): constant-time primerjava - prepreči timing attack!
    # Navaden == bi se ustavil pri prvi razliki (hiter za napačne gesle)
    # compare_digest vedno primerja CELOTEN string, ne glede na razlike
    stored_hash = USERS[username]
    return hmac.compare_digest(input_hash, stored_hash)

# -------------------------------------------------------
# HTML template za login stran
# Jinja2 templating - {{ }} za spremenljivke, {% %} za logiko
# -------------------------------------------------------
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

# -------------------------------------------------------
# Route /login - sprejema GET in POST zahteve
# GET: prikaže obrazec
# POST: obdela prijavo
# -------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    # request.method pove katera HTTP metoda je bila uporabljena
    if request.method == "POST":
        # request.form je slovar podatkov iz HTML obrazca
        # .strip() odstrani whitespace na začetku/koncu (prepreči trike s presledki)
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # Pokličemo varno funkcijo za preverjanje
        if check_password(username, password):
            # redirect() vrne HTTP 302 odgovor ki browser preusmeri
            # Uspešna prijava -> /success/<username>
            return redirect(f"/success/{username}")
        else:
            # Napačna kombinacija -> /failure
            return redirect("/failure")
    
    # GET request: samo prikaži obrazec brez napake
    # render_template_string() izriše Jinja2 template iz stringa
    return render_template_string(LOGIN_TEMPLATE, error=None)


# -------------------------------------------------------
# Route /success/<username> - prikaže uspešno prijavo
# <username> je dinamični del URL-ja (URL parameter)
# -------------------------------------------------------
@app.route("/success/<username>")
def success(username):
    # username je avtomatično izvlečen iz URL-ja
    return f"<h1>Dobrodošel, {username}! Prijava uspešna.</h1>"


# -------------------------------------------------------
# Route /failure - prikaže napako pri prijavi
# -------------------------------------------------------
@app.route("/failure")
def failure():
    return "<h1>Napačno uporabniško ime ali geslo!</h1>", 401
    # 401 = Unauthorized HTTP status koda


# -------------------------------------------------------
# Entry point - zažene Flask development server
# debug=True: avtomatski reload ob spremembah kode
# host="0.0.0.0": dostopen na vseh mrežnih vmesnikih
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
