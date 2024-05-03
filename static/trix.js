const inputDocumentTitle = document.querySelector('#input-document-title');
const inputDocumentContent = document.querySelector('#input-document-content');

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

    return true;
}

function createDocument() {
    if (!validateDocumentForm()) {
        return false;
    }
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
        .catch(error => {
            const alertSubmissionError = document.querySelector('#alert-submission-error');
            alertSubmissionError.textContent = error.message;
            alertSubmissionError.classList.remove('d-none');
        });
}

function updateDocument(documentId) {
    if (!validateDocumentForm()) {
        return false;
    }
    fetch(`${url_update_document}/${documentId}`, {
        method: 'PUT',
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
        .catch(error => {
            const alertSubmissionError = document.querySelector('#alert-submission-error');
            alertSubmissionError.textContent = error.message;
            alertSubmissionError.classList.remove('d-none');
        });
}

btnDelete = document.querySelector('#btn-delete-document');
btnCancel = document.querySelector('#btn-cancel-document');
btnEdit = document.querySelector('#btn-edit-document');
btnSave = document.querySelector('#btn-save-document');
btnCreate = document.querySelector('#btn-create-document');

btnDelete.addEventListener('click', function() {
});

btnCancel.addEventListener('click', function() {
    history.back();
});

btnEdit.addEventListener('click', function() {
    inputDocumentTitle.removeAttribute('readonly');
    inputDocumentContent.editor.element.setAttribute('contentEditable', true)
    inputDocumentContent.focus();
    btnEdit.classList.add('d-none');
    btnSave.classList.remove('d-none');
    btnCancel.classList.remove('d-none');
});

btnSave.addEventListener('click', function() {
    inputDocumentTitle.setAttribute('readonly', true);
    inputDocumentContent.editor.element.setAttribute('contentEditable', false)
    btnEdit.classList.remove('d-none');
    btnSave.classList.add('d-none');
    btnCancel.classList.add('d-none');
});

btnCreate.addEventListener('click', function() {
    inputDocumentTitle.removeAttribute('readonly');
    inputDocumentContent.editor.element.setAttribute('contentEditable', true)
    inputDocumentTitle.focus();
    btnCreate.classList.add('d-none');
    btnSave.classList.remove('d-none');
    btnCancel.classList.remove('d-none');
});


