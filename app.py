from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

import requests
from bs4 import BeautifulSoup

from pymongo import MongoClient

client = MongoClient('13.124.151.213', 27017, username='test', password='test')
db = client.ftime

from datetime import datetime


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/challenge', methods=['GET'])
def listing():
    challenges = list(db.challenge.find({}, {'_id': False}))
    return jsonify({'all_challenges': challenges})

@app.route('/challenge/delete', methods=['POST'])
def delete_challenge():
    title_receive = request.form['title_give']
    db.challenge.delete_one({'challenge_title':title_receive})
    return jsonify({'msg': "챌린지 삭제 되었습니다." })


@app.route('/challenge', methods=['POST'])
def save_challenge():
    title_receive = request.form["title_give"]
    decs_receive = request.form["desc_give"]
    period_receive = request.form["period_give"]

    file_len = len(request.files)
    # file_len 이 0이면 JS에서 파일을 안보낸준 것!
    # 파일을 안보내줬으면 default 파일이름을 넘겨준다.
    if file_len == 0:
        full_file_name = "default.png" # default 파일이름 설정
    else:
        # 파일을 제대로 전달해줬으면 파일을 꺼내서 저장하고 파일이름을 넘겨준다.
        image_receive = request.files["image_give"]

        extension = image_receive.filename.split('.')[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

        filename = f'file-{mytime}'

        save_to = f'static/{filename}.{extension}'
        image_receive.save(save_to)

        full_file_name = f'{filename}.{extension}'

    doc = {
        'challenge_title': title_receive,
        'challenge_desc': decs_receive,
        'challenge_img': full_file_name,
        'challenge_startTime': period_receive.split(',')[0],
        'challenge_endTime': period_receive.split(',')[1],
        'challenge_host': 'admin'
    }

    db.challenge.insert_one(doc)
    return jsonify({'msg': "챌린지 등록 되었습니다." })
