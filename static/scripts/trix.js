const btnBack = document.querySelector('#btn-back');
const btnDelete = document.querySelector('#btn-delete-item');
const btnCancel = document.querySelector('#btn-cancel-item');
const btnEdit = document.querySelector('#btn-edit-item');
const btnSave = document.querySelector('#btn-save-item');
const btnCreate = document.querySelector('#btn-create-item');

const formItem = document.querySelector('#form-item');
const itemTitle = document.querySelector('#item-title');
const inputItemTitle = document.querySelector('#input-item-title');
const inputItemContent = document.querySelector('#input-item-content');
const inputHiddenTrix = document.querySelector('#input-hidden-trix');
const alertSubmissionSuccess = document.querySelector('#alert-submission-success');
const spinnerLoading = document.querySelector('#spinner-loading');
const itemActions = document.querySelector('#item-actions');

const trixToolbar = document.querySelector('trix-toolbar');

const redirectTimeout = 1500;

function enableEditor() {
    inputItemTitle.removeAttribute('readonly');
    inputItemContent.editor.element.setAttribute('contentEditable', true)
    trixToolbar.classList.remove('d-none');
}

function disableEditor() {
    inputItemTitle.setAttribute('readonly', '');
    inputItemContent.editor.element.setAttribute('contentEditable', false)
    trixToolbar.classList.add('d-none');
}

function validateItemForm() {
    const title = document.querySelector('#input-item-title').value;
    const content = document.querySelector('#input-item-content').value;

    const alertContentMissing = document.querySelector('#alert-content-missing');

    if (!title || !content) {
        alertContentMissing.classList.remove('d-none');
        return false;
    }

    alertContentMissing.classList.add('d-none');

    return true;
}

function createItem(title, content) {
    if (!validateItemForm()) {
        return false;
    }

    inputItemTitle.setAttribute('readonly', '');
    inputItemContent.editor.element.setAttribute('contentEditable', false)
    btnCreate.classList.add('d-none');
    btnBack.classList.add('d-none');
    spinnerLoading.classList.remove('d-none');

    const labels = [];
    const labelInputs = document.querySelectorAll('input[name="labels"]:checked');

    labelInputs.forEach((labelInput) => {
        labels.push(labelInput.value);
    });

    fetch(`${url_create_item}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            title,
            content,
            labels
        })
    })
        .then(response => {
            if (response.ok) {
                alertSubmissionSuccess.classList.remove('d-none');
                setInterval(() => {
                    history.back();
                }, redirectTimeout);
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

            inputItemTitle.removeAttribute('readonly');
            inputItemContent.editor.element.setAttribute('contentEditable', true)
            btnCreate.classList.remove('d-none');
            btnBack.classList.remove('d-none');
            spinnerLoading.classList.add('d-none');
        })
        .finally(() => {
            spinnerLoading.classList.add('d-none');
        });
}

function updateItem(itemId, title, content) {
    if (!validateItemForm()) {
        return false;
    }
    url = url_update_item.replace('NODE_ID', itemId);

    disableEditor();

    setElementVisibility({
        '#btn-back': false,
        '#btn-delete-item': false,
        '#btn-cancel-item': false,
        '#btn-edit-item': false,
        '#btn-save-item': false,
        '#btn-create-item': false
    });

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
                }, redirectTimeout);
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

function deleteItem(itemId) {
    url = url_delete_item.replace('NODE_ID', itemId);

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
                }, redirectTimeout);
            } else {
                return response.json().then(data => {
                    throw new Error(data.message);
                });
            }
        })
        .catch(error => {
            const alertSubmissionError = document.querySelector('#alert-submission-error');
            alertSubmissionError.textContent = error.message;
            setElementVisibility({
                '#alert-submission-error': true,
                '#btn-back': true,
                '#btn-delete-item': true,
                '#btn-edit-item': true
            });
        })
        .finally(() => {
            spinnerLoading.classList.add('d-none');
        });
}

if (btnBack) {
    btnBack.addEventListener('click', function() {
        history.back();
    });
}

if (btnDelete) {
    btnDelete.addEventListener('click', function () {
        itemId = formItem.getAttribute('data-item-id');
        deleteItem(itemId);
    });
}

if (btnCancel) {
    btnCancel.addEventListener('click', function () {
        setElementVisibility({
            '#btn-back': true,
            '#btn-delete-item': true,
            '#btn-cancel-item': false,
            '#btn-edit-item': true,
            '#btn-save-item': false,
            '#btn-create-item': false,
            '#label-input-item-title': false,
            '#input-item-title': false,
            '#item-title': true,
            'trix-toolbar': false
        });

        inputItemTitle.setAttribute('readonly', true);
        inputItemContent.editor.element.setAttribute('contentEditable', false);
    });
}

if (btnEdit) {
    btnEdit.addEventListener('click', function() {
        enableEditor();
        inputItemContent.focus();
        setElementVisibility({
            '#btn-back': false,
            '#btn-delete-item': false,
            '#btn-cancel-item': true,
            '#btn-edit-item': false,
            '#btn-save-item': true,
            '#btn-create-item': false,
            '#label-input-item-title': true,
            '#input-item-title': true,
            '#item-title': false
        });
    });
}

if (btnSave) {
    btnSave.addEventListener('click', function() {
        itemId = formItem.getAttribute('data-item-id');
        title = inputItemTitle.value;
        content = inputItemContent.value;
        updateItem(itemId, title, content);
    });
}

if (btnCreate) {
    btnCreate.addEventListener('click', function() {
        title = inputItemTitle.value;
        content = inputItemContent.value;
        createItem(title, content);
    });
}


document.addEventListener('trix-attachment-add', function (event) {
    console.log('trix-attachment-add');
    console.log(event);
    const attachment = event.attachment;
    uploadAttachment(attachment);
});


document.addEventListener('trix-attachment-remove', function (event) {
    console.log('trix-attachment-remove');
    console.log(event);
    const attachment = event.attachment;
    if (attachment.file) {
        return deleteAttachment(attachment);
    }
});


function prepareFormData(file) {
    const form = new FormData();
    form.append('file', file);
    return form;
}

async function uploadFile(form) {
    const response = await fetch(url_create_file, {
        method: 'POST',
        body: form
    });
    if (!response.ok) {
        throw new Error('Error uploading file');
    }
    return await response.json();
}

function handleFileUploadResponse(data, file, selectedRange, attachment) {
    const url = url_get_file.replace('FILE_ID', data.id);
    attachment.setAttributes({
        url: url
    });

    if (file.type.startsWith('audio')) {
        return processAudioFile(url, selectedRange);
    } else if (file.type.startsWith('image')) {
        console.log('Processing image file');
        return processImageFile(url, attachment);
    }
}

function processAudioFile(url, selectedRange) {
    const audioHtml = `<audio controls src=${url}>`;
    const audioAttachment = new Trix.Attachment({ content: audioHtml });
    inputItemContent.editor.setSelectedRange(selectedRange);
    inputItemContent.editor.insertAttachment(audioAttachment);
}

function createAudioTranscription(form, file) {
    fetch(url_create_transcription, {
        method: 'POST',
        body: form
    }).then(response => {
        if (!response.ok) {
            throw new Error('Error creating transcription');
        }
        return response.json();
    }).then(data => {
        inputItemContent.editor.insertHTML(`<i>Audio transcription:\n${data.text}</i>`);
    }).catch(console.error);
}

function processImageFile(url, attachment) {
    return fetch(url_create_completion, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            messages: [{
                role: 'user',
                content: [
                    { type: 'text', text: "What's in this image?" },
                    { type: 'image_url', image_url: { url: `${window.location.origin}${url}` } }
                ]
            }]
        })
    }).then(response => processImageResponse(response, attachment))
        .catch(console.error);
}

function processImageResponse(response, attachment) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedDescription = "";
    readStreamToUpdateCaption(reader, decoder, attachment, accumulatedDescription);
}

function readStreamToUpdateCaption(reader, decoder, attachment, accumulatedDescription) {
    reader.read().then(({ done, value }) => {
        if (done) {
            return;
        }
        accumulatedDescription += decoder.decode(value);
        readStreamToUpdateCaption(reader, decoder, attachment, accumulatedDescription);
        updateImageCaption(accumulatedDescription, attachment);
    });
}

function updateImageCaption(description, attachment) {
    const editor = document.querySelector('trix-editor').editor;
    const originalRange = editor.getSelectedRange();
    const attachmentRange = editor.getDocument().getRangeOfAttachment(attachment);

    editor.setSelectedRange(attachmentRange);
    editor.activateAttribute("caption", description);
    editor.setSelectedRange(originalRange);
}

function readStream(reader, decoder) {
    reader.read().then(({ done, value }) => {
        if (done) {
            return;
        }
        inputItemContent.editor.insertHTML(`<i>${decoder.decode(value)}</i>`);
        readStream(reader, decoder);
    });
}

function restoreEditorState() {
    inputItemContent.editor.element.setAttribute('contentEditable', true);
}

function uploadAttachment(attachment) {
    const file = attachment.file;
    const selectedRange = inputItemContent.editor.getSelectedRange();

    if (file) {
        const form = prepareFormData(file);
        inputItemContent.editor.element.setAttribute('contentEditable', false);

        const uploadFilePromise = uploadFile(form)
            .then(data => handleFileUploadResponse(data, file, selectedRange, attachment))
            .catch(console.error);

        const transcriptionPromise = file.type.startsWith('audio') ?
            createAudioTranscription(form, file) : Promise.resolve();

        Promise.all([uploadFilePromise, transcriptionPromise])
            .catch(console.error)
            .finally(restoreEditorState);
    }
}


function deleteAttachment(attachment) {
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

