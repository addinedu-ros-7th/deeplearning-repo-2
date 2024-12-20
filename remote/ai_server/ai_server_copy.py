from ultralytics import YOLO
from collections import defaultdict
import cv2
import socket
import time

# 모델 로드 (두 개의 .pt 파일)
model1 = YOLO('/home/zoo/venv/yolov8/Documents/my_data/data/traffic_light_best.pt')
model2 = YOLO('/home/zoo/venv/yolov8/Documents/my_data/data/traffic_sign.pt')

### 카메라

# 카메라 장치 인덱스 설정
device_index = 2  # 기본 카메라
cap = cv2.VideoCapture(device_index)

### 영상


# 임계값 및 NMS 설정
confidence_threshold = 0.4  # 신뢰도 임계값 설정
nms_iou_threshold = 0.35  # NMS에서 IOU 임계값 설정

# 프레임 건너뛰기 비율 설정 
frame_skip = 5
frame_counter = 0

# 객체 감지 횟수 임계값 설정
detection_threshold = 5  # 최소 탐지 횟수

# 객체 감지 횟수를 추적하는 딕셔너리
object_counts = defaultdict(int)

# 이전에 출력된 객체를 추적하기 위한 집합 (클래스 이름만 저장)
last_printed_objects = {"traffic_light": None, "traffic_sign": None}

# 서버 설정
HOST = '192.168.7.117'  # 모든 인터페이스에서 수신
PORT = 1236  # 포트 번호
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT)) 
server_socket.listen(1)
print(f"서버가 {PORT} 포트에서 대기 중입니다.")

client_socket, addr = server_socket.accept()
print(f"클라이언트 연결: {addr}")

first_sign_size = 0
first_sign_index = 0
first_light_size = 0
first_light_index = 0

def send_command(command):
    try:
        client_socket.sendall(command.encode('utf-8'))
    except Exception as e:
        print(f"명령 전송 중 오류: {e}")

while True:
    ret, frame = cap.read()
    if not ret:  # 카메라 입력이 없으면 종료
        print("카메라로부터 입력을 받을 수 없습니다.")
        break

    frame_counter += 1

    # 지정된 프레임 건너뛰기
    if frame_counter % frame_skip != 0:
        continue

    # 모델1과 모델2를 이용한 객체 탐지
    results1 = model1(frame, conf=confidence_threshold, iou=nms_iou_threshold, verbose=False)
    results2 = model2(frame, conf=confidence_threshold, iou=nms_iou_threshold, verbose=False)

    combined_frame = frame.copy()

    first_sign_size = 0
    first_sign_index = 0
    first_light_size = 0
    first_light_index = 0

    # 모델1의 결과 처리 (신호등)
    for result in results1[0].boxes:
        x1, y1, x2, y2 = map(int, result.xyxy[0])  # 바운딩 박스 좌표
        confidence = result.conf[0].item()  # 신뢰도
        class_id = int(result.cls[0].item())  # 클래스 ID
        class_name = results1[0].names[class_id]  # 클래스 이름

        temp = abs(x2 - x1) * abs(y2 - y1)
        if (first_light_size < temp):
            first_light_size = temp
            first_light_index = class_id

        # 객체 감지 횟수 증가
        object_counts[class_name] += 1

    # 신호등 클래스에서 값이 달라지면 출력 및 명령 전송
    if first_light_size != 0:
    # if last_printed_objects["traffic_light"] != class_name:
    #     if object_counts[class_name] >= detection_threshold:
        class_id = first_light_index
        class_name = results1[0].names[class_id]
        print(f"신호등: {class_name}, 감지 횟수: {object_counts[class_name]}")
        send_command(class_name)
        last_printed_objects["traffic_light"] = class_name  # 객체 출력 처리
        object_counts[class_name] = 0  # 감지 횟수 초기화

    # 바운딩 박스와 라벨 그리기
    label = f'{class_name} {confidence:.2f}'
    cv2.rectangle(combined_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(combined_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # 모델2의 결과 처리 (교통 표지판)
    for result in results2[0].boxes:
        x1, y1, x2, y2 = map(int, result.xyxy[0])  # 바운딩 박스 좌표
        confidence = result.conf[0].item()  # 신뢰도
        class_id = int(result.cls[0].item())  # 클래스 ID
        class_name = results2[0].names[class_id]  # 클래스 이름

        # 객체 감지 횟수 증가
        object_counts[class_name] += 1

        temp = abs(x2 - x1) * abs(y2 - y1)
        if (first_sign_size < temp):
            first_sign_size = temp
            first_sign_index = class_id

        # 교통 표지판 클래스에서 값이 달라지면 출력 및 명령 전송
        # if last_printed_objects["traffic_sign"] != class_name:
        #     if object_counts[class_name] >= detection_threshold:
    if first_sign_size != 0:
        class_id = first_sign_index
        class_name = results1[0].names[class_id]
        print(f"교통 표지판: {class_name}, 감지 횟수: {object_counts[class_name]}")
        send_command(class_name)
        last_printed_objects["traffic_sign"] = class_name  # 객체 출력 처리
        object_counts[class_name] = 0  # 감지 횟수 초기화

    # 바운딩 박스와 라벨 그리기
    label = f'{class_name} {confidence:.2f}'
    cv2.rectangle(combined_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
    cv2.putText(combined_frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    # 결과 출력
    cv2.imshow('Combined Object Detection', combined_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 리소스 해제 및 종료
cap.release()
cv2.destroyAllWindows()
client_socket.close()
server_socket.close()
