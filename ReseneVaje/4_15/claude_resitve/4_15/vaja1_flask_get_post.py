from flask import Flask, request, jsonify

app = Flask(__name__)

# -------------------------------------------------
# GET /welcome
# v cmd: curl http://127.0.0.1:1234/welcome
# -------------------------------------------------
@app.route('/welcome', methods=['GET'])
def welcome():

    if request.method == 'GET':
        return "Pozdravljen v Flask strezniku!"


# -------------------------------------------------
# POST /posttext
# v cmd: curl -X POST http://127.0.0.1:1234/posttext -H "Content-Type: text/plain" -d "Pozdrav"
# -------------------------------------------------
@app.route('/posttext', methods=['POST'])
def posttext():

    tekst = request.data.decode('utf-8')

    odgovor = f"Prejel sem tekst: {tekst}"

    return odgovor


# -------------------------------------------------
# POST /postjson
# v cmd: curl -X POST http://127.0.0.1:1234/postjson -H "Content-Type: application/json" -d "{\"ime\":\"Ana\",\"starost\":22}"
# -------------------------------------------------
@app.route('/postjson', methods=['POST'])
def postjson():

    podatki = request.get_json()

    odgovor = {
        "sporocilo": "JSON prejet",
        "prejeti_podatki": podatki
    }

    return jsonify(odgovor)


# -------------------------------------------------
# Zagon aplikacije
# -------------------------------------------------
app.run(
    host='127.0.0.1',
    port=1234,
    debug=True,
    use_reloader=False
)