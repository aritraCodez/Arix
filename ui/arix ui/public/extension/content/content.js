(function () {
  'use strict';

  // --- Configuration ---
  const CONFIG = {
    // API_BASE_URL: 'http://127.0.0.1:8000', //local test
    API_BASE_URL: 'https://arix-wiff.onrender.com',//live server
    POLL_INTERVAL: 1000,
  };

  const ASSETS = {
    crypto: [
      { symbol: 'BTCUSDT', name: 'Bitcoin' }, { symbol: 'ETHUSDT', name: 'Ethereum' },
      { symbol: 'BNBUSDT', name: 'Binance' }, { symbol: 'SOLUSDT', name: 'Solana' },
      { symbol: 'LTCUSDT', name: 'Litecoin' }, { symbol: 'XRPUSDT', name: 'Ripple' }
    ],
    forex: [
      { symbol: 'EURUSD', name: 'EUR/USD' }, { symbol: 'GBPUSD', name: 'GBP/USD' },
      { symbol: 'USDJPY', name: 'USD/JPY' }, { symbol: 'AUDUSD', name: 'AUD/USD' },
      { symbol: 'USDCAD', name: 'USD/CAD' }, { symbol: 'EURJPY', name: 'EUR/JPY' },
      { symbol: 'GBPJPY', name: 'GBP/JPY' }, { symbol: 'CADJPY', name: 'CAD/JPY' },
      { symbol: 'GBPCHF', name: 'GBP/CHF' }, { symbol: 'AUDCAD', name: 'AUD/CAD' },
      { symbol: 'EURAUD', name: 'EUR/AUD' }, { symbol: 'CHFJPY', name: 'CHF/JPY' },
      { symbol: 'NZDUSD', name: 'NZD/USD' }, { symbol: 'EURGBP', name: 'EUR/GBP' },
      { symbol: 'GBPNZD', name: 'GBP/NZD' }, { symbol: 'AUDNZD', name: 'AUD/NZD' },
      { symbol: 'EURNZD', name: 'EUR/NZD' }, { symbol: 'GBPCAD', name: 'GBP/CAD' },
      { symbol: 'EURNZD', name: 'EUR/NZD' }, { symbol: 'AUDJPY', name: 'AUD/JPY' }
    ],
    commodity: [
      { symbol: 'GOLD', name: 'Gold' }, { symbol: 'SILVER', name: 'Silver' },
      { symbol: 'OIL', name: 'Crude Oil' }, { symbol: 'UKBRENT', name: 'Brent Oil' },
      { symbol: 'XAUUSD', name: 'Gold' }, { symbol: 'NATGAS', name: 'Natural Gas' }
    ],
    stock: [
      { symbol: 'FACEBOOK', name: 'Facebook' }, { symbol: 'META', name: 'Meta' },
      { symbol: 'APPLE', name: 'Apple' }, { symbol: 'GOOGLE', name: 'Google' },
      { symbol: 'AMAZON', name: 'Amazon' }, { symbol: 'NETFLIX', name: 'Netflix' },
      { symbol: 'TESLA', name: 'Tesla' }, { symbol: 'MICROSOFT', name: 'Microsoft' }
    ]
  };

  // --- Styles (Embedded for reliability) ---
  const STYLES = `
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    :host { all: initial; font-family: 'Inter', sans-serif; }
    .signal-panel { position: fixed; top: 20px; right: 80px; z-index: 2147483647; display: flex; align-items: flex-start; gap: 16px; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
    .signal-orb { position: relative; width: 72px; height: 72px; background: #fff; border: 1px solid #eee; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); cursor: grab; display: flex; flex-direction: column; align-items: center; justify-content: center; user-select: none; flex-shrink: 0; }
    .orb-ml-tag { position: absolute; top: 6px; left: 6px; font-size: 6px; font-weight: 900; padding: 1px 3px; border-radius: 3px; background: #f0f0f0; color: #aaa; transition: all 0.3s; line-height: 1; }
    .orb-ml-tag.active { background: #2ecc71; color: #fff; }
    .signal-orb.up { border-bottom: 4px solid #2ecc71; }
    .signal-orb.down { border-bottom: 4px solid #e74c3c; }
    .orb-asset { font-size: 10px; font-weight: 700; color: #666; margin-bottom: 2px; }
    .orb-stats { font-size: 14px; font-weight: 800; color: #222; }
    .orb-arrow { font-size: 18px; margin: -2px 0; }
    .details-card { width: 260px; background: #fff; border: 1px solid #eee; border-radius: 24px; padding: 20px; box-shadow: 0 15px 40px rgba(0,0,0,0.1); opacity: 0; transform: translateX(20px); pointer-events: none; transition: all 0.3s ease; }
    .signal-panel.expanded .details-card { opacity: 1; transform: translateX(0); pointer-events: all; }
    .details-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
    #detailsTitle { font-size: 12px; font-weight: 800; color: #333; }
    .prediction-row { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 15px; }
    .pred-box { flex: 1; padding: 10px; border-radius: 12px; text-align: center; background: #f8f9fa; }
    .pred-box.up { border-left: 4px solid #2ecc71; color: #2ecc71; }
    .pred-box.down { border-left: 4px solid #e74c3c; color: #e74c3c; }
    .pred-label { font-size: 9px; font-weight: 800; margin-bottom: 4px; color: #666; }
    .pred-val { font-size: 16px; font-weight: 800; }
    .stats-grid { display: flex; flex-direction: column; gap: 8px; border-top: 1px solid #f0f0f0; padding-top: 10px; }
    .stat-item { display: flex; justify-content: space-between; font-size: 11px; }
    .stat-item label { color: #666; font-weight: 600; }
    .stat-item span { color: #333; font-weight: 700; }
  `;

  // --- Setup ---
  let state = {
    selectedAsset: null,
    selectedType: null,
    signal: null,
    loading: true,
    mlEnabled: true,
    baseUrl: CONFIG.API_BASE_URL
  };

  // Sync settings
  function syncSettings() {
    chrome.storage.local.get(['apiConfig'], (res) => {
      if (res.apiConfig) {
        state.baseUrl = res.apiConfig.baseUrl || CONFIG.API_BASE_URL;
        state.mlEnabled = res.apiConfig.mlEnabled !== undefined ? res.apiConfig.mlEnabled : true;
      }
    });
  }
  syncSettings();

  // Listen for updates
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === 'CONFIG_UPDATED') {
      state.baseUrl = msg.config.baseUrl;
      state.mlEnabled = msg.config.mlEnabled;
      fetchSignal(); // Immediate refresh on save
    }
  });
  const container = document.createElement('div');
  const shadow = container.attachShadow({ mode: 'closed' });
  const styleTag = document.createElement('style');
  styleTag.textContent = STYLES;
  shadow.appendChild(styleTag);
  document.body.appendChild(container);

  const panel = document.createElement('div');
  panel.className = 'signal-panel';
  panel.innerHTML = `
    <div class="signal-orb" id="signalOrb">
      <div class="orb-ml-tag" id="orbMlTag">ML</div>
      <div class="orb-asset" id="orbAsset">...</div>
      <div class="orb-stats" id="orbStats">--%</div>
      <div class="orb-arrow" id="orbArrow">—</div>
    </div>
    <div class="details-card" id="detailsCard">
      <div class="details-header">
        <span id="detailsTitle">DETAILED PREDICTION</span>
      </div>
      <div class="prediction-row">
        <div class="pred-box up">
          <div class="pred-label">BULLISH (UP)</div>
          <div class="pred-val" id="predUpVal">0%</div>
        </div>
        <div class="pred-box down">
          <div class="pred-label">BEARISH (DOWN)</div>
          <div class="pred-val" id="predDownVal">0%</div>
        </div>
      </div>
      <div class="stats-grid">
        <div class="stat-item"><label>RSI (14)</label><span id="statRsi">—</span></div>
        <div class="stat-item"><label>MACD</label><span id="statMacd">—</span></div>
        <div class="stat-item"><label>EMA (Trend)</label><span id="statEma">—</span></div>
        <div class="stat-item"><label>Latency</label><span id="statLatency">0ms</span></div>
      </div>
    </div>
  `;
  shadow.appendChild(panel);

  const $ = (s) => shadow.querySelector(s);
  const el = {
    panel, signalOrb: $('#signalOrb'), orbAsset: $('#orbAsset'), orbStats: $('#orbStats'),
    orbArrow: $('#orbArrow'), orbMlTag: $('#orbMlTag'), predUpVal: $('#predUpVal'), predDownVal: $('#predDownVal'),
    statRsi: $('#statRsi'), statMacd: $('#statMacd'), statEma: $('#statEma'),
    statLatency: $('#statLatency'), detailsTime: $('#detailsTime')
  };

  // --- Interaction ---
  let isDragging = false, clickStart = 0, dragStartX, dragStartY, panelStartX, panelStartY;
  el.signalOrb.addEventListener('mousedown', (e) => {
    isDragging = false; clickStart = Date.now();
    dragStartX = e.clientX; dragStartY = e.clientY;
    const r = panel.getBoundingClientRect();
    panelStartX = r.left; panelStartY = r.top;
    panel.style.transition = 'none';
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  });
  el.signalOrb.addEventListener('click', () => {
    if (!isDragging && Date.now() - clickStart < 200) panel.classList.toggle('expanded');
  });
  function onMouseMove(e) {
    const dx = e.clientX - dragStartX, dy = e.clientY - dragStartY;
    if (Math.abs(dx) > 5 || Math.abs(dy) > 5) isDragging = true;
    if (isDragging) { panel.style.left = (panelStartX + dx) + 'px'; panel.style.top = (panelStartY + dy) + 'px'; panel.style.right = 'auto'; }
  }
  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove); document.removeEventListener('mouseup', onMouseUp);
    panel.style.transition = 'all 0.4s ease';
    if (isDragging) chrome.storage.local.set({ pos: { l: panel.style.left, t: panel.style.top } });
  }

  // --- Data ---
  let pollTimer = null;
  let isFetching = false;

  async function fetchSignal() {
    if (isFetching) return; // Only one request at a time
    if (pollTimer) clearTimeout(pollTimer);

    if (!state.selectedAsset) {
      pollTimer = setTimeout(fetchSignal, 500);
      return;
    }

    isFetching = true;
    const start = performance.now();
    const url = `${state.baseUrl}/signal?symbol=${state.selectedAsset}&type=${state.selectedType}&risk=medium&use_ml=${state.mlEnabled}&_t=${Date.now()}`;

    chrome.runtime.sendMessage({ type: 'FETCH_SIGNAL', url }, (res) => {
      isFetching = false;
      const latency = performance.now() - start;

      let nextPoll = 500;

      if (res && res.status === 429) {
        nextPoll = 2000;
        if (state.signal) state.signal.latency_msg = "RATE LIMITED - SLOWING DOWN";
        render();
      } else if (res && res.status === 422) {
        // INSUFFICIENT DATA
        state.signal = { confidence: NaN, latency_msg: "NO CHART DATA (TOO FEW CANDLES)" };
        render();
      } else if (res && res.data) {
        state.signal = res.data;
        state.signal.latency = latency;
        state.signal.latency_msg = null;
        render();
      } else if (res && res.error) {
        // OTHER ERROR
        state.signal = { confidence: NaN, latency_msg: "SERVER ERROR" };
        render();
      }

      pollTimer = setTimeout(fetchSignal, nextPoll);
    });
  }

  function render() {
    const d = state.signal;
    // Handle NaN or missing data
    if (!d || isNaN(d.confidence)) {
      el.orbStats.textContent = 'OFFLINE';
      el.orbArrow.textContent = '—';
      el.orbStats.style.fontSize = '10px';
      el.orbStats.style.color = '#999';
    } else {
      el.orbStats.textContent = `${Math.round(d.confidence)}%`;
      el.orbStats.style.fontSize = '14px';
      el.orbStats.style.color = '#222';

      // Use "leaning" for direction — it always shows UP/DOWN even on NO_TRADE
      const direction = d.leaning || d.signal;
      el.orbArrow.textContent = direction === 'UP' ? '↑' : (direction === 'DOWN' ? '↓' : '—');
    }

    el.orbAsset.textContent = (state.selectedAsset || '...').replace('USDT', '');

    // Use leaning for orb color so it always reflects the dominant direction
    const orbDirection = d && (d.leaning || d.signal);
    el.signalOrb.className = `signal-orb ${orbDirection ? orbDirection.toLowerCase() : ''}`;

    // Update ML tag status
    if (state.mlEnabled) {
      el.orbMlTag.classList.add('active');
      el.orbMlTag.title = "Machine Learning Active";
    } else {
      el.orbMlTag.classList.remove('active');
      el.orbMlTag.title = "Machine Learning Disabled";
    }

    // Detailed rows
    if (d && !isNaN(d.up_percent)) {
      el.predUpVal.textContent = `${d.up_percent}%`;
      el.predDownVal.textContent = `${d.down_percent}%`;
      el.statRsi.textContent = d.indicators.rsi.value.toFixed(1);
      el.statMacd.textContent = d.indicators.macd.value.toFixed(4);

      let emaTrend = 'NEUTRAL';
      if (d.indicators.ema_trend.value > 0) emaTrend = 'UP ↑';
      else if (d.indicators.ema_trend.value < 0) emaTrend = 'DOWN ↓';
      el.statEma.textContent = emaTrend;
    } else {
      el.predUpVal.textContent = '0%';
      el.predDownVal.textContent = '0%';
      el.statRsi.textContent = '--';
      el.statMacd.textContent = '--';
      el.statEma.textContent = 'WAITING';
    }

    // Latency / Status
    if (d && d.latency_msg) {
      el.statLatency.textContent = d.latency_msg;
      el.statLatency.style.color = '#f1c40f'; // Yellow
    } else if (!d || isNaN(d.confidence)) {
      el.statLatency.textContent = 'MARKET OFFLINE';
      el.statLatency.style.color = '#e74c3c'; // Red
    } else {
      const net = d.latency.toFixed(1);
      const srv = d.execution_time || 0;
      el.statLatency.textContent = `${srv}ms / ${net}ms`;
      el.statLatency.style.color = d.latency < 500 ? '#2ecc71' : '#f1c40f';
    }

  }

  // Known crypto base tickers (matches backend's BINANCE_SYMBOLS without the USDT suffix)
  const CRYPTO_BASES = new Set([
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'DOGE', 'ADA', 'AVAX',
    'DOT', 'MATIC', 'LINK', 'LTC', 'SHIB', 'TRX', 'ATOM'
  ]);

  // Quotex displays FULL NAMES on tabs (e.g. "Bitcoin", "Ethereum", "Facebook").
  // This map converts those names to the correct API symbol + type.
  const NAME_TO_SYMBOL = {
    // Crypto (full names → Binance symbol)
    'BITCOIN': { symbol: 'BTCUSDT', type: 'crypto' },
    'ETHEREUM': { symbol: 'ETHUSDT', type: 'crypto' },
    'BINANCE': { symbol: 'BNBUSDT', type: 'crypto' },
    'BINANCECOIN': { symbol: 'BNBUSDT', type: 'crypto' },
    'SOLANA': { symbol: 'SOLUSDT', type: 'crypto' },
    'RIPPLE': { symbol: 'XRPUSDT', type: 'crypto' },
    'DOGECOIN': { symbol: 'DOGEUSDT', type: 'crypto' },
    'CARDANO': { symbol: 'ADAUSDT', type: 'crypto' },
    'AVALANCHE': { symbol: 'AVAXUSDT', type: 'crypto' },
    'POLKADOT': { symbol: 'DOTUSDT', type: 'crypto' },
    'POLYGON': { symbol: 'MATICUSDT', type: 'crypto' },
    'CHAINLINK': { symbol: 'LINKUSDT', type: 'crypto' },
    'LITECOIN': { symbol: 'LTCUSDT', type: 'crypto' },
    'TRON': { symbol: 'TRXUSDT', type: 'crypto' },
    'COSMOS': { symbol: 'ATOMUSDT', type: 'crypto' },
    'SHIBA': { symbol: 'SHIBUSDT', type: 'crypto' },
    // Stocks (full names → backend handles Yahoo mapping)
    'FACEBOOK': { symbol: 'FACEBOOK', type: 'stock' },
    'APPLE': { symbol: 'APPLE', type: 'stock' },
    'GOOGLE': { symbol: 'GOOGLE', type: 'stock' },
    'AMAZON': { symbol: 'AMAZON', type: 'stock' },
    'NETFLIX': { symbol: 'NETFLIX', type: 'stock' },
    'TESLA': { symbol: 'TESLA', type: 'stock' },
    'MICROSOFT': { symbol: 'MICROSOFT', type: 'stock' },
    'NVIDIA': { symbol: 'NVIDIA', type: 'stock' },
    'INTEL': { symbol: 'INTEL', type: 'stock' },
    'ALIBABA': { symbol: 'ALIBABA', type: 'stock' },
    'META': { symbol: 'META', type: 'stock' },
    'VISA': { symbol: 'VISA', type: 'stock' },
    // Commodities (full names)
    'GOLD': { symbol: 'GOLD', type: 'commodity' },
    'SILVER': { symbol: 'SILVER', type: 'commodity' },
    'CRUDEOIL': { symbol: 'OIL', type: 'commodity' },
    'NATURALGAS': { symbol: 'NATGAS', type: 'commodity' },
    'BRENTOIL': { symbol: 'UKBRENT', type: 'commodity' },
  };

  // Known commodity keywords (for partial matching fallback)
  const COMMODITY_KEYWORDS = ['GOLD', 'SILVER', 'OIL', 'NATGAS', 'XAUUSD', 'UKBRENT', 'CRUDEOIL'];

  // Known stock keywords (for partial matching fallback)
  const STOCK_KEYWORDS = ['FACEBOOK', 'META', 'APPLE', 'GOOGLE', 'AMAZON', 'NETFLIX', 'TESLA', 'MICROSOFT', 'NVIDIA', 'INTEL', 'ALIBABA', 'VISA'];

  function autoDetect() {
    // Find active tab — Quotex uses dynamic class names, try multiple selectors
    const active = document.querySelector(
      '.tab-item.active, [class*="active"][class*="tab"], [class*="idOc0"]'
    );
    if (!active) return;

    // --- Extract ONLY the asset name, NOT the payout percentage ---
    // Quotex puts asset name in a child element (e.g. .Sgocu) and
    // payout % in another (e.g. .gDH53). Using textContent on the
    // parent concatenates both: "GBP/CHF86" instead of "GBP/CHF".
    let rawName = '';

    // Strategy 1: Try to grab the first text-like child (asset name element)
    const children = active.querySelectorAll('span, div, p');
    for (const child of children) {
      const t = child.textContent.trim();
      // Asset names contain letters and "/" but NOT just a number/percentage
      if (t && /[A-Z]/i.test(t) && !/^\d+%?$/.test(t)) {
        rawName = t;
        break;
      }
    }

    // Strategy 2: Fallback — use full textContent but strip trailing digits (payout %)
    if (!rawName) {
      rawName = active.textContent.trim();
    }

    rawName = rawName.toUpperCase();

    // Clean: "GBP/CHF (OTC)" -> "GBPCHF", "Bitcoin (OTC)" -> "BITCOIN"
    const isOtc = rawName.includes('OTC');
    let clean = rawName
      .replace(/\(OTC\)/gi, '')   // Remove OTC marker
      .replace(/\d+%?/g, '')      // Remove payout percentages like "86%" or "86"
      .replace(/[^A-Z]/g, '')     // Keep only letters
      .trim();

    if (!clean || clean.length < 2) return;

    // --- Determine asset type and symbol ---
    let type, symbol;

    // Priority 1: Check the name-to-symbol map with PREFIX matching.
    // Quotex may show "Facebook Inc" → cleaned to "FACEBOOKINC"
    // which should still match the "FACEBOOK" key.
    let bestMatch = null;
    for (const key of Object.keys(NAME_TO_SYMBOL)) {
      if (clean.startsWith(key) && (!bestMatch || key.length > bestMatch.length)) {
        bestMatch = key; // Pick the longest matching prefix
      }
    }
    if (bestMatch) {
      symbol = NAME_TO_SYMBOL[bestMatch].symbol;
      type = NAME_TO_SYMBOL[bestMatch].type;
    }
    // Priority 2: Check crypto tickers (BTC, ETH, etc.)
    else if (CRYPTO_BASES.has(clean)) {
      symbol = clean + 'USDT';
      type = 'crypto';
    }
    // Priority 3: Commodity keywords
    else if (COMMODITY_KEYWORDS.some(c => clean.includes(c))) {
      symbol = clean;
      type = 'commodity';
    }
    // Priority 4: Stock keywords
    else if (STOCK_KEYWORDS.some(s => clean.includes(s))) {
      symbol = clean;
      type = 'stock';
    }
    // Default: forex
    else {
      symbol = clean;
      type = 'forex';
    }

    if (state.selectedAsset !== symbol || state.selectedType !== type) {
      console.log(`[AutoDetect] Tab: "${rawName}" → Symbol: ${symbol} (${type})${isOtc ? ' [OTC]' : ''}`);
      state.selectedAsset = symbol;
      state.selectedType = type;
      state.signal = null;
      render();
      fetchSignal();
    }
  }

  // Sync settings and start
  chrome.storage.local.get(['apiConfig'], (res) => {
    if (res.apiConfig) {
      state.baseUrl = res.apiConfig.baseUrl || CONFIG.API_BASE_URL;
      state.mlEnabled = res.apiConfig.mlEnabled !== undefined ? res.apiConfig.mlEnabled : true;
    }
    // Don't fetch yet, wait for autoDetect to find the real asset
    autoDetect();
  });

  // High-speed detection
  setInterval(autoDetect, 500);

  // Also listen for clicks on tabs for instant switch
  document.addEventListener('click', () => {
    setTimeout(autoDetect, 100); // Small delay for Quotex DOM to update
  }, true);
})();
