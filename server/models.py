from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy import MetaData

from config import db, bcrypt

# Optional: Add naming convention for constraints
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)

class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String, nullable=False, unique=True)
    _password_hash = db.Column(db.String)
    image_url = db.Column(db.String)
    bio = db.Column(db.String)
    
    # Relationship: User has many recipes
    recipes = db.relationship('Recipe', back_populates='user')
    
    # Serialization rules
    serialize_rules = ('-recipes.user', '-_password_hash',)
    
    @hybrid_property
    def password_hash(self):
        raise AttributeError('Password hashes may not be viewed.')
    
    @password_hash.setter
    def password_hash(self, password):
        password_hash = bcrypt.generate_password_hash(password.encode('utf-8'))
        self._password_hash = password_hash.decode('utf-8')
    
    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password.encode('utf-8'))
    
    @validates('username')
    def validate_username(self, key, username):
        if not username:
            raise ValueError("Username must be present")
        # Check if username already exists (excluding current user for updates)
        existing_user = User.query.filter(User.username == username).first()
        if existing_user and existing_user.id != self.id:
            raise ValueError("Username must be unique")
        return username
    
    def __repr__(self):
        return f'<User {self.id}, {self.username}>'

class Recipe(db.Model, SerializerMixin):
    __tablename__ = 'recipes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String, nullable=False)
    minutes_to_complete = db.Column(db.Integer)
    
    # Foreign key: Recipe belongs to a user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationship: Recipe belongs to a user
    user = db.relationship('User', back_populates='recipes')
    
    # Serialization rules
    serialize_rules = ('-user.recipes',)
    
    @validates('title')
    def validate_title(self, key, title):
        if not title:
            raise ValueError("Title must be present")
        return title
    
    @validates('instructions')
    def validate_instructions(self, key, instructions):
        if not instructions:
            raise ValueError("Instructions must be present")
        if len(instructions) < 50:
            raise ValueError("Instructions must be at least 50 characters long")
        return instructions
    
    def __repr__(self):
        return f'<Recipe {self.id}, {self.title}>'