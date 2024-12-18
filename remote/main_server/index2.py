import os
import speech_recognition as sr
import numpy as np
import pickle
import re
import cv2
from flask import Flask, Response, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from db import *
import sys
from konlpy.tag import Hannanum
from geopy.geocoders import Nominatim
import random
from datetime import datetime, timedelta
from ultralytics import YOLO
import torch
import requests

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app,cors_allowed_origins="*")
KAKAO_REST_API_KEY = "fa9b778e6585289e190dc4ca50d395ed"
# 음성 인식 초기화

global target
cap = None

# def initialize_camera():
#     global cap
#     global target
#     cap = cv2.VideoCapture(2)
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

#         _, buffer = cv2.imencode('.jpg', frame)
#         frame_data = buffer.tobytes()

#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

# # YOLO 모델 경로
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
        
        
# # YOLO 모델 경로
# MODEL_PATH_YOLO_2 = "/home/dw/ws/git_ws/deeplearning-repo-2/remote/main_server/data/traffic_light_90000.pt"
# MODEL_PATH_YOLO_1 = "/home/dw/ws/git_ws/deeplearning-repo-2/remote/main_server/data/traffic_sign.pt"

# # GPU 확인
# if torch.cuda.is_available():
#     print("GPU 사용 가능:", torch.cuda.get_device_name(0))
# else:
#     print("GPU를 사용할 수 없습니다. CPU로 실행됩니다.")

# # 모델 로딩 (CPU 사용)
# model_yolo_1 = YOLO(MODEL_PATH_YOLO_1)
# model_yolo_2 = YOLO(MODEL_PATH_YOLO_2)
# print("YOLO 모델 1 실행 장치:", model_yolo_1.device)
# print("YOLO 모델 2 실행 장치:", model_yolo_2.device)
# # 비디오 파일 경로
# VIDEO_PATH = "/home/dw/ws/git_ws/deeplearning-repo-2/remote/main_server/data/drive_video_1_1.mp4"

# def initialize_camera():
#     global cap
#     cap = cv2.VideoCapture(VIDEO_PATH)  # MP4 파일 사용

# def generate_frames():
#     global cap
#     if cap is None:
#         initialize_camera()

#     frame_skip = 2  # 프레임 스킵
#     frame_count = 0

#     while True:
#         success, frame = cap.read()
#         if not success:
#             cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
#             continue

#         frame_count += 1
#         if frame_count % frame_skip != 0:
#             # 스킵된 프레임은 원본 그대로 전달
#             _, buffer = cv2.imencode('.jpg', frame)
#             frame_data = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
#             continue

#         # YOLO 추론
#         results1 = model_yolo_1.predict(frame, verbose=False)
#         results2 = model_yolo_2.predict(frame, verbose=False)

#         # 결과 병합
#         combined_frame = frame.copy()  # 원본 프레임 복사
#         if len(results1) > 0:
#             combined_frame = results1[0].plot(combined_frame)
#         if len(results2) > 0:
#             combined_frame = results2[0].plot(combined_frame)

#         # JPG 인코딩
#         _, buffer = cv2.imencode('.jpg', combined_frame)
#         frame_data = buffer.tobytes()

#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
def check_gpu():
    # GPU 확인
    if torch.cuda.is_available():
        print("GPU 사용 가능:", torch.cuda.get_device_name(0))
    else:
        print("GPU를 사용할 수 없습니다. CPU로 실행됩니다.")

# YOLO 모델 경로 설정
MODEL_PATH_YOLO_1 = "./data/traffic_sign.pt"
MODEL_PATH_YOLO_2 = "./data/traffic_light_90000.pt"

# GPU 확인
check_gpu()

# YOLO 모델 로드
model_yolo_1 = YOLO(MODEL_PATH_YOLO_1)  # 교통 표지판 모델
model_yolo_2 = YOLO(MODEL_PATH_YOLO_2)  # 신호등 모델
print("YOLO 모델 1 실행 장치:", model_yolo_1.device)
print("YOLO 모델 2 실행 장치:", model_yolo_2.device)

# 비디오 파일 경로 설정
VIDEO_PATH = "./data/drive_video_1_1.mp4"

def initialize_camera():
    # 비디오 파일 불러오기
    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        print("Error: 비디오 파일을 열 수 없습니다.")
        exit()
    return cap

def generate_frames():
    cap = initialize_camera()
    frame_skip = 2  # 프레임 스킵 비율
    frame_count = 0

    while True:
        success, frame = cap.read()
        if not success:  # 비디오 끝에서 다시 시작
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame_count += 1
        if frame_count % frame_skip != 0:
            # 프레임 스킵 적용
            _, buffer = cv2.imencode('.jpg', frame)
            frame_data = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
            continue

        # 두 YOLO 모델로 프레임 처리
        results1 = model_yolo_1(frame, conf=0.4, iou=0.35, verbose=False)
        results2 = model_yolo_2(frame, conf=0.4, iou=0.35, verbose=False)

        # 결과 병합 및 시각화
        combined_frame = frame.copy()
        if results1 and results1[0].boxes is not None:
            for box in results1[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = f"{results1[0].names[int(box.cls[0])]} {box.conf[0]:.2f}"
                cv2.rectangle(combined_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(combined_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        if results2 and results2[0].boxes is not None:
            for box in results2[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = f"{results2[0].names[int(box.cls[0])]} {box.conf[0]:.2f}"
                cv2.rectangle(combined_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                cv2.putText(combined_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        # JPG 인코딩
        _, buffer = cv2.imencode('.jpg', combined_frame)
        frame_data = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

    
from gtts import gTTS

def create_feedback_wav(text):
    tts = gTTS(text=text, lang='ko')
    tts.save("feedback.wav")

def get_address_from_lat_long(latitude, longitude):
    """
    위도, 경도를 카카오 로컬 API를 통해 주소로 변환
    """
    url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "x": longitude,  # 경도
        "y": latitude   # 위도
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        documents = data.get('documents', [])
        if documents:
            address_info = documents[0].get('address')
            if address_info:
                return address_info.get('address_name', "주소를 찾을 수 없습니다.")
    return "주소를 찾을 수 없습니다."

def get_lat_long_from_address(address):
    """
    주소를 카카오 로컬 API를 통해 위도/경도로 변환
    """
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"}
    params = {
        "query": address
    }

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        documents = data.get('documents', [])
        if documents:
            x = documents[0]['x']  # 경도
            y = documents[0]['y']  # 위도
            return float(y), float(x)
    return None, None
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
def address_api():
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

    lat, lon = get_lat_long_from_address(address)
    if lat is not None and lon is not None:
        return jsonify({
            'latitude': lat,
            'longitude': lon
        })
    else:
        return jsonify({'error': '주소를 찾을 수 없습니다.'}), 404

def emit_lat_long(address):
    """
    주어진 주소를 위경도로 변환하고 SocketIO를 통해 emit하는 함수.
    """
    if not address:
        print("주소가 제공되지 않았습니다.")
        return

    lat, lon = get_lat_long_from_address(address)
    if lat is not None and lon is not None:
        socketio.emit('target_updated', {'target': address, 'latitude': lat, 'longitude': lon}, namespace='target_origin')
        print(f"주소: {address} -> 위도: {lat}, 경도: {lon} 전송 완료.")
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
