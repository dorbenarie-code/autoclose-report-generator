import pytest
from myapp.app import app

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_login(client):
    """בדיקת התחברות עם JWT"""
    response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json

def test_rate_limiting(client):
    """בדיקת Rate Limiting ל־/upload/upload"""
    # ננסה לשלוח בקשה יותר מהמגבלה
    for _ in range(12):  # מנסה יותר מ-10 פעמים
        response = client.post('/upload/upload')
    # הציפייה היא לקבל שגיאת 429 (Too Many Requests)
    assert response.status_code == 429

def test_protected(client):
    """בדיקת גישה מוגבלת"""
    # ראשית, עלינו להשיג טוקן
    login_response = client.post('/api/login', json={
        'username': 'admin',
        'password': 'password'
    })
    token = login_response.json['access_token']
    # נשלח בקשה ל־protected עם Authorization Header
    response = client.get('/api/protected', headers={
        'Authorization': f'Bearer {token}'
    })
    assert response.status_code == 200
    assert b"logged_in_as" in response.data 