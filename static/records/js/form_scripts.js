/* records/static/records/js/form_scripts.js */

document.addEventListener('DOMContentLoaded', function () {
    console.log('Form scripts loading...');
    const config = window.RECORD_FORM_CONFIG || {};
    console.log('Config:', config);

    const autocompleteUrl = config.autocompleteUrl;
    const getDiseaseCodeUrl = config.getDiseaseCodeUrl;
    const getJobCodeUrl = config.getJobCodeUrl;
    const ragSearchApiUrl = config.ragSearchApiUrl;

    console.log('URLs:', { autocompleteUrl, getDiseaseCodeUrl, getJobCodeUrl, ragSearchApiUrl });

    function debounce(func, delay) {
        let timeout;
        return function (...args) {
            const context = this;
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(context, args), delay);
        };
    }

    async function updateDiseaseCodeField(diseaseName) {
        const diseaseCodeDisplayInput = document.getElementById('disease_code_display');
        const diseaseCodeHiddenFormInput = document.getElementById('disease_code_hidden_form');

        if (!diseaseName) {
            if (diseaseCodeDisplayInput) diseaseCodeDisplayInput.value = '';
            if (diseaseCodeHiddenFormInput) diseaseCodeHiddenFormInput.value = '';
            return;
        }

        try {
            const response = await fetch(`${getDiseaseCodeUrl}?disease_name=${encodeURIComponent(diseaseName)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.disease_code) {
                if (diseaseCodeDisplayInput) diseaseCodeDisplayInput.value = data.disease_code;
                if (diseaseCodeHiddenFormInput) diseaseCodeHiddenFormInput.value = data.disease_code;
            } else {
                if (diseaseCodeDisplayInput) diseaseCodeDisplayInput.value = '코드 없음';
                if (diseaseCodeHiddenFormInput) diseaseCodeHiddenFormInput.value = '';
            }
        } catch (error) {
            console.error('Error fetching disease code:', error);
            if (diseaseCodeDisplayInput) diseaseCodeDisplayInput.value = '오류';
            if (diseaseCodeHiddenFormInput) diseaseCodeHiddenFormInput.value = '';
        }
    }

    async function updateJobCodeField(occupationName) {
        const jobCodeDisplayInput = document.getElementById('job_code_display');
        const jobCodeHiddenFormInput = document.getElementById('job_code_hidden_form');

        if (!occupationName) {
            if (jobCodeDisplayInput) jobCodeDisplayInput.value = '';
            if (jobCodeHiddenFormInput) jobCodeHiddenFormInput.value = '';
            return;
        }

        try {
            const response = await fetch(`${getJobCodeUrl}?occupation_name=${encodeURIComponent(occupationName)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            if (data.job_code) {
                if (jobCodeDisplayInput) jobCodeDisplayInput.value = data.job_code;
                if (jobCodeHiddenFormInput) jobCodeHiddenFormInput.value = data.job_code;
            } else {
                if (jobCodeDisplayInput) jobCodeDisplayInput.value = '코드 없음';
                if (jobCodeHiddenFormInput) jobCodeHiddenFormInput.value = '';
            }
        } catch (error) {
            console.error('Error fetching job code:', error);
            if (jobCodeDisplayInput) jobCodeDisplayInput.value = '오류';
            if (jobCodeHiddenFormInput) jobCodeHiddenFormInput.value = '';
        }
    }

    function setupAutocomplete(inputElementId, suggestionsContainerId, tagsContainerId, hiddenInputId, onTagAdded, onTagRemoved, allowMultiple = true) {
        console.log(`Setting up autocomplete for: ${inputElementId}`);

        const inputElement = document.getElementById(inputElementId);
        if (!inputElement) {
            console.error(`Input element not found: ${inputElementId}`);
            return;
        }

        const suggestionsContainer = document.getElementById(suggestionsContainerId);
        const tagsContainer = document.getElementById(tagsContainerId);
        const hiddenInput = document.getElementById(hiddenInputId);
        const fieldName = inputElement.dataset.fieldName;

        console.log(`Elements found for ${inputElementId}:`, {
            inputElement: !!inputElement,
            suggestionsContainer: !!suggestionsContainer,
            tagsContainer: !!tagsContainer,
            hiddenInput: !!hiddenInput,
            fieldName
        });

        let selectedTags = new Set();
        let currentFetchController = null;

        function loadInitialTags() {
            // ✅ 우선순위 1: hidden input에서 값 가져오기
            if (hiddenInput.value) {
                const initialValues = hiddenInput.value.split(',').map(v => v.trim()).filter(v => v !== '');
                initialValues.forEach(tagText => {
                    addTag(tagText, false);
                });
            }
            // ✅ 우선순위 2: hidden input이 비어있고 visible input에 값이 있으면 그 값을 사용
            else if (inputElement.value && inputElement.value.trim() !== '') {
                console.log(`Loading initial value from visible input ${inputElementId}: "${inputElement.value}"`);
                addTag(inputElement.value.trim(), false);
                // 입력 필드 비우기 (태그로 변환되었으므로)
                inputElement.value = '';
            }
        }

        function addTag(tagText, updateHidden = true) {
            if (selectedTags.has(tagText)) return;

            // 단일 선택인 경우 기존 태그 모두 제거
            if (!allowMultiple) {
                selectedTags.clear();
                tagsContainer.innerHTML = '';
            }

            selectedTags.add(tagText);
            const tagItem = document.createElement('div');
            tagItem.className = 'tag-item';
            tagItem.dataset.value = tagText;
            const tagTextSpan = document.createElement('span');
            tagTextSpan.textContent = tagText;
            tagItem.appendChild(tagTextSpan);
            const closeButton = document.createElement('span');
            closeButton.className = 'tag-close';
            closeButton.textContent = 'X';
            closeButton.addEventListener('click', () => removeTag(tagItem));
            tagItem.appendChild(closeButton);
            tagsContainer.appendChild(tagItem);
            if (updateHidden) updateHiddenInput();
            updateSuggestionsPosition();
            if (onTagAdded) onTagAdded(tagText);
        }

        function removeTag(tagItem) {
            const tagText = tagItem.dataset.value;
            selectedTags.delete(tagText);
            tagItem.remove();
            updateHiddenInput();
            updateSuggestionsPosition();
            if (onTagRemoved) {
                const currentTags = Array.from(selectedTags);
                if (currentTags.length > 0) {
                    onTagRemoved(currentTags[0]);
                } else {
                    onTagRemoved('');
                }
            }
        }

        function updateHiddenInput() {
            hiddenInput.value = Array.from(selectedTags).join(',');
        }

        function updateSuggestionsPosition() {
            const suggestionsContainer = document.getElementById(suggestionsContainerId);
            if (!suggestionsContainer || !suggestionsContainer.classList.contains('active')) return;
            const autocompleteWrapper = document.querySelector(`#${inputElementId}`).closest('.autocomplete-wrapper');
            if (!autocompleteWrapper) return;
            const wrapperHeight = autocompleteWrapper.offsetHeight;
            const calculatedTop = wrapperHeight + 5;
            suggestionsContainer.style.top = `${calculatedTop}px`;
            suggestionsContainer.style.left = `0px`;
            suggestionsContainer.style.width = autocompleteWrapper.offsetWidth + 'px';
        }

        const fetchSuggestions = debounce(async (query) => {
            console.log(`Fetching suggestions for ${fieldName}, query: "${query}"`);

            if (!autocompleteUrl) {
                console.error('Autocomplete URL not configured');
                return;
            }

            if (currentFetchController) currentFetchController.abort();
            currentFetchController = new AbortController();
            const { signal } = currentFetchController;

            try {
                const url = `${autocompleteUrl}?field_name=${fieldName}&q=${encodeURIComponent(query)}`;
                console.log(`Fetching: ${url}`);

                const response = await fetch(url, { signal });
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();

                console.log(`Response for ${fieldName}:`, data);
                renderSuggestions(data.suggestions || []);
            } catch (error) {
                if (error.name !== 'AbortError') {
                    console.error(`[${fieldName}] Error fetching autocomplete suggestions:`, error);
                }
                if (suggestionsContainer) {
                    suggestionsContainer.classList.remove('active');
                    suggestionsContainer.innerHTML = '';
                }
            } finally {
                currentFetchController = null;
            }
        }, 300);

        function renderSuggestions(suggestions) {
            console.log(`Rendering ${suggestions.length} suggestions for ${fieldName}`);

            if (!suggestionsContainer) {
                console.error(`Suggestions container not found for ${fieldName}`);
                return;
            }

            suggestionsContainer.innerHTML = '';
            if (suggestions.length > 0) {
                suggestions.forEach((suggestion, index) => {
                    const suggestionItem = document.createElement('div');
                    suggestionItem.className = 'suggestion-item';
                    // suggestion이 객체 형태인 경우 (API response)와 문자열인 경우 모두 처리
                    const displayText = suggestion.name || suggestion;
                    suggestionItem.textContent = displayText;
                    suggestionItem.addEventListener('click', () => {
                        console.log(`Suggestion clicked: ${displayText}`);
                        addTag(displayText);
                        inputElement.value = '';
                        suggestionsContainer.classList.remove('active');
                    });
                    suggestionsContainer.appendChild(suggestionItem);
                });
                suggestionsContainer.classList.add('active');
                updateSuggestionsPosition();
                console.log(`Suggestions container made active for ${fieldName}`);
            } else {
                suggestionsContainer.classList.remove('active');
                console.log(`No suggestions to show for ${fieldName}`);
            }
        }

        if (inputElement) {
            console.log(`Adding event listeners to ${inputElementId}`);

            inputElement.addEventListener('input', (event) => {
                console.log(`Input event on ${inputElementId}: "${event.target.value}"`);
                fetchSuggestions(event.target.value);
            });

            inputElement.addEventListener('focus', () => {
                console.log(`Focus event on ${inputElementId}`);
                if (inputElement.value === '') {
                    fetchSuggestions('');
                }
            });

            inputElement.addEventListener('blur', () => {
                console.log(`Blur event on ${inputElementId}`);
                setTimeout(() => {
                    suggestionsContainer.classList.remove('active');
                }, 150);
            });
        }
        loadInitialTags();
    }
    
    console.log('Setting up autocomplete fields...');

    // 질병: 단일 선택
    console.log('Setting up disease autocomplete...');
    setupAutocomplete('disease_input', 'disease_suggestions', 'disease_tags', 'disease_hidden',
        (tagText) => updateDiseaseCodeField(tagText),
        (tagText) => updateDiseaseCodeField(tagText), false);

    // 직종: 단일 선택
    console.log('Setting up job autocomplete...');
    setupAutocomplete('job_input', 'job_suggestions', 'job_tags', 'job_hidden',
        (tagText) => updateJobCodeField(tagText),
        (tagText) => updateJobCodeField(tagText), false);

    // 추가 질병: 단일 선택
    console.log('Setting up additional disease autocomplete...');
    setupAutocomplete('additional_disease_input', 'additional_disease_suggestions', 'additional_disease_tags', 'additional_disease_hidden',
        null, null, false);

    // 유해인자: 다중 선택 (기본값)
    console.log('Setting up exposure autocomplete...');
    setupAutocomplete('exposure_input', 'exposure_suggestions', 'exposure_tags', 'exposure_hidden');

    // 초기 질병 코드 설정
    const diseaseHiddenInput = document.getElementById('disease_hidden');
    if (diseaseHiddenInput && diseaseHiddenInput.value) {
        const initialDiseaseName = diseaseHiddenInput.value.split(',').filter(v => v.trim() !== '')[0];
        if (initialDiseaseName) {
            updateDiseaseCodeField(initialDiseaseName);
        }
    }

    // 초기 직종 코드 설정
    const jobHiddenInput = document.getElementById('job_hidden');
    if (jobHiddenInput && jobHiddenInput.value) {
        const initialJobName = jobHiddenInput.value.split(',').filter(v => v.trim() !== '')[0];
        if (initialJobName) {
            updateJobCodeField(initialJobName);
        }
    }

    // 초기 추가 질병 코드 설정 (이미 current_data에서 가져온 값이 있으면 표시)
    const additionalDiseaseCodeDisplay = document.getElementById('additional_disease_code_display');
    const additionalDiseaseCodeHidden = document.getElementById('additional_disease_code_hidden_form');
    // 코드 필드는 이미 템플릿에서 current_data로 설정되어 있으므로 추가 처리 불필요

    // --- RAG 검색 기능 추가 (간소화) ---
    async function runRagSearch() {
        const query = document.getElementById('id_smry').value;
        if (!query) {
            alert("검색할 내용을 '요약' 필드에 입력해주세요.");
            return;
        }

        const resultsBody = document.querySelector('#rag-search-table tbody');
        if (!resultsBody) {
             console.error("RAG search table body not found.");
             return;
        }

        // 모달 팝업
        $('#ragSearchModal').modal('show');
        
        // 검색 중 메시지 표시
        resultsBody.innerHTML = `<tr><td colspan="4" class="text-center">검색 중... 잠시만 기다려 주세요.</td></tr>`;

        try {
            const response = await fetch(`${ragSearchApiUrl}?query=${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`HTTP 오류! 상태: ${response.status}`);
            }
            const data = await response.json();
            resultsBody.innerHTML = '';
            if (data.results && data.results.length > 0) {
                data.results.forEach(item => {
                    const row = document.createElement('tr');
                    const fullDescription = item.description || '';
                    row.innerHTML = `
                        <td>${item.score}%</td>
                        <td>[${item.code}]</td>
                        <td>${item.job_name}</td>
                        <td>${fullDescription}</td>
                    `;
                    row.addEventListener('click', function () {
                        document.getElementById('occupation_input').value = item.job_name;
                        document.getElementById('job_code_display').value = item.code;
                        document.getElementById('job_code_hidden_form').value = item.code;
                        updateJobCodeField(item.job_name);
                        $('#ragSearchModal').modal('hide');
                    });
                    resultsBody.appendChild(row);
                });
            } else {
                resultsBody.innerHTML = `<tr><td colspan="4" class="text-center">검색 결과가 없습니다.</td></tr>`;
            }
        } catch (error) {
            console.error('RAG 검색 중 오류 발생:', error);
            resultsBody.innerHTML = `<tr><td colspan="4" class="text-danger">검색 중 오류가 발생했습니다. (콘솔 확인)</td></tr>`;
        }
    }
    
    // 'RAG 검색' 버튼 이벤트 리스너
    const ragSearchBtn = document.getElementById('rag-search-button');
    if (ragSearchBtn) {
        ragSearchBtn.addEventListener('click', async function () {
            await runRagSearch();
        });
    }

    // 모달 내 검색 버튼 이벤트 리스너
    const ragSearchSubmitBtn = document.getElementById('rag-search-submit');
    if (ragSearchSubmitBtn) {
        ragSearchSubmitBtn.addEventListener('click', async function () {
            const query = document.getElementById('rag-search-query').value;
            if (!query) {
                alert("검색할 내용을 입력해주세요.");
                return;
            }
            await runRagSearch(query);
        });
    }
    // --- RAG 검색 기능 끝 ---

    // --- AI 검색 기능 시작 ---
    let currentAiSearchTarget = null;

    // AI 검색 버튼 이벤트 리스너
    document.addEventListener('click', function(e) {
        // SVG 내부를 클릭해도 버튼을 찾을 수 있도록 closest 사용
        const button = e.target.closest('.ai-search-btn');
        if (button) {
            const target = button.dataset.target;
            currentAiSearchTarget = target;

            console.log('AI 검색 버튼 클릭됨:', target); // 디버그 로그

            // 검색어 준비
            let searchQuery = '';
            if (target === 'disease') {
                // 질병: 고찰 내용 사용
                const smryField = document.getElementById('id_smry');
                searchQuery = smryField && smryField.value.trim() ? smryField.value.trim() : '';
            } else if (target === 'job') {
                // 직종: 현재 입력된 직종명 사용
                const jobInput = document.getElementById('job_input');
                searchQuery = jobInput && jobInput.value.trim() ? jobInput.value.trim() : '';
            }

            console.log('검색어:', searchQuery); // 디버그 로그

            // 팝업 창 열기
            let popupTitle = target === 'disease' ? 'D-ai: 질병 AI 검색' : 'J-ai: 직종 AI 검색';
            openAiSearchPopup(target, popupTitle, searchQuery);
        }
    });

    // 팝업 창 열기 함수
    function openAiSearchPopup(target, title, initialQuery) {
        // URL 매개변수를 간단하게 구성
        const params = new URLSearchParams({
            target: target,
            title: title,
            initial_query: initialQuery || ''
        });
        const popupUrl = `/epedit/ai-search-popup/?${params.toString()}`;
        // job 타겟은 작은 창, disease는 큰 창
        const windowSize = target === 'job' ? 'width=1000,height=800' : 'width=1400,height=900';
        const popup = window.open(
            popupUrl,
            'aiSearchPopup',
            `${windowSize},scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no`
        );

        // 팝업에서 결과 선택시 처리할 함수를 전역으로 등록
        window.handleAiSearchResult = function(result, searchTarget) {
            try {
                selectAiSearchResult(result, searchTarget);
                console.log('AI 검색 결과 적용 완료:', result);

                // 팝업 닫기
                if (popup && !popup.closed) {
                    popup.close();
                }
            } catch (error) {
                console.error('AI 검색 결과 처리 중 오류:', error);
            }
        };

        return popup;
    }


    // AI 검색 결과 선택 (팝업에서 호출됨)
    function selectAiSearchResult(result, searchTarget) {
        const target = searchTarget || currentAiSearchTarget;

        if (target === 'disease') {
            // 질병 필드에 결과 적용
            const diseaseName = result.disease_name || result.job_name || result.name || '';
            const diseaseCode = result.code || '';

            const diseaseInput = document.getElementById('disease_input');
            const diseaseHidden = document.getElementById('disease_hidden');
            const diseaseCodeDisplay = document.getElementById('disease_code_display');
            const diseaseCodeHidden = document.getElementById('disease_code_hidden_form');

            if (diseaseInput) diseaseInput.value = diseaseName;
            if (diseaseHidden) diseaseHidden.value = diseaseName;

            // 질병 코드 직접 설정 (AI 검색 결과의 코드 사용)
            if (diseaseCodeDisplay) diseaseCodeDisplay.value = diseaseCode;
            if (diseaseCodeHidden) diseaseCodeHidden.value = diseaseCode;

            // 질병 태그 추가
            const diseaseTagsContainer = document.getElementById('disease_tags');
            if (diseaseTagsContainer) {
                // 기존 태그 제거 (단일 선택)
                diseaseTagsContainer.innerHTML = '';
                // 새 태그 추가
                const tagItem = document.createElement('div');
                tagItem.className = 'tag-item';
                tagItem.innerHTML = `<span>${diseaseName}</span><span class="tag-close">X</span>`;
                tagItem.addEventListener('click', function() {
                    tagItem.remove();
                    if (diseaseInput) diseaseInput.value = '';
                    if (diseaseHidden) diseaseHidden.value = '';
                    if (diseaseCodeDisplay) diseaseCodeDisplay.value = '';
                    if (diseaseCodeHidden) diseaseCodeHidden.value = '';
                });
                diseaseTagsContainer.appendChild(tagItem);
            }

            // Dictionary에서 질병 코드도 함께 업데이트 (보조적으로)
            updateDiseaseCodeField(diseaseName);

        } else if (target === 'job') {
            // 직종 필드에 결과 적용
            const jobName = result.job_name || result.name || '';
            const jobCode = result.code || '';

            const jobInput = document.getElementById('job_input');
            const jobHidden = document.getElementById('job_hidden');
            const jobCodeDisplay = document.getElementById('job_code_display');
            const jobCodeHidden = document.getElementById('job_code_hidden_form');

            if (jobInput) jobInput.value = jobName;
            if (jobHidden) jobHidden.value = jobName;

            // 직종 코드 직접 설정 (AI 검색 결과의 코드 사용)
            if (jobCodeDisplay) {
                jobCodeDisplay.value = jobCode;
                console.log('Job code set to:', jobCode);
            }
            if (jobCodeHidden) {
                jobCodeHidden.value = jobCode;
            }

            // 직종 태그 추가
            const jobTagsContainer = document.getElementById('job_tags');
            if (jobTagsContainer) {
                // 기존 태그 제거 (단일 선택)
                jobTagsContainer.innerHTML = '';
                // 새 태그 추가
                const tagItem = document.createElement('div');
                tagItem.className = 'tag-item';
                tagItem.innerHTML = `<span>${jobName}</span><span class="tag-close">X</span>`;
                tagItem.addEventListener('click', function() {
                    tagItem.remove();
                    if (jobInput) jobInput.value = '';
                    if (jobHidden) jobHidden.value = '';
                    if (jobCodeDisplay) jobCodeDisplay.value = '';
                    if (jobCodeHidden) jobCodeHidden.value = '';
                });
                jobTagsContainer.appendChild(tagItem);
            }

            // AI 검색에서 코드가 없을 때만 Dictionary 조회
            if (!jobCode) {
                updateJobCodeField(jobName);
            }
        }
    }

    // --- AI 검색 기능 끝 ---
});