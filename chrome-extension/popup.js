// Configuration
const API_BASE = 'http://127.0.0.1:5000';
const SUPPORTED_SITES = ['amazon.in', 'amazon.com', 'blinkit.com'];

// DOM Elements
let currentTab = null;
let analysisResult = null;

// Initialize popup when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
  await initializePopup();
  setupEventListeners();
});

// Initialize popup with current tab info
async function initializePopup() {
  try {
    // Get current active tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tabs[0];
    
    if (!currentTab) {
      showError('Unable to access current tab');
      return;
    }

    // Update UI with current page info
    updatePageInfo(currentTab);
    
    // Check if site is supported
    const isSupported = checkSiteSupport(currentTab.url);
    updateSupportStatus(isSupported);
    
  } catch (error) {
    console.error('Failed to initialize popup:', error);
    showError('Failed to initialize extension');
  }
}

// Setup event listeners
function setupEventListeners() {
  document.getElementById('analyze-btn').addEventListener('click', startAnalysis);
  document.getElementById('open-app-btn').addEventListener('click', openWebApp);
  document.getElementById('view-report-btn').addEventListener('click', viewFullReport);
  document.getElementById('analyze-another-btn').addEventListener('click', resetToInitial);
  document.getElementById('retry-btn').addEventListener('click', startAnalysis);
  document.getElementById('manual-entry-btn').addEventListener('click', openWebApp);
  document.getElementById('settings-link').addEventListener('click', openSettings);
  document.getElementById('help-link').addEventListener('click', openHelp);
}

// Update page information in UI
function updatePageInfo(tab) {
  const titleElement = document.getElementById('page-title');
  const urlElement = document.getElementById('page-url');
  
  titleElement.textContent = tab.title || 'Unknown Page';
  urlElement.textContent = formatUrl(tab.url);
}

// Check if current site is supported
function checkSiteSupported(url) {
  return SUPPORTED_SITES.some(site => url.includes(site));
}

// Update support status indicator
function updateSupportStatus(isSupported) {
  const indicator = document.getElementById('status-indicator');
  const analyzeBtn = document.getElementById('analyze-btn');
  
  if (isSupported) {
    indicator.className = 'status-indicator supported';
    indicator.innerHTML = '<i class="fas fa-check-circle"></i>';
    analyzeBtn.disabled = false;
  } else {
    indicator.className = 'status-indicator unsupported';
    indicator.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<i class="fas fa-ban"></i><span>Site Not Supported</span>';
  }
}

// Start compliance analysis
async function startAnalysis() {
  if (!currentTab || !checkSiteSupported(currentTab.url)) {
    showError('Current page is not supported');
    return;
  }

  showSection('loading-section');
  
  try {
    // Simulate progress steps
    updateLoadingStep('Extracting product data...', 'step-crawl', 'active');
    
    // Make API call to Flask backend
    const response = await fetch(`${API_BASE}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: currentTab.url,
        source: 'extension'
      })
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status}`);
    }

    updateLoadingStep('Reading product labels...', 'step-ocr', 'active');
    await new Promise(resolve => setTimeout(resolve, 1000));

    const result = await response.json();
    analysisResult = result;

    updateLoadingStep('Checking compliance...', 'step-validate', 'active');
    await new Promise(resolve => setTimeout(resolve, 1000));

    // Complete all steps
    completeStep('step-crawl');
    completeStep('step-ocr');
    completeStep('step-validate');

    await new Promise(resolve => setTimeout(resolve, 500));

    // Show results
    displayResults(result);

  } catch (error) {
    console.error('Analysis failed:', error);
    showError('Failed to analyze product. Please try again or use the web app.');
  }
}

// Update loading step
function updateLoadingStep(text, stepId, status) {
  document.getElementById('loading-step').textContent = text;
  
  const step = document.getElementById(stepId);
  if (step) {
    step.className = `progress-step ${status}`;
  }
}

// Complete a progress step
function completeStep(stepId) {
  const step = document.getElementById(stepId);
  if (step) {
    step.className = 'progress-step completed';
    const icon = step.querySelector('.step-icon i');
    if (icon) {
      icon.className = 'fas fa-check';
    }
  }
}

// Display analysis results
function displayResults(result) {
  showSection('results-section');
  
  // Update compliance score
  const score = result.compliance_summary?.compliance_score || '0/4';
  const scoreNum = parseInt(score.split('/')[0]);
  const maxScore = parseInt(score.split('/')[1]);
  const percentage = (scoreNum / maxScore) * 100;
  
  document.getElementById('score-text').textContent = score;
  document.getElementById('fields-found').textContent = scoreNum;
  document.getElementById('fields-missing').textContent = maxScore - scoreNum;
  
  // Update score styling
  const scoreCircle = document.getElementById('score-circle');
  const scoreLabel = document.getElementById('score-label');
  
  if (percentage >= 75) {
    scoreCircle.className = 'score-circle excellent';
    scoreLabel.textContent = 'Excellent Compliance';
  } else if (percentage >= 50) {
    scoreCircle.className = 'score-circle good';
    scoreLabel.textContent = 'Good Compliance';
  } else if (percentage >= 25) {
    scoreCircle.className = 'score-circle fair';
    scoreLabel.textContent = 'Fair Compliance';
  } else {
    scoreCircle.className = 'score-circle poor';
    scoreLabel.textContent = 'Poor Compliance';
  }
  
  // Display quick results
  displayQuickResults(result);
}

// Display quick results summary
function displayQuickResults(result) {
  const container = document.getElementById('quick-results');
  container.innerHTML = '';
  
  const fields = [
    { key: 'mrp', label: 'MRP', icon: 'fas fa-rupee-sign' },
    { key: 'quantity', label: 'Quantity', icon: 'fas fa-balance-scale' },
    { key: 'manufacturer', label: 'Manufacturer', icon: 'fas fa-industry' },
    { key: 'origin', label: 'Origin', icon: 'fas fa-globe' }
  ];
  
  fields.forEach(field => {
    const value = result[field.key];
    const item = document.createElement('div');
    item.className = 'result-item';
    
    const status = value && value !== 'Not Found' ? 'found' : 'missing';
    const statusIcon = status === 'found' ? 'fas fa-check-circle' : 'fas fa-times-circle';
    
    item.innerHTML = `
      <div class="result-icon">
        <i class="${field.icon}"></i>
      </div>
      <div class="result-content">
        <div class="result-label">${field.label}</div>
        <div class="result-value">${value || 'Not Found'}</div>
      </div>
      <div class="result-status ${status}">
        <i class="${statusIcon}"></i>
      </div>
    `;
    
    container.appendChild(item);
  });
}

// Show specific section
function showSection(sectionId) {
  const sections = document.querySelectorAll('.section');
  sections.forEach(section => section.classList.add('hidden'));
  
  const targetSection = document.getElementById(sectionId);
  if (targetSection) {
    targetSection.classList.remove('hidden');
  }
}

// Show error state
function showError(message) {
  document.getElementById('error-message').textContent = message;
  showSection('error-section');
}

// Reset to initial state
function resetToInitial() {
  analysisResult = null;
  showSection('initial-section');
}

// Open web application
function openWebApp() {
  chrome.tabs.create({ url: `${API_BASE}/process` });
}

// View full report
function viewFullReport() {
  if (analysisResult) {
    // Store result in chrome storage and open report page
    chrome.storage.local.set({ 'lastAnalysis': analysisResult }, () => {
      chrome.tabs.create({ url: `${API_BASE}/report` });
    });
  } else {
    openWebApp();
  }
}

// Open settings
function openSettings() {
  chrome.tabs.create({ url: `${API_BASE}/settings` });
}

// Open help
function openHelp() {
  chrome.tabs.create({ url: `${API_BASE}/help` });
}

// Utility functions
function formatUrl(url) {
  try {
    const urlObj = new URL(url);
    return urlObj.hostname + urlObj.pathname;
  } catch {
    return url;
  }
}

function checkSiteSupport(url) {
  if (!url) return false;
  return SUPPORTED_SITES.some(site => url.includes(site));
}

// Handle extension icon click
chrome.action?.onClicked?.addListener((tab) => {
  // This will open the popup automatically
  console.log('Extension clicked on tab:', tab.url);
});