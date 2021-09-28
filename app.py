from flask import Flask, render_template, jsonify, request, session, redirect, url_for

app = Flask(__name__)

from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient('mongodb://test:test@13.124.151.213:27017')
db = client.ftime


@app.route('/', methods=['GET'])
def main_page():
    challenges = objectIdDecoder(list(db.challenge.find({})))
    return render_template('index.html', challenges=challenges)


@app.route('/error', methods=['GET'])
def error_page():
    return render_template('404.html')


@app.route('/user', methods=['GET'])
def user():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        return render_template('user.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))

    return render_template('user.html')


@app.route('/challenge/create', methods=['GET'])
def challenge_create_page():
    return render_template('challenge-create.html')


@app.route('/challenge/<challengeId>', methods=['GET'])
def challenge_detail_page(challengeId):
    challenge = db.challenge.find_one({'_id': ObjectId(challengeId)})
    challenge['_id'] = str(challenge['_id'])
    return render_template("challenge-detail.html", challenge=challenge)


# 준호님 code start

import jwt
import hashlib
from datetime import datetime, timedelta

# from werkzeug.utils import secure_filename


app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'FEVER'


@app.route('/check-login')
def home():
    token_receive = request.cookies.get('mytoken')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        return render_template('index.html')
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@app.route('/help-login')
def login():
    msg = request.args.get("msg")
    return render_template('challenge-login.html', msg=msg)


# @app.route('/user/<username>')
# def user(username):
#     # 각 사용자의 프로필과 글을 모아볼 수 있는 공간
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         status = (username == payload["id"])  # 내 프로필이면 True, 다른 사람 프로필 페이지면 False
#
#         user_info = db.users.find_one({"username": username}, {"_id": False})
#         return render_template('user.html', user_info=user_info, status=status)
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))
#

@app.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'username': username_receive, 'password': pw_hash})
    if result is not None:
        payload = {
            'id': username_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})

    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    username_receive = request.form['username_give']
    password_receive = request.form['password_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "username": username_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        # "profile_name": username_receive,                           # 프로필 이름 기본값은 아이디
        # "profile_pic": "",                                          # 프로필 사진 파일 이름
        # "profile_pic_real": "profile_pics/profile_placeholder.png", # 프로필 사진 기본 이미지
        # "profile_info": ""                                          # 프로필 한 마디
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    username_receive = request.form['username_give']
    exists = bool(db.users.find_one({"username": username_receive}))
    return jsonify({'result': 'success', 'exists': exists})


# @app.route('/update_profile', methods=['POST'])
# def save_img():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 프로필 업데이트
#         return jsonify({"result": "success", 'msg': '프로필을 업데이트했습니다.'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route('/posting', methods=['POST'])
# def posting():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 포스팅하기
#         return jsonify({"result": "success", 'msg': '포스팅 성공'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route("/get_posts", methods=['GET'])
# def get_posts():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 포스팅 목록 받아오기
#         return jsonify({"result": "success", "msg": "포스팅을 가져왔습니다."})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# @app.route('/update_like', methods=['POST'])
# def update_like():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         # 좋아요 수 변경
#         return jsonify({"result": "success", 'msg': 'updated'})
#     except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
#         return redirect(url_for("home"))


# 준호님 code end

# 수빈님 code start

# @app.route('/challenge', methods=['GET'])
# def get_challenge():
#     challenges = list(db.challenge.find({}))
#     json_str = dumps(challenges)
#     print(json_str)
#     return jsonify({'all_challenges': json_str})

@app.route('/challenge', methods=['POST'])
def save_challenge():
    title_receive = request.form["title_give"]
    desc_receive = request.form["desc_give"]
    period_receive = request.form["period_give"]
    address_receive = request.form["address_give"]
    # host_receive = request.form["host_give"]

    file_len = len(request.files)
    # file_len 이 0이면 JS에서 파일을 안보낸준 것!
    # 파일을 안보내줬으면 default 파일이름을 넘겨준다.
    if file_len == 0:
        full_file_name = "challenge.jfif"  # default 파일이름 설정
    else:
        # 파일을 제대로 전달해줬으면 파일을 꺼내서 저장하고 파일이름을 넘겨준다.
        image_receive = request.files["image_give"]

        extension = image_receive.filename.split('.')[-1]
        today = datetime.now()
        mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

        filename = f'file-{mytime}'

        save_to = f'static/assets/img/challenge/{filename}.{extension}'
        image_receive.save(save_to)

        full_file_name = f'{filename}.{extension}'

    doc = {
        'challenge_title': title_receive,
        'challenge_desc': desc_receive,
        'challenge_img': full_file_name,
        'challenge_startTime': period_receive.split(',')[0],
        'challenge_endTime': period_receive.split(',')[1],
        'challenge_address': address_receive,
        'challenge_host':  'admin'
    }

    db.challenge.insert_one(doc)
    return jsonify({'msg': "챌린지 등록 되었습니다."})


@app.route('/challenge/delete', methods=['POST'])
def delete_word():
    host_receive = request.form['host_give']
    db.challenge.delete_one({'challenge_host': host_receive})
    return jsonify({'result': 'success', 'msg': '챌린지 삭제 되었습니다.'})


@app.route('/challenge/check', methods=['POST'])
def challenge_check():
    challenge_receive = request.form["challenge_give"]
    cont_receive = request.form["cont_give"]
    file = request.files["img_give"]

    extension = file.filename.split('.')[-1]

    today = datetime.now()
    mytime = today.strftime("%Y-%m-%d-%H-%M-%S")
    uploadtime = today.strftime("%Y-%m-%d")

    filename = f'file-{mytime}'

    save_to = f'static/assets/img/join/{filename}.{extension}'
    file.save(save_to)

    doc = {
        'join_challenge': challenge_receive,
        'join_date': uploadtime,
        'join_cont': cont_receive,
        'join_img': f'{filename}.{extension}',

    }

    db.join.insert_one(doc)
    return jsonify({'msg': "챌린지 인증 되었습니다."})


@app.route('/challenge/get', methods=['GET'])
def challenge_get():
    challenge_receive = request.args.get('challenge_give')
    challenges = list(db.join.find({'join_challenge': challenge_receive}, {"_id": False}))
    # 예문 가져오기
    return jsonify({'all_challenges': challenges})


# 수빈님 code end

# 현규님 code start
def objectIdDecoder(list):
    results = []
    for document in list:
        document['_id'] = str(document['_id'])
        results.append(document)
    return results


# 현규님 code end

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
