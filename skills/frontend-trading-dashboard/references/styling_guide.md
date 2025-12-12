# 스타일링 가이드 참조

## TailwindCSS 설정

### 현재 프로젝트의 테마 (tailwind.config.js)

```javascript
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // 커스텀 색상
        primary: '#3B82F6',
        secondary: '#6B7280',
        success: '#10B981',
        danger: '#EF4444',
        warning: '#F59E0B',
      },
    },
  },
  plugins: [],
};
```

---

## 색상 팔레트 (다크 테마)

| 용도 | TailwindCSS 클래스 | Hex |
|------|-------------------|-----|
| 메인 배경 | `bg-gray-900` | #111827 |
| 카드 배경 | `bg-gray-800` | #1F2937 |
| 입력 필드 배경 | `bg-gray-700` | #374151 |
| 테두리 | `border-gray-700` | #374151 |
| 기본 텍스트 | `text-white` | #FFFFFF |
| 보조 텍스트 | `text-gray-400` | #9CA3AF |
| 성공 (수익) | `text-green-400` | #4ADE80 |
| 실패 (손실) | `text-red-400` | #F87171 |
| 강조 | `text-blue-400` | #60A5FA |
| 경고 | `text-yellow-400` | #FBBF24 |

---

## 레이아웃 패턴

### 기본 페이지 레이아웃

```jsx
const PageLayout = ({ children }) => (
  <div className="min-h-screen bg-gray-900">
    <MainLayout>
      <div className="p-4 md:p-6 lg:p-8">
        {children}
      </div>
    </MainLayout>
  </div>
);
```

### 그리드 레이아웃

```jsx
// 반응형 카드 그리드
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
  {items.map(item => <Card key={item.id} item={item} />)}
</div>

// 대시보드 그리드 (사이드바 + 메인)
<div className="flex flex-col lg:flex-row gap-4">
  <div className="lg:w-1/3 xl:w-1/4">
    {/* 사이드바 */}
  </div>
  <div className="lg:w-2/3 xl:w-3/4">
    {/* 메인 컨텐츠 */}
  </div>
</div>
```

### Flexbox 패턴

```jsx
// 수평 정렬
<div className="flex items-center justify-between">
  <span>왼쪽</span>
  <span>오른쪽</span>
</div>

// 수직 가운데 정렬
<div className="flex items-center justify-center h-screen">
  <LoadingSpinner />
</div>

// 간격 있는 수평 배치
<div className="flex items-center gap-4">
  <Button>버튼1</Button>
  <Button>버튼2</Button>
</div>
```

---

## 컴포넌트 스타일

### 버튼

```jsx
// 기본 버튼
<button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors">
  버튼
</button>

// 아웃라인 버튼
<button className="px-4 py-2 border border-blue-500 text-blue-500 hover:bg-blue-500 hover:text-white font-medium rounded-lg transition-colors">
  버튼
</button>

// 위험 버튼
<button className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white font-medium rounded-lg transition-colors">
  삭제
</button>

// 비활성화
<button className="px-4 py-2 bg-gray-500 text-gray-300 font-medium rounded-lg cursor-not-allowed opacity-50" disabled>
  비활성화
</button>

// 로딩 버튼
<button className="px-4 py-2 bg-blue-500 text-white font-medium rounded-lg flex items-center gap-2" disabled>
  <span className="loading loading-spinner loading-sm"></span>
  처리 중...
</button>
```

### 입력 필드

```jsx
// 기본 입력
<input
  type="text"
  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
  placeholder="입력하세요"
/>

// 에러 상태
<input
  type="text"
  className="w-full px-3 py-2 bg-gray-700 border border-red-500 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
/>

// 레이블과 함께
<div className="space-y-1">
  <label className="block text-sm text-gray-400">이메일</label>
  <input
    type="email"
    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
  />
</div>

// 아이콘 포함
<div className="relative">
  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
  <input
    type="text"
    className="w-full pl-10 pr-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
    placeholder="검색"
  />
</div>
```

### 카드

```jsx
// 기본 카드
<div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
  <h3 className="text-lg font-semibold text-white mb-2">제목</h3>
  <p className="text-gray-400">내용</p>
</div>

// 그림자 카드
<div className="bg-gray-800 rounded-xl p-4 shadow-lg shadow-black/20">
  내용
</div>

// 호버 효과 카드
<div className="bg-gray-800 rounded-xl p-4 border border-gray-700 hover:border-blue-500 hover:shadow-lg hover:shadow-blue-500/10 transition-all cursor-pointer">
  클릭 가능한 카드
</div>

// 상태 카드
<div className="bg-gray-800 rounded-xl p-4 border-l-4 border-green-500">
  <div className="flex items-center gap-2">
    <CheckCircle className="w-5 h-5 text-green-400" />
    <span className="text-white">성공</span>
  </div>
</div>
```

### 테이블

```jsx
<div className="overflow-x-auto rounded-lg border border-gray-700">
  <table className="w-full">
    <thead className="bg-gray-700/50">
      <tr>
        <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">
          컬럼1
        </th>
        <th className="px-4 py-3 text-left text-sm font-medium text-gray-300">
          컬럼2
        </th>
      </tr>
    </thead>
    <tbody className="divide-y divide-gray-700">
      {rows.map((row, i) => (
        <tr key={i} className="hover:bg-gray-700/30 transition-colors">
          <td className="px-4 py-3 text-sm text-white">{row.col1}</td>
          <td className="px-4 py-3 text-sm text-gray-400">{row.col2}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

### 배지

```jsx
// 상태 배지
<span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-500/10 text-green-400">
  활성
</span>

// 카운트 배지
<span className="inline-flex items-center justify-center w-5 h-5 text-xs font-bold text-white bg-red-500 rounded-full">
  3
</span>

// 아이콘 배지
<span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400">
  <TrendingUp className="w-3 h-3" />
  +5.2%
</span>
```

---

## 애니메이션

### 기본 트랜지션

```jsx
// 색상 변경
<button className="transition-colors hover:bg-blue-600">
  버튼
</button>

// 모든 속성
<div className="transition-all hover:scale-105 hover:shadow-lg">
  카드
</div>

// 특정 속성
<div className="transition-transform hover:-translate-y-1">
  호버 시 위로 이동
</div>
```

### 로딩 애니메이션

```jsx
// 스피너
<div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />

// 펄스
<div className="animate-pulse bg-gray-700 rounded h-4 w-full" />

// 스켈레톤 로딩
<div className="space-y-3">
  <div className="h-4 bg-gray-700 rounded animate-pulse w-3/4" />
  <div className="h-4 bg-gray-700 rounded animate-pulse w-1/2" />
  <div className="h-4 bg-gray-700 rounded animate-pulse w-5/6" />
</div>
```

### 페이드 인/아웃

```css
/* index.css */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

.animate-fade-in {
  animation: fadeIn 0.3s ease-out;
}
```

---

## 반응형 디자인

### 브레이크포인트

| 프리픽스 | 최소 너비 | 용도 |
|---------|---------|------|
| `sm:` | 640px | 모바일 (가로) |
| `md:` | 768px | 태블릿 |
| `lg:` | 1024px | 노트북 |
| `xl:` | 1280px | 데스크탑 |
| `2xl:` | 1536px | 대형 모니터 |

### 반응형 패턴

```jsx
// 그리드 반응형
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* 카드들 */}
</div>

// 숨기기/보이기
<div className="hidden lg:block">
  {/* 데스크탑에서만 표시 */}
</div>

<div className="lg:hidden">
  {/* 모바일/태블릿에서만 표시 */}
</div>

// 텍스트 크기
<h1 className="text-xl md:text-2xl lg:text-3xl font-bold">
  반응형 제목
</h1>

// 패딩/마진
<div className="p-4 md:p-6 lg:p-8">
  반응형 패딩
</div>
```

---

## Ant Design 커스터마이징

```jsx
// antd 테이블 다크 테마
<ConfigProvider
  theme={{
    algorithm: theme.darkAlgorithm,
    token: {
      colorBgContainer: '#1F2937',
      colorBorder: '#374151',
      colorText: '#FFFFFF',
      colorTextSecondary: '#9CA3AF',
    },
  }}
>
  <Table />
</ConfigProvider>
```

```css
/* antd 커스텀 스타일 (index.css) */
.ant-table {
  background-color: #1f2937 !important;
}

.ant-table-thead > tr > th {
  background-color: #374151 !important;
  color: #f9fafb !important;
}

.ant-table-tbody > tr > td {
  border-color: #374151 !important;
}

.ant-table-tbody > tr:hover > td {
  background-color: #374151 !important;
}
```
