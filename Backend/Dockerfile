FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install Microsoft ODBC Driver 18 for SQL Server.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl gnupg2 apt-transport-https ca-certificates unixodbc-dev \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list \
    && ACCEPT_EULA=Y apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 libgssapi-krb5-2 \
    && apt-get purge -y --auto-remove curl gnupg2 apt-transport-https \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
