/* records/static/records/js/form_scripts.js */

document.addEventListener('DOMContentLoaded', function () {
    const autocompleteUrl = DJANGO_URLS.autocompleteSuggestions;
    const getDiseaseCodeUrl = DJANGO_URLS.getDiseaseCodeByName;
    const getJobCodeUrl = DJANGO_URLS.getJobCodeByOccupationName;
    const ragSearchApiUrl = DJANGO_URLS.ragSearchApi; // 여기에서 변수를 한 번만 선언합니다.

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

    function setupAutocomplete(inputElementId, suggestionsContainerId, tagsContainerId, hiddenInputId, onTagAdded, onTagRemoved) {
        const inputElement = document.getElementById(inputElementId);
        if (!inputElement) return;

        const suggestionsContainer = document.getElementById(suggestionsContainerId);
        const tagsContainer = document.getElementById(tagsContainerId);
        const hiddenInput = document.getElementById(hiddenInputId);
        const fieldName = inputElement.dataset.fieldName;

        let selectedTags = new Set();
        let currentFetchController = null;

        function loadInitialTags() {
            if (hiddenInput.value) {
                const initialValues = hiddenInput.value.split(',').map(v => v.trim()).filter(v => v !== '');
                initialValues.forEach(tagText => {
                    addTag(tagText, false);
                });
            }
        }

        function addTag(tagText, updateHidden = true) {
            if (selectedTags.has(tagText)) return;
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
            if (currentFetchController) currentFetchController.abort();
            currentFetchController = new AbortController();
            const { signal } = currentFetchController;
            try {
                const response = await fetch(`${autocompleteUrl}?field_name=${fieldName}&q=${encodeURIComponent(query)}`, { signal });
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                renderSuggestions(data.suggestions);
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
            suggestionsContainer.innerHTML = '';
            if (suggestions.length > 0) {
                suggestions.forEach(suggestion => {
                    const suggestionItem = document.createElement('div');
                    suggestionItem.className = 'suggestion-item';
                    suggestionItem.textContent = suggestion;
                    suggestionItem.addEventListener('click', (event) => {
                        event.preventDefault();
                        addTag(suggestion);
                        inputElement.value = '';
                        suggestionsContainer.classList.remove('active');
                    });
                    suggestionsContainer.appendChild(suggestionItem);
                });
                suggestionsContainer.classList.add('active');
                updateSuggestionsPosition();
            } else {
                suggestionsContainer.classList.remove('active');
            }
        }

        if (inputElement) {
            inputElement.addEventListener('input', (event) => {
                fetchSuggestions(event.target.value);
            });
            inputElement.addEventListener('focus', (event) => {
                if (inputElement.value === '') {
                    fetchSuggestions('');
                }
            });
            inputElement.addEventListener('blur', () => {
                setTimeout(() => {
                    suggestionsContainer.classList.remove('active');
                }, 150);
            });
        }
        loadInitialTags();
    }
    
    setupAutocomplete('disease_name_input', 'disease_name_suggestions', 'disease_name_tags', 'disease_name_hidden',
        (tagText) => updateDiseaseCodeField(tagText),
        (tagText) => updateDiseaseCodeField(tagText));
    setupAutocomplete('occupation_input', 'occupation_suggestions', 'occupation_tags', 'occupation_hidden',
        (tagText) => updateJobCodeField(tagText),
        (tagText) => updateJobCodeField(tagText));

    const initialDiseaseName = document.getElementById('disease_name_hidden').value.split(',').filter(v => v.trim() !== '')[0];
    if (initialDiseaseName) {
        updateDiseaseCodeField(initialDiseaseName);
    }
    const initialOccupationName = document.getElementById('occupation_hidden').value.split(',').filter(v => v.trim() !== '')[0];
    if (initialOccupationName) {
        updateJobCodeField(initialOccupationName);
    }

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
});