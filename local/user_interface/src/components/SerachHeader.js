import React, { useState } from 'react';
import styled from 'styled-components';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
import axios from 'axios';

// Styled-components
const Container = styled.div`
    display: flex;
    align-items: center;
    padding: 20px;
    background-color: #f9f9f9;
    border: 1px solid #ddd;
    border-radius: 5px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
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

const Spacer = styled.div`
    margin: 0 10px; // 버튼과 입력 필드 사이의 간격
`;

const SearchHeader = ({ onSearch }) => {
    const [startDate, setStartDate] = useState(null);
    const [endDate, setEndDate] = useState(null);
    const [searchValue, setSearchValue] = useState('');
    const [taxiList, setTaxiList] = useState([]);
    const [showPopup, setShowPopup] = useState(false);
    const [searchByTaxiId, setSearchByTaxiId] = useState(false); // 체크박스 상태 추가

    const handleSearch = () => {
        const criteria = {
            startDate,
            endDate,
            searchValue,
            searchByTaxiId, // 체크박스 상태 포함
        };
        onSearch(criteria);
    };

    const fetchTaxiList = async () => {
        try {
            const response = await axios.get('http://localhost:5000/taxi_list');
            setTaxiList(response.data);
            setShowPopup(true);
        } catch (error) {
            console.error('Error fetching taxi list:', error);
        }
    };

    return (
        <Container>
            <DatePickerStyled
                selected={startDate}
                onChange={(date) => setStartDate(date)}
                selectsStart
                startDate={startDate}
                endDate={endDate}
                placeholderText="시작 날짜"
            />
            <DatePickerStyled
                selected={endDate}
                onChange={(date) => setEndDate(date)}
                selectsEnd
                startDate={startDate}
                endDate={endDate}
                placeholderText="종료 날짜"
                minDate={startDate}
            />
            <Input
                type="text"
                placeholder="검색할 값 입력"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
            />
            <Spacer />
            <label>
                <input
                    type="checkbox"
                    checked={searchByTaxiId}
                    onChange={() => setSearchByTaxiId(!searchByTaxiId)}
                />
                taxi_id로 검색
            </label>
            <Spacer />
            <Button onClick={handleSearch}>검색</Button>
            <Spacer />
            <Button onClick={fetchTaxiList}>택시 차량번호 리스트</Button>

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

export default SearchHeader;
