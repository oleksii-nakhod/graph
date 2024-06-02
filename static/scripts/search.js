function updateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(function (bar) {
        const score = parseFloat(bar.getAttribute('data-score'));
        const percentage = score * 100;
        let progressClass;
        let progressText;

        if (score < 0.5) {
            progressClass = 'bg-danger';
            progressText = 'Bad Match'
        } else if (score < 0.75) {
            progressClass = 'bg-warning';
            progressText = 'Average Match';
        } else {
            progressClass = 'bg-success';
            progressText = 'Close Match';
        }

        bar.style.width = percentage.toFixed(2) + '%';
        bar.classList.add(progressClass);
        bar.setAttribute('aria-valuenow', score);
        bar.innerText = progressText;
    });
}

function formatDateTime() {
    document.querySelectorAll('.datetime').forEach(function (element) {
        const utcTime = element.getAttribute('data-datetime');
        const date = new Date(utcTime);

        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: 'numeric',
            minute: 'numeric',
            hour12: true
        };
        const userLocale = navigator.language || 'en-US';
        const formattedDate = new Intl.DateTimeFormat(userLocale, options).format(date);
        element.innerHTML = formattedDate;
    });
}


async function getInsights() {
    const insightsContent = document.querySelector('#insights-content');
    const urlParams = new URLSearchParams(window.location.search);
    const query = urlParams.get('q', '');

    const systemMessage = {
        role: 'system',
        content: "You are a helpful assistant that provides insights into information that is stored in a knowledge base. You can call external functions to retrieve additional data if necessary."
    }

    const userMessage = {
        role: 'user',
        content: query
    };

    const messages = [systemMessage, userMessage];

    const response = await fetch(url_create_completion, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            messages
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let content = '';
    while (true) {
        const { done, value } = await reader.read();
        content += decoder.decode(value);
        insightsContent.innerHTML = marked.parse(content);
        if (done) {
            break;
        }
    }
}


function initializeSearch() {
    updateProgressBars();
    formatDateTime();

    const urlParams = new URLSearchParams(window.location.search);
    const insights = urlParams.get('insights') === 'true';
    if (insights) {
        getInsights();
    }

}


initializeSearch()