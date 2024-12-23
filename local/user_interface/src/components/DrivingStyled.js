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
  background-color: #f8f9fa; /* 배경 색상 설정 */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  width: 100%; /* 가로 100% */
`;

export const RouteLabel = styled.div`
  text-align: center;
  font-size: 20px;
  margin: 10px 0;
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
  border: none; /* 기본 테두리 제거 */
  border-radius: 5px; /* 모서리 둥글게 */
  transition: background-color 0.3s; /* 배경 색상 변경 애니메이션 */

  &:hover {
    background-color: #0056b3; /* 호버 시 배경 색상 변경 */
    color: white; /* 글자 색상 변경 */
  }

  &.red {
    background-color: red; /* 빨간색 배경 */
    color: white; /* 글자 색상 흰색 */
  }
`;

export const Input = styled.input`
  width: 100%;
  padding: 10px;
  margin: 10px 0;
  box-sizing: border-box; /* 패딩 포함하여 전체 너비 계산 */
  border: 1px solid #ccc; /* 테두리 색상 */
  border-radius: 5px; /* 모서리 둥글게 */
  color: ${props => (props.isDefault ? '#aaa' : '#000')}; /* 글자 색상 설정 */
  transition: border-color 0.3s; /* 테두리 색상 변경 애니메이션 */

  &:focus {
    border-color: #007bff; /* 포커스 시 테두리 색상 변경 */
    outline: none; /* 기본 아웃라인 제거 */
  }
`;

export const TaxiPopup = styled.div`
  position: fixed;
  bottom: 20px;  // 화면 하단에서 20px
  right: 20px;   // 화면 오른쪽에서 20px
  background-color: white;
  border: 1px solid #ccc;
  padding: 20px;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  z-index: 1000; // 다른 요소 위에 표시
  width: 300px; // 팝업 너비 설정
  border-radius: 10px; // 모서리 둥글게
`;
