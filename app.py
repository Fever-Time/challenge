from flask import Flask, render_template, jsonify, request
app = Flask(__name__)

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient
client = MongoClient('13.124.151.213', 27017, username = 'test', password = 'test')
db = client.ftime

from datetime import datetime



@app.route('/')
def home():
    return render_template('index.html')

@app.route('/challenge', methods=['GET'])
def listing():
    challenges = list(db.challenge.find({},{'_id':False}))
    return jsonify({'all_challenges': challenges})


@app.route('/challenge', methods=['POST'])
def save_diary():


    title_receive = request.form["title_give"]
    decs_receive = request.form["desc_give"]
    period_receive = request.form["period_give"]
    image_receive = request.files["image_give"]

    extension = image_receive.filename.split('.')[-1]
    today = datetime.now()
    mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

    filename = f'file-{mytime}'

    save_to = f'static/{filename}.{extension}'
    image_receive.save(save_to)


    doc = {
        'challenge_title': title_receive,
        'challenge_desc': decs_receive,
        'challenge_img':f'{filename}.{extension}',
        'challenge_startTime' : period_receive.split(',')[0],
        'challenge_endTime': period_receive.split(',')[1],
        'challenge_host': 'admin'



    }

    db.challenge.insert_one(doc)
    return jsonify({'msg': '저장 완료!'})



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)