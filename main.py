from flask import Flask, render_template, request, redirect, url_for, flash, session # session ekledik
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
# Flash mesajları ve session yönetimi için gizli anahtar şart
app.secret_key = "kitcher_cok_gizli_anahtar_123" 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Veritabanı Modeli
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("Bu e-posta adresi zaten kullanımda!")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # KAYIT SONRASI OTURUMU AÇ:
        session['user_id'] = new_user.id
        session['username'] = new_user.username
        
        flash("Başarıyla kayıt oldun!")
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear() # Oturumu kapatır
    return redirect(url_for('index'))

# Giriş yap rotası (Şimdilik sadece sayfayı gösterir)
@app.route('/login')
def login():
    return render_template('register.html') # Şimdilik register'a yönlendirebilirsin veya login.html yapabiliriz

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)