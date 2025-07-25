# Personal AI Career Co-Pilot v1.4

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Firebase](https://img.shields.io/badge/Firebase-hosting-orange.svg)](https://firebase.google.com/)
[![Genkit](https://img.shields.io/badge/Genkit-framework-green.svg)](https://firebase.google.com/docs/genkit)
[![Gemini](https://img.shields.io/badge/Gemini%202.5%20Pro-AI-purple.svg)](https://ai.google.dev/)

A serverless, Firebase-native Progressive Web Application (PWA) that automatically generates high-quality, tailored job application documents for Australian Community Services professionals using Google's Gemini 2.5 Pro AI model.

## 🚀 Features

### Core Functionality
- **Intelligent Document Generation**: Creates personalized resumes, cover letters, and Key Selection Criteria (KSC) responses
- **Job Ad Analysis**: Automatically scrapes and analyzes job advertisements from URLs
- **ATS Optimization**: Provides detailed Applicant Tracking System analysis and keyword matching
- **Multi-Theme Support**: 5 professional PDF themes optimized for different industries
- **Automated Job Scouting**: Background monitoring of Gmail for interview invitations with calendar integration

### Technical Highlights
- **Serverless Architecture**: Built with Google Cloud Functions and Firebase
- **AI-Powered**: Leverages Gemini 2.5 Pro for intelligent content generation
- **PWA Ready**: Installable Progressive Web App with offline capabilities
- **Real-time Processing**: Live document preview and generation
- **Responsive Design**: Clean, card-based UI optimized for desktop and mobile

## 🏗️ Architecture

### Tech Stack
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Backend**: Python 3.9+ with Genkit framework
- **Database**: Cloud Firestore
- **AI Model**: Google Gemini 2.5 Pro
- **Hosting**: Firebase Hosting
- **Functions**: Cloud Functions for Firebase
- **Automation**: Cloud Scheduler, GitHub Actions

### Project Structure
```
personal-ai-career-copilot/
├── README.md                           # Project documentation
├── .gitignore                         # Git ignore patterns
├── firebase.json                      # Firebase configuration
├── .firebaserc                       # Firebase project settings
├── package.json                      # Node.js dependencies for deployment
├── 
├── .github/
│   └── workflows/
│       └── deploy.yml                # GitHub Actions CI/CD workflow
├── 
├── functions/                        # Firebase Cloud Functions (Genkit backend)
│   ├── main.py                      # Primary Genkit flows and HTTP endpoints
│   ├── requirements.txt             # Python dependencies
│   ├── .env.example                # Environment variables template
│   ├── config.py                   # Configuration management
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── scraper.py              # Job ad scraping utilities
│   │   ├── firebase_client.py      # Firestore client wrapper
│   │   └── pdf_generator.py        # PDF generation using themes
│   ├── kb/                         # Knowledge Base directory
│   │   ├── pdf_themes_json.json
│   │   ├── australian_sector_glossary.md
│   │   ├── skill_taxonomy_community_services.md
│   │   ├── Gold-Standard-Knowledge-Artifact-1.md
│   │   └── action_verbs_community_services.md
│   └── tests/
│       ├── __init__.py
│       ├── test_flows.py
│       └── test_utils.py
├── 
├── public/                           # PWA Frontend (Firebase Hosting)
│   ├── index.html                   # Main application page
│   ├── manifest.json               # PWA manifest
│   ├── sw.js                       # Service worker for PWA
│   ├── favicon.ico
│   ├── icons/                      # PWA icons
│   │   ├── icon-192x192.png
│   │   ├── icon-512x512.png
│   │   └── apple-touch-icon.png
│   ├── css/

```

## 🎯 Target Audience

Designed specifically for professionals in the Australian Community Services sector, including:
- Housing Support Workers
- AOD (Alcohol and Other Drugs) Peer Support Workers
- Community Project Officers
- Social Workers
- Mental Health Support Workers
- Youth Services Coordinators

## 📋 Prerequisites

- Node.js 18+
- Python 3.9+
- Firebase CLI
- Google Cloud Project with billing enabled
- Gmail API credentials (for job scouting feature)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <repository-url>
cd personal-ai-career-copilot
npm install
pip install -r functions/requirements.txt
```

### 2. Firebase Configuration
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Initialize project
firebase init
```

### 3. Environment Setup
Create a `.env` file in the functions directory:
```env
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GEMINI_API_KEY=your_gemini_api_key
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
```

### 4. Deploy
```bash
# Deploy functions and hosting
firebase deploy

# Or use GitHub Actions for automated deployment
git push origin main
```

## 💼 Usage

### Initial Setup
1. Run the profile population script:
```bash
python scripts/populate_profile.py --resume-path /path/to/resume.pdf
```

### Generating Application Documents
1. Open the web application
2. Paste a job advertisement URL
3. Select a theme and tone of voice
4. Click "Generate" to create tailored documents
5. Preview, copy, or download as PDF

### Available Themes
- **Professional Classic**: Traditional industries, conservative fields
- **Modern Minimalist**: Tech, design, startups
- **Bold Executive**: Creative executives, dynamic industries
- **Contemporary Professional**: Healthcare, education, non-profits
- **Vibrant Creative**: Creative agencies, entertainment, digital media

## 🤖 AI Features

### Document Generation Flow
1. **Job Ad Scraping**: Extracts key information from job postings
2. **Profile Retrieval**: Loads user's structured career data
3. **Knowledge Base Integration**: Accesses sector-specific expertise
4. **AI Generation**: Uses Gemini 2.5 Pro for content creation
5. **ATS Analysis**: Provides keyword matching and optimization suggestions

### Knowledge Base
The system includes comprehensive Australian Community Services sector knowledge:
- Industry-specific terminology and acronyms
- Professional skill taxonomies
- Gold-standard resume and cover letter examples
- KSC response methodologies (STAR format)

## 📱 PWA Features

- **Installable**: Add to home screen on mobile/desktop
- **Offline Capable**: Service worker for offline functionality
- **Responsive Design**: Optimized for all screen sizes
- **Fast Loading**: Efficient caching strategies

## 🔒 Security & Privacy

- **Data Encryption**: All data transmitted over HTTPS
- **Firestore Security Rules**: Strict database access controls
- **API Key Management**: Secure credential storage
- **Privacy First**: No tracking, minimal data collection

## 🧪 Testing

```bash
# Run frontend tests
npm test

# Run Python tests
python -m pytest functions/tests/

# Integration tests
firebase emulators:start --only functions,firestore
```

## 📊 Monitoring

The application includes built-in monitoring through:
- Firebase Analytics
- Cloud Logging
- Error Reporting
- Performance Monitoring

## 🚀 Deployment

### Automated Deployment (Recommended)
Push to the `main` branch triggers automatic deployment via GitHub Actions.

### Manual Deployment
```bash
firebase deploy --only functions
firebase deploy --only hosting
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support, please:
1. Check the [documentation](docs/)
2. Search existing [issues](../../issues)
3. Create a new issue with detailed information

## 🙏 Acknowledgments

- **Google Genkit**: Framework for AI-powered applications
- **Firebase**: Serverless platform and hosting
- **Gemini 2.5 Pro**: Advanced AI language model
- **Australian Community Services Sector**: Domain expertise and knowledge base

---

**Note**: This application is specifically designed for the Australian Community Services sector and includes region-specific knowledge, terminology, and best practices.
