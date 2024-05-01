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

function drawGraph() {
    const config = {
        containerId: "viz",
        neo4j: {
            serverUrl: "neo4j://localhost:7687",
            serverUser: "neo4j",
            serverPassword: "k59D5ftw^N^WUm",
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
        initialCypher: "MATCH (n:Document) RETURN *"
    };

    neoViz = new NeoVis.default(config);
    neoViz.render();
}