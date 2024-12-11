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

app = Flask(__name__)
# CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app,cors_allowed_origins="*")

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

MODEL_PATH = "./data/speech_intent_model.h5"
TOKENIZER_PATH = "./data/tokenizer.pkl"
LABEL_DICT = {0: "로보 호출", 1: "목적지 지정", 2: "하차", 3: "의미 없음"}
MAX_LEN = 30

def focal_loss(gamma=2., alpha=0.25):
    def focal_loss_fixed(y_true, y_pred):
        epsilon = K.epsilon()
        y_pred = K.clip(y_pred, epsilon, 1. - epsilon)
        pt = tf.where(K.equal(y_true, 1), y_pred, 1 - y_pred)
        return -K.sum(alpha * K.pow(1. - pt, gamma) * K.log(pt))
    return focal_loss_fixed

model = load_model(MODEL_PATH, custom_objects={"focal_loss_fixed": focal_loss()})

with open(TOKENIZER_PATH, "rb") as f:
    tokenizer = pickle.load(f)

recognizer = sr.Recognizer()

kkma = Kkma()

def extract_subject(text):
    morphs = kkma.pos(text)
    subject = []
    current_noun = ''

    for word, pos in morphs:
        if pos in ['NNG', 'NNP']:
            current_noun += word
        else:
            if current_noun:
                subject.append(current_noun)
                current_noun = ''

    if current_noun:
        subject.append(current_noun)

    address_pattern = re.compile(r'([가-힣]+)\s?(\d{1,5}-\d{1,5})')
    address_matches = address_pattern.findall(text)
    for match in address_matches:
        subject.append(match[0] + " " + match[1])

    return subject

def predict_with_temperature_adjustment(text, threshold=0.6, gap_threshold=0.3, temperature=1.2):
    sequence = tokenizer.texts_to_sequences([text])
    padded_sequence = pad_sequences(sequence, maxlen=MAX_LEN, padding="post")

    logits = model.predict(padded_sequence) / temperature
    confidence = np.max(logits)
    predicted_label = np.argmax(logits)
    second_highest = np.partition(logits.flatten(), -2)[-2]
    confidence_gap = confidence - second_highest

    label_scores = {LABEL_DICT[i]: logits[0][i] for i in range(len(LABEL_DICT))}

    if confidence < threshold or confidence_gap < gap_threshold:
        result = f"'{text}' -> 최종 결과: 의미 없음 (신뢰도: {confidence:.2f})\n"
        result += "라벨별 점수:"
        result += " ".join([f"{label}: {score:.2f}" for label, score in label_scores.items()])
        return result, None

    result = f"'{text}' -> 예측: {LABEL_DICT.get(predicted_label, '알 수 없음')} (신뢰도: {confidence:.2f})\n"
    result += "라벨별 점수:"
    result +=  " ".join([f"{label}: {score:.2f}" for label, score in label_scores.items()])

    if predicted_label in [1, 2] and confidence >= threshold:
        subject = extract_subject(text)
        result += f"\n추출된 주어: {subject}"
        return result, subject

    return result, None

def voice_to_intent():
    global target
    with sr.Microphone() as source:
        print("말씀하세요 (Ctrl+C로 종료):")
        try:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            recognizer.energy_threshold = 2000
            print("음성을 기다리는 중...")
            audio = recognizer.listen(source)
            print("음성을 처리 중입니다...")
            text = recognizer.recognize_google(audio, language="ko-KR")
            print(f"인식된 텍스트: {text}")

            intent_details, subject = predict_with_temperature_adjustment(text)

            if subject:
                print(f"주어 추출 결과: {subject}")
                target = subject
                socketio.emit('target_updated', {'target': target})
        except sr.UnknownValueError:
            print("음성을 인식할 수 없습니다.")
        except sr.RequestError as e:
            print(f"Google Speech Recognition 서비스에 접근할 수 없습니다: {e}")

def run_voice_recognition():
    while True:
        voice_to_intent()

def run_flask_server():
    # app.run(host='0.0.0.0', port=5000, debug=True)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)

if __name__ == '__main__':
    threading.Thread(target=run_voice_recognition, daemon=True).start()
    run_flask_server()