/**
 * API Communication Layer
 * Handles all communication with the Firebase Cloud Functions backend
 */

class CareerAPI {
    constructor() {
        // Firebase project configuration
        this.baseURL = window.location.hostname === 'localhost' 
            ? 'http://localhost:5001/personal-ai-career-copilot/us-central1'
            : 'https://us-central1-personal-ai-career-copilot.cloudfunctions.net';
        
        this.endpoints = {
            generateDocument: '/generate_application_http',
            documentHistory: '/get_document_history',
            healthCheck: '/health_check'
        };

        // Request configuration
        this.defaultHeaders = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        this.requestTimeout = 120000; // 2 minutes for document generation
    }

    /**
     * Generate a career document using the AI backend
     * @param {Object} requestData - Document generation parameters
     * @returns {Promise<Object>} API response with generated document
     */
    async generateDocument(requestData, file = null) {
        const url = `${this.baseURL}${this.endpoints.generateDocument}`;
        
        try {
            console.log('Generating document with data:', requestData);
            
            let body;
            const headers = { ...this.defaultHeaders };

            if (file) {
                const formData = new FormData();
                formData.append('requestData', JSON.stringify(requestData));
                formData.append('resume', file);
                body = formData;
                delete headers['Content-Type']; // Let the browser set the correct content type with boundary
            } else {
                body = JSON.stringify(requestData);
            }

            const response = await this.makeRequest('POST', url, body, {
                headers: headers,
                timeout: this.requestTimeout
            });

            if (response.generatedMarkdown && response.atsAnalysis) {
                return {
                    success: true,
                    data: response
                };
            } else {
                throw new Error('Invalid response format from server');
            }

        } catch (error) {
            console.error('Document generation failed:', error);
            return {
                success: false,
                error: this.getErrorMessage(error)
            };
        }
    }

    /**
     * Get user's document generation history
     * @returns {Promise<Object>} API response with document history
     */
    async getDocumentHistory() {
        const url = `${this.baseURL}${this.endpoints.documentHistory}`;
        
        try {
            const response = await this.makeRequest('GET', url);
            
            return {
                success: true,
                data: response.documents || []
            };

        } catch (error) {
            console.error('Failed to fetch document history:', error);
            return {
                success: false,
                error: this.getErrorMessage(error),
                data: []
            };
        }
    }

    /**
     * Check API health status
     * @returns {Promise<Object>} Health check response
     */
    async healthCheck() {
        const url = `${this.baseURL}${this.endpoints.healthCheck}`;
        
        try {
            const response = await this.makeRequest('GET', url, null, {
                timeout: 10000 // 10 seconds timeout for health check
            });
            
            return {
                success: true,
                data: response
            };

        } catch (error) {
            console.error('Health check failed:', error);
            return {
                success: false,
                error: this.getErrorMessage(error)
            };
        }
    }

    /**
     * Make HTTP request with error handling and retry logic
     * @param {string} method - HTTP method
     * @param {string} url - Request URL
     * @param {Object} data - Request body data
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    async makeRequest(method, url, data = null, options = {}) {
        const config = {
            method: method.toUpperCase(),
            headers: { ...this.defaultHeaders },
            ...options
        };

        // Add request body for POST/PUT requests
        if (data && ['POST', 'PUT', 'PATCH'].includes(config.method)) {
            if (data instanceof FormData) {
                config.body = data;
            } else {
                config.body = JSON.stringify(data);
            }
        }

        // Add timeout handling
        const controller = new AbortController();
        config.signal = controller.signal;

        const timeoutId = setTimeout(() => {
            controller.abort();
        }, options.timeout || 30000);

        try {
            const response = await fetch(url, config);
            clearTimeout(timeoutId);

            // Handle HTTP errors
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage;

                try {
                    const errorJson = JSON.parse(errorText);
                    errorMessage = errorJson.error || errorJson.message || `HTTP ${response.status}`;
                } catch {
                    errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                }

                throw new Error(errorMessage);
            }

            // Parse JSON response
            const responseData = await response.json();
            return responseData;

        } catch (error) {
            clearTimeout(timeoutId);

            if (error.name === 'AbortError') {
                throw new Error('Request timeout - please try again');
            }

            throw error;
        }
    }

    /**
     * Get user-friendly error message from error object
     * @param {Error} error - Error object
     * @returns {string} User-friendly error message
     */
    getErrorMessage(error) {
        if (error.message) {
            // Handle specific error types
            if (error.message.includes('timeout')) {
                return 'Request timed out. The server may be busy, please try again.';
            }
            
            if (error.message.includes('Failed to fetch')) {
                return 'Unable to connect to the server. Please check your internet connection.';
            }
            
            if (error.message.includes('HTTP 429')) {
                return 'Too many requests. Please wait a moment before trying again.';
            }
            
            if (error.message.includes('HTTP 500')) {
                return 'Server error. Please try again later.';
            }
            
            // Return the original error message if it's user-friendly
            return error.message;
        }

        return 'An unexpected error occurred. Please try again.';
    }

    /**
     * Upload resume file to the backend
     * @param {File} file - Resume file to upload
     * @returns {Promise<Object>} Upload response
     */
    async uploadResume(file) {
        const url = `${this.baseURL}/upload_resume`;
        
        try {
            const formData = new FormData();
            formData.append('resume', file);

            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                // Don't set Content-Type header, let browser set it with boundary
                headers: {
                    'Accept': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`Upload failed: HTTP ${response.status}`);
            }

            const result = await response.json();
            
            return {
                success: true,
                data: result
            };

        } catch (error) {
            console.error('Resume upload failed:', error);
            return {
                success: false,
                error: this.getErrorMessage(error)
            };
        }
    }

    /**
     * Test API connectivity
     * @returns {Promise<boolean>} Connection status
     */
    async testConnection() {
        try {
            const result = await this.healthCheck();
            return result.success;
        } catch {
            return false;
        }
    }

    /**
     * Get supported job sites for scraping
     * @returns {Array<string>} List of supported domains
     */
    getSupportedJobSites() {
        return [
            'seek.com.au',
            'ethicaljobs.com.au',
            'jora.com',
            'indeed.com.au',
            'linkedin.com'
        ];
    }

    /**
     * Validate if a URL is from a supported job site
     * @param {string} url - Job advertisement URL
     * @returns {boolean} Whether the URL is supported
     */
    isSupportedJobSite(url) {
        try {
            const domain = new URL(url).hostname.toLowerCase();
            const cleanDomain = domain.startsWith('www.') ? domain.slice(4) : domain;
            
            return this.getSupportedJobSites().some(site => 
                cleanDomain.includes(site)
            );
        } catch {
            return false;
        }
    }

    /**
     * Get job site name from URL
     * @param {string} url - Job advertisement URL
     * @returns {string} Job site name
     */
    getJobSiteName(url) {
        try {
            const domain = new URL(url).hostname.toLowerCase();
            
            if (domain.includes('seek.com.au')) return 'SEEK';
            if (domain.includes('ethicaljobs.com.au')) return 'Ethical Jobs';
            if (domain.includes('jora.com')) return 'Jora';
            if (domain.includes('indeed.com.au')) return 'Indeed Australia';
            if (domain.includes('linkedin.com')) return 'LinkedIn';
            
            return 'Unknown Site';
        } catch {
            return 'Invalid URL';
        }
    }
}

/**
 * API Response Status Helper
 */
class APIStatus {
    static isSuccess(response) {
        return response && response.success === true;
    }

    static isError(response) {
        return response && response.success === false;
    }

    static getErrorMessage(response) {
        if (this.isError(response)) {
            return response.error || 'Unknown error occurred';
        }
        return null;
    }

    static getData(response) {
        if (this.isSuccess(response)) {
            return response.data;
        }
        return null;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { CareerAPI, APIStatus };
}
