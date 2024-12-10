import { createStore } from 'redux';

// 초기 상태
const initialState = {
    startDate: null,
    endDate: null,
    searchValue: '',
};

// 리듀서
const reducer = (state = initialState, action) => {
    switch (action.type) {
        case 'SET_START_DATE':
            return { ...state, startDate: action.payload };
        case 'SET_END_DATE':
            return { ...state, endDate: action.payload };
        case 'SET_SEARCH_VALUE':
            return { ...state, searchValue: action.payload };
        default:
            return state;
    }
};

// 스토어 생성
const store = createStore(reducer);

export default store;
