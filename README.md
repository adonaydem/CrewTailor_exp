# CrewTailor

CrewTailor is a full-stack demo application with a React frontend and a Flask backend.

## License  
This project is licensed under the Apache License 2.0 - see the [LICENSE](./LICENSE) file for details.

## Project Structure

- `frontend/` - Contains the React application.
- `backend/` - Contains the Flask API.

## Getting Started

### Prerequisites

Ensure you have the following installed:

- [Node.js](https://nodejs.org/) (for React frontend)
- [Python](https://www.python.org/) (for Flask backend)
- [pip](https://pip.pypa.io/en/stable/) (Python package installer)
- [venv](https://docs.python.org/3/library/venv.html) (Python virtual environment manager)
- [MongoDB](https://www.mongodb.com/) (NoSQL database) Follow setup instruction below.

#### API Keys

To use this application, you'll need the following API keys, all of them have at least [limited free usage]:

- *OPENAI_API_KEY*: Used for accessing OPENAI API. 

- *TAVILY_API_KEY*: Required for accessing web, for realtime data. Obtain it from [Tavily](https://tavily.com/).

- *ALPHA_VANTAGE_API_KEY*: Needed for global financial data from Alpha Vantage. Sign up [here](https://www.alphavantage.co/).

### Frontend Setup

1. Navigate to the `frontend` directory:

   ```bash
   cd frontend
   ```

2. Create a `.env` file in the `frontend` directory with the following content:

   ```plaintext
   REACT_APP_FIREBASE_API_KEY=your_firebase_api_key
   REACT_APP_FIREBASE_AUTH_DOMAIN=your_firebase_auth_domain
   REACT_APP_FIREBASE_PROJECT_ID=your_firebase_project_id
   REACT_APP_FIREBASE_STORAGE_BUCKET=your_firebase_storage_bucket
   REACT_APP_FIREBASE_MESSAGING_SENDER_ID=your_firebase_messaging_sender_id
   REACT_APP_FIREBASE_APP_ID=your_firebase_app_id
   REACT_APP_FIREBASE_MEASUREMENT_ID=your_firebase_measurement_id
   REACT_APP_BACKEND_URL=http://127.0.0.1:5000   # Replace with your backend URL
   ```

   Replace the placeholder values with your actual Firebase configuration details.

3. Install the required npm packages:

   ```bash
   npm install
   ```

4. Start the React development server:

   ```bash
   npm start
   ```

   Your React application will be available at `http://localhost:3000`.

### Backend Setup

1. Navigate to the `backend` directory:

   ```bash
   cd backend
   ```

2. Create a `.env` file in the `backend` directory with the following content:

   ```plaintext
   FLASK_APP=app.py
   FLASK_ENV=development
   OPENAI_API_KEY=your_openai_api_key
   TAVILY_API_KEY=your_tavily_api_key
   ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key
   ```

   Replace the placeholder values with your actual API keys and configuration details.

3. Create and activate a Python virtual environment:

   ```bash
   python -m venv venv
   ```

   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS/Linux:

     ```bash
     source venv/bin/activate
     ```

4. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

5. Run the Flask development server:

   ```bash
   python app.py
   ```

   Your Flask API will be available at `http://127.0.0.1:5000`.

### MongoDB Setup Guide

1. **Create Data Directory:**
   ```bash
   mkdir C:\data\db
   ```

2. **Start MongoDB:**
   ```bash
   mongod
   ```

3. **Connect to MongoDB:**
   ```bash
   mongo
   ```

4. **Update Application Configuration:**
   Ensure the app connects to `localhost:27017`.

## Firebase Authentication

The frontend application uses Firebase for authentication. Ensure you have correctly configured your Firebase project and updated the `.env` file in the `frontend` directory with your Firebase credentials.

For more information on Firebase authentication, refer to the [Firebase Authentication documentation](https://firebase.google.com/docs/auth).


**Third-Party Licenses**

This project uses LangChain, which is licensed under the MIT License.
See the [LangChain License](https://github.com/langchain-ai/langchain/blob/master/LICENSE).

## Acknowledgements

- [Langchain](https://www.langchain.com/)
- [Firebase](https://firebase.google.com/)
- [React](https://reactjs.org/)
- [Flask](https://flask.palletsprojects.com/)

