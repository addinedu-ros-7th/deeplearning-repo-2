import React from 'react';
import styled from 'styled-components';

// Styled components
const ListContainer = styled.div`
    width: 100%; // 너비를 100%로 설정
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
    background-color: #f9f9f9;
`;

const Table = styled.div`
    display: table;
    width: 100%;
    border-collapse: collapse;
`;

const TableHeader = styled.div`
    display: table-row;
    font-weight: bold;
    background-color: #e0e0e0;
`;

const TableRow = styled.div`
    display: table-row;
`;

const TableCell = styled.div`
    display: table-cell;
    padding: 10px;
    border: 1px solid #ddd;
    text-align: left;
    vertical-align: middle;
`;

const TaxiList = ({ taxis }) => {
    return (
        <ListContainer>
            <Table>
                <TableHeader>
                    <TableCell>Taxi ID</TableCell>
                    <TableCell>Username</TableCell>
                    <TableCell>Phone</TableCell>
                    <TableCell>Start Time</TableCell>
                    <TableCell>End Time</TableCell>
                    <TableCell>Distance</TableCell>
                    <TableCell>Charge</TableCell>
                    <TableCell>Start Location</TableCell>
                    <TableCell>Start Point</TableCell>  
                    <TableCell>End Point</TableCell>  
                </TableHeader>
                {taxis.length > 0 ? (
                    taxis.map(taxi => (
                        <TableRow key={taxi.taxi_id}>
                            <TableCell>{taxi.taxi_id}</TableCell>
                            <TableCell>{taxi.username}</TableCell>
                            <TableCell>{taxi.phone_number}</TableCell>
                            <TableCell>{taxi.start_time}</TableCell>
                            <TableCell>{taxi.end_time}</TableCell>
                            <TableCell>{taxi.distance}</TableCell>
                            <TableCell>{taxi.charge}</TableCell>
                            <TableCell>{taxi.start_location}</TableCell>
                            <TableCell>{taxi.start_point}</TableCell> 
                            <TableCell>{taxi.end_point}</TableCell>
                        </TableRow>
                    ))
                ) : (
                    <TableRow>
                        <TableCell colSpan={11}>No taxis found.</TableCell>
                    </TableRow>
                )}
            </Table>
        </ListContainer>
    );
};

export default TaxiList;
