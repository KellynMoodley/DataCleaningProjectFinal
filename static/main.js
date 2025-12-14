// Tracks which Google Sheet is currently selected.
let currentSheet = null;

// Stores pagination and sorting state for each table.
let currentTableStates = {
    original: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
    included: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
    excluded: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' }
};

// Stores active filters (name, month, year) for each table.
let currentFilters = {
    original: { name: '', month: '', year: '' },
    included: { name: '', month: '', year: '' },
    excluded: { name: '', month: '', year: '' }
};

// Global Chart.js instance (used so charts can be destroyed/reloaded)
let chartInstance = null;

// State for duplicate records pagination and grouping
let currentDuplicatesState = {
    groupType: 'name_year',
    page: 1,
    perPage: 50
};

//comparison state
let currentComparisonState = {
    view: 'summary',  
    page: 1,
    perPage: 50,
    filterTop80: null,
    top80Only: false
};


// ==============================
// SHEET PROCESSING
// ==============================

// Sends a request to process a Google Sheet and displays status + results
function processSheet(sheetKey) {
    const statusBox = document.getElementById(`status-${sheetKey}`);
    const processBtn = event.target;
    const viewBtn = document.getElementById(`view-btn-${sheetKey}`);
    
    // Disable process button while running
    processBtn.disabled = true;
    processBtn.textContent = '⏳ Processing...';
    
    // Show loading UI
    statusBox.className = 'status-box show';
    statusBox.innerHTML = `
        <div style="text-align: center;">
            <div class="spinner" style="margin: 0 auto 12px;"></div>
            <p><strong>Processing sheet...</strong></p>
            <p style="margin-top: 8px; font-size: 0.9rem;">This may take a few minutes for large datasets.</p>
        </div>
    `;
    
    // POST request to backend to process the sheet
    fetch(`/process/${sheetKey}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            statusBox.className = 'status-box show error';
            statusBox.innerHTML = `
                <p><strong>❌ Error:</strong> ${data.error}</p>
            `;
            processBtn.disabled = false;
            processBtn.textContent = '🔄 Process Sheet';
            return;
        }
        
        // Display success statistics
        statusBox.className = 'status-box show success';
        statusBox.innerHTML = `
            <p><strong>✅ Processing Complete!</strong></p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-label">Total Rows</div>
                    <div class="stat-value">${data.total_rows.toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Included</div>
                    <div class="stat-value" style="color: #27ae60;">${data.included_count.toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Excluded</div>
                    <div class="stat-value" style="color: #e74c3c;">${data.excluded_count.toLocaleString()}</div>
                </div>
            </div>
        `;
        
        // Enable viewing data
        viewBtn.disabled = false;
        // Lock process button
        processBtn.disabled = true;
        processBtn.textContent = '✅ Already Processed';
        processBtn.style.backgroundColor = '#95a5a6';
        
        // Set current active sheet
        currentSheet = sheetKey;
    })
    .catch(error => {
        console.error('Error:', error);
        statusBox.className = 'status-box show error';
        statusBox.innerHTML = `
            <p><strong>❌ Error:</strong> Failed to process sheet. Please try again.</p>
        `;
        processBtn.disabled = false;
        processBtn.textContent = '🔄 Process Sheet';
    });
}

// ==============================
// VIEW SHEET DATA
// ==============================

// Displays data section and loads default table

function viewSheetData(sheetKey) {
    currentSheet = sheetKey;

    // Show data container
    const dataDisplay = document.getElementById('data-display');
    dataDisplay.style.display = 'block';

    // Update header with sheet name
    const sheetNameElement = document.getElementById('current-sheet-name');

    // Attempt to get display name from DOM
    const sheetCard = document.querySelector(
        `.sheet-card button[onclick="viewSheetData('${sheetKey}')"]`
    )?.closest('.sheet-card');

    const displayName = sheetCard
        ? sheetCard.querySelector('h3').innerText
        : sheetKey;

    sheetNameElement.textContent = `${displayName} (${sheetKey})`;

    // Scroll into view
    dataDisplay.scrollIntoView({ behavior: 'smooth' });

    // Reset table states
    currentTableStates = {
        original: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
        included: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
        excluded: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' }
    };

    // Load default tab
    switchTab('original');
}

// ==============================
// TAB NAVIGATION
// ==============================

// Handles switching between tabs and loading appropriate content
function switchTab(tableType) {
    // Remove active class from main tabs
    const mainTabs = document.querySelectorAll('.tabs > .tab');
    mainTabs.forEach(tab => tab.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Hide all sections
    document.querySelectorAll('.table-section').forEach(section => {
        section.classList.remove('show');
    });

    // Show the selected section
    const sectionId = `${tableType}-section`;
    const section = document.getElementById(sectionId);
    
    if (section) {
        section.classList.add('show');
        
        // Load section-specific data
        if (tableType === 'original' || tableType === 'included' || tableType === 'excluded') {
            loadTableData(tableType);
        } else if (tableType === 'summary_stats') {
            loadAnalyticsSummary();
        } else if (tableType === 'duplicates') {
            loadDuplicates('name_year');
        } else if (tableType === 'charts') {
            loadChart('birthyear');
        }else if (tableType === 'common_names') {
            loadCommonNames();
        }else if (tableType === 'comparison') {
            loadComparisonSummary();
        }
    }
}

// ==============================
// TABLE DATA LOADING
// ==============================

// Fetches paginated, sorted, and filtered table data from backend
function loadTableData(tableType) {
    if (!currentSheet) return;
    
    const state = currentTableStates[tableType];
    const container = document.getElementById(`${tableType}-table-container`);
    
    // Show loading indicator
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading data...</p>
        </div>
    `;

    // Build API URL with pagination, sorting, and filters
    const filters = currentFilters[tableType];
    let url = `/data/${currentSheet}/${tableType}?page=${state.page}&per_page=${state.perPage}&sort_by=${state.sortBy}&sort_order=${state.sortOrder}`;

    if (filters.name) url += `&filter_name=${encodeURIComponent(filters.name)}`;
    if (filters.month) url += `&filter_month=${filters.month}`;
    if (filters.year) url += `&filter_year=${filters.year}`;
    
    // Fetch table data
    fetch(url)
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            container.innerHTML = `
                <div class="loading">
                    <p style="color: #e74c3c;">❌ Error: ${data.error}</p>
                </div>
            `;
            return;
        }
        
        // Render table rows
        renderTable(tableType, data.data);
        
        // Render pagination controls
        renderPagination(tableType, data.page, data.total_pages, data.total_count);
    })
    .catch(error => {
        console.error('Error loading data:', error);
        container.innerHTML = `
            <div class="loading">
                <p style="color: #e74c3c;">❌ Error loading data. Please try again.</p>
            </div>
        `;
    });
}

// ==============================
// TABLE RENDERING
// ==============================

// Renders HTML table based on returned dataset
function renderTable(tableType, data) {
    const container = document.getElementById(`${tableType}-table-container`);

    // Handle empty datasets
    if (!data || data.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #7f8c8d;">No data available</p>';
        return;
    }
    
    // Define column order depending on table type
    let columns;
    if (tableType === 'included') {
        columns = ['original_row_number', 'row_id', 'firstname', 'birthday', 'birthmonth', 'birthyear'];
    } else if (tableType === 'excluded') {
        columns = ['original_row_number', 'row_id', 'firstname', 'birthday', 'birthmonth', 'birthyear', 'exclusion_reason'];
    } else {
        columns = ['original_row_number', 'row_id', 'firstname', 'birthday', 'birthmonth', 'birthyear', 'exclusion_reason', 'status'];
    }
    
    // Only keep columns that actually exist in the data
    columns = columns.filter(col => col in data[0]);
    
    const state = currentTableStates[tableType];
    
    // Start building table HTML
    let html = '<table><thead><tr>';

    // Render table headers with sorting controls
    columns.forEach(col => {
        const sortIndicator = state.sortBy === col ? 
            (state.sortOrder === 'asc' ? '▲' : '▼') : '';
        html += `<th onclick="sortTable('${tableType}', '${col}')">${formatColumnName(col)} <span class="sort-indicator">${sortIndicator}</span></th>`;
    });
    
    html += '</tr></thead><tbody>';
    
    // Render table rows
    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            if (value === null || value === undefined) {
                value = '';
            }
            // Truncate long strings for readability
            if (typeof value === 'string' && value.length > 100) {
                value = value.substring(0, 100) + '...';
            }
            html += `<td>${escapeHtml(String(value))}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    // Insert table HTML
    container.innerHTML = html;
    
    // Populate year filter options dynamically
    if (data.length > 0) {
        // Extract unique years for filter
        const uniqueYears = [...new Set(data.map(row => row.birthyear).filter(y => y))].sort();
        populateYearFilter(tableType, uniqueYears);
    }
}

// ==============================
// PAGINATION
// ==============================

// Renders pagination controls below tables
function renderPagination(tableType, currentPage, totalPages, totalCount) {
    const container = document.getElementById(`${tableType}-pagination`);

    // If only one page, show total count only
    if (totalPages <= 1) {
        container.innerHTML = `<div class="page-info">Total: ${totalCount} records</div>`;
        return;
    }
    
    let html = `
        <button onclick="goToPage('${tableType}', ${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            ← Previous
        </button>
        <div class="page-info">
            Page ${currentPage} of ${totalPages} (${totalCount} total records)
        </div>
        <button onclick="goToPage('${tableType}', ${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            Next →
        </button>
    `;
    
    container.innerHTML = html;
}

// ==============================
// SORTING & PAGING CONTROLS
// ==============================

// Updates sorting state and reloads table
function sortTable(tableType, column) {
    const state = currentTableStates[tableType];
    
    // Toggle sort order if same column, otherwise default to asc
    if (state.sortBy === column) {
        state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortBy = column;
        state.sortOrder = 'asc';
    }
    
    // Reset to first page after sorting
    state.page = 1;
    
    // Reload data
    loadTableData(tableType);
}

// Navigates to a specific page
function goToPage(tableType, page) {
    const state = currentTableStates[tableType];
    state.page = page;
    loadTableData(tableType);
}

// Change per page
function changePerPage(tableType) {
    const select = document.getElementById(`${tableType}-per-page`);
    const state = currentTableStates[tableType];
    state.perPage = parseInt(select.value);
    state.page = 1; // Reset to first page
    loadTableData(tableType);
}

// Converts snake_case to Title Case for column headers
function formatColumnName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

// Escapes HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ==============================
// TABLE DOWNLOADS
// ==============================

// Downloads the currently viewed table in CSV or JSON format
function downloadTable(tableType, format) {
    if (!currentSheet) {
        alert('Please select a sheet first');
        return;
    }
    
    // Show temporary loading notification
    const statusMessage = document.createElement('div');
    statusMessage.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #3498db; color: white; padding: 15px 20px; border-radius: 8px; z-index: 9999;';
    statusMessage.textContent = `Generating ${format.toUpperCase()}... Please wait.`;
    document.body.appendChild(statusMessage);
    
    // Trigger download
    window.location.href = `/download/${currentSheet}/${tableType}/${format}`;
    
    // Remove loading notification
    setTimeout(() => {
        statusMessage.remove();
    }, 3000);
}


// ==============================
// ANALYTICS SECTION
// ==============================

// Loads all analytics components in sequence
function loadAnalyticsData() {
    if (!currentSheet) return;
    
    // Load quick summary first
    loadAnalyticsSummary();
    
    // Load charts next
    loadAnalyticsDistributions();
    
    // Load duplicates last (slowest)
    loadAnalyticsDuplicates();
}

// Creates analytics tables on backend
function loadanalytics(sheetKey) {
    if (!currentSheet) {
        alert('Please select a sheet first');
        return;
    }
    
    const loadBtn = event.target;
    loadBtn.disabled = true;
    loadBtn.textContent = '⏳ Creating Analytics...';
    
    fetch(`/analytics/${currentSheet}/create`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to create analytics');
            });
        }
        return response.json();
    })
    .then(data => {
        // Success - update button
        loadBtn.textContent = '✅ Analytics Ready';
        loadBtn.style.backgroundColor = '#95a5a6';
        
        // Load analytics data into UI
        loadAnalyticsData();
    })
    .catch(error => {
        console.error('Error creating analytics:', error);
        alert('Failed to create analytics. Please try again.');
        loadBtn.disabled = false;
        loadBtn.textContent = '📥 Load analytics';
    });
}

// ==============================
// ANALYTICS SUMMARY
// ==============================

// Loads summary statistics for analytics
function loadAnalyticsSummary() {
    if (!currentSheet) return;
    
    const container = document.getElementById('analytics-summary');
    
    // Show loading
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading summary...</p>
        </div>
    `;
    
    fetch(`/analytics/${currentSheet}/summary`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `
                    <p style="color: #e74c3c;">Error: ${data.error}</p>
                `;
                return;
            }
            
            // Render summary cards
            container.innerHTML = `
                <div class="stats">
                    <div class="stat-item">
                        <div class="stat-label">Unique Names</div>
                        <div class="stat-value">${(data.unique_names || 0).toLocaleString()}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Unique Birthdays</div>
                        <div class="stat-value">${(data.unique_birthdays || 0).toLocaleString()}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Name+Year Combos</div>
                        <div class="stat-value">${(data.unique_name_year || 0).toLocaleString()}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Name+Month Combos</div>
                        <div class="stat-value">${(data.unique_name_month || 0).toLocaleString()}</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-label">Name+Day Combos</div>
                        <div class="stat-value">${(data.unique_name_day || 0).toLocaleString()}</div>
                    </div>
                </div>
            `;
        })
        .catch(error => {
            console.error('Error loading analytics summary:', error);
            container.innerHTML = `
                <p style="color: #e74c3c;">Failed to load summary data</p>
            `;
        });
}

//loads chart
function loadAnalyticsDistributions() {
    loadChart('birthyear');
}

// ==============================
// ANALYTICS DUPLICATES
// ==============================

// Loads default duplicates grouping
function loadAnalyticsDuplicates() {
    // Load default duplicates
    loadDuplicates('name_year');
}

// Switches duplicate grouping type
function loadDuplicates(groupType) {
    if (!currentSheet) return;
    // Update global state for duplicates view
    currentDuplicatesState.groupType = groupType;
    currentDuplicatesState.page = 1;
    
    // Update active tab styling
    const duplicateTabs = document.querySelectorAll('#duplicates-section .tabs .tab');
    duplicateTabs.forEach(tab => tab.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    fetchDuplicates();// Fetch duplicate data from server
}

// Fetch duplicate data from backend
function fetchDuplicates() {
    const container = document.getElementById('duplicates-container');
    const { groupType, page, perPage } = currentDuplicatesState;
    
    // Show loading spinner
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading duplicates...</p>
        </div>
    `;
    
    // Call backend endpoint for duplicates
    fetch(`/analytics/${currentSheet}/duplicates/${groupType}?page=${page}&per_page=${perPage}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<p style="color: #e74c3c;">Error: ${data.error}</p>`;
                return;
            }
            
            if (!data.data || data.data.length === 0) {
                container.innerHTML = `<p style="text-align: center; padding: 20px; color: #7f8c8d;">No duplicates found for this combination</p>`;
                document.getElementById('duplicates-pagination').innerHTML = '';
                return;
            }
            
            renderDuplicates(data.data, groupType);
            renderDuplicatesPagination(data.page, data.total_pages, data.total_count);
        })
        .catch(error => {
            console.error('Error loading duplicates:', error);
            container.innerHTML = `<p style="color: #e74c3c;">Failed to load duplicates</p>`;
        });
}

// ==============================
// DUPLICATE RENDERING
// ==============================

// Render duplicate groups as a simple list with counts
function renderDuplicates(duplicates, groupType) {
    const container = document.getElementById('duplicates-container');
    
    if (!duplicates || duplicates.length === 0) {
        container.innerHTML = `<p style="text-align: center; padding: 20px; color: #7f8c8d;">No duplicates found</p>`;
        return;
    }
    
    let html = '<div style="padding: 20px;">';
    
    duplicates.forEach(dup => {
        let label = '';
        // Build label based on grouping type
        if (groupType === 'name_year') {
            label = `${escapeHtml(dup.firstname)} - ${dup.birthyear}`;
        } else if (groupType === 'name_month') {
            label = `${escapeHtml(dup.firstname)} - Month ${dup.birthmonth}`;
        } else if (groupType === 'name_day') {
            label = `${escapeHtml(dup.firstname)} - Day ${dup.birthday}`;
        } else if (groupType === 'year_month') {
            label = `${dup.birthyear} - Month ${dup.birthmonth}`;
        } else if (groupType === 'year_day') {
            label = `${dup.birthyear} - Day ${dup.birthday}`;
        } else if (groupType === 'month_day') {
            label = `Month ${dup.birthmonth} - Day ${dup.birthday}`;
        }
        
        html += `
            <div style="padding: 12px 0; border-bottom: 1px solid #ecf0f1;">
                <span style="font-weight: 500; color: #2c3e50;">${label}</span>
                <span style="color: #e74c3c; margin-left: 12px;">(${dup.duplicate_count} duplicates)</span>
            </div>
        `;
    });
    
    html += '</div>';
    container.innerHTML = html;
}

//sort out duplicates pagination
function renderDuplicatesPagination(currentPage, totalPages, totalCount) {
    const container = document.getElementById('duplicates-pagination');
    
    if (totalPages <= 1) {
        container.innerHTML = `<div class="page-info">Total: ${totalCount} duplicate groups</div>`;
        return;
    }
    
    let html = `
        <button onclick="goToDuplicatesPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            ← Previous
        </button>
        <div class="page-info">
            Page ${currentPage} of ${totalPages} (${totalCount} duplicate groups)
        </div>
        <button onclick="goToDuplicatesPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            Next →
        </button>
    `;
    
    container.innerHTML = html;
}

//navigate to duplicate pages
function goToDuplicatesPage(page) {
    currentDuplicatesState.page = page;
    fetchDuplicates();
}

// ==============================
// ANALYTICS CHARTS
// ==============================

//load charts
function loadChart(chartType) {
    if (!currentSheet) return;
    
    // Update tab active state for chart tabs
    const chartTabs = document.querySelectorAll('#charts-section .tabs .tab');
    chartTabs.forEach(tab => tab.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    const container = document.getElementById('chart-container');
    
    // Show loading
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading chart...</p>
        </div>
    `;
    
    // Fetch chart data from backend
    fetch(`/analytics/${currentSheet}/charts/${chartType}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<p style="color: #e74c3c;">Error: ${data.error}</p>`;
                return;
            }
            
            // Restore canvas for Chart.js
            container.innerHTML = '<canvas id="analytics-chart" style="max-height: 400px;"></canvas>';
            renderChart(data.data, chartType);
        })
        .catch(error => {
            console.error('Error loading chart:', error);
            container.innerHTML = `<p style="color: #e74c3c;">Failed to load chart</p>`;
        });
}

// Render chart using Chart.js
function renderChart(data, chartType) {
    const canvas = document.getElementById('analytics-chart');
    
    if (!data || data.length === 0) {
        const container = document.getElementById('chart-container');
        container.innerHTML = `<p style="text-align: center; padding: 20px; color: #7f8c8d;">No data available</p>`;
        return;
    }
    
    // Destroy existing chart if present
    if (chartInstance) {
        chartInstance.destroy();
    }
    
    // Prepare data for Chart.js
    const labels = data.map(item => {
        if (chartType === 'birthyear') {
            return item.birthyear.toString();
        } else {
            const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return monthNames[item.birthmonth - 1];
        }
    });
    
    const counts = data.map(item => item.count);
    
    // Create new chart
    const ctx = canvas.getContext('2d');
    chartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: chartType === 'birthyear' ? 'Records by Birth Year' : 'Records by Birth Month',
                data: counts,
                backgroundColor: 'rgba(52, 152, 219, 0.6)',
                borderColor: 'rgba(52, 152, 219, 1)',
                borderWidth: 2,
                borderRadius: 4,
                hoverBackgroundColor: 'rgba(52, 152, 219, 0.8)',
                hoverBorderColor: 'rgba(41, 128, 185, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        font: {
                            size: 14
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toLocaleString() + ' records';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0,
                        callback: function(value) {
                            return value.toLocaleString();
                        }
                    },
                    title: {
                        display: true,
                        text: 'Number of Records',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: chartType === 'birthyear' ? 'Birth Year' : 'Birth Month',
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    },
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// ==============================
// COMMON NAMES ANALYTICS
// ==============================

// Load most common names with summary stats
function loadCommonNames() {
    if (!currentSheet) return;
    
    const container = document.getElementById('common-names-container');
    
    // Show loading
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading common names...</p>
        </div>
    `;
    
    fetch(`/analytics/${currentSheet}/common_names`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<p style="color: #e74c3c;">Error: ${data.error}</p>`;
                return;
            }
            
            if (!data.names || data.names.length === 0) {
                container.innerHTML = `<p style="text-align: center; padding: 20px; color: #7f8c8d;">No data available</p>`;
                return;
            }
            
            // Build HTML table with frequency stats
            let html = `
                <div style="padding: 20px;">
                    <div class="stats" style="margin-bottom: 20px;">
                        <div class="stat-item">
                            <div class="stat-label">Number of Names</div>
                            <div class="stat-value">${data.summary.total_names.toLocaleString()}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Records Covered</div>
                            <div class="stat-value">${data.summary.coverage_count.toLocaleString()}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Total Records</div>
                            <div class="stat-value">${data.summary.total_records.toLocaleString()}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label">Coverage</div>
                            <div class="stat-value">80%</div>
                        </div>
                    </div>
                    
                    <div style="display: flex; gap: 10px; margin-bottom: 20px;">
                        <button onclick="downloadCommonNames('csv')" style="background-color: #27ae60; padding: 10px 20px; border: none; color: white; border-radius: 6px; cursor: pointer;">
                            📥 Download CSV
                        </button>
                        <button onclick="downloadCommonNames('json')" style="background-color: #3498db; padding: 10px 20px; border: none; color: white; border-radius: 6px; cursor: pointer;">
                            📥 Download JSON
                        </button>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; overflow-x: auto;">
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="background: #34495e; color: white;">
                                    <th style="padding: 12px; text-align: left;">Rank</th>
                                    <th style="padding: 12px; text-align: left;">Name</th>
                                    <th style="padding: 12px; text-align: right;">Frequency</th>
                                    <th style="padding: 12px; text-align: right;">Percentage</th>
                                    <th style="padding: 12px; text-align: right;">Cumulative Count</th>
                                    <th style="padding: 12px; text-align: right;">Cumulative %</th>
                                </tr>
                            </thead>
                            <tbody>
            `;
            
            data.names.forEach((row, index) => {
                const bgColor = index % 2 === 0 ? '#ffffff' : '#f8f9fa';
                html += `
                    <tr style="background: ${bgColor}; border-bottom: 1px solid #ecf0f1;">
                        <td style="padding: 10px;">${row.rank}</td>
                        <td style="padding: 10px; font-weight: 500;">${escapeHtml(row.firstname)}</td>
                        <td style="padding: 10px; text-align: right;">${row.frequency.toLocaleString()}</td>
                        <td style="padding: 10px; text-align: right;">${row.percentage_of_total}%</td>
                        <td style="padding: 10px; text-align: right;">${row.cumulative_count.toLocaleString()}</td>
                        <td style="padding: 10px; text-align: right;">${row.cumulative_percentage}%</td>
                    </tr>
                `;
            });
            
            html += `
                            </tbody>
                        </table>
                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        })
        .catch(error => {
            console.error('Error loading common names:', error);
            container.innerHTML = `<p style="color: #e74c3c;">Failed to load common names</p>`;
        });
}

// Trigger download of common names
function downloadCommonNames(format) {
    if (!currentSheet) {
        alert('Please select a sheet first');
        return;
    }
    
    // Show loading state
    const statusMessage = document.createElement('div');
    statusMessage.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #3498db; color: white; padding: 15px 20px; border-radius: 8px; z-index: 9999;';
    statusMessage.textContent = `Generating ${format.toUpperCase()}... Please wait.`;
    document.body.appendChild(statusMessage);
    
    // Trigger download
    window.location.href = `/analytics/${currentSheet}/common_names/download/${format}`;
    
    // Remove status message after delay
    setTimeout(() => {
        statusMessage.remove();
    }, 3000);
}


// ==============================
// Comparison Section Functions
// ==============================

// Load the comparison section placeholder with a loading message
function loadComparison() {
    const container = document.getElementById('comparison-container');
    
    // Show loading
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Click "Load Comparison" to generate comparison analytics...</p>
        </div>
    `;
}

// Trigger the creation of comparison analytics via a POST request
function loadComparisonAnalytics() {
    const loadBtn = event.target;
    loadBtn.disabled = true; // prevent multiple clicks
    loadBtn.textContent = '⏳ Creating Comparison...';
    
    fetch('/comparison/create', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Failed to create comparison analytics');
            });
        }
        return response.json();
    })
    .then(data => {
        // Success - update button
        loadBtn.textContent = '✅ Comparison Ready';
        loadBtn.style.backgroundColor = '#95a5a6';
        
        // Load the comparison data
        loadComparisonSummary();
    })
    .catch(error => {
        console.error('Error creating comparison:', error);
        alert('Failed to create comparison analytics. Please ensure both JAN and APR sheets are processed first.');
        loadBtn.disabled = false;
        loadBtn.textContent = '📥 Load Comparison';
    });
}

// Load summary of the comparison data
function loadComparisonSummary() {
    const container = document.getElementById('comparison-container');
    
    // Show loading
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading comparison summary...</p>
        </div>
    `;
    
    fetch('/comparison/summary')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<p style="color: #e74c3c;">Error: ${data.error}</p>`;
                return;
            }
            // Render the comparison summary stats
            renderComparisonSummary(data);
        })
        .catch(error => {
            console.error('Error loading comparison summary:', error);
            container.innerHTML = `<p style="color: #e74c3c;">Failed to load comparison summary</p>`;
        });
}

// Render the comparison summary UI
function renderComparisonSummary(summary) {
    const container = document.getElementById('comparison-container');
    
    // Create HTML for summary stats (JAN/APR totals, unique, top 80%, etc.)
    let html = `
        <div style="padding: 20px;">
            <h3 style="color: #2c3e50; margin-bottom: 20px;">📊 Dataset Overview</h3>
            
            <div class="stats" style="margin-bottom: 30px;">
                <div class="stat-item">
                    <div class="stat-label">JAN Total Records</div>
                    <div class="stat-value">${(summary.jan_total_records || 0).toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">JAN Unique Names</div>
                    <div class="stat-value">${(summary.jan_unique_names || 0).toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">JAN Top 80% Names</div>
                    <div class="stat-value">${(summary.jan_top80_count || 0).toLocaleString()}</div>
                </div>
            </div>
            
            <div class="stats" style="margin-bottom: 30px;">
                <div class="stat-item">
                    <div class="stat-label">APR Total Records</div>
                    <div class="stat-value">${(summary.apr_total_records || 0).toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">APR Unique Names</div>
                    <div class="stat-value">${(summary.apr_unique_names || 0).toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">APR Top 80% Names</div>
                    <div class="stat-value">${(summary.apr_top80_count || 0).toLocaleString()}</div>
                </div>
            </div>
            
            <h3 style="color: #2c3e50; margin-bottom: 20px;">🔍 Comparison Results</h3>
            
            <div class="stats" style="margin-bottom: 30px;">
                <div class="stat-item">
                    <div class="stat-label">Common Names</div>
                    <div class="stat-value" style="color: #3498db;">${(summary.common_names_count || 0).toLocaleString()}</div>
                    <div style="font-size: 0.85rem; color: #7f8c8d; margin-top: 4px;">
                        ${(summary.common_names_pct_of_jan || 0)}% of JAN, ${(summary.common_names_pct_of_apr || 0)}% of APR
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Unique to JAN</div>
                    <div class="stat-value" style="color: #e74c3c;">${(summary.unique_jan_names_count || 0).toLocaleString()}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Unique to APR</div>
                    <div class="stat-value" style="color: #f39c12;">${(summary.unique_apr_names_count || 0).toLocaleString()}</div>
                </div>
            </div>
            
            <h3 style="color: #2c3e50; margin-bottom: 20px;">🏆 Top 80% Overlap Analysis</h3>
            
            <div class="stats" style="margin-bottom: 30px;">
                <div class="stat-item">
                    <div class="stat-label">JAN Top 80% in APR</div>
                    <div class="stat-value">${(summary.jan_top80_in_apr_count || 0).toLocaleString()}</div>
                    <div style="font-size: 0.85rem; color: #7f8c8d; margin-top: 4px;">
                        ${(summary.jan_top80_in_apr_pct || 0)}% of JAN's top 80%
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">APR Top 80% in JAN</div>
                    <div class="stat-value">${(summary.apr_top80_in_jan_count || 0).toLocaleString()}</div>
                    <div style="font-size: 0.85rem; color: #7f8c8d; margin-top: 4px;">
                        ${(summary.apr_top80_in_jan_pct || 0)}% of APR's top 80%
                    </div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">In Both Top 80%</div>
                    <div class="stat-value" style="color: #27ae60;">${(summary.both_top80_count || 0).toLocaleString()}</div>
                </div>
            </div>
            
            <h3 style="color: #2c3e50; margin-bottom: 20px;">📋 Detailed Views</h3>
            
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                <button onclick="loadComparisonCommonNames()" style="background-color: #3498db; padding: 10px 20px; border: none; color: white; border-radius: 6px; cursor: pointer;">
                    📄 View Common Names
                </button>
                <button onclick="loadComparisonUniqueJan()" style="background-color: #e74c3c; padding: 10px 20px; border: none; color: white; border-radius: 6px; cursor: pointer;">
                    📄 View Unique to JAN
                </button>
                <button onclick="loadComparisonUniqueApr()" style="background-color: #f39c12; padding: 10px 20px; border: none; color: white; border-radius: 6px; cursor: pointer;">
                    📄 View Unique to APR
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

// ==============================
// Detailed Comparison Tables
// ==============================

// Load Common Names table
function loadComparisonCommonNames() {
    currentComparisonState.view = 'common_names';
    currentComparisonState.page = 1;// reset page
    fetchComparisonData();
}

// Load Unique JAN Names table
function loadComparisonUniqueJan() {
    currentComparisonState.view = 'unique_jan';
    currentComparisonState.page = 1;
    fetchComparisonData();
}

// Load Unique APR Names table
function loadComparisonUniqueApr() {
    currentComparisonState.view = 'unique_apr';
    currentComparisonState.page = 1;
    fetchComparisonData();
}

// Fetch table data based on current state (view, page, filters)
function fetchComparisonData() {
    const container = document.getElementById('comparison-container');
    const { view, page, perPage, filterTop80, top80Only } = currentComparisonState;
    
    // Show loading spinner
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading data...</p>
        </div>
    `;
    
    // Build URL based on table type
    let url = '';
    if (view === 'common_names') {
        url = `/comparison/common_names?page=${page}&per_page=${perPage}`;
        if (filterTop80) url += `&filter_top80=${filterTop80}`;
    } else if (view === 'unique_jan') {
        url = `/comparison/unique_jan?page=${page}&per_page=${perPage}&top80_only=${top80Only}`;
    } else if (view === 'unique_apr') {
        url = `/comparison/unique_apr?page=${page}&per_page=${perPage}&top80_only=${top80Only}`;
    }
    
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<p style="color: #e74c3c;">Error: ${data.error}</p>`;
                return;
            }
            // Render table data
            renderComparisonTable(data);
        })
        .catch(error => {
            console.error('Error loading comparison data:', error);
            container.innerHTML = `<p style="color: #e74c3c;">Failed to load data</p>`;
        });
}


function renderComparisonTable(data) {
    // Get the container where the comparison table will be rendered
    const container = document.getElementById('comparison-container');

    // Get the current table view (common_names, unique_jan, unique_apr)
    const { view } = currentComparisonState;
    
    // Initialize variables for table title and dataset for download
    let title = '';
    let downloadDataset = '';
    
    // Set title and download dataset based on current view
    if (view === 'common_names') {
        title = 'Common Names (in both JAN and APR)';
        downloadDataset = 'common_names';
    } else if (view === 'unique_jan') {
        title = 'Names Unique to JAN';
        downloadDataset = 'unique_jan';
    } else {
        title = 'Names Unique to APR';
        downloadDataset = 'unique_apr';
    }
    
    // Start building the HTML for the table container
    let html = `
        <div style="padding: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="color: #2c3e50;">${title}</h3>
                <div style="display: flex; gap: 10px;">
                    <button onclick="loadComparisonSummary()" style="background-color: #95a5a6; padding: 8px 16px; border: none; color: white; border-radius: 6px; cursor: pointer;">
                        ← Back to Summary
                    </button>
                    <button onclick="downloadComparisonData('${downloadDataset}')" style="background-color: #27ae60; padding: 8px 16px; border: none; color: white; border-radius: 6px; cursor: pointer;">
                        📥 Download CSV
                    </button>
                </div>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse;">
    `;
    
    // Render table header & rows for common names
    if (view === 'common_names') {
        html += `
            <thead>
                <tr style="background: #34495e; color: white;">
                    <th style="padding: 12px; text-align: left;">Name</th>
                    <th style="padding: 12px; text-align: right;">JAN Frequency</th>
                    <th style="padding: 12px; text-align: right;">APR Frequency</th>
                    <th style="padding: 12px; text-align: right;">Total</th>
                    <th style="padding: 12px; text-align: center;">In JAN Top 80%</th>
                    <th style="padding: 12px; text-align: center;">In APR Top 80%</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        // Render each row of common names data
        data.data.forEach((row, index) => {
            const bgColor = index % 2 === 0 ? '#ffffff' : '#f8f9fa';
            html += `
                <tr style="background: ${bgColor}; border-bottom: 1px solid #ecf0f1;">
                    <td style="padding: 10px; font-weight: 500;">${escapeHtml(row.firstname)}</td>
                    <td style="padding: 10px; text-align: right;">${row.jan_frequency.toLocaleString()}</td>
                    <td style="padding: 10px; text-align: right;">${row.apr_frequency.toLocaleString()}</td>
                    <td style="padding: 10px; text-align: right;">${row.total_frequency.toLocaleString()}</td>
                    <td style="padding: 10px; text-align: center;">${row.in_jan_top80 ? '✓' : ''}</td>
                    <td style="padding: 10px; text-align: center;">${row.in_apr_top80 ? '✓' : ''}</td>
                </tr>
            `;
        });
    } else {
        // Unique JAN or APR
        const dataset = view === 'unique_jan' ? 'JAN' : 'APR';
        html += `
            <thead>
                <tr style="background: #34495e; color: white;">
                    <th style="padding: 12px; text-align: left;">Row #</th>
                    <th style="padding: 12px; text-align: left;">Name</th>
                    <th style="padding: 12px; text-align: left;">Birth Year</th>
                    <th style="padding: 12px; text-align: left;">Birth Month</th>
                    <th style="padding: 12px; text-align: left;">Birth Day</th>
                    <th style="padding: 12px; text-align: center;">In Top 80%</th>
                </tr>
            </thead>
            <tbody>
        `;
        
        // Render each row of unique names data
        data.data.forEach((row, index) => {
            const bgColor = index % 2 === 0 ? '#ffffff' : '#f8f9fa';
            const inTop80 = view === 'unique_jan' ? row.in_jan_top80 : row.in_apr_top80;
            html += `
                <tr style="background: ${bgColor}; border-bottom: 1px solid #ecf0f1;">
                    <td style="padding: 10px;">${row.original_row_number}</td>
                    <td style="padding: 10px; font-weight: 500;">${escapeHtml(row.firstname)}</td>
                    <td style="padding: 10px;">${row.birthyear || ''}</td>
                    <td style="padding: 10px;">${row.birthmonth || ''}</td>
                    <td style="padding: 10px;">${row.birthday || ''}</td>
                    <td style="padding: 10px; text-align: center;">${inTop80 ? '✓' : ''}</td>
                </tr>
            `;
        });
    }
    
    html += `
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Render pagination if multiple pages exist
    if (data.total_pages > 1) {
        renderComparisonPagination(data.page, data.total_pages, data.total_count);
    }
}

// Comparison Pagination Functions
function renderComparisonPagination(currentPage, totalPages, totalCount) {
    const container = document.getElementById('comparison-container');
    
    // Generate pagination controls
    let paginationHtml = `
        <div class="pagination" style="margin-top: 20px;">
            <button onclick="goToComparisonPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
                ← Previous
            </button>
            <div class="page-info">
                Page ${currentPage} of ${totalPages} (${totalCount} total)
            </div>
            <button onclick="goToComparisonPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
                Next →
            </button>
        </div>
    `;
    
    container.innerHTML += paginationHtml;
}

//navigate to comparison page
function goToComparisonPage(page) {
    currentComparisonState.page = page;
    fetchComparisonData();
}

// ==============================
// Comparison Download Function
// ==============================
function downloadComparisonData(dataset) {
    const { filterTop80, top80Only } = currentComparisonState;
    
    // Construct the download URL
    let url = `/comparison/download/${dataset}/csv`;
    
    if (dataset === 'common_names' && filterTop80) {
        url += `?filter_top80=${filterTop80}`;
    } else if ((dataset === 'unique_jan' || dataset === 'unique_apr') && top80Only) {
        url += `?top80_only=true`;
    }
    
    // Show loading state
    const statusMessage = document.createElement('div');
    statusMessage.style.cssText = 'position: fixed; top: 20px; right: 20px; background: #3498db; color: white; padding: 15px 20px; border-radius: 8px; z-index: 9999;';
    statusMessage.textContent = 'Generating CSV... Please wait.';
    document.body.appendChild(statusMessage);
    
    // Trigger download
    window.location.href = url;
    
    // Remove status message after delay
    setTimeout(() => {
        statusMessage.remove();
    }, 3000);
}

// Check if comparison tables exist
function checkComparisonTablesExist() {
    fetch('/comparison/check')
        .then(response => response.json())
        .then(data => {
            if (data.exists) {
                // Comparison tables exist - update button
                const comparisonBtn = document.querySelector('#comparison-section button[onclick*="loadComparisonAnalytics"]');
                if (comparisonBtn) {
                    comparisonBtn.disabled = true;
                    comparisonBtn.textContent = '✅ Comparison Ready';
                    comparisonBtn.style.backgroundColor = '#95a5a6';
                }
            }
        })
        .catch(err => {
            console.error('Error checking comparison tables:', err);
        });
}
// ==============================
// Apply filters to a specific table
// ==============================

function applyFilters(tableType) {
    // Get the values from the filter input fields
    const nameFilter = document.getElementById(`${tableType}-filter-name`).value;
    const monthFilter = document.getElementById(`${tableType}-filter-month`).value;
    const yearFilter = document.getElementById(`${tableType}-filter-year`).value;
    
    // Save the current filter state for this table
    currentFilters[tableType] = {
        name: nameFilter,
        month: monthFilter,
        year: yearFilter
    };
    
    // Reset to page 1 when filtering
    currentTableStates[tableType].page = 1;
    loadTableData(tableType);
}

// Clear filters
function clearFilters(tableType) {
    document.getElementById(`${tableType}-filter-name`).value = '';
    document.getElementById(`${tableType}-filter-month`).value = '';
    document.getElementById(`${tableType}-filter-year`).value = '';
    
    currentFilters[tableType] = { name: '', month: '', year: '' };
    currentTableStates[tableType].page = 1;
    loadTableData(tableType);
}

// Populate year filter dynamically
function populateYearFilter(tableType, years) {
    const yearSelect = document.getElementById(`${tableType}-filter-year`);
    if (!yearSelect) return;
    
    // Start with default "All Years" option
    yearSelect.innerHTML = '<option value="">All Years</option>';
    years.forEach(year => {
        yearSelect.innerHTML += `<option value="${year}">${year}</option>`;
    });
}


// ==============================
// Initialize sheet status and comparison checks on DOM load
// ==============================


document.addEventListener('DOMContentLoaded', function() {
    // Get all sheet keys from the page
    const sheetCards = document.querySelectorAll('.sheet-card');
    
    sheetCards.forEach(card => {
        const processBtn = card.querySelector('.btn-process');
        const viewBtn = card.querySelector('.btn-view');
        const sheetKey = processBtn.getAttribute('onclick').match(/'([^']+)'/)[1];
        
        // Check if tables exist for this sheet
        fetch(`/check_tables/${sheetKey}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.exists) {
                    // Tables exist - disable process, enable view
                    processBtn.disabled = true;
                    processBtn.textContent = '✅ Already Processed';
                    processBtn.style.backgroundColor = '#95a5a6';
                    
                    viewBtn.disabled = false;
                    
                    // Show row counts in status
                    const statusBox = document.getElementById(`status-${sheetKey}`);
                    statusBox.className = 'status-box show success';
                    statusBox.innerHTML = `
                        <p><strong>✅ Data Already Processed</strong></p>
                        <div class="stats">
                            <div class="stat-item">
                                <div class="stat-label">Total Rows</div>
                                <div class="stat-value">${data.counts.original.toLocaleString()}</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">Included</div>
                                <div class="stat-value" style="color: #27ae60;">${data.counts.included.toLocaleString()}</div>
                                <div class="stat-value" style="color: #131315ff; font-size: 12px;">${((data.counts.included / data.counts.original) * 100).toFixed(1)}%</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-label">Excluded</div>
                                <div class="stat-value" style="color: #e74c3c;">${data.counts.excluded.toLocaleString()}</div>
                                <div class="stat-value" style="color: #131315ff; font-size: 12px;">${((data.counts.excluded / data.counts.original) * 100).toFixed(1)}%</div>
                            </div>
                        </div>
                    `;
                }

                // Check if analytics table exists for this sheet
                if (data.analytics_exists) {
                    // Find all "Load Analytics" buttons in different sections
                    const analyticsSections = ['#summary_stats-section', '#duplicates-section', '#charts-section', '#common_names-section'];
                    
                    analyticsSections.forEach(sectionId => {
                        const section = document.querySelector(sectionId);
                        if (section) {
                            const analyticsBtn = section.querySelector('button[onclick*="loadanalytics"]');
                            if (analyticsBtn) {
                                analyticsBtn.textContent = '✅ Load Analytics';
                                analyticsBtn.style.backgroundColor = '#95a5a6';
                            }
                        }
                    });
                }
            })
            .catch(err => {
                console.error(`Error checking tables for ${sheetKey}:`, err);
            });
    });
    
    // Check if comparison tables exist (after both sheets are loaded)
    setTimeout(() => {
        checkComparisonTablesExist();
    }, 1000); // Give time for sheet checks to complete
});