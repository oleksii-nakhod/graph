function validateSearchForm() {
    const query = document.querySelector('#input-query').value;
    const alertSearch = document.querySelector('#alert-search');

    if (!query) {
        alertSearch.classList.remove('d-none');
        return false;
    }

    alertSearch.classList.add('d-none');
    window.location.href = '/search?q=' + encodeURIComponent(query);
    return false;
}


function serializeForm(formId) {
    const form = document.getElementById(formId);
    const formData = new FormData(form);
    const json = {};
    formData.forEach((value, key) => {
        json[key] = value || "";
    });
    return json;
}

function validateSignupForm() {
    const json = serializeForm('form-signup');
    fetch(url_signup, {
        method: 'POST',
        body: JSON.stringify(json),
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (response.ok) {
                document.getElementById('message-signup-error').style.display = 'none';
                return response.json();
            } else {
                document.getElementById('message-signup-success').style.display = 'none';
                return response.json().then(data => {
                    throw new Error(data.msg);
                });
            }
        })
        .then(() => {
            location.reload();
        })
        .catch(error => {
            const errorMessage = document.getElementById('message-signup-error');
            errorMessage.textContent = error.message;
            errorMessage.style.display = 'block';
        });

    return false;
}

function validateLoginForm() {
    const json = serializeForm('form-login');
    fetch(url_login, {
        method: 'POST',
        body: JSON.stringify(json),
        headers: {
            'Content-Type': 'application/json'
        }
    })
        .then(response => {
            if (response.ok) {
                document.getElementById('modal-login').style.display = 'none';
                document.getElementById('message-login-error').style.display = 'none';
                location.reload();
            } else {
                return response.json().then(data => {
                    throw new Error(data.msg);
                });
            }
        })
        .catch(error => {
            const errorMessage = document.getElementById('message-login-error');
            errorMessage.textContent = error.message;
            errorMessage.style.display = 'block';
        });

    return false;
}



function validateDocumentForm() {
    const title = document.querySelector('#input-document-title').value;
    const content = document.querySelector('#input-document-content').value;
    
    const alertContentMissing = document.querySelector('#alert-content-missing');
    const alertSubmissionSuccess = document.querySelector('#alert-submission-success');

    if (!title || !content) {
        alertContentMissing.classList.remove('d-none');
        return false;
    }

    alertContentMissing.classList.add('d-none');

    fetch(`${url_create_document}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title: title,
            content: content
        })
    })
    .then(response => {
        if (response.ok) {
            alertSubmissionSuccess.classList.remove('d-none');
            setInterval(() => {
                history.back();
            }, 2000);
        } else {
            return response.json().then(data => {
                throw new Error(data.msg);
            });
        }
    })
    return false;
}

function logOut() {
    fetch(url_logout, {
        method: 'POST'
    })
    .then(() => {
        location.reload();
    });
}