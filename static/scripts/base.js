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
                    throw new Error(data.message);
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
                    throw new Error(data.message);
                });
            }
        })
        .catch(error => {
            const errorMessage = document.getElementById('message-login-error');
            errorMessage.textContent = error;
            errorMessage.style.display = 'block';
        });

    return false;
}

function logOut() {
    fetch(url_logout, {
        method: 'POST'
    })
    .then((response) => {
        if (response.ok) {
            location.reload();
        } else {
            return response.json().then(data => {
                throw new Error(data.message);
            });
        }
    })
    .catch(error => {
        console.error(error);
    });
}


const loginLink = document.getElementById('link-login-modal');
const signupLink = document.getElementById('link-signup-modal');
const loginModal = new bootstrap.Modal('#modal-login', {
    keyboard: false
})
const signupModal = new bootstrap.Modal('#modal-signup', {
    keyboard: false
})

signupLink.addEventListener('click', function () {
    loginModal.hide();
    signupModal.show();
});

loginLink.addEventListener('click', function () {
    signupModal.hide();
    loginModal.show();
});