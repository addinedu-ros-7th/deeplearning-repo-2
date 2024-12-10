import cv2
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from db import *

app = Flask(__name__)
CORS(app, resources={r"/*":{"origins":"http://localhost:3000"}})

# cap = cv2.VideoCapture(2)  # 비디오 파일 경로
cap = None

def initialize_camera():
    global cap
    cap = cv2.VideoCapture(2)

def generate_frames():
    global cap
    if cap is None:
        initialize_camera()
        
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 처음부터 다시 시작
            continue

        # 프레임을 JPEG 형식으로 인코딩
        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = buffer.tobytes()

        # 클라이언트로 프레임 전송
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/select_data', methods=['POST'])
def get_data():
    criteria = request.json  # JSON 형식으로 조건을 받음
    start_date = criteria.get('startDate')  # 시작 날짜
    end_date = criteria.get('endDate')      # 종료 날짜
    search_value = criteria.get('searchValue')  # 검색 값

    # 기본 쿼리
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

    # 조건이 없을 경우, 모든 데이터를 조회
    params = []
    if not start_date and not end_date and not search_value:
        query += ""  # WHERE 절 없이 모든 데이터 조회
    else:
        query += "WHERE 1=1 "  # 기본 조건 추가
        if start_date and end_date:
            query += "AND taxi_operation.start_time BETWEEN %s AND %s "
            params += [start_date, end_date]
        if search_value:
            query += "AND (taxi.taxi_id LIKE %s OR users.username LIKE %s OR users.phone_number LIKE %s) "
            params += [f"%{search_value}%", f"%{search_value}%", f"%{search_value}%"]

    # execute_query 함수를 사용하여 데이터 조회
    raw_data = execute_query(query, params)

    # 응답을 JSON 형식으로 변환
    data = [
        {
            "taxi_id": row[0],
            "username": row[1],
            "phone_number": row[2],
            "start_time": row[3].isoformat(),  # ISO 포맷으로 변환
            "end_time": row[4].isoformat(),    # ISO 포맷으로 변환
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

    # 기본 쿼리
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

    # execute_query 함수를 사용하여 데이터 조회
    total_revenue = execute_query(query, params)

    # 결과를 JSON 형식으로 변환
    result = {
        "taxi_id": taxi_id if taxi_id else "All",
        "total_revenue": total_revenue[0][0] if total_revenue else 0
    }

    return jsonify(result)

@app.route('/taxi_list', methods=['GET'])
def get_taxi_list():
    query = "SELECT taxi_id, taxi_type FROM taxi"
    raw_data = execute_query(query)

    # 응답을 JSON 형식으로 변환
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

    # 기본 쿼리
    query = """
    SELECT SUM(charge) AS total_revenue
    FROM taxi_operation
    WHERE user_id = %s
    """

    params = [user_id]

    if start_date and end_date:
        query += " AND start_time BETWEEN %s AND %s"
        params += [start_date, end_date]

    # execute_query 함수를 사용하여 데이터 조회
    total_revenue = execute_query(query, params)

    # 결과를 JSON 형식으로 변환
    result = {
        "user_id": user_id,
        "total_revenue": total_revenue[0][0] if total_revenue else 0
    }

    return jsonify(result)

@app.route('/users', methods=['GET'])
def get_users():
    query = "SELECT user_id, username FROM users"
    raw_data = execute_query(query)

    # 응답을 JSON 형식으로 변환
    data = [
        {
            "user_id": row[0],
            "username": row[1],
        }
        for row in raw_data
    ]

    return jsonify(data)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)