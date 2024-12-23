// import React, { useState } from 'react';
// import styled from 'styled-components';
// import LiveVideo from './components/LiveVideo';
// import { BrowserRouter, Routes, Route } from 'react-router-dom';
// import SearchHeader from './components/SerachHeader'; // 경로 수정
// import { Provider } from 'react-redux';
// import store from './store'; // Redux 스토어 가져오기
// import TaxiList from './components/TaxiList';
// import PieChart from './components/PieChart';
// import UserMoney from './components/UserMoney';
// import Driving from './components/Driving';
// import KakaoMap from './components/KakaoMap';
// import Map from './components/Map';

// const Container = styled.div`
//     display: flex;
//     flex-direction: column;
//     height: 100vh;
// `;

// const TopSection = styled.div`
//     flex: 0 0 15%; // 세로 20% 차지
//     display: flex;
//     align-items: center;
//     justify-content: center;
//     padding: 0 5%; // 좌우 패딩 5%
// `;

// const BottomSection = styled.div`
//     flex: 1; // 나머지 80% 차지
//     background-color: #ffffff; // 배경색
//     padding: 20px; // 내부 패딩
//     display: flex;
//     align-items: center;
//     justify-content: center;
//     padding: 0 5%; // 좌우 패딩 5%
// `;

// const App = () => {
//   const [searchCriteria, setSearchCriteria] = useState({ startDate: null, endDate: null, searchValue: '' });
//   const [taxis, setTaxis] = useState([]); // 변수명 변경

//   const handleSearch = (criteria) => {
//       console.log('Search Criteria:', criteria);
//       setSearchCriteria(criteria);
//       fetchUsers(criteria); // 이 함수 이름은 유지
//   };

//   const fetchUsers = async (criteria) => {
//       try {
//           const response = await fetch('http://localhost:5000/select_data', {
//               method: 'POST',
//               headers: {
//                   'Content-Type': 'application/json',
//               },
//               body: JSON.stringify(criteria),
//           });
//           const data = await response.json();
//           console.log('Fetched Taxis:', data); // 변수명 변경
//           setTaxis(data); // 변수명 변경
//       } catch (error) {
//           console.error('Error fetching taxis:', error); // 변수명 변경
//       }
//   };

//   return (
//       <Provider store={store}>
//           <BrowserRouter>
//               <Container>
//                 <Routes>
//                     <Route path='manager/taxi/list' element={
//                     <TopSection>
//                         <SearchHeader onSearch={handleSearch} />
//                     </TopSection>}
//                     />
//                 </Routes>
//                   <BottomSection>
//                       <Routes>
//                           <Route path='manager/taxi/list' element={<TaxiList taxis={taxis} />} />
//                           <Route path='manager/taxi/chart' element={<PieChart />} />
//                           <Route path='user/video' element={<LiveVideo />} />
//                           <Route path='user/driving' element={<Driving />} />
//                           <Route path='user/money/chart' element={<UserMoney />} />
//                       </Routes>
//                   </BottomSection>
//               </Container>
//           </BrowserRouter>
//       </Provider>
//   );
// };

// export default App;
import React, { useState } from 'react';
import styled from 'styled-components';
import LiveVideo from './components/LiveVideo';
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import SearchHeader from './components/SerachHeader'; // 경로 수정
import { Provider } from 'react-redux';
import store from './store'; // Redux 스토어 가져오기
import TaxiList from './components/TaxiList';
import PieChart from './components/PieChart';
import UserMoney from './components/UserMoney';
import Driving from './components/Driving';

const Container = styled.div`
    display: flex;
    flex-direction: column;
    height: 100vh;
`;

const Header = styled.header`
    display: flex;
    justify-content: center;
    background-color: #007bff;
    padding: 10px;
`;

const Button = styled(Link)`
    background-color: #ffffff;
    color: #007bff;
    border: none;
    padding: 10px 20px;
    margin: 0 10px;
    text-decoration: none;
    border-radius: 4px;
    transition: background-color 0.3s;

    &:hover {
        background-color: #e7e7e7;
    }
`;

const TopSection = styled.div`
    flex: 0 0 15%;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 5%;
`;

const BottomSection = styled.div`
    flex: 1;
    background-color: #ffffff;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 5%;
    flex-direction: column; // 세로 방향으로 정렬
`;

const App = () => {
  const [searchCriteria, setSearchCriteria] = useState({ startDate: null, endDate: null, searchValue: '' });
  const [taxis, setTaxis] = useState([]);

  const handleSearch = (criteria) => {
      console.log('Search Criteria:', criteria);
      setSearchCriteria(criteria);
      fetchUsers(criteria);
  };

  const fetchUsers = async (criteria) => {
      try {
          const response = await fetch('http://localhost:5000/select_data', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify(criteria),
          });
          const data = await response.json();
          console.log('Fetched Taxis:', data);
          setTaxis(data);
      } catch (error) {
          console.error('Error fetching taxis:', error);
      }
  };

  return (
      <Provider store={store}>
          <BrowserRouter>
              <Container>
                    <Header>
                        <Button to="/manager/taxi/list">택시 리스트</Button>
                        <Button to="/manager/taxi/chart">매출 조회</Button>
                        <Button to="/user/video">운영 영상</Button>
                        <Button to="/user/driving">호출하기</Button>
                        <Button to="/user/money/chart">유저 차트</Button>
                        <Button to="/">홈으로</Button>
                    </Header>
                    <Routes>
                        <Route path='manager/taxi/list' element={
                            <TopSection>
                                <SearchHeader onSearch={handleSearch} />
                            </TopSection>}
                        />
                    </Routes>
                  <BottomSection>
                      <Routes>
                          <Route path='manager/taxi/list' element={<TaxiList taxis={taxis} />} />
                          <Route path='manager/taxi/chart' element={<PieChart />} />
                          <Route path='user/video' element={<LiveVideo />} />
                          <Route path='user/driving' element={<Driving />} />
                          <Route path='user/money/chart' element={<UserMoney />} />
                      </Routes>
                  </BottomSection>
              </Container>
          </BrowserRouter>
      </Provider>
  );
};

export default App;
