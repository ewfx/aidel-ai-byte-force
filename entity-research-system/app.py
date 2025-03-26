import os
import logging

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename
import pandas as pd
import json
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize database
db = SQLAlchemy(model_class=Base)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///entity_research.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload directory exists
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

# Initialize database with app
db.init_app(app)

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import Entity, Transaction, Evidence, RiskScore, Report
    db.create_all()

# Import processing modules
from data_processor import process_file, extract_entities
from ai_engine import analyze_entity, generate_evidence_summary
from api_integrations import fetch_entity_data
from risk_scoring import calculate_risk_score

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Get summary stats
    entity_count = Entity.query.count()
    high_risk_count = RiskScore.query.filter(RiskScore.score >= 0.7).count()
    transaction_count = Transaction.query.count()
    
    # Get recent entities
    recent_entities = Entity.query.order_by(Entity.created_at.desc()).limit(5).all()
    
    # Get top risk entities
    high_risk_entities = db.session.query(Entity, RiskScore).\
        join(RiskScore, Entity.id == RiskScore.entity_id).\
        order_by(RiskScore.score.desc()).\
        limit(5).all()
    
    return render_template('dashboard.html', 
                          entity_count=entity_count,
                          high_risk_count=high_risk_count,
                          transaction_count=transaction_count,
                          recent_entities=recent_entities,
                          high_risk_entities=high_risk_entities)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
            
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
            
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # Process the file and extract entities
            try:
                data = process_file(file_path)
                entities = extract_entities(data)
                
                # Store extracted entities in the database
                for entity_data in entities:
                    # Check if entity already exists
                    existing_entity = Entity.query.filter_by(name=entity_data['name']).first()
                    
                    if not existing_entity:
                        entity = Entity(
                            name=entity_data['name'],
                            entity_type=entity_data['type'],
                            description=entity_data.get('description', ''),
                            source_file=filename
                        )
                        db.session.add(entity)
                        db.session.flush()
                        
                        # Fetch additional data and analyze entity
                        external_data = fetch_entity_data(entity_data['name'])
                        analysis = analyze_entity(entity_data, external_data)
                        
                        # Add evidence
                        for evidence_item in analysis['evidence']:
                            evidence = Evidence(
                                entity_id=entity.id,
                                source=evidence_item['source'],
                                content=evidence_item['content'],
                                confidence=evidence_item.get('confidence', 0.0)
                            )
                            db.session.add(evidence)
                        
                        # Calculate and store risk score
                        risk_data = calculate_risk_score(entity_data, analysis)
                        risk_score = RiskScore(
                            entity_id=entity.id,
                            score=risk_data['score'],
                            factors=json.dumps(risk_data['factors']),
                            last_updated=datetime.now()
                        )
                        db.session.add(risk_score)
                
                # Save all transactions
                for transaction in data:
                    new_transaction = Transaction(
                        transaction_id=transaction.get('transaction_id', f"TX-{pd.util.hash_pandas_object(pd.Series(transaction)).sum()}"),
                        sender=transaction.get('sender', ''),
                        receiver=transaction.get('receiver', ''),
                        amount=transaction.get('amount', 0.0),
                        currency=transaction.get('currency', 'USD'),
                        timestamp=transaction.get('timestamp', datetime.now()),
                        source_file=filename,
                        raw_data=json.dumps(transaction)
                    )
                    db.session.add(new_transaction)
                
                db.session.commit()
                flash(f'Processed {len(entities)} entities from {filename}', 'success')
                return redirect(url_for('dashboard'))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error processing file: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/entities')
def entities():
    entities = Entity.query.all()
    return render_template('entity_details.html', entities=entities)

@app.route('/entity/<int:entity_id>')
def entity_details(entity_id):
    entity = Entity.query.get_or_404(entity_id)
    evidence = Evidence.query.filter_by(entity_id=entity_id).all()
    risk_score = RiskScore.query.filter_by(entity_id=entity_id).first()
    
    # Get related transactions
    transactions = Transaction.query.filter(
        (Transaction.sender == entity.name) | (Transaction.receiver == entity.name)
    ).all()
    
    # Get connected entities through transactions
    connected_entities = set()
    for tx in transactions:
        if tx.sender == entity.name and tx.receiver != entity.name:
            connected_entity = Entity.query.filter_by(name=tx.receiver).first()
            if connected_entity:
                connected_entities.add(connected_entity)
        elif tx.receiver == entity.name and tx.sender != entity.name:
            connected_entity = Entity.query.filter_by(name=tx.sender).first()
            if connected_entity:
                connected_entities.add(connected_entity)
    
    return render_template('entity_details.html', 
                          entity=entity, 
                          evidence=evidence, 
                          risk_score=risk_score, 
                          transactions=transactions,
                          connected_entities=list(connected_entities))

@app.route('/api/entity-network')
def entity_network():
    # Generate network data for visualization
    entities = Entity.query.all()
    transactions = Transaction.query.all()
    
    nodes = []
    for entity in entities:
        risk_score = RiskScore.query.filter_by(entity_id=entity.id).first()
        score = risk_score.score if risk_score else 0.0
        nodes.append({
            'id': entity.id,
            'name': entity.name,
            'type': entity.entity_type,
            'risk_score': score
        })
    
    links = []
    for tx in transactions:
        source_entity = Entity.query.filter_by(name=tx.sender).first()
        target_entity = Entity.query.filter_by(name=tx.receiver).first()
        
        if source_entity and target_entity:
            links.append({
                'source': source_entity.id,
                'target': target_entity.id,
                'value': tx.amount,
                'currency': tx.currency
            })
    
    return jsonify({'nodes': nodes, 'links': links})

@app.route('/reports')
def reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return render_template('reports.html', reports=reports)

@app.route('/generate-report', methods=['POST'])
def generate_report():
    report_type = request.form.get('report_type', 'all_entities')
    
    # Generate report
    if report_type == 'all_entities':
        entities = Entity.query.all()
        risk_scores = {rs.entity_id: rs for rs in RiskScore.query.all()}
        
        report_data = {
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'report_type': 'All Entities Risk Assessment',
            'entities': [
                {
                    'id': entity.id,
                    'name': entity.name,
                    'type': entity.entity_type,
                    'risk_score': risk_scores.get(entity.id).score if entity.id in risk_scores else None,
                    'risk_factors': json.loads(risk_scores.get(entity.id).factors) if entity.id in risk_scores and risk_scores.get(entity.id).factors else []
                }
                for entity in entities
            ]
        }
        
        # Create report in database
        report = Report(
            title=f"All Entities Risk Assessment - {datetime.now().strftime('%Y-%m-%d')}",
            report_type=report_type,
            content=json.dumps(report_data)
        )
        db.session.add(report)
        db.session.commit()
        
        flash('Report generated successfully', 'success')
    
    return redirect(url_for('reports'))

@app.route('/view-report/<int:report_id>')
def view_report(report_id):
    report = Report.query.get_or_404(report_id)
    report_data = json.loads(report.content)
    
    return render_template('report_view.html', report=report, report_data=report_data)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return render_template('500.html'), 500
