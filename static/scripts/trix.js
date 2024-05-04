const btnBack = document.querySelector('#btn-back');
const btnDelete = document.querySelector('#btn-delete-document');
const btnCancel = document.querySelector('#btn-cancel-document');
const btnEdit = document.querySelector('#btn-edit-document');
const btnSave = document.querySelector('#btn-save-document');
const btnCreate = document.querySelector('#btn-create-document');

const formDocument = document.querySelector('#form-document');
const inputDocumentTitle = document.querySelector('#input-document-title');
const inputDocumentContent = document.querySelector('#input-document-content');
const inputHiddenTrix = document.querySelector('#input-hidden-trix');
const alertSubmissionSuccess = document.querySelector('#alert-submission-success');
const spinnerLoading = document.querySelector('#spinner-loading');
const documentActions = document.querySelector('#document-actions');

const trixToolbar = document.querySelector('trix-toolbar');

function enableEditor() {
    inputDocumentTitle.removeAttribute('readonly');
    inputDocumentContent.editor.element.setAttribute('contentEditable', true)
    trixToolbar.classList.remove('d-none');
}

function disableEditor() {
    inputDocumentTitle.setAttribute('readonly', '');
    inputDocumentContent.editor.element.setAttribute('contentEditable', false)
    trixToolbar.classList.add('d-none');
}

function validateDocumentForm() {
    const title = document.querySelector('#input-document-title').value;
    const content = document.querySelector('#input-document-content').value;

    const alertContentMissing = document.querySelector('#alert-content-missing');

    if (!title || !content) {
        alertContentMissing.classList.remove('d-none');
        return false;
    }

    alertContentMissing.classList.add('d-none');

    return true;
}

function createDocument(title, content) {
    if (!validateDocumentForm()) {
        return false;
    }

    inputDocumentTitle.setAttribute('readonly', '');
    inputDocumentContent.editor.element.setAttribute('contentEditable', false)
    btnCreate.classList.add('d-none');
    btnBack.classList.add('d-none');
    spinnerLoading.classList.remove('d-none');

    fetch(`${url_create_document}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title,
            content
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
                    throw new Error(data.message);
                });
            }
        })
        .catch(error => {
            const alertSubmissionError = document.querySelector('#alert-submission-error');
            alertSubmissionError.textContent = error.message;
            alertSubmissionError.classList.remove('d-none');

            inputDocumentTitle.removeAttribute('readonly');
            inputDocumentContent.editor.element.setAttribute('contentEditable', true)
            btnCreate.classList.remove('d-none');
            btnBack.classList.remove('d-none');
            spinnerLoading.classList.add('d-none');
        })
        .finally(() => {
            spinnerLoading.classList.add('d-none');
        });
}

function updateDocument(documentId, title, content) {
    if (!validateDocumentForm()) {
        return false;
    }
    url = url_update_document.replace('DOCUMENT_ID', documentId);

    disableEditor();

    btnBack.classList.add('d-none');
    btnEdit.classList.add('d-none');
    btnDelete.classList.add('d-none');
    btnSave.classList.add('d-none');
    btnCancel.classList.add('d-none');
    btnCreate.classList.add('d-none');
    trixToolbar.classList.add('d-none');

    spinnerLoading.classList.remove('d-none');

    fetch(`${url}`, {
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
                    location.href = '/'
                }, 2000);
            } else {
                return response.json().then(data => {
                    throw new Error(data.message);
                });
            }
        })
        .catch(error => {
            const alertSubmissionError = document.querySelector('#alert-submission-error');
            alertSubmissionError.textContent = error.message;
            alertSubmissionError.classList.remove('d-none');
            enableEditor();
            btnCancel.classList.remove('d-none');
            btnSave.classList.remove('d-none');
            trixToolbar.classList.remove('d-none');
        })
        .finally(() => {
            spinnerLoading.classList.add('d-none');
        });
}

function deleteDocument(documentId) {
    url = url_delete_document.replace('DOCUMENT_ID', documentId);

    btnBack.classList.add('d-none');
    btnEdit.classList.add('d-none');
    btnDelete.classList.add('d-none');
    btnSave.classList.add('d-none');
    btnCancel.classList.add('d-none');
    btnCreate.classList.add('d-none');

    spinnerLoading.classList.remove('d-none');

    fetch(`${url}`, {
        method: 'DELETE'
    })
        .then(response => {
            if (response.ok) {
                alertSubmissionSuccess.classList.remove('d-none');
                setInterval(() => {
                    location.href = '/'
                }, 2000);
            } else {
                return response.json().then(data => {
                    throw new Error(data.message);
                });
            }
        })
        .catch(error => {
            const alertSubmissionError = document.querySelector('#alert-submission-error');
            alertSubmissionError.textContent = error.message;
            alertSubmissionError.classList.remove('d-none');
            btnBack.classList.remove('d-none');
            btnDelete.classList.remove('d-none');
            btnEdit.classList.remove('d-none');
        })
        .finally(() => {
            spinnerLoading.classList.add('d-none');
        });
}


btnBack.addEventListener('click', function() {
    history.back();
});


btnDelete.addEventListener('click', function() {
    documentId = formDocument.getAttribute('data-document-id');
    deleteDocument(documentId);
});


btnCancel.addEventListener('click', function() {
    btnSave.classList.add('d-none');
    btnCancel.classList.add('d-none');
    btnEdit.classList.remove('d-none');
    btnDelete.classList.remove('d-none');
    btnBack.classList.remove('d-none');
    btnCreate.classList.add('d-none');

    inputDocumentTitle.setAttribute('readonly', true);
    inputDocumentContent.editor.element.setAttribute('contentEditable', false);
    trixToolbar.classList.add('d-none');
});


btnEdit.addEventListener('click', function() {
    enableEditor();
    inputDocumentContent.focus();
    btnEdit.classList.add('d-none');
    btnBack.classList.add('d-none');
    btnDelete.classList.add('d-none');
    btnSave.classList.remove('d-none');
    btnCancel.classList.remove('d-none');
});


btnSave.addEventListener('click', function() {
    documentId = formDocument.getAttribute('data-document-id');
    title = inputDocumentTitle.value;
    content = inputDocumentContent.value;
    updateDocument(documentId, title, content);
});


btnCreate.addEventListener('click', function() {
    title = inputDocumentTitle.value;
    content = inputDocumentContent.value;
    createDocument(title, content);
});


document.addEventListener('trix-attachment-add', function (event) {
    const attachment = event.attachment;
    uploadAttachment(attachment);
});


document.addEventListener('trix-attachment-remove', function (event) {
    const attachment = event.attachment;
    if (attachment.file) {
        return deleteFileAttachment(attachment);
    }
});


function uploadAttachment(attachment) {
    const file = attachment.file;

    if (file) {
        const form = new FormData();
        form.append('file', file);

        fetch(url_create_file, {
            method: 'POST',
            body: form
        })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Error uploading file');
                }
            })
            .then(data => {
                const url = url_get_file.replace('FILE_ID', data.id);

                attachment.setAttributes({
                    url: url,
                    href: url,
                });

                if (file.type.startsWith('audio')) {
                    const audioHtml = `<audio controls src=${url}>`;
                    const audioAttachment = new Trix.Attachment({ content: audioHtml });
                    inputDocumentContent.editor.insertAttachment(audioAttachment);
                }
            })
            .catch(error => {
                console.error(error);
            });
        return;
    }
}

function deleteFileAttachment(attachment) {
    const fileId = attachment.attachment.attributes.values.url.split('/').pop();
    const url = url_delete_file.replace('FILE_ID', fileId);
    fetch(url, {
        method: 'DELETE'
    })
        .then(response => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Error deleting file');
            }
        })
        .catch(error => {
            console.error(error);
        })
}

