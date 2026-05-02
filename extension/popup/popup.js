/**
 * Popup script — manages settings for the Trading Signal Analyzer extension.
 */

document.addEventListener('DOMContentLoaded', () => {
  const apiUrlInput = document.getElementById('apiUrl');
  const btnSave = document.getElementById('btnSave');
  const btnTest = document.getElementById('btnTest');
  const statusMsg = document.getElementById('statusMsg');
  const mlToggle = document.getElementById('mlToggle');

  // Load saved settings
  chrome.storage.local.get(['apiConfig'], (result) => {
    if (result.apiConfig) {
      apiUrlInput.value = result.apiConfig.baseUrl || 'http://127.0.0.1:8000';
      mlToggle.checked = result.apiConfig.mlEnabled !== undefined ? result.apiConfig.mlEnabled : true;
    }
  });

  // Auto-save ML toggle
  mlToggle.addEventListener('change', () => {
    const baseUrl = apiUrlInput.value.trim().replace(/\/+$/, '') || 'http://127.0.0.1:8000';
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

  // Save settings
  btnSave.addEventListener('click', () => {
    const baseUrl = apiUrlInput.value.trim().replace(/\/+$/, '');
    if (!baseUrl) {
      showStatus('Please enter a valid URL', 'error');
      return;
    }

    chrome.storage.local.set({
      apiConfig: {
        baseUrl: baseUrl,
        mlEnabled: mlToggle.checked,
      },
    }, () => {
      showStatus('Settings saved! Reload qxbroker.com to apply.', 'success');

      // Notify content scripts in all tabs
      chrome.tabs.query({}, (tabs) => {
        tabs.forEach(tab => {
          chrome.tabs.sendMessage(tab.id, {
            type: 'CONFIG_UPDATED',
            config: { baseUrl, mlEnabled: mlToggle.checked },
          }).catch(() => { }); // Ignore tabs where script isn't loaded
        });
      });
    });
  });

  // Test connection
  btnTest.addEventListener('click', async () => {
    const baseUrl = apiUrlInput.value.trim().replace(/\/+$/, '');
    if (!baseUrl) {
      showStatus('Enter a URL first', 'error');
      return;
    }

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
      btnTest.textContent = 'Test';
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
