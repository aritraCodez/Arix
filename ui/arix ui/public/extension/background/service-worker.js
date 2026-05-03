/**
 * Background service worker for the Trading Signal Analyzer extension.
 * Manages extension lifecycle and message relay.
 */

// Handle installation
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get('apiConfig', (result) => {
    if (!result.apiConfig) {
      chrome.storage.local.set({
        apiConfig: {
          baseUrl: 'http://127.0.0.1:8000',
          mlEnabled: true,
        },
      });
    }
  });
});

// Message handler
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Relay config updates to all qxbroker tabs
  if (message.type === 'CONFIG_UPDATED') {
    chrome.tabs.query({ url: ['*://qxbroker.com/*', '*://*.qxbroker.com/*'] }, (tabs) => {
      for (const tab of tabs) {
        chrome.tabs.sendMessage(tab.id, message).catch(() => {});
      }
    });
    sendResponse({ success: true });
    return true;
  }

  // Proxy fetch requests to bypass CSP/Mixed Content
  if (message.type === 'FETCH_SIGNAL') {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout

    fetch(message.url, { signal: controller.signal })
      .then(async (resp) => {
        clearTimeout(timeoutId);
        const ok = resp.ok;
        const status = resp.status;
        const data = await resp.json().catch(() => ({}));
        sendResponse({ success: ok, status, data });
      })
      .catch((err) => {
        clearTimeout(timeoutId);
        sendResponse({ success: false, error: err.name === 'AbortError' ? 'Timeout' : err.message });
      });
    return true; // Keep channel open for async response
  }

  return true;
});
