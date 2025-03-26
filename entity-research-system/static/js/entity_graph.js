document.addEventListener('DOMContentLoaded', function() {
    // Load the entity network graph if the container exists
    const networkContainer = document.getElementById('entity-network-graph');
    if (networkContainer) {
        loadEntityNetwork();
    }
});

/**
 * Load and render the entity relationship network graph
 */
function loadEntityNetwork() {
    // Fetch entity network data
    fetch('/api/entity-network')
        .then(response => response.json())
        .then(data => {
            renderNetworkGraph(data);
        })
        .catch(error => {
            console.error('Error loading entity network data:', error);
            document.getElementById('entity-network-graph').innerHTML = 
                '<div class="alert alert-danger">Error loading entity network data</div>';
        });
}

/**
 * Render the network graph using D3.js
 * @param {Object} data - Network data with nodes and links
 */
function renderNetworkGraph(data) {
    const container = document.getElementById('entity-network-graph');
    const width = container.clientWidth;
    const height = 500; // Fixed height or adjust as needed
    
    // Clear any existing content
    container.innerHTML = '';
    
    // Create SVG element
    const svg = d3.select(container)
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height])
        .attr('style', 'max-width: 100%; height: auto;');
    
    // Create a tooltip div
    const tooltip = d3.select(container)
        .append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background-color', 'rgba(0, 0, 0, 0.8)')
        .style('color', 'white')
        .style('padding', '8px')
        .style('border-radius', '6px')
        .style('pointer-events', 'none')
        .style('z-index', '1');
    
    // Create a group for the graph
    const g = svg.append('g');
    
    // Add zoom functionality
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on('zoom', (event) => {
            g.attr('transform', event.transform);
        });
    
    svg.call(zoom);
    
    // Define color scale for risk scores
    const colorScale = d3.scaleSequential(d3.interpolateRgb("green", "red"))
        .domain([0, 1]);
    
    // Define node size scale based on connections
    const nodeSizeScale = d3.scaleLinear()
        .domain([0, d3.max(data.nodes, d => {
            // Count links connected to this node
            return data.links.filter(l => l.source === d.id || l.target === d.id).length;
        })])
        .range([5, 20]);
    
    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force('link', d3.forceLink(data.links).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => nodeSizeScale(
            data.links.filter(l => l.source.id === d.id || l.target.id === d.id).length
        ) + 10));
    
    // Create links
    const link = g.append('g')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .selectAll('line')
        .data(data.links)
        .join('line')
        .attr('stroke-width', d => Math.sqrt(d.value / 10000 + 1));
    
    // Create nodes
    const node = g.append('g')
        .selectAll('circle')
        .data(data.nodes)
        .join('circle')
        .attr('r', d => {
            // Count links connected to this node
            const linkCount = data.links.filter(l => 
                (l.source.id === d.id || l.target.id === d.id) || 
                (l.source === d.id || l.target === d.id)
            ).length;
            return nodeSizeScale(linkCount || 1);
        })
        .attr('fill', d => colorScale(d.risk_score || 0))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1.5)
        .on('mouseover', function(event, d) {
            d3.select(this)
                .attr('stroke', '#000')
                .attr('stroke-width', 2);
                
            tooltip.transition()
                .duration(200)
                .style('opacity', .9);
            
            // Get connected entities
            const connections = data.links.filter(l => 
                (l.source.id === d.id || l.target.id === d.id) || 
                (l.source === d.id || l.target === d.id)
            );
            
            let connectionsList = '';
            if (connections.length > 0) {
                connectionsList = '<h6>Connections:</h6><ul>';
                connections.forEach(c => {
                    const connectedId = c.source.id === d.id || c.source === d.id ? c.target : c.source;
                    const connectedNode = data.nodes.find(n => n.id === connectedId || n.id === connectedId.id);
                    if (connectedNode) {
                        connectionsList += `<li>${connectedNode.name} ($${c.value.toLocaleString()})</li>`;
                    }
                });
                connectionsList += '</ul>';
            }
            
            tooltip.html(`
                <div class="p-2">
                    <h5>${d.name}</h5>
                    <p>Type: ${d.type}</p>
                    <p>Risk Score: ${(d.risk_score || 0).toFixed(2)}</p>
                    ${connectionsList}
                    <small class="text-muted">Click for details</small>
                </div>
            `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 28) + 'px');
        })
        .on('mouseout', function() {
            d3.select(this)
                .attr('stroke', '#fff')
                .attr('stroke-width', 1.5);
            
            tooltip.transition()
                .duration(500)
                .style('opacity', 0);
        })
        .on('click', function(event, d) {
            // Navigate to entity details page
            window.location.href = `/entity/${d.id}`;
        })
        .call(drag(simulation));
    
    // Add node labels
    const labels = g.append('g')
        .selectAll('text')
        .data(data.nodes)
        .join('text')
        .attr('dx', 12)
        .attr('dy', '.35em')
        .text(d => d.name)
        .style('font-size', '10px')
        .style('fill', '#fff')
        .style('text-shadow', '1px 1px 2px black');
    
    // Add simulation tick
    simulation.on('tick', () => {
        link
            .attr('x1', d => d.source.x)
            .attr('y1', d => d.source.y)
            .attr('x2', d => d.target.x)
            .attr('y2', d => d.target.y);
        
        node
            .attr('cx', d => d.x)
            .attr('cy', d => d.y);
        
        labels
            .attr('x', d => d.x)
            .attr('y', d => d.y);
    });
    
    // Add legend
    const legend = svg.append('g')
        .attr('class', 'legend')
        .attr('transform', `translate(20, ${height - 120})`);
    
    // Risk score legend
    legend.append('text')
        .attr('x', 0)
        .attr('y', 0)
        .text('Risk Score')
        .style('font-weight', 'bold')
        .style('fill', '#fff');
    
    const riskGradient = legend.append('defs')
        .append('linearGradient')
        .attr('id', 'risk-gradient')
        .attr('x1', '0%')
        .attr('y1', '0%')
        .attr('x2', '100%')
        .attr('y2', '0%');
    
    riskGradient.append('stop')
        .attr('offset', '0%')
        .attr('stop-color', 'green');
    
    riskGradient.append('stop')
        .attr('offset', '50%')
        .attr('stop-color', 'yellow');
    
    riskGradient.append('stop')
        .attr('offset', '100%')
        .attr('stop-color', 'red');
    
    legend.append('rect')
        .attr('x', 0)
        .attr('y', 10)
        .attr('width', 150)
        .attr('height', 10)
        .style('fill', 'url(#risk-gradient)');
    
    legend.append('text')
        .attr('x', 0)
        .attr('y', 35)
        .text('Low')
        .style('fill', '#fff')
        .style('font-size', '10px');
    
    legend.append('text')
        .attr('x', 75)
        .attr('y', 35)
        .text('Medium')
        .style('fill', '#fff')
        .style('font-size', '10px');
    
    legend.append('text')
        .attr('x', 130)
        .attr('y', 35)
        .text('High')
        .style('fill', '#fff')
        .style('font-size', '10px');
    
    // Node size legend
    legend.append('text')
        .attr('x', 0)
        .attr('y', 55)
        .text('Node Size = Number of Connections')
        .style('font-weight', 'bold')
        .style('fill', '#fff');
    
    // Add controls
    const controls = container.parentNode.querySelector('.graph-controls') || 
                     document.createElement('div');
    
    controls.className = 'graph-controls mt-3';
    controls.innerHTML = `
        <div class="btn-group" role="group">
            <button class="btn btn-sm btn-secondary" id="zoom-in">
                <i class="fas fa-search-plus"></i> Zoom In
            </button>
            <button class="btn btn-sm btn-secondary" id="zoom-out">
                <i class="fas fa-search-minus"></i> Zoom Out
            </button>
            <button class="btn btn-sm btn-secondary" id="reset-zoom">
                <i class="fas fa-sync"></i> Reset
            </button>
        </div>
    `;
    
    if (!container.parentNode.querySelector('.graph-controls')) {
        container.parentNode.appendChild(controls);
    }
    
    // Add event listeners for controls
    document.getElementById('zoom-in').addEventListener('click', () => {
        svg.transition().call(zoom.scaleBy, 1.5);
    });
    
    document.getElementById('zoom-out').addEventListener('click', () => {
        svg.transition().call(zoom.scaleBy, 0.75);
    });
    
    document.getElementById('reset-zoom').addEventListener('click', () => {
        svg.transition().call(zoom.transform, d3.zoomIdentity);
    });
    
    // Function for drag behavior
    function drag(simulation) {
        function dragstarted(event) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }
        
        function dragged(event) {
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }
        
        function dragended(event) {
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }
        
        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }
}
