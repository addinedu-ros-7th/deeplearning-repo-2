/* global kakao */
import React, { useEffect, useRef } from 'react';
import styled from 'styled-components';

const Kakao = styled.div`
  height: 100%;
  width: 100%;
`;

const KakaoMap = ({ startCoords, targetCoords }) => {
  const mapRef = useRef(null);
  const markersRef = useRef([]); // 마커를 저장할 배열

  useEffect(() => {
    const loadKakaoMap = () => {
      const script = document.createElement('script');
      script.async = true;
      script.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey=e8f1677269dd57608c41205f9e55842f&autoload=false";

      script.onload = () => {
        kakao.maps.load(() => {
          const container = document.getElementById('map');
          const options = {
            center: new kakao.maps.LatLng(37.5665, 126.978),
            level: 4,
          };

          const map = new kakao.maps.Map(container, options); // 지도 생성
          mapRef.current = map; // mapRef에 지도 저장

          // 마커 삭제 및 추가
          removeMarkers();

          // 출발지 좌표로 마커 생성
          if (startCoords) {
            const startMarker = new kakao.maps.Marker({
              map: map,
              position: startCoords,
            });
            const startInfowindow = new kakao.maps.InfoWindow({
              content: `<div style="width:150px;text-align:center;padding:6px 0;">출발지</div>`,
            });
            startInfowindow.open(map, startMarker);
            markersRef.current.push(startMarker); // 마커 저장
            map.setCenter(startCoords); // 출발지로 지도 중심 이동
          }

          // 목적지 좌표로 마커 생성
          if (targetCoords) {
            const targetMarker = new kakao.maps.Marker({
              map: map,
              position: targetCoords,
            });
            const targetInfowindow = new kakao.maps.InfoWindow({
              content: `<div style="width:150px;text-align:center;padding:6px 0;">목적지</div>`,
            });
            targetInfowindow.open(map, targetMarker);
            markersRef.current.push(targetMarker); // 마커 저장
          }
        });
      };

      script.onerror = () => {
        console.error('Kakao Maps script failed to load.');
      };

      document.head.appendChild(script);
    };

    loadKakaoMap(); // Kakao Map 로드 함수 호출
  }, [startCoords, targetCoords]);

  const removeMarkers = () => {
    markersRef.current.forEach(marker => {
      marker.setMap(null); // 마커를 지도에서 제거
    });
    markersRef.current = []; // 마커 배열 초기화
  };

  return (
    <Kakao id="map"></Kakao>
  );
};

export default KakaoMap;