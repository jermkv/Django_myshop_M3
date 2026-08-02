from django.contrib.auth import get_user_model


def test_web_registration_redirects_and_logs_in(client, db):
	User = get_user_model()
	email = 'webtest@example.com'
	password = 'StrongPass123'

	# Submit registration form via POST (email & password)
	response = client.post('/register/', {'email': email, 'password': password})

	# Expect redirect to account page
	assert response.status_code in (301, 302)

	# After redirect, client should be authenticated - account page accessible
	r = client.get('/account/')
	assert r.status_code == 200

	# User exists in DB
	assert User.objects.filter(username=email).exists()
