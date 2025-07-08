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
