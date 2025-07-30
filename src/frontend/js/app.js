// Application data
const APP_DATA = {
  themes: [
    {
      id: "theme1",
      name: "Professional Classic",
      description: "Traditional industries, Senior-level positions, Conservative fields",
    },
    {
      id: "theme2",
      name: "Modern Minimalist",
      description: "Tech, Design, Startups, Creative agencies",
    },
    {
      id: "theme3",
      name: "Bold Executive",
      description: "Creative executives, Innovative leaders, Dynamic industries",
    },
    {
      id: "theme4",
      name: "Contemporary Professional",
      description: "Healthcare, Education, Non-profits, Government",
    },
    {
      id: "theme5",
      name: "Vibrant Creative",
      description: "Creative agencies, Startups, Entertainment, Digital media",
    }
  ],
  toneOptions: [
    "Professional",
    "Conversational",
    "Confident",
    "Collaborative",
    "Results-focused"
  ],
  // Data from pdf_themes_json.json, to be used for PDF generation
  pdfThemes: {
    "theme1": { "name": "Professional Classic", "typography": { "allDocuments": { "headings": { "font": "Times New Roman", "sizes": { "nameTitle": "16pt", "sectionHeadersQuestions": "14pt" }, "weight": "bold" }, "bodyText": { "font": "Times New Roman", "size": "11pt", "lineHeight": "1.4" } } } },
    "theme2": { "name": "Modern Minimalist", "typography": { "allDocuments": { "headings": { "font": "Helvetica, Arial, sans-serif", "sizes": { "nameTitle": "18pt", "sectionHeadersQuestions": "12pt" }, "weight": "bold", "case": "uppercase", "letterSpacing": "1px" }, "bodyText": { "font": "Helvetica, Arial, sans-serif", "size": "10pt", "lineHeight": "1.5" } } } },
    "theme3": { "name": "Bold Executive", "typography": { "allDocuments": { "headings": { "font": "Georgia, serif", "sizes": { "nameTitle": "22pt", "sectionHeadersQuestions": "16pt" }, "weight": "normal", "color": "#2563eb" }, "bodyText": { "font": "Georgia, serif", "size": "12pt", "lineHeight": "1.4" } } } },
    "theme4": { "name": "Contemporary Professional", "typography": { "allDocuments": { "headings": { "font": "Calibri, sans-serif", "sizes": { "nameTitle": "17pt", "sectionHeadersQuestions": "13pt" }, "weight": "600" }, "bodyText": { "font": "Calibri, sans-serif", "size": "11pt", "lineHeight": "1.4" } } } },
    "theme5": { "name": "Vibrant Creative", "typography": { "allDocuments": { "headings": { "font": "Futura, sans-serif", "sizes": { "nameTitle": "20pt", "sectionHeadersQuestions": "14pt" }, "weight": "bold", "color": "#10b981" }, "bodyText": { "font": "Futura, sans-serif", "size": "11pt", "lineHeight": "1.5" } } } }
  }
};

// Application state
let appState = {
  uploadedFile: null,
  isDarkMode: false,
  isGenerating: false,
  latestResult: null,
};

// Initialize application
document.addEventListener('DOMContentLoaded', () => {
  initializeApp();
  setupEventListeners();
  registerServiceWorker();
});

function initializeApp() {
  const savedTheme = localStorage.getItem('theme');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (savedTheme === 'dark' || (!savedTheme && prefersDark)) {
    enableDarkMode();
  }
  populateThemeOptions();
  populateToneOptions();
}

function setupEventListeners() {
  document.getElementById('theme-toggle')?.addEventListener('click', toggleTheme);
  document.getElementById('theme-select')?.addEventListener('change', handleThemeChange);
  const jobUrlInput = document.getElementById('job-url');
  if (jobUrlInput) {
    jobUrlInput.addEventListener('blur', validateJobUrl);
    jobUrlInput.addEventListener('input', clearUrlError);
  }
  const fileUpload = document.getElementById('file-upload');
  const resumeFileInput = document.getElementById('resume-file');
  if (fileUpload && resumeFileInput) {
    fileUpload.addEventListener('click', () => resumeFileInput.click());
    fileUpload.addEventListener('dragover', handleDragOver);
    fileUpload.addEventListener('dragleave', handleDragLeave);
    fileUpload.addEventListener('drop', handleFileDrop);
    resumeFileInput.addEventListener('change', handleFileSelect);
  }
  document.getElementById('remove-file')?.addEventListener('click', removeUploadedFile);
  document.getElementById('generation-form')?.addEventListener('submit', handleFormSubmission);
  document.getElementById('copy-btn')?.addEventListener('click', copyDocumentToClipboard);
  document.getElementById('download-pdf-btn')?.addEventListener('click', downloadAsPdf);
  document.getElementById('new-generation-btn')?.addEventListener('click', startNewGeneration);
  document.getElementById('refine-btn')?.addEventListener('click', refineResults);
}

function populateThemeOptions() {
  const themeSelect = document.getElementById('theme-select');
  if (!themeSelect) return;
  APP_DATA.themes.forEach(theme => {
    const option = document.createElement('option');
    option.value = theme.id;
    option.textContent = theme.name;
    themeSelect.appendChild(option);
  });
}

function populateToneOptions() {
  const toneSelect = document.getElementById('tone-select');
  if (!toneSelect) return;
  APP_DATA.toneOptions.forEach(tone => {
    const option = document.createElement('option');
    option.value = tone.toLowerCase().replace(/\s+/g, '-');
    option.textContent = tone;
    toneSelect.appendChild(option);
  });
}

function toggleTheme() { appState.isDarkMode ? disableDarkMode() : enableDarkMode(); }

function enableDarkMode() {
  document.documentElement.setAttribute('data-color-scheme', 'dark');
  const themeIcon = document.querySelector('.theme-icon');
  if (themeIcon) themeIcon.textContent = '☀️';
  appState.isDarkMode = true;
  localStorage.setItem('theme', 'dark');
}

function disableDarkMode() {
  document.documentElement.setAttribute('data-color-scheme', 'light');
  const themeIcon = document.querySelector('.theme-icon');
  if (themeIcon) themeIcon.textContent = '🌙';
  appState.isDarkMode = false;
  localStorage.setItem('theme', 'light');
}

function handleThemeChange(event) {
  const theme = APP_DATA.themes.find(t => t.id === event.target.value);
  if (theme) showThemePreview(theme);
  else hideThemePreview();
}

function showThemePreview(theme) {
  const themePreview = document.getElementById('theme-preview');
  if (themePreview) {
    themePreview.textContent = theme.description;
    themePreview.classList.add('show');
  }
}

function hideThemePreview() {
  document.getElementById('theme-preview')?.classList.remove('show');
}

function validateJobUrl() {
  const jobUrlInput = document.getElementById('job-url');
  if (!jobUrlInput) return true;
  const url = jobUrlInput.value.trim();
  if (url && !isValidUrl(url)) {
    showUrlError('Please enter a valid URL');
    return false;
  }
  clearUrlError();
  return true;
}

function isValidUrl(string) { try { new URL(string); return true; } catch (_) { return false; } }

function showUrlError(message) {
  const urlError = document.getElementById('url-error');
  if (urlError) {
    urlError.textContent = message;
    urlError.classList.add('show');
  }
  document.getElementById('job-url')?.style.setProperty('border-color', 'var(--color-error)');
}

function clearUrlError() {
  document.getElementById('url-error')?.classList.remove('show');
  document.getElementById('job-url')?.style.setProperty('border-color', '');
}

function handleDragOver(event) { event.preventDefault(); document.getElementById('file-upload')?.classList.add('dragover'); }
function handleDragLeave(event) { event.preventDefault(); document.getElementById('file-upload')?.classList.remove('dragover'); }
function handleFileDrop(event) {
  event.preventDefault();
  document.getElementById('file-upload')?.classList.remove('dragover');
  if (event.dataTransfer.files.length > 0) handleFileSelection(event.dataTransfer.files[0]);
}
function handleFileSelect(event) { if (event.target.files[0]) handleFileSelection(event.target.files[0]); }

function handleFileSelection(file) {
  const allowedTypes = ['.pdf', '.doc', '.docx'];
  if (!allowedTypes.includes('.' + file.name.split('.').pop().toLowerCase())) {
    showToast('Please select a PDF, DOC, or DOCX file', 'error');
    return;
  }
  if (file.size > 10 * 1024 * 1024) { showToast('File size must be less than 10MB', 'error'); return; }
  appState.uploadedFile = file;
  showUploadedFile(file);
}

function showUploadedFile(file) {
  const uploadedFileEl = document.getElementById('uploaded-file');
  if (uploadedFileEl) {
    uploadedFileEl.querySelector('.file-name').textContent = file.name;
    uploadedFileEl.style.display = 'flex';
  }
  document.getElementById('file-upload').style.display = 'none';
}

function removeUploadedFile() {
  appState.uploadedFile = null;
  document.getElementById('uploaded-file').style.display = 'none';
  document.getElementById('file-upload').style.display = 'block';
  document.getElementById('resume-file').value = '';
}

async function handleFormSubmission(event) {
  event.preventDefault();
  if (appState.isGenerating || !validateForm()) return;
  await startGeneration();
}

function validateForm() {
  const jobUrlInput = document.getElementById('job-url');
  if (!jobUrlInput.value.trim()) {
    showToast('Please enter a job advertisement URL', 'error');
    jobUrlInput.focus();
    return false;
  }
  return validateJobUrl();
}

async function startGeneration() {
  appState.isGenerating = true;
  showLoadingOverlay();
  setGenerateButtonLoading(true);
  const api = new CareerAPI();
  const requestData = {
      job_ad_url: document.getElementById('job-url').value,
      theme_id: document.getElementById('theme-select').value,
      tone_of_voice: document.getElementById('tone-select').value,
  };
  try {
    const response = await api.generateDocument(requestData, appState.uploadedFile);
    if (APIStatus.isSuccess(response)) {
      appState.latestResult = APIStatus.getData(response);
      displayResults();
      showToast('Application documents generated successfully!', 'success');
    } else {
      showToast(APIStatus.getErrorMessage(response), 'error');
    }
  } catch (error) {
    showToast('A critical error occurred. Please try again.', 'error');
  } finally {
    appState.isGenerating = false;
    hideLoadingOverlay();
    setGenerateButtonLoading(false);
  }
}

function setGenerateButtonLoading(isLoading) {
  const btn = document.getElementById('generate-btn');
  if (!btn) return;
  btn.disabled = isLoading;
  btn.querySelector('.btn-text').textContent = isLoading ? 'Generating...' : 'Generate Application Documents';
  btn.querySelector('.loading-spinner').style.display = isLoading ? 'inline-flex' : 'none';
}

function showLoadingOverlay() {
  document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoadingOverlay() {
  document.getElementById('loading-overlay').style.display = 'none';
}

function displayResults() {
  const { latestResult } = appState;
  if (!latestResult) return;
  document.getElementById('document-preview').textContent = latestResult.generatedMarkdown;
  displayAtsAnalysis(latestResult.atsAnalysis);
  const resultsSection = document.getElementById('results-section');
  resultsSection.style.display = 'block';
  resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function displayAtsAnalysis(analysis) {
  const percentage = Math.round(analysis.keywordMatchPercent);
  document.getElementById('score-number').textContent = `${percentage}%`;
  const degrees = (percentage / 100) * 360;
  document.getElementById('score-circle').style.background = `conic-gradient(var(--color-primary) ${degrees}deg, var(--color-bg-1) ${degrees}deg)`;
  document.getElementById('analysis-details').innerHTML = `
    <div class="keyword-section"><h4>Matched Keywords (${analysis.matchedKeywords.length})</h4><div class="keyword-list">${analysis.matchedKeywords.map(k => `<span class="keyword-tag matched">${k}</span>`).join('')}</div></div>
    <div class="keyword-section"><h4>Missing Keywords (${analysis.missingKeywords.length})</h4><div class="keyword-list">${analysis.missingKeywords.map(k => `<span class="keyword-tag missing">${k}</span>`).join('')}</div></div>
    <div class="keyword-section"><h4>Suggestions</h4><p class="suggestions">${analysis.suggestions}</p></div>`;
}

async function copyDocumentToClipboard() {
  if (!appState.latestResult?.generatedMarkdown) {
    showToast('No document to copy.', 'error');
    return;
  }
  await navigator.clipboard.writeText(appState.latestResult.generatedMarkdown);
  showToast('Document copied to clipboard!', 'success');
}

// CORE: Implements client-side PDF generation
async function downloadAsPdf() {
    if (!appState.latestResult) {
        showToast('Please generate a document first.', 'error');
        return;
    }
    showToast('Preparing PDF download...', 'info');

    const { jsPDF } = window.jspdf;
    const { marked } = window;
    const { html2canvas } = window;

    // Get theme and markdown
    const themeId = document.getElementById('theme-select').value || 'theme1';
    const theme = APP_DATA.pdfThemes[themeId];
    const markdown = appState.latestResult.generatedMarkdown;

    // Create a hidden element to render the styled HTML for capture
    const renderContainer = document.createElement('div');
    renderContainer.id = 'pdf-render-container';
    renderContainer.style.position = 'absolute';
    renderContainer.style.left = '-9999px';
    renderContainer.style.width = '210mm'; // A4 width
    renderContainer.style.padding = '20mm';
    renderContainer.style.background = 'white';
    renderContainer.style.color = 'black';
    renderContainer.innerHTML = marked.parse(markdown);
    document.body.appendChild(renderContainer);

    // Generate and apply theme styles
    const styleEl = document.createElement('style');
    const typography = theme.typography.allDocuments;
    styleEl.innerHTML = `
        #pdf-render-container { font-family: ${typography.bodyText.font}; font-size: ${typography.bodyText.size}; line-height: ${typography.bodyText.lineHeight}; }
        #pdf-render-container h1 { font-family: ${typography.headings.font}; font-size: ${typography.headings.sizes.nameTitle}; font-weight: ${typography.headings.weight}; color: ${typography.headings.color || 'black'}; }
        #pdf-render-container h2 { font-family: ${typography.headings.font}; font-size: ${typography.headings.sizes.sectionHeadersQuestions}; font-weight: ${typography.headings.weight}; color: ${typography.headings.color || 'black'}; margin-top: 1em; }
        #pdf-render-container h3, #pdf-render-container h4, #pdf-render-container p, #pdf-render-container ul { margin-bottom: 0.8em; }
    `;
    document.head.appendChild(styleEl);

    try {
        const canvas = await html2canvas(renderContainer, { scale: 2 });
        const imgData = canvas.toDataURL('image/png');

        const pdf = new jsPDF({
            orientation: 'portrait',
            unit: 'mm',
            format: 'a4'
        });

        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = pdf.internal.pageSize.getHeight();
        const canvasWidth = canvas.width;
        const canvasHeight = canvas.height;
        const ratio = canvasWidth / canvasHeight;
        const imgHeight = pdfWidth / ratio;

        pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, imgHeight);
        pdf.save('AI-Career-Co-Pilot-Document.pdf');
        showToast('PDF download started!', 'success');

    } catch (error) {
        console.error("PDF Generation Error: ", error);
        showToast('Sorry, there was an error creating the PDF.', 'error');
    } finally {
        // Clean up the temporary elements
        document.body.removeChild(renderContainer);
        document.head.removeChild(styleEl);
    }
}


function startNewGeneration() {
  document.getElementById('generation-form')?.reset();
  removeUploadedFile();
  hideThemePreview();
  clearUrlError();
  document.getElementById('results-section').style.display = 'none';
  appState.latestResult = null;
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function refineResults() { showToast('Refinement feature coming soon!', 'info'); }

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

async function registerServiceWorker() {
  if ('serviceWorker' in navigator) {
    try {
      await navigator.serviceWorker.register('/sw.js');
    } catch (error) {
      console.error('ServiceWorker registration failed:', error);
    }
  }
}

document.addEventListener('keydown', (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
    if (!appState.isGenerating && document.getElementById('job-url')?.value.trim()) {
      document.getElementById('generation-form')?.dispatchEvent(new Event('submit'));
    }
  }
});
