// Profile dropdown toggle functionality
function toggleDropdown() {
  const dropdown = document.getElementById("profileDropdown");
  const isVisible = getComputedStyle(dropdown).display === "flex";
  dropdown.style.display = isVisible ? "none" : "flex";
}

// Hide if clicked outside
window.addEventListener("click", function (e) {
  const dropdown = document.getElementById("profileDropdown");
  const profile = document.querySelector(".profile-container");
  
  if (!profile.contains(e.target)) {
    dropdown.style.display = "none";
  }
});

// Theme toggle functionality
function toggleTheme() {
  document.body.classList.toggle('dark');
  
  // Save theme preference
  if (document.body.classList.contains('dark')) {
    localStorage.setItem('theme', 'dark');
  } else {
    localStorage.setItem('theme', 'light');
  }
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', function() {
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'dark') {
    document.body.classList.add('dark');
  }
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
