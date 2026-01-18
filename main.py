from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

app = Flask(__name__)
# Flash mesajları ve session yönetimi için gizli anahtar
app.secret_key = "kitcher_cok_gizli_anahtar_123" 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_BINDS'] = {
    'recipes': 'sqlite:///recipes.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Veritabanı Modelleri
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class Recipe(db.Model):
    __bind_key__ = 'recipes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False) # Stored as JSON string

    def get_ingredients(self):
        return json.loads(self.ingredients)

def seed_recipes():
    initial_recipes = [
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
        },
        {
            "name": "menemen",
            "ingredients": ["yumurta", "domates", "biber", "tuz", "sıvı yağ"],
        },
        {
            "name": "köfte",
            "ingredients": ["kıyma", "soğan", "ekmek içi", "yumurta", "kimyon", "karabiber", "tuz"],
        },
        {
            "name": "pilav",
            "ingredients": ["pirinç", "tereyağı", "tuz", "su", "şehriye"],
        },
        {
            "name": "tost",
            "ingredients": ["tost ekmeği", "kaşar peyniri", "sucuk", "tereyağı"],
        },
        {
            "name": "çoban salatası",
            "ingredients": ["domates", "salatalık", "biber", "soğan", "zeytinyağı", "limon", "tuz"],
        },
        {
            "name": "mercimek çorbası",
            "ingredients": ["kırmızı mercimek", "soğan", "havuç", "patates", "sıvı yağ", "tuz", "nane"],
        },
        {
            "name": "tavuk sote",
            "ingredients": ["tavuk göğsü", "biber", "domates", "soğan", "sarımsak", "kekik", "pul biber", "sıvı yağ"],
        }
    ]
    
    for r in initial_recipes:
        if not Recipe.query.filter_by(name=r["name"]).first():
            new_recipe = Recipe(name=r["name"], ingredients=json.dumps(r["ingredients"]))
            db.session.add(new_recipe)
            print(f"Added recipe: {r['name']}")
    
    db.session.commit()
    print("Recipe seeding check completed!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').lower().strip()
    results = []
    
    if query:
        # Split by comma if user types "un, süt"
        user_ingredients = [i.strip() for i in query.split(",")]
        
        recipes = Recipe.query.all()
        for recipe in recipes:
            recipe_ingredients = recipe.get_ingredients()
            # Starts-with match check
            # Logic: If ANY user ingredient matches the START of ANY recipe ingredient
            match_found = False
            for user_ing in user_ingredients:
                if not user_ing: continue
                if any(r_ing.startswith(user_ing) for r_ing in recipe_ingredients):
                    match_found = True
                    break
            
            if match_found:
                results.append({
                    "name": recipe.name,
                    "ingredients": recipe_ingredients
                })
                
    return jsonify(results)

#Malzeme analiz -----------------------------------------------------------------------------------------------------------------
@app.route('/analysis', methods=['GET', 'POST'])
def analysis():
    # Keep the old route just in case, but it might not be used if JS takes over completely.
    # Or simply render the template blank.
    return render_template('analysis.html')

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
        seed_recipes()
    app.run(debug=True)