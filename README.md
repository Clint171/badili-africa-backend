# Badili Africa API Documentation

## Table of Contents
- [Badili Africa API Documentation](#badili-africa-api-documentation)
  - [Table of Contents](#table-of-contents)
  - [Introduction](#introduction)
  - [Base URL](#base-url)
  - [Authentication](#authentication)
  - [Endpoints](#endpoints)
    - [User Management](#user-management)
      - [User Registration](#user-registration)
        - [Request Body](#request-body)
        - [Success Response](#success-response)
      - [User Login](#user-login)
        - [Request Body](#request-body-1)
        - [Success Response](#success-response-1)
      - [List Users](#list-users)
        - [Success Response](#success-response-2)
      - [Retrieve User](#retrieve-user)
        - [Success Response](#success-response-3)
      - [Update User](#update-user)
        - [Request Body](#request-body-2)
        - [Success Response](#success-response-4)
      - [Delete User](#delete-user)
        - [Success Response](#success-response-5)
    - [Project Management](#project-management)
      - [List Projects](#list-projects)
        - [Success Response](#success-response-6)
      - [Create Project](#create-project)
        - [Request Body](#request-body-3)
        - [Success Response](#success-response-7)
      - [Retrieve Project](#retrieve-project)
        - [Success Response](#success-response-8)
      - [Update Project](#update-project)
        - [Request Body](#request-body-4)
        - [Success Response](#success-response-9)
      - [Delete Project](#delete-project)
        - [Success Response](#success-response-10)
    - [Expense Management](#expense-management)
      - [List Expenses](#list-expenses)
        - [Success Response](#success-response-11)
      - [Create Expense](#create-expense)
        - [Request Body](#request-body-5)
        - [Success Response](#success-response-12)
      - [Retrieve Expense](#retrieve-expense)
        - [Success Response](#success-response-13)
      - [Delete Expense](#delete-expense)
        - [Success Response](#success-response-14)
      - [Get Expenses by Project](#get-expenses-by-project)
        - [Success Response](#success-response-15)
  - [Models](#models)
    - [User](#user)
    - [Project](#project)
    - [Expense](#expense)
  - [Error Handling](#error-handling)
    - [Common Error Codes](#common-error-codes)
    - [Error Response Format](#error-response-format)

## Introduction

This document provides detailed information about the Badili Africa backend API. It covers authentication, available endpoints, request/response formats, and error handling.

## Base URL

All URLs referenced in the documentation have the following base:

```
http://localhost:8000/api/
```

You can store this as a variable in your environment.

## Authentication

The API uses Token-based authentication. Include the token in the Authorization header for all authenticated requests:

```
Authorization: Bearer <token>
```

To obtain a token, use the login endpoint.

## Endpoints

### User Management

#### User Registration

- **URL:** `/signup/`
- **Method:** `POST`
- **Auth required:** No

##### Request Body

| Field      | Type   | Required | Description            |
|------------|--------|----------|------------------------|
| username   | string | Yes      | User's username        |
| password   | string | Yes      | User's password        |
| password2  | string | Yes      | Password confirmation  |
| email      | string | Yes      | User's email address   |
| first_name | string | Yes      | User's first name      |
| last_name  | string | Yes      | User's last name       |
| alias      | string | No       | User's alias           |
| designation| string | No       | User's designation     |

##### Success Response

- **Code:** 201 CREATED
- **Content:**

```json
{
  "user": {
    "id": 1,
    "username": "example_user",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "alias": "johnd",
    "designation": "Developer"
  },
  "token": "your-auth-token"
}
```

#### User Login

- **URL:** `/login/`
- **Method:** `POST`
- **Auth required:** No

##### Request Body

| Field    | Type   | Required | Description     |
|----------|--------|----------|-----------------|
| username | string | Yes      | User's username |
| password | string | Yes      | User's password |

##### Success Response

- **Code:** 200 OK
- **Content:**

```json
{
  "token": "Bearer your-auth-token",
  "user_id": 1,
  "email": "user@example.com"
}
```

#### List Users

- **URL:** `/users/`
- **Method:** `GET`
- **Auth required:** Yes (Admin only)

##### Success Response

- **Code:** 200 OK
- **Content:**

```json
[
  {
    "id": 1,
    "username": "example_user",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "alias": "johnd",
    "designation": "Developer"
  },
  // ... more users
]
```

#### Retrieve User

- **URL:** `/users/<id>/`
- **Method:** `GET`
- **Auth required:** Yes (Admin only)

##### Success Response

- **Code:** 200 OK
- **Content:**

```json
{
  "id": 1,
  "username": "example_user",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "alias": "johnd",
  "designation": "Developer"
}
```

#### Update User

- **URL:** `/users/<id>/`
- **Method:** `PUT`
- **Auth required:** Yes (Admin only)

##### Request Body

Same as User Registration, but all fields are optional.

##### Success Response

- **Code:** 200 OK
- **Content:** Updated user object

#### Delete User

- **URL:** `/users/<id>/`
- **Method:** `DELETE`
- **Auth required:** Yes (Admin only)

##### Success Response

- **Code:** 204 NO CONTENT

### Project Management

#### List Projects

- **URL:** `/projects/`
- **Method:** `GET`
- **Auth required:** Yes

##### Success Response

- **Code:** 200 OK
- **Content:**

```json
[
  {
    "id": 1,
    "name": "Project A",
    "description": "Description of Project A",
    "activities": ["Visit girls' school" , "Mission to home", ...],
    "status" : "active"
    "created_at": "2024-09-18T14:30:00Z"
  },
  // ... more projects
]
```

#### Create Project

- **URL:** `/projects/`
- **Method:** `POST`
- **Auth required:** Yes

##### Request Body

| Field        | Type   | Required | Description                                                                   |
|--------------|--------|----------|-------------------------------------------------------------------------------|
| name | string | Yes      | Name of the project                                                           |
| description  | string | Yes      | Project description                                                           |
| activities   | array  | Yes      | Project activities                                                            |
| status       | string | Yes      | Project status enum : "inactive", "active"(default), "completed", "abandoned" |

##### Success Response

- **Code:** 201 CREATED
- **Content:** Created project object

#### Retrieve Project

- **URL:** `/projects/<id>/`
- **Method:** `GET`
- **Auth required:** Yes

##### Success Response

- **Code:** 200 OK
- **Content:** Project object

#### Update Project

- **URL:** `/projects/<id>/`
- **Method:** `PUT`
- **Auth required:** Yes

##### Request Body

Same as Create Project, but all fields are optional.

##### Success Response

- **Code:** 200 OK
- **Content:** Updated project object

#### Delete Project

- **URL:** `/projects/<id>/`
- **Method:** `DELETE`
- **Auth required:** Yes

##### Success Response

- **Code:** 204 NO CONTENT

### Expense Management

#### List Expenses

- **URL:** `/expenses/`
- **Method:** `GET`
- **Auth required:** Yes

##### Success Response

- **Code:** 200 OK
- **Content:**

```json
[
  {
    "id": 1,
    "project_id": 1,
    "project_name" : "project 1",
    "activity": "Client meeting",
    "amount": "50.00",
    "description": "Lunch with client",
    "receipt": "/media/receipts/receipt_file.jpg",
    "project_officer_id": 1,
    "project_officer" : "Clint",
    "created_at": "2024-09-18T14:30:00Z"
  },
  // ... more expenses
]
```

#### Create Expense

- **URL:** `/expenses/`
- **Method:** `POST`
- **Auth required:** Yes
- **Content-Type:** `multipart/form-data`

##### Request Body

| Field       | Type    | Required | Description                    |
|-------------|---------|----------|--------------------------------|
| project     | string  | Yes      | Name of the associated project |
| activity    | string  | Yes      | Description of the activity    |
| amount      | decimal | Yes      | Expense amount                 |
| description | string  | Yes      | Detailed description           |
| receipt     | file    | Yes      | Receipt file (image/pdf)       |

##### Success Response

- **Code:** 201 CREATED
- **Content:** Created expense object

#### Retrieve Expense

- **URL:** `/expenses/<id>/`
- **Method:** `GET`
- **Auth required:** Yes

##### Success Response

- **Code:** 200 OK
- **Content:** Expense object


#### Delete Expense

- **URL:** `/expenses/<id>/`
- **Method:** `DELETE`
- **Auth required:** Yes

##### Success Response

- **Code:** 204 NO CONTENT

#### Get Expenses by Project

- **URL:** `/projects/<project_id>/expenses/`
- **Method:** `GET`
- **Auth required:** Yes

##### Success Response

- **Code:** 200 OK
- **Content:** List of expense objects for the specified project

## Models

### User

- id: Integer
- username: String
- email: String
- first_name: String
- last_name: String
- alias: String
- designation: String

### Project

- id: Integer
- name: String
- description: Text
- activities: Array(string)
- status: String (enum: inactive, active , completed , abandoned)
- created_at: DateTime

### Expense

- id: Integer
- project_id: ForeignKey(Project)
- project_name
- activity: String
- amount: Decimal
- description: Text
- receipt: File
- project_officer: String
- project_officer_id: ForeignKey(User)
- created_at: DateTime

## Error Handling

The API uses standard HTTP response codes to indicate the success or failure of requests. In case of errors, the response will include a JSON object with more details about the error.

### Common Error Codes

- 400 Bad Request: The request was invalid or cannot be served.
- 401 Unauthorized: The request requires authentication.
- 403 Forbidden: The server understood the request but refuses to authorize it.
- 404 Not Found: The requested resource could not be found.
- 500 Internal Server Error: The server encountered an unexpected condition which prevented it from fulfilling the request.

### Error Response Format

```json
{
  "detail": "Error message describing the issue"
}
```

For validation errors, the response may include field-specific error messages:

```json
{
  "field_name": [
    "Error message for this field"
  ]
}
```

This concludes the API documentation for Badili Africa's backend. Happy coding!