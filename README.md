# News Application

A Django-based news platform where independent journalists publish articles, editors approve them, and readers subscribe to publications or individual journalists. Approved articles are automatically emailed to subscribers and posted to X (formerly Twitter).

Built as the **Capstone Project** for the HyperionDev Software Engineering Bootcamp.

![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django)
![DRF](https://img.shields.io/badge/DRF-3.x-A30000)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)

---

##  Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Running the App](#-running-the-app)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Project Structure](#-project-structure)
- [Screenshots](#-screenshots)
- [Author](#-author)
- [License](#-license)

---

##  Features

### Roles & Permissions
- **Reader** — can view articles and newsletters, subscribe to publishers/journalists
- **Journalist** — can create, view, update, and delete articles and newsletters
- **Editor** — can view, update, delete, and **approve** articles and newsletters

### Core Functionality
- Custom user model with role-based fields
- Automatic group assignment by role (Reader / Editor / Journalist)
- Publisher model supporting multiple editors and journalists
- Newsletter model with many-to-many relation to articles
- Article approval workflow with editor-only access

### Integrations
- **Email notification** — approved articles emailed to subscribers
- **X (Twitter) integration** — approved articles auto-posted to a designated account
- **RESTful API** — full CRUD for articles with token-based authentication

### API
- JWT authentication via `djangorestframework-simplejwt`
- Role-protected endpoints (readers view, journalists create, editors approve)
- Pagination on list endpoints
- Browsable API for exploration

### Quality
- 60+ automated unit tests covering models, API, and signals
- PEP 8 compliant, modular, defensive code
- MariaDB-ready (SQLite for local development)

---

##  Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.x |
| API | Django REST Framework |
| Auth | SimpleJWT (Bearer tokens) |
| Database | MariaDB / MySQL (SQLite in dev) |
| Email | Django `send_mail` (console backend in dev) |
| HTTP Client | `requests` (for X API) |
| Config | `python-decouple` + `.env` |
| Python | 3.12 |

---

##  Architecture
