from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "working"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)