"# UserService-AWS" 
<img width="1565" height="761" alt="image" src="https://github.com/user-attachments/assets/55678f9d-71fc-4df9-8741-29913b4969f5" />
# 🧑‍💼 User Service (FastAPI + AWS Cognito)

A production-ready **User Service** built with **FastAPI** that handles user registration, authentication, and authorization using **AWS Cognito**.  
This service is designed for scalability, modularity, and cloud-native deployment on **AWS ECS** with **CI/CD pipelines**.

---

## 🚀 Features

- 🔐 **AWS Cognito Integration** for secure user management (sign up, sign in, token verification)
- 🧱 **FastAPI** backend with async endpoints
- 🧩 **Clean architecture** (routers, services, repositories)
- 🐳 **Dockerized** for consistent environment
- ☁️ **AWS ECS + ECR + RDS** ready
- 🧪 **Pytest** for testing endpoints
- 🧠 **LoggingService** with rotating file logs
- 🧰 **Environment variables** managed with `.env`

---

## 🧭 Architecture Overview

```
app/
 ┣ core/
 ┃ ┣ auth/
 ┃ ┃ ┗ cognito_service.py      # AWS Cognito integration logic
 ┃ ┣ config.py                 # App and AWS configuration
 ┃ ┣ error_handler.py          # Global error handlers
 ┃ ┗ logging_service.py        # Centralized logging
 ┣ api/
 ┃ ┣ routes/
 ┃ ┃ ┗ user_router.py          # Signup, login, refresh endpoints
 ┃ ┗ dependencies.py           # Dependency injection
 ┣ tests/                      # Unit and integration tests
 ┣ main.py                     # FastAPI entry point
 ┗ Dockerfile                  # Container build
```

---

## ⚙️ Environment Variables

Create a `.env` file in the project root with:

```bash
AWS_REGION=us-east-1
AWS_COGNITO_USER_POOL_ID=your_user_pool_id
AWS_COGNITO_CLIENT_ID=your_client_id
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

APP_NAME=UserService
APP_ENV=production
LOG_LEVEL=INFO
```

---

## 🐳 Running with Docker

```bash
docker build -t user-service .
docker run -p 8000:8000 --env-file .env user-service
```

Then visit [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🔄 CI/CD with GitHub Actions

- Lint and test on each commit
- Build and push Docker image to AWS ECR
- Deploy to ECS Fargate

Example pipeline (`.github/workflows/deploy.yml`):
```yaml
on: [push]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build Docker image
        run: docker build -t user-service .
      - name: Push to ECR
        run: |
          aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY
          docker tag user-service:latest $ECR_REPOSITORY:user-service
          docker push $ECR_REPOSITORY:user-service
```

---

## 🧠 Example Routes

| Method | Endpoint | Description |
|--------|-----------|-------------|
| `POST` | `/auth/signup` | Register a new user |
| `POST` | `/auth/login` | Authenticate and get tokens |
| `GET`  | `/auth/me` | Get current user info |
| `POST` | `/auth/refresh` | Refresh access token |

---

## 🧰 Testing

```bash
pytest -v
```

---

## 📦 Deployment Overview

1. Push code to GitHub → GitHub Actions builds image → pushes to ECR  
2. ECS Fargate automatically deploys latest image  
3. Application connects to AWS Cognito and RDS for user management  

---

## 📜 License

MIT License © 2025 Mahmoud Mady
