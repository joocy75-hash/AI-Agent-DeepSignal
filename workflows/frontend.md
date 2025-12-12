---
description: 프론트엔드 컴포넌트 개발 - 새 페이지/컴포넌트 추가 절차
---

# 🎨 프론트엔드 개발 워크플로우

## 📋 사전 준비

### 1. SKILL 파일 읽기

// turbo

- `skills/frontend-trading-dashboard/SKILL.md` 읽기

### 2. 기존 컴포넌트 구조 파악

- `frontend/src/pages/` - 페이지 컴포넌트
- `frontend/src/components/` - 재사용 가능 컴포넌트

## 🛠️ 개발 단계

### Step 1: 페이지 컴포넌트 생성

```
위치: frontend/src/pages/
파일: {PageName}.jsx
```

```jsx
import { useState, useEffect } from 'react';
import { Row, Col, Card, message } from 'antd';
import apiClient from '../api/client';

const NewPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/api/endpoint');
      setData(response.data);
    } catch (error) {
      message.error('데이터 로드 실패');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ background: '#0d0d14', minHeight: 'calc(100vh - 64px)', padding: 24 }}>
      <h1 style={{ color: '#fff' }}>New Page</h1>
      {/* 콘텐츠 */}
    </div>
  );
};

export default NewPage;
```

### Step 2: 라우터 등록

```
위치: frontend/src/App.jsx
```

```jsx
const NewPage = lazy(() => import('./pages/NewPage'));

<Route path="/new-page" element={
  <ProtectedRoute><NewPage /></ProtectedRoute>
} />
```

### Step 3: 네비게이션 추가

```
위치: frontend/src/components/layout/MainLayout.jsx
```

```jsx
{ key: '/new-page', icon: <SomeIcon />, label: '새 페이지' },
```

### Step 4: API 모듈 생성 (필요시)

```
위치: frontend/src/api/
파일: {feature}.js
```

```javascript
import apiClient from './client';

const featureAPI = {
  list: async () => {
    const response = await apiClient.get('/feature/list');
    return response.data;
  },
  create: async (data) => {
    const response = await apiClient.post('/feature/create', data);
    return response.data;
  },
};

export default featureAPI;
```

### Step 5: 테스트

```bash
# 개발 서버 실행
npm run dev

# 브라우저에서 확인
http://localhost:3000/new-page
```

## 🎨 스타일 가이드

| 요소 | 스타일 |
|------|--------|
| 배경 | `#0d0d14` |
| 카드 배경 | `#1a1a2e` |
| 테두리 | `#2d2d44` |
| 텍스트 | `#ffffff` |
| 보조 텍스트 | `#a0a0b0` |
| 수익 | `#00d26a` |
| 손실 | `#ff4757` |

## ✅ 완료 체크리스트

- [ ] 페이지 컴포넌트 생성
- [ ] 라우터 등록
- [ ] 네비게이션 추가
- [ ] API 연동
- [ ] 다크 테마 적용
- [ ] 반응형 디자인 확인
- [ ] 에러 처리 추가
- [ ] 로딩 상태 표시
