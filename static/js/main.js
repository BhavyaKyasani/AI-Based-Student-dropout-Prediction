// Main Javascript for Student Dropout Prediction System

document.addEventListener('DOMContentLoaded', function() {
    // 1. Sidebar Toggle for Mobile
    const toggleBtn = document.querySelector('.menu-toggle-btn');
    const sidebar = document.querySelector('.sidebar');
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('show');
        });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(event) {
        if (sidebar && sidebar.classList.contains('show') && 
            !sidebar.contains(event.target) && 
            !toggleBtn.contains(event.target)) {
            sidebar.classList.remove('show');
        }
    });

    // 2. Animate KPI Counters
    animateCounters();

    // 3. Highlight active menu item based on current URL
    highlightActiveMenuItem();
});

// Counter Animation Function
function animateCounters() {
    const counters = document.querySelectorAll('.animate-counter');
    counters.forEach(counter => {
        const targetText = counter.getAttribute('data-target');
        if (!targetText) return;
        
        const isFloat = targetText.includes('.');
        const target = parseFloat(targetText);
        const duration = 1200; // ms
        const frameRate = 1000 / 60; // 60fps
        const totalFrames = Math.round(duration / frameRate);
        let frame = 0;
        
        const timer = setInterval(() => {
            frame++;
            const progress = frame / totalFrames;
            // Easing function (easeOutQuad)
            const easeProgress = progress * (2 - progress);
            const currentVal = target * easeProgress;
            
            if (isFloat) {
                counter.innerText = currentVal.toFixed(1);
            } else {
                counter.innerText = Math.floor(currentVal);
            }
            
            if (frame >= totalFrames) {
                counter.innerText = targetText;
                clearInterval(timer);
            }
        }, frameRate);
    });
}

// Highlight sidebar menu items
function highlightActiveMenuItem() {
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.sidebar-item a');
    
    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (currentPath === href || (href !== '/' && currentPath.startsWith(href))) {
            // Remove active from all
            document.querySelectorAll('.sidebar-item').forEach(item => item.classList.remove('active'));
            // Add to parent li
            link.parentElement.classList.add('active');
        }
    });
}

// Chart Helper Functions
const chartColors = {
    gold: '#D4AF37',
    goldHover: '#E6C65C',
    success: '#22C55E',
    warning: '#F59E0B',
    danger: '#EF4444',
    dark: '#121212',
    gridLines: '#E2E8F0',
    lightGray: '#B0B0B0',
    text: '#1A1A1A'
};

// Global Chart Options helper
function getCommonChartOptions(title, displayLegend = false) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            title: {
                display: false
            },
            legend: {
                display: displayLegend,
                position: 'bottom',
                labels: {
                    font: {
                        family: 'Inter',
                        size: 12
                    },
                    color: chartColors.text
                }
            }
        },
        scales: {
            x: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    color: chartColors.text,
                    font: { family: 'Inter' }
                }
            },
            y: {
                grid: {
                    color: 'rgba(0, 0, 0, 0.05)'
                },
                ticks: {
                    color: chartColors.text,
                    font: { family: 'Inter' }
                }
            }
        }
    };
}
