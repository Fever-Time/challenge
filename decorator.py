import jwt
import os
from dotenv import load_dotenv
from functools import wraps
from flask import request, redirect, url_for

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')
TOKEN_NAME = 'fever-time'


def login_required(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        token_receive = request.cookies.get(TOKEN_NAME)
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            user_id = payload['id']
            request.user_id = user_id

            return func(*args, **kwargs)

        except jwt.ExpiredSignatureError:
            return redirect(url_for('login', msg='로그인 시간이 만료되었습니다.'))
        except jwt.exceptions.DecodeError:
            return redirect(url_for('login', msg='로그인 정보가 존재하지 않습니다.'))

    return decorated_function
