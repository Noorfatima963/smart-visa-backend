# Smart Visa Backend API Documentation

Base URL: `http://localhost:8000` (or your configured domain)

## Windows Setup Guide

### Prerequisites
- [Python 3.8+](https://www.python.org/downloads/windows/) (Ensure "Add Python to PATH" is checked during installation)
- [Git](https://git-scm.com/download/win)

### Installation Steps

1.  **Clone the Repository**
    ```powershell
    git clone <repository_url>
    cd smart-visa-backend
    ```

2.  **Create Virtual Environment**
    ```powershell
    python -m venv venv
    ```

3.  **Activate Virtual Environment**
    ```powershell
    .\venv\Scripts\activate
    ```
    *(You should see `(venv)` at the start of your command prompt)*

4.  **Install Dependencies**
    ```powershell
    pip install -r requirements.txt
    ```

5.  **Apply Database Migrations**
    ```powershell
    python manage.py migrate
    ```

6.  **Initialize Document Data** (Important for first setup)
    ```powershell
    python manage.py init_documents
    ```

7.  **Create Superuser** (Optional, for Admin Panel access)
    ```powershell
    python manage.py createsuperuser
    ```

8.  **Run the Server**
    ```powershell
    python manage.py runserver
    ```
    Access the Admin Panel at: `http://127.0.0.1:8000/admin/`

---

## Authentication (`/api/users/`)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/users/register/` | Register a new user account. |
| `POST` | `/api/users/verify-email/` | Verify user email address (requires `uid` and `token`). |
| `POST` | `/api/users/login/` | Log in with email and password to obtain JWT tokens. |
| `POST` | `/api/users/token/refresh/` | Refresh the JWT access token. |

## Student Profile (`/api/profile/`)

These endpoints require authentication.

### Main Profile
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/profile/` | Retrieve the authenticated user's full profile (including nested data). |
| `PUT` | `/api/profile/` | Update the authenticated user's profile details (bio-data, address, etc.). |

### Education History
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/profile/education/` | List all education records. |
| `POST` | `/api/profile/education/` | Add a new education record. |
| `GET` | `/api/profile/education/<id>/` | Retrieve a specific education record. |
| `PUT` | `/api/profile/education/<id>/` | Update a specific education record. |
| `DELETE` | `/api/profile/education/<id>/` | Delete a specific education record. |

### Language Tests (IELTS, TOEFL, etc.)
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/profile/language-tests/` | List all language test scores. |
| `POST` | `/api/profile/language-tests/` | Add a new language test score. |
| `GET` | `/api/profile/language-tests/<id>/` | Retrieve a specific test score. |
| `PUT` | `/api/profile/language-tests/<id>/` | Update a specific test score. |
| `DELETE` | `/api/profile/language-tests/<id>/` | Delete a specific test score. |

### Travel History
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/profile/travel-history/` | List all travel history records. |
| `POST` | `/api/profile/travel-history/` | Add a new travel history record. |
| `GET` | `/api/profile/travel-history/<id>/` | Retrieve a specific travel record. |
| `PUT` | `/api/profile/travel-history/<id>/` | Update a specific travel record. |
| `DELETE` | `/api/profile/travel-history/<id>/` | Delete a specific travel record. |

### Financial Profile
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/profile/financial/` | Retrieve the financial profile (Income, Savings, Sponsor). |
| `PUT` | `/api/profile/financial/` | Update the financial profile. |

## Document Management (`/api/documents/`)

These endpoints require authentication.

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/documents/definitions/` | List all required document definitions (Passport, CV, etc.). Supports filtering by `?country=USA` or `?phase=ADMISSION`. |
| `GET` | `/api/documents/` | List all documents uploaded by the authenticated user. |
| `POST` | `/api/documents/` | Upload a new document file. Requires `file` (multipart) and `definition_slug`. |
