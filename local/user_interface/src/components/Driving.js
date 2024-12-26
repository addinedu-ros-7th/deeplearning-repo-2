import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { io } from 'socket.io-client';
import styled from 'styled-components';
import KakaoMap from './KakaoMap'; // KakaoMap 컴포넌트 import
import { 
  Container, 
  Header, 
  RouteLabel, 
  MapContainer, 
  Popup, 
  Overlay, 
  Button, 
  Input,
  TaxiPopup
} from './DrivingStyled'; 
import Map from './Map';

// 1 호출하기 눌러야 맵 뜨는 것
// 3. 하차하기

const Driving = () => {
  const dispatch = useDispatch();
  const [target, setTarget] = useState('');
  const [startLon, setStartLon] = useState(null);
  const [startLat, setStartLat] = useState(null);
  const [targetLat, setTargetLat] = useState(null);
  const [targetLon, setTargetLon] = useState(null);
  const [route, setRoute] = useState([]); // 경로 상태 추가
  const [kakaoLoaded, setKakaoLoaded] = useState(false);
  const [isTargetChecked, setIsTargetChecked] = useState(false);
  const [activePopup, setActivePopup] = useState(null);
  const [socket, setSocket] = useState(null);
  const [newTarget, setNewTarget] = useState('목적지를 설정해주세요.');
  const [startLocation, setStartLocation] = useState('');
  const [newStartLocation, setNewStartLocation] = useState('');
  const [targetCheckMessage, setTargetCheckMessage] = useState('');
  const [taxiInfo, setTaxiInfo] = useState(null);
  const [startCoords, setStartCoords] = useState(null); // 출발지 좌표
  const [targetCoords, setTargetCoords] = useState(null); // 목적지 좌표
  const [updateReady, setUpdateReady] = useState(false);

  // kakao map api load
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

  // socketio connecting
  useEffect(() => {
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    // basic connect
    newSocket.on('connect', () => {
      console.log('서버에 연결되었습니다.');
      newSocket.emit('request_target');  // 서버에 목적지 요청
    });

    // target checked receive
    newSocket.on('target_checked', (data) => {
      console.log('목적지 확인:', data.target_checked);
      setIsTargetChecked(true);
      setTarget(data.target_checked);
      setTargetCheckMessage(`${data.target_checked}가 맞습니까?`);
      dispatch({ type: 'UPDATE_TARGET', payload: data.target_checked });
      setNewTarget(data.target_checked); // 입력 박스에 현재 목표 설정
      setActivePopup('target'); // 목적지 설정 팝업 열기
    });

    newSocket.on('target_updated', async (data) => {
      console.log('수신된 목적지:', data.target_updated);
      setTarget(data.target_updated);
      dispatch({ type: 'UPDATE_TARGET', payload: data.target_updated });
      const coords = await getLatLongFromAddress(data.target_updated);
      if (coords) {
        setTargetLat(coords.latitude);
        setTargetLon(coords.longitude);
        console.log("좌표 업데이트 완료:", coords);
        // 좌표가 모두 업데이트된 후 호출
        handleCallTaxi();
      } else {
        console.error("좌표를 가져오는 데 실패했습니다.");
      }
    });


    return () => {
      newSocket.disconnect();
    };
  }, [dispatch]);

  const getLatLongFromAddress = async (address) => {
    try {
      // 1단계: 주소 검색 시도
      let response = await fetch(
        `https://dapi.kakao.com/v2/local/search/address.json?query=${encodeURIComponent(address)}`,
        {
          headers: {
            Authorization: `KakaoAK fa9b778e6585289e190dc4ca50d395ed`,
          },
        }
      );
  
      let data = await response.json();
  
      // 주소 검색 결과가 있으면 반환
      if (data.documents && data.documents.length > 0) {
        const { x, y } = data.documents[0]; // 경도(x), 위도(y)
        return { latitude: parseFloat(y), longitude: parseFloat(x) };
      }
  
      // 2단계: 키워드 검색 시도 (주소 검색 실패 시)
      response = await fetch(
        `https://dapi.kakao.com/v2/local/search/keyword.json?query=${encodeURIComponent(address)}`,
        {
          headers: {
            Authorization: `KakaoAK fa9b778e6585289e190dc4ca50d395ed`,
          },
        }
      );
  
      data = await response.json();
  
      if (data.documents && data.documents.length > 0) {
        const { x, y } = data.documents[0];
        return { latitude: parseFloat(y), longitude: parseFloat(x) };
      }
  
      // 검색 결과가 모두 없을 경우
      console.error("검색 결과가 없습니다:", data);
      alert("주소를 찾을 수 없습니다. 정확한 장소명을 입력해주세요.");
    } catch (error) {
      console.error("API 호출 중 오류 발생:", error);
      alert("위치 정보를 가져오는 데 문제가 발생했습니다. 다시 시도해주세요.");
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

  useEffect(() => {
    if ( updateReady && startLat !== null && startLon !== null && targetLat !== null && targetLon !== null) {
      handleCallTaxi();
    }
  }, [updateReady, startLat, startLon, targetLat, targetLon]);
  
  const handleCallTaxi = () => {
    // 위도와 경도가 유효한지 확인
    console.log(startLat, startLon, targetLat, targetLon );
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
  
  const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

  const handleUpdateStartLocation = async () => {
    // 새로운 출발지의 위도와 경도를 가져옵니다.
    const coords = await getLatLongFromAddress(newStartLocation);
    if (coords) {
      setStartLat(coords.latitude);
      setStartLon(coords.longitude);
      setStartCoords(new window.kakao.maps.LatLng(coords.latitude, coords.longitude)); // 출발지 좌표 설정
    }
  };

  const handleUpdateTarget = async () => {
    // 새로운 목적지의 위도와 경도를 가져옵니다.
    const coords = await getLatLongFromAddress(newTarget);
    if (coords) {
      setTargetLat(coords.latitude);
      setTargetLon(coords.longitude);
      setTargetCoords(new window.kakao.maps.LatLng(coords.latitude, coords.longitude)); // 목적지 좌표 설정
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

  const handleCallButton = async () => {
    try {
      await handleUpdateStartLocation();
      await handleUpdateTarget();
      setTarget(newTarget);
      setUpdateReady(true);
    } catch (error) {
      console.log('hondleCallButton error :',error);
    }
  }

  const handleDropTaxi = async (taxiId) => {
    try {
      const response = await fetch('http://localhost:5000/drop_taxi', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ taxiId }),
      });
  
      if (response.ok) {
        const data = await response.json();
        alert(data.message); // 하차 완료 메시지 표시
        setTaxiInfo(null); // 택시 정보 초기화
      } else {
        const errorData = await response.json();
        alert(errorData.error || '하차 중 오류가 발생했습니다.');
      }
    } catch (error) {
      console.error('API 호출 중 오류 발생:', error);
      alert('하차 요청 중 오류가 발생했습니다.');
    }
  };
  

  return (
    <Container>
      <Header>
        <h2>출발지: {startLocation} | 목적지: {target}</h2>
        <Button onClick={() => setActivePopup('target')}>목적지 설정</Button>
      </Header>
      {/* <RouteLabel>
        {startLocation && target ? `${startLocation} -> ${target}` : ''}
      </RouteLabel> */}
      <MapContainer>
        {kakaoLoaded && startCoords && targetCoords && (
          // <KakaoMap 
          //   startCoords={startCoords} 
          //   targetCoords={targetCoords} 
          //   route={route} 
          //   startLocation={startLocation} // 출발지 정보 추가
          //   target={target} // 목적지 정보 추가
          // />
          <Map
            startCoords={startCoords}
            targetCoords={targetCoords}
            startLocation={startLocation}
            target={target} 
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
                placeholder={setNewStartLocation}
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
            <Button onClick={handleCallButton}>호출하기</Button>
            <Button onClick={() => setActivePopup(null)}>취소</Button>
          </Popup>
        </>
      )}
  
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

      {taxiInfo && (
        <TaxiPopup>
          <h2>택시 배차 정보</h2>
          <p>택시 ID: {taxiInfo.taxiId}</p>
          <p>택시 종류: {taxiInfo.taxiType}</p>
          <p>택시 라이센스: {taxiInfo.taxiLicense}</p>
          <Button 
            style={{ backgroundColor: 'red', color: 'white' }} 
            onClick={() => handleDropTaxi(taxiInfo.taxiId)}>하차하기</Button>
        </TaxiPopup>
      )}
    </Container>
  );  
};

export default Driving;