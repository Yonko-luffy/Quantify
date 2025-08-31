// Profile dropdown toggle functionality
function toggleDropdown() {
  const dropdown = document.getElementById("profileDropdown");
  dropdown.classList.toggle("show");
}

// Hide if clicked outside
window.addEventListener("click", function (e) {
  const dropdown = document.getElementById("profileDropdown");
  const profile = document.querySelector(".profile-container");
  
  if (!profile.contains(e.target)) {
    dropdown.classList.remove("show");
  }
});

// Auto-hide flash messages
document.addEventListener('DOMContentLoaded', function() {
  const alerts = document.querySelectorAll('.flash-messages-container .alert');
  alerts.forEach(function(alert) {
    // Auto-hide after 5 seconds
    setTimeout(function() {
      alert.style.animation = 'slideUp 0.3s ease-out forwards';
      setTimeout(function() {
        alert.remove();
      }, 300);
    }, 5000);
    
    // Allow manual dismissal by clicking
    alert.addEventListener('click', function() {
      alert.style.animation = 'slideUp 0.3s ease-out forwards';
      setTimeout(function() {
        alert.remove();
      }, 300);
    });
  });
});

// Login cooldown logic
document.addEventListener('DOMContentLoaded', function() {
  const loginBtn = document.getElementById('loginBtn');
  const cooldownMsg = document.getElementById('cooldownMsg');
  if (loginBtn && cooldownMsg) {
    loginBtn.disabled = true;
    let cooldown = 60; // seconds, adjust as needed or pass from backend
    function updateCooldown() {
      if (cooldown > 0) {
        cooldownMsg.textContent = `Please wait ${cooldown} seconds before trying again.`;
        cooldown--;
        setTimeout(updateCooldown, 1000);
      } else {
        cooldownMsg.textContent = '';
        loginBtn.disabled = false;
      }
    }
    updateCooldown();
  }
});

// Dynamic Favicon based on browser theme
document.addEventListener('DOMContentLoaded', function() {
  function updateFavicon() {
    // Check if browser supports dark mode detection
    if (window.matchMedia) {
      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
      
      // Get or create favicon link element
      let favicon = document.querySelector('link[rel="icon"]');
      if (!favicon) {
        favicon = document.createElement('link');
        favicon.rel = 'icon';
        favicon.type = 'image/svg+xml';
        document.head.appendChild(favicon);
      }
      
      // Set favicon based on theme
      if (darkModeQuery.matches) {
        // Dark mode - use white favicon
        favicon.href = '/static/images/favicon_white.svg';
      } else {
        // Light mode - use black favicon
        favicon.href = '/static/images/favicone_black.svg';
      }
    }
  }
  
  // Set initial favicon
  updateFavicon();
  
  // Listen for theme changes
  if (window.matchMedia) {
    const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
    darkModeQuery.addListener(updateFavicon);
  }
});
