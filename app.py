from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

from pymongo import MongoClient

client = MongoClient('mongodb://test:test@13.124.151.213:27017')
db = client.ftime


@app.route('/')
def home():
    return render_template('index.html')


# 준호님 code start


# 준호님 code end

# 수빈님 code start


# 수빈님 code end

# 현규님 code start


# 현규님 code end

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
