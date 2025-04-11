const themeToggler = document.querySelector(".theme-toggler");
const rows = document.querySelectorAll("tbody tr");

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', () => {
    const isDark = localStorage.getItem('theme') === 'dark';
    document.body.classList.toggle('dark-theme-variables', isDark);
    themeToggler.querySelector('span:nth-child(1)').classList.toggle('active', !isDark);
    themeToggler.querySelector('span:nth-child(2)').classList.toggle('active', isDark);
});

// Change theme
themeToggler.addEventListener('click', () => {
    const isDark = !document.body.classList.contains('dark-theme-variables');
    
    // Toggle UI
    document.body.classList.toggle('dark-theme-variables');
    themeToggler.querySelector('span:nth-child(1)').classList.toggle('active');
    themeToggler.querySelector('span:nth-child(2)').classList.toggle('active');
    
    // Save to localStorage
    localStorage.setItem('theme', isDark ? 'dark' : 'light');
});


document.querySelector(".subjects-toggle").addEventListener("click", function(event) {
    event.preventDefault();
    const dropdown = document.querySelector(".subjects-dropdown");
    dropdown.style.display = (dropdown.style.display === "none" || dropdown.style.display === "") ? "flex" : "none";
});

rows.forEach((row, index) => {
    const rankCell = row.cells[0]; // Get the first cell (Rank column) in the row
    rankCell.textContent = index + 1; // Set the rank as index + 1
});
