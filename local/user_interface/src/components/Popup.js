import React, { useState } from 'react';
import styled from 'styled-components';

// Styled components for the popup
const PopupContainer = styled.div`
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
`;

const PopupContent = styled.div`
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3);
    width: 300px;
`;

const Input = styled.input`
    width: 100%;
    padding: 10px;
    margin: 10px 0;
    border: 1px solid #ddd;
    border-radius: 4px;
`;

const Button = styled.button`
    margin-top: 10px;
    padding: 10px;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;

    &:hover {
        background-color: #0056b3;
    }
`;

const Popup = ({ onClose, onSubmit }) => {
    const [inputValue, setInputValue] = useState('');

    const handleSubmit = () => {
        onSubmit(inputValue);
        onClose();
    };

    return (
        <PopupContainer>
            <PopupContent>
                <h2>출발지 수정하기</h2>
                <Input
                    type="text"
                    placeholder="새 출발지 입력"
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                />
                <Button onClick={handleSubmit}>확인</Button>
                <Button onClick={onClose} style={{ marginLeft: '10px' }}>취소</Button>
            </PopupContent>
        </PopupContainer>
    );
};

export default Popup;
