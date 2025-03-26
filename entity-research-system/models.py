from app import db
from datetime import datetime
from sqlalchemy.dialects.sqlite import JSON

class Entity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50))  # corporation, non-profit, shell company, financial intermediary
    description = db.Column(db.Text)
    source_file = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    evidence = db.relationship('Evidence', backref='entity', lazy=True)
    risk_scores = db.relationship('RiskScore', backref='entity', lazy=True)
    
    def __repr__(self):
        return f'<Entity {self.name}>'

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(255), nullable=False)
    sender = db.Column(db.String(255))
    receiver = db.Column(db.String(255))
    amount = db.Column(db.Float)
    currency = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime)
    source_file = db.Column(db.String(255))
    raw_data = db.Column(db.Text)  # JSON data of the original transaction
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'

class Evidence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    source = db.Column(db.String(255))
    content = db.Column(db.Text)
    confidence = db.Column(db.Float, default=0.0)  # Confidence score 0-1
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Evidence {self.id} for Entity {self.entity_id}>'

class RiskScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)
    score = db.Column(db.Float, nullable=False)  # Risk score 0-1
    factors = db.Column(db.Text)  # JSON array of risk factors
    last_updated = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<RiskScore {self.score} for Entity {self.entity_id}>'

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    report_type = db.Column(db.String(50))
    content = db.Column(db.Text)  # JSON data of the report
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Report {self.title}>'
