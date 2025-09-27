from flask import Flask, request, session, jsonify
from flask_restful import Api, Resource
from flask_migrate import Migrate
from config import db, app
from models import User, Recipe

migrate = Migrate(app, db)
api = Api(app)

class Signup(Resource):
    def post(self):
        data = request.get_json()
        
        try:
            # Create new user
            user = User(
                username=data.get('username'),
                image_url=data.get('image_url'),
                bio=data.get('bio')
            )
            
            # Set password using the property setter
            user.password_hash = data.get('password')
            
            # Add and commit to database
            db.session.add(user)
            db.session.commit()
            
            # Save user ID in session
            session['user_id'] = user.id
            
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 201
            
        except ValueError as e:
            return {'error': str(e)}, 422
        except Exception as e:
            return {'error': 'Failed to create user'}, 422

class CheckSession(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Not authorized'}, 401
        
        user = User.query.filter(User.id == user_id).first()
        
        if not user:
            return {'error': 'User not found'}, 401
        
        return {
            'id': user.id,
            'username': user.username,
            'image_url': user.image_url,
            'bio': user.bio
        }, 200

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter(User.username == username).first()
        
        if user and user.authenticate(password):
            session['user_id'] = user.id
            return {
                'id': user.id,
                'username': user.username,
                'image_url': user.image_url,
                'bio': user.bio
            }, 200
        else:
            return {'error': 'Invalid username or password'}, 401

class Logout(Resource):
    def delete(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Not authorized'}, 401
        
        session.pop('user_id', None)
        return '', 204

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Not authorized'}, 401
        
        recipes = Recipe.query.all()
        
        return jsonify([{
            'id': recipe.id,
            'title': recipe.title,
            'instructions': recipe.instructions,
            'minutes_to_complete': recipe.minutes_to_complete,
            'user': {
                'id': recipe.user.id,
                'username': recipe.user.username,
                'image_url': recipe.user.image_url,
                'bio': recipe.user.bio
            }
        } for recipe in recipes])
    
    def post(self):
        user_id = session.get('user_id')
        
        if not user_id:
            return {'error': 'Not authorized'}, 401
        
        data = request.get_json()
        
        try:
            recipe = Recipe(
                title=data.get('title'),
                instructions=data.get('instructions'),
                minutes_to_complete=data.get('minutes_to_complete'),
                user_id=user_id
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            return {
                'id': recipe.id,
                'title': recipe.title,
                'instructions': recipe.instructions,
                'minutes_to_complete': recipe.minutes_to_complete,
                'user': {
                    'id': recipe.user.id,
                    'username': recipe.user.username,
                    'image_url': recipe.user.image_url,
                    'bio': recipe.user.bio
                }
            }, 201
            
        except ValueError as e:
            return {'error': str(e)}, 422
        except Exception as e:
            return {'error': 'Failed to create recipe'}, 422

# Add resources to API
api.add_resource(Signup, '/signup')
api.add_resource(CheckSession, '/check_session')
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(RecipeIndex, '/recipes')

if __name__ == '__main__':
    app.run(port=5555, debug=True)