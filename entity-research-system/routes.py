from flask import render_template, request, jsonify, redirect, url_for, flash, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
import json
import io
import csv
from datetime import datetime

from models import (
    db, User, Entity, Transaction, Evidence, Relationship, 
    AnalysisJob, RiskLevel, EntityType
)
from services.data_processor import process_transaction_data
from services.entity_extractor import extract_entities
from services.risk_scorer import calculate_risk_score
from services.network_analyzer import analyze_network
from services.openai_service import analyze_entity

def register_routes(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        # Get high-level stats for dashboard
        entity_count = Entity.query.count()
        transaction_count = Transaction.query.count()
        evidence_count = Evidence.query.count()
        
        # Get risk distribution
        risk_distribution = db.session.query(
            Entity.risk_level, 
            db.func.count(Entity.id)
        ).group_by(Entity.risk_level).all()
        
        risk_data = {level.value: 0 for level in RiskLevel}
        for level, count in risk_distribution:
            risk_data[level.value] = count
        
        # Get entity type distribution
        entity_type_distribution = db.session.query(
            Entity.entity_type, 
            db.func.count(Entity.id)
        ).group_by(Entity.entity_type).all()
        
        entity_type_data = {etype.value: 0 for etype in EntityType}
        for etype, count in entity_type_distribution:
            entity_type_data[etype.value] = count
        
        # Get recent entities
        recent_entities = Entity.query.order_by(Entity.created_at.desc()).limit(5).all()
        
        return render_template(
            'dashboard.html',
            entity_count=entity_count,
            transaction_count=transaction_count,
            evidence_count=evidence_count,
            risk_data=risk_data,
            entity_type_data=entity_type_data,
            recent_entities=recent_entities
        )
    
    @app.route('/upload', methods=['GET', 'POST'])
    @login_required
    def upload():
        if request.method == 'POST':
            if 'file' not in request.files:
                flash('No file selected', 'danger')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
            
            try:
                # Process the uploaded file
                file_content = file.read().decode('utf-8')
                
                # Create analysis job
                job = AnalysisJob(
                    job_type='data_upload',
                    status='processing',
                    data_source=file.filename,
                    parameters={'format': file.filename.split('.')[-1]}
                )
                db.session.add(job)
                db.session.commit()
                
                # Process transaction data
                processed_data = process_transaction_data(file_content, file.filename)
                
                # Extract entities
                entities = extract_entities(processed_data)
                
                # Save entities and transactions to database
                for entity_data in entities:
                    # Check if entity already exists
                    entity = Entity.query.filter_by(name=entity_data['name']).first()
                    if not entity:
                        entity = Entity(
                            name=entity_data['name'],
                            entity_type=entity_data['type'],
                            description=entity_data.get('description', ''),
                            country=entity_data.get('country', ''),
                            address=entity_data.get('address', '')
                        )
                        db.session.add(entity)
                        db.session.flush()  # Get entity ID
                    
                    # Calculate risk score
                    risk_score, risk_level = calculate_risk_score(entity_data)
                    entity.risk_score = risk_score
                    entity.risk_level = risk_level
                    
                    # Add transactions
                    for tx_data in entity_data.get('transactions', []):
                        transaction = Transaction(
                            transaction_id=tx_data['id'],
                            entity_id=entity.id,
                            amount=tx_data['amount'],
                            transaction_date=tx_data['date'],
                            transaction_type=tx_data.get('type', 'unknown'),
                            source=tx_data.get('source', ''),
                            destination=tx_data.get('destination', ''),
                            currency=tx_data.get('currency', 'USD')
                        )
                        db.session.add(transaction)
                
                # Analyze entity network
                relationships = analyze_network(entities)
                for rel_data in relationships:
                    source = Entity.query.filter_by(name=rel_data['source']).first()
                    target = Entity.query.filter_by(name=rel_data['target']).first()
                    
                    if source and target:
                        relationship = Relationship(
                            source_entity_id=source.id,
                            target_entity_id=target.id,
                            relationship_type=rel_data['type'],
                            weight=rel_data.get('weight', 1.0),
                            description=rel_data.get('description', '')
                        )
                        db.session.add(relationship)
                
                # Update job status
                job.status = 'completed'
                job.completed_at = datetime.utcnow()
                job.results = {'entities_processed': len(entities)}
                
                db.session.commit()
                
                flash(f'Successfully processed {len(entities)} entities from {file.filename}', 'success')
                return redirect(url_for('dashboard'))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error processing file: {str(e)}', 'danger')
                return redirect(request.url)
        
        return render_template('upload.html')
    
    @app.route('/entities')
    @login_required
    def entities():
        search = request.args.get('search', '')
        risk_level = request.args.get('risk_level', '')
        entity_type = request.args.get('entity_type', '')
        
        query = Entity.query
        
        if search:
            query = query.filter(Entity.name.ilike(f'%{search}%'))
        
        if risk_level:
            query = query.filter(Entity.risk_level == risk_level)
        
        if entity_type:
            query = query.filter(Entity.entity_type == entity_type)
        
        entities = query.order_by(Entity.risk_score.desc()).all()
        
        return render_template(
            'search.html',
            entities=entities,
            search=search,
            risk_level=risk_level,
            entity_type=entity_type,
            risk_levels=[level.value for level in RiskLevel],
            entity_types=[etype.value for etype in EntityType]
        )
    
    @app.route('/entity/<int:entity_id>')
    @login_required
    def entity_details(entity_id):
        entity = Entity.query.get_or_404(entity_id)
        
        # Get transactions
        transactions = Transaction.query.filter_by(entity_id=entity_id).order_by(Transaction.transaction_date.desc()).all()
        
        # Get evidence
        evidences = Evidence.query.filter_by(entity_id=entity_id).order_by(Evidence.created_at.desc()).all()
        
        # Get relationships
        relationships_out = Relationship.query.filter_by(source_entity_id=entity_id).all()
        relationships_in = Relationship.query.filter_by(target_entity_id=entity_id).all()
        
        related_entities = []
        
        for rel in relationships_out:
            target = Entity.query.get(rel.target_entity_id)
            related_entities.append({
                'entity': target,
                'relationship': rel.relationship_type,
                'direction': 'outgoing',
                'weight': rel.weight
            })
        
        for rel in relationships_in:
            source = Entity.query.get(rel.source_entity_id)
            related_entities.append({
                'entity': source,
                'relationship': rel.relationship_type,
                'direction': 'incoming',
                'weight': rel.weight
            })
        
        return render_template(
            'entity_details.html',
            entity=entity,
            transactions=transactions,
            evidences=evidences,
            related_entities=related_entities
        )
    
    @app.route('/analyze/<int:entity_id>', methods=['POST'])
    @login_required
    def analyze_entity_route(entity_id):
        entity = Entity.query.get_or_404(entity_id)
        
        try:
            # Create analysis job
            job = AnalysisJob(
                job_type='entity_analysis',
                status='processing',
                parameters={'entity_id': entity_id}
            )
            db.session.add(job)
            db.session.commit()
            
            # Analyze entity using AI
            analysis_result = analyze_entity(entity.name, entity.entity_type.value)
            
            # Save evidence
            for evidence_item in analysis_result.get('evidence', []):
                evidence = Evidence(
                    entity_id=entity_id,
                    evidence_type=evidence_item['type'],
                    description=evidence_item['description'],
                    source=evidence_item['source'],
                    confidence_score=evidence_item['confidence'],
                    data=evidence_item.get('data', {})
                )
                db.session.add(evidence)
            
            # Update entity information
            if 'entity_info' in analysis_result:
                entity_info = analysis_result['entity_info']
                entity.description = entity_info.get('description', entity.description)
                entity.country = entity_info.get('country', entity.country)
                entity.address = entity_info.get('address', entity.address)
                
                if 'registration_number' in entity_info:
                    entity.registration_number = entity_info['registration_number']
            
            # Update risk score
            if 'risk_score' in analysis_result:
                entity.risk_score = analysis_result['risk_score']
                entity.risk_level = RiskLevel(analysis_result['risk_level'])
            
            # Update job status
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            job.results = {'evidence_count': len(analysis_result.get('evidence', []))}
            
            db.session.commit()
            
            flash('Entity analysis completed successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error analyzing entity: {str(e)}', 'danger')
        
        return redirect(url_for('entity_details', entity_id=entity_id))
    
    @app.route('/report/<int:entity_id>')
    @login_required
    def generate_report(entity_id):
        entity = Entity.query.get_or_404(entity_id)
        
        # Get transactions
        transactions = Transaction.query.filter_by(entity_id=entity_id).order_by(Transaction.transaction_date.desc()).all()
        
        # Get evidence
        evidences = Evidence.query.filter_by(entity_id=entity_id).order_by(Evidence.created_at.desc()).all()
        
        # Get relationships
        relationships_out = Relationship.query.filter_by(source_entity_id=entity_id).all()
        relationships_in = Relationship.query.filter_by(target_entity_id=entity_id).all()
        
        related_entities = []
        
        for rel in relationships_out:
            target = Entity.query.get(rel.target_entity_id)
            related_entities.append({
                'entity': target,
                'relationship': rel.relationship_type,
                'direction': 'outgoing',
                'weight': rel.weight
            })
        
        for rel in relationships_in:
            source = Entity.query.get(rel.source_entity_id)
            related_entities.append({
                'entity': source,
                'relationship': rel.relationship_type,
                'direction': 'incoming',
                'weight': rel.weight
            })
        
        return render_template(
            'report.html',
            entity=entity,
            transactions=transactions,
            evidences=evidences,
            related_entities=related_entities,
            generation_time=datetime.utcnow()
        )
    
    @app.route('/export/entity/<int:entity_id>')
    @login_required
    def export_entity(entity_id):
        entity = Entity.query.get_or_404(entity_id)
        
        # Get transactions
        transactions = Transaction.query.filter_by(entity_id=entity_id).order_by(Transaction.transaction_date.desc()).all()
        
        # Get evidence
        evidences = Evidence.query.filter_by(entity_id=entity_id).order_by(Evidence.created_at.desc()).all()
        
        # Create CSV output
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Entity information
        writer.writerow(['Entity Report'])
        writer.writerow(['Generated On', datetime.utcnow()])
        writer.writerow([])
        writer.writerow(['Entity ID', entity.id])
        writer.writerow(['Name', entity.name])
        writer.writerow(['Type', entity.entity_type.value])
        writer.writerow(['Risk Score', entity.risk_score])
        writer.writerow(['Risk Level', entity.risk_level.value])
        writer.writerow(['Country', entity.country])
        writer.writerow(['Address', entity.address])
        writer.writerow(['Description', entity.description])
        writer.writerow([])
        
        # Transactions
        writer.writerow(['Transactions'])
        writer.writerow(['ID', 'Date', 'Amount', 'Currency', 'Type', 'Source', 'Destination'])
        for tx in transactions:
            writer.writerow([
                tx.transaction_id,
                tx.transaction_date,
                tx.amount,
                tx.currency,
                tx.transaction_type,
                tx.source,
                tx.destination
            ])
        writer.writerow([])
        
        # Evidence
        writer.writerow(['Evidence'])
        writer.writerow(['ID', 'Type', 'Source', 'Confidence', 'Description'])
        for ev in evidences:
            writer.writerow([
                ev.id,
                ev.evidence_type,
                ev.source,
                ev.confidence_score,
                ev.description
            ])
        
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'entity_report_{entity.id}_{datetime.utcnow().strftime("%Y%m%d")}.csv'
        )
    
    @app.route('/network')
    @login_required
    def network_view():
        return render_template('network.html')
    
    @app.route('/api/network-data')
    @login_required
    def network_data():
        # Get all entities
        entities = Entity.query.all()
        
        # Get all relationships
        relationships = Relationship.query.all()
        
        # Build network data
        nodes = []
        for entity in entities:
            nodes.append({
                'id': entity.id,
                'name': entity.name,
                'type': entity.entity_type.value,
                'risk_level': entity.risk_level.value,
                'risk_score': entity.risk_score
            })
        
        links = []
        for rel in relationships:
            links.append({
                'source': rel.source_entity_id,
                'target': rel.target_entity_id,
                'type': rel.relationship_type,
                'weight': rel.weight
            })
        
        return jsonify({
            'nodes': nodes,
            'links': links
        })
    
    @app.route('/api/entity-transaction-history/<int:entity_id>')
    @login_required
    def entity_transaction_history(entity_id):
        # Get transactions for entity
        transactions = Transaction.query.filter_by(entity_id=entity_id).order_by(Transaction.transaction_date).all()
        
        data = []
        for tx in transactions:
            data.append({
                'date': tx.transaction_date.strftime('%Y-%m-%d'),
                'amount': tx.amount,
                'currency': tx.currency,
                'type': tx.transaction_type
            })
        
        return jsonify(data)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                return redirect(url_for('dashboard'))
            
            flash('Invalid username or password', 'danger')
        
        return render_template('login.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        flash('You have been logged out', 'info')
        return redirect(url_for('login'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Check if username or email already exists
            if User.query.filter_by(username=username).first() is not None:
                flash('Username already exists', 'danger')
                return redirect(url_for('register'))
            
            if User.query.filter_by(email=email).first() is not None:
                flash('Email already exists', 'danger')
                return redirect(url_for('register'))
            
            # Create new user
            user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful, please log in', 'success')
            return redirect(url_for('login'))
        
        return render_template('register.html')

    # Add a few initial users if none exist
    with app.app_context():
        if User.query.count() == 0:
            users = [
                {'username': 'admin', 'email': 'admin@example.com', 'password': 'admin123'},
                {'username': 'analyst', 'email': 'analyst@example.com', 'password': 'analyst123'}
            ]
            
            for user_data in users:
                user = User(
                    username=user_data['username'],
                    email=user_data['email'],
                    password_hash=generate_password_hash(user_data['password'])
                )
                db.session.add(user)
            
            db.session.commit()
