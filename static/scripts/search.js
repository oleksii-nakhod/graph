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

function convertUtcToLocal() {
    document.querySelectorAll('.datetime').forEach(function (element) {
        const utcTime = element.getAttribute('data-datetime');
        const localTime = new Date(utcTime).toLocaleString();
        element.innerHTML = localTime;
    });
}


updateProgressBars();
convertUtcToLocal();
