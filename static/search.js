answerContent = document.querySelector('#answer-content');

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
    const systemMessage = {
        role: 'system',
        content: "Answer the user query with the information from their internal knowledge base. If this knowledge conflicts with yours, give preference to the user's knowledge. If you don't know the answer, you can say 'I don't know'."
    }

    const internalKnowledgeMessages = searchResponse.results.map(result => {
        return {
            role: 'assistant',
            content: `Title: ${result.title}\nContent: ${result.content}`
        };
    });

    const userMessage = {
        role: 'user',
        content: searchResponse.query
    };

    const messages = [systemMessage, ...internalKnowledgeMessages, userMessage];

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
        answerContent.innerHTML = marked.parse(content);
        if (done) {
            break;
        }
    }
}

updateProgressBars();
getAnswer();
