function updateGraph(data) {
    if (neoViz) {
        neoViz.clearNetwork();
        neoViz._config.initialCypher = "MATCH (doc:Document) WHERE id(doc) IN [" + data.map(item => item.id).join(",") + "] RETURN doc";
        neoViz.render();
    }
}