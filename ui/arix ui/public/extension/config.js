/**
 * Extension configuration.
 * Can be overridden via chrome.storage.local from the popup.
 */
const DEFAULT_CONFIG = {
  API_BASE_URL: 'https://arix-wiff.onrender.com', //live server
  // API_BASE_URL: 'http://127.0.0.1:8000', //for local testing
  POLL_INTERVAL_MS: 3000,
  STALE_THRESHOLD_MS: 10000,
  MAX_BACKOFF_MS: 30000,
  DEBOUNCE_MS: 500,
};

// Make available globally for content script
if (typeof window !== 'undefined') {
  window.__SIGNAL_CONFIG = DEFAULT_CONFIG;
}
