uriParams = new URLSearchParams(window.location.search);
if (uriParams.has("q")) {
    const query = uriParams.get("q");
    const searchInput = document.querySelector("#input-query");
    searchInput.value = query;
}