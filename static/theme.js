// Theme switcher with localStorage persistence
(function () {
  const STORAGE_KEY = 'threat-dashboard-theme';
  const THEME_LIGHT = 'light';
  const THEME_DARK = 'dark';
  const ICON_LIGHT = '☀️';
  const ICON_DARK = '🌙';

  // Detect system preference
  function getSystemTheme() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? THEME_DARK : THEME_LIGHT;
  }

  // Get the current theme from localStorage or system preference
  function getCurrentTheme() {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) return saved;
    return getSystemTheme();
  }

  // Apply theme to document
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    updateToggleButton(theme);
  }

  // Update toggle button appearance
  function updateToggleButton(theme) {
    const btn = document.getElementById('theme-toggle');
    if (btn) {
      const icon = theme === THEME_LIGHT ? ICON_DARK : ICON_LIGHT;
      const label = `Switch to ${theme === THEME_LIGHT ? 'dark' : 'light'} mode`;
      btn.setAttribute('aria-label', label);
      btn.setAttribute('title', label);
      const iconSpan = btn.querySelector('.theme-icon');
      if (iconSpan) {
        iconSpan.textContent = icon;
      }
    }
  }

  // Toggle between themes
  function toggleTheme() {
    const current = getCurrentTheme();
    const next = current === THEME_LIGHT ? THEME_DARK : THEME_LIGHT;
    applyTheme(next);
  }

  // Initialize on page load
  function init() {
    const theme = getCurrentTheme();
    applyTheme(theme);

    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', toggleTheme);
    }
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
