document.addEventListener('DOMContentLoaded', function() {
    // Initialize the dashboard
    initDashboard();
    
    // Set up event listeners
    setupEventListeners();
});

/**
 * Initialize the dashboard components
 */
function initDashboard() {
    // Load risk distribution chart
    loadRiskDistributionChart();
    
    // Load entity type chart
    loadEntityTypeChart();
    
    // Load transaction volume chart
    loadTransactionVolumeChart();
    
    // Initialize the entity network graph if the container exists
    const networkContainer = document.getElementById('entity-network-graph');
    if (networkContainer) {
        loadEntityNetwork();
    }
}

/**
 * Set up event listeners for dashboard interactivity
 */
function setupEventListeners() {
    // Risk threshold slider
    const riskSlider = document.getElementById('risk-threshold');
    if (riskSlider) {
        riskSlider.addEventListener('input', function() {
            const threshold = parseFloat(this.value);
            document.getElementById('threshold-value').textContent = threshold.toFixed(1);
            filterEntitiesByRisk(threshold);
        });
    }
    
    // Search input
    const searchInput = document.getElementById('entity-search');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            searchEntities(searchTerm);
        });
    }
    
    // Date range filters
    const dateRangeBtn = document.getElementById('date-range-apply');
    if (dateRangeBtn) {
        dateRangeBtn.addEventListener('click', function() {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            filterByDateRange(startDate, endDate);
        });
    }
}

/**
 * Load the risk distribution chart
 */
function loadRiskDistributionChart() {
    const ctx = document.getElementById('risk-distribution-chart');
    if (!ctx) return;
    
    // Fetch risk score data
    fetch('/api/risk-distribution')
        .then(response => response.json())
        .then(data => {
            // Create risk distribution chart
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Very Low', 'Low', 'Medium', 'High', 'Very High'],
                    datasets: [{
                        label: 'Entities by Risk Level',
                        data: data.distribution,
                        backgroundColor: [
                            'rgba(40, 167, 69, 0.7)',  // success green
                            'rgba(23, 162, 184, 0.7)', // info blue
                            'rgba(255, 193, 7, 0.7)',  // warning yellow
                            'rgba(220, 53, 69, 0.7)',  // danger red
                            'rgba(108, 17, 17, 0.7)'   // dark red
                        ],
                        borderColor: [
                            'rgb(40, 167, 69)',
                            'rgb(23, 162, 184)',
                            'rgb(255, 193, 7)',
                            'rgb(220, 53, 69)',
                            'rgb(108, 17, 17)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Number of Entities'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Risk Level'
                            }
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.raw} entities`;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading risk distribution data:', error);
            ctx.innerHTML = '<p class="text-danger">Error loading chart data</p>';
        });
}

/**
 * Load the entity type distribution chart
 */
function loadEntityTypeChart() {
    const ctx = document.getElementById('entity-type-chart');
    if (!ctx) return;
    
    // Fetch entity type data
    fetch('/api/entity-types')
        .then(response => response.json())
        .then(data => {
            // Create entity type pie chart
            new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: data.types,
                    datasets: [{
                        data: data.counts,
                        backgroundColor: [
                            'rgba(13, 110, 253, 0.7)',  // primary blue
                            'rgba(23, 162, 184, 0.7)',  // info blue
                            'rgba(255, 193, 7, 0.7)',   // warning yellow
                            'rgba(220, 53, 69, 0.7)',   // danger red
                            'rgba(108, 117, 125, 0.7)'  // secondary gray
                        ],
                        borderColor: [
                            'rgb(13, 110, 253)',
                            'rgb(23, 162, 184)',
                            'rgb(255, 193, 7)',
                            'rgb(220, 53, 69)',
                            'rgb(108, 117, 125)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const label = context.label || '';
                                    const value = context.raw || 0;
                                    const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                    const percentage = Math.round((value / total) * 100);
                                    return `${label}: ${value} (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading entity type data:', error);
            ctx.innerHTML = '<p class="text-danger">Error loading chart data</p>';
        });
}

/**
 * Load the transaction volume chart
 */
function loadTransactionVolumeChart() {
    const ctx = document.getElementById('transaction-volume-chart');
    if (!ctx) return;
    
    // Fetch transaction volume data
    fetch('/api/transaction-volume')
        .then(response => response.json())
        .then(data => {
            // Create transaction volume line chart
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [{
                        label: 'Transaction Volume',
                        data: data.volumes,
                        borderColor: 'rgb(13, 110, 253)',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Volume'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    }
                }
            });
        })
        .catch(error => {
            console.error('Error loading transaction volume data:', error);
            ctx.innerHTML = '<p class="text-danger">Error loading chart data</p>';
        });
}

/**
 * Filter entities by risk score threshold
 */
function filterEntitiesByRisk(threshold) {
    const entityRows = document.querySelectorAll('.entity-row');
    
    entityRows.forEach(row => {
        const riskScore = parseFloat(row.dataset.riskScore || 0);
        
        if (riskScore >= threshold) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update counts
    const visibleCount = Array.from(entityRows).filter(row => row.style.display !== 'none').length;
    const totalCount = entityRows.length;
    
    const countElement = document.getElementById('entity-count');
    if (countElement) {
        countElement.textContent = `Showing ${visibleCount} of ${totalCount} entities`;
    }
}

/**
 * Search entities by name or other attributes
 */
function searchEntities(searchTerm) {
    const entityRows = document.querySelectorAll('.entity-row');
    
    entityRows.forEach(row => {
        const entityName = (row.dataset.entityName || '').toLowerCase();
        const entityType = (row.dataset.entityType || '').toLowerCase();
        
        if (entityName.includes(searchTerm) || entityType.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
    
    // Update counts
    const visibleCount = Array.from(entityRows).filter(row => row.style.display !== 'none').length;
    const totalCount = entityRows.length;
    
    const countElement = document.getElementById('entity-count');
    if (countElement) {
        countElement.textContent = `Showing ${visibleCount} of ${totalCount} entities`;
    }
}

/**
 * Filter data by date range
 */
function filterByDateRange(startDate, endDate) {
    // Convert to Date objects
    const start = new Date(startDate);
    const end = new Date(endDate);
    
    // Validate dates
    if (isNaN(start.getTime()) || isNaN(end.getTime())) {
        alert('Please enter valid dates');
        return;
    }
    
    if (start > end) {
        alert('Start date must be before end date');
        return;
    }
    
    // Update charts with filtered data
    // This would typically involve re-fetching data with the date range
    // For this example, we'll just show an alert
    alert(`Filtering data from ${startDate} to ${endDate}`);
    
    // In a real implementation, you would make API calls with the date range
    // and refresh the visualizations with the new data
}

/**
 * Export dashboard data as CSV
 */
function exportDashboardData() {
    // In a real implementation, you would make an API call to get the data
    // and then convert it to CSV format
    alert('Exporting dashboard data...');
    
    // Redirect to an export endpoint
    window.location.href = '/api/export-dashboard-data';
}
