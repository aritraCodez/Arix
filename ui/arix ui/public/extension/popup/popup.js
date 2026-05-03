/**
 * Popup script — manages settings for the Trading Signal Analyzer extension.
 */

document.addEventListener('DOMContentLoaded', () => {
  const btnTest = document.getElementById('btnTest');
  const statusMsg = document.getElementById('statusMsg');
  const mlToggle = document.getElementById('mlToggle');
  // const baseUrl = 'http://127.0.0.1:8000';//local test
  const baseUrl = 'https://arix-wiff.onrender.com';//live server

  // Load saved settings
  chrome.storage.local.get(['apiConfig'], (result) => {
    if (result.apiConfig) {
      mlToggle.checked = result.apiConfig.mlEnabled !== undefined ? result.apiConfig.mlEnabled : true;
    }
  });

  // Auto-save ML toggle
  mlToggle.addEventListener('change', () => {
    chrome.storage.local.set({
      apiConfig: { baseUrl, mlEnabled: mlToggle.checked }
    }, () => {
      chrome.tabs.query({}, (tabs) => {
        tabs.forEach(tab => {
          chrome.tabs.sendMessage(tab.id, {
            type: 'CONFIG_UPDATED',
            config: { baseUrl, mlEnabled: mlToggle.checked }
          }).catch(() => { });
        });
      });
    });
  });

  // Test connection
  btnTest.addEventListener('click', async () => {
    btnTest.textContent = '...';
    btnTest.disabled = true;

    try {
      const resp = await fetch(`${baseUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000),
      });
      const data = await resp.json();

      if (data.status === 'healthy') {
        showStatus(`✓ Connected! ML: ${data.ml_enabled ? 'Enabled' : 'Disabled'}`, 'success');
      } else {
        showStatus('Server responded but status is not healthy', 'error');
      }
    } catch (err) {
      showStatus(`✗ Connection failed: ${err.message}`, 'error');
    } finally {
      btnTest.textContent = 'Test Connection';
      btnTest.disabled = false;
    }
  });

  function showStatus(msg, type) {
    statusMsg.textContent = msg;
    statusMsg.className = `status-message ${type}`;
    setTimeout(() => {
      statusMsg.className = 'status-message';
    }, 5000);
  }
});
