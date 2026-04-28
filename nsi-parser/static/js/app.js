document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const modelInput = document.getElementById('modelInput');
    const pagesInput = document.getElementById('pagesInput');
    const searchBtn = document.getElementById('searchBtn');
    const loading = document.getElementById('loading');
    const loadingText = document.getElementById('loadingText');
    const errorAlert = document.getElementById('errorAlert');
    const resultsSection = document.getElementById('resultsSection');
    const resultsCount = document.getElementById('resultsCount');
    const resultsBody = document.getElementById('resultsBody');
    const emptyState = document.getElementById('emptyState');
    const exportExcel = document.getElementById('exportExcel');
    const exportJson = document.getElementById('exportJson');

    let currentResults = null;

    function showError(message) {
        errorAlert.textContent = message;
        errorAlert.classList.remove('d-none');
        setTimeout(() => errorAlert.classList.add('d-none'), 5000);
    }

    function showLoading(message) {
        loadingText.textContent = message;
        loading.classList.remove('d-none');
        searchBtn.disabled = true;
    }

    function hideLoading() {
        loading.classList.add('d-none');
        searchBtn.disabled = false;
    }

    function renderTable(data) {
        if (!data || data.length === 0) {
            resultsSection.classList.add('d-none');
            emptyState.classList.remove('d-none');
            return;
        }

        emptyState.classList.add('d-none');
        resultsSection.classList.remove('d-none');
        resultsCount.textContent = data.length;

        resultsBody.innerHTML = data.map(item => {
            const link = item.url ? `<a href="${item.url}" target="_blank" title="${item.url}">Открыть</a>` : '-';
            return `
                <tr>
                    <td><strong>${escapeHtml(item.model)}</strong></td>
                    <td>${item.flow_rate || '-'}</td>
                    <td>${item.head || '-'}</td>
                    <td>${item.motor_power || '-'}</td>
                    <td>${item.rotation_speed || '-'}</td>
                    <td>${link}</td>
                </tr>
            `;
        }).join('');
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async function exportData(format) {
        if (!currentResults || currentResults.length === 0) {
            showError('Нет данных для экспорта');
            return;
        }

        try {
            const response = await fetch('/api/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ format, data: currentResults })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Ошибка экспорта');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `data_${format === 'excel' ? 'xlsx' : 'json'}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            showToast('Файл успешно скачан', 'success');
        } catch (error) {
            showError(error.message);
        }
    }

    function showToast(message, type = 'info') {
        const toastId = 'toast-' + Date.now();
        const toastContainer = document.querySelector('.toast-container') ||
            (function() {
                const container = document.createElement('div');
                container.className = 'toast-container';
                document.body.appendChild(container);
                return container;
            })();

        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">${message}</div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastEl = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
        toast.show();
        toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
    }

    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const model = modelInput.value.trim();
        const pages = parseInt(pagesInput.value) || 5;

        if (!model) {
            showError('Введите модель');
            return;
        }

        showLoading('Подключение к сайту...');
        errorAlert.classList.add('d-none');

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ model, pages })
            });

            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Ошибка сервера');
            }

            if (!result.success || result.count === 0) {
                showLoading('Поиск завершён');
                setTimeout(() => {
                    hideLoading();
                    showError('Ничего не найдено. Попробуйте упростить запрос.');
                    resultsSection.classList.add('d-none');
                    emptyState.classList.remove('d-none');
                }, 500);
                return;
            }

            currentResults = result.data;
            renderTable(currentResults);
            showLoading('Обработка данных...');
            setTimeout(() => {
                hideLoading();
                showToast(`Найдено: ${result.count}`, 'success');
            }, 300);

        } catch (error) {
            hideLoading();
            showError(error.message);
        }
    });

    exportExcel.addEventListener('click', () => exportData('excel'));
    exportJson.addEventListener('click', () => exportData('json'));

    modelInput.focus();
});