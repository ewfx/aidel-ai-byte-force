document.addEventListener('DOMContentLoaded', function() {
    // Initialize DataTables
    initDataTables();
    
    // Set up table filters and export functionality
    setupTableControls();
});

/**
 * Initialize DataTables for all tables with the datatable class
 */
function initDataTables() {
    // Entity table
    const entityTable = document.querySelector('.table.entity-table');
    if (entityTable) {
        // Initialize with DataTables
        const dataTable = new DataTable(entityTable, {
            pageLength: 10,
            order: [[5, 'desc']], // Sort by risk score by default
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
            responsive: true,
            dom: 'Bfrtip',
            buttons: [
                'copy', 'csv', 'excel', 'pdf'
            ],
            columnDefs: [
                // Format risk score column with color-coding
                {
                    targets: 'risk-score-column',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            let colorClass = '';
                            const score = parseFloat(data);
                            
                            if (score >= 0.8) {
                                colorClass = 'bg-danger text-white';
                            } else if (score >= 0.6) {
                                colorClass = 'bg-warning';
                            } else if (score >= 0.4) {
                                colorClass = 'bg-info';
                            } else {
                                colorClass = 'bg-success text-white';
                            }
                            
                            return `<span class="badge ${colorClass}" style="width: 100%">${score.toFixed(2)}</span>`;
                        }
                        return data;
                    }
                },
                // Format entity type column
                {
                    targets: 'entity-type-column',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            let badgeClass = '';
                            
                            switch(data) {
                                case 'corporation':
                                    badgeClass = 'bg-primary';
                                    break;
                                case 'non-profit':
                                    badgeClass = 'bg-success';
                                    break;
                                case 'financial_intermediary':
                                    badgeClass = 'bg-info';
                                    break;
                                case 'shell_company':
                                    badgeClass = 'bg-danger';
                                    break;
                                default:
                                    badgeClass = 'bg-secondary';
                            }
                            
                            return `<span class="badge ${badgeClass}">${data}</span>`;
                        }
                        return data;
                    }
                }
            ]
        });
        
        // Add custom search functionality
        document.getElementById('entity-search-input')?.addEventListener('keyup', function() {
            dataTable.search(this.value).draw();
        });
    }
    
    // Transaction table
    const transactionTable = document.querySelector('.table.transaction-table');
    if (transactionTable) {
        new DataTable(transactionTable, {
            pageLength: 10,
            order: [[4, 'desc']], // Sort by amount by default
            lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "All"]],
            responsive: true,
            dom: 'Bfrtip',
            buttons: [
                'copy', 'csv', 'excel', 'pdf'
            ],
            columnDefs: [
                // Format amount column
                {
                    targets: 'amount-column',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            return parseFloat(data).toLocaleString('en-US', {
                                style: 'currency',
                                currency: row[5] || 'USD'
                            });
                        }
                        return data;
                    }
                },
                // Format date column
                {
                    targets: 'date-column',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            return new Date(data).toLocaleDateString();
                        }
                        return data;
                    }
                }
            ]
        });
    }
    
    // Evidence table
    const evidenceTable = document.querySelector('.table.evidence-table');
    if (evidenceTable) {
        new DataTable(evidenceTable, {
            pageLength: 5,
            order: [[2, 'desc']], // Sort by confidence by default
            lengthMenu: [[5, 10, 25, -1], [5, 10, 25, "All"]],
            responsive: true,
            columnDefs: [
                // Format confidence column
                {
                    targets: 'confidence-column',
                    render: function(data, type, row) {
                        if (type === 'display') {
                            const confidence = parseFloat(data);
                            const width = (confidence * 100) + '%';
                            
                            let barClass = 'bg-success';
                            if (confidence < 0.4) {
                                barClass = 'bg-danger';
                            } else if (confidence < 0.7) {
                                barClass = 'bg-warning';
                            }
                            
                            return `
                                <div class="progress">
                                    <div class="progress-bar ${barClass}" role="progressbar" 
                                         style="width: ${width}" aria-valuenow="${confidence * 100}" 
                                         aria-valuemin="0" aria-valuemax="100">
                                        ${(confidence * 100).toFixed(0)}%
                                    </div>
                                </div>
                            `;
                        }
                        return data;
                    }
                }
            ]
        });
    }
}

/**
 * Set up table filters and export functionality
 */
function setupTableControls() {
    // Entity type filter
    const entityTypeFilter = document.getElementById('entity-type-filter');
    if (entityTypeFilter) {
        entityTypeFilter.addEventListener('change', function() {
            const selectedType = this.value;
            
            // Get the datatable instance
            const table = DataTable.tables({ visible: true, api: true }).tables()[0];
            
            // Clear search and then apply the filter
            table.search('').columns(1).search(selectedType !== 'all' ? selectedType : '').draw();
        });
    }
    
    // Risk level filter
    const riskLevelFilter = document.getElementById('risk-level-filter');
    if (riskLevelFilter) {
        riskLevelFilter.addEventListener('change', function() {
            const selectedLevel = this.value;
            const table = DataTable.tables({ visible: true, api: true }).tables()[0];
            
            // Apply custom filtering for risk levels
            table.columns(5).search('').draw();
            
            if (selectedLevel !== 'all') {
                table.rows().every(function() {
                    const data = this.data();
                    const riskScore = parseFloat(data[5]);
                    
                    let visible = false;
                    switch(selectedLevel) {
                        case 'very-high':
                            visible = riskScore >= 0.8;
                            break;
                        case 'high':
                            visible = riskScore >= 0.6 && riskScore < 0.8;
                            break;
                        case 'medium':
                            visible = riskScore >= 0.4 && riskScore < 0.6;
                            break;
                        case 'low':
                            visible = riskScore >= 0.2 && riskScore < 0.4;
                            break;
                        case 'very-low':
                            visible = riskScore < 0.2;
                            break;
                    }
                    
                    this.node().style.display = visible ? '' : 'none';
                });
            }
        });
    }
    
    // Date range filter
    const dateFilterBtn = document.getElementById('date-filter-btn');
    if (dateFilterBtn) {
        dateFilterBtn.addEventListener('click', function() {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            
            if (!startDate || !endDate) {
                alert('Please enter both start and end dates');
                return;
            }
            
            const start = new Date(startDate);
            const end = new Date(endDate);
            
            // Check for valid dates
            if (isNaN(start.getTime()) || isNaN(end.getTime())) {
                alert('Please enter valid dates');
                return;
            }
            
            if (start > end) {
                alert('Start date must be before end date');
                return;
            }
            
            // Apply date filter to the transaction table
            const table = DataTable.tables({ visible: true, api: true }).tables()[0];
            
            // Apply custom filtering
            table.rows().every(function() {
                const data = this.data();
                const dateCol = data[3]; // Assuming the 4th column is the date column
                const rowDate = new Date(dateCol);
                
                this.node().style.display = (rowDate >= start && rowDate <= end) ? '' : 'none';
            });
        });
    }
    
    // Reset filters
    const resetFiltersBtn = document.getElementById('reset-filters-btn');
    if (resetFiltersBtn) {
        resetFiltersBtn.addEventListener('click', function() {
            // Reset all filter inputs
            const entityTypeFilter = document.getElementById('entity-type-filter');
            const riskLevelFilter = document.getElementById('risk-level-filter');
            const startDateInput = document.getElementById('start-date');
            const endDateInput = document.getElementById('end-date');
            const searchInput = document.getElementById('entity-search-input');
            
            if (entityTypeFilter) entityTypeFilter.value = 'all';
            if (riskLevelFilter) riskLevelFilter.value = 'all';
            if (startDateInput) startDateInput.value = '';
            if (endDateInput) endDateInput.value = '';
            if (searchInput) searchInput.value = '';
            
            // Reset the table
            const table = DataTable.tables({ visible: true, api: true }).tables()[0];
            table.search('').columns().search('').draw();
            
            // Reset custom styling
            table.rows().every(function() {
                this.node().style.display = '';
            });
        });
    }
}

/**
 * Export table data to CSV
 * @param {string} tableId - ID of the table to export
 * @param {string} filename - Filename for the exported CSV
 */
function exportTableToCSV(tableId, filename) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    let csv = [];
    
    for (let i = 0; i < rows.length; i++) {
        let row = [], cols = rows[i].querySelectorAll('td, th');
        
        for (let j = 0; j < cols.length; j++) {
            // Get the text content
            let text = cols[j].textContent.trim();
            // Escape double quotes
            text = text.replace(/"/g, '""');
            // Add quotes around the field
            row.push('"' + text + '"');
        }
        
        csv.push(row.join(','));
    }
    
    // Create CSV file
    const csvContent = csv.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    
    // Create download link
    const a = document.createElement('a');
    a.setAttribute('hidden', '');
    a.setAttribute('href', url);
    a.setAttribute('download', filename + '.csv');
    document.body.appendChild(a);
    
    // Trigger download
    a.click();
    document.body.removeChild(a);
}
