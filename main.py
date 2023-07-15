import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import exc
from werkzeug.utils import secure_filename


app = Flask(__name__)

app = Flask(__name__)
app.secret_key = 'somekey123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///utsceats.db'

db= SQLAlchemy(app)

# Upload image files to static
UPLOAD_FOLDER = './static/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Order status constants
FULFILLED = 'Order Fulfilled'
PROCESSING = 'Processing'
ORDERED = 'Ordered'
COMPLETED = 'Completed, Ready to Pickup'

# Allow image files only
def image_check(image_file):
    return '.' in image_file and image_file.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Database tables
class User(db.Model):
  __tablename__ = 'User'
  email = db.Column(db.String, primary_key=True)
  password = db.Column(db.String, nullable=False)
  name = db.Column(db.String, nullable=False)

class Vendor(db.Model):
  __tablename__ = 'Vendor'
  vendor_password = db.Column(db.String, nullable=False)
  vendor_name = db.Column(db.String, primary_key=True)
  vendor_address = db.Column(db.String, nullable=False)
  vendor_building = db.Column(db.String, nullable=False)
  vendor_image = db.Column(db.String, nullable=True)

class Food(db.Model):
  __tablename__ = 'Food'
  id = db.Column(db.Integer, primary_key=True)
  vendor = db.Column(db.String, db.ForeignKey('Vendor.vendor_name'))
  food_name = db.Column(db.String, nullable=False)
  price = db.Column(db.Float, nullable=False)
  description = db.Column(db.String, nullable=False)
  image = db.Column(db.String, nullable=False)
  
class Food_Orders(db.Model):
  __tablename__ ='Orders'
  id = db.Column(db.Integer, primary_key=True)
  vendor = db.Column(db.String, db.ForeignKey('Vendor.vendor_name'))
  customer_id = db.Column(db.String, db.ForeignKey('User.email'))
  customer_name = db.Column(db.String, db.ForeignKey('User.name'))
  status = db.Column(db.String, nullable=False)
  total_cost = db.Column(db.Float, nullable=False)
  time_of_order = db.Column(db.DateTime)
  time_of_completion = db.Column(db.DateTime)
  
class Food_Order(db.Model):
  __tablename__ = 'Order'
  order_item_id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, db.ForeignKey('Orders.id'))
  menu_item_id = db.Column(db.Integer, db.ForeignKey('Food.id'))
  food_item = db.Column(db.String,  db.ForeignKey('Food.id'))
  qty = db.Column(db.Integer, nullable=False)
  special_requests = db.Column(db.String, nullable=False)
  price = db.Column(db.Integer, nullable=False)
  
with app.app_context():
  #db.drop_all()
  db.create_all()

# Home, login, signin, signout, register pages for user and vendor
@app.route('/')
def home():
    if 'user' in session:
      return render_template('index.html', user=session['user'].title())
    return render_template('index.html')
  
@app.route('/api/login', methods=['GET', 'POST'])
def login_user():
  if request.method == 'GET':
    return render_template('login.html')
  else:
    email = request.form['email'].lower()
    password  = request.form['password']
    try:
      user = db.session.execute(db.select(User).filter_by(email=email)).scalar_one()
      if user.password == password:
        session['user'] = user.name
        session['email'] = user.email
        return redirect(url_for('home'))
      else:
        flash('Incorrect username/password. Please try again.', 'error')
        return redirect(url_for('login'))
    except exc.NoResultFound:
      flash('No records found. Please try again or register an account.', 'error')
      return redirect(url_for('login'))
  
@app.route('/login')
def login():
  return render_template('login.html')
  
@app.route('/api/register', methods=['GET', 'POST'])
def register_user():
    if request.method == 'GET':
      return redirect(url_for('register'))
    else:
      name = request.form['name'].lower()
      email = request.form['email'].lower()
      password = request.form['password']
      new_user = User(email = email, password = password, name = name)
      try:
        db.session.add(new_user)
        db.session.commit()
        flash('Success! Account Has Been Created! ', 'success')
        return redirect(url_for('register'))
      except exc.IntegrityError:
        flash('Email has already been registered with another account.', 'error')
        return redirect(url_for('register'))

@app.route('/signout')
def signout():
  if 'user' in session:
    session.pop('user')
    session.pop('email')
    flash('Logged out!', 'success')
    return redirect(url_for('home'))
  else:
    return redirect(url_for('vendor_home'))
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')
  
@app.route('/vendor/api/register', methods=['GET', 'POST'])
def register_vendor():
    if request.method == 'GET':
      return redirect(url_for('vendor_register'))
    else:
      vendor_name = request.form['vendor_name'].lower()
      password = request.form['password']
      address = request.form['address']
      building = request.form['building']
      new_vendor = Vendor(vendor_password = password, vendor_name=vendor_name, vendor_address=address, vendor_building=building)
      try:
        db.session.add(new_vendor)
        db.session.commit()
        flash('Success! Account Has Been Created! ', 'success')
        return redirect(url_for('vendor_register'))
      except exc.IntegrityError:
        flash('Another vendor has already been registered with the same name', 'error')
        return redirect(url_for('vendor_register'))  

@app.route('/vendor/home')
def vendor_home():
  if 'vendor_user' in session:
      return render_template('vendor_home.html', user=session['vendor_user'].title())
  return render_template('vendor_home.html')
    
@app.route('/vendor/login')
def vendor_login():
    return render_template('vendor_login.html')
  
@app.route('/vendor/register')
def vendor_register():
    return render_template('vendor_register.html')
  
@app.route('/vendor/signout')
def vendor_signout():
  if 'vendor_user' in session:
    session.pop('vendor_user')
    flash('Logged out!', 'success')
    return redirect(url_for('vendor_home'))
  else:
    return redirect(url_for('vendor_home'))
  
@app.route('/vendor/api/login', methods=['GET', 'POST'])
def login_vendor():
  if request.method == 'GET':
    return render_template('vendor_login.html')
  else:
    vendor_name = request.form['vendor_name'].lower()
    password  = request.form['vendor_password']
    try:
      vendor = db.session.execute(db.select(Vendor).filter_by(vendor_name=vendor_name)).scalar_one()
      if vendor.vendor_password == password:
        session['vendor_user'] = vendor.vendor_name
        return redirect(url_for('vendor_home'))
      else:
        flash('Incorrect username/password. Please try again.', 'error')
        return redirect(url_for('vendor_login'))
    except exc.NoResultFound:
      flash('Account not found. Register your account instead. ', 'error')
      return redirect(url_for('vendor_login'))
    
# Page to display all items of vendor's menu. Allows them to edit or delete. 
@app.route('/vendor/manage-menu')
def manage_menu():
  if 'vendor_user' in session:
    food_items={}
    food_list = db.session.execute(db.select(Food).filter_by(vendor=session['vendor_user'])).all()
    for food in food_list:
      for info in food:
        food_items[info.food_name] = [info.id, info.food_name, info.description, info.price, info.image]
    return render_template('manage-menu.html', foods=food_items, user=session['vendor_user'].title())
  else:
    flash('You are not signed in as vendor', 'error')
    return redirect(url_for('vendor_login'))
  
# Page for vendor to add items to menu. 
@app.route('/vendor/add-menu')
def add_menu():
  if 'vendor_user' in session:
    return render_template('add-menu.html')
  else:
    return redirect(url_for('manage_menu'))
  
# Adds menu item to DB. 
@app.route('/vendor/api/add-item', methods=['GET', 'POST'])
def add_item():
  if request.method == 'GET':
    return redirect(url_for('add_menu'))
  else:
    food_image = request.files['food_image']
    # If no image file given, set image of menu item to the generic. 
    if not food_image.filename:
        food_name = request.form['food_name']
        food_desc = request.form['food_desc']
        food_price = request.form['food_price']
        new_food = Food(vendor = session['vendor_user'], food_name=food_name, price=food_price, description=food_desc, image='generic_food_thumbnail.jpg')
        db.session.add(new_food)
        db.session.commit()
        flash('Menu item added with generic image!', 'success')
        return redirect(url_for('manage_menu'))
    # Add menu item with the image file that is given
    if food_image and image_check(food_image.filename):
        image_name = secure_filename(food_image.filename)
        food_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
        food_name = request.form['food_name']
        food_desc = request.form['food_desc']
        food_price = request.form['food_price']
        new_food = Food(vendor = session['vendor_user'], food_name=food_name, price=food_price, description=food_desc, image=image_name)
        db.session.add(new_food)
        db.session.commit()
        flash('Menu item added!', 'success')
        return redirect(url_for('manage_menu'))

# Delete specific vendor item menu
@app.route('/vendor/api/delete-item', methods=['GET', 'POST'])
def delete_vendor_item():
  if request.method=='GET':
    return redirect(url_for('manage_menu'))
  else:
    value = request.form['food-item']
    item_to_delete = db.session.execute(db.select(Food).filter_by(id=value)).scalar_one()
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for('manage_menu'))

# Edit menu item page
@app.route('/vendor/edit-item', methods=['POST', 'GET'])
def edit_vendor_item():
  if request.method=='GET':
    return redirect(url_for('manage_menu'))
  else:
    food_id = request.form['food-id']
    food_name = request.form['food-name']
    price = request.form['food-price']
    description = request.form['food-desc']
    image = request.form['food-image']
    return render_template('vendor_edit_item.html', food_name=food_name, price=price, description=description, image=image, food_id=food_id)
  
# Edit menu item attributes.
@app.route('/vendor/api/edit-item', methods=['POST', 'GET'])
def confirm_edit_item():
  if request.method == 'GET':
    return redirect(url_for('manage_menu'))
  else:
    food_image = request.files['food_image']
    # Changes menu attributes and image
    if food_image and image_check(food_image.filename):
        image_name = secure_filename(food_image.filename)
        food_image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_name))
        food_id = request.form['food_id']
        food_name = request.form['food_name']
        food_desc = request.form['food_desc']
        food_price = request.form['food_price']
        food_to_edit = db.session.execute(db.select(Food).filter_by(id=food_id)).scalar_one()
        food_to_edit.food_name = food_name
        food_to_edit.price = food_price
        food_to_edit.description = food_desc
        food_to_edit.image = image_name
        db.session.commit()
        flash('Menu item edited!', 'success')
        return redirect(url_for('manage_menu'))
    # If no image given, keep the current one
    else:
      food_id = request.form['food_id']
      food_name = request.form['food_name']
      food_desc = request.form['food_desc']
      food_price = request.form['food_price']
      food_image = request.form['current_image']
      food_to_edit = db.session.execute(db.select(Food).filter_by(id=food_id)).scalar_one()
      food_to_edit.food_name = food_name
      food_to_edit.price = food_price
      food_to_edit.description = food_desc
      food_to_edit.image = food_image
      db.session.commit()
      flash('Menu item edited!', 'success')
      return redirect(url_for('manage_menu'))
    
# Page that displays all vendors
@app.route('/vendors')
def vendors():
  vendor_info = {}
  vendors = db.session.execute(db.select(Vendor)).all()
  for vendor in vendors:
    for info in vendor:
      vendor_info[info.vendor_name] = [info.vendor_building, info.vendor_image, info.vendor_name.title()]
  return render_template('vendors.html', vendor_info=vendor_info)

# Page that allows vendor to view their info and edit. 
@app.route('/vendor/vendor-info')
def vendor_info():
  if 'vendor_user' not in session:
    flash('Vendor not logged in', 'error')
    return redirect(url_for('vendor_login'))
  else:
    name = session['vendor_user']
    vendor = db.session.execute(db.select(Vendor).filter_by(vendor_name=name)).scalar_one()
    vendor_address = vendor.vendor_address
    vendor_building = vendor.vendor_building
    vendor_image = vendor.vendor_image
    return render_template('vendor_info.html', address=vendor_address, building=vendor_building, image=vendor_image, name=name)
  
# Edit vendor info. 
@app.route('/vendor/api/edit-vendor-info', methods=['GET','POST'])
def edit_vendor_info():
  if request.method=='GET':
    return redirect(url_for('vendor_info'))
  else:
    vendor_image = request.files['vendor_image']
    # if theres a image file given, change vendor_image to that
    if vendor_image and image_check(vendor_image.filename):
        vendor_image_name = secure_filename(vendor_image.filename)
        vendor_image.save(os.path.join(app.config['UPLOAD_FOLDER'], vendor_image_name))
        building = request.form['building']
        address = request.form['address']
        name = request.form['vendor_name'].lower()
        vendor_to_edit = db.session.execute(db.select(Vendor).filter_by(vendor_name=name)).scalar_one()
        vendor_to_edit.vendor_building = building
        vendor_to_edit.vendor_address = address
        vendor_to_edit.vendor_image = vendor_image_name
        db.session.commit()
        flash('Information edited!', 'success')
        return redirect(url_for('vendor_info'))
    # If image not given
    else:
      building = request.form['building']
      address = request.form['address']
      name = request.form['vendor_name']
      vendor_to_edit = db.session.execute(db.select(Vendor).filter_by(vendor_name=name)).scalar_one()
      vendor_to_edit.vendor_building = building
      vendor_to_edit.vendor_address = address
      db.session.commit()
      flash('Information edited!', 'success')
      return redirect(url_for('vendor_info'))
    
# When User clicks on a vendor, create session of order, vendor, 
# and order_num to create orders.
@app.route('/api/vendor-order', methods=['GET', 'POST'])
def vendor_order():
  if request.method == 'POST':
    session['vendor'] = request.form['vendor'].lower()
    session['order'] = {}
    session['order_num'] = 1
    return redirect(url_for('vendor_menu'))
  else:
    return redirect(url_for('vendor_menu'))

# Show menu of specifc vendor from session vendor
@app.route('/vendor-menu')
def vendor_menu():
    if 'vendor' in session:
      vendor = session['vendor']
      vendor_menu = {}
      vendor_food = db.session.execute(db.select(Food).filter_by(vendor=vendor)).all()
      for food in vendor_food:
          for info in food:
              vendor_menu[info.food_name] = [info.price, info.description, info.image, info.id, info.vendor]

      return render_template('vendor_menu.html', vendor_menu=vendor_menu, vendor=vendor.title())
    else:
      return redirect(url_for('vendors'))

# Add order to the session order dict to keep track of user orders.
@app.route('/api/add-order', methods=['GET', 'POST'])
def add_order():
  if request.method == 'POST':
    price = request.form['item-price']
    food_item_name = request.form['food-item-name']
    food_item = int(request.form['food-item'])
    qty = int(request.form['qty'])
    special_requests = request.form['special-request']
    order = session['order']
    order_num = session['order_num']
    order[str(order_num)] = [food_item, food_item_name, qty, special_requests, float(price)*qty, float(price)]
    order_num += 1
    session['order_num'] = order_num
    session['order'] = order
    flash(f'Order added!', 'success')
    return redirect(url_for('vendor_menu'))
  else:
    return redirect(url_for('vendor_menu'))
  
# Edit order
@app.route('/api/edit-order', methods=['GET', 'POST'])
def edit_order():
  if request.method == 'POST':
    orders = session['order']
    price = request.form['price']
    order_id = request.form['order_id']
    qty = request.form['qty']
    special_request = request.form['special-requests']
    orders[order_id][2] = qty
    orders[order_id][3] = special_request
    orders[order_id][4] = float(price)*int(qty)
    session['order'] = orders
    return redirect(url_for('my_cart'))
  else:
    return redirect(url_for('vendor_menu'))
  
# View user's cart before sending order. Allows them to edit. 
@app.route('/my-cart')
def my_cart():
  if 'order' in session and 'vendor' in session:
    orders = session['order']
    vendor = session['vendor']
    amount = 0
    for order in orders:
      amount += orders[order][-2]
    return render_template('orders.html', orders=orders, vendor=vendor.title(), amount=amount)
  else:
    return redirect(url_for('vendors'))
  
# Records all key details and writes the order to DB
@app.route('/api/confirm-order', methods=['POST', 'GET'])
def confirm_order():
  if request.method == 'GET':
    return redirect(url_for('my_orders')) 
  else:
    orders = session['order']
    vendor = session['vendor']
    customer_id = session['email']
    customer_name = session['user']
    total_cost = request.form['total_amount']
    
    time = datetime.now()
    
    new_orders = Food_Orders(vendor=vendor, customer_id=customer_id, customer_name=customer_name, status='Ordered', total_cost=total_cost, time_of_order=time) 
    db.session.add(new_orders)
    db.session.commit()
    order_id = new_orders.id   
    
    for order in orders:
      item_id = int(orders[order][0])
      order_id = order_id
      food_item = orders[order][1]
      qty = orders[order][2]
      special_requests = orders[order][3]
      price = orders[order][4]
      
      new_order = Food_Order(order_id=order_id, menu_item_id=item_id, food_item=food_item, qty=qty, special_requests=special_requests, price=price)
      db.session.add(new_order)
      db.session.commit()
    session.pop('order')
    session.pop('vendor')
    flash(f'Order added! Order id: {order_id}', 'success')
    return redirect(url_for('my_orders')) 
  
# Page to view users current orders
@app.route('/my-orders')
def my_orders():
  if 'email' in session and 'user' in session:
    orders_info = {}
    user_id = session['email']
    user = session['user']
  
    list_orders = Food_Orders.query.filter_by(customer_id=user_id).filter(Food_Orders.status != FULFILLED) \
      .order_by(Food_Orders.time_of_order.desc()).all()
    
    for orders in list_orders:
      time_of_order = orders.time_of_order.strftime('%Y-%m-%d %H:%M:%S')
      time_completion = 'N/A'
      orders_info[orders.id] = [orders.vendor, orders.status, orders.total_cost, time_of_order, time_completion]
    return render_template('my_orders.html', orders_info=orders_info, user=user.title())
  else:
    flash('You are not signed in', 'error')
    return redirect(url_for('login'))

# View user's past orders 
@app.route('/my-orders-history')
def my_orders_history():
  if 'email' in session and 'user' in session:
    orders_info = {}
    user_id = session['email']
    user = session['user']
    list_orders = Food_Orders.query.filter_by(customer_id=user_id).filter(Food_Orders.status == 'Order Fulfilled') \
      .order_by(Food_Orders.time_of_order.desc()).all()
    
    for orders in list_orders:
      time_completed = orders.time_of_completion.strftime('%Y-%m-%d %H:%M:%S')
      time_of_order = orders.time_of_order.strftime('%Y-%m-%d %H:%M:%S')
      orders_info[orders.id] = [orders.vendor, orders.status, orders.total_cost, time_of_order, time_completed]
    return render_template('my_orders.html', orders_info=orders_info, user=user.title())
  else:
    flash('You are not signed in', 'error')
    return redirect(url_for('login'))

# Tracks what order user wants to see specfically
@app.route('/api/my-orders-detailed', methods=['POST', 'GET'])
def my_orders_detailed():
  if request.method == 'POST':
    session['view_order_id'] = request.form['order_id']
    return redirect(url_for('customer_detailed_order'))
  else:
    return redirect(url_for('customer_detailed_order'))
  
# Page to view the specific details of a order
@app.route('/detailed-order')
def customer_detailed_order():
  if 'email' in session and 'view_order_id' in session:
    user_email = session['email']
    order_id = session['view_order_id']
    vendor_orders_detail = db.session.query(Food_Orders, Food_Order).\
      join(Food_Order, Food_Order.order_id == Food_Orders.id).\
      filter(Food_Orders.customer_id == user_email, Food_Orders.id == order_id).all()
      
    detailed_food_orders = {}

    for food_orders, food_order in vendor_orders_detail:
        
        order_item_id = food_order.order_item_id
        customer_name = food_orders.customer_name
        qty = food_order.qty
        menu_item_id = food_order.menu_item_id
        food_item = food_order.food_item
        item_cost = food_order.price
        total_cost = food_orders.total_cost
        special_requests = food_order.special_requests
        status = food_orders.status
        
        detailed_food_orders[order_item_id] = [menu_item_id, food_item, special_requests, qty, item_cost, customer_name]
    
    return render_template('order_detailed.html', detailed_food_orders=detailed_food_orders, total_cost=total_cost, status=status, order_id=order_id)
  else:
    return redirect(url_for('my_orders'))

# Shows all current orders that vendor has
@app.route('/vendor/order-dashboard')
def order_dashboard():
  if 'vendor_user' in session:
    orders_info = {}
    vendor = session['vendor_user']
    vendor_orders = Food_Orders.query.filter_by(vendor=vendor).filter(Food_Orders.status != FULFILLED)\
      .order_by(Food_Orders.time_of_order.desc()).all()
      
    for orders in vendor_orders:
      time_of_order = orders.time_of_order.strftime('%Y-%m-%d %H:%M:%S')
      orders_info[orders.id] = [orders.customer_id, orders.customer_name, orders.status, orders.total_cost, time_of_order]
          
    return render_template('vendor_orders.html', orders_info=orders_info, vendor=vendor.title())
  else:
    flash('You are not signed in', 'error')
    return redirect(url_for('vendor_login'))

# Shows all past orders that a vendor has
@app.route('/vendor/order-history')
def order_history():
  if 'vendor_user' in session:
    orders_info = {}
    vendor = session['vendor_user']
    vendor_orders = Food_Orders.query.filter_by(vendor=vendor).filter(Food_Orders.status == 'Order Fulfilled')\
      .order_by(Food_Orders.time_of_order.desc()).all()
      
    for orders in vendor_orders:
      
      time_completed = orders.time_of_completion.strftime('%Y-%m-%d %H:%M:%S')
      time_ordered = orders.time_of_order.strftime('%Y-%m-%d %H:%M:%S')
      orders_info[orders.id] = [orders.customer_id, orders.customer_name, orders.status, orders.total_cost, time_completed, time_ordered]
          
    return render_template('vendor_orders.html', orders_info=orders_info, vendor=vendor.title())
  else:
    flash('You are not signed in', 'error')
    return redirect(url_for('vendor_login'))

# Track order id of what vendor wants to see specifcally 
@app.route('/api/vendor/view-detailed-order', methods=['POST', 'GET'])
def view_detailed_order():
  if request.method == 'POST':
    session['view_order_id'] = request.form['order_id']
    return redirect(url_for('detailed_order'))
  else:
    return redirect(url_for('order_dashboard'))


# View details of a specifc order for vendor
@app.route('/vendor/detailed-order')
def detailed_order():
  if 'vendor_user' in session and 'view_order_id' in session:
    vendor = session['vendor_user']
    order_id = session['view_order_id']
    vendor_orders_detail = db.session.query(Food_Orders, Food_Order).\
      join(Food_Order, Food_Order.order_id == Food_Orders.id).\
      filter(Food_Orders.vendor == vendor, Food_Orders.id == order_id).all()
      
    detailed_food_orders = {}

    for food_orders, food_order in vendor_orders_detail:
      
        if food_orders.status == ORDERED:
          food_orders.status = PROCESSING
          db.session.commit()
        
        order_item_id = food_order.order_item_id
        customer_name = food_orders.customer_name
        qty = food_order.qty
        menu_item_id = food_order.menu_item_id
        food_item = food_order.food_item
        item_cost = food_order.price
        total_cost = food_orders.total_cost
        special_requests = food_order.special_requests
        status = food_orders.status
        
        detailed_food_orders[order_item_id] = [menu_item_id, food_item, special_requests, qty, item_cost, customer_name]
    return render_template('vendor_order_details.html', detailed_food_orders=detailed_food_orders, total_cost=total_cost, status=status, order_id=order_id)
  else:
    return redirect(url_for('order_dashboard'))

# Updates order status by vendor. 
@app.route('/api/vendor/complete-order', methods=['POST', 'GET'])
def complete_order():
  if request.method == 'POST':
    order_id = request.form['order_id']
    order = Food_Orders.query.filter_by(id=order_id).first()
    if order.status == PROCESSING:
      order.status = COMPLETED
    elif order.status == COMPLETED:
      order.status = FULFILLED
      time = datetime.now()
      order.time_of_completion = time
    db.session.commit()
    return redirect(url_for('detailed_order'))
  else:
    return redirect(url_for('detailed_order'))
  

app.run(host='0.0.0.0', port=5000, debug=True)
