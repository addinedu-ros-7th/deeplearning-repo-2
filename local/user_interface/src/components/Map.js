import React, { useEffect, useState, useRef } from 'react';

const { kakao } = window;

const Map = ({ startCoords, targetCoords, startLocation, target }) => {
  const [map, setMap] = useState(null);
  const startMarkerRef = useRef(null);
  const endMarkerRef = useRef(null);
  const polylineRef = useRef(null);
  const startLabelRef = useRef(null);
  const targetLabelRef = useRef(null);
  
  console.log(startCoords, targetCoords, startLocation, target)

  // 하버사인 공식 구현
  const haversineDistance = (coords1, coords2) => {
    const R = 6371; // 지구 반지름 (킬로미터)
    const lat1 = coords1.getLat() * (Math.PI / 180);
    const lon1 = coords1.getLng() * (Math.PI / 180);
    const lat2 = coords2.getLat() * (Math.PI / 180);
    const lon2 = coords2.getLng() * (Math.PI / 180);

    const dLat = lat2 - lat1;
    const dLon = lon2 - lon1;

    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1) * Math.cos(lat2) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return R * c; // 거리 (킬로미터)
  };

  useEffect(() => {
    const mapContainer = document.getElementById('map');

    // 출발지와 목적지의 중심 좌표 계산
    const centerLat = (startCoords.getLat() + targetCoords.getLat()) / 2;
    const centerLng = (startCoords.getLng() + targetCoords.getLng()) / 2;

    // 거리 계산 (킬로미터 단위로)
    const distance = haversineDistance(startCoords, targetCoords);
    console.log(`Direct distance between start and target: ${distance.toFixed(2)} km`); // 거리 출력

    // 확대 수준 설정 (거리 기반)
    const level = distance > 5 ? 5 : (distance > 1 ? 6 : 7);

    const mapOptions = {
      center: new kakao.maps.LatLng(centerLat, centerLng), // 초기 맵의 중심 좌표
      level: level // 확대 수준
    };

    const kakaoMap = new kakao.maps.Map(mapContainer, mapOptions);
    setMap(kakaoMap);
  }, []);

  useEffect(() => {
    if (map) {
      // 출발지 마커 추가
      if (startCoords) {
        if (startMarkerRef.current) {
          startMarkerRef.current.setPosition(startCoords); // 기존 마커 위치 업데이트
        } else {
          startMarkerRef.current = new kakao.maps.Marker({ position: startCoords });
          startMarkerRef.current.setMap(map);

          // 인포윈도우 생성
          startLabelRef.current = new kakao.maps.InfoWindow({
            content: `<div style="padding:5px;">${startLocation || '출발지'}</div>`,
            position: new kakao.maps.LatLng(startCoords.getLat() + 0.0005, startCoords.getLng()),
            zIndex: 1,
          });

          startLabelRef.current.open(map, startMarkerRef.current); // 인포윈도우 표시
        }
      }

      // 목적지 마커 추가
      if (targetCoords) {
        if (endMarkerRef.current) {
          endMarkerRef.current.setPosition(targetCoords); // 기존 마커 위치 업데이트
        } else {
          endMarkerRef.current = new kakao.maps.Marker({ position: targetCoords });
          endMarkerRef.current.setMap(map);

          // 인포윈도우 생성
          targetLabelRef.current = new kakao.maps.InfoWindow({
            content: `<div style="padding:5px;">${target || '목적지'}</div>`,
            position: new kakao.maps.LatLng(targetCoords.getLat() + 0.0005, targetCoords.getLng()),
            zIndex: 1,
          });

          targetLabelRef.current.open(map, endMarkerRef.current); // 인포윈도우 표시
        }
      }

      // 인포윈도우 내용 업데이트
      if (startLabelRef.current) {
        startLabelRef.current.setContent(`<div style="padding:5px;">${startLocation || '출발지'}</div>`);
        startLabelRef.current.setPosition(new kakao.maps.LatLng(startCoords.getLat() + 0.0005, startCoords.getLng())); // 라벨 위치 업데이트
      }

      if (targetLabelRef.current) {
        targetLabelRef.current.setContent(`<div style="padding:5px;">${target || '목적지'}</div>`);
        targetLabelRef.current.setPosition(new kakao.maps.LatLng(targetCoords.getLat() + 0.0005, targetCoords.getLng())); // 라벨 위치 업데이트
      }

      // 경로 표시
      if (startCoords && targetCoords) {
        getCarDirection();
      }
    }
  }, [map, startCoords, targetCoords, startLocation, target]);

  const getCarDirection = async () => {
    const REST_API_KEY = '5fddd34337fb2ada12a19433030b102e'; // 여기에 본인의 API 키를 입력하세요
    const url = 'https://apis-navi.kakaomobility.com/v1/directions';

    const origin = `${startCoords.getLng()},${startCoords.getLat()}`;
    const destination = `${targetCoords.getLng()},${targetCoords.getLat()}`;

    const headers = {
      Authorization: `KakaoAK ${REST_API_KEY}`,
      'Content-Type': 'application/json'
    };

    const queryParams = new URLSearchParams({
      origin: origin,
      destination: destination
    });

    const requestUrl = `${url}?${queryParams}`;

    try {
      const response = await fetch(requestUrl, {
        method: 'GET',
        headers: headers
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      
      // 경로 길이 출력
      const routeDistance = data.routes[0].sections[0].distance; // 거리 (미터 단위)
      console.log(`Route distance by car: ${(routeDistance / 1000).toFixed(2)} km`); // 거리 출력

      const linePath = [];
      data.routes[0].sections[0].roads.forEach(router => {
        router.vertexes.forEach((vertex, index) => {
          if (index % 2 === 0) {
            linePath.push(new kakao.maps.LatLng(router.vertexes[index + 1], router.vertexes[index]));
          }
        });
      });

      // 기존 경로가 있으면 제거
      if (polylineRef.current) {
        polylineRef.current.setMap(null);
      }

      polylineRef.current = new kakao.maps.Polyline({
        path: linePath,
        strokeWeight: 5,
        strokeColor: '#000000',
        strokeOpacity: 0.7,
        strokeStyle: 'solid'
      });

      polylineRef.current.setMap(map);

    } catch (error) {
      console.error('Error:', error);
    }
  };

  return (
    <>
      <div id="map" style={{ width: "100%", height: "100%" }} />
    </>
  );
};

export default Map;