import React, { useEffect, useState } from 'react';
import { useDispatch } from 'react-redux';
import { io } from 'socket.io-client';
import styled from 'styled-components';
import KakaoMap from './KakaoMap'; // KakaoMap 컴포넌트 import

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
`;

const TargetDisplay = styled.div`
  margin: 20px;
  font-size: 24px;
`;

const LocationDisplay = styled.div`
  margin: 20px;
  font-size: 20px;
`;

const Button = styled.button`
  margin: 10px;
  padding: 10px 20px;
  font-size: 16px;
`;

const Driving = () => {
  const dispatch = useDispatch();
  const [target, setTarget] = useState('');
  const [startLocation, setStartLocation] = useState('');
  const [startLat, setStartLat] = useState(null);
  const [startLon, setStartLon] = useState(null);
  const [socket, setSocket] = useState(null);
  const [targetLat, setTargetLat] = useState(null);
  const [targetLon, setTargetLon] = useState(null);
  const [route, setRoute] = useState([]);
  const [kakaoLoaded, setKakaoLoaded] = useState(false);
  const [isTargetChecked, setIsTargetChecked] = useState(false); // 목적지 확인 상태 추가

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

    // 목적지 확인 이벤트 수신
    newSocket.on('target_checked', (data) => {
      console.log('목적지 확인:', data.target_checked);
      setIsTargetChecked(true);
      setTarget(data.target_checked);
      dispatch({ type: 'UPDATE_TARGET', payload: data.target_checked });
      getLatLongFromAddress(data.target_checked);
    });

    // 최종 목적지 업데이트 이벤트 수신
    newSocket.on('target_updated', async (data) => {
      console.log('수신된 목적지:', data.target_updated);
      setTarget(data.target_updated);
      dispatch({ type: 'UPDATE_TARGET', payload: data.target_updated });
      await getLatLongFromAddress(data.target_updated);
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
        setTargetLat(data.latitude);
        setTargetLon(data.longitude);
        console.log(`목적지 위도: ${data.latitude}, 경도: ${data.longitude}`);
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

  const handleCallTaxi = () => {
    if (startLat && startLon && targetLat && targetLon) {
      const start = new window.kakao.maps.LatLng(startLat, startLon);
      const end = new window.kakao.maps.LatLng(targetLat, targetLon);
      const directionsService = new window.kakao.maps.services.Directions();

      directionsService.route({
        origin: start,
        destination: end,
        callback: function (result, status) {
          if (status === window.kakao.maps.services.Status.OK) {
            const routePath = result.routes[0].path;
            setRoute(routePath);
          } else {
            console.error('경로를 가져오는 중 오류 발생:', status);
          }
        },
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

  return (
    <Container>
      <h1>Driving Component</h1>
      <TargetDisplay>
        {target ? `목적지: ${target}` : '목적지를 설정하세요.'}
      </TargetDisplay>
      <LocationDisplay>
        {startLocation ? `현재 위치: ${startLocation}` : '현재 위치를 가져오는 중입니다...'}
      </LocationDisplay>
      <Button onClick={handleCallTaxi}>호출하기</Button>
      <KakaoMap 
        startCoords={new window.kakao.maps.LatLng(startLat, startLon)} 
        targetCoords={new window.kakao.maps.LatLng(targetLat, targetLon)} 
        route={route} 
      />
    </Container>
  );
};

export default Driving;
