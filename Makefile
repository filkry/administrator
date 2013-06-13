test:
	python -m unittest administrator.test.tests

run_server:
	exec gunicorn administrator:app -b localhost:8000

debug_server:
	exec gunicorn administrator:app --debug -b localhost:8000
