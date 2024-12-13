import React from 'react';
import styled from 'styled-components';

const VideoContainer = styled.div`
    width: auto; // 너비를 자동으로 설정
    height: 100%; // 높이를 100% 차지
    display: flex;
    justify-content: center; // 수평 중앙 정렬
    align-items: center; // 수직 중앙 정렬
`;

const LiveVideo = () => {
    return (
        <VideoContainer>
            <img 
                src="http://192.168.0.31:5000/video_feed"
                alt="Live Feed" 
                style={{ width: 'auto', height: '100%' }} // 너비는 자동, 높이는 100%
            />
        </VideoContainer>
    );
};

export default LiveVideo;

// src="http://192.168.0.219:5000/video_feed" 