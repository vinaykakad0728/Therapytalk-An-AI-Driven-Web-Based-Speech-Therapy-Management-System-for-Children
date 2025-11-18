import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your_secret_key'
    
    # MySQL Configuration
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '@vinay0728'
    MYSQL_DB = 'therapytalk'

    # Flask-Mail Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USERNAME = 'vinaykakad56@gmail.com'
    MAIL_PASSWORD = 'hxre eoif qqgh jegk'
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False