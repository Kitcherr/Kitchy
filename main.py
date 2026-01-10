from flask import Flask, render_template, request, redirect, url_for, flash, session # session ekledik
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


app = Flask(__name__)
# Flash mesajları ve session yönetimi için gizli anahtar şart
app.secret_key = "kitcher_cok_gizli_anahtar_123" 

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Veritabanı Modelleri
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    # İlişkiler
    posts = db.relationship('Post', backref='author', lazy=True, cascade='all, delete-orphan')
    upvotes = db.relationship('Upvote', backref='user', lazy=True, cascade='all, delete-orphan')
    # Bu kullanıcıyı takip edenler (followers)
    followers_rel = db.relationship('Follow', foreign_keys='Follow.following_id', backref='user_being_followed', lazy=True, cascade='all, delete-orphan')
    # Bu kullanıcının takip ettikleri (following)
    following_rel = db.relationship('Follow', foreign_keys='Follow.follower_id', backref='user_following', lazy=True, cascade='all, delete-orphan')
    
    def get_followers_count(self):
        """Bu kullanıcıyı kaç kişi takip ediyor?"""
        return len(self.followers_rel)
    
    def get_following_count(self):
        """Bu kullanıcı kaç kişiyi takip ediyor?"""
        return len(self.following_rel)
    
    def get_posts_count(self):
        """Bu kullanıcının kaç gönderisi var?"""
        return len(self.posts)
    
    def is_followed_by(self, user_id):
        """Belirli bir kullanıcı bu kullanıcıyı takip ediyor mu?"""
        if not user_id:
            return False
        return Follow.query.filter_by(follower_id=user_id, following_id=self.id).first() is not None

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # İlişkiler
    upvotes = db.relationship('Upvote', backref='post', lazy=True, cascade='all, delete-orphan')
    
    def get_upvote_count(self):
        return len(self.upvotes)
    
    def is_upvoted_by(self, user_id):
        if not user_id:
            return False
        return Upvote.query.filter_by(post_id=self.id, user_id=user_id).first() is not None

class Upvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Benzersiz kısıtlama: bir kullanıcı bir gönderiyi sadece bir kez upvote edebilir
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='unique_upvote'),)

class Follow(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    following_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    # Benzersiz kısıtlama: bir kullanıcı başka bir kullanıcıyı sadece bir kez takip edebilir
    # ve kendini takip edemez
    __table_args__ = (db.UniqueConstraint('follower_id', 'following_id', name='unique_follow'),)

@app.route('/')
def index():
    return render_template('index.html')

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

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Kullanıcı giriş yapmış mı kontrol et
    if 'user_id' not in session:
        flash("Profil sayfasına erişmek için giriş yapmalısınız!")
        return redirect(url_for('index'))
    
    user = User.query.get(session['user_id'])
    
    if not user:
        flash("Kullanıcı bulunamadı!")
        session.clear()
        return redirect(url_for('index'))
    
    # Profil güncelleme işlemi
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        new_password = request.form.get('password')
        
        # Email değişikliği kontrolü (başka kullanıcıda var mı?)
        if email != user.email:
            email_exists = User.query.filter_by(email=email).first()
            if email_exists:
                flash("Bu e-posta adresi başka bir kullanıcı tarafından kullanılıyor!")
                return redirect(url_for('profile'))
            user.email = email
        
        user.username = username
        session['username'] = username  # Session'ı güncelle
        
        # Şifre değiştirildiyse güncelle
        if new_password:
            user.password = new_password
        
        db.session.commit()
        flash("Profil bilgileriniz başarıyla güncellendi!")
        return redirect(url_for('profile'))
    
    # Kullanıcının gönderilerini getir
    user_posts = Post.query.filter_by(user_id=user.id).order_by(Post.created_at.desc()).all()
    
    # İstatistikler
    stats = {
        'posts_count': user.get_posts_count(),
        'followers_count': user.get_followers_count(),
        'following_count': user.get_following_count()
    }
    
    return render_template('profile.html', user=user, stats=stats, user_posts=user_posts)

@app.route('/community')
def community():
    # Tüm gönderileri tarihe göre sıralayarak getir
    posts = Post.query.order_by(Post.created_at.desc()).all()
    
    # Kullanıcı giriş yapmış mı kontrol et
    current_user_id = session.get('user_id')
    current_user = None
    if current_user_id:
        current_user = User.query.get(current_user_id)
    
    # Her gönderi için upvote durumu ve sayısını kontrol et
    posts_data = []
    for post in posts:
        post_dict = {
            'post': post,
            'upvote_count': post.get_upvote_count(),
            'is_upvoted': post.is_upvoted_by(current_user_id),
            'author': post.author,
            'is_following': False
        }
        
        # Takip durumu kontrolü
        if current_user_id and current_user_id != post.author.id:
            follow_exists = Follow.query.filter_by(
                follower_id=current_user_id,
                following_id=post.author.id
            ).first()
            post_dict['is_following'] = follow_exists is not None
        
        posts_data.append(post_dict)
    
    return render_template('community.html', posts_data=posts_data, current_user=current_user)

@app.route('/community/create_post', methods=['POST'])
def create_post():
    if 'user_id' not in session:
        flash("Gönderi oluşturmak için giriş yapmalısınız!")
        return redirect(url_for('community'))
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    
    if not title or not content:
        flash("Başlık ve içerik gereklidir!")
        return redirect(url_for('community'))
    
    new_post = Post(title=title, content=content, user_id=session['user_id'])
    db.session.add(new_post)
    db.session.commit()
    
    flash("Gönderiniz başarıyla oluşturuldu!")
    return redirect(url_for('community'))

@app.route('/community/upvote/<int:post_id>', methods=['POST'])
def upvote_post(post_id):
    """Gönderiye upvote yap veya kaldır"""
    if 'user_id' not in session:
        flash("Upvote yapmak için giriş yapmalısınız!")
        return redirect(url_for('community'))
    
    post = Post.query.get_or_404(post_id)
    user_id = session['user_id']
    
    # Zaten upvote edilmiş mi kontrol et
    existing_upvote = Upvote.query.filter_by(user_id=user_id, post_id=post_id).first()
    
    if existing_upvote:
        # Upvote'u kaldır
        db.session.delete(existing_upvote)
        db.session.commit()
        flash("Upvote kaldırıldı!")
    else:
        # Yeni upvote ekle
        new_upvote = Upvote(user_id=user_id, post_id=post_id)
        db.session.add(new_upvote)
        db.session.commit()
        flash("Gönderi upvote edildi!")
    
    # Nereden geldiğini kontrol et ve oraya yönlendir
    referrer = request.referrer or url_for('community')
    if '/user/' in referrer:
        # Profil sayfasından geldiyse, o kullanıcının profil sayfasına dön
        try:
            import re
            match = re.search(r'/user/(\d+)', referrer)
            if match:
                return redirect(url_for('user_profile', user_id=int(match.group(1))))
        except:
            pass
    
    return redirect(url_for('community'))

@app.route('/community/follow/<int:user_id>', methods=['POST'])
def follow_user(user_id):
    """Kullanıcıyı takip et veya takipten çık - community sayfasından"""
    if 'user_id' not in session:
        flash("Kullanıcıyı takip etmek için giriş yapmalısınız!")
        return redirect(url_for('community'))
    
    return _handle_follow(user_id, session['user_id'], redirect_to='community')

@app.route('/user/<int:user_id>/follow', methods=['POST'])
def follow_user_from_profile(user_id):
    """Kullanıcıyı takip et veya takipten çık - profil sayfasından"""
    if 'user_id' not in session:
        flash("Kullanıcıyı takip etmek için giriş yapmalısınız!")
        return redirect(url_for('user_profile', user_id=user_id))
    
    return _handle_follow(user_id, session['user_id'], redirect_to='user_profile', redirect_param=user_id)

def _handle_follow(user_id, current_user_id, redirect_to='community', redirect_param=None):
    """Takip işlemini yöneten yardımcı fonksiyon"""
    # Kendini takip edemez
    if current_user_id == user_id:
        flash("Kendinizi takip edemezsiniz!")
        if redirect_to == 'user_profile':
            return redirect(url_for('user_profile', user_id=user_id))
        return redirect(url_for('community'))
    
    # Kullanıcı var mı kontrol et
    user_to_follow = User.query.get_or_404(user_id)
    
    # Zaten takip ediliyor mu kontrol et
    existing_follow = Follow.query.filter_by(
        follower_id=current_user_id,
        following_id=user_id
    ).first()
    
    if existing_follow:
        # Takibi kaldır
        db.session.delete(existing_follow)
        db.session.commit()
        flash(f"{user_to_follow.username} takipten çıkarıldı!")
    else:
        # Yeni takip ekle
        new_follow = Follow(follower_id=current_user_id, following_id=user_id)
        db.session.add(new_follow)
        db.session.commit()
        flash(f"{user_to_follow.username} takip ediliyor!")
    
    if redirect_to == 'user_profile':
        return redirect(url_for('user_profile', user_id=user_id))
    return redirect(url_for('community'))

@app.route('/user/<int:user_id>')
def user_profile(user_id):
    """Başka bir kullanıcının profilini görüntüle"""
    # Görüntülenen kullanıcıyı bul
    profile_user = User.query.get_or_404(user_id)
    
    # Mevcut kullanıcı (giriş yapmışsa)
    current_user_id = session.get('user_id')
    current_user = None
    is_own_profile = False
    is_following = False
    
    if current_user_id:
        current_user = User.query.get(current_user_id)
        is_own_profile = (current_user_id == user_id)
        if not is_own_profile:
            is_following = profile_user.is_followed_by(current_user_id)
    
    # Bu kullanıcının gönderilerini getir (en yeni önce)
    user_posts = Post.query.filter_by(user_id=user_id).order_by(Post.created_at.desc()).all()
    
    # Her gönderi için upvote bilgisi ekle
    posts_data = []
    for post in user_posts:
        post_dict = {
            'post': post,
            'upvote_count': post.get_upvote_count(),
            'is_upvoted': post.is_upvoted_by(current_user_id) if current_user_id else False
        }
        posts_data.append(post_dict)
    
    # İstatistikler
    stats = {
        'posts_count': profile_user.get_posts_count(),
        'followers_count': profile_user.get_followers_count(),
        'following_count': profile_user.get_following_count()
    }
    
    return render_template('user_profile.html', 
                         profile_user=profile_user,
                         current_user=current_user,
                         is_own_profile=is_own_profile,
                         is_following=is_following,
                         posts_data=posts_data,
                         stats=stats)

@app.route('/user/<int:user_id>/followers')
def user_followers(user_id):
    """Kullanıcının takipçilerini listele"""
    profile_user = User.query.get_or_404(user_id)
    
    # Takipçileri getir
    followers = []
    for follow in profile_user.followers_rel:
        follower = User.query.get(follow.follower_id)
        if follower:
            followers.append(follower)
    
    # Mevcut kullanıcı
    current_user_id = session.get('user_id')
    current_user = None
    if current_user_id:
        current_user = User.query.get(current_user_id)
    
    return render_template('followers_list.html',
                         profile_user=profile_user,
                         users=followers,
                         list_type='Takipçiler',
                         current_user=current_user)

@app.route('/user/<int:user_id>/following')
def user_following(user_id):
    """Kullanıcının takip ettiklerini listele"""
    profile_user = User.query.get_or_404(user_id)
    
    # Takip edilenleri getir
    following = []
    for follow in profile_user.following_rel:
        followed_user = User.query.get(follow.following_id)
        if followed_user:
            following.append(followed_user)
    
    # Mevcut kullanıcı
    current_user_id = session.get('user_id')
    current_user = None
    if current_user_id:
        current_user = User.query.get(current_user_id)
    
    return render_template('followers_list.html',
                         profile_user=profile_user,
                         users=following,
                         list_type='Takip Edilenler',
                         current_user=current_user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)