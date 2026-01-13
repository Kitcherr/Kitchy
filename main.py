from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
# Flash mesajları ve session yönetimi için gizli anahtar
app.secret_key = "kitcher_cok_gizli_anahtar_123" 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Veritabanı Modelleri - Sadece Kayıt İçin Gerekli Olanlar
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

#Malzeme analiz -----------------------------------------------------------------------------------------------------------------
@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    results = []

    recipes = [
        {
            "name": "pankek",
            "ingredients": ["un", "süt", "yumurta", "şeker", "kabartma tozu"],
        },
        {
            "name": "omlet",
            "ingredients": ["yumurta", "süt", "tuz", "karabiber", "peynir"],
        },
        {   
            "name": "spagetti",
            "ingredients": ["spagetti makarna", "domates sosu", "zeytinyağı", "sarımsak", "fesleğen"],
        }
    ]


    if request.method == "POST":
        user_input = request.form.get("ingredients")
        user_ingredients = [i.strip().lower() for i in user_input.split(",")]

        for recipe in recipes:
            # en az 1 ortak malzeme var mı?
            for ing in user_ingredients:
                if ing in recipe["ingredients"]:
                    results.append(recipe)
                    break  # bu tarif tamam, diğer malzemelere bakma

    return render_template('analysis.html', results=results)

# -------------------------------------------------------------------------------------------------------------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Kullanıcı kontrolü
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("Bu e-posta adresi zaten kullanımda!")
            return redirect(url_for('register'))

        # Yeni kullanıcı oluşturma
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Kayıt sonrası oturum açma
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        
        flash("Başarıyla kayıt oldun!")
        return redirect(url_for('index'))

    return render_template('register.html')
@app.route('/suggestion-day')
def suggestion_day():
    return render_template('suggestion-day.html')

@app.route('/feedback')
def feedback():
    return render_template('feedback.html')

@app.route('/logout')
def logout():
    session.clear() 
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)