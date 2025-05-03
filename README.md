# FastAPI Rate Limiting Decorators

This repository provides two implementations of rate-limiting decorators for FastAPI endpoints:
- An **in-memory** implementation using Python dictionaries (`main.py`).
- A **Redis-based** implementation using Redis sorted sets (`redis_ver.py`).

These decorators allow you to limit the number of requests a client can make to your FastAPI endpoints within a specified time period.

---

## Features
1. **In-Memory Rate Limiting**:
   - Simple and lightweight.
   - Best suited for single-process applications or local development.

2. **Redis-Based Rate Limiting**:
   - Distributed and scalable.
   - Ideal for production environments with multiple instances of your application.

3. **Customizable Parameters**:
   - Set the maximum number of allowed calls (`max_calls`) and the time window (`period`) in seconds.

4. **Client Identification**:
   - Clients are identified by their IP address, hashed for security.

---

## File Descriptions

### `main.py`
Implements in-memory rate limiting using a Python dictionary for tracking request timestamps. This is a simple and efficient approach for single-process applications.

#### Example Usage:
```python
from fastapi import FastAPI, Request
from main import rate_limit

app = FastAPI()

@rate_limit(max_calls=5, period=60)
async def my_endpoint(request: Request):
    return {"message": "Hello, World!"}
```

---

### `redis_ver.py`
Implements rate limiting using Redis sorted sets to store and manage request timestamps. This approach supports distributed applications where multiple instances share the same rate-limiting data.

#### Required Environment Variables:
- `REDIS_HOST`: Redis server hostname.
- `REDIS_PORT`: Redis server port.
- `REDIS_USERNAME`: Redis username (if applicable).
- `REDIS_PASSWORD`: Redis password.

#### Example Usage:
```python
from fastapi import FastAPI, Request
from redis_ver import rate_limit

app = FastAPI()

@rate_limit(max_calls=10, period=60)
async def my_endpoint(request: Request):
    return {"message": "Hello, World!"}
```

---

## Dependencies

Install the required dependencies using `pip`:
```bash
pip install -r requirements.txt
```

### `requirements.txt`:
- **fastapi[standard]>=0.115.6**: FastAPI framework for building APIs.
- **redis==5.2.1**: Redis client for Python.
- **aioredis==2.0.1**: Async Redis client for Python.

---

## How It Works

### In-Memory Rate Limiting (`main.py`)
1. Tracks the timestamps of requests in a dictionary where the keys are unique client identifiers (hashed IP addresses).
2. Removes timestamps older than the specified period.
3. If the number of requests in the period exceeds `max_calls`, returns a `429 Too Many Requests` error with a retry time.

---

### Redis-Based Rate Limiting (`redis_ver.py`)
1. Uses Redis sorted sets to store request timestamps, with the score being the timestamp in milliseconds.
2. Periodically removes old timestamps outside the defined period.
3. Counts the number of requests in the current window.
4. If the number of requests exceeds `max_calls`, returns a `429 Too Many Requests` error with a retry time.

---

## Use Cases
- Prevent abuse of APIs by limiting the number of requests from clients.
- Implement rate limiting at the application level for APIs.
- Protect your services from being overwhelmed with requests.

---

## Running the Application

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/fastapi-rate-limiting.git
   cd fastapi-rate-limiting
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run your FastAPI application:
   ```bash
   uvicorn main:app --reload  # For in-memory rate limiting
   uvicorn redis_ver:app --reload  # For Redis-based rate limiting
   ```

4. Test the endpoints:
   Using tools like `curl` or Postman, send requests to your endpoint and observe rate-limiting behavior.

---

## Notes
- **In-memory Implementation**:
  - Do not use in a production environment with multiple instances; rate limiting will not be consistent across instances.

- **Redis Implementation**:
  - Ensure the Redis server is properly configured and accessible.
  - Works seamlessly in distributed environments.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

## Contributing
Contributions are welcome! Feel free to open issues or submit pull requests to enhance the project.

---

## Author
Developed by [al-chris](https://github.com/al-chris).