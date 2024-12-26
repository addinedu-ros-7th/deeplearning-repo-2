import React, { useEffect } from 'react';

const KakaoMap = ({ startCoords, targetCoords, startLocation, target }) => {
  useEffect(() => {
    const container = document.getElementById('map'); // 맵을 표시할 DOM 요소
    const options = {
      center: startCoords, // 초기 맵의 중심 좌표
      level: 3, // 확대 수준
    };

    const map = new window.kakao.maps.Map(container, options); // 맵 생성

    // 출발지 마커 추가
    const startMarker = new window.kakao.maps.Marker({
      position: startCoords,
    });
    startMarker.setMap(map); // 맵에 마커 추가

    // 출발지 이름 표시
    const startLabel = new window.kakao.maps.InfoWindow({
      content: `<div style="padding:5px; background-color: white; border: 1px solid #ccc;">${startLocation}</div>`, // 마커에 표시할 내용
      position: new window.kakao.maps.LatLng(startCoords.getLat() + 0.0005, startCoords.getLng()), // 마커 위로 약간 이동
      zIndex: 1, // 마커 위에 표시되도록 설정
    });

    // 출발지 마커 클릭 이벤트
    window.kakao.maps.event.addListener(startMarker, 'click', () => {
      if (startLabel.getMap()) {
        startLabel.setMap(null); // 이미 표시된 경우 숨김
      } else {
        startLabel.setMap(map); // 표시되지 않은 경우 맵에 추가
      }
    });

    // 목적지 마커 추가
    const targetMarker = new window.kakao.maps.Marker({
      position: targetCoords,
    });
    targetMarker.setMap(map); // 맵에 마커 추가

    // 목적지 이름 표시
    const targetLabel = new window.kakao.maps.InfoWindow({
      content: `<div style="padding:5px; background-color: white; border: 1px solid #ccc;">${target}</div>`, // 마커에 표시할 내용
      position: new window.kakao.maps.LatLng(targetCoords.getLat() + 0.0005, targetCoords.getLng()), // 마커 위로 약간 이동
      zIndex: 1, // 마커 위에 표시되도록 설정
    });

    // 목적지 마커 클릭 이벤트
    window.kakao.maps.event.addListener(targetMarker, 'click', () => {
      if (targetLabel.getMap()) {
        targetLabel.setMap(null); // 이미 표시된 경우 숨김
      } else {
        targetLabel.setMap(map); // 표시되지 않은 경우 맵에 추가
      }
    });

    // 경로 표시
    const path = [startCoords, targetCoords]; // 출발지와 목적지 좌표를 경로로 설정
    const polyline = new window.kakao.maps.Polyline({
      path: path,
      strokeWeight: 5,
      strokeColor: '#FF0000',
      strokeOpacity: 0.7,
      strokeStyle: 'solid',
    });
    polyline.setMap(map); // 맵에 경로 추가

  }, [startCoords, targetCoords, startLocation, target]); // 의존성 배열

  return <div id="map" style={{ width: '100%', height: '100%' }}></div>; // 맵을 표시할 div
};

export default KakaoMap;