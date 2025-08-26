// This function runs when the entire HTML document has been loaded.
document.addEventListener('DOMContentLoaded', () => {

    // Select all the elements with the class 'category-card'.
    const categoryCards = document.querySelectorAll('.category-card');

    // Loop through each card we found.
    categoryCards.forEach(card => {
        // Add a 'click' event listener to each card.
        card.addEventListener('click', () => {
            // Find the h2 element inside the clicked card and get its text.
            const categoryName = card.querySelector('h2').innerText;
            
            // Log a message to the browser's developer console.
            // You can press F12 or right-click -> Inspect to see the console.
            console.log(`You clicked on the "${categoryName}" category!`);
            
            // Here you could add code to navigate to another page,
            // play a song, or show more information.
        });
    });

});
