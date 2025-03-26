document.addEventListener('DOMContentLoaded', function() {
    // Set up report generation functionality
    setupReportGenerator();
    
    // Initialize any existing report visualizations
    initReportVisualizations();
});

/**
 * Set up report generation form and event handlers
 */
function setupReportGenerator() {
    const reportForm = document.getElementById('report-generator-form');
    if (!reportForm) return;
    
    reportForm.addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Show loading indicator
        const submitBtn = reportForm.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating...';
        submitBtn.disabled = true;
        
        // Get form data
        const formData = new FormData(reportForm);
        
        // Send request to generate report
        fetch('/generate-report', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Error generating report');
            }
            return response.json();
        })
        .then(data => {
            // Reset form
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
            
            // Show success message
            const alert = document.createElement('div');
            alert.className = 'alert alert-success';
            alert.innerHTML = `
                <h4>Report Generated Successfully</h4>
                <p>Your report has been generated and is now available.</p>
                <a href="/view-report/${data.report_id}" class="btn btn-primary">View Report</a>
            `;
            
            // Insert alert before the form
            reportForm.parentNode.insertBefore(alert, reportForm);
            
            // Hide alert after 5 seconds
            setTimeout(() => {
                alert.remove();
            }, 5000);
        })
        .catch(error => {
            console.error('Error:', error);
            
            // Reset button
            submitBtn.innerHTML = originalBtnText;
            submitBtn.disabled = false;
            
            // Show error message
            const alert = document.createElement('div');
            alert.className = 'alert alert-danger';
            alert.innerHTML = `
                <h4>Error Generating Report</h4>
                <p>${error.message}</p>
            `;
            
            // Insert alert before the form
            reportForm.parentNode.insertBefore(alert, reportForm);
            
            // Hide alert after 5 seconds
            setTimeout(() => {
                alert.remove();
            }, 5000);
        });
    });
    
    // Handle report type selection changes
    const reportTypeSelect = document.getElementById('report-type');
    const entitySelect = document.getElementById('entity-select');
    const dateRangeFields = document.getElementById('date-range-fields');
    
    if (reportTypeSelect && entitySelect && dateRangeFields) {
        reportTypeSelect.addEventListener('change', function() {
            if (this.value === 'single_entity') {
                entitySelect.style.display = 'block';
                dateRangeFields.style.display = 'none';
            } else if (this.value === 'date_range') {
                entitySelect.style.display = 'none';
                dateRangeFields.style.display = 'block';
            } else {
                entitySelect.style.display = 'none';
                dateRangeFields.style.display = 'none';
            }
        });
    }
}

/**
 * Initialize visualizations for an existing report
 */
function initReportVisualizations() {
    const reportContent = document.getElementById('report-content');
    if (!reportContent) return;
    
    // Try to parse report data if available
    const reportDataElement = document.getElementById('report-data');
    if (!reportDataElement) return;
    
    try {
        const reportData = JSON.parse(reportDataElement.textContent);
        
        // Render visualizations based on report type
        if (reportData.report_type === 'All Entities Risk Assessment') {
            renderRiskDistributionChart(reportData);
            renderEntityTypeChart(reportData);
            renderTopRiskEntitiesTable(reportData);
        } else if (reportData.report_type === 'Single Entity Analysis') {
            renderEntityTimeline(reportData);
            renderRiskFactorBreakdown(reportData);
        } else if (reportData.report_type === 'Transaction Analysis') {
            renderTransactionVolumeChart(reportData);
            renderTransactionNetworkChart(reportData);
        }
        
    } catch (error) {
        console.error('Error parsing report data:', error);
    }
}

/**
 * Render risk distribution chart for a report
 */
function renderRiskDistributionChart(reportData) {
    const container = document.getElementById('risk-distribution-chart');
    if (!container) return;
    
    // Process data for the chart
    const entities = reportData.entities || [];
    const riskCategories = {
        'Very Low Risk': 0,
        'Low Risk': 0,
        'Medium Risk': 0,
        'High Risk': 0,
        'Very High Risk': 0
    };
    
    // Categorize entities by risk score
    entities.forEach(entity => {
        const score = entity.risk_score || 0;
        
        if (score >= 0.8) {
            riskCategories['Very High Risk']++;
        } else if (score >= 0.6) {
            riskCategories['High Risk']++;
        } else if (score >= 0.4) {
            riskCategories['Medium Risk']++;
        } else if (score >= 0.2) {
            riskCategories['Low Risk']++;
        } else {
            riskCategories['Very Low Risk']++;
        }
    });
    
    // Create chart
    const ctx = container.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: Object.keys(riskCategories),
            datasets: [{
                label: 'Number of Entities',
                data: Object.values(riskCategories),
                backgroundColor: [
                    'rgba(40, 167, 69, 0.7)',  // very low - green
                    'rgba(23, 162, 184, 0.7)', // low - blue
                    'rgba(255, 193, 7, 0.7)',  // medium - yellow
                    'rgba(255, 153, 0, 0.7)',  // high - orange
                    'rgba(220, 53, 69, 0.7)'   // very high - red
                ],
                borderColor: [
                    'rgb(40, 167, 69)',
                    'rgb(23, 162, 184)',
                    'rgb(255, 193, 7)',
                    'rgb(255, 153, 0)',
                    'rgb(220, 53, 69)'
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
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Entity Risk Distribution'
                }
            }
        }
    });
}

/**
 * Render entity type distribution chart
 */
function renderEntityTypeChart(reportData) {
    const container = document.getElementById('entity-type-chart');
    if (!container) return;
    
    // Process data for the chart
    const entities = reportData.entities || [];
    const entityTypes = {};
    
    // Count entity types
    entities.forEach(entity => {
        const type = entity.type || 'unknown';
        entityTypes[type] = (entityTypes[type] || 0) + 1;
    });
    
    // Create chart
    const ctx = container.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: Object.keys(entityTypes),
            datasets: [{
                data: Object.values(entityTypes),
                backgroundColor: [
                    'rgba(13, 110, 253, 0.7)',   // primary blue
                    'rgba(220, 53, 69, 0.7)',    // danger red
                    'rgba(40, 167, 69, 0.7)',    // success green
                    'rgba(255, 193, 7, 0.7)',    // warning yellow
                    'rgba(108, 117, 125, 0.7)'   // secondary gray
                ],
                borderColor: [
                    'rgb(13, 110, 253)',
                    'rgb(220, 53, 69)',
                    'rgb(40, 167, 69)',
                    'rgb(255, 193, 7)',
                    'rgb(108, 117, 125)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Entity Type Distribution'
                },
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

/**
 * Render table of top risk entities
 */
function renderTopRiskEntitiesTable(reportData) {
    const container = document.getElementById('top-risk-entities');
    if (!container) return;
    
    // Process data for the table
    const entities = reportData.entities || [];
    
    // Sort entities by risk score (descending)
    const sortedEntities = [...entities].sort((a, b) => 
        (b.risk_score || 0) - (a.risk_score || 0)
    );
    
    // Take top 10 entities
    const topEntities = sortedEntities.slice(0, 10);
    
    // Create table HTML
    let tableHtml = `
        <table class="table table-striped table-hover">
            <thead>
                <tr>
                    <th>Entity Name</th>
                    <th>Type</th>
                    <th>Risk Score</th>
                    <th>Key Risk Factors</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    // Add rows for each entity
    topEntities.forEach(entity => {
        const riskScore = entity.risk_score || 0;
        let scoreClass = '';
        
        if (riskScore >= 0.8) {
            scoreClass = 'bg-danger text-white';
        } else if (riskScore >= 0.6) {
            scoreClass = 'bg-warning';
        } else if (riskScore >= 0.4) {
            scoreClass = 'bg-info';
        } else {
            scoreClass = 'bg-success text-white';
        }
        
        // Get top 3 risk factors
        const riskFactors = entity.risk_factors || [];
        const topFactors = riskFactors.slice(0, 3).map(factor => factor.factor || '').join(', ');
        
        tableHtml += `
            <tr>
                <td>${entity.name}</td>
                <td><span class="badge bg-secondary">${entity.type}</span></td>
                <td><span class="badge ${scoreClass}">${riskScore.toFixed(2)}</span></td>
                <td>${topFactors || 'None identified'}</td>
            </tr>
        `;
    });
    
    tableHtml += `
            </tbody>
        </table>
    `;
    
    // Set the HTML content
    container.innerHTML = tableHtml;
}

/**
 * Render entity timeline visualization
 */
function renderEntityTimeline(reportData) {
    const container = document.getElementById('entity-timeline');
    if (!container) return;
    
    // This would be implemented with a timeline visualization
    // For example using vis-timeline.js
    container.innerHTML = '<p class="text-center">Timeline visualization would appear here.</p>';
}

/**
 * Render risk factor breakdown for an entity
 */
function renderRiskFactorBreakdown(reportData) {
    const container = document.getElementById('risk-factor-breakdown');
    if (!container) return;
    
    // Ensure we have entity data
    if (!reportData.entity) return;
    
    const entity = reportData.entity;
    const riskFactors = entity.risk_factors || [];
    
    // Create data for chart
    const labels = riskFactors.map(factor => factor.factor || 'Unknown');
    const data = riskFactors.map(factor => factor.weight || 0);
    
    // Create chart
    const ctx = container.getContext('2d');
    new Chart(ctx, {
        type: 'horizontalBar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Risk Weight',
                data: data,
                backgroundColor: 'rgba(220, 53, 69, 0.7)',
                borderColor: 'rgb(220, 53, 69)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                x: {
                    beginAtZero: true,
                    max: 1
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Risk Factor Breakdown'
                }
            }
        }
    });
}

/**
 * Export report as PDF
 */
function exportReportAsPDF() {
    // Show loading indicator
    const exportBtn = document.getElementById('export-pdf-btn');
    if (!exportBtn) return;
    
    const originalBtnText = exportBtn.innerHTML;
    exportBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Exporting...';
    exportBtn.disabled = true;
    
    // Get report ID from data attribute
    const reportId = exportBtn.dataset.reportId;
    if (!reportId) return;
    
    // Request PDF export
    fetch(`/export-report/${reportId}/pdf`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Error exporting report');
            }
            return response.blob();
        })
        .then(blob => {
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'report.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            
            // Reset button
            exportBtn.innerHTML = originalBtnText;
            exportBtn.disabled = false;
        })
        .catch(error => {
            console.error('Export error:', error);
            
            // Reset button
            exportBtn.innerHTML = originalBtnText;
            exportBtn.disabled = false;
            
            // Show error message
            alert('Error exporting report: ' + error.message);
        });
}
