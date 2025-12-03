# Messaging Module Integration and Project Update Summary

## 1. Project Version Summary

This document provides a summary of the recent updates to the project, with a focus on the new features and the necessary steps to integrate and run the latest version. The most significant changes include the addition of a new Admin Dashboard and a complete refactoring of the Appointments module.

### New Features

*   **Admin Dashboard**: A new, data-rich dashboard has been added for administrators, providing insights into system usage, student engagement, and more. The dashboard is composed of several reusable components, including chart cards and metric cards.
*   **Revamped Appointments**: The appointments module has been completely redesigned to improve its structure and scalability. The underlying data models and UI components have been updated to provide a more robust and maintainable feature.
*   **Real-time Messaging**: The messaging module now supports real-time updates via WebSockets, allowing for instant message delivery and a more dynamic user experience.

## 2. Requirements

To run this version of the project, you will need to ensure that your environment is set up correctly. The following are the key requirements for the backend and frontend.

### Backend Requirements

*   **Python**: Ensure you have Python 3.11 or a compatible version installed.
*   **Dependencies**: All the required Python packages are listed in the `requirements.txt` file. You can install them using the following command:
    ```sh
    pip install -r requirements.txt
    ```
*   **Database Setup**: The project now includes a setup script that will automatically create the database and the default users. To run the script, navigate to the `backend` directory and run the following command:
    ```sh
    python script.py
    ```
*   **Running the Server with Daphne**: To support WebSockets for real-time messaging, the development server must be run with Daphne, the ASGI server for Django. The project is already configured to use Daphne. You can start the server with the following command:
    ```sh
    python manage.py runserver
    ```

### Frontend Requirements

*   **PyQt6**: The frontend is built with PyQt6. Ensure you have it installed in your environment.

## 3. Messaging Module Integration

The `Messaging` module is designed to be a self-contained component that can be easily integrated into the main application. The following steps outline how to integrate and use the module.

### Launching the Messaging Module

The entry point for the messaging module is the `LauncherWindow` class in `frontend/views/Messaging/launcher.py`. This window is responsible for loading the appropriate UI based on the user's role (student or faculty).

To integrate the `LauncherWindow`, you will need to import it into your main router and add it to the page map, as shown in the following example:

```python
# In your main router file
from frontend.views.Messaging.launcher import LauncherWindow

# Add the LauncherWindow to your page map
self.page_map[15] = {
    "widget": LauncherWindow,
    "path": "views.Messaging.launcher",
    "access": ["student", "faculty"],
}
```

### Data Management

The `DataManager` class (`frontend/views/Messaging/data_manager.py`) is responsible for all communication with the backend API. It handles fetching and sending messages, as well as managing user data. The `LauncherWindow` initializes the `DataManager` and passes it to the appropriate UI (student or faculty).

### Real-time Updates with WebSockets

The `faculty_app.py` and the student-facing UI are designed to connect to a WebSocket endpoint to receive real-time updates. The WebSocket connection is established in the `_init_ws` method, which connects to the `/ws/broadcasts/` endpoint.

When a new message is received, the `_on_ws_message` method is called, which then triggers the `_handle_incoming_message` method to update the UI in real-time.

## 4. Backend Configuration for Messaging

The backend has been configured to support the real-time features of the messaging module. The following are the key configuration details.

### `settings.py`

In `backend/config/settings.py`, the `INSTALLED_APPS` have been updated to include `daphne` and `channels`:

```python
INSTALLED_APPS = [
    "daphne",
    # ... other apps
    "channels",
    "apps.Messaging",
]
```

The `ASGI_APPLICATION` setting has also been configured to point to the routing configuration:

```python
ASGI_APPLICATION = "config.asgi.application"
```

### `asgi.py`

The `backend/config/asgi.py` file is the entry point for the ASGI server. It sets up the `ProtocolTypeRouter` to handle both HTTP and WebSocket connections.

### URL Routing

The WebSocket URL is defined in `backend/apps/Messaging/routing.py` and included in the main `asgi.py` file. This ensures that WebSocket connections to `/ws/broadcasts/` are handled by the appropriate consumer.
