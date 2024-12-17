import os
import speech_recognition as sr
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
from tensorflow.keras import backend as K
from konlpy.tag import Kkma
import re
import cv2
from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from db import *
import tensorflow as tf
import threading
import sys
from konlpy.tag import Hannanum
from geopy.geocoders import Nominatim
import random
from playsound import playsound
from datetime import datetime, timedelta

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app,cors_allowed_origins="*")

# 학습된 모델 및 토크나이저 경로
MODEL_PATH = "./data/speech_intent_model2.keras"
TOKENIZER_PATH = "./data/tokenizer2.pkl"

# 의도 라벨 정의
LABEL_DICT = {0: "로보 호출", 1: "목적지 지정", 2: "하차", 3: "의미 없음",4:"부정", 5:"긍정"}

MAX_LEN = 30

# Focal Loss 정의
def focal_loss(gamma=2., alpha=0.25):
    def focal_loss_fixed(y_true, y_pred):
        epsilon = K.epsilon()
        y_pred = K.clip(y_pred, epsilon, 1. - epsilon)
        pt = tf.where(K.equal(y_true, 1), y_pred, 1 - y_pred)
        return -K.sum(alpha * K.pow(1. - pt, gamma) * K.log(pt))
    return focal_loss_fixed

# 모델 및 토크나이저 로드
try:
    model = load_model(MODEL_PATH, custom_objects={"focal_loss_fixed": focal_loss()})
    with open(TOKENIZER_PATH, "rb") as f:
        tokenizer = pickle.load(f)
except Exception as e:
    print(f"모델 로드 오류: {e}")
    sys.exit(1)

# 음성 인식 초기화
recognizer = sr.Recognizer()
kkma = Kkma()

global target
cap = None

def initialize_camera():
    global cap
    global target
    cap = cv2.VideoCapture(2)
    target = None
    
def generate_frames():
    global cap
    if cap is None:
        initialize_camera()

    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
#YOLO 모델 경로
# MODEL_PATH_YOLO = "/home/dw/ws/git_ws/deeplearning-repo-2/remote/main_server/data/traffic_light_best.pt"

# # 모델 로딩 (CPU로 변경)
# model_yolo = YOLO(MODEL_PATH_YOLO)

# def initialize_camera():
#     global cap
#     global target
#     cap = cv2.VideoCapture(2)  # 카메라 인덱스 확인 필요
#     target = None

# def generate_frames():
#     global cap
#     if cap is None:
#         initialize_camera()

#     while True:
#         success, frame = cap.read()
#         if not success:
#             cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#             continue
#         # #BGR -> RGB 변환
#         # frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         # # YOLO 추론
#         # results = model_yolo.predict(frame_rgb)
#         results = model_yolo.predict(frame)
#         # 결과 체크 후 plot
#         if len(results) > 0:
#             annotated_frame = results[0].plot()
#         else:
#             # 검출 없는 경우 원본 프레임 사용
#             annotated_frame = frame
#         # JPG 인코딩
#         _, buffer = cv2.imencode('.jpg', annotated_frame)
#         frame_data = buffer.tobytes()

#         # YIELD로 이미지 바이너리 스트림 반환
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
def respond_yes():
    playsound("./data/calling.wav")

def check_des():
    playsound("./data/check_destination.wav")

def retake_des():
    playsound("./data/retake_destination.wav")

def go_des():
    playsound("./data/go_destination.wav")

def not_understand():
    playsound("./data/not_understand.wav")

def play_feedback_wav():
    playsound("feedback.wav")
    
from gtts import gTTS

def create_feedback_wav(text):
    tts = gTTS(text=text, lang='ko')
    tts.save("feedback.wav")

def get_address_from_lat_long(latitude, longitude):
    """
    위도와 경도를 입력받아 해당하는 주소를 반환하는 함수

    args:
        latitude: 위도
        longitude: 경도
    
    return
        주소(string)
    """
    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.reverse((latitude, longitude), language="ko")
    if location is not None:
        address = location.address
        return address
    else:
        return "주소를 찾을 수 없습니다."

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/select_data', methods=['POST']) # need select query changed
def get_data():
    criteria = request.json
    start_date = criteria.get('startDate')
    end_date = criteria.get('endDate')
    search_value = criteria.get('searchValue')

    query = """
    SELECT 
        taxi.taxi_id AS taxi_id,
        users.username AS username,
        users.phone_number AS phone_number,
        taxi_operation.start_time AS start_time,
        taxi_operation.end_time AS end_time,
        taxi_operation.distance AS distance,
        taxi_operation.charge AS charge,
        taxi_operation.video_path AS start_location,
        taxi_operation.target AS destination
    FROM 
        taxi_operation
    JOIN 
        taxi ON taxi_operation.taxi_id = taxi.taxi_id
    JOIN 
        users ON taxi_operation.user_id = users.user_id
    """

    params = []
    if not start_date and not end_date and not search_value:
        query += ""
    else:
        query += "WHERE 1=1 "
        if start_date and end_date:
            query += "AND taxi_operation.start_time BETWEEN %s AND %s "
            params += [start_date, end_date]
        if search_value:
            query += "AND (taxi.taxi_id LIKE %s OR users.username LIKE %s OR users.phone_number LIKE %s) "
            params += [f"%{search_value}%", f"%{search_value}%", f"%{search_value}%"]

    raw_data = execute_query(query, params)

    data = [
        {
            "taxi_id": row[0],
            "username": row[1],
            "phone_number": row[2],
            "start_time": row[3].isoformat(),
            "end_time": row[4].isoformat(),
            "distance": row[5],
            "charge": row[6],
            "start_location": row[7],
            "destination": row[8]
        }
        for row in raw_data
    ]

    return jsonify(data)

@app.route('/revenue', methods=['POST'])
def get_revenue():
    criteria = request.json
    taxi_id = criteria.get('taxiId')
    start_date = criteria.get('startDate')
    end_date = criteria.get('endDate')

    query = """
    SELECT SUM(taxi_operation.charge) AS total_revenue
    FROM taxi_operation
    WHERE 1=1
    """

    params = []
    if taxi_id:
        query += " AND taxi_operation.taxi_id = %s"
        params.append(taxi_id)

    if start_date and end_date:
        query += " AND taxi_operation.start_time BETWEEN %s AND %s"
        params.append(start_date)
        params.append(end_date)

    total_revenue = execute_query(query, params)

    result = {
        "taxi_id": taxi_id if taxi_id else "All",
        "total_revenue": total_revenue[0][0] if total_revenue else 0
    }

    return jsonify(result)

@app.route('/taxi_list', methods=['GET'])
def get_taxi_list():
    query = "SELECT taxi_id, taxi_type FROM taxi"
    raw_data = execute_query(query)

    data = [
        {
            "taxi_id": row[0],
            "taxi_type": row[1],
        }
        for row in raw_data
    ]

    return jsonify(data)

@app.route('/user_revenue', methods=['POST'])
def get_user_revenue():
    criteria = request.json
    user_id = criteria.get('userId')
    start_date = criteria.get('startDate')
    end_date = criteria.get('endDate')

    query = """
    SELECT SUM(charge) AS total_revenue
    FROM taxi_operation
    WHERE user_id = %s
    """

    params = [user_id]

    if start_date and end_date:
        query += " AND start_time BETWEEN %s AND %s"
        params += [start_date, end_date]

    total_revenue = execute_query(query, params)

    result = {
        "user_id": user_id,
        "total_revenue": total_revenue[0][0] if total_revenue else 0
    }

    return jsonify(result)

@app.route('/users', methods=['GET'])
def get_users():
    query = "SELECT user_id, username FROM users"
    raw_data = execute_query(query)

    data = [
        {
            "user_id": row[0],
            "username": row[1],
        }
        for row in raw_data
    ]

    return jsonify(data)

@app.route('/get_target', methods=['GET'])
def get_target():
    global target
    return str(target)

@app.route('/address', methods=['POST'])
def get_address():
    """
    args
        json
        {
            "latitude" : 위도,
            "longitude": 경도
        }
    return
        json
        {
            "address": 주소
        }
    """
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    if latitude is None or longitude is None:
        return jsonify({'error': '위도와 경도를 모두 입력해야 합니다.'}), 400

    address = get_address_from_lat_long(latitude, longitude)
    return jsonify({'address': address})

@app.route('/get_lat_long', methods=['POST'])
def get_lat_long():
    """
    args
        json
        {
            "address": 주소
        }
    return
        json
        {
            "latitude": 위도,
            "longitude": 경도
        }
    """
    data = request.get_json()
    address = data.get('address')

    if not address:
        return jsonify({'error': '주소를 입력해야 합니다.'}), 400

    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(address, language="ko")

    if location:
        return jsonify({
            'latitude': location.latitude,
            'longitude': location.longitude
        })
    else:
        return jsonify({'error': '주소를 찾을 수 없습니다.'}), 404
    
def emit_lat_long(address):
    """
    주어진 주소를 위경도로 변환하고 SocketIO를 통해 emit하는 함수.

    args:
        address: 변환할 주소(string)
    """
    if not address:
        print("주소가 제공되지 않았습니다.")
        return
    
    print(address)

    geolocator = Nominatim(user_agent="my_geocoder")
    location = geolocator.geocode(address, language="ko")

    if location:
        latitude = location.latitude
        longitude = location.longitude
        # SocketIO로 emit
        socketio.emit('target_updated', {'target': address, 'latitude': latitude, 'longitude': longitude}, namespace='target_origin')
        print(f"주소: {address} -> 위도: {latitude}, 경도: {longitude} 전송 완료.")
    else:
        print("주소를 찾을 수 없습니다.")

@app.route('/random_taxi', methods=['GET'])
def random_taxi():
    query = "SELECT taxi_id, taxi_type, taxi_license FROM taxi WHERE status = 0"
    raw_data = execute_query(query)

    if not raw_data:
        return jsonify({"message": "사용 가능한 택시가 없습니다."}), 404

    random_taxi = random.choice(raw_data)

    response = {
        "taxi_id": random_taxi[0],
        "taxi_type": random_taxi[1],
        "taxi_license": random_taxi[2]
    }
    print(response)
    return jsonify(response)

# @app.route('/call_taxi', methods=['POST'])
# def call_taxi():
#     try:
#         data = request.json
#         user_id = data.get('userId')
#         start_point = data.get('startPoint')
#         end_point = data.get('endPoint')

#         # 데이터 유효성 검사
#         if not user_id or not start_point or not end_point:
#             return jsonify({'error': '필수 데이터가 누락되었습니다.'}), 400

#         # 랜덤으로 사용 가능한 택시 선택 (taxi_id, taxi_type, taxi_license를 포함)
#         query = "SELECT taxi_id, taxi_type, taxi_license FROM taxi WHERE status = true ORDER BY RAND() LIMIT 1"
#         raw_data = execute_query(query)

#         if not raw_data:
#             return jsonify({'message': '사용 가능한 택시가 없습니다.'}), 404

#         taxi_id, taxi_type, taxi_license = raw_data[0]  # 택시 정보 추출
#         # print(raw_data[0])
#         start_time = datetime.now()
#         pred_end_time = start_time + timedelta(minutes=15)

#         # charge를 10으로 설정
#         charge = 10

#         # 마지막 taxi_operation의 video_path 가져오기
#         video_query = "SELECT video_path FROM taxi_operation ORDER BY to_id DESC LIMIT 1"
#         last_video_data = execute_query(video_query)
#         print(last_video_data[0][0])

#         if last_video_data:
#             last_video_path = last_video_data[0][0]  # 마지막 video_path 가져오기
#             # 'video_'와 숫자 부분을 분리
#             base_video_path = last_video_path.rsplit('_', 1)[0]  # 'video_' 부분
#             last_number = int(last_video_path.rsplit('_', 1)[1])  # 마지막 숫자
#             new_number = last_number + 1  # 새로운 숫자 생성
#             new_video_path = f"{base_video_path}_{new_number}"  # 새로운 video_path 생성
#         else:
#             new_video_path = "video_1"  # 첫 번째 비디오가 없을 경우 기본값

#         # 택시 호출 기록 저장
#         insert_query = """
#             INSERT INTO taxi_operation (taxi_id, user_id, start_time, pred_end_time, start_point, end_point, charge, video_path)
#             VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
#         """
#         execute_query(insert_query, (taxi_id, user_id, start_time, pred_end_time, start_point, end_point, charge, new_video_path))
#         print(insert_query, (taxi_id, user_id, start_time, pred_end_time, start_point, end_point, charge, new_video_path))

#         # # 택시 상태 업데이트
#         # execute_query("UPDATE taxi SET status = false WHERE taxi_id = %s", (taxi_id,))

#         # 응답에 택시 정보 포함
#         return jsonify({
#             'message': '택시 호출 성공',
#             'taxiId': taxi_id,
#             'taxiType': taxi_type,
#             'taxiLicense': taxi_license,
#             'videoPath': new_video_path
#         }), 200
#     except Exception as e:
#         print(f"서버 오류: {e}")
#         return jsonify({'error': '서버에서 오류가 발생했습니다.'}), 500
@app.route('/call_taxi', methods=['POST'])
def call_taxi():
    try:
        data = request.json
        user_id = data.get('userId')
        start_point = data.get('startPoint')
        end_point = data.get('endPoint')

        # 데이터 유효성 검사
        if not user_id or not start_point or not end_point:
            return jsonify({'error': '필수 데이터가 누락되었습니다.'}), 400

        # 랜덤으로 사용 가능한 택시 선택
        query = "SELECT taxi_id, taxi_type, taxi_license FROM taxi WHERE status = true ORDER BY RAND() LIMIT 1"
        raw_data = execute_query(query)

        if not raw_data:
            return jsonify({'message': '사용 가능한 택시가 없습니다.'}), 404

        taxi_id, taxi_type, taxi_license = raw_data[0]  # 택시 정보 추출
        start_time = datetime.now()
        pred_end_time = start_time + timedelta(minutes=15)

        # charge를 10으로 설정
        charge = 10

        # video_path를 'video_path_test'로 하드코딩
        new_video_path = "video_path_test"

        # 택시 호출 기록 저장
        insert_query = """
            INSERT INTO taxi_operation (taxi_id, user_id, start_time, pred_end_time, start_point, end_point, charge, video_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(insert_query, (taxi_id, user_id, start_time, pred_end_time, start_point, end_point, charge, new_video_path))
        print(insert_query, (taxi_id, user_id, start_time, pred_end_time, start_point, end_point, charge, new_video_path))

        # 택시 상태 업데이트
        execute_query("UPDATE taxi SET status = false WHERE taxi_id = %s", (taxi_id,))

        # 응답에 택시 정보 포함
        return jsonify({
            'message': '택시 호출 성공',
            'taxiId': taxi_id,
            'taxiType': taxi_type,
            'taxiLicense': taxi_license,
            'videoPath': new_video_path
        }), 200
    except Exception as e:
        print(f"서버 오류: {e}")
        return jsonify({'error': '서버에서 오류가 발생했습니다.'}), 500
    
# voice2.py에서 목표 값 수신
@socketio.on('target_updated')
def handle_update_target(data):
    global target
    print(data)
    print(data.get('target_updated'))
    target = data.get('target_updated')
    print(f"목표 위치 업데이트됨: {target}")
    
    # 웹 클라이언트로 브로드캐스트
    socketio.emit('target_updated', {'target_updated': target})
    print(target)
    
@socketio.on('target_checked')
def handle_checked_target(data):
    global target
    print(data)
    print(data.get('target_checked'))
    target = data.get('target_checked')
    print(f"목표 위치 업데이트됨: {target}")
    
    # 웹 클라이언트로 브로드캐스트
    socketio.emit('target_checked', {'target_checked': target})
    print(target)


# def run_voice_recognition():
#     while True:
#         voice_to_intent()

# def run_flask_server():
    # app.run(host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    # threading.Thread(target=run_voice_recognition, daemon=True).start()
    # run_flask_server()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
