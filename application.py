from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_cors import CORS

# from pymongo import MongoClient
# from bson.objectid import ObjectId
# from dotenv import load_dotenv
# import os
# import jwt
# import hashlib
# from datetime import datetime, timedelta

application = Flask(__name__)
# application.config["TEMPLATES_AUTO_RELOAD"] = True
cors = CORS(application, resources={r"/*": {"origins": "*"}})


# load_dotenv()
# client = MongoClient(os.environ.get("MONGO_URL"))
# db = client.ftime
# SECRET_KEY = os.environ.get("SECRET_KEY")

@application.route('/')
def main():
    return "hello python-app"


# @application.route('/', methods=['GET'])
# def main_page():
#     challenges = objectIdDecoder(list(db.challenge.find({})))
#     for challenge in challenges:
#         challenge['people'] = len(list(db.join.distinct("join_user", {"join_challenge": challenge['_id']})))
#     return render_template('index.html', challenges=challenges)
#
#
# @application.route('/error', methods=['GET'])
# def error_page():
#     return render_template('404.html')
#
#
# @application.route('/user', methods=['GET'])
# def user():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         user_id = payload['id']
#
#         join_challenge_id_list = list(db.join.distinct("join_challenge", {'join_user': user_id}))
#
#         challenges = []
#         for challenge_id in join_challenge_id_list:
#             challenges.append(db.challenge.find_one({'_id': ObjectId(challenge_id)}))
#
#         return render_template('user.html', challenges=challenges)
#     except jwt.ExpiredSignatureError:
#         return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
#     except jwt.exceptions.DecodeError:
#         return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
#
#
# @application.route('/challenge', methods=['GET'])
# def challenge_create_page():
#     return render_template('challenge-create.html')
#
#
# @application.route('/challenge/<challengeId>', methods=['GET'])
# def challenge_detail_page(challengeId):
#     challenge = db.challenge.find_one({'_id': ObjectId(challengeId)})
#     challenge['_id'] = str(challenge['_id'])
#
#     # 챌린지 인증 가져오기
#     joins = list(db.join.find({'join_challenge': challengeId}, {"_id": False}))
#
#     # 챌린지 카테고리 가져오기
#     if 'challenge_categories' in challenge:
#         categories = ', '.join(challenge['challenge_categories']) \
#             .replace("category1", "운동") \
#             .replace("category2", "공부") \
#             .replace("category3", "취미")
#     else:
#         categories = ''
#
#     # 연관 챌린지 가쟈오기(3개)
#     related_challenge = objectIdDecoder(list(db.challenge.find({'_id': {'$ne': ObjectId(challengeId)}}).limit(3)))
#     for r_challenge in related_challenge:
#         r_challenge['people'] = len(list(db.join.distinct("join_user", {"join_challenge": r_challenge['_id']})))
#
#     people = len(list(db.join.distinct("join_user", {"join_challenge": challengeId})))
#
#     token_receive = request.cookies.get('mytoken')
#
#     status = False
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#         status = (challenge['challenge_host'] == payload["id"])  # 내가 만든 챌리지이면 True
#     finally:
#         return render_template("challenge-detail.html", challenge=challenge, people=people, status=status,
#                                categories=categories, related_challenge=related_challenge, joins=joins)
#
#
# # 준호님 code start
# @application.route('/help-login')
# def login():
#     msg = request.args.get("msg")
#     return render_template('challenge-login.html', msg=msg)
#
#
# @application.route('/sign_in', methods=['POST'])
# def sign_in():
#     # 로그인
#     username_receive = request.form['username_give']
#     password_receive = request.form['password_give']
#
#     pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
#     result = db.users.find_one({'username': username_receive, 'password': pw_hash})
#     if result is not None:
#         payload = {
#             'id': username_receive,
#             'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지
#         }
#         token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
#         return jsonify({'result': 'success', 'token': token})
#
#     # 찾지 못하면
#     else:
#         return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})
#
#
# @application.route('/sign_up/save', methods=['POST'])
# def sign_up():
#     username_receive = request.form['username_give']
#     password_receive = request.form['password_give']
#     password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
#     doc = {
#         "username": username_receive,  # 아이디
#         "password": password_hash,  # 비밀번호
#     }
#     db.users.insert_one(doc)
#     return jsonify({'result': 'success'})
#
#
# @application.route('/sign_up/check_dup', methods=['POST'])
# def check_dup():
#     username_receive = request.form['username_give']
#     exists = bool(db.users.find_one({"username": username_receive}))
#     return jsonify({'result': 'success', 'exists': exists})
#
#
# # 준호님 code end
#
# # 수빈님 code start
# @application.route('/challenge', methods=['POST'])
# def save_challenge():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#
#         challenge_host = payload['id']
#
#         title_receive = request.form["title_give"]
#         decs_receive = request.form["desc_give"]
#         period_receive = request.form["period_give"]
#         address_receive = request.form["address_give"]
#
#         categories_receive = request.form["categories_give"]
#         categories = categories_receive.split(',')
#
#         file_len = len(request.files)
#         # file_len 이 0이면 JS에서 파일을 안보낸준 것!
#         # 파일을 안보내줬으면 default 파일이름을 넘겨준다.
#         if file_len == 0:
#             full_file_name = "challenge.jfif"  # default 파일이름 설정
#         else:
#             # 파일을 제대로 전달해줬으면 파일을 꺼내서 저장하고 파일이름을 넘겨준다.
#             image_receive = request.files["image_give"]
#
#             extension = image_receive.filename.split('.')[-1]
#             today = datetime.now()
#             mytime = today.strftime('%Y-%m-%d-%H-%M-%S')
#
#             filename = f'file-{mytime}'
#
#             save_to = f'static/assets/img/challenge/{filename}.{extension}'
#             image_receive.save(save_to)
#
#             full_file_name = f'{filename}.{extension}'
#
#         doc = {
#             'challenge_title': title_receive,
#             'challenge_desc': decs_receive,
#             'challenge_img': full_file_name,
#             'challenge_startTime': period_receive.split(',')[0],
#             'challenge_endTime': period_receive.split(',')[1],
#             'challenge_address': address_receive,
#             'challenge_host': challenge_host,
#             'challenge_categories': categories
#         }
#
#         db.challenge.insert_one(doc)
#
#         return jsonify({'msg': "챌린지 등록 되었습니다."})
#     except jwt.ExpiredSignatureError:
#         return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
#     except jwt.exceptions.DecodeError:
#         return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
#
#
# @application.route('/challenge', methods=['DELETE'])
# def delete_challenge():
#     challengeId_receive = request.form['challengeId_give']
#     db.challenge.delete_one({'_id': ObjectId(challengeId_receive)})
#     db.join.delete_many({'join_challenge': challengeId_receive})
#     return jsonify({'result': 'success', 'msg': '챌린지 삭제 되었습니다.'})
#
#
# @application.route('/challenge/check', methods=['POST'])
# def challenge_check():
#     token_receive = request.cookies.get('mytoken')
#     try:
#         payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
#
#         user_id = payload['id']
#
#         challenge_receive = request.form["challenge_give"]
#         cont_receive = request.form["cont_give"]
#         file = request.files["img_give"]
#
#         extension = file.filename.split('.')[-1]
#
#         today = datetime.now()
#         mytime = today.strftime("%Y-%m-%d-%H-%M-%S")
#         uploadtime = today.strftime("%Y-%m-%d")
#
#         filename = f'file-{mytime}'
#
#         save_to = f'static/assets/img/join/{filename}.{extension}'
#         file.save(save_to)
#
#         doc = {
#             'join_challenge': challenge_receive,
#             'join_date': uploadtime,
#             'join_user': user_id,
#             'join_cont': cont_receive,
#             'join_img': f'{filename}.{extension}',
#         }
#
#         db.join.insert_one(doc)
#         return jsonify({'msg': "챌린지 인증 되었습니다."})
#     except jwt.ExpiredSignatureError:
#         return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
#     except jwt.exceptions.DecodeError:
#         return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))
#
#
# # 수빈님 code end
#
# # 현규님 code start
# def objectIdDecoder(list):
#     results = []
#     for document in list:
#         document['_id'] = str(document['_id'])
#         results.append(document)
#     return results


# 현규님 code end

if __name__ == '__main__':
    application.debug = True
    application.run()
