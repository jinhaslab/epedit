// record_form.js - 모듈화된 폼 관리 시스템

class RecordFormManager {
  constructor(config) {
    this.config = config;
    this.init();
  }

  init() {
    console.log("Initializing RecordFormManager with config:", this.config);
    this.setupAutocomplete();
    this.setupInitialTags();
    this.setupFormEvents();
    this.setupRAGSearch();
    console.log("RecordFormManager initialization complete");
  }

  // === 유틸리티 함수들 ===
  debounce(func, delay) {
    let timeout;
    return function (...args) {
      const context = this;
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(context, args), delay);
    };
  }

  // === 질병 관련 함수들 ===
  async updateDiseaseCodeField(diseaseName) {
    const diseaseCodeDisplayInput = document.getElementById("disease_code_display");
    const diseaseCodeHiddenFormInput = document.getElementById("disease_code_hidden_form");

    if (!diseaseName) {
      if (diseaseCodeDisplayInput) diseaseCodeDisplayInput.value = "";
      if (diseaseCodeHiddenFormInput) diseaseCodeHiddenFormInput.value = "";
      return;
    }

    try {
      const response = await fetch(`${this.config.getDiseaseCodeUrl}?disease_name=${encodeURIComponent(diseaseName)}`);
      const data = await response.json();
      const diseaseCode = data.disease_code || "코드 없음";

      if (diseaseCodeDisplayInput) diseaseCodeDisplayInput.value = diseaseCode;
      if (diseaseCodeHiddenFormInput) diseaseCodeHiddenFormInput.value = diseaseCode;
    } catch (error) {
      console.error("질병 코드 조회 오류:", error);
      if (diseaseCodeDisplayInput) diseaseCodeDisplayInput.value = "조회 실패";
      if (diseaseCodeHiddenFormInput) diseaseCodeHiddenFormInput.value = "";
    }
  }

  // === 직종 관련 함수들 ===
  async updateJobCodeField(jobName) {
    const jobCodeDisplayInput = document.getElementById("job_code_display");
    const jobCodeHiddenFormInput = document.getElementById("job_code_hidden_form");

    if (!jobName) {
      if (jobCodeDisplayInput) jobCodeDisplayInput.value = "";
      if (jobCodeHiddenFormInput) jobCodeHiddenFormInput.value = "";
      return;
    }

    try {
      const response = await fetch(`${this.config.getJobCodeUrl}?occupation_name=${encodeURIComponent(jobName)}`);
      const data = await response.json();
      const jobCode = data.job_code || "코드 없음";

      if (jobCodeDisplayInput) jobCodeDisplayInput.value = jobCode;
      if (jobCodeHiddenFormInput) jobCodeHiddenFormInput.value = jobCode;
    } catch (error) {
      console.error("직종 코드 조회 오류:", error);
      if (jobCodeDisplayInput) jobCodeDisplayInput.value = "조회 실패";
      if (jobCodeHiddenFormInput) jobCodeHiddenFormInput.value = "";
    }
  }

  // === 태그 시스템 ===
  createTag(container, value, isError = false, onRemove = null) {
    const tagItem = document.createElement("div");
    tagItem.className = "tag-item";
    if (isError) {
      tagItem.classList.add("dictionary-error");
    }
    tagItem.dataset.value = value;

    const textSpan = document.createElement("span");
    textSpan.textContent = value;
    tagItem.appendChild(textSpan);

    const closeButton = document.createElement("span");
    closeButton.className = "tag-close";
    closeButton.textContent = "×";
    closeButton.addEventListener("click", () => {
      tagItem.remove();
      if (onRemove) onRemove(value);
    });
    tagItem.appendChild(closeButton);

    container.appendChild(tagItem);
    return tagItem;
  }

  addDiseaseTag(diseaseName) {
    const container = document.getElementById("disease_tags");
    const hiddenInput = document.getElementById("disease_hidden");

    if (!container || !hiddenInput) return;

    // 기존 태그 제거
    container.innerHTML = "";

    // 새 태그 추가
    const hasDiseaseFk = this.config.hasDiseaseFk;
    this.createTag(container, diseaseName, !hasDiseaseFk, () => {
      hiddenInput.value = "";
      this.updateDiseaseCodeField("");
    });

    // 사전 검증 오류 메시지
    if (!hasDiseaseFk) {
      const errorMsg = document.createElement("div");
      errorMsg.className = "dictionary-error-message";
      errorMsg.textContent = "사전에 없는 질병명입니다. 수정이 필요합니다.";
      container.appendChild(errorMsg);
    }

    hiddenInput.value = diseaseName;
    this.updateDiseaseCodeField(diseaseName);
  }

  addJobTag(jobName) {
    const container = document.getElementById("job_tags");
    const hiddenInput = document.getElementById("job_hidden");

    if (!container || !hiddenInput) return;

    // 기존 태그 제거
    container.innerHTML = "";

    // 새 태그 추가
    const hasJobFk = this.config.hasJobFk;
    this.createTag(container, jobName, !hasJobFk, () => {
      hiddenInput.value = "";
      this.updateJobCodeField("");
    });

    // 사전 검증 오류 메시지
    if (!hasJobFk) {
      const errorMsg = document.createElement("div");
      errorMsg.className = "dictionary-error-message";
      errorMsg.textContent = "사전에 없는 직종명입니다. 수정이 필요합니다.";
      container.appendChild(errorMsg);
    }

    hiddenInput.value = jobName;
    this.updateJobCodeField(jobName);
  }

  addExposureTag(exposureName) {
    const container = document.getElementById("exposure_tags");
    const hiddenInput = document.getElementById("exposure_hidden");

    if (!container || !hiddenInput) return;

    // 중복 확인
    const existingTags = container.querySelectorAll('.tag-item');
    for (let tag of existingTags) {
      if (tag.dataset.value === exposureName) {
        return; // 이미 존재하는 태그
      }
    }

    this.createTag(container, exposureName, false, (removedValue) => {
      this.updateExposureHiddenValue();
    });

    this.updateExposureHiddenValue();
  }

  updateExposureHiddenValue() {
    const container = document.getElementById("exposure_tags");
    const hiddenInput = document.getElementById("exposure_hidden");

    if (!container || !hiddenInput) return;

    const tags = container.querySelectorAll('.tag-item');
    const values = Array.from(tags).map(tag => tag.dataset.value);
    hiddenInput.value = values.join(',');
  }

  // === 자동완성 시스템 ===
  setupAutocomplete() {
    this.setupFieldAutocomplete(
      "disease_input",
      "disease_suggestions",
      "disease_name",
      (suggestion) => this.addDiseaseTag(suggestion.name)
    );

    this.setupFieldAutocomplete(
      "job_input",
      "job_suggestions",
      "job",
      (suggestion) => this.addJobTag(suggestion.name)
    );

    this.setupFieldAutocomplete(
      "exposure_input",
      "exposure_suggestions",
      "exposure",
      (suggestion) => {
        this.addExposureTag(suggestion.name);
        document.getElementById("exposure_input").value = "";
      }
    );
  }

  setupFieldAutocomplete(inputId, suggestionsId, fieldName, onSelect) {
    const inputElement = document.getElementById(inputId);
    const suggestionsContainer = document.getElementById(suggestionsId);

    if (!inputElement || !suggestionsContainer) {
      console.error(`Autocomplete elements not found: ${inputId}, ${suggestionsId}`);
      return;
    }

    console.log(`Setting up autocomplete for ${inputId} with field ${fieldName}`);

    const debouncedFetch = this.debounce(async (query) => {
      if (query.length < 1) {
        suggestionsContainer.classList.remove("active");
        return;
      }

      console.log(`Fetching suggestions for: ${query}`);

      try {
        const url = `${this.config.autocompleteUrl}?field=${fieldName}&q=${encodeURIComponent(query)}`;
        console.log(`Autocomplete URL: ${url}`);

        const response = await fetch(url);
        const data = await response.json();

        console.log("Autocomplete response:", data);
        this.displaySuggestions(suggestionsContainer, data.suggestions || [], onSelect);
      } catch (error) {
        console.error("자동완성 조회 오류:", error);
        suggestionsContainer.classList.remove("active");
      }
    }, 300);

    inputElement.addEventListener("input", (e) => {
      debouncedFetch(e.target.value.trim());
    });

    inputElement.addEventListener("blur", (e) => {
      // 약간의 지연을 두어 클릭 이벤트가 먼저 처리되도록 함
      setTimeout(() => {
        suggestionsContainer.classList.remove("active");
      }, 200);
    });
  }

  displaySuggestions(container, suggestions, onSelect) {
    console.log(`Displaying ${suggestions.length} suggestions`);
    container.innerHTML = "";

    if (suggestions.length > 0) {
      suggestions.forEach((suggestion) => {
        console.log("Adding suggestion:", suggestion);
        const suggestionItem = document.createElement("div");
        suggestionItem.className = "suggestion-item";
        suggestionItem.textContent = suggestion.name || suggestion;
        suggestionItem.addEventListener("click", (event) => {
          event.preventDefault();
          console.log("Suggestion clicked:", suggestion);
          onSelect(suggestion);
          container.classList.remove("active");
        });
        container.appendChild(suggestionItem);
      });
      container.classList.add("active");
      console.log("Suggestions container activated");
    } else {
      console.log("No suggestions to display");
      container.classList.remove("active");
    }
  }

  // === 초기 태그 설정 ===
  setupInitialTags() {
    // 질병 초기 설정
    const diseaseHidden = document.getElementById("disease_hidden");
    if (diseaseHidden && diseaseHidden.dataset.initialName) {
      const initialDiseaseName = diseaseHidden.dataset.initialName.trim();
      if (initialDiseaseName) {
        this.addDiseaseTag(initialDiseaseName);
      }
    }

    // 직종 초기 설정
    const jobHidden = document.getElementById("job_hidden");
    if (jobHidden && jobHidden.dataset.initialName) {
      const initialJobName = jobHidden.dataset.initialName.trim();
      if (initialJobName) {
        this.addJobTag(initialJobName);
      }
    }

    // 유해인자 초기 설정
    const exposureHidden = document.getElementById("exposure_hidden");
    if (exposureHidden && exposureHidden.dataset.initialExposure) {
      const initialExposure = exposureHidden.dataset.initialExposure.trim();
      if (initialExposure) {
        const exposureItems = initialExposure.split(',').map(item => item.trim()).filter(item => item);
        exposureItems.forEach(exposureName => {
          this.addExposureTag(exposureName);
        });
      }
    }
  }

  // === 폼 이벤트 설정 ===
  setupFormEvents() {
    // 엔터 키 처리
    document.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        const activeElement = document.activeElement;

        if (activeElement && activeElement.classList.contains("autocomplete-input")) {
          e.preventDefault();

          // 현재 활성화된 suggestion이 있으면 클릭
          const suggestionsContainer = activeElement.nextElementSibling;
          if (suggestionsContainer && suggestionsContainer.classList.contains("active")) {
            const firstSuggestion = suggestionsContainer.querySelector(".suggestion-item");
            if (firstSuggestion) {
              firstSuggestion.click();
            }
          }
        }
      }
    });
  }

  // === RAG 검색 기능 ===
  setupRAGSearch() {
    const ragSearchButton = document.getElementById("rag-search-button");
    const runSearchButton = document.getElementById("run-rag-search");

    if (runSearchButton) {
      runSearchButton.addEventListener("click", () => {
        const query = document.getElementById("rag-search-query").value;
        if (query) {
          this.runRagSearch(query);
        } else {
          this.showRagMessage("검색어를 입력해주세요.", true);
        }
      });
    }
  }

  async runRagSearch(query) {
    const resultsContainer = document.getElementById("rag-results");
    const messageContainer = document.getElementById("rag-message");

    this.showRagMessage("검색 중...", false);

    try {
      const response = await fetch(this.config.ragSearchApiUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value,
        },
        body: JSON.stringify({ query: query }),
      });

      const data = await response.json();

      if (data.success && data.results && data.results.length > 0) {
        this.displayRagResults(data.results);
        messageContainer.style.display = "none";
      } else {
        this.showRagMessage("검색 결과가 없습니다.", true);
      }
    } catch (error) {
      console.error("RAG 검색 오류:", error);
      this.showRagMessage("검색 중 오류가 발생했습니다.", true);
    }
  }

  displayRagResults(results) {
    const resultsContainer = document.getElementById("rag-results");
    resultsContainer.innerHTML = "";

    results.forEach((item, index) => {
      const resultDiv = document.createElement("div");
      resultDiv.className = "rag-result-item";
      resultDiv.innerHTML = `
        <h6>검색 결과 ${index + 1}</h6>
        <p><strong>직종명:</strong> ${item.job_name || "정보 없음"}</p>
        <p><strong>직종 코드:</strong> ${item.job_code || "정보 없음"}</p>
        <button type="button" class="btn btn-sm btn-primary" onclick="recordFormManager.applyRagResult('${item.job_name}', '${item.job_code}')">
          적용하기
        </button>
      `;
      resultsContainer.appendChild(resultDiv);
    });

    resultsContainer.style.display = "block";
  }

  applyRagResult(jobName, jobCode) {
    if (jobName) {
      this.addJobTag(jobName);
    }

    // 모달 닫기
    $("#ragSearchModal").modal("hide");
  }

  showRagMessage(message, isError = false) {
    const messageContainer = document.getElementById("rag-message");
    messageContainer.textContent = message;
    messageContainer.className = isError ? "alert alert-warning" : "alert alert-info";
    messageContainer.style.display = "block";

    document.getElementById("rag-results").style.display = "none";
  }
}

// 전역 변수로 내보내기
let recordFormManager;

// DOM이 로드되면 초기화
document.addEventListener("DOMContentLoaded", function () {
  const config = window.RECORD_FORM_CONFIG || {};
  recordFormManager = new RecordFormManager(config);
});