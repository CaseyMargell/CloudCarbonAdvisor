(function() {
    var configEl = document.getElementById('app-config');
    var ROOT = configEl.dataset.rootPath || '';
    var MAX_SIZE = (parseInt(configEl.dataset.maxFileSizeMb, 10) || 20) * 1024 * 1024;
    var MAX_SIZE_MB = configEl.dataset.maxFileSizeMb || '20';

    var dropZone = document.getElementById('drop-zone');
    var fileInput = document.getElementById('file-input');
    var uploadSection = document.getElementById('upload-section');
    var processingSection = document.getElementById('processing-section');
    var resultsSection = document.getElementById('results-section');
    var resultsContent = document.getElementById('results-content');
    var resultsActions = document.getElementById('results-actions');
    var detailsCta = document.getElementById('details-cta');
    var detailsBtn = document.getElementById('details-btn');
    var detailsContent = document.getElementById('details-content');
    var staticFooter = document.getElementById('static-footer');
    var errorSection = document.getElementById('error-section');
    var errorMessage = document.getElementById('error-message');

    var cachedBillText = null;

    marked.setOptions({ breaks: true, gfm: true });

    function cleanText(s) {
        return s
            .replace(/\u2014/g, '--')
            .replace(/\u2013/g, '-')
            .replace(/\u2018|\u2019/g, "'")
            .replace(/\u201C|\u201D/g, '"')
            .replace(/\u2026/g, '...')
            .replace(/\u2192/g, '->')
            .replace(/\u00a0/g, ' ');
    }

    var earthSpinner = '<svg class="section-spinner" width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">' +
        '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" ' +
        'd="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>';

    var sectionLabels = {
        'bill summary': 'Summarizing your bill',
        'recommendation summary': 'Building recommendations overview',
        'carbon footprint': 'Estimating carbon footprint',
        'top actions': 'Identifying top actions',
        'implementation roadmap': 'Building implementation roadmap',
        'implementation priority': 'Building implementation roadmap',
        'region migration': 'Analyzing region migration options',
        'instance optimization': 'Evaluating instance alternatives',
        'right-sizing': 'Checking for right-sizing opportunities',
        'idle resource': 'Scanning for idle resources',
        'workload scheduling': 'Analyzing workload scheduling',
        'database': 'Reviewing database optimization'
    };

    function getLabelForHeader(header) {
        var lower = header.toLowerCase();
        for (var key in sectionLabels) {
            if (lower.indexOf(key) !== -1) return sectionLabels[key];
        }
        return 'Analyzing ' + header;
    }

    // --- Drag and drop ---
    dropZone.addEventListener('dragover', function(e) { e.preventDefault(); dropZone.classList.add('drag-over'); });
    dropZone.addEventListener('dragleave', function() { dropZone.classList.remove('drag-over'); });
    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) { fileInput.files = e.dataTransfer.files; handleFile(e.dataTransfer.files[0]); }
    });
    dropZone.addEventListener('click', function() { fileInput.click(); });
    dropZone.addEventListener('keydown', function(e) { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fileInput.click(); } });
    fileInput.addEventListener('change', function() { if (fileInput.files.length) handleFile(fileInput.files[0]); });

    function handleFile(file) {
        if (file.size > MAX_SIZE) { showError('File too large. Maximum size is ' + MAX_SIZE_MB + 'MB.'); return; }
        uploadAndStream(file);
    }

    function showError(msg) {
        uploadSection.classList.add('hidden');
        processingSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        errorSection.classList.remove('hidden');
        errorMessage.textContent = msg;
    }

    async function uploadAndStream(file) {
        uploadSection.classList.add('hidden');
        processingSection.classList.remove('hidden');
        resultsSection.classList.add('hidden');
        errorSection.classList.add('hidden');

        var formData = new FormData();
        formData.append('file', file);

        var response;
        try { response = await fetch(ROOT + '/api/analyze', { method: 'POST', body: formData }); }
        catch (err) { showError('Network error. Please check your connection and try again.'); return; }

        if (!response.ok) {
            try { var data = await response.json(); showError(data.error || 'Something went wrong.'); }
            catch (e) { showError('Something went wrong. Please try again.'); }
            return;
        }

        processingSection.classList.add('hidden');
        resultsSection.classList.remove('hidden');
        resultsContent.innerHTML = '';
        resultsActions.classList.add('hidden');

        var reader = response.body.getReader();
        var decoder = new TextDecoder();
        var buffer = '';
        var accumulated = '';
        var renderedUpTo = 0;
        var sections = [];
        var progressEl = null;
        var renderPending = false;

        function createProgressIndicator(label, container) {
            if (progressEl) progressEl.remove();
            progressEl = document.createElement('div');
            progressEl.className = 'section-progress';
            progressEl.innerHTML = earthSpinner + ' <span>' + label + '...</span>';
            (container || resultsContent).appendChild(progressEl);
            progressEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function scanAndRender() {
            var headerPattern = /\n(#{1,2}\s+\S[^\n]*)/g;
            var match;
            var boundaries = [];
            while ((match = headerPattern.exec(accumulated)) !== null) {
                boundaries.push({ idx: match.index + 1, header: match[1] });
            }
            if (/^#{1,2}\s+\S/.test(accumulated)) {
                var firstLine = accumulated.split('\n')[0];
                boundaries.unshift({ idx: 0, header: firstLine });
            }

            for (var i = 0; i < boundaries.length; i++) {
                var b = boundaries[i];
                if (b.idx <= renderedUpTo) continue;

                if (sections.length > 0) {
                    var prev = sections[sections.length - 1];
                    var prevMarkdown = accumulated.substring(prev.startIdx, b.idx);
                    prev.el.innerHTML = DOMPurify.sanitize(marked.parse(prevMarkdown));
                }

                var el = document.createElement('div');
                el.className = 'result-section';
                resultsContent.appendChild(el);
                sections.push({ el: el, startIdx: b.idx });

                var headerText = b.header.replace(/^#+\s*/, '').trim();
                createProgressIndicator(getLabelForHeader(headerText));

                renderedUpTo = b.idx;
            }

            if (sections.length > 0 && !renderPending) {
                renderPending = true;
                requestAnimationFrame(function() {
                    var curr = sections[sections.length - 1];
                    var currMarkdown = accumulated.substring(curr.startIdx);
                    curr.el.innerHTML = DOMPurify.sanitize(marked.parse(currMarkdown));
                    renderPending = false;
                });
            }
        }

        createProgressIndicator('Reading your cloud bill');

        while (true) {
            var result = await reader.read();
            if (result.done) break;

            buffer += decoder.decode(result.value, { stream: true });
            var lines = buffer.split('\n');
            buffer = lines.pop();

            var eventType = '';
            for (var i = 0; i < lines.length; i++) {
                var line = lines[i];
                if (line.startsWith('event: ')) {
                    eventType = line.slice(7).trim();
                } else if (line.startsWith('data: ')) {
                    try {
                        var data = JSON.parse(line.slice(6));
                        if (eventType === 'context' && data.bill_text) {
                            cachedBillText = data.bill_text;

                        } else if (eventType === 'chunk' && data.content) {
                            accumulated += cleanText(data.content);
                            scanAndRender();

                        } else if (eventType === 'done') {
                            if (sections.length > 0) {
                                var last = sections[sections.length - 1];
                                last.el.innerHTML = DOMPurify.sanitize(marked.parse(accumulated.substring(last.startIdx)));
                            }
                            if (progressEl) progressEl.remove();
                            var isNotBill = accumulated.indexOf('Not a Cloud Bill') !== -1;
                            if (isNotBill) {
                                document.getElementById('download-btn').classList.add('hidden');
                            } else {
                                if (cachedBillText) detailsCta.classList.remove('hidden');
                                staticFooter.classList.remove('hidden');
                            }
                            resultsActions.classList.remove('hidden');

                        } else if (eventType === 'error') {
                            if (progressEl) progressEl.remove();
                            if (accumulated) {
                                var errDiv = document.createElement('div');
                                errDiv.className = 'stream-error';
                                errDiv.innerHTML = (data.message || 'Analysis was interrupted.') + ' <a href="' + ROOT + '/">Start over</a>';
                                resultsContent.appendChild(errDiv);
                            } else {
                                showError(data.message || 'Something went wrong.');
                            }
                        }
                    } catch (e) {}
                }
            }
        }
    }

    // --- Load details ---
    var detailsLoaded = false;
    var detailsLoading = false;

    async function loadDetails() {
        if (detailsLoaded) return true;
        if (detailsLoading) return false;
        if (!cachedBillText) return false;

        detailsLoading = true;
        detailsCta.classList.add('hidden');
        detailsContent.innerHTML = '';

        var response;
        try {
            response = await fetch(ROOT + '/api/analyze/details', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bill_text: cachedBillText })
            });
        } catch (err) {
            detailsContent.innerHTML = '<div class="stream-error">Network error loading details. <a href="' + ROOT + '/">Start over</a></div>';
            detailsLoading = false;
            return false;
        }

        if (!response.ok) {
            try { var errData = await response.json(); detailsContent.innerHTML = '<div class="stream-error">' + (errData.error || 'Failed to load details.') + '</div>'; }
            catch (e) { detailsContent.innerHTML = '<div class="stream-error">Failed to load details.</div>'; }
            detailsLoading = false;
            return false;
        }

        var dReader = response.body.getReader();
        var dDecoder = new TextDecoder();
        var dBuffer = '', dAccumulated = '';
        var dSections = [], dRenderedUpTo = 0, dRenderPending = false;
        var dProgressEl = null;

        function dCreateProgress(label) {
            if (dProgressEl) dProgressEl.remove();
            dProgressEl = document.createElement('div');
            dProgressEl.className = 'section-progress';
            dProgressEl.innerHTML = earthSpinner + ' <span>' + label + '...</span>';
            detailsContent.appendChild(dProgressEl);
            dProgressEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }

        function dScanAndRender() {
            var headerPattern = /\n(#{1,2}\s+\S[^\n]*)/g;
            var match, boundaries = [];
            while ((match = headerPattern.exec(dAccumulated)) !== null) {
                boundaries.push({ idx: match.index + 1, header: match[1] });
            }
            if (/^#{1,2}\s+\S/.test(dAccumulated)) {
                boundaries.unshift({ idx: 0, header: dAccumulated.split('\n')[0] });
            }
            for (var i = 0; i < boundaries.length; i++) {
                var b = boundaries[i];
                if (b.idx <= dRenderedUpTo) continue;
                if (dSections.length > 0) {
                    var prev = dSections[dSections.length - 1];
                    prev.el.innerHTML = DOMPurify.sanitize(marked.parse(dAccumulated.substring(prev.startIdx, b.idx)));
                }
                var el = document.createElement('div');
                el.className = 'result-section';
                detailsContent.appendChild(el);
                dSections.push({ el: el, startIdx: b.idx });
                var headerText = b.header.replace(/^#+\s*/, '').trim();
                dCreateProgress(getLabelForHeader(headerText));
                dRenderedUpTo = b.idx;
            }
            if (dSections.length > 0 && !dRenderPending) {
                dRenderPending = true;
                requestAnimationFrame(function() {
                    var curr = dSections[dSections.length - 1];
                    curr.el.innerHTML = DOMPurify.sanitize(marked.parse(dAccumulated.substring(curr.startIdx)));
                    dRenderPending = false;
                });
            }
        }

        dCreateProgress('Generating detailed recommendations');

        while (true) {
            var dResult = await dReader.read();
            if (dResult.done) break;
            dBuffer += dDecoder.decode(dResult.value, { stream: true });
            var dLines = dBuffer.split('\n');
            dBuffer = dLines.pop();
            var dEventType = '';
            for (var i = 0; i < dLines.length; i++) {
                var dl = dLines[i];
                if (dl.startsWith('event: ')) { dEventType = dl.slice(7).trim(); }
                else if (dl.startsWith('data: ')) {
                    try {
                        var dd = JSON.parse(dl.slice(6));
                        if (dEventType === 'chunk' && dd.content) {
                            dAccumulated += cleanText(dd.content);
                            dScanAndRender();
                        } else if (dEventType === 'done') {
                            if (dSections.length > 0) {
                                var last = dSections[dSections.length - 1];
                                last.el.innerHTML = DOMPurify.sanitize(marked.parse(dAccumulated.substring(last.startIdx)));
                            }
                            if (dProgressEl) dProgressEl.remove();
                        } else if (dEventType === 'error') {
                            if (dProgressEl) dProgressEl.remove();
                            detailsContent.innerHTML += '<div class="stream-error">' + (dd.message || 'Details interrupted.') + '</div>';
                        }
                    } catch (e) {}
                }
            }
        }

        detailsLoaded = true;
        detailsLoading = false;
        return true;
    }

    detailsBtn.addEventListener('click', function() { loadDetails(); });

    document.getElementById('download-btn').addEventListener('click', async function() {
        var btn = this;
        if (!detailsLoaded && cachedBillText) {
            btn.textContent = 'Generating full report...';
            btn.disabled = true;
            await loadDetails();
            btn.textContent = 'Download PDF Report';
            btn.disabled = false;
        }
        document.querySelectorAll('#details-content details').forEach(function(d) { d.open = true; });
        window.print();
    });
})();
