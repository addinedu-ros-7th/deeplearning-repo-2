import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
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
  const [route, setRoute] = useState([]); // 경로를 저장할 상태 추가
  const [kakaoLoaded, setKakaoLoaded] = useState(false);

  useEffect(() => {
    const loadKakaoMap = () => {
      const script = document.createElement('script');
      script.async = true;
      script.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey=e8f1677269dd57608c41205f9e55842f&autoload=false";

      script.onload = () => {
        setKakaoLoaded(true); // 로드 완료 시 상태 업데이트
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

    newSocket.on('target_updated', async (data) => {
      console.log('수신된 목적지:', data.target);
      setTarget(data.target);
      dispatch({ type: 'UPDATE_TARGET', payload: data.target });
      await getLatLongFromAddress(data.target);
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
          setStartLocation(await getAddressFromLatLong(latitude, longitude));
          setStartLat(latitude);
          setStartLon(longitude);
          console.log(`출발지 위도: ${latitude}, 경도: ${longitude}`);
          dispatch({ type: 'UPDATE_START_LOCATION', payload: startLocation });
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
      // Kakao Maps의 경로 요청
      const start = new window.kakao.maps.LatLng(startLat, startLon);
      const end = new window.kakao.maps.LatLng(targetLat, targetLon);
      const directionsService = new window.kakao.maps.services.Directions();

      directionsService.route({
        origin: start,
        destination: end,
        callback: function (result, status) {
          if (status === window.kakao.maps.services.Status.OK) {
            const routePath = result.routes[0].path; // 첫 번째 경로의 좌표
            setRoute(routePath); // 경로를 상태에 저장
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
        route={route} // 경로를 KakaoMap에 전달
      />
    </Container>
  );
};

export default Driving;
// const handleCallTaxi = () => {
//   if (window.kakao.maps.services) {
//     // console.error("Kakao Maps가 로드되지 않았습니다.");
//     // return;


//   if (startLat && startLon && targetLat && targetLon) {
//     const start = new window.kakao.maps.LatLng(startLat, startLon);
//     const end = new window.kakao.maps.LatLng(targetLat, targetLon);
    
//     const directionsService = new window.kakao.maps.services.Directions();
//     directionsService.route({
//       origin: start,
//       destination: end,
//       callback: function (result, status) {
//         if (status === window.kakao.maps.services.Status.OK) {
//           const routePath = result.routes[0].path; // 첫 번째 경로의 좌표
//           console.log("경로 데이터:", routePath); // 경로 데이터 확인
//           setRoute(routePath); // 경로를 상태에 저장
//         } else {
//           console.error('경로를 가져오는 중 오류 발생:', status);
//         }
//       },
//     });
//   } else {
//     console.error("출발지 또는 목적지의 위도와 경도를 확인하세요.");
//   }
//   }

// };

// useEffect(() => {
//   getCurrentLocation();
// }, []);

// return (
//   <Container>
//     <h1>Driving Component</h1>
//     <TargetDisplay>
//       {target ? `목적지: ${target}` : '목적지를 설정하세요.'}
//     </TargetDisplay>
//     <LocationDisplay>
//       {startLocation ? `현재 위치: ${startLocation}` : '현재 위치를 가져오는 중입니다...'}
//     </LocationDisplay>
//     <Button onClick={handleCallTaxi}>호출하기</Button>
//     <KakaoMap 
//       startCoords={new window.kakao.maps.LatLng(startLat, startLon)} 
//       targetCoords={new window.kakao.maps.LatLng(targetLat, targetLon)} 
//       route={route} // 경로를 KakaoMap에 전달
//     />
//   </Container>
// );
// };

// export default Driving;