/* global kakao */
import React, { useEffect } from 'react';
import styled from 'styled-components';

const KakaoMap = () => {
    const theme = {
        sizes: {
          mobile: 360,
          tablet: 768,
          desktop: 1024,
        },
        media: {
          mobile: (...args) => `@media (max-width: ${theme.sizes.mobile}px) {
            ${args}
          }`,
          tablet: (...args) => `@media (min-width: ${theme.sizes.mobile + 1}px) and (max-width: ${theme.sizes.tablet}px) {
            ${args}
          }`,
          desktop: (...args) => `@media (min-width: ${theme.sizes.tablet + 1}px) {
            ${args}
          }`,
        },
      };
    
    const Kakao = styled.div`
        height: 100%;
        max-height: 800px;
        max-width: 1200px;
        width: 60vw;
    `;

    useEffect(() => {
        const loadKakaoMap = () => {
            const script = document.createElement('script');
            script.async = true;
            script.src = "https://dapi.kakao.com/v2/maps/sdk.js?appkey=e8f1677269dd57608c41205f9e55842f&autoload=false";
            document.head.appendChild(script);

            script.onload = () => {
                kakao.maps.load(() => {
                    const container = document.getElementById('map');
                    const options = {
                        center: new kakao.maps.LatLng(35.1608594, 128.8675003),
                        level: 9,
                    };
                    const map = new kakao.maps.Map(container, options);

                    // 마커 생성
                    const markerPosition = new kakao.maps.LatLng(35.1608594, 128.8675003);
                    const marker = new kakao.maps.Marker({
                        position: markerPosition,
                    });

                    // 마커 지도에 표시
                    marker.setMap(map);

                    // 정보 창 생성 및 표시
                    const infowindow = new kakao.maps.InfoWindow({
                        content: '<div style="padding:5px;">회사위치</div>',
                    });
                    kakao.maps.event.addListener(marker, 'click', () => {
                        infowindow.open(map, marker);
                    });
                });
            };
        };

        loadKakaoMap();
    }, []);

    return <Kakao id="map"></Kakao>
};

export default KakaoMap;