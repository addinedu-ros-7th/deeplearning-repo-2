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

cap = None
global target

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

def respond_yes():
    playsound("./data/respond_yes.wav")
    
def check_des():
    playsound("./data/check_destination.wav")
    
def retake_des():
    playsound("./data/retake_destination.wav")

def go_des():
    playsound("./data/go_destination.wav")

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

# 주어 추출 함수
def extract_subject_des(text):
    try:
        # 1단계: 텍스트 정리 (불필요한 어미 제거)
        text = re.sub(r"(가자|줘|으로|로|가)$", "", text).strip()

        # 2단계: 숫자와 단위 연결 (띄어쓰기 처리)
        text = re.sub(r"(\d+)\s+(번|층|호|출구)", r"\1\2", text)

        # 3단계: 하이픈 연결 (숫자-숫자 형태 유지)
        text = re.sub(r"(\d+)\s*-\s*(\d+)", r"\1-\2", text)

        # 4단계: Hannanum 명사 추출
        hannanum = Hannanum()
        nouns = hannanum.nouns(text)

        # 5단계: 숫자와 단위를 결합
        combined_text = " ".join(nouns)
        combined_text = re.sub(r"(\d+)(번|층|호|출구)", r"\1\2", combined_text)

        # 6단계: 불필요한 단어 제거 (텍스트 끝에 남은 '으로', '로' 처리)
        result = re.sub(r"(으로|로)$", "", combined_text.replace(" ", "")).strip()

        return result if result else None
    except Exception as e:
        return f"주어 추출 중 오류: {e}"

def extract_subject_hacha(text):
    try:
        # 1단계: 불필요한 어미 제거
        text = re.sub(r"(내려줘|세워줘|멈춰|으로|로|가)$", "", text).strip()

        # 2단계: Hannanum 명사 추출
        hannanum = Hannanum()
        nouns = hannanum.nouns(text)

        # 3단계: 의미 있는 단어 결합
        combined_text = " ".join(nouns)

        # 4단계: 위치 관련 표현 정리 (띄어쓰기와 불필요한 단어 제거)
        combined_text = re.sub(r"(앞|뒤|여기|저기|지금|바로|횡단보도|카페|길|사거리|코너)", r" \1", combined_text)
        result = combined_text.replace(" ", "").strip()

        return result if result else None
    except Exception as e:
        return f"하차 주어 추출 중 오류: {e}"

# 주어 추출 함수
def extract_subject(text):
    try:
        # 1단계: 텍스트 정리 (불필요한 어미 제거)
        text = re.sub(r"(가자|줘|으로|로|가)$", "", text).strip()

        # 2단계: Hannanum 명사 추출
        hannanum = Hannanum()
        nouns = hannanum.nouns(text)

        # 3단계: 숫자와 단위를 결합
        combined_text = " ".join(nouns)
        combined_text = re.sub(r"(\d+)(번|층|호|출구)", r"\1\2", combined_text)

        # 4단계: 불필요한 단어 제거 (텍스트 끝에 남은 '으로', '로' 처리)
        result = re.sub(r"(으로|로)$", "", combined_text.replace(" ", "")).strip()

        return result if result else None
    except Exception as e:
        return f"주어 추출 중 오류: {e}"

# 호출 상태를 관리하는 변수
is_robot_called = False
# 온도 조정된 예측 함수
def predict_with_temperature_adjustment(text, threshold=0.7, gap_threshold=0.3, temperature=1.0):
    global is_robot_called
    global target
    try:
        sequence = tokenizer.texts_to_sequences([text])
        padded_sequence = pad_sequences(sequence, maxlen=MAX_LEN, padding="post")
        logits = model.predict(padded_sequence) / temperature
        confidence = np.max(logits)
        predicted_label = np.argmax(logits)
        second_highest = sorted(logits.flatten())[-2]
        confidence_gap = confidence - second_highest
        label_scores = ", ".join([f"{LABEL_DICT[i]}: {logits[0][i]:.2f}" for i in range(len(LABEL_DICT))])
        
        # 로보 호출 처리
        if predicted_label == 0 and confidence >= threshold:
            is_robot_called = True  # 호출 상태 활성화
            respond_yes() # 로보 호출 확인 음성
            return f"'{text}' -> 예측: 로보 호출 (신뢰도: {confidence:.2f}), {label_scores}, 응답: 네"
        
        # 로보 호출이 활성화된 상태에서만 나머지 판단
        if is_robot_called:
            if predicted_label == 1 and confidence >= threshold:
                subject = extract_subject_des(text)
                target = subject
                check_des()
                print("목적지가 맞나 확인합니다.")
                return f"'{text}' -> 예측: {LABEL_DICT.get(predicted_label, '알 수 없음')} (신뢰도: {confidence:.2f}), {label_scores}, 추출된 주어: {subject}"
            
            elif predicted_label == 4 and confidence >= threshold:
                print("목적지를 새로 입력하세요")
                retake_des()
            
            elif predicted_label == 5 and confidence >= threshold:
                print("목적지가 확정 되었습니다")
                go_des()
                socketio.emit('target_updated', {'target': target})
                is_robot_called = False # 확정되면 상태 초기화 
            
            elif predicted_label == 2 and confidence >= threshold:
                subject2 = extract_subject_hacha(text)
                target = subject2
                is_robot_called = False # 하차한다고하면 상태 초기화
            
            elif predicted_label == 3:
                is_robot_called = False  # 의미 없음이라도 상태 초기화
                return f"'{text}' -> 최종 결과: 의미 없음 (신뢰도: {confidence:.2f}), {label_scores}"

        # 호출되지 않은 상태에서 다른 라벨 입력
        return f"'{text}' -> 로보 호출 대기 중: {label_scores}"

    except Exception as e:
        return f"예측 중 오류 발생: {e}"

# 음성을 의도로 변환
def voice_to_intent():
    """실시간 음성 인식을 통해 텍스트를 의도로 변환"""
    with sr.Microphone() as source:
        print("음성 인식 준비 중...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        recognizer.pause_threshold = 2.0
        print("준비 완료! 말씀하세요 (Ctrl+C로 종료)")

        # while True:  # 지속적으로 음성을 처리하기 위해 반복
        try:
            print("음성을 기다리는 중...")
            audio = recognizer.listen(source, timeout=None)
            print("음성을 처리 중입니다...")

            text = recognizer.recognize_google(audio, language="ko-KR")
            print(f"인식된 텍스트: {text}")

            prediction = predict_with_temperature_adjustment(text)
            print(f"예측 결과: {prediction}")

        except sr.UnknownValueError:
            print("음성을 인식할 수 없습니다.")
        except KeyboardInterrupt:
            print("음성 인식이 중단되었습니다.")
        except Exception as e:
            print(f"예기치 못한 오류 발생: {e}")

def run_voice_recognition():
    while True:
        voice_to_intent()

def run_flask_server():
    # app.run(host='0.0.0.0', port=5000, debug=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)

if __name__ == '__main__':
    threading.Thread(target=run_voice_recognition, daemon=True).start()
    run_flask_server()