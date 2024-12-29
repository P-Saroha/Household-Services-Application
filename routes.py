from flask import render_template, request, redirect, url_for, flash, Flask, session ,send_from_directory
from datetime import datetime
import os
from werkzeug.utils import secure_filename 
from werkzeug.security import generate_password_hash

from models import app, db, Customer, ServiceProfessional , Service, ServiceRequest 

######################################## Home Route ###################################################

# Route for the home page, which will render index.html
@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("index.html")  
###################################################################################################
################################## About US #######################################################
# Route for the "About Us" page
@app.route('/about')
def about():
    return render_template('about.html') # This will render the about.html file

#################################### Customer Signup ##################################################

# Route for customer signup page and account creation
@app.route('/customer_signup', methods=['GET', 'POST'])
def create_customer_account():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        address = request.form['address']
        pincode = request.form['pincode']
        mobile = request.form['mobile']

        # password validation
        if len(password) < 6 and len(password)>10:
            flash("pasword must be between 6 to 10 characters long")
            return redirect(url_for('create_customer_account'))
        
        if not any(char.islower() for char in password):
            flash("password should contain at least one lowercase letter")
            return redirect(url_for('create_customer_account'))
        
        if not any(char.isupper() for char in password):
            flash("password should contain at least one uppercase letter")
            return redirect(url_for('create_customer_account'))
        if not any(char.isdigit() for char in password):

            flash("password should contain at least one digit")
            return redirect(url_for('create_customer_account'))

        # Check if username already exists
        if Customer.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('create_customer_account'))

        # Check if email already exists
        if Customer.query.filter_by(email=email).first():
            flash('Email already exists. Please use a different email.', 'error')
            return redirect(url_for('create_customer_account'))
        # hash the password
        password_hash = generate_password_hash(password)
        # Create new customer and add to database
        new_customer = Customer(username=username, email=email, password=password,
                                address=address, pincode=pincode, mobile=mobile)
        db.session.add(new_customer)
        db.session.commit()
        flash('Account created successfully! You can log in now.', 'success')
        return redirect(url_for('login'))

    return render_template('customer_signup.html')

########################### Combined login route for both customer and professional  ######################################

@app.route('/login', methods=['GET', 'POST'])
def login():
    # Handles user login for both customers and service professionals    
    # Check if the request method is POST (form submission)
    if request.method == 'POST':
        # Retrieve form data: username, password, and user type (customer or service professional)
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']

        # If the user is a customer
        if user_type == 'customer':
            # Query the database for a customer with the provided username
            customer = Customer.query.filter_by(username=username).first()
            
            # Check if the customer exists and if the password matches
            if customer and customer.password == password:  # Direct password comparison
                # Check if the customer's status is 'rejected'
                if customer.status == Customer.STATUS_REJECTED:
                    flash("Your account has been rejected. Please contact support for further assistance.", "danger")
                    return redirect(url_for('login'))

                # Store customer details in the session
                session['customer_id'] = customer.id
                session['customer_name'] = customer.username
                flash('Customer login successful!', 'success')  # Provide feedback for successful login
                
                # Redirect to the customer dashboard
                return redirect(url_for('customer_dashboard'))
            
            # Flash error message if login fails
            flash('Customer login failed! Check your credentials.', 'danger')

        # If the user is a service professional
        elif user_type == 'service_professional':
            # Query the database for a service professional with the provided username
            professional = ServiceProfessional.query.filter_by(username=username).first()
            
            # Check if the professional exists and if the password matches
            if professional and professional.password == password:  # Direct password comparison
                # Check if the professional's status is 'rejected'
                if professional.status == ServiceProfessional.STATUS_REJECTED:
                    flash("Your account has been rejected. Please contact support for further assistance.", "danger")
                    return redirect(url_for('login'))

                # Store professional details in the session
                session['professional_id'] = professional.id
                session['professional_name'] = professional.username
                flash('Service Professional login successful!', 'success')  # Provide feedback for successful login
                
                # Redirect to the professional dashboard
                return redirect(url_for('professional_dashboard'))
            
            # Flash error message if login fails
            flash('Service Professional login failed! Check your credentials.', 'danger')

    # For GET request or failed login, render the login page
    return render_template('login.html')

############################################## Logout for all three  #############################################
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('home'))  # Redirect to the home page

#######################################################################################################

############################# Service Professional Signup and Resume Upload ############################

# Set upload folder and allowed extensions for resume files
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Service Professional Routes
@app.route('/service_professional_signup', methods=['GET', 'POST'])
def create_service_professional_account():
    if request.method == 'POST':
        # Retrieve form data for new service professional account
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        service_id = request.form['service_id']
        service_type = Service.query.get(service_id).name
        experience = request.form['experience']
        pincode = request.form['pincode']
        address = request.form['address']
        mobile_no = request.form['mobile_no']
        resume_file = request.files.get('resume_file')

        # Ensure the upload folder exists; create it if it doesn't
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

        resume_path = None
        # If a resume file is uploaded and its extension is allowed, save it
        if resume_file and allowed_file(resume_file.filename):
            filename = secure_filename(resume_file.filename)
            resume_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            resume_file.save(resume_path)

        # Check if username already exists in the database
        if ServiceProfessional.query.filter_by(username=username).first():
            flash("Username already exists. Please choose a different one.", "error")
            return render_template('service_professional_signup.html')

        # Check if email already exists in the database
        if ServiceProfessional.query.filter_by(email=email).first():
            flash("Email already exists. Please use a different email.", "error")
            return render_template('service_professional_signup.html')

        # Create a new ServiceProfessional object and populate it with form data
        new_professional = ServiceProfessional(
            username=username,
            email=email,
            password=password,
            service_id=service_id,  # Retrieve the service ID from the form data
            service_type=service_type,
            experience=experience,
            pincode=pincode,
            address=address,
            status=ServiceProfessional.STATUS_PENDING,  # Set the default status to 'Pending'
            mobile_no=mobile_no,
            resume_file_path=resume_path  # Store the file path of the uploaded resume
        )
        
        # Add the new professional to the database and commit the transaction
        db.session.add(new_professional)
        db.session.commit()
        
        # Flash a success message and redirect to the login page
        flash('Account created successfully! You can log in now.', 'success')
        return redirect(url_for("login"))  # Redirect to the combined login page

    # Render the service professional signup page if the request method is GET
    services = Service.query.all()
    return render_template('service_professional_signup.html', services=services)


#######################################################################################################

########################################## Admin Part #################################################

# Admin Login Route
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    # 'error' variable stores any error messages to be displayed on the login page
    error = None
    # Define superuser credentials as a dictionary (key-value pair of username: password)
    superuser = {'Parveen': 'saroha123'}
    
    # If the request method is GET (initial page load)
    if request.method == 'GET':
        return render_template('admin_login.html')
    
    # If the request method is POST (form submission)
    elif request.method == 'POST':
        # Retrieve the 'username' and 'password' from the form submission
        username = request.form['username']
        password = request.form['password']
        
        # Check if the provided username exists in the superuser dictionary and if the password matches
        if username in superuser and superuser[username] == password:
            return redirect(url_for('admin_dashboard'))
        else:
            error = 'Invalid credentials! Please try again.' # If credentials are invalid, set an error message
    
    # Render the admin login page again with the error message if login fails
    return render_template('admin_login.html', error=error)

####################################################################################################


######################################### Admin Dashboard () #######################################
# Route to display the admin dashboard with service requests, services, and professionals
@app.route('/admin_dashboard')
def admin_dashboard():
    services = Service.query.all()
    professionals = ServiceProfessional.query.all()
    service_requests = ServiceRequest.query.all()
    customers  = Customer.query.all()

    # Modify professionals to ensure only the filename is stored in `resume_file_path`
    for professional in professionals:
        professional.resume_file_path = os.path.basename(professional.resume_file_path)

    return render_template('admin_dashboard.html', services=services, professionals=professionals, service_requests=service_requests,customers = customers)

######################################### Directory containing the resumes ####################################
RESUME_DIR = 'uploads'

@app.route('/resume/<filename>')
def serve_resume(filename):
    return send_from_directory(RESUME_DIR, filename)
#######################################################################################################

####################################### Admin search ####################################################

@app.route('/admin_search', methods=['GET', 'POST'])
def admin_search():
    # Get the search query and selected category from the form
    search_query = request.form.get('search_query', '').strip()
    category = request.form.get('category')  # Get selected category from dropdown

    # Initialize empty lists to hold search results for each category
    service_requests = []
    customers = []
    professionals = []

    # Filter based on the selected category
    if category == 'service_requests':
        service_requests = ServiceRequest.query.filter(
            # Filter for matching customer username
            ServiceRequest.customer.has(Customer.username.ilike(f"%{search_query}%")) |
            # Filter for matching professional username
            ServiceRequest.service_professional.has(ServiceProfessional.username.ilike(f"%{search_query}%")) |
            # Filter for matching service name
            ServiceRequest.service.has(Service.name.ilike(f"%{search_query}%"))
        ).all()
    elif category == 'customers':
        customers = Customer.query.filter(Customer.username.ilike(f"%{search_query}%")).all()
    elif category == 'professionals':
        professionals = ServiceProfessional.query.filter(
            ServiceProfessional.username.ilike(f"%{search_query}%")
        ).all()

    # Pass results and selected category to the template
    return render_template(
        'admin_search.html',
        service_requests=service_requests,
        customers=customers,
        professionals=professionals,
        category=category
    )
#####################################################################################################

######################################### Admin summary  ##############################################
from sqlalchemy import func
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# Define route to render the admin summary page
@app.route('/admin_summary')
def admin_summary():
    # Query to get average rating for each service professional
    avg_rating_query = (
        db.session.query(ServiceProfessional.username, func.avg(ServiceRequest.rating).label('avg_rating'))
        .join(ServiceRequest, ServiceProfessional.id == ServiceRequest.professional_id)
        .filter(ServiceRequest.rating.isnot(None))
        .group_by(ServiceProfessional.username)
        .all()
    )
    avg_rating_dict = {professional: avg_rating for professional, avg_rating in avg_rating_query}

    # Query to get the count of service requests by status
    status_counts_query = (
        db.session.query(ServiceRequest.status, func.count(ServiceRequest.id))
        .group_by(ServiceRequest.status)
        .all()
    )
    request_status_dict = {status: count for status, count in status_counts_query}

    # Populate the dictionary with service request statuses
    service_requests = ServiceRequest.query.all()
    status_dict = {'Closed': 0, 'Accepted': 0, 'Rejected': 0,'Pending': 0 }
    for service in service_requests:
        status_dict[service.status] += 1

    # Create a histogram using Matplotlib
    labels = list(status_dict.keys())
    values = list(status_dict.values())
    
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=['blue', 'orange', 'red'])
    plt.xlabel('Status')
    plt.ylabel('Count')
    plt.title('Service Request Status Summary')

    # Setting y-axis values to integer
    plt.yticks(range(0, max(values) + 1, 1))

    # Save the histogram to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Convert the BytesIO object to a base64-encoded image
    image = base64.b64encode(buf.getvalue()).decode('utf8')
    buf.close()

    # Render the template with queried data and the image
    return render_template(
        'admin_summary.html',
        avg_rating_dict=avg_rating_dict,
        request_status_dict=request_status_dict,
        service_requests=service_requests,
        image=image
    )
#####################################################################################################

###################################### Services Handle by Admin #############################################

# Route to create a new service
@app.route('/create_service', methods=['GET', 'POST'])
def create_service():
    # Handles the creation of a new service with GET and POST methods
    
    if request.method == 'POST':
        # Retrieve service details from the form: name, description, and base price
        name = request.form.get('name')
        description = request.form.get('description')
        base_price = request.form.get('base_price')

        # Create a new Service instance with the provided details
        new_service = Service(name=name, description=description, base_price=float(base_price))
        
        # Add the new service to the database session and commit changes
        db.session.add(new_service)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    # If the request method is GET, render the create service page with the form
    return render_template('create_service.html')


# Route to edit an existing service
@app.route('/edit_service/<int:service_id>', methods=['GET', 'POST'])
def edit_service(service_id):
    # Handles editing of an existing service identified by 'service_id'
    
    # Retrieve the service from the database or return a 404 error if not found
    service = Service.query.get_or_404(service_id)

    # If the request method is POST (form submission)
    if request.method == 'POST':
        # Update the service details with values from the form
        service.name = request.form.get('name')
        service.description = request.form.get('description')
        service.base_price = request.form.get('base_price')

        # Commit the updated service details to the database
        db.session.commit()
        return redirect(url_for('admin_dashboard'))

    # If the request method is GET, render the edit service page with the current service details
    return render_template('edit_service.html', service=service)


# Route to delete a service
@app.route('/delete_service/<int:service_id>', methods=['POST'])
def delete_service(service_id):
    # Handles deletion of an existing service identified by 'service_id'
    
    # Retrieve the service from the database or return a 404 error if not found
    service = Service.query.get_or_404(service_id)
    
    # Delete the service from the database and commit changes
    db.session.delete(service)
    db.session.commit()
    
    # Redirect to the admin dashboard after successful deletion
    return redirect(url_for('admin_dashboard'))


##########################################  admin handle service professional status ###############################

# Route for updating the status of a professional (Approve/Reject)
@app.route('/update_professional_status/<int:professional_id>', methods=['POST'])
def update_professional_status(professional_id):

    professional = ServiceProfessional.query.get_or_404(professional_id)  # Retrieve the professional by their ID
    new_status = request.form.get('status')  # Get the new status from the form data
    
    # Check if the new status is valid
    if new_status in ['approved', 'rejected']:
        # Update the status of the professional
        professional.status = new_status
        db.session.commit()  
        
        flash(f'Professional status updated to {new_status.capitalize()}', 'success')  # Display a success message
    else:
        flash('Invalid status update', 'danger')  # If the status is invalid, show an error message   
    return redirect(url_for('admin_dashboard')) 

# Route for deleting a professional
@app.route('/delete_professional/<int:professional_id>', methods=['POST'])
def delete_professional(professional_id):
    professional = ServiceProfessional.query.get_or_404(professional_id)   # Retrieve the professional by their ID
    
    db.session.delete(professional)  # Delete the professional from the database
    db.session.commit()  
    flash('Professional deleted successfully', 'success')  
    
    return redirect(url_for('admin_dashboard'))  # Redirect back to the dashboard after deletion

####################################################################################################################

############################################## admin handels customers ###########################################
# Block customer route
@app.route('/block_customer/<int:customer_id>', methods=['POST'])
def block_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        customer.status = Customer.STATUS_REJECTED
        db.session.commit()
        flash('Customer has been blocked', 'success')
    else:
        flash('Customer not found', 'danger')
    return redirect(url_for('admin_dashboard'))

# unblock the customer
@app.route('/unblock_customer/<int:customer_id>', methods=['POST'])
def unblock_customer(customer_id):
    customer = Customer.query.get(customer_id)
    if customer:
        customer.status = Customer.STATUS_ACCEPTED

        db.session.commit()
        flash('Customer has been blocked', 'success')
    else:
        flash('Customer not found', 'danger')
    return redirect(url_for('admin_dashboard'))

# Delete route for customer
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
def delete_customer(customer_id):
    customer = Customer.query.get(customer_id)

    if customer:
        # Deleting the customer will automatically delete related service requests due to cascade
        db.session.delete(customer)
        db.session.commit()
        flash("Customer deleted successfully!", "success")
    else:
        flash("Customer not found!", "danger")

    return redirect(url_for('admin_dashboard'))

###################################### Professional Dashboard ###########################################################

# Route for Professional Dashboard
@app.route('/professional_dashboard')
def professional_dashboard():
    # Check if the professional is logged in by verifying if 'professional_id' is in session
    if 'professional_id' not in session:
        return redirect(url_for('login'))  
    
    # Retrieve the logged-in professional's details from the database using their ID in session
    professional = ServiceProfessional.query.get(session['professional_id'])
    
    # Query for all service requests with 'Pending' status that have not been assigned to any professional
    pending_requests = ServiceRequest.query.filter(
        ServiceRequest.status == 'Pending',
        ServiceRequest.service_id == professional.service_id,
        ServiceRequest.professional_id == None  # Filter for requests not yet accepted by any professional
    ).all()
    
    # Query for all closed service requests
    # closed_service_request = ServiceRequest.query.filter_by(status='Closed').all()
    closed_service_request = ServiceRequest.query.filter(
        ServiceRequest.status == 'Closed',
        ServiceRequest.service_id == professional.service_id,  # Filter for requests closed by the professional
        ServiceRequest.professional_id ==  professional.id
    )

    # Render the professional dashboard template with data for the professional, pending requests, and closed requests
    return render_template(
        'professional_dashboard.html', 
        professional=professional, 
        today_services=pending_requests, 
        closed_service_request=closed_service_request
    )

# Route to accept a service request
@app.route('/accept_service/<int:service_id>', methods=['POST', 'GET'])
def accept_service(service_id):
    # Retrieve the service request from the database by its ID
    service_request = ServiceRequest.query.get(service_id)
    
    # If the service request exists
    if service_request:
        service_request.accept_request() # Update the request status to 'accepted' using a custom method
        
        # Set the professional ID in the service request to the logged-in professional's ID
        service_request.professional_id = session.get('professional_id')
        
        # Add the updated service request to the database session and commit the changes
        db.session.add(service_request)
        db.session.commit()  # Commit changes to save the acceptance
        
        # Display a success message indicating that the service request was accepted
        flash(f"Service Request {service_id} accepted!", "success")
    return redirect(url_for('professional_dashboard'))# Redirect to the professional dashboard after accepting the request


# Route to reject a service request
@app.route('/reject_service/<int:service_id>', methods=['POST', 'GET'])
def reject_service(service_id):
    service_request = ServiceRequest.query.get(service_id)# Retrieve the service request from the database by its ID
    
    # If the service request exists
    if service_request:    
        service_request.status = 'Rejected' # Update the request status to 'Rejected'
        service_request.professional_id = None # Set the professional ID to None as no professional is handling the request
        service_request.professional_id = session.get('professional_id')# Record the professional who rejected the service
        
        # Commit the changes to the database
        db.session.add(service_request)
        db.session.commit()
        
        # Display a danger message indicating that the service request was rejected
        flash(f"Service Request {service_id} rejected!", "danger")
    
    # Redirect to the professional dashboard after rejecting the request
    return redirect(url_for('professional_dashboard'))


########################################### professinal Search #########################################################

# Route to search for service requests or customers based on different criteria
@app.route('/service_professional_search', methods=['GET'])
def service_professional_search():
    # Get the search criteria and search text from the query parameters
    search_by = request.args.get('search_by')  # Criteria by which to search (date, location, or pin)
    search_text = request.args.get('search_text')  # Text to search for based on selected criteria
    search_results = []  # Initialize an empty list for search results

    # Proceed with search if both criteria and search text are provided
    if search_by and search_text:
        # If searching by date
        if search_by == 'date':
            try:
                # Convert the search text into a date object (expects format dd/mm/yyyy)
                search_date = datetime.strptime(search_text, '%d/%m/%Y').date()
                # Query for service requests on the specified date
                search_results = ServiceRequest.query.filter_by(request_date=search_date).all()
            except ValueError:
                # If date format is incorrect, return an empty result set
                search_results = []
        
        # If searching by location
        elif search_by == 'location':
            # Search for customers with an address that includes the search text, case-insensitive
            search_results = Customer.query.filter(Customer.address.ilike(f'%{search_text}%')).all()
        
        # If searching by pin code
        elif search_by == 'pin':
            # Query for customers with a matching pin code
            search_results = Customer.query.filter(Customer.pincode == search_text).all()

    # Render the search results in the professional_search template
    return render_template('professional_search.html', search_results=search_results)

#########################################################################################################################

################################ Professional summary ##########################################################
from io import BytesIO

@app.route('/professional_summary')
def professional_summary():
    # Query to get average rating for each service professional
    avg_rating_query = (
        db.session.query(ServiceProfessional.username, func.avg(ServiceRequest.rating).label('avg_rating'))
        .join(ServiceRequest, ServiceProfessional.id == ServiceRequest.professional_id)
        .filter(ServiceRequest.rating.isnot(None))
        .group_by(ServiceProfessional.username)
        .all()
    )
    avg_rating_dict = {professional: avg_rating for professional, avg_rating in avg_rating_query}

    # Query to get the count of service requests by status
    status_counts_query = (
        db.session.query(ServiceRequest.status, func.count(ServiceRequest.id))
        .group_by(ServiceRequest.status)
        .all()
    )
    # Initialize a dictionary for statuses
    status_dict = {'Accepted': 0, 'Rejected': 0, 'Closed': 0}
    for status, count in status_counts_query:
        if status in status_dict:
            status_dict[status] += count

    # Create a bar graph for service request statuses
    labels = list(status_dict.keys())
    values = list(status_dict.values())
    
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=['green', 'red', 'gray'])
    plt.xlabel('Status')
    plt.ylabel('Count')
    plt.title('Service Request Status for Professionals')

    # Save the bar graph to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Convert the BytesIO object to a base64-encoded image
    image = base64.b64encode(buf.getvalue()).decode('utf8')
    buf.close()

    # Render the template with queried data and the image
    return render_template(
        'professional_summary.html',
        avg_rating_dict=avg_rating_dict,
        status_dict=status_dict,
        image=image
    )
####################################################################################################################

######################################## Customer #####################################################################
# Route to display the customer dashboard
@app.route('/customer_dashboard')
def customer_dashboard():
    # Check if the customer is logged in
    if 'customer_id' not in session:
        flash('You need to log in first.')
        return redirect(url_for('login'))  # Redirect to login if not logged in

    customer = Customer.query.get(session['customer_id'])   # Retrieve the logged-in customer's details
    
    # Get the service history for the customer
    service_history = ServiceRequest.query.filter_by(customer_id=customer.id).all()
    
    # Fetch all available services (optional, if additional details about services are needed)
    services = Service.query.all()

    # Render the customer dashboard template with customer and service history data
    return render_template(
        'customer_dashboard.html',
        customer=customer,
        service_history=service_history,
        services=services
    )

# Route to close a service request
@app.route('/close_service/<int:service_id>', methods=['POST'])
def close_service(service_id):
    service_request = ServiceRequest.query.get(service_id) # Retrieve the service request to be closed
    
    # Check if the service request exists and belongs to the logged-in customer
    if service_request and service_request.customer_id == session.get('customer_id'):
        remarks = request.form.get('remarks')# Get the remarks from the form
        
        # Set the remarks if provided
        if remarks:
            service_request.set_remarks(remarks)
        
        # Mark the request as closed
        service_request.close_request()
        flash("Service request closed successfully.", "success")
    else:
        flash("Service request not found or unauthorized action.", "danger")
    
    return redirect(url_for('customer_dashboard'))

# Route to rate a completed service request
@app.route('/rate_service/<int:service_id>', methods=['POST'])
def rate_service(service_id):
    # Retrieve the rating value from the form submission
    rating = request.form.get('rating')
    
    remarks = request.form.get('remarks') # Retrieve the remarks from the form
      
    service_request = ServiceRequest.query.get(service_id)# Retrieve the service request to be rated
    
    # Check if the service request exists and belongs to the logged-in customer
    if service_request and service_request.customer_id == session.get('customer_id'):
        service_request.set_rating(rating) # Set the rating for the service request
        
        # Set the remarks for the service request
        if remarks:
            service_request.set_remarks(remarks)
        
        flash("Service rated successfully!", "success")
    else:
        flash("Service request not found or unauthorized action.", "danger")# Show an error message if the request doesn't exist or unauthorized access
    
    return redirect(url_for('customer_dashboard')) # Redirect back to the customer dashboard

#######################################  Booking Route for Customers #########################################################

# Route to allow customers to book a service
@app.route("/book_service/<int:service_id>", methods=["GET", "POST"])
def book_service(service_id):
    # Retrieve the customer ID from session data
    customer_id = session.get("customer_id")
    
    # If the customer is not logged in, prompt them to log in and redirect to the login page
    if not customer_id:
        flash("Please log in to book a service.", "error")
        return redirect(url_for("login"))

    # If the request method is POST, handle the service booking process
    if request.method == "POST": 
        date_of_booking = request.form.get("date_of_booking") # Retrieve the booking date entered by the customer in the form

        # Check if a booking date was provided
        if date_of_booking:
            try:
                # Attempt to parse the provided date in the format YYYY-MM-DD
                booking_date = datetime.strptime(date_of_booking, "%Y-%m-%d")
                
                # Create a new service request with 'Pending' status and no assigned professional initially
                new_request = ServiceRequest(
                    service_id=service_id,
                    customer_id=customer_id,
                    request_date=booking_date,
                    status='Pending',       # Default status is set to 'Pending'
                    professional_id=None    # No professional assigned at booking
                )
                
                # Add the new service request to the database session and commit the changes
                db.session.add(new_request)
                db.session.commit()
                
                # Display success message and redirect to the customer dashboard
                flash("Service booked successfully!", "success")
                return redirect(url_for("customer_dashboard"))
                   
            except ValueError: # Handle errors in date format parsing
                flash("Invalid date format. Please select a valid booking date.", "error")
            
            # Handle other database-related or unexpected exceptions
            except Exception as e:
                db.session.rollback()  # Roll back the session in case of an error
                flash(f"Error booking service: {str(e)}", "danger")
        else:
            flash("Please select a valid booking date.", "error")# Prompt the user to select a booking date if it was not provided
    
    # Render the service booking template, passing the service ID for the booking form
    return render_template("book_service.html", service_id=service_id)

########################### Customer search #########################################################

# Route for customer search functionality
@app.route('/customer_search', methods=['GET'])
def customer_search():
    # Retrieve the search criteria (e.g., service type, location, pincode) and search query from the request arguments
    search_criteria = request.args.get('search_criteria')
    search_query = request.args.get('search_query')

    # Initialize an empty list to hold the search results (Service Professionals)
    professionals = []

    # Check if both search criteria and query are provided
    if search_criteria and search_query:
        # Perform search based on the selected criteria
        if search_criteria == 'service_type':
            # Search for professionals based on the service type
            professionals = ServiceProfessional.query.filter(ServiceProfessional.service_type.ilike(f"%{search_query}%")).all()
        elif search_criteria == 'location':
            # Search for professionals based on their address location
            professionals = ServiceProfessional.query.filter(ServiceProfessional.address.ilike(f"%{search_query}%")).all()
        elif search_criteria == 'pincode':
            # Search for professionals based on their pincode
            professionals = ServiceProfessional.query.filter(ServiceProfessional.pincode.ilike(f"%{search_query}%")).all()

    # Render the customer_search.html template, passing the search results and the original search query
    return render_template('customer_search.html', professionals=professionals, search_query=search_query)


################################################ Customer summary ########################################################

@app.route('/customer_summary')
def customer_summary():
    # Query to get the count of service requests by status for customers
    status_counts_query = (
        db.session.query(ServiceRequest.status, func.count(ServiceRequest.id))
        .group_by(ServiceRequest.status)
        .all()
    )
    
    # Initialize dictionary for statuses
    status_dict = {'Accepted': 0, 'Rejected': 0, 'Closed': 0}
    for status, count in status_counts_query:
        if status in status_dict:
            status_dict[status] += count

    # Create a bar graph for service request statuses for customers
    labels = list(status_dict.keys())
    values = list(status_dict.values())
    
    plt.figure(figsize=(8, 5))
    plt.bar(labels, values, color=['blue', 'red', 'gray'])
    plt.xlabel('Status')
    plt.ylabel('Count')
    plt.title('Customer Service Request Status Summary')

    # Save the bar graph to a BytesIO object
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Convert the BytesIO object to a base64-encoded image
    image = base64.b64encode(buf.getvalue()).decode('utf8')
    buf.close()

    # Render the template with the image and status data
    return render_template(
        'customer_summary.html',
        status_dict=status_dict,
        image=image
    )

#############################################################################################################

# Made by Parveen Saroha 
# ROll NO - 21f3001560
# Mad 1 project 