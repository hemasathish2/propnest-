import pytest
from app import app, init_db, valid_email, safe_link

@pytest.fixture
def client(tmp_path):
    app.config.update(TESTING=True, DATABASE=str(tmp_path / 'test.db'))
    init_db()
    return app.test_client()

PROFILE = dict(name='Asha Dev', headline='Python Developer', bio='I build apps.', email='asha@example.com', github='https://github.com/asha', theme='sunset')
PROJECT = dict(title='Task Tracker', description='A useful task app', tech='Python, Flask', link='https://example.com')
SKILL = dict(name='Python', category='Backend')
CONTACT = dict(sender='Visitor', email='visitor@example.com', message='Nice portfolio!')

def test_01_health(client): assert client.get('/api/health').json['status'] == 'ok'
def test_02_home(client): assert client.get('/').status_code == 200
def test_03_editor(client): assert client.get('/editor').status_code == 200
def test_04_portfolio(client): assert client.get('/portfolio').status_code == 200
def test_05_dashboard(client): assert client.get('/dashboard').status_code == 200
def test_06_initial_metrics(client): assert client.get('/api/metrics').json == dict(projects=0,skills=0,messages=0)
def test_07_default_profile(client): assert b'Demo Developer' in client.get('/portfolio').data
def test_08_update_profile(client):
    assert b'Profile saved' in client.post('/profile',data=PROFILE,follow_redirects=True).data
    assert b'Asha Dev' in client.get('/portfolio').data

def test_09_profile_requires_name(client):
    assert b'Invalid profile' in client.post('/profile',data={**PROFILE,'name':''},follow_redirects=True).data

def test_10_profile_rejects_bad_email(client):
    assert b'Invalid profile' in client.post('/profile',data={**PROFILE,'email':'bad'},follow_redirects=True).data

def test_11_profile_rejects_theme(client):
    assert b'Invalid profile' in client.post('/profile',data={**PROFILE,'theme':'unknown'},follow_redirects=True).data

def test_12_profile_rejects_unsafe_link(client):
    assert b'Invalid profile' in client.post('/profile',data={**PROFILE,'github':'javascript:alert(1)'},follow_redirects=True).data

def test_13_add_project(client):
    assert b'Project added' in client.post('/projects/add',data=PROJECT,follow_redirects=True).data
    assert client.get('/api/metrics').json['projects'] == 1

def test_14_project_in_portfolio(client):
    client.post('/projects/add',data=PROJECT)
    assert b'Task Tracker' in client.get('/portfolio').data

def test_15_reject_project_without_title(client):
    assert b'Invalid project' in client.post('/projects/add',data={**PROJECT,'title':''},follow_redirects=True).data

def test_16_reject_project_unsafe_url(client):
    assert b'Invalid project' in client.post('/projects/add',data={**PROJECT,'link':'javascript:bad'},follow_redirects=True).data

def test_17_delete_project(client):
    client.post('/projects/add',data=PROJECT)
    assert b'Project deleted' in client.post('/projects/1/delete',follow_redirects=True).data
    assert client.get('/api/metrics').json['projects'] == 0

def test_18_delete_missing_project(client):
    assert b'Project not found' in client.post('/projects/999/delete',follow_redirects=True).data

def test_19_add_skill(client):
    assert b'Skill added' in client.post('/skills/add',data=SKILL,follow_redirects=True).data
    assert b'Python' in client.get('/portfolio').data

def test_20_duplicate_skill(client):
    client.post('/skills/add',data=SKILL)
    assert b'Skill already exists' in client.post('/skills/add',data=SKILL,follow_redirects=True).data

def test_21_reject_invalid_skill_category(client):
    assert b'Invalid skill' in client.post('/skills/add',data={**SKILL,'category':'Hacking'},follow_redirects=True).data

def test_22_delete_skill(client):
    client.post('/skills/add',data=SKILL)
    assert b'Skill deleted' in client.post('/skills/1/delete',follow_redirects=True).data
    assert client.get('/api/metrics').json['skills'] == 0

def test_23_delete_missing_skill(client):
    assert b'Skill not found' in client.post('/skills/999/delete',follow_redirects=True).data

def test_24_valid_contact(client):
    assert b'Message received' in client.post('/contact',data=CONTACT,follow_redirects=True).data
    assert b'Nice portfolio!' in client.get('/dashboard').data
    assert client.get('/api/metrics').json['messages'] == 1

def test_25_invalid_contact(client):
    assert b'Invalid contact' in client.post('/contact',data={**CONTACT,'email':'bad'},follow_redirects=True).data
    assert client.get('/api/metrics').json['messages'] == 0
