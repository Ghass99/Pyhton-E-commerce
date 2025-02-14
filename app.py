from itertools import chain
from flask import Flask, jsonify, render_template, redirect, request, send_from_directory, session, url_for, flash
import stripe
from flask_cors import CORS
import os
from datetime import timedelta

stripe.api_key = 'sk_test_51QfOxdEQ9pnqxHRoSCeox4aoVW1xG6Odw0D8czUNETnprGyUyORrnqrHOjJwUDxGhEooKLoLeJyrUwU05yNjVNfP00Vd1UHlhL'

app = Flask(__name__, static_folder='Statics')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=2)
app.secret_key = os.urandom(24)
CORS(app)

active_users = set()
# Sample product data
products = [
    {"id": 1, "name": "Product A", "price": 19.99, "description": "Description of Product A", "image": "/Statics/images/post-item1.jpg"},
    {"id": 2, "name": "Product B", "price": 29.99, "description": "Description of Product B", "image": "/Statics/images/post-item2.jpg"},
    {"id": 3, "name": "Product C", "price": 39.99, "description": "Description of Product C", "image": "/Statics/images/post-item3.jpg"},
    {"id": 9, "name": "Product H", "price": 30.99, "description": "Description of Product H", "image": "/Statics/images/post-item4.jpg"},
]
users = {
    "user@example.com": "password123",
    "admin@example.com": "adminpass"
}
productsW = [
    {"id":4, "name": "Product W1", "price": 19.99, "description": "Description of Product A", "image": "/Statics/images/post-item7.jpg"},
    {"id": 5, "name": "Product W2", "price": 29.99, "description": "Description of Product B", "image": "/Statics/images/post-item5.jpg"},
    {"id": 6, "name": "Product W3", "price": 39.99, "description": "Description of Product C", "image": "/Statics/images/post-item6.jpg"},
    {"id": 7, "name": "Product W4", "price": 30.99, "description": "Description of Product C", "image": "/Statics/images/card-item6.jpg"},
]
# Homepage Route
@app.route('/Statics/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

@app.route('/')
def home():
    cart = session.get('cart', [])
    total = 0

    # Calculate the total price of the cart
    for item in cart:
        total += item['price'] * item['quantity']

    total = round(total, 2)
    return render_template('index.html', products=products,productsW=productsW, cart=cart, total=total)

# Products Route
@app.route('/products')
def products_page():
    return render_template('products.html', products=products)

@app.before_request
def check_session_timeout():
    session.modified = True  
    if 'email' in session and not session.permanent:
        session.pop('email', None)
        active_users.discard(session.get('email', None))
        flash("Session expired. Please log in again.", "info")
        return redirect(url_for('home'))

# Product Details Route
@app.route('/products/<int:product_id>')
def product_details(product_id):
    product = next((p for p in products if p['id'] == product_id), None)
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for('products_page'))
    return render_template('product_details.html', product=product)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'email' not in session:
        flash("You must be logged in to add items to the cart.", "warning")
        return redirect(url_for('home'))

    product_id = int(request.form['product_id'])
    quantity = int(request.form['quantity'])
    
    product = next((item for item in chain(products, productsW) if item['id'] == product_id), None)
    if not product:
        flash("Product not found!", "danger")
        return redirect(url_for('home'))

    if 'cart' not in session:
        session['cart'] = []

    found = False
    for item in session['cart']:
        if item['id'] == product_id:
            item['quantity'] += quantity
            found = True
            break

    if not found:
        session['cart'].append({
            'id': product['id'],
            'name': product['name'],
            'price': product['price'],
            'image': product['image'],
            'quantity': quantity
        })

    session.modified = True
    flash("Item added to cart!", "success")
    return redirect(url_for('home'))


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form['product_id'])

    # Check if 'cart' exists in the session
    if 'cart' in session:
        # Filter out the product from the cart
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
    
    session.modified = True  # Mark session as modified
    return redirect(url_for('home'))  # Redirect back to the homepage or cart page


@app.route('/cart')
def cart():
    return render_template('cart.html')

# Profile Route
@app.route('/profile')
def profile():
    return render_template('profile.html', user={"name": "John Doe", "email": "john@example.com"})

@app.route('/checkout', methods=['POST','GET'])
def checkout():
    cart = session.get('cart', [])
    total = 0

    for item in cart:
        total += item['price'] * item['quantity']

    total_price = round(total, 2)

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(total_price * 100),  # Stripe accepts amount in cents
            currency='usd',
            metadata={'integration_check': 'accept_a_payment'},
        )
        return jsonify({'client_secret': intent.client_secret})

    except Exception as e:
        return jsonify(error=str(e)), 403

@app.route('/payment_success', methods=['GET'])
def payment_success():
    # Render a payment success page or handle order logic
    session.pop('cart', None)
    return redirect(url_for('home'))

# Login Route
@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if active_users:
        flash("Another user is already active. Please try again later.", "danger")
        return redirect(url_for('home'))
    if username in users and users[username] == password:
        session['email'] = username
        session.permanent = True  
        active_users.add(username)
        flash("Login successful!", "success")
        return redirect(url_for('home'))
    else:
        flash("Invalid username or password.", "danger")
        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    email = session.pop('email', None)
    if email:
        active_users.discard(email)  # Remove from active users
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))



if __name__ == '__main__':
    app.run(debug=True)
