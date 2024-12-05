import sqlite3

def veritabani_olustur():
    # Veritabanı bağlantısı
    conn = sqlite3.connect('veritabani.db')

    # İmleç oluşturma
    c = conn.cursor()

    # Tabloyu oluşturma (eğer yoksa)
    c.execute('''
    CREATE TABLE IF NOT EXISTS sayfalar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        isim TEXT NOT NULL,
        sayfa TEXT NOT NULL
    )
    ''')

    # Değişiklikleri kaydetme
    conn.commit()

    # Veritabanı bağlantısını kapatma
    conn.close()
    

# Users tablosunu oluşturmak için fonksiyonu çalıştırın
create_users_table()
    
def veritabani_olustur():
    # Veritabanı bağlantısı
    conn = sqlite3.connect('ecommerce.db')

    # İmleç oluşturma
    c = conn.cursor()

    # Tabloyu oluşturma (eğer yoksa)
    c.execute('''
    
    CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_name TEXT NOT NULL,
    product_price REAL NOT NULL
    )
    ''')


    # Tabloyu oluşturma (eğer yoksa)
    c.execute('''
    CREATE TABLE favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
    )
    ''')
    # Değişiklikleri kaydetme
    conn.commit()

    # Veritabanı bağlantısını kapatma
    conn.close()

if __name__ == '__main__':
    veritabani_olustur()
    print("Veritabanı ve tablo başarıyla oluşturuldu.")