import React, { useState } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import styled from 'styled-components';
import axios from 'axios';

// Chart.js에서 사용할 컴포넌트 등록
ChartJS.register(ArcElement, Tooltip, Legend);

// Styled-components
const Container = styled.div`
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 20px;
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    width: 100%;
`;

const InputContainer = styled.div`
    display: flex;
    justify-content: space-between;
    width: 100%;
    max-width: 900px; // 최대 너비 증가
    margin-bottom: 20px;
`;

const Input = styled.input`
    padding: 10px;
    margin: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    flex: 1; // 남은 공간 모두 차지
    font-size: 18px; // 글자 크기 증가
    min-width: 100px; // 최소 너비 설정

    &:focus {
        border-color: #007bff;
        outline: none;
    }
`;

const Button = styled.button`
    padding: 10px 20px; // 패딩 유지
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 18px; // 글자 크기 증가
    min-width: 120px; // 최소 너비 설정

    &:hover {
        background-color: #0056b3;
    }
`;

const ChartContainer = styled.div`
    margin-top: 20px;
    width: 100%;
    height: 500px;
    max-width: 600px;
`;

const UserListContainer = styled.div`
    margin-top: 20px;
    max-width: 800px;
    width: 100%;
`;

const UserItem = styled.div`
    padding: 5px;
    border: 1px solid #ddd;
    border-radius: 5px;
    margin: 5px 0;
`;

const PopupContainer = styled.div`
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background-color: white;
    border: 1px solid #ddd;
    border-radius: 5px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    padding: 20px;
    z-index: 1000;
    width: 90%; // 팝업 너비 증가
    max-width: 600px; // 최대 너비 조정
    height: auto; // 자동 높이
    max-height: 80vh; // 최대 높이 설정
    overflow-y: auto; // 내용이 많은 경우 스크롤 가능
`;

const Overlay = styled.div`
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.5);
    z-index: 999;
`;

const UserMoney = () => {
    const [chartData, setChartData] = useState({
        labels: [],
        datasets: [{
            label: 'Total Revenue',
            data: [],
            backgroundColor: [
                'rgba(75, 192, 192, 0.6)',
                'rgba(153, 102, 255, 0.6)',
            ],
            borderColor: 'rgba(255, 255, 255, 1)',
            borderWidth: 1,
        }],
    });

    const [userId, setUserId] = useState('');
    const [startDate, setStartDate] = useState('');
    const [endDate, setEndDate] = useState('');
    const [userList, setUserList] = useState([]);
    const [showPopup, setShowPopup] = useState(false);

    const fetchUserList = async () => {
        try {
            const response = await axios.get('http://localhost:5000/users');
            setUserList(response.data);
            setShowPopup(true); // 팝업 열기
        } catch (error) {
            console.error('Error fetching users:', error);
        }
    };

    const fetchData = async () => {
        try {
            const response = await axios.post('http://localhost:5000/user_revenue', {
                userId: userId || null,
                startDate: startDate || null,
                endDate: endDate || null,
            });
            const json = response.data;

            // 데이터가 예상한 형식인지 확인
            if (json && json.user_id) {
                const newChartData = {
                    labels: [`User ID: ${json.user_id}`],
                    datasets: [{
                        label: 'Total Revenue',
                        data: [json.total_revenue],
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.6)',
                            'rgba(153, 102, 255, 0.6)',
                        ],
                        borderColor: 'rgba(255, 255, 255, 1)',
                        borderWidth: 1,
                    }],
                };

                console.log('Chart Data:', newChartData);
                setChartData(newChartData);
            } else {
                console.error('Unexpected response format:', json);
            }
        } catch (error) {
            console.error('Error fetching user revenue data:', error);
        }
    };

    const handleSearch = () => {
        fetchData();
    };

    return (
        <Container>
            <h2>사용자 요금 지출 검색</h2>
            <InputContainer>
                <Input
                    type="text"
                    placeholder="사용자 ID"
                    value={userId}
                    onChange={(e) => setUserId(e.target.value)}
                />
                <Input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                />
                <Input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                />
                <Button onClick={handleSearch}>검색</Button>
                <div style={{ marginLeft: '10px' }} /> {/* 간격 추가 */}
                <Button onClick={fetchUserList}>사용자 목록 조회</Button>
            </InputContainer>

            <ChartContainer>
                {chartData.labels.length > 0 ? (
                    <Pie data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />
                ) : (
                    <p>Loading chart data...</p>
                )}
            </ChartContainer>

            {showPopup && (
                <>
                    <Overlay onClick={() => setShowPopup(false)} />
                    <PopupContainer>
                        <h3>사용자 목록</h3>
                        <UserListContainer>
                            {userList.length > 0 ? (
                                userList.map(user => (
                                    <UserItem key={user.user_id}>
                                        ID: {user.user_id}, 이름: {user.username}
                                    </UserItem>
                                ))
                            ) : (
                                <p>사용자가 없습니다.</p>
                            )}
                        </UserListContainer>
                        <Button onClick={() => setShowPopup(false)}>닫기</Button>
                    </PopupContainer>
                </>
            )}
        </Container>
    );
};

export default UserMoney;