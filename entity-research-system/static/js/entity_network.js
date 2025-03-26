/**
 * Entity Network Visualization for Entity Research System
 * Uses D3.js to create interactive network visualizations of entity relationships
 */

class EntityNetworkVisualization {
    /**
     * Initialize the network visualization
     * @param {string} elementId - The ID of the element to render the network in
     * @param {Object} options - Configuration options
     */
    constructor(elementId, options = {}) {
        this.containerElement = document.getElementById(elementId);
        if (!this.containerElement) {
            console.error(`Element with ID "${elementId}" not found`);
            return;
        }
        
        // Default options
        this.options = {
            width: this.containerElement.clientWidth,
            height: 600,
            nodeRadius: 12,
            linkDistance: 150,
            chargeStrength: -300,
            ...options
        };
        
        // Initialize data structures
        this.nodes = [];
        this.links = [];
        this.simulation = null;
        this.svg = null;
        this.linkElements = null;
        this.nodeElements = null;
        this.textElements = null;
        
        // Initialize the visualization
        this.initVisualization();
        
        // Add resize event listener
        window.addEventListener('resize', () => {
            this.options.width = this.containerElement.clientWidth;
            this.updateVisualization();
        });
    }
    
    /**
     * Initialize the visualization SVG and force simulation
     */
    initVisualization() {
        // Clear any existing content
        this.containerElement.innerHTML = '';
        
        // Create SVG container
        this.svg = d3.select(this.containerElement)
            .append('svg')
            .attr('width', this.options.width)
            .attr('height', this.options.height)
            .attr('class', 'entity-network-svg');
            
        // Add zoom and pan functionality
        const zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                this.svg.select('.network-container')
                    .attr('transform', event.transform);
            });
            
        this.svg.call(zoom);
        
        // Create a group for the network that will be transformed during zoom
        this.networkContainer = this.svg.append('g')
            .attr('class', 'network-container');
            
        // Add arrow marker for directed edges
        this.svg.append('defs').append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '-0 -5 10 10')
            .attr('refX', this.options.nodeRadius + 9)
            .attr('refY', 0)
            .attr('orient', 'auto')
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('xoverflow', 'visible')
            .append('svg:path')
            .attr('d', 'M 0,-5 L 10 ,0 L 0,5')
            .attr('fill', '#999')
            .style('stroke', 'none');
            
        // Initialize force simulation
        this.simulation = d3.forceSimulation()
            .force('link', d3.forceLink().id(d => d.id).distance(this.options.linkDistance))
            .force('charge', d3.forceManyBody().strength(this.options.chargeStrength))
            .force('center', d3.forceCenter(this.options.width / 2, this.options.height / 2))
            .force('collision', d3.forceCollide().radius(this.options.nodeRadius * 1.5));
    }
    
    /**
     * Load network data from an API endpoint
     * @param {string} url - The API URL to fetch data from
     */
    loadData(url) {
        // Show loading indicator
        this.containerElement.innerHTML = '<div class="loading-indicator"><i class="fas fa-spinner fa-spin"></i> Loading network data...</div>';
        
        // Fetch data from API
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                this.setData(data.nodes, data.links);
            })
            .catch(error => {
                console.error('Error loading network data:', error);
                this.containerElement.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> Error loading network data: ${error.message}
                    </div>
                `;
            });
    }
    
    /**
     * Set the network data and update the visualization
     * @param {Array} nodes - Array of node objects
     * @param {Array} links - Array of link objects
     */
    setData(nodes, links) {
        this.nodes = nodes;
        this.links = links;
        
        // Re-initialize the visualization
        this.initVisualization();
        this.updateVisualization();
    }
    
    /**
     * Update the visualization with current data
     */
    updateVisualization() {
        // Create links
        this.linkElements = this.networkContainer.selectAll('.link')
            .data(this.links)
            .enter()
            .append('line')
            .attr('class', 'link')
            .attr('marker-end', 'url(#arrowhead)')
            .attr('stroke-width', d => Math.sqrt(d.weight) / 5 + 1)
            .attr('stroke', d => {
                // Color links based on type
                switch(d.type) {
                    case 'parent-subsidiary': return '#27ae60';
                    case 'investor-investee': return '#3498db';
                    case 'banking': return '#f39c12';
                    case 'customer': return '#9b59b6';
                    case 'supplier': return '#1abc9c';
                    case 'donor': return '#e74c3c';
                    default: return '#95a5a6';
                }
            });
            
        // Create node groups
        const nodeGroups = this.networkContainer.selectAll('.node')
            .data(this.nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', this.dragStarted.bind(this))
                .on('drag', this.dragged.bind(this))
                .on('end', this.dragEnded.bind(this))
            )
            .on('click', this.nodeClicked.bind(this))
            .on('mouseover', this.nodeMouseOver.bind(this))
            .on('mouseout', this.nodeMouseOut.bind(this));
            
        // Add node circles
        this.nodeElements = nodeGroups.append('circle')
            .attr('r', this.options.nodeRadius)
            .attr('fill', d => {
                // Color nodes based on entity type
                switch(d.type) {
                    case 'corporation': return '#2c7be5';
                    case 'non_profit': return '#27ae60';
                    case 'shell_company': return '#e74c3c';
                    case 'financial_intermediary': return '#3498db';
                    case 'individual': return '#9b59b6';
                    default: return '#95a5a6';
                }
            })
            .attr('stroke', d => {
                // Border color based on risk level
                switch(d.risk_level) {
                    case 'low': return '#28a745';
                    case 'medium': return '#ffc107';
                    case 'high': return '#dc3545';
                    case 'critical': return '#212529';
                    default: return '#6c757d';
                }
            })
            .attr('stroke-width', 2);
            
        // Add node labels
        this.textElements = nodeGroups.append('text')
            .text(d => this.truncateLabel(d.name))
            .attr('font-size', 10)
            .attr('dx', 15)
            .attr('dy', 4)
            .attr('class', 'node-label');
            
        // Add risk level indicators
        nodeGroups.append('text')
            .attr('font-family', 'FontAwesome')
            .attr('text-anchor', 'middle')
            .attr('dominant-baseline', 'central')
            .attr('font-size', 8)
            .attr('fill', 'white')
            .text(d => {
                // Use FontAwesome icons based on risk level
                switch(d.risk_level) {
                    case 'high': case 'critical': return '\uf071'; // warning
                    case 'medium': return '\uf06a'; // exclamation-circle
                    default: return '';
                }
            });
            
        // Update the simulation
        this.simulation
            .nodes(this.nodes)
            .on('tick', this.ticked.bind(this));
            
        this.simulation.force('link')
            .links(this.links);
            
        // Restart the simulation
        this.simulation.alpha(1).restart();
        
        // Add legend
        this.addLegend();
    }
    
    /**
     * Handle simulation tick events to update element positions
     */
    ticked() {
        this.linkElements
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
            
        this.nodeElements
            .attr('cx', d => d.x = Math.max(this.options.nodeRadius, Math.min(this.options.width - this.options.nodeRadius, d.x)))
            .attr('cy', d => d.y = Math.max(this.options.nodeRadius, Math.min(this.options.height - this.options.nodeRadius, d.y)));
            
        this.textElements
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    }
    
    /**
     * Handle drag start event
     */
    dragStarted(event, d) {
        if (!event.active) this.simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }
    
    /**
     * Handle drag event
     */
    dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }
    
    /**
     * Handle drag end event
     */
    dragEnded(event, d) {
        if (!event.active) this.simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }
    
    /**
     * Handle node click event
     */
    nodeClicked(event, d) {
        // Navigate to entity details page
        window.location.href = `/entity/${d.id}`;
    }
    
    /**
     * Handle node mouseover event
     */
    nodeMouseOver(event, d) {
        // Highlight connected nodes and links
        const connectedNodes = new Set();
        const connectedLinks = new Set();
        
        this.links.forEach(link => {
            if (link.source.id === d.id || link.target.id === d.id) {
                connectedLinks.add(link);
                if (link.source.id === d.id) connectedNodes.add(link.target.id);
                if (link.target.id === d.id) connectedNodes.add(link.source.id);
            }
        });
        
        this.nodeElements
            .attr('opacity', node => (node.id === d.id || connectedNodes.has(node.id)) ? 1.0 : 0.3);
            
        this.linkElements
            .attr('opacity', link => connectedLinks.has(link) ? 1.0 : 0.1);
            
        this.textElements
            .attr('opacity', node => (node.id === d.id || connectedNodes.has(node.id)) ? 1.0 : 0.3);
            
        // Show tooltip with entity details
        const tooltip = d3.select('body').append('div')
            .attr('class', 'network-tooltip')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '10px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('opacity', 0);
            
        tooltip.html(`
            <div><strong>${d.name}</strong></div>
            <div>Type: ${d.type}</div>
            <div>Risk Score: ${d.risk_score.toFixed(2)}</div>
            <div>Risk Level: ${d.risk_level}</div>
            <div class="mt-1"><small>Click for details</small></div>
        `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 15) + 'px')
            .transition()
            .duration(200)
            .style('opacity', 1);
            
        d3.select(event.currentTarget).attr('data-tooltip-id', '__current_tooltip');
    }
    
    /**
     * Handle node mouseout event
     */
    nodeMouseOut(event, d) {
        // Reset node and link opacity
        this.nodeElements.attr('opacity', 1);
        this.linkElements.attr('opacity', 1);
        this.textElements.attr('opacity', 1);
        
        // Remove tooltip
        if (d3.select(event.currentTarget).attr('data-tooltip-id') === '__current_tooltip') {
            d3.selectAll('.network-tooltip').remove();
            d3.select(event.currentTarget).attr('data-tooltip-id', null);
        }
    }
    
    /**
     * Add a legend to the visualization
     */
    addLegend() {
        const legend = this.svg.append('g')
            .attr('class', 'legend')
            .attr('transform', 'translate(20, 20)');
            
        // Entity type legend
        const entityTypes = [
            { type: 'corporation', label: 'Corporation', color: '#2c7be5' },
            { type: 'non_profit', label: 'Non-Profit', color: '#27ae60' },
            { type: 'shell_company', label: 'Shell Company', color: '#e74c3c' },
            { type: 'financial_intermediary', label: 'Financial', color: '#3498db' },
            { type: 'individual', label: 'Individual', color: '#9b59b6' },
            { type: 'other', label: 'Other', color: '#95a5a6' }
        ];
        
        const entityTypeLegend = legend.append('g')
            .attr('class', 'entity-type-legend');
            
        entityTypeLegend.append('text')
            .attr('x', 0)
            .attr('y', 0)
            .text('Entity Types')
            .attr('font-weight', 'bold')
            .attr('font-size', 12);
            
        entityTypes.forEach((item, i) => {
            const g = entityTypeLegend.append('g')
                .attr('transform', `translate(0, ${i * 20 + 20})`);
                
            g.append('circle')
                .attr('r', 6)
                .attr('fill', item.color);
                
            g.append('text')
                .attr('x', 15)
                .attr('y', 4)
                .text(item.label)
                .attr('font-size', 10);
        });
        
        // Risk level legend
        const riskLevels = [
            { level: 'low', label: 'Low Risk', color: '#28a745' },
            { level: 'medium', label: 'Medium Risk', color: '#ffc107' },
            { level: 'high', label: 'High Risk', color: '#dc3545' },
            { level: 'critical', label: 'Critical Risk', color: '#212529' }
        ];
        
        const riskLevelLegend = legend.append('g')
            .attr('class', 'risk-level-legend')
            .attr('transform', `translate(120, 0)`);
            
        riskLevelLegend.append('text')
            .attr('x', 0)
            .attr('y', 0)
            .text('Risk Levels')
            .attr('font-weight', 'bold')
            .attr('font-size', 12);
            
        riskLevels.forEach((item, i) => {
            const g = riskLevelLegend.append('g')
                .attr('transform', `translate(0, ${i * 20 + 20})`);
                
            g.append('circle')
                .attr('r', 6)
                .attr('fill', 'transparent')
                .attr('stroke', item.color)
                .attr('stroke-width', 2);
                
            g.append('text')
                .attr('x', 15)
                .attr('y', 4)
                .text(item.label)
                .attr('font-size', 10);
        });
    }
    
    /**
     * Truncate a label to a maximum length
     * @param {string} label - The label to truncate
     * @param {number} maxLength - Maximum length before truncation
     * @returns {string} Truncated label
     */
    truncateLabel(label, maxLength = 15) {
        return label.length > maxLength ? label.substring(0, maxLength) + '...' : label;
    }
}

// Initialize network visualization on page load
document.addEventListener('DOMContentLoaded', function() {
    const networkContainer = document.getElementById('networkVisualization');
    
    if (networkContainer) {
        const network = new EntityNetworkVisualization('networkVisualization');
        network.loadData('/api/network-data');
        
        // Add event listener for filtering
        const filterForm = document.getElementById('networkFilterForm');
        if (filterForm) {
            filterForm.addEventListener('submit', function(event) {
                event.preventDefault();
                
                // Build filter query
                const entityType = document.getElementById('entityTypeFilter').value;
                const riskLevel = document.getElementById('riskLevelFilter').value;
                const minRiskScore = document.getElementById('minRiskScoreFilter').value;
                
                let url = '/api/network-data?';
                if (entityType) url += `entity_type=${entityType}&`;
                if (riskLevel) url += `risk_level=${riskLevel}&`;
                if (minRiskScore) url += `min_risk_score=${minRiskScore}&`;
                
                // Load filtered data
                network.loadData(url);
            });
        }
    }
});
