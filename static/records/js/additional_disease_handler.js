/**
 * 추가 질병 필드 처리 및 계층적 자동입력 로직
 */

(function() {
    'use strict';

    // 추가 질병 D-ai+ 버튼 핸들러
    document.addEventListener('DOMContentLoaded', function() {
        const additionalDiseaseBtn = document.getElementById('additional-disease-ai-btn');

        if (additionalDiseaseBtn) {
            additionalDiseaseBtn.addEventListener('click', function() {
                const query = document.getElementById('additional_disease_input')?.value || '';
                const popupUrl = `/epedit/ai-search-popup/?target=disease&title=D-ai%2B:%20추가%20질병%20검색&query=${encodeURIComponent(query)}`;

                const popup = window.open(
                    popupUrl,
                    'AdditionalDiseaseAiSearch',
                    'width=1400,height=900,resizable=yes,scrollbars=yes'
                );

                if (!popup || popup.closed || typeof popup.closed === 'undefined') {
                    alert('팝업이 차단되었습니다. 팝업 차단을 해제해주세요.');
                }

                // 전역 핸들러에 추가 질병용 플래그 설정
                window.currentAdditionalDiseaseMode = true;
            });
        }
    });

    // AI 검색 결과 처리 확장 (기존 handleAiSearchResult 수정 필요)
    const originalHandleAiSearchResult = window.handleAiSearchResult;

    window.handleAiSearchResult = function(result, searchTarget) {
        // 추가 질병 모드인 경우
        if (window.currentAdditionalDiseaseMode && searchTarget === 'disease') {
            handleAdditionalDiseaseResult(result);
            window.currentAdditionalDiseaseMode = false;
        } else {
            // 기존 로직 호출
            if (originalHandleAiSearchResult) {
                originalHandleAiSearchResult(result, searchTarget);
            }
        }
    };

    // 추가 질병 결과 처리
    function handleAdditionalDiseaseResult(result) {
        const selectedCode = result.code || '';
        const selectedName = result.name || result.disease_name || '';
        const selectedPath = result.path || '';

        console.log('추가 질병 선택:', selectedCode, selectedName);

        // 추가 질병명/코드 설정 (메인 질병 필드는 변경하지 않음)
        const additionalInput = document.getElementById('additional_disease_input');
        const additionalHidden = document.getElementById('additional_disease_hidden');
        const additionalCodeDisplay = document.getElementById('additional_disease_code_display');
        const additionalCodeHidden = document.getElementById('additional_disease_code_hidden_form');

        if (additionalInput) additionalInput.value = selectedName;
        if (additionalHidden) additionalHidden.value = selectedName;
        if (additionalCodeDisplay) additionalCodeDisplay.value = selectedCode;
        if (additionalCodeHidden) additionalCodeHidden.value = selectedCode;

        // 태그 추가
        const tagsContainer = document.getElementById('additional_disease_tags');
        if (tagsContainer) {
            tagsContainer.innerHTML = '';
            const tagItem = document.createElement('div');
            tagItem.className = 'tag-item';
            tagItem.innerHTML = `<span>${selectedName}</span><span class="tag-close">X</span>`;
            tagItem.addEventListener('click', function() {
                tagItem.remove();
                if (additionalInput) additionalInput.value = '';
                if (additionalHidden) additionalHidden.value = '';
                if (additionalCodeDisplay) additionalCodeDisplay.value = '';
                if (additionalCodeHidden) additionalCodeHidden.value = '';
            });
            tagsContainer.appendChild(tagItem);
        }

        console.log('추가 질병 필드만 업데이트됨 (메인 질병은 변경 없음)');
    }

})();
