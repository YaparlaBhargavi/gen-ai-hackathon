// app/static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
  console.log('AI Productivity App loaded');

  // Theme toggle
  const toggle = document.querySelector('.theme-toggle');
  if (toggle) {
    toggle.addEventListener('click', () => {
      document.documentElement.dataset.theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    });
  }
});

