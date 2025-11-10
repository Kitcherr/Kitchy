from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Kullanıcı tablosu
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

# 🏡 Ana Rota: index.html dosyasını render eder.
@app.route('/')
def index():
    # templates/index.html dosyasını çalıştırır
    return render_template('index.html')


# 👤 Kayıt Rota'sı: register.html formunu gösterir ve POST ile kayıt yapar.
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Yeni kullanıcı kaydı...
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Kayıt sonrası ana sayfaya (index rotasına) yönlendir
        return redirect(url_for('index'))

    # Kayıt formunu açar (Sizin bu projede register.html'iniz olmalı)
    return render_template('register.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)