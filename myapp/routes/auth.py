from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from functools import wraps

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    # בדוק את פרטי המשתמש והסיסמה
    if username != 'admin' or password != 'password':
        return jsonify({"msg": "Bad username or password"}), 401
    # יצירת token
    access_token = create_access_token(identity=username, additional_claims={"role": "admin" if username == "admin" else "user"})
    return jsonify(access_token=access_token)

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from flask_jwt_extended import get_jwt
        claims = get_jwt()
        if claims.get("role") != 'admin':
            return jsonify({"msg": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

@auth_bp.route('/admin', methods=['GET'])
@jwt_required()
@admin_required
def admin_only():
    return jsonify({"msg": "Welcome admin!"}), 200

# פונקציה ליצירת JWT עם תפקיד דינמי

def create_jwt_for_user(username, role):
    additional_claims = {"role": role}
    access_token = create_access_token(identity=username, additional_claims=additional_claims)
    return access_token 