# deeplearning-repo-2
딥러닝 프로젝트 2조 저장소. RoadMind
---
> ### ***신호등 및 표지판 인식, 음성 인식 으로 안전하고 효율적인 자율주행의 기반을 구성하는 것***
<br/>

## 🤖 프로젝트 소개
<details markdown="1">
<summary><h3>자율주행 택시에 필요한 AI 시스템 RoadMind</h3></summary>
<li>자율주행 기술의 발전은 현대 교통 시스템에 혁신을 가져오고 있습니다.</li>
<li>RoadMind <b>신호등 및 표지판 인식, 음성 인식을 통해 안전하고 효율적인 자율주행의 기반을 구성</b>하고자 합니다.</li>
<li>이 프로젝트에서는 자율주행을 위한 교통 상황 인식과 장애물 인식 기능을 개발하여, 차량이 실시간으로 환경을 이해하고 안전하게 주행할 수 있도록 지원합니다.</li>
</details>
<br/>

## 🧠 구성원 및 역할
|이름|업무|
|:---|:---|
| 임주원 | 프로젝트 기획 및 총괄, Jira&Confluence 관리, 자율주행자동차 통신 및 제어, 주행 맵 설계 및 제작, 교통표지판 인식을 위한 데이터 수집 및 학습| 
| 김진재 | 발표자료 제작, 교통표지판 인식을 위한 데이터수집과 Labeling, UML(System&State Architecture)작성, 설계구체화 | 
| 임시온 | WEB Design, WEB Server와 Database 설계 및 제작과 연동, WEB에 음성인식 기능 이식, 다양한 지도 API로 성능개선| 
| 공도웅 | 음성인식 기능제작, 음성인식을 위한 자료수집과 프로그램제작, 신호등 인식을위한 데이터 수집과 학습| 
<br/>

<hr/>

### 프로젝트 선정 이유
| 대중성 : 매년 증가하는 무인 자동차의 이용자 |
|:---|
| ![image](https://github.com/user-attachments/assets/9109cd6c-04f1-4ae5-8139-00dbbbfe6bf4) |

| 안정성 : 고령화로 인해 늘어가는 고령 택시 운전자 |
|:---|
| ![image](https://github.com/user-attachments/assets/9c38cf3e-6bec-400a-b612-de1f1c5278ef) |

| 조용함 : 택시기사가 말을 거는게 거북하거나 통화를 엿듣는게 걱정되는 사람들 |
|:---|
| ![image](https://github.com/user-attachments/assets/a097c235-b466-472b-b5bb-d134c66a40bd) |
<hr/>
<br/>

## 🖥️ 활용 기술
|구분|상세|
|:---|:---|
|개발환경|<img src="https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white" /> <img src="https://img.shields.io/badge/Armbian-333399?style=for-the-badge&logo=armbian&logoColor=white" />|
|IDE| <img src="https://img.shields.io/badge/VSCode-0078D4?style=for-the-badge&logo=visual%20studio%20code&logoColor=white" /> <img src="https://img.shields.io/badge/Jupyter-F37626.svg?&style=for-the-badge&logo=Jupyter&logoColor=white" /> 
|언어| <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />   |
|시각화 및 데이터 수집|<img src="https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white" /> <img src="https://img.shields.io/badge/numpy-%23013243.svg?style=for-the-badge&logo=numpy&logoColor=white" /> <img src="https://img.shields.io/badge/Matplotlib-%23ffffff.svg?style=for-the-badge&logo=Matplotlib&logoColor=black" /> <img src="https://img.shields.io/badge/OPENAPI-%6BA539.svg?style=for-the-badge&logo=openapiinitiative&logoColor=black" /> <img src="https://img.shields.io/badge/roboflow-6706CE.svg?style=for-the-badge&logo=roboflow&logoColor=black" />|
|DB|<img src="https://img.shields.io/badge/Amazon_RDS-232F3E?style=for-the-badge&logo=amazon-aws&logoColor=white" /> <img src="https://img.shields.io/badge/MySQL-00000F?style=for-the-badge&logo=mysql&logoColor=white" />|
|웹 프레임워크|<img src="https://img.shields.io/badge/react-61DAFB?style=for-the-badge&logo=react&logoColor=white" /> <img src="https://img.shields.io/badge/flask-000000?style=for-the-badge&logo=flask&logoColor=white" />|
|API|<img src="https://img.shields.io/badge/kakaomapAPi-FFCD00?style=for-the-badge&logo=kakao&logoColor=white" />|
|라이브러리|<img src="https://img.shields.io/badge/NLTK-154F5B?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://img.shields.io/badge/KONLPY-CD0000?style=for-the-badge&logo=python&logoColor=white" /> <img src="https://github.com/user-attachments/assets/fa2adf0e-2553-4cd6-84c8-c43b93028551" alt="image" width="101.750" height="28" />|
|협업| <img src="https://img.shields.io/badge/Slack-4A154B?style=for-the-badge&logo=slack&logoColor=white" /> <img src="https://img.shields.io/badge/confluence-172B4D?style=for-the-badge&logo=confluence&logoColor=white" /> <img src="https://img.shields.io/badge/jira-0052CC?style=for-the-badge&logo=jira&logoColor=white" />|
<br />

## 기능 리스트
![image](https://github.com/user-attachments/assets/c1bfe84e-1218-44ff-b512-a979fbbb9d21)

## 시스템 구성도
![image](https://github.com/user-attachments/assets/41ed0cdb-08df-44dd-9816-acadf4e6cc83)

<hr/>

## UML
### State Diagram
![image](https://github.com/user-attachments/assets/faca4d08-c369-48e4-b226-da6abb2d14cb)
### Sequence Diagram
![Untitled Diagram-1733471061903 drawio](https://github.com/user-attachments/assets/8f2e5f93-9c82-4179-851a-fe442bf0f31f)
<hr/>

## Database
![image](https://github.com/user-attachments/assets/ee72ddc1-24e7-4e44-8250-2fcc45b54e19)

## GUI 설계
<br/>
<hr/>

# Demostraction
## 객체 인식
**• Daytime**

![road_video_1](https://github.com/user-attachments/assets/7f838eff-cd00-4cc2-a6a9-f4b7588a2bb1)

**• Night**

![src_test1_1_1_2_1](https://github.com/user-attachments/assets/6a0653f4-444f-452c-8642-23080e9f6526)




## 장애물 회피
**• 정적 장애물**

![1000005061_1](https://github.com/user-attachments/assets/1fd4c95e-7421-4dc7-aaba-76b9a7fe758a)

**• 동적 장애물**

![1000005073_1](https://github.com/user-attachments/assets/366feee2-a0d9-4d5b-b665-a30b77c15b5a)

## 음성 인식

## 동작 시나리오
**1. 택시 호출**

![final_1_1_1_1_1_1](https://github.com/user-attachments/assets/37d54e79-45dc-4d3f-9ba8-09395804ffa7)


**2. 택시 주행**

**• Inside of Car**

![final_2](https://github.com/user-attachments/assets/89ce6543-2b84-4864-a7d2-5d3b4610d48f)

**• Outside of Car**

![20241226_162147](https://github.com/user-attachments/assets/3aa1d6fd-171f-48c8-bcbb-800c3a23b502)


**3. 택시 하차**

![final_1_2_1_1_1](https://github.com/user-attachments/assets/7e3f34c8-8f28-4007-8f25-57007a15fe21)

