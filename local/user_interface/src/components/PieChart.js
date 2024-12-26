import React, { useState } from 'react';
import { Pie } from 'react-chartjs-2';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import styled from 'styled-components';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

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
    width: 100%; // 너비 100%
`;

const InputContainer = styled.div`
    display: flex;
    justify-content: space-between; // 가로 정렬 및 공간 분배
    width: 100%; // 너비 100%
    max-width: 800px; // 최대 너비 조정
    margin-bottom: 20px; // 입력 필드와 차트 사이의 간격
`;

const DatePickerStyled = styled(DatePicker)`
    margin-right: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    padding: 10px;
    width: 150px;
    font-size: 16px;
    background-color: #ffffff;

    &:focus {
        outline: none;
        border-color: #007bff;
    }
`;

const Input = styled.input`
    padding: 10px;
    margin-right: 10px;
    border: 1px solid #ccc;
    border-radius: 5px;
    flex: 1;
    font-size: 16px;

    &:focus {
        border-color: #007bff;
        outline: none;
    }
`;

const Button = styled.button`
    padding: 10px 20px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;

    &:hover {
        background-color: #0056b3;
    }
`;

const ChartContainer = styled.div`
    margin-top: 20px;
    width: 100%; // 너비 100%
    height: 500px; // 차트 높이 설정
    max-width: 600px; // 최대 너비 조정
`;

const ListButton = styled(Button)`
    margin-top: 20px; // 버튼과 차트 사이 간격
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

const TaxiListTable = styled.table`
    width: 100%;
    border-collapse: collapse;

    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }

    th {
        background-color: #f2f2f2;
    }
`;

const PieChart = () => {
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

    const [taxiId, setTaxiId] = useState('');
    const [startDate, setStartDate] = useState(null);
    const [endDate, setEndDate] = useState(null);
    const [showPopup, setShowPopup] = useState(false);
    const [taxiList, setTaxiList] = useState([]);

    const fetchData = async () => {
        try {
            const response = await fetch('http://localhost:5000/revenue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    taxiId: taxiId || null,
                    startDate: startDate ? startDate.toISOString().split('T')[0] : null,
                    endDate: endDate ? endDate.toISOString().split('T')[0] : null,
                }),
            });
            const json = await response.json();

            // 데이터가 예상한 형식인지 확인
            if (json && json.taxi_id) {
                const newChartData = {
                    labels: [`Taxi ID: ${json.taxi_id}`],
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
            console.error('Error fetching revenue data:', error);
        }
    };

    const handleSearch = () => {
        fetchData();
    };

    const fetchTaxiList = async () => {
        try {
            const response = await fetch('http://localhost:5000/taxi_list');
            const data = await response.json();
            setTaxiList(data);
            setShowPopup(true);
        } catch (error) {
            console.error('Error fetching taxi list:', error);
        }
    };

    return (
        <Container>
            <h2>택시 매출 검색</h2>
            <InputContainer>
                <Input
                    type="text"
                    placeholder="택시 ID"
                    value={taxiId}
                    onChange={(e) => setTaxiId(e.target.value)}
                />
                <DatePickerStyled
                    selected={startDate}
                    onChange={(date) => setStartDate(date)}
                    placeholderText="시작 날짜"
                />
                <DatePickerStyled
                    selected={endDate}
                    onChange={(date) => setEndDate(date)}
                    placeholderText="종료 날짜"
                    minDate={startDate}
                />
                <Button onClick={handleSearch}>검색</Button>
            </InputContainer>

            <ChartContainer>
                {chartData.labels.length > 0 ? (
                    <Pie data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />
                ) : (
                    <p>Loading chart data...</p>
                )}
            </ChartContainer>

            <ListButton onClick={fetchTaxiList}>택시 차량번호 조회하기</ListButton>

            {showPopup && (
                <>
                    <Overlay onClick={() => setShowPopup(false)} />
                    <PopupContainer>
                        <h2>택시 차량번호 리스트</h2>
                        <TaxiListTable>
                            <thead>
                                <tr>
                                    <th>Taxi ID</th>
                                    <th>Taxi Type</th>
                                </tr>
                            </thead>
                            <tbody>
                                {taxiList.length > 0 ? (
                                    taxiList.map(taxi => (
                                        <tr key={taxi.taxi_id}>
                                            <td>{taxi.taxi_id}</td>
                                            <td>{taxi.taxi_type}</td>
                                        </tr>
                                    ))
                                ) : (
                                    <tr>
                                        <td colSpan="2">택시 정보가 없습니다.</td>
                                    </tr>
                                )}
                            </tbody>
                        </TaxiListTable>
                        <Button onClick={() => setShowPopup(false)}>닫기</Button>
                    </PopupContainer>
                </>
            )}
        </Container>
    );
};

export default PieChart;
