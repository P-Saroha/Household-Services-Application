from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Initialize Flask app
app = Flask(__name__)

# Configure the SQLite database URI (database file location) and session secret key
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///householddb.sqlite3"  # SQLite database URI
app.secret_key = "ELfkVqmHSQT854$"  # Secret key used for session management (protects session cookies)

# Initialize SQLAlchemy for database operations
db = SQLAlchemy(app)

######################################## Models ##########################################################

# Model for Customer Table
class Customer(db.Model):
    # Specify the name of the table in the database
    __tablename__ = 'customers'
    
    # Define columns in the Customer table
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the customer
    username = db.Column(db.String(100), nullable=False)  # Customer's username
    email = db.Column(db.String(100), unique=True, nullable=False)  # Unique email for the customer
    password = db.Column(db.String(100), nullable=False)  
    address = db.Column(db.String(100), nullable=False)  
    pincode = db.Column(db.Integer, nullable=False)  
    mobile = db.Column(db.String(15), nullable=False)  
    status = db.Column(db.String(20), nullable=False, default='pending')  # Account status (pending, accepted, rejected)

    # Predefined status options for easy reference
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    
     # Establish relationship with ServiceRequest and enable cascade delete
    service_requests = db.relationship('ServiceRequest', backref='customer', lazy=True, cascade="all, delete-orphan")

# Model for Service Professional Table
class ServiceProfessional(db.Model):
    __tablename__ = 'service_professionals'
    
    # Define columns for the service professional table
    id = db.Column(db.Integer, primary_key=True)  # Primary key for the service professional
    username = db.Column(db.String(100), nullable=False)  # Username of the professional
    email = db.Column(db.String(120), unique=True, nullable=False)  # Email (must be unique)
    password = db.Column(db.String(128), nullable=False) 
    service_type = db.Column(db.String(100), nullable=False) 
    experience = db.Column(db.Integer, nullable=False) 
    pincode = db.Column(db.String(10), nullable=False)  
    address = db.Column(db.String(255), nullable=False)  
    resume_file_path = db.Column(db.String(255), nullable=True)  
    status = db.Column(db.String(20), nullable=False, default='pending')  # Status (pending, accepted, rejected)
    mobile_no = db.Column(db.String(15), nullable=False)  
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)

    # Predefined status options for easy reference
    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_CLOSED = "closed"  # Status for closed service requests
    
    # Establish a one-to-many relationship with the ServiceRequest model
    service_requests = db.relationship('ServiceRequest', backref='service_professional', lazy=True)

# Model for Service Table
class Service(db.Model):
    __tablename__ = 'services'  
    
    # Define columns for the service table
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)  # Name of the service (e.g., plumbing, cleaning)
    description = db.Column(db.Text, nullable=False)  
    base_price = db.Column(db.Float, nullable=False)  

    # One-to-many relationship with the ServiceRequest model (a service can have many requests)
    service_requests = db.relationship('ServiceRequest', backref='service', lazy=True, cascade="all, delete-orphan")

# Model for Service Request Table
class ServiceRequest(db.Model):
    __tablename__ = 'service_requests'  # Define the table name in database
    
    # Define columns for the service request table
    id = db.Column(db.Integer, primary_key=True)  
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False)  # Foreign key linking to the Service table
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False)  # Foreign key linking to the Customer table
    professional_id = db.Column(db.Integer, db.ForeignKey('service_professionals.id'), nullable=True)  # Optional foreign key for the professional assigned to the request
    request_date = db.Column(db.DateTime, nullable=False)  # The date and time when the request was made
    status = db.Column(db.String(50), default="Pending")  # Status of the request (e.g., Pending, Accepted, Completed)
    rating = db.Column(db.Integer, nullable=True)  
    remarks = db.Column(db.String(500), nullable=True) 
    
    

      # Methods to change the status of the request (e.g., Accept, Reject, Close , remarks)
    def accept_request(self):
        self.status = "Accepted"
        db.session.commit()

    def reject_request(self):
        self.status = "Rejected"
        db.session.commit()

    def close_request(self):
        self.status = "Closed"
        db.session.commit()

    def set_rating(self, rating):
        self.rating = rating
        db.session.commit()

    def close_by_customer(self):
        self.status = "Closed by Customer"
        db.session.commit()

    def set_remarks(self, remarks):
        self.remarks = remarks
        db.session.commit()


######################################## Database Initialization ###############################################

# Create the database tables if they do not exist already
with app.app_context():
    db.create_all()  # Creates the tables based on the models if they don't already exist
