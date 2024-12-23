document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.getElementById('search-form');
    const resultsDiv = document.getElementById('results');
    const searchInput = document.getElementById('query');

    searchForm.addEventListener('submit', function (e) {
        e.preventDefault();

        // Show loading state
        resultsDiv.innerHTML = '<p>Searching...</p>';

        const form = new FormData(this);

        fetch('', {
            method: 'POST',
            body: form,
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(response => response.json())
            .then(data => {
                resultsDiv.innerHTML = '';

                if (data.status === 'error') {
                    throw new Error(data.message);
                }

                if (!data.results || data.results.length === 0) {
                    resultsDiv.innerHTML = '<p>No results found.</p>';
                    return;
                }

                data.results.forEach((result, index) => {
                    const resultDiv = document.createElement('div');
                    resultDiv.className = 'result-item';
                    resultDiv.innerHTML = `
                        <div class="result-title">
                            <a href="/search/doc/${result.docid}" 
                            class="title-link" 
                            title="View full document">
                                Result #${index + 1}
                            </a>
                            <p>Document #${result.docid}</p>
                        </div>
                        <p class="result-text">${result.text}</p>
                    `;
                    resultsDiv.appendChild(resultDiv);
                });
            })
            .catch(error => {
                console.error('Error:', error);
                resultsDiv.innerHTML = '<p class="error-message">An error occurred while searching. Please try again.</p>';
            });
    });

    // Helper function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});