btnGoCreate = document.querySelector('#btn-go-create-document');
btnGoCreate.classList.add('d-none');

btnDelete.classList.add('d-none');
btnCancel.classList.remove('d-none');
btnEdit.classList.add('d-none');
btnSave.classList.add('d-none');
btnCreate.classList.remove('d-none');

function generateRandomPlaceholder() {
    const placeholders = [
        {
            "title": "May the Forms Be With You",
            "content": "A guide on how to efficiently fill out and manage digital forms in your business processes."
        },
        {
            "title": "Winter is Coming",
            "content": "An advisory piece on how businesses can prepare for the economic downturn or seasonal business fluctuations."
        },
        {
            "title": "You Shall Not Pass… Without Authentication",
            "content": "A detailed guide on the importance of cybersecurity measures and authentication protocols."
        },
        {
            "title": "To Infinity and Beyond!",
            "content": "An inspirational piece on pushing the limits of innovation and achieving the seemingly impossible in technology."
        }
    ];
    const randomIndex = Math.floor(Math.random() * placeholders.length);
    return placeholders[randomIndex];
}

if (inputDocumentTitle && inputDocumentContent) {
    placeholder = generateRandomPlaceholder();
    inputDocumentTitle.placeholder = placeholder.title;
    inputDocumentContent.setAttribute('placeholder', placeholder.content);
}