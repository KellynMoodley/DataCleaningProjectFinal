// Global state
let currentSheet = null;
let currentTableStates = {
    original: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
    included: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
    excluded: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' }
};

// Process a sheet
function processSheet(sheetKey) {
    const statusBox = document.getElementById(`status-${sheetKey}`);
    const processBtn = event.target;
    const viewBtn = document.getElementById(`view-btn-${sheetKey}`);
    
    // Disable buttons
    processBtn.disabled = true;
    processBtn.textContent = '⏳ Processing...';
    
    // Show loading status
    statusBox.className = 'status-box show';
    statusBox.innerHTML = `
        <div style="text-align: center;">
            <div class="spinner" style="margin: 0 auto 12px;"></div>
            <p><strong>Processing sheet...</strong></p>
            <p style="margin-top: 8px; font-size: 0.9rem;">This may take a few minutes for large datasets.</p>
        </div>
    `;
    
    // Make POST request to process the sheet
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
        
        // Show success status with stats
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
        
        // Enable view button
        viewBtn.disabled = false;
        // Inside processSheet() function, in the success handler after viewBtn.disabled = false;
        processBtn.disabled = true;
        processBtn.textContent = '✅ Already Processed';
        processBtn.style.backgroundColor = '#95a5a6';
        
        // Store current sheet
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

// View sheet data
function viewSheetData(sheetKey) {
    currentSheet = sheetKey;
    
    // Show data display section
    document.getElementById('data-display').style.display = 'block';
    
    // Scroll to data display
    document.getElementById('data-display').scrollIntoView({ behavior: 'smooth' });
    
    // Reset table states
    currentTableStates = {
        original: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
        included: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' },
        excluded: { page: 1, perPage: 100, sortBy: 'original_row_number', sortOrder: 'asc' }
    };
    
    // Load data for all tables
    switchTab('original');
}

// Switch between tabs
function switchTab(tableType) {
    // Update tab active state for main tabs only
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
        
        // Load data based on section type
        if (tableType === 'original' || tableType === 'included' || tableType === 'excluded') {
            loadTableData(tableType);
        } else if (tableType === 'summary_stats') {
            loadAnalyticsSummary();
        } else if (tableType === 'duplicates') {
            loadDuplicates('name_year');
        } else if (tableType === 'charts') {
            loadChart('birthyear');
        }
    }
}

// Load table data
function loadTableData(tableType) {
    if (!currentSheet) return;
    
    const state = currentTableStates[tableType];
    const container = document.getElementById(`${tableType}-table-container`);
    
    // Show loading
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading data...</p>
        </div>
    `;
    
    // Fetch data
    const url = `/data/${currentSheet}/${tableType}?page=${state.page}&per_page=${state.perPage}&sort_by=${state.sortBy}&sort_order=${state.sortOrder}`;
    
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
        
        // Render table
        renderTable(tableType, data.data);
        
        // Render pagination
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

// Render table
function renderTable(tableType, data) {
    const container = document.getElementById(`${tableType}-table-container`);
    
    if (!data || data.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 40px; color: #7f8c8d;">No data available</p>';
        return;
    }
    
    // Define column order based on table type
    let columns;
    if (tableType === 'included') {
        columns = ['original_row_number', 'row_id', 'firstname', 'birthday', 'birthmonth', 'birthyear'];
    } else if (tableType === 'excluded') {
        columns = ['original_row_number', 'row_id', 'firstname', 'birthday', 'birthmonth', 'birthyear', 'exclusion_reason'];
    } else {
        columns = ['original_row_number', 'row_id', 'firstname', 'birthday', 'birthmonth', 'birthyear', 'exclusion_reason', 'status'];
    }
    
    // Filter columns to only include those that exist in the data
    columns = columns.filter(col => col in data[0]);
    
    const state = currentTableStates[tableType];
    
    // Build table HTML
    let html = '<table><thead><tr>';
    
    columns.forEach(col => {
        const sortIndicator = state.sortBy === col ? 
            (state.sortOrder === 'asc' ? '▲' : '▼') : '';
        html += `<th onclick="sortTable('${tableType}', '${col}')">${formatColumnName(col)} <span class="sort-indicator">${sortIndicator}</span></th>`;
    });
    
    html += '</tr></thead><tbody>';
    
    // Add rows
    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
            let value = row[col];
            if (value === null || value === undefined) {
                value = '';
            }
            // Truncate long text
            if (typeof value === 'string' && value.length > 100) {
                value = value.substring(0, 100) + '...';
            }
            html += `<td>${escapeHtml(String(value))}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    
    container.innerHTML = html;
}

// Render pagination
function renderPagination(tableType, currentPage, totalPages, totalCount) {
    const container = document.getElementById(`${tableType}-pagination`);
    
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

// Sort table
function sortTable(tableType, column) {
    const state = currentTableStates[tableType];
    
    // Toggle sort order if same column, otherwise default to asc
    if (state.sortBy === column) {
        state.sortOrder = state.sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        state.sortBy = column;
        state.sortOrder = 'asc';
    }
    
    // Reset to page 1
    state.page = 1;
    
    // Reload data
    loadTableData(tableType);
}

// Go to page
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

// Utility functions
function formatColumnName(name) {
    return name
        .replace(/_/g, ' ')
        .replace(/\b\w/g, l => l.toUpperCase());
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Download table data
function downloadTable(tableType, format) {
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
    window.location.href = `/download/${currentSheet}/${tableType}/${format}`;
    
    // Remove status message after delay
    setTimeout(() => {
        statusMessage.remove();
    }, 3000);
}


//analytics section 
function loadAnalyticsData() {
    if (!currentSheet) return;
    
    // Load summary first (fast)
    loadAnalyticsSummary();
    
    // Load distributions (medium speed)
    loadAnalyticsDistributions();
    
    // Load duplicates last (slow)
    loadAnalyticsDuplicates();
}

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
        
        // Load the analytics data
        loadAnalyticsData();
    })
    .catch(error => {
        console.error('Error creating analytics:', error);
        alert('Failed to create analytics. Please try again.');
        loadBtn.disabled = false;
        loadBtn.textContent = '📥 Load analytics';
    });
}


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

// Global chart instance
let chartInstance = null;

// State for duplicates
let currentDuplicatesState = {
    groupType: 'name_year',
    page: 1,
    perPage: 50
};


function loadAnalyticsDistributions() {
    // Load default chart
    loadChart('birthyear');
}

function loadAnalyticsDuplicates() {
    // Load default duplicates
    loadDuplicates('name_year');
}

function loadDuplicates(groupType) {
    if (!currentSheet) return;
    
    currentDuplicatesState.groupType = groupType;
    currentDuplicatesState.page = 1;
    
    // Update tab active state for duplicate tabs
    const duplicateTabs = document.querySelectorAll('#duplicates-section .tabs .tab');
    duplicateTabs.forEach(tab => tab.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    fetchDuplicates();
}

function fetchDuplicates() {
    const container = document.getElementById('duplicates-container');
    const { groupType, page, perPage } = currentDuplicatesState;
    
    container.innerHTML = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Loading duplicates...</p>
        </div>
    `;
    
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

function renderDuplicates(duplicates, groupType) {
    const container = document.getElementById('duplicates-container');
    
    if (!duplicates || duplicates.length === 0) {
        container.innerHTML = `<p style="text-align: center; padding: 20px; color: #7f8c8d;">No duplicates found</p>`;
        return;
    }
    
    let html = '<div style="padding: 20px;">';
    
    duplicates.forEach(dup => {
        let label = '';
        
        if (groupType === 'name_year') {
            label = `${escapeHtml(dup.firstname)} - ${dup.birthyear}`;
        } else if (groupType === 'name_month') {
            label = `${escapeHtml(dup.firstname)} - Month ${dup.birthmonth}`;
        } else if (groupType === 'name_day') {
            label = `${escapeHtml(dup.firstname)} - Day ${dup.birthday}`;
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

function goToDuplicatesPage(page) {
    currentDuplicatesState.page = page;
    fetchDuplicates();
}

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
    
    fetch(`/analytics/${currentSheet}/charts/${chartType}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                container.innerHTML = `<p style="color: #e74c3c;">Error: ${data.error}</p>`;
                return;
            }
            
            // Restore canvas
            container.innerHTML = '<canvas id="analytics-chart" style="max-height: 400px;"></canvas>';
            renderChart(data.data, chartType);
        })
        .catch(error => {
            console.error('Error loading chart:', error);
            container.innerHTML = `<p style="color: #e74c3c;">Failed to load chart</p>`;
        });
}

function renderChart(data, chartType) {
    const canvas = document.getElementById('analytics-chart');
    
    if (!data || data.length === 0) {
        const container = document.getElementById('chart-container');
        container.innerHTML = `<p style="text-align: center; padding: 20px; color: #7f8c8d;">No data available</p>`;
        return;
    }
    
    // Destroy existing chart if it exists
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


// Check table status on page load
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

                if (data.analytics_exists) {  // Add this field from backend
                   const analyticsBtn = document.querySelector('#analytics-section button[onclick*="loadanalytics"]');
                   if (analyticsBtn) {
                       analyticsBtn.disabled = true;
                       analyticsBtn.textContent = '✅ Analytics Ready';
                       analyticsBtn.style.backgroundColor = '#95a5a6';
                   }
                }
            })
            .catch(err => {
                console.error(`Error checking tables for ${sheetKey}:`, err);
            });
    });
});