import styled from 'styled-components';

export const Container = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh; /* 전체 높이를 100%로 설정 */
  width: 100%;
`;

export const Header = styled.div`
  display: flex;
  justify-content: space-between; /* 버튼을 양쪽에 배치 */
  align-items: center; /* 수직 중앙 정렬 */
  padding: 20px;
  background-color: white; /* 배경 색상 설정 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%; /* 가로 100% */
`;

export const RouteLabel = styled.div`
  text-align: center;
  font-size: 20px;
`;

export const MapContainer = styled.div`
  flex: 1; /* 남은 공간을 모두 차지하도록 설정 */
  position: relative; /* 자식 요소의 절대 위치 설정을 위해 */
  width: 100%; /* 가로 100% */
`;

export const Popup = styled.div`
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

export const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
`;

export const Button = styled.button`
  margin: 0 10px; /* 버튼 간격 설정 */
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer; /* 커서 모양 변경 */
`;

export const Input = styled.input`
  width: 100%;
  padding: 10px;
  margin: 10px 0;
  box-sizing: border-box; /* 패딩 포함하여 전체 너비 계산 */
  color: ${props => (props.isDefault ? '#aaa' : '#000')}; /* 글자 색상 설정 */
`;
