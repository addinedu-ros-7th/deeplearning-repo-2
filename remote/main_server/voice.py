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
# import torch
from socketio import Client
import time
# sio = Client()

# # 서버 연결
# sio.connect('http://localhost:5000') 

# SocketIO 클라이언트 초기화
sio = Client()
# 서버 연결
try:
    sio.connect('http://localhost:5000')
    print("서버에 성공적으로 연결되었습니다.")
except Exception as e:
    print(f"서버 연결 실패: {e}")

# 목표값을 서버에 전송
def send_target_update(target):
    print(f"서버에 목표 전송: {target}")
    sio.emit('target_updated', {'target_updated': target})  # 서버에 목표값 전송

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
        # 6단계: 불필요한 단어 제거 (텍스트 끝에 남은 '으로', '로' 처리
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
        # 4단계: 위치 관련 표현 정리 띄어쓰기와 불필요한 단어 제거)
        combined_text = re.sub(r"(앞|뒤|여기|저기|지금|바로|횡단보도|카페|길|사거리|코너)", r" \1", combined_text)
        result = combined_text.replace(" ", "").strip()
        return result if result else None
    except Exception as e:
        return f"하차 주어 추출 중 오류: {e}"

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
        # 호출이 안된 상태에서 의미없는 단어가 왔을때 
        if (is_robot_called == False) and ((predicted_label == 3 and confidence >= threshold ) or (confidence < threshold or confidence_gap < gap_threshold)):
            not_understand()
        # 로보 호출이 활성화된 상태에서만 나머지 판단
        if is_robot_called:
            if predicted_label == 1 and confidence >= threshold:
                subject = extract_subject_des(text)
                target = subject
                # check_des()
                # print("목적지가 맞나 확인합니다.")
                        # 피드백 질문 생성
                feedback_question = f"{target} 목적지가 맞습니까?"
                # 음성 파일 생성 (TTS 활용)
                create_feedback_wav(feedback_question)
                 # 질문 출력 및 재생
                print("목적지가 맞나 확인합니다.")
                play_feedback_wav()
                return f"'{text}' -> 예측: {LABEL_DICT.get(predicted_label, '알 수 없음')} (신뢰도: {confidence:.2f}), {label_scores}, 추출된 주어: {subject}"
            
            elif predicted_label == 4 and confidence >= threshold:
                print("목적지를 새로 입력하세요")
                retake_des()
            elif predicted_label == 5 and confidence >= threshold:
                print("목적지가 확정 되었습니다")
                go_des()
                send_target_update(target)
                is_robot_called = False # 확정되면 상태 초기화 
            elif predicted_label == 2 and confidence >= threshold:
                subject2 = extract_subject_hacha(text)
                target = subject2
                is_robot_called = False # 하차한다고하면 상태 초기화
            # 즉 별로 쓸모없는 문장 or 이상하게 인식되었다.
            elif (predicted_label == 3 and confidence >= threshold ) or (confidence < threshold or confidence_gap < gap_threshold):
                not_understand()
                is_robot_called = True  # 여전히 호출은 되어있는 상태
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
            
            
# 실행
if __name__ == "__main__":
    while True:
        voice_to_intent()