import requests
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, make_response
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from dotenv import load_dotenv
import os
import jwt
import hashlib
from datetime import datetime, timedelta
import boto3
from apscheduler.schedulers.background import BackgroundScheduler

application = Flask(__name__)
application.config["TEMPLATES_AUTO_RELOAD"] = True
cors = CORS(application, resources={r"/*": {"origins": "*"}})

load_dotenv()
client = MongoClient(os.environ.get("MONGO_URL"))
db = client.ftime
SECRET_KEY = os.environ.get("SECRET_KEY")
TOKEN_NAME = "fever-time"


@application.route('/', methods=['GET'])
def main_page():
    challenges = objectIdDecoder(list(db.challenge.find({})))
    for challenge in challenges:
        challenge['people'] = len(list(db.join.distinct("join_user", {"join_challenge": challenge['_id']})))
    return render_template('index.html', challenges=challenges)


@application.route('/error', methods=['GET'])
def error_page():
    return render_template('404.html')


@application.route('/find', methods=['GET'])
def find_pw():
    return render_template('findPw.html')


@application.route('/search', methods=['GET'])
def search_challenge():
    search_receive = request.args.get('search')
    challenges = objectIdDecoder(list(db.challenge.find({})))
    search_ch = []
    for challenge in challenges:
        if search_receive in challenge["challenge_title"]:
            search_ch.append(challenge)
            challenge['people'] = len(list(db.join.distinct("join_user", {"join_challenge": challenge["_id"]})))
    return render_template('index.html', challenges=search_ch)


@application.route('/user', methods=['GET'])
def user():
    token_receive = request.cookies.get(TOKEN_NAME)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']

        join_challenge_id_list = list(db.join.distinct("join_challenge", {'join_user': user_id}))

        challenge_cnt = dict()
        challenge_cnt['ing'] = 0
        challenge_cnt['pause'] = 0
        challenge_cnt['end'] = 0
        for challenge_id in join_challenge_id_list:
            if db.challenge.find_one({'_id': ObjectId(challenge_id)})['challenge_status'] == 1:
                challenge_cnt['pause'] += 1
            elif db.challenge.find_one({'_id': ObjectId(challenge_id)})['challenge_status'] == 0:
                challenge_cnt['ing'] += 1
            else:
                challenge_cnt['end'] += 1

        challenges = []
        for challenge_id in join_challenge_id_list:
            challenges.append(db.challenge.find_one({'_id': ObjectId(challenge_id)}))

        return render_template('user.html', challenges=challenges, challenge_cnt=challenge_cnt)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@application.route('/challenge', methods=['GET'])
def challenge_create_page():
    return render_template('challenge-create.html')


@application.route('/challenge/<challengeId>', methods=['GET'])
def challenge_detail_page(challengeId):
    challenge = db.challenge.find_one({'_id': ObjectId(challengeId)})
    challenge['_id'] = str(challenge['_id'])

    # 챌린지 인증 가져오기
    joins = list(db.join.find({'join_challenge': challengeId}, {"_id": False}))

    # 챌린지 카테고리 가져오기
    if 'challenge_categories' in challenge:
        categories = ', '.join(challenge['challenge_categories']) \
            .replace("category1", "운동") \
            .replace("category2", "공부") \
            .replace("category3", "취미")
    else:
        categories = ''

    # 연관 챌린지 가쟈오기(3개)
    related_challenge = objectIdDecoder(list(db.challenge.find({'_id': {'$ne': ObjectId(challengeId)}}).limit(3)))
    for r_challenge in related_challenge:
        r_challenge['people'] = len(list(db.join.distinct("join_user", {"join_challenge": r_challenge['_id']})))

    people = len(list(db.join.distinct("join_user", {"join_challenge": challengeId})))
    join = list(db.join.distinct("join_user", {"join_challenge": challengeId}))
    token_receive = request.cookies.get('fever-time')

    status = False
    status_join = False

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        status = (challenge['challenge_host'] == payload["id"])  # 내가 만든 챌리지이면 True
        status_join = (payload["id"] in join)  # 인증한 유저 중에 내 아이디가 있으면 TRUE
    finally:
        return render_template("challenge-detail.html", challenge=challenge, people=people, status=status,
                               categories=categories, related_challenge=related_challenge, joins=joins,
                               status_join=status_join)


# 준호님 code start
@application.route('/login', methods=['GET'])
def login():
    msg = request.args.get("msg")
    return render_template('login.html', msg=msg)


@application.route('/sign_in', methods=['POST'])
def sign_in():
    # 로그인
    email_receive = request.form['user_email']
    password_receive = request.form['user_pw']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    result = db.users.find_one({'user_email': email_receive, 'user_pw': pw_hash})
    if result is not None:
        payload = {
            'id': email_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')

        response = make_response(redirect(url_for("main_page")))
        response.set_cookie(TOKEN_NAME, token)
        return response

    # 찾지 못하면
    else:
        return redirect(url_for("login", msg='아이디/비밀번호가 일치하지 않습니다.'))


@application.route('/sign_up', methods=['GET'])
def sign_up():
    return render_template('sign-up.html')


@application.route('/sign_up', methods=['POST'])
def sign_up_save():
    email_receive = request.form['user_email']
    username_receive = request.form['user_name']
    password_receive = request.form['user_pw']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    doc = {
        "user_email": email_receive,
        "user_name": username_receive,
        "user_pw": password_hash
    }

    db.users.insert_one(doc)

    return redirect(url_for("login", msg='회원가입 하셨습니다.'))


@application.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    email_receive = request.form['user_email']
    exists = bool(db.users.find_one({"user_email": email_receive}))
    return jsonify({'result': 'success', 'exists': exists})


@application.route('/check_pwd', methods=['POST'])  # 현재 비밀번호가 맞는지 확인
def check_pwd():
    token_receive = request.cookies.get(TOKEN_NAME)
    password_receive = request.form['pwd']
    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()

    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']
        exists = bool(db.users.find_one({"user_email": user_id, "user_pw": pw_hash}))

    except jwt.ExpiredSignatureError:
        return jsonify({'result': '쿠키 만료'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': '쿠키값 디코드 실패'})
    # 토큰을 불러와서 유저아이디를 기준으로 비밀번호가 있어야됨
    # 같은 비밀번호가 있으면 EXIT이 YES가된다.

    return jsonify({'result': exists})


@application.route('/change_pwd', methods=['PUT'])  # 비밀번호 변경
def change_pwd():
    token_receive = request.cookies.get(TOKEN_NAME)
    password_receive = request.args.get('pwd')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
        user_id = payload['id']
        db.users.update_one({'user_email': user_id}, {'$set': {'user_pw': pw_hash}})

    except jwt.ExpiredSignatureError:
        return jsonify({'result': '쿠키 만료'})
    except jwt.exceptions.DecodeError:
        return jsonify({'result': '쿠키값 디코드 실패'})
    return jsonify({'result': 'success'})


@application.route('/unregister', methods=['POST'])  # 회원탈퇴
def unregister():
    token_receive = request.cookies.get(TOKEN_NAME)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']
        db.users.delete_one({'user_email': user_id})


    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="회원 정보가 존재하지 않습니다."))
    return jsonify({"result": '회원탈퇴 되었습니다.'})


@application.route('/oauth/callback', methods=['GET'])
def oauth():
    # code는 index.html에 카카오 버튼 url을 보면 알 수 있습니다. 버튼 url에 만든사람 인증id, return uri이 명시되어 있습니다.
    # 사용자 로그인에 성공하면 로그인 한 사람의 코드를 발급해줍니다.
    code = request.args.get("code")

    # 그 코드를 이용해 서버에 토큰을 요청해야 합니다. 아래는 POST 요청을 위한 header와 body입니다.
    client_id = '568f2b791efeffd312f12ece9bb5faea'
    redirect_uri = 'https://fevertime.shop/oauth/callback'
    token_url = "https://kauth.kakao.com/oauth/token"
    token_headers = {
        'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
    }
    data = {
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'code': code
    }
    response = requests.post(url=token_url, headers=token_headers, data=data)
    token = response.json()

    print(f'토큰 = {token}')
    # POST 요청에 성공하면 return value를 JSON 형식으로 파싱해서 담아줍니다.

    info_url = "https://kapi.kakao.com/v2/user/me"
    info_headers = {
        'Authorization': 'Bearer ' + token['access_token'],
        'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
    }
    info_response = requests.post(url=info_url, headers=info_headers)
    infos = info_response.json()
    print(f'유저 정보 = {infos}')

    kakao_id = infos['id']
    kakao_name = infos['properties']['nickname']

    exist = bool(db.users.find_one({'user_email': infos['id']}))
    print(exist)
    if exist:  # 이미 가입한 유저라면
        payload = {
            'id': kakao_id,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")  # 토큰을 발급하고
        response = make_response(redirect(url_for("main_page")))  # 쿠키를 저장해줄 페이지 지정(?)
        response.set_cookie(TOKEN_NAME, token)  # 메인페이지 기준으로 쿠키 설정(?)

        return response
    else:
        doc = {
            "user_email": kakao_id,
            "user_name": kakao_name
        }
        db.users.insert_one(doc)
        payload = {
            'id': kakao_id,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
        }

        token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")  # 토큰을 발급하고
        response = make_response(redirect(url_for("main_page")))  # 쿠키를 저장해줄 페이지 지정(?)
        response.set_cookie(TOKEN_NAME, token)  # 메인페이지 기준으로 쿠키 설정(?)

        return response


# 준호님 code end


# 수빈님 code start
@application.route('/challenge', methods=['POST'])
def save_challenge():
    token_receive = request.cookies.get(TOKEN_NAME)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        challenge_host = payload['id']

        title_receive = request.form["title_give"]
        decs_receive = request.form["desc_give"]
        period_receive = request.form["period_give"]
        address_receive = request.form["address_give"]

        categories_receive = request.form["categories_give"]
        categories = categories_receive.split(',')

        file_len = len(request.files)
        # file_len 이 0이면 JS에서 파일을 안보낸준 것!
        # 파일을 안보내줬으면 default 파일이름을 넘겨준다.
        if file_len == 0:
            full_file_name = "default-challenge-img.jfif"  # default 파일이름 설정
        else:
            # 파일을 제대로 전달해줬으면 파일을 꺼내서 저장하고 파일이름을 넘겨준다.
            image_receive = request.files["image_give"]

            extension = image_receive.filename.split('.')[-1]

            today = datetime.now()
            mytime = today.strftime('%Y-%m-%d-%H-%M-%S')

            filename = f'challenge-file-{mytime}'
            # save_to = f'static/assets/img/challenge/{filename}.{extension}'
            # image_receive.save(save_to)
            full_file_name = f'{filename}.{extension}'

            # s3 지정한 버킷에 파일 업로드
            s3 = boto3.client('s3',
                              aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                              aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
                              )
            s3.put_object(
                ACL="public-read",
                Bucket=os.environ["BUCKET_NAME"],
                Body=image_receive,
                Key=full_file_name,
                ContentType=image_receive.content_type
            )

        doc = {
            'challenge_title': title_receive,
            'challenge_desc': decs_receive,
            'challenge_img': full_file_name,
            'challenge_startTime': period_receive.split(',')[0],
            'challenge_endTime': period_receive.split(',')[1],
            'challenge_address': address_receive,
            'challenge_host': challenge_host,
            'challenge_categories': categories,
            'challenge_status': 0,
        }

        db.challenge.insert_one(doc)

        return jsonify({'msg': "챌린지 등록 되었습니다."})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


@application.route('/challenge', methods=['PUT'])
def pause_challenge():
    challengeId_receive = request.form['challengeId_give']
    pause_receive = int(request.form['pause_give'])
    if pause_receive == 0:
        db.challenge.update_one({'_id': ObjectId(challengeId_receive)}, {'$set': {'challenge_status': 1}})
        return jsonify({'result': 'success', 'msg': '챌린지가 중단 되었습니다.'})
    else:
        db.challenge.update_one({'_id': ObjectId(challengeId_receive)}, {'$set': {'challenge_status': 0}})
        return jsonify({'result': 'success', 'msg': '챌린지가 활성화 되었습니다.'})


@application.route('/challenge', methods=['DELETE'])
def delete_challenge():
    challengeId_receive = request.form['challengeId_give']

    challenge_img = db.challenge.find_one({'_id': ObjectId(challengeId_receive)})['challenge_img']
    join_list = list(db.join.find({'join_challenge': challengeId_receive}))

    # s3 버킷에서도 사진 삭제
    s3 = boto3.resource('s3')
    # 챌린지 이미지 삭제
    if challenge_img != 'default-challenge-img.jfif':
        s3.Object(os.environ["BUCKET_NAME"], challenge_img).delete()
    # 챌린지 인증 이미지 삭제
    for join in join_list:
        s3.Object(os.environ["BUCKET_NAME"], join['join_img']).delete()

    db.challenge.delete_one({'_id': ObjectId(challengeId_receive)})
    db.join.delete_many({'join_challenge': challengeId_receive})
    return jsonify({'result': 'success', 'msg': '챌린지 삭제 되었습니다.'})


@application.route('/challenge/cancel', methods=['DELETE'])
def cancel_challenge():
    challengeId_receive = request.form['challengeId_give']
    token_receive = request.cookies.get('fever-time')
    payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
    user_receive = payload["id"]

    join_list = list(db.join.find({'join_challenge': challengeId_receive, 'join_user': user_receive}))

    # s3 버킷에서도 사진 삭제
    s3 = boto3.resource('s3')
    # 챌린지 인증 이미지 삭제
    for join in join_list:
        s3.Object(os.environ["BUCKET_NAME"], join['join_img']).delete()

    db.join.delete_many({'join_challenge': challengeId_receive, 'join_user': user_receive})
    return jsonify({'result': 'success', 'msg': '참가 챌린지에서 삭제 되었습니다.'})


@application.route('/challenge/check', methods=['POST'])
def challenge_check():
    token_receive = request.cookies.get(TOKEN_NAME)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])

        user_id = payload['id']

        user_name = db.users.find_one({'user_email': user_id})['user_name']
        challenge_receive = request.form["challenge_give"]
        cont_receive = request.form["cont_give"]
        image_receive = request.files["img_give"]

        extension = image_receive.filename.split('.')[-1]

        today = datetime.now()
        mytime = today.strftime("%Y-%m-%d-%H-%M-%S")
        uploadtime = today.strftime("%Y-%m-%d")

        filename = f'join-file-{mytime}'
        # save_to = f'static/assets/img/join/{filename}.{extension}'
        # file.save(save_to)
        full_file_name = f'{filename}.{extension}'

        # s3 지정한 버킷에 파일 업로드
        s3 = boto3.client('s3',
                          aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
                          )
        s3.put_object(
            ACL="public-read",
            Bucket=os.environ["BUCKET_NAME"],
            Body=image_receive,
            Key=full_file_name,
            ContentType=image_receive.content_type
        )

        doc = {
            'join_challenge': challenge_receive,
            'join_date': uploadtime,
            'join_user': user_id,
            'join_user_name': user_name,
            'join_cont': cont_receive,
            'join_img': full_file_name
        }

        db.join.insert_one(doc)
        return jsonify({'msg': "챌린지 인증 되었습니다."})
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


# 수빈님 code end

# 현규님 code start
def objectIdDecoder(list):
    results = []
    for document in list:
        document['_id'] = str(document['_id'])
        results.append(document)
    return results


# scheduler start
scheduler = BackgroundScheduler()


@scheduler.scheduled_job('cron', hour='00', minute='00', id='schedule-job', timezone='Asia/Seoul')
def challenge_scheduler():
    today = datetime.now()
    yesterday = today - timedelta(1)
    date = yesterday.strftime("%Y-%m-%d")
    db.challenge.update_many({'challenge_endTime': date}, {'$set': {'challenge_status': 2}})


scheduler.start()
# scheduler end

# 현규님 code end

if __name__ == '__main__':
    application.debug = True
    application.run()
