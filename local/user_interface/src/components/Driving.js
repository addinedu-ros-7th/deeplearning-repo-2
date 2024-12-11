import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { io } from 'socket.io-client';
import styled from 'styled-components';

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

const Driving = () => {
  const [target, setTarget] = useState('');
  const [socket, setSocket] = useState(null);

  // Redux 상태 가져오기
  const { startDate, endDate, searchValue } = useSelector(state => state);

  useEffect(() => {
    // WebSocket 연결
    const newSocket = io('http://localhost:5000');
    setSocket(newSocket);

    // 서버에서 target 업데이트 수신
    newSocket.on('target_updated', (data) => {
      console.log('수신된 목적지:', data.target); // 수신된 데이터 출력
      setTarget(data.target);
    });

    // 컴포넌트 언마운트 시 소켓 연결 해제
    return () => {
      newSocket.disconnect();
    };
  }, []);

  return (
    <Container>
      <h1>Driving Component</h1>
      <TargetDisplay>
        {target ? `목적지: ${target}` : '목적지를 설정하세요.'}
      </TargetDisplay>
    </Container>
  );
};

export default Driving;
