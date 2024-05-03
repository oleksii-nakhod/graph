answerContent = document.querySelector('#answer-content');

function updateSearchInput() {
    uriParams = new URLSearchParams(window.location.search);
    if (uriParams.has("q")) {
        const query = uriParams.get("q");
        const searchInput = document.querySelector("#input-query");
        searchInput.value = query;
    }
}

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

async function getAnswer() {
    const response = await fetch(url_create_completion, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            content: document.querySelector('#input-query').value
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let content = '';
    while (true) {
        const { done, value } = await reader.read();
        content += decoder.decode(value);
        console.log(content);
        answerContent.innerHTML = marked.parse(content);
        if (done) {
            break;
        }
    }
}

updateSearchInput();
updateProgressBars();
getAnswer();
