from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

FILE_NAME = "data.txt"


# -------------------------------------------------
# Pomozna funkcija
# -------------------------------------------------
def load_data():

    if not os.path.exists(FILE_NAME):
        return []

    with open(FILE_NAME, "r") as f:

        content = f.read()

        if content == "":
            return []

        return json.loads(content)


def save_data(data):

    with open(FILE_NAME, "w") as f:
        json.dump(data, f)


# -------------------------------------------------
# GET ALL
# curl http://127.0.0.1:1234/getall
# -------------------------------------------------
@app.route('/getall', methods=['GET'])
def queryall():

    data = load_data()

    return jsonify(data)


# -------------------------------------------------
# POST
# curl -X POST http://127.0.0.1:1234/ -H "Content-Type: application/json" -d "{\"ime\":\"Ana\",\"visina\":\"165\"}"
# -------------------------------------------------
@app.route('/', methods=['POST'])
def create():

    data = load_data()

    record = request.get_json()

    data.append(record)

    save_data(data)

    return "Nov vnos dodan"


# -------------------------------------------------
# PUT = posodobi obstoječi vnos
# curl -X PUT http://127.0.0.1:1234/ -H "Content-Type: application/json" -d "{\"ime\":\"Ana\",\"visina\":\"170\"}"
# -------------------------------------------------
@app.route('/', methods=['PUT'])
def update():

    data = load_data()

    new_record = request.get_json()

    for record in data:

        if record["ime"] == new_record["ime"]:

            record["visina"] = new_record["visina"]

            save_data(data)

            return "Vnos posodobljen"

    return "Oseba ne obstaja"


# -------------------------------------------------
# DELETE
# curl -X DELETE http://127.0.0.1:1234/ -H "Content-Type: application/json" -d "{\"ime\":\"Ana\"}"
# -------------------------------------------------
@app.route('/', methods=['DELETE'])
def delete():

    data = load_data()

    record_to_delete = request.get_json()

    novo = []

    for record in data:

        if record["ime"] != record_to_delete["ime"]:
            novo.append(record)

    save_data(novo)

    return "Vnos izbrisan"


# -------------------------------------------------
# RUN
# -------------------------------------------------
app.run(
    host='127.0.0.1',
    port=1234,
    debug=True,
    use_reloader=False
)