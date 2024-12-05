from flask import Flask, request, redirect, url_for, render_template, flash, session, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'some_secret_key'

# Veritabanı bağlantısı fonksiyonu
def get_db_connection():
    conn = sqlite3.connect('veritabani.db')
    conn.row_factory = sqlite3.Row
    return conn

# Veritabanı tablosunu oluşturma fonksiyonu
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(''' 
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS favorites (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        UNIQUE(user_id, product_id)  -- Aynı ürünü iki kez favorilere eklemeyi engellemek için
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL
    )
    ''')

    conn.commit()
    conn.close()

# Kullanıcı kaydı route'u
@app.route('/kaydol', methods=['POST'])
def kaydol():
    if request.is_json:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            return jsonify({'message': 'Kayıt başarılı!'}), 201
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Bu kullanıcı adı zaten mevcut!'}), 409
        finally:
            conn.close()
    else:
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            hashed_password = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
            flash('Kayıt başarılı!', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Bu kullanıcı adı zaten mevcut!', 'error')
        finally:
            conn.close()

    return render_template('kaydol.html')


# Kullanıcı girişi route'u (admin kontrolü dahil)
@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()  # AJAX istekleri için
        username = data.get('username')
        password = data.get('password')

        # Admin kontrolü
        if username == 'admin' and password == 'admin1234':
            session['user_id'] = 0  # Admin için özel bir ID tanımlayabiliriz
            session['username'] = 'admin'
            return jsonify({"message": "Admin olarak giriş başarılı!"}), 200

        # Normal kullanıcı girişi
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']  # Oturum aç
            session['username'] = user['username']  # Kullanıcı adını oturumda sakla
            return jsonify({"message": "Giriş başarılı!"}), 200
        else:
            return jsonify({"error": "Kullanıcı adınız veya şifreniz yanlış!"}), 401

    return jsonify({"error": "Geçersiz istek"}), 400



# Ana sayfa
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Kullanıcının girdiği isim
        isim = request.form.get('isim')
        
        # Veritabanına bağlan ve isimle eşleşen sayfayı al
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT sayfa FROM sayfalar WHERE isim = ?', (isim,))
        sayfa = c.fetchone()
        conn.close()

        if sayfa:
            # Eğer sayfa bulunduysa, kullanıcıyı o sayfaya yönlendir
            return redirect(url_for('sayfa', sayfa=sayfa[0]))
        else:
            return render_template('sayfa_yok.html')

    return render_template('index.html')



@app.route('/sayfa_yok', methods=['GET'])  
def sayfa_yok():
    return render_template('sayfa_yok.html')

@app.route('/dklasik', methods=['GET'])  
def dklasik():
    return render_template('dunya-klasikleri.html')

@app.route('/tklasik', methods=['GET'])  
def tklasik():
    return render_template('turk-klasikleri.html')

@app.route('/bilimk', methods=['GET'])  
def bilimk():
    return render_template('bilim-kurgu.html')

@app.route('/polisiye', methods=['GET'])  
def polisiye():
    return render_template('polisiye.html')

@app.route('/romanlar', methods=['GET'])  
def roman():
    return render_template('romanlar.html')

@app.route('/siirler', methods=['GET'])  
def siir():
    return render_template('siirler.html')

@app.route('/hakkimizda', methods=['GET'])  
def hakkimizda():
    return render_template('hakkimizda.html')

@app.route('/favoriler', methods=['GET'])  
def favoriler():
    return render_template('favoriler.html')

# Kullanıcıları listeleme ve silme işlemleri
@app.route('/kullanicilar', methods=['GET'])
def kullanicilar():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return render_template('kullanicilar.html', users=users)

@app.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash('Kullanıcı başarıyla silindi.', 'success')
    return redirect(url_for('kullanicilar'))

# Favoriler Sayfası (Yalnızca admin erişebilir)
@app.route('/favorites', methods=['GET'])
def favorites():
    # Oturum kontrolü
    if 'username' not in session or session['username'] != 'admin':
        flash('Bu sayfaya sadece admin erişebilir.', 'error')
        return redirect(url_for('login'))

    # Favori ürünleri getirme (sadece admin erişebildiği için örnek olarak bırakabiliriz)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.id, p.name, p.description, p.price
        FROM favorites f
        JOIN products p ON f.product_id = p.id
        WHERE f.user_id = (SELECT id FROM users WHERE username = 'admin')
    ''')
    favorite_products = cursor.fetchall()
    conn.close()

    return render_template('favoriler.html', products=favorite_products)




# Favori Ürünü Ekleme
@app.route('/add_to_favorites/<int:product_id>', methods=['POST'])
def add_to_favorites(product_id):
    if 'user_id' not in session:
        flash('Lütfen önce giriş yapın.', 'error')
        return redirect(url_for('login'))  # Oturum açılmamışsa, login sayfasına yönlendir

    user_id = session['user_id']  # Kullanıcıya özel favori işlemi

    conn = get_db_connection()
    cursor = conn.cursor()

    # Kullanıcının favorilerine eklenmiş mi kontrol et
    cursor.execute('SELECT * FROM favorites WHERE user_id = ? AND product_id = ?', (user_id, product_id))
    already_favorite = cursor.fetchone()

    if already_favorite:
        flash('Bu ürün zaten favorilerinizde.', 'info')
    else:
        # Ürünü favorilere ekle
        cursor.execute('INSERT INTO favorites (user_id, product_id) VALUES (?, ?)', (user_id, product_id))
        conn.commit()
        flash('Ürün favorilere eklendi.', 'success')

    conn.close()
    return redirect(url_for('product_detail', product_id=product_id))



# Çıkış Route'u
@app.route('/logout')
def logout():
    if 'user_id' in session:
        # Kullanıcının favorilerini silme işlemi yapmıyoruz çünkü favoriler, veritabanında tutuluyor.
        session.clear()  # Oturumu temizle
        flash('Çıkış yapıldı.', 'success')

    return redirect(url_for('login'))


# Ürün detayları sayfası
@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
    product = cursor.fetchone()
    conn.close()

    if not product:
        flash('Ürün bulunamadı.', 'error')
        return redirect(url_for('index'))

    return render_template('product_detail.html', product=product)


# Sabit sayfalar için dinamik route'lar
@app.route('/<sayfa>', methods=['GET'])
def sayfa(sayfa):
    try:
        return render_template(f'{sayfa}.html')
    except Exception:
        flash('Sayfa bulunamadı.', 'error')
        return redirect(url_for('index'))



# İletişim formu route'u
@app.route('/iletisim', methods=['POST'])
def iletisim():
    isim = request.form.get('isim')
    oneri = request.form.get('oneri')
    mesaj = request.form.get('mesaj')

    with open('iletisim_mesajlari.txt', 'a') as f:
        f.write(f"İsim: {isim}, Öneri: {oneri}, Mesaj: {mesaj}\n")

    flash('Mesajınız iletildi.', 'success')
    return redirect(url_for('index'))





if __name__ == '__main__':
    create_tables()
    app.run(debug=True)


