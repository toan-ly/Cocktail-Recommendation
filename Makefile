DB_HOST=127.0.0.1
DB_PORT=5433
DB_USER=postgres
DB_NAME=cocktails_db

psql:
	psql -h $(DB_HOST) -p $(DB_PORT) -U $(DB_USER) -d $(DB_NAME)

run-setup:
	uv run src/database_setup.py

run-preprocess:
	uv run src/data_preprocessing.py

run-recommender:
	uv run src/recommender.py


docker-up:
	docker compose up -d

docker-down:
	docker compose down -v


demo:
	uv run -m streamlit run src/app.py