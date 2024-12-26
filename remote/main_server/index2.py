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
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app,cors_allowed_origins="*")
KAKAO_REST_API_KEY = "fa9b778e6585289e190dc4ca50d395ed"
# 음성 인식 초기화

global target
cap = None

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

cap = None
last_frame = None

# YOLO 모델 로드
MODEL_PATH_YOLO_1 = "./data/traffic_sign.pt"
MODEL_PATH_YOLO_2 = "./data/traffic_light_90000.pt"

model_yolo_1 = YOLO(MODEL_PATH_YOLO_1)  # 교통 표지판 모델
model_yolo_2 = YOLO(MODEL_PATH_YOLO_2)  # 신호등 모델

def initialize_camera():
    """카메라 초기화"""
    global cap
    if cap is None:
        cap = cv2.VideoCapture(0)  # 카메라 열기
    if not cap.isOpened():
        print("Error: 카메라를 열 수 없습니다.")
        exit()

def read_frame():
    """프레임 읽기"""
    global cap, last_frame
    if cap is None:
        initialize_camera()
    
    success, frame = cap.read()
    if success:
        last_frame = frame.copy()  # 성공적으로 읽은 프레임 저장
    return last_frame

def process_frame_with_yolo(frame):
    """YOLO 모델로 프레임 처리"""
    combined_frame = frame.copy()

    # YOLO 모델 1 결과 처리 (교통 표지판)
    results1 = model_yolo_1(frame, conf=0.4, iou=0.35, verbose=False)
    if results1 and results1[0].boxes is not None:
        for box in results1[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = f"{results1[0].names[int(box.cls[0])]} {box.conf[0]:.2f}"
            cv2.rectangle(combined_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(combined_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # YOLO 모델 2 결과 처리 (신호등)
    results2 = model_yolo_2(frame, conf=0.4, iou=0.35, verbose=False)
    if results2 and results2[0].boxes is not None:
        for box in results2[0].boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            label = f"{results2[0].names[int(box.cls[0])]} {box.conf[0]:.2f}"
            cv2.rectangle(combined_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(combined_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    return combined_frame

def generate_frames():
    """클라이언트에게 프레임 스트리밍"""
    while True:
        frame = read_frame()  # 전역적으로 관리되는 프레임 읽기
        if frame is None:
            continue

        # YOLO 모델 처리
        processed_frame = process_frame_with_yolo(frame)

        # JPG 인코딩
        _, buffer = cv2.imencode('.jpg', processed_frame)
        frame_data = buffer.tobytes()
        
        # HTTP 스트림 형식으로 반환
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

@app.route('/select_data', methods=['POST'])
def get_data():
    criteria = request.json
    start_date = criteria.get('startDate')
    end_date = criteria.get('endDate')
    search_value = criteria.get('searchValue')
    search_by_taxi_id = criteria.get('searchByTaxiId')  # 체크박스 상태

    print(search_by_taxi_id, search_value)

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
        taxi_operation.start_point AS start_point,  -- start_point 추가
        taxi_operation.end_point AS end_point,      -- end_point 추가
        taxi_operation.end_point AS destination       -- destination 추가
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
            if search_by_taxi_id:
                # taxi_id로만 검색
                query += "AND taxi.taxi_id LIKE %s "
                params.append(f"%{search_value}%")
            else:
                # 모든 컬럼에 대해 검색
                query += "AND ("
                query += "taxi.taxi_id LIKE %s OR "
                query += "users.username LIKE %s OR "
                query += "users.phone_number LIKE %s OR "
                query += "taxi_operation.distance LIKE %s OR "
                query += "taxi_operation.charge LIKE %s OR "
                query += "taxi_operation.video_path LIKE %s OR "
                query += "taxi_operation.start_point LIKE %s OR "  # start_point 추가
                query += "taxi_operation.end_point LIKE %s"  # end_point 추가
                query += ") "
                params += [f"%{search_value}%"] * 8  # 모든 검색 조건에 대해 search_value 사용

    raw_data = execute_query(query, params)
    print(raw_data)
    data = [
        {
            "taxi_id": row[0],
            "username": row[1],
            "phone_number": row[2],
            "start_time": row[3].isoformat(),
            "end_time": row[4].isoformat() if row[4] else None,
            "distance": row[5],
            "charge": row[6],
            "start_location": row[7],
            "start_point": row[8],  # start_point 반환
            "end_point": row[9],    # end_point 반환
            "destination": row[10]   # destination 반환
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

# 택시 하차
@app.route('/drop_taxi', methods=['POST'])
def drop_taxi():
    data = request.json
    taxi_id = data['taxiId']
    
    # 현재 시간을 end_time으로 설정
    end_time = datetime.now()

    try:
        # 택시 상태를 0으로 업데이트 (하차)
        update_taxi_query = "UPDATE taxi SET status = 0 WHERE taxi_id = %s"
        execute_query(update_taxi_query, (taxi_id,))

        # 택시의 마지막 운행 정보를 업데이트 (end_time)
        update_operation_query = """
            UPDATE taxi_operation 
            SET end_time = %s 
            WHERE taxi_id = %s AND end_time IS NULL
            ORDER BY start_time DESC 
            LIMIT 1
        """
        execute_query(update_operation_query, (end_time, taxi_id))

        return jsonify({"message": "택시 하차 완료."}), 200
    except Exception as e:
        print(f"서버 오류: {e}")
        return jsonify({"error": "하차 중 오류가 발생했습니다."}), 500

    
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

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
