function applyTheme() {
    // Default to light theme since that is the root in CSS.
    const theme = localStorage.getItem('theme') || 'light';
    if (theme === 'dark') {
        document.body.classList.add('dark-theme');
    } else {
        document.body.classList.remove('dark-theme');
    }
    updateThemeIcon();
}

function toggleTheme() {
    const isDark = document.body.classList.contains('dark-theme');
    if (isDark) {
        localStorage.setItem('theme', 'light');
        document.body.classList.remove('dark-theme');
    } else {
        localStorage.setItem('theme', 'dark');
        document.body.classList.add('dark-theme');
    }
    updateThemeIcon();
}

function updateThemeIcon() {
    const icon = document.getElementById('theme-icon');
    if (icon) {
        if (document.body.classList.contains('dark-theme')) {
            icon.className = 'fas fa-sun';
        } else {
            icon.className = 'fas fa-moon';
        }
    }
}

function createToggleButton() {
    if (document.getElementById('floating-theme-btn')) return;

    const btn = document.createElement('button');
    btn.id = 'floating-theme-btn';
    btn.onclick = toggleTheme;
    btn.style.position = 'fixed';
    btn.style.bottom = '20px';
    btn.style.left = '20px'; // Bottom left to avoid overlapping toasts on bottom right
    btn.style.zIndex = '9999';
    btn.style.background = 'var(--glass-bg)';
    btn.style.border = '1px solid var(--glass-border)';
    btn.style.color = 'var(--text-main)';
    btn.style.width = '45px';
    btn.style.height = '45px';
    btn.style.borderRadius = '50%';
    btn.style.boxShadow = 'var(--glass-shadow)';
    btn.style.cursor = 'pointer';
    btn.style.display = 'flex';
    btn.style.alignItems = 'center';
    btn.style.justifyContent = 'center';
    btn.style.fontSize = '1.2rem';
    btn.style.transition = 'all 0.3s ease';
    
    btn.onmouseover = () => btn.style.transform = 'scale(1.1)';
    btn.onmouseout = () => btn.style.transform = 'scale(1)';

    const icon = document.createElement('i');
    icon.id = 'theme-icon';
    btn.appendChild(icon);

    document.body.appendChild(btn);
    updateThemeIcon();
}

document.addEventListener("DOMContentLoaded", () => {
    applyTheme();
    createToggleButton();
});

// Run immediately for instant application (prevents white flash if dark mode was saved)
applyTheme();
