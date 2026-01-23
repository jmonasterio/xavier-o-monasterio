// Web Worker for building Lunr.js search index in background
importScripts('https://cdn.jsdelivr.net/npm/lunr@2.3.9/lunr.min.js');

let searchIndex = null;
let searchDocs = null;

self.onmessage = function(e) {
    if (e.data.type === 'build') {
        searchDocs = e.data.docs;

        // Build Lunr index
        searchIndex = lunr(function() {
            this.ref('id');
            this.field('title', { boost: 10 });
            this.field('body');

            searchDocs.forEach(doc => {
                this.add(doc);
            });
        });

        self.postMessage({ type: 'ready', count: searchDocs.length });
    }

    if (e.data.type === 'search') {
        if (!searchIndex) {
            self.postMessage({ type: 'results', results: [], error: 'Index not ready' });
            return;
        }

        try {
            const results = searchIndex.search(e.data.query);
            // Map results to include document data
            const mappedResults = results.slice(0, 20).map(result => ({
                ...searchDocs[result.ref],
                score: result.score
            }));
            self.postMessage({ type: 'results', results: mappedResults, query: e.data.query });
        } catch (err) {
            self.postMessage({ type: 'results', results: [], error: err.message });
        }
    }
};
