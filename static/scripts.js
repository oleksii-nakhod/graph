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


function validateDocumentForm() {
    const title = document.querySelector('#document-title').value;
    const content = document.querySelector('#document-content').value;
    
    const alertDocument = document.querySelector('#alert-document');

    if (!title || !content) {
        alertDocument.classList.remove('d-none');
        return false;
    }

    alertDocument.classList.add('d-none');

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
    return false;
}

function drawGraph(initialCypher) {
    const config = {
        containerId: "viz",
        neo4j: {
            serverUrl: "neo4j://localhost:7687",
            serverUser: "anonymous",
            serverPassword: "password",
        },
        labels: {
            Document: {
                label: "title",
                value: "pagerank",
                group: "community"
            }
        },
        relationships: {
            INTERACTS: {
                value: "weight"
            }
        },
        initialCypher
    };

    neoViz = new NeoVis.default(config);
    neoViz.render();
}