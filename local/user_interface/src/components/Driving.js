import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { io } from 'socket.io-client';
import styled from 'styled-components';
import KakaoMap from './KakaoMap'; // KakaoMap 컴포넌트 import

const Container = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh; /* 전체 높이를 100%로 설정 */
  width: 100%;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between; /* 버튼을 양쪽에 배치 */
  align-items: center; /* 수직 중앙 정렬 */
  padding: 20px;
  background-color: white; /* 배경 색상 설정 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%; /* 가로 100% */
`;

const RouteLabel = styled.div`
  text-align: center;
  font-size: 20px;
`;

const MapContainer = styled.div`
  flex: 1; /* 남은 공간을 모두 차지하도록 설정 */
  position: relative; /* 자식 요소의 절대 위치 설정을 위해 */
  width: 100%; /* 가로 100% */
`;

const Popup = styled.div`
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background-color: white;
  border: 1px solid #ccc;
  padding: 20px;
  z-index: 1000;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
`;

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
`;

const Button = styled.button`
  margin: 0 10px; /* 버튼 간격 설정 */
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer; /* 커서 모양 변경 */
`;

const Input = styled.input`
  width: 100%;
  padding: 10px;
  margin: 10px 0;
  box-sizing: border-box; /* 패딩 포함하여 전체 너비 계산 */
  color: ${props => (props.isDefault ? '#aaa' : '#000')}; /* 글자 색상 설정 */
`;

const Driving = () => {
  const dispatch = useDispatch();
  const [target, setTarget] = useState('');
  const [startLocation, setStartLocation] = useState('');
  const [startLat, setStartLat] = useState(null);
  const [startLon, setStartLon] = useState(null);
  const [targetLat, setTargetLat] = useState(null);
  const [targetLon, setTargetLon] = useState(null);
  const [route, setRoute] = useState([]); // 경로 상태 추가
  const [kakaoLoaded, setKakaoLoaded] = useState(false);
  const [isTargetChecked, setIsTargetChecked] = useState(false);
  const [activePopup, setActivePopup] = useState(null);
  const [socket, setSocket] = useState(null);
  const [newTarget, setNewTarget] = useState('목적지를 설정해주세요.');
  const [newStartLocation, setNewStartLocation] = useState('');
  const [targetCheckMessage, setTargetCheckMessage] = useState('');
  const [taxiInfo, setTaxiInfo] = useState(null);

  const [startCoords, setStartCoords] = useState(null); // 출발지 좌표
  const [targetCoords, setTargetCoords] = useState(null); // 목적지 좌표

  // Kakao Maps API 로드
  useEffect(() => {
    const loadKakaoMap = () => {
      const script = document.createElement('script');
      script.async = true;
      script.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey=e8f1677269dd57608c41205f9e55842f&autoload=false";

      script.onload = () => {
        setKakaoLoaded(true);
      };

      script.onerror = () => {
        console.error('Kakao Maps script failed to load.');
      };

      document.head.appendChild(script);
    };

    loadKakaoMap();
  }, []);

  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('서버에 연결되었습니다.');
      newSocket.emit('request_target');  // 서버에 목적지 요청
    });

    newSocket.on('target_checked', (data) => {
      console.log('목적지 확인:', data.target_checked);
      setIsTargetChecked(true);
      setTarget(data.target_checked);
      setTargetCheckMessage(`${data.target_checked}가 맞습니까?`);
      dispatch({ type: 'UPDATE_TARGET', payload: data.target_checked });
      getLatLongFromAddress(data.target_checked);
      setNewTarget(data.target_checked); // 입력 박스에 현재 목표 설정
      setActivePopup('target'); // 목적지 설정 팝업 열기
    });

    newSocket.on('target_updated', async (data) => {
      console.log('수신된 목적지:', data.target_updated);
      setTarget(data.target_updated);
      dispatch({ type: 'UPDATE_TARGET', payload: data.target_updated });
      await getLatLongFromAddress(data.target_updated);
      setNewTarget(data.target_updated); // 입력 박스에 현재 목표 설정
      setActivePopup(null); // 팝업 닫기
    });

    return () => {
      newSocket.disconnect();
    };
  }, [dispatch]);

  const getLatLongFromAddress = async (address) => {
    try {
      const response = await fetch('http://localhost:5000/get_lat_long', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ address }),
      });
      const data = await response.json();
      if (data.latitude && data.longitude) {
        return { latitude: data.latitude, longitude: data.longitude }; // 위도와 경도를 반환
      } else {
        console.error('위도와 경도를 가져오는 중 오류 발생:', data.error);
      }
    } catch (error) {
      console.error('API 호출 중 오류 발생:', error);
    }
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          const { latitude, longitude } = position.coords;
          const address = await getAddressFromLatLong(latitude, longitude);
          setStartLocation(address);
          setStartLat(latitude);
          setStartLon(longitude);
          setNewStartLocation(address); // 현재 위치를 기본값으로 설정
          console.log(`출발지 위도: ${latitude}, 경도: ${longitude}`);
          dispatch({ type: 'UPDATE_START_LOCATION', payload: address });
        },
        (error) => {
          console.error("위치 정보를 가져오는 중 오류 발생:", error);
        }
      );
    } else {
      console.error("이 브라우저에서는 위치 정보를 지원하지 않습니다.");
    }
  };

  const getAddressFromLatLong = async (latitude, longitude) => {
    try {
      const response = await fetch('http://localhost:5000/address', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ latitude, longitude }),
      });
      const data = await response.json();
      return data.address;
    } catch (error) {
      console.error('주소를 가져오는 중 오류 발생:', error);
      throw error;
    }
  };

  const handleUpdateStartLocation = () => {
    // 출발지 업데이트
    setStartLocation(newStartLocation); // 새로운 출발지 설정
    dispatch({ type: 'UPDATE_START_LOCATION', payload: newStartLocation });
  
    // 새로운 출발지의 위도와 경도를 가져옵니다.
    getLatLongFromAddress(newStartLocation).then((coords) => {
      if (coords) {
        setStartLat(coords.latitude); // 새로운 출발지 위도 설정
        setStartLon(coords.longitude); // 새로운 출발지 경도 설정
      } else {
        console.error("위도를 가져오는 중 오류 발생");
      }
    });
  };
  
  const handleUpdateTarget = () => {
    // 목적지 업데이트
    setTarget(newTarget); // 새로운 목적지 설정
    dispatch({ type: 'UPDATE_TARGET', payload: newTarget });
  
    // 새로운 목적지의 위도와 경도를 가져옵니다.
    getLatLongFromAddress(newTarget).then((coords) => {
      if (coords) {
        setTargetLat(coords.latitude); // 새로운 목적지 위도 설정
        setTargetLon(coords.longitude); // 새로운 목적지 경도 설정
      } else {
        console.error("위도를 가져오는 중 오류 발생");
      }
    });
  };
  
  const handleCallTaxi = () => {
    // 위도와 경도가 유효한지 확인
    if (startLat !== null && startLon !== null && targetLat !== null && targetLon !== null) {
      const startPoint = newStartLocation; // 출발지
      const endPoint = newTarget; // 목적지
      const userId = 1; // 게스트 사용자를 위한 ID (예: 1)
  
      const requestData = {
        userId,
        startPoint,
        endPoint
      };
  
      // 출발지와 목적지 업데이트
      dispatch({ type: 'UPDATE_START_LOCATION', payload: startPoint });
      dispatch({ type: 'UPDATE_TARGET', payload: endPoint });
  
      fetch('http://localhost:5000/call_taxi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      })
      .then(response => response.json())
      .then(data => {
        if (data.message) {
          setTaxiInfo(data); // 택시 정보를 상태로 설정
          console.log(data);
          setActivePopup('taxiInfo'); // 택시 정보 팝업 열기
  
          // 좌표 설정
          const newStartCoords = new window.kakao.maps.LatLng(startLat, startLon);
          const newTargetCoords = new window.kakao.maps.LatLng(targetLat, targetLon);
  
          setStartCoords(newStartCoords); // 출발지 좌표 설정
          setTargetCoords(newTargetCoords); // 목적지 좌표 설정
  
          // 경로 설정
          setRoute([
            { lat: startLat, lng: startLon }, // 출발지
            { lat: targetLat, lng: targetLon }  // 목적지
          ]);
        } else {
          console.error(data.error);
          alert('택시 호출 중 오류가 발생했습니다.');
        }
      })
      .catch(error => {
        console.error('API 호출 중 오류 발생:', error);
      });
    } else {
      console.error("출발지 또는 목적지의 위도와 경도를 확인하세요.");
    }
  };
  

  useEffect(() => {
    getCurrentLocation();
  }, []);

  useEffect(() => {
    if (isTargetChecked) {
      handleCallTaxi(); // 목적지가 확인되면 자동으로 경로 요청
    }
  }, [isTargetChecked]);

  const handleInputFocus = (setter) => {
    setter(''); // 입력 박스가 포커스될 때 기본값 지우기
  };

  return (
    <Container>
      <Header>
        <Button onClick={() => setActivePopup('target')}>목적지 설정</Button>
      </Header>
      <RouteLabel>
        {startLocation && target ? `${startLocation} -> ${target}` : ''}
      </RouteLabel>
      <MapContainer>
        {kakaoLoaded && startCoords && targetCoords && (
          // <KakaoMap 
          //   startCoords={startCoords} 
          //   targetCoords={targetCoords} 
          //   route={route} 
          // />
          <KakaoMap 
            startCoords={startCoords} 
            targetCoords={targetCoords} 
            route={route} 
            startLocation={startLocation} // 출발지 정보 추가
            target={target} // 목적지 정보 추가
          />
        )}
      </MapContainer>
  
      {activePopup === 'target' && (
        <>
          <Overlay onClick={() => setActivePopup(null)} />
          <Popup>
            <h2>목적지를 말해주세요.</h2>
            <p>{targetCheckMessage}</p>
            <div>
              <label htmlFor="startInput">출발지:</label>
              <Input 
                id="startInput"
                type="text" 
                value={newStartLocation} 
                onFocus={() => handleInputFocus(setNewStartLocation)} 
                onChange={(e) => {
                  setNewStartLocation(e.target.value);
                  console.log("입력된 출발지:", e.target.value);
                }} 
                placeholder="현재 위치" 
                isDefault={newStartLocation === ''} 
              />
            </div>
            <div>
              <label htmlFor="targetInput">목적지:</label>
              <Input 
                id="targetInput"
                type="text" 
                value={newTarget} 
                onFocus={() => handleInputFocus(setNewTarget)} 
                onChange={(e) => {
                  setNewTarget(e.target.value);
                  console.log("입력된 목적지:", e.target.value);
                }} 
                placeholder="목적지를 입력하세요" 
                isDefault={newTarget === '목적지를 설정해주세요.'} 
              />
            </div>
            <Button onClick={() => {
              handleUpdateStartLocation(); // 출발지 업데이트
              handleUpdateTarget(); // 목적지 업데이트
              handleCallTaxi(); // 택시 호출
            }}>호출하기</Button>
            <Button onClick={() => setActivePopup(null)}>취소</Button>
          </Popup>
        </>
      )}
  
      {/* 택시 배차 정보 팝업 */}
      {taxiInfo && activePopup === 'taxiInfo' && (
        <>
          <Overlay onClick={() => setActivePopup(null)} />
          <Popup>
            <h2>택시 배차 정보</h2>
            <p>택시 ID: {taxiInfo.taxiId}</p>
            <p>택시 종류: {taxiInfo.taxiType}</p>
            <p>택시 라이센스: {taxiInfo.taxiLicense}</p>
            <Button onClick={() => setActivePopup(null)}>닫기</Button>
          </Popup>
        </>
      )}
    </Container>
  );  

};

export default Driving;