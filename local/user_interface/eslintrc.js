module.exports = {
    // ... 기존 설정 ...
    "extends": [
      "eslint:recommended",
      "plugin:react/recommended" // 추가
    ],
    "plugins": [
      "react" // 추가
    ],
    "settings": {
      "react": {
        "version": "detect" // 추가
      }
    }
  };