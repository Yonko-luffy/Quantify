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
