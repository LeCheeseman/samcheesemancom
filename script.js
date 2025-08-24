// Carousel logic
const track = document.querySelector('.carousel-track');
const slides = Array.from(track.children);
const prevBtn = document.querySelector('.carousel-btn.prev');
const nextBtn = document.querySelector('.carousel-btn.next');
let currentIndex = 0;

function updateSlide() {
  const slideWidth = slides[0].getBoundingClientRect().width;
  track.style.transform = `translateX(-${slideWidth * currentIndex}px)`;
}

nextBtn.addEventListener('click', () => {
  currentIndex = (currentIndex + 1) % slides.length;
  updateSlide();
});

prevBtn.addEventListener('click', () => {
  currentIndex = (currentIndex - 1 + slides.length) % slides.length;
  updateSlide();
});

window.addEventListener('resize', updateSlide);

// Toggle switch functionality for Featured Works filter
document.addEventListener('DOMContentLoaded', function() {
    const workToggle = document.getElementById('workToggle');
    
    if (workToggle) {
        workToggle.addEventListener('change', function() {
            const isChecked = this.checked;
            // Add functionality here to filter between Commercials and Copywriting
            console.log(isChecked ? 'Showing Copywriting works' : 'Showing Commercial works');
            
            // You can add actual filtering logic here when you have the work items
            // For example:
            // filterWorks(isChecked ? 'copywriting' : 'commercials');
        });
    }
});

// Function to filter works (placeholder for future implementation)
function filterWorks(category) {
    // This function can be implemented to show/hide work items based on category
    console.log(`Filtering works by: ${category}`);
}