# 담당자(Assignee) 레코드 뷰 모듈화 플랜

**날짜**: 2025-10-08
**목표**: record_list.html을 모듈화하여 assignee_records와 공통 UI 사용

---

## 📋 현재 문제점

1. **UI 불일치**: `record_list.html`과 `assignee_records.html`이 서로 다른 디자인
2. **중복 코드**: 필터, 레코드 목록, 페이지네이션 등이 중복 구현
3. **확장성 부족**: 새로운 뷰 추가 시 매번 전체 UI 재작성 필요
4. **컨텍스트 유지 실패**: 수정 후 담당자 페이지로 복귀하지 못함

---

## 🎯 목표

### 1. 모듈화된 템플릿 구조
- 공통 스타일/레이아웃을 재사용 가능한 컴포넌트로 분리
- 각 뷰에서 필요한 부분만 조립하여 사용

### 2. Assignee 전용 헤더
- "○○의 작업 영역" 대시보드 (진행률, 통계)
- IDS 범위 표시
- 전체 목록 링크

### 3. URL 파라미터 보존
- `assignee_id` 파라미터를 detail/edit 페이지까지 전달
- 수정 완료 후 담당자 페이지로 복귀

---

## 📐 새로운 템플릿 구조

```
records/templates/records/
├── record_list.html              # 전체 목록 (기존, 리팩토링)
├── assignee_records_view.html    # 담당자 전용 뷰 (새로 생성)
│
├── includes/
│   ├── _styles.html              # 공통 CSS 스타일
│   ├── _scripts.html             # 공통 JavaScript
│   ├── _header.html              # Yonsei 헤더
│   ├── _sidebar.html             # 사이드바
│   ├── _assignee_header.html     # 담당자 대시보드 헤더 ⭐ NEW
│   ├── _filter_form.html         # 필터 폼
│   ├── _record_items.html        # 레코드 카드 목록
│   └── _pagination.html          # 페이지네이션
```

---

## 🔧 구현 세부사항

### Step 1: 공통 스타일 분리
**파일**: `includes/_styles.html`
- 모든 CSS 스타일을 독립 파일로 분리

### Step 2: 필터 폼 모듈화
**파일**: `includes/_filter_form.html`

**컨텍스트 변수**:
- `show_mapping_stats`: 사전 매칭 통계 표시 여부 (기본: True)
- `assignee_mode`: 담당자 모드 여부 (기본: False)

### Step 3: 레코드 목록 모듈화
**파일**: `includes/_record_items.html`

### Step 4: 담당자 헤더 생성
**파일**: `includes/_assignee_header.html`

### Step 5: View 로직 변경
`AssigneeRecordsView` 클래스 생성 (ListView 기반)

---

## 📝 템플릿 사용 예시

### `assignee_records_view.html` (담당자 전용)
```django
{% include "records/includes/_styles.html" %}
{% include "records/includes/_header.html" %}
{% include "records/includes/_sidebar.html" %}
{% include "records/includes/_assignee_header.html" %}
{% include "records/includes/_filter_form.html" %}
{% include "records/includes/_record_items.html" %}
{% include "records/includes/_pagination.html" %}
{% include "records/includes/_scripts.html" %}
```

---

## ✅ 구현 체크리스트

- [ ] `includes/_styles.html` 생성
- [ ] `includes/_scripts.html` 생성
- [ ] `includes/_header.html` 생성
- [ ] `includes/_sidebar.html` 생성
- [ ] `includes/_filter_form.html` 생성
- [ ] `includes/_record_items.html` 생성
- [ ] `includes/_pagination.html` 생성
- [ ] `includes/_assignee_header.html` 생성 ⭐
- [ ] `record_list.html` 리팩토링
- [ ] `assignee_records_view.html` 생성
- [ ] `AssigneeRecordsView` 클래스 생성
- [ ] Assignee 모델에 통계 properties 추가
- [ ] URL 파라미터 보존 로직 추가
- [ ] 네비게이션 개선
- [ ] 테스트
- [ ] GitHub 커밋
