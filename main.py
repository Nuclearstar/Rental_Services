from flask import *
import MySQLdb, hashlib, os
from werkzeug.utils import secure_filename
from PIL import Image
import glob
import shutil
import urllib

app = Flask(__name__)
app.secret_key = 'random string'
UPLOAD_FOLDER = '/home/niveditha/Dbms/Shopping-Cart-master/static/uploads'
ALLOWED_EXTENSIONS = set(['jpeg', 'jpg', 'png', 'gif'])
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def getLoginDetails():
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    if 'email' not in session:
        loggedIn = False
        firstName = ''
        noOfItems = 0
    else:
        loggedIn = True
        cur.execute("SELECT usrID, IName FROM User WHERE emailID = \'" + session['email'] + "\';")
        userId, firstName = cur.fetchone()
        cur.execute("SELECT count(ItemID) FROM Cart WHERE usrId = " + str(userId) + ";")
    	noOfItems = cur.fetchone()[0]
    conn.close()
    return (loggedIn, firstName, noOfItems)

@app.route("/")
def root():
    loggedIn, firstName, noOfItems = getLoginDetails()
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    cur.execute('SELECT ItemID, IName, Price, description, image FROM Items;')
    itemData = cur.fetchall()
    cur.execute('SELECT catId, catName FROM Category;')
    categoryData = cur.fetchall()
    itemData = parse(itemData)
    return render_template('home.html', itemData=itemData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems, categoryData=categoryData)

@app.route("/add")
def admin():
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    cur.execute("SELECT catId, catName FROM Category;")
    categories = cur.fetchall()
    conn.close()
    return render_template('add.html', categories=categories)

@app.route("/addItem", methods=["GET", "POST"])
def addItem():
    if request.method == "POST":
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        categoryId = int(request.form['category'])

        #Uploading image procedure
        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        imagename = filename
        conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
        try:
            cur = conn.cursor()
            cur.execute("INSERT INTO Items (IName,Price, description, image, catId) VALUES ( \'"+name+"\',"+ price+",\'"+ description+"\',\'" +imagename+"\'," +categoryId+");")
            conn.commit()
            msg="added successfully"
        except:
            msg="error occured"
            conn.rollback()
        conn.close()
        print(msg)
        return redirect(url_for('root'))

@app.route("/remove")
def remove():
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    cur.execute('SELECT ItemID, IName, Price, description, image FROM Items;')
    data = cur.fetchall()
    conn.close()
    return render_template('remove.html', data=data)

@app.route("/removeItem")
def removeItem():
    productId = request.args.get('productId')
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    try:
        cur = conn.cursor()
        cur.execute('DELETE FROM Items WHERE ItemID = ' + productId + ";")
        conn.commit()
        msg = "Deleted successsfully"
    except:
        conn.rollback()
        msg = "Error occured"
    conn.close()
    print(msg)
    return redirect(url_for('root'))

@app.route("/displayCategory")
def displayCategory():
        loggedIn, firstName, noOfItems = getLoginDetails()
        categoryId = request.args.get("categoryId")
        conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
        cur = conn.cursor()
        cur.execute("SELECT catId,catName FROM Category WHERE catId = "+str(categoryId)+";")
        categoryName = cur.fetchall()
        #categoryName = parse(categoryName)
        cur.execute("SELECT ItemID,IName,Price,image FROM Items WHERE catId ="+str(categoryId)+";")
        data = cur.fetchall()
        conn.close()

        data = parse(data)
       # categoryName = parse(categoryName)
        return render_template('displayCategory.html', Itemdata=data, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems,categoryName=categoryName)

@app.route("/account/profile")
def profileHome():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    return render_template("profileHome.html", loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/edit")
def editProfile():
    if 'email' not in session:
        return redirect(url_for('root'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    cur.execute("SELECT usrID, emailID, IName, Address, PhoneNo FROM User WHERE emailID = \'" + session['email'] + "\';")
    profileData = cur.fetchone()
    conn.close()
    return render_template("editProfile.html", profileData=profileData, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/account/profile/changePassword", methods=["GET", "POST"])
def changePassword():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    if request.method == "POST":
        oldPassword = request.form['oldpassword']
        oldPassword = hashlib.md5(oldPassword.encode()).hexdigest()
        newPassword = request.form['newpassword']
        newPassword = hashlib.md5(newPassword.encode()).hexdigest()
        conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
        cur = conn.cursor()
        cur.execute("SELECT usrname, password FROM Login WHERE usrname = \'" + session['email'] + "\';")
        emailid, password = cur.fetchone()
        if (password == oldPassword):
            try:
                cur.execute("UPDATE Login SET password = \'"+newPassword+"\' WHERE usrname = \'"+ emailid+"\';")
                conn.commit()
                msg="Changed successfully"
            except:
                conn.rollback()
                msg = "Failed"
            return render_template("changePassword.html", msg=msg)
        else:
            msg = "Wrong password"
        conn.close()
        return render_template("changePassword.html", msg=msg)
    else:
        return render_template("changePassword.html")

@app.route("/updateProfile", methods=["GET", "POST"])
def updateProfile():
    if request.method == 'POST':
        email = request.form['email']
        firstName = request.form['firstName']
        address = request.form['address1']
        phone = request.form['phone']
        con =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
        try:
            cur = con.cursor()
            cur.execute('UPDATE User SET IName = \''+firstName+"\', Address = \'"+address+"\', PhoneNo = \'"+phone+"\' WHERE emailID = \'"+ email+"\';")

            con.commit()
            msg = "Saved Successfully"
        except:
            con.rollback()
            msg = "Error occured"
        con.close()
        return redirect(url_for('editProfile'))

@app.route("/loginForm")
def loginForm():
    if 'email' in session:
        return redirect(url_for('root'))
    else:
        return render_template('login.html', error='')

@app.route("/login", methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if is_valid(email, password):
            session['email'] = email
            return redirect(url_for('root'))
        else:
            error = 'Invalid UserId / Password'
            return render_template('login.html', error=error)

@app.route("/productDescription")
def productDescription():
    loggedIn, firstName, noOfItems = getLoginDetails()
    productId = request.args.get('productId')
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    cur.execute("SELECT ItemID, IName, Price, description, image FROM Items WHERE ItemID ="+str(productId)+";")
    productData = cur.fetchone()
    conn.close()
    productData = parse(productData)
    return render_template("productDescription.html", Itemdata = productData, loggedIn = loggedIn, firstName = firstName, noOfItems = noOfItems)

@app.route("/addToCart")
def addToCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    else:
        productId = (request.args.get('productId'))
        conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
        cur = conn.cursor()
        cur.execute("SELECT usrID FROM User WHERE emailID = \'" + str(session['email']) + "\';")
        userId = cur.fetchone()[0]
        try:
            cur.execute("INSERT INTO Cart(usrId,ItemID) VALUES("+str(userId)+"," +str(productId)+");")
            conn.commit()
            msg = "Added successfully"
        except:
            conn.rollback()
            msg = "Error occured"
        conn.close()
        return redirect(url_for('root'))

@app.route("/cart")
def cart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    loggedIn, firstName, noOfItems = getLoginDetails()
    email = session['email']
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    cur.execute("SELECT usrID FROM User WHERE emailID = \'" + email + "\';")
    userId = cur.fetchone()[0]
    cur.execute("SELECT Items.ItemID,IName,Price,image FROM Items, Cart WHERE Cart.usrId =" + str(userId) + " and Items.ItemID = Cart.ItemID ;")
    products = cur.fetchall()
    totalPrice = 0
    for row in products:
        totalPrice += row[2]
    return render_template("cart.html", products = products, totalPrice=totalPrice, loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)

@app.route("/removeFromCart")
def removeFromCart():
    if 'email' not in session:
        return redirect(url_for('loginForm'))
    email = session['email']
    productId = int(request.args.get('productId'))
    conn =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = conn.cursor()
    cur.execute("SELECT usrID FROM User WHERE emailID = \'" + email + "\';" )
    userId = cur.fetchone()[0]
    try:
        cur.execute("DELETE FROM Cart WHERE usrId = " + str(userId) + " AND ItemID = " + str(productId) + ";")
        conn.commit()
        msg = "removed successfully"
    except:
        conn.rollback()
        msg = "error occured"
    conn.close()
    return redirect(url_for('root'))

@app.route("/logout")
def logout():
    session.pop('email', None)
    return redirect(url_for('root'))

def is_valid(email, password):
    con = MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
    cur = con.cursor()
    cur.execute('SELECT usrname, password FROM Login;')
    data = cur.fetchall()
    for row in data:
        if row[0] == email and row[1] == hashlib.md5(password.encode()).hexdigest():
            return True
    return False


@app.route("/sell",  methods = ['GET', 'POST'])
def selling():
	#if 'email' not in session:
	#	return redirect(url_for('root'))
	#loggedIn, firstName, noOfItems = getLoginDetails()
	#return render_template("sell.html",loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
	if request.method == 'POST':
		name = str(request.form['itemname'])
		cate = str(request.form['catname'])
		descr = str(request.form['descr'])
		image = (request.form['imag'])
		price = float(request.form['price'])
#		dest = "/static/uploads"
#		image = request.url()
#		urllib.urlretrieve(image,dest)
#		if image and allowed_file(image.filename):
#			filename = secure_filename(image.filename)
#			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#			imagename = filename
		#image1 = request.form['image1']
		conn = MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
		try:
			cur = conn.cursor()
			cur.execute("SELECT usrID from User where emailID = \'"+session['email']+"\';")
			usrid = cur.fetchall()
			cure.execute("SELECT catId FROM Category WHERE catName = \'"+cate+"\';")
			catid = cur.fetchall()
			cur.execute("INSERT INTO Items (usrID,IName,catId,Price,description,image) VALUES ("+usrid+",\'"+name+"\',"+catid+","+price+",\'"+descr+"\',\'"+image+"\');")
			msg = "Advertisement Generated."
		except:
			conn.rollback()
			msg = "Error."
		conn.close()
		
		#return redirect(url_for("root"))
		return render_template("home.html",error = msg)
@app.route("/account/sell")
def sell():
	if 'email' not in session:
		return redirect(url_for('root'))
	loggedIn, firstName, noOfItems = getLoginDetails()
	return render_template("sell.html",loggedIn=loggedIn, firstName=firstName, noOfItems=noOfItems)
		
@app.route("/register", methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        #Parse form data
        password = request.form['password']
        password = str(password)
        email = request.form['email']
        email = str(email)
        firstName = request.form['firstName']
        address = request.form['address1']
        phone = request.form['phone']
        firstName = str(firstName)
        address = str(address)
        phone = str(phone)
        con =  MySQLdb.Connect(host="localhost",user="root",passwd="niveditha",db="MerchantileDB")
        try:
            cur = con.cursor()
            cur.execute("INSERT INTO User (emailID, IName, Address, PhoneNo) VALUES ( \'"+ email + "\',\'" +firstName+"\',\'"+ address+"\',\'"+ phone+"\');")
            cur.execute("INSERT INTO Login (usrname,password) VALUES (\'" +email+"\',\'"+hashlib.md5(password.encode()).hexdigest()+"\');")
            con.commit()

            msg = "Registered Successfully"
        except Exception,e:
            con.rollback()
            msg = str(e)
        con.close()
        return render_template("login.html", error=msg)
@app.route("/checkout")
def checkout():
	return render_template("checkout.html")

@app.route("/registerationForm")
def registrationForm():
    return render_template("register.html")

def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def parse(data):
    ans = []
    i = 0
    while i < len(data):
        current = []
        for j in range(5):
            if i >= len(data):
                break
            current.append(data[i])
            i += 1
        ans.append(current)
    return ans

if __name__ == '__main__':
    app.run(debug=True)
