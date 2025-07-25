/**
 * @file app.js
 * @description Client-side JavaScript for the Personal AI Career Co-Pilot PWA.
 * @version 1.4
 * @author Perplexity Labs (as instructed by Nishant Jonas Dougall)
 *
 * This script handles all frontend interactivity, including:
 * - Theme (light/dark mode) management.
 * - Dynamic population of form dropdowns (Themes, Tones).
 * - File upload handling (drag-and-drop, click-to-browse).
 * - Form submission and validation.
 * - Simulating a call to the 'generateApplication' Genkit backend flow.
 * - Displaying a detailed loading overlay with progress updates.
 * - Rendering the generated application documents and ATS analysis.
 * - Handling result actions like copying text and downloading a PDF.
 * - Displaying toast notifications for user feedback.
 */

document.addEventListener('DOMContentLoaded', () => {

    // --- DOM Element References ---
    const themeToggle = document.getElementById('theme-toggle');
    const generationForm = document.getElementById('generation-form');
    const jobUrlInput = document.getElementById('job-url');
    const urlError = document.getElementById('url-error');
    const themeSelect = document.getElementById('theme-select');
    const themePreview = document.getElementById('theme-preview');
    const toneSelect = document.getElementById('tone-select');
    const fileUpload = document.getElementById('file-upload');
    const resumeFileInput = document.getElementById('resume-file');
    const uploadedFileContainer = document.getElementById('uploaded-file');
    const fileNameSpan = uploadedFileContainer.querySelector('.file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const generateBtn = document.getElementById('generate-btn');
    const generateBtnText = generateBtn.querySelector('.btn-text');
    const generateBtnSpinner = generateBtn.querySelector('.loading-spinner');
    const resultsSection = document.getElementById('results-section');
    const documentPreview = document.getElementById('document-preview');
    const copyBtn = document.getElementById('copy-btn');
    const downloadPdfBtn = document.getElementById('download-pdf-btn');
    const scoreCircle = document.getElementById('score-circle');
    const scoreNumber = document.getElementById('score-number');
    const analysisDetails = document.getElementById('analysis-details');
    const newGenerationBtn = document.getElementById('new-generation-btn');
    const refineBtn = document.getElementById('refine-btn');
    const toastContainer = document.getElementById('toast-container');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingStatus = document.getElementById('loading-status');
    const progressFill = document.getElementById('progress-fill');
    
    // --- State Management ---
    let resumeFile = null;
    let isLoading = false;

    // --- Data Definitions (from provided JSON/MD files) ---
    // In a real app, this might be fetched, but embedding is fine for this scope.
    const PDF_THEMES = {
        theme1: { name: "Professional Classic", bestFor: "Traditional industries, senior-level positions." },
        theme2: { name: "Modern Minimalist", bestFor: "Tech, design, startups, and creative agencies." },
        theme3: { name: "Bold Executive", bestFor: "Creative executives and innovative leaders." },
        theme4: { name: "Contemporary Professional", bestFor: "Healthcare, education, non-profits, government." },
        theme5: { name: "Vibrant Creative", bestFor: "Creative agencies, startups, and digital media." }
    };

    const TONES_OF_VOICE = [
        "Professional & Confident",
        "Empathetic & Collaborative",
        "Formal & Respectful",
        "Passionate & Driven",
        "Innovative & Strategic"
    ];

    /**
     * Initializes the application by setting up themes, event listeners, etc.
     */
    function init() {
        setupTheme();
        populateThemeSelect();
        populateToneSelect();
        setupEventListeners();
    }

    // --- Theme Management ---
    
    /**
     * Sets up the light/dark theme based on user preference or system settings.
     */
    function setupTheme() {
        const storedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

        const currentTheme = storedTheme || (systemPrefersDark ? 'dark' : 'light');
        applyTheme(currentTheme);

        themeToggle.addEventListener('click', () => {
            const newTheme = document.documentElement.dataset.colorScheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }

    /**
     * Applies a specific theme to the document.
     * @param {string} theme - The theme to apply ('light' or 'dark').
     */
    function applyTheme(theme) {
        document.documentElement.dataset.colorScheme = theme;
        themeToggle.querySelector('.theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
    }


    // --- Form Population ---

    /**
     * Populates the document theme dropdown from the PDF_THEMES object.
     */
    function populateThemeSelect() {
        Object.entries(PDF_THEMES).forEach(([id, theme]) => {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = theme.name;
            themeSelect.appendChild(option);
        });
    }

    /**
     * Populates the tone of voice dropdown.
     */
    function populateToneSelect() {
        TONES_OF_VOICE.forEach(tone => {
            const option = document.createElement('option');
            option.value = tone;
            option.textContent = tone;
            toneSelect.appendChild(option);
        });
    }

    // --- Event Listener Setup ---

    /**
     * Attaches all necessary event listeners for the application.
     */
    function setupEventListeners() {
        generationForm.addEventListener('submit', handleFormSubmit);
        themeSelect.addEventListener('change', updateThemePreview);

        // File Upload Listeners
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            fileUpload.addEventListener(eventName, preventDefaults, false);
        });
        ['dragenter', 'dragover'].forEach(eventName => {
            fileUpload.addEventListener(eventName, () => fileUpload.classList.add('dragover'), false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            fileUpload.addEventListener(eventName, () => fileUpload.classList.remove('dragover'), false);
        });
        fileUpload.addEventListener('drop', handleDrop, false);
        fileUpload.addEventListener('click', () => resumeFileInput.click());
        resumeFileInput.addEventListener('change', handleFileSelect);
        removeFileBtn.addEventListener('click', handleRemoveFile);

        // Results Action Buttons
        copyBtn.addEventListener('click', handleCopy);
        downloadPdfBtn.addEventListener('click', handleDownloadPdf);
        newGenerationBtn.addEventListener('click', resetUI);
        refineBtn.addEventListener('click', handleRefine);
    }
    
    // --- UI Update Functions ---
    
    /**
     * Updates the theme preview text when a theme is selected.
     */
    function updateThemePreview() {
        const selectedThemeId = themeSelect.value;
        if (selectedThemeId && PDF_THEMES[selectedThemeId]) {
            themePreview.textContent = `Best for: ${PDF_THEMES[selectedThemeId].bestFor}`;
            themePreview.classList.add('show');
        } else {
            themePreview.classList.remove('show');
        }
    }

    /**
     * Toggles the loading state of the generate button.
     * @param {boolean} showLoading - Whether to show the loading state.
     */
    function setButtonLoadingState(showLoading) {
        isLoading = showLoading;
        generateBtn.disabled = showLoading;
        generateBtnText.style.display = showLoading ? 'none' : 'inline';
        generateBtnSpinner.style.display = showLoading ? 'inline-flex' : 'none';
    }


    // --- File Handling ---

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    }

    /**
     * Processes a selected/dropped file.
     * @param {File} file - The file to handle.
     */
    function handleFileUpload(file) {
        const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
        if (file && allowedTypes.includes(file.type)) {
            resumeFile = file;
            fileNameSpan.textContent = file.name;
            fileUpload.style.display = 'none';
            uploadedFileContainer.style.display = 'flex';
        } else {
            showToast('Invalid file type. Please upload PDF, DOC, or DOCX.', 'error');
            handleRemoveFile();
        }
    }
    
    function handleRemoveFile() {
        resumeFile = null;
        resumeFileInput.value = ''; // Reset the input
        uploadedFileContainer.style.display = 'none';
        fileUpload.style.display = 'block';
    }
    
    
    // --- Form Submission and API Call ---
    
    /**
     * Handles the main form submission event.
     * @param {Event} e - The submit event.
     */
    async function handleFormSubmit(e) {
        e.preventDefault();
        if (isLoading) return;

        if (!validateForm()) return;

        setButtonLoadingState(true);
        showLoadingOverlay();

        const formData = {
            job_ad_url: jobUrlInput.value,
            theme_id: themeSelect.value,
            tone_of_voice: toneSelect.value
        };

        try {
            // This simulates the call to the Genkit 'generateApplication' flow
            const result = await simulateApiCall(formData);
            renderResults(result);
            resultsSection.style.display = 'block';
            resultsSection.scrollIntoView({ behavior: 'smooth' });
        } catch (error) {
            console.error('Generation failed:', error);
            showToast(error.message || 'An unexpected error occurred.', 'error');
        } finally {
            hideLoadingOverlay();
            setButtonLoadingState(false);
        }
    }
    
    /**
     * Validates the form inputs before submission.
     * @returns {boolean} - True if the form is valid, false otherwise.
     */
    function validateForm() {
        let isValid = true;
        urlError.classList.remove('show');

        try {
            new URL(jobUrlInput.value);
        } catch (_) {
            urlError.textContent = 'Please enter a valid URL.';
            urlError.classList.add('show');
            jobUrlInput.focus();
            isValid = false;
        }

        if (!jobUrlInput.value) {
            urlError.textContent = 'Job Advertisement URL is required.';
            urlError.classList.add('show');
            isValid = false;
        }
        
        return isValid;
    }
    
    /**
     * Simulates the complex backend process with progress updates.
     * @param {object} data - The form data sent to the backend.
     * @returns {Promise<object>} A promise that resolves with the generated data.
     */
    function simulateApiCall(data) {
        return new Promise((resolve, reject) => {
            const steps = [
                { status: 'Scraping job ad from URL...', duration: 2000, progress: 20 },
                { status: 'Retrieving user profile from Firestore...', duration: 1500, progress: 35 },
                { status: 'Loading Knowledge Base for context...', duration: 1500, progress: 50 },
                { status: 'Prompting Gemini 2.5 Pro to generate documents...', duration: 4000, progress: 85 },
                { status: 'Analyzing document for ATS compatibility...', duration: 2000, progress: 100 },
                { status: 'Finalizing results...', duration: 500, progress: 100 },
            ];

            let currentStep = 0;
            let totalTime = 0;

            function runStep() {
                if (currentStep < steps.length) {
                    const step = steps[currentStep];
                    updateLoadingProgress(step.status, step.progress);
                    totalTime += step.duration;
                    
                    setTimeout(() => {
                        currentStep++;
                        runStep();
                    }, step.duration);
                } else {
                     // Based on REQ-2.4 schema
                    const mockResponse = {
                        generatedMarkdown: `### Cover Letter for Housing Support Worker\n\n**Subject: Application for Housing Support Officer**\n\nDear Hiring Manager,\n\nI am writing with great enthusiasm to apply for the Housing Support Officer position at Metro Housing Alliance, as advertised on SEEK.com.au. My experience at City Outreach Mission, where I managed a complex caseload of over 15 clients, aligns perfectly with the requirements of this role. I have a proven ability to apply trauma-informed practices and conduct comprehensive risk assessments, which are critical skills I understand your organization values.\n\nI am particularly drawn to your commitment to assertive outreach. In my previous role, I successfully connected an average of 5 new clients per week to ongoing case management, demonstrating my resilience and practical ability to engage vulnerable individuals. I am confident I can contribute to your team's success in achieving sustainable housing outcomes for your clients.\n\nThank you for your time. I have attached my resume and look forward to discussing my application further.\n\nSincerely,\nNishant Jonas Dougall`,
                        atsAnalysis: {
                            keywordMatchPercent: 88,
                            matchedKeywords: ["Case Management", "Trauma-Informed", "Risk Assessment", "Advocacy", "Homelessness", "Client Support", "Stakeholder Engagement", "NDIS", "Mental Health", "AOD"],
                            missingKeywords: ["MARAM Framework", "CIMS", "Child Protection"],
                            suggestions: "Your document is a strong match. To improve further, consider explicitly mentioning experience with the MARAM framework if applicable, and name specific Client Information Management Systems (CIMS) you've used."
                        }
                    };
                    resolve(mockResponse);
                }
            }

            runStep();
        });
    }


    // --- Loading Overlay ---

    function showLoadingOverlay() {
        loadingOverlay.style.display = 'flex';
        updateLoadingProgress('Initializing generation...', 0);
    }

    function hideLoadingOverlay() {
        loadingOverlay.style.display = 'none';
    }
    
    function updateLoadingProgress(status, percent) {
        loadingStatus.textContent = status;
        progressFill.style.width = `${percent}%`;
    }

    // --- Results Rendering ---

    /**
     * Renders the results from the API into the UI.
     * @param {object} result - The result object from the API.
     */
    function renderResults(result) {
        // Render Markdown Preview
        documentPreview.textContent = result.generatedMarkdown;

        // Render ATS Analysis Score
        const score = result.atsAnalysis.keywordMatchPercent;
        scoreNumber.textContent = `${score}%`;
        const angle = (score / 100) * 360;
        scoreCircle.style.background = `conic-gradient(var(--color-primary) ${angle}deg, var(--color-bg-1) ${angle}deg 360deg)`;

        // Render ATS Details
        analysisDetails.innerHTML = ''; // Clear previous results

        const matchedSection = createKeywordSection('Matched Keywords', result.atsAnalysis.matchedKeywords, 'matched');
        const missingSection = createKeywordSection('Missing Keywords', result.atsAnalysis.missingKeywords, 'missing');
        
        const suggestionsSection = document.createElement('div');
        suggestionsSection.className = 'keyword-section';
        suggestionsSection.innerHTML = `
            <h4>Suggestions for Improvement</h4>
            <p class="suggestions">${result.atsAnalysis.suggestions}</p>
        `;

        analysisDetails.appendChild(matchedSection);
        analysisDetails.appendChild(missingSection);
        analysisDetails.appendChild(suggestionsSection);
    }
    
    /**
     * Helper to create a section of keyword tags.
     * @param {string} title - The title for the section.
     * @param {string[]} keywords - An array of keywords.
     * @param {string} type - 'matched' or 'missing'.
     * @returns {HTMLElement} The created DOM element for the section.
     */
    function createKeywordSection(title, keywords, type) {
        const section = document.createElement('div');
        section.className = 'keyword-section';
        
        const h4 = document.createElement('h4');
        h4.textContent = title;
        section.appendChild(h4);

        if (keywords.length > 0) {
            const list = document.createElement('div');
            list.className = 'keyword-list';
            keywords.forEach(kw => {
                const tag = document.createElement('span');
                tag.className = `keyword-tag ${type}`;
                tag.textContent = kw;
                list.appendChild(tag);
            });
            section.appendChild(list);
        } else {
            const p = document.createElement('p');
            p.className = 'suggestions';
            p.textContent = type === 'matched' ? 'No keywords matched.' : 'No missing keywords found. Great job!';
            section.appendChild(p);
        }

        return section;
    }


    // --- Results Actions ---

    /**
     * Handles copying the generated document text to the clipboard.
     */
    function handleCopy() {
        navigator.clipboard.writeText(documentPreview.textContent)
            .then(() => showToast('Copied to clipboard!', 'success'))
            .catch(err => showToast('Failed to copy text.', 'error'));
    }

    /**
     * Handles downloading the generated document as a PDF.
     * NOTE: Requires the jsPDF library to be included in index.html.
     */
    function handleDownloadPdf() {
        if (typeof jspdf === 'undefined') {
            showToast('PDF library not found. Cannot download.', 'error');
            console.error("jsPDF library is not loaded. Please include it in index.html.");
            return;
        }
        
        try {
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF();
            
            // This is a basic implementation. A full implementation would parse
            // the pdf_themes_json.json and apply complex styling (fonts, colors, layout),
            // which is a much larger task.
            const text = documentPreview.textContent;
            const splitText = doc.splitTextToSize(text, 180);
            
            doc.setFontSize(12);
            doc.text(splitText, 15, 20);
            
            doc.save('AI-Generated-Application.pdf');
            showToast('Downloading PDF...', 'success');
        } catch (error) {
            console.error("PDF Generation Error: ", error);
            showToast('Failed to generate PDF.', 'error');
        }
    }

    /**
     * Resets the entire UI to the initial state for a new generation.
     */
    function resetUI() {
        generationForm.reset();
        handleRemoveFile();
        updateThemePreview();
        urlError.classList.remove('show');
        resultsSection.style.display = 'none';
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }
    
    /**
     * Handles the "Refine" button click. Scrolls to the form without resetting.
     */
    function handleRefine() {
        showToast('Refine your inputs and generate again.', 'info');
        generationForm.scrollIntoView({ behavior: 'smooth' });
    }

    
    // --- Toast Notifications ---
    
    /**
     * Displays a toast notification.
     * @param {string} message - The message to display.
     * @param {string} type - 'success', 'error', or 'info'.
     */
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'fadeOut 0.5s forwards';
            setTimeout(() => toast.remove(), 500);
        }, 3000);
    }

    // --- Start the App ---
    init();

});