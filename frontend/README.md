# React Chat Agent UI

This project is a simple and aesthetic chat interface built with React, designed to serve as a frontend for a conversational AI agent. It provides a clean, modern user interface similar to popular chatbots like Gemini and ChatGPT, with a light theme and a blue color palette.

This guide is intended for beginners in React and frontend development, providing a thorough walkthrough of the setup, code, and next steps for connecting this UI to a backend agent service like Google's Agent Development Kit (ADK).

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation and Running the App](#installation-and-running-the-app)
- [Code Explained](#code-explained)
  - [Project Structure](#project-structure)
  - [Components](#components)
    - [`App.js`](#appjs)
    - [`ChatWindow.js`](#chatwindowjs)
    - [`Message.js`](#messagejs)
    - [`ChatInput.js`](#chatinputjs)
  - [Styling](#styling)
- [Next Steps: Connecting to an Agent](#next-steps-connecting-to-an-agent)
  - [1. Understanding the Frontend-Backend Connection](#1-understanding-the-frontend-backend-connection)
  - [2. Modifying the Frontend to Call an API](#2-modifying-the-frontend-to-call-an-api)
  - [3. Setting Up Your Google ADK Backend](#3-setting-up-your-google-adk-backend)
  - [4. CORS (Cross-Origin Resource Sharing)](#4-cors-cross-origin-resource-sharing)

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/en/) (which includes npm, the Node.js package manager) installed on your system. You can download it from the official website.

### Installation and Running the App

1.  **Open a terminal** in the project directory.
2.  **Install the necessary dependencies** by running the following command:
    ```bash
    npm install
    ```
3.  **Start the development server**:
    ```bash
    npm start
    ```
    This will open the application in your default web browser at `http://localhost:3000`.

## Code Explained

This application is built with a few key components that work together to create the chat interface.

### Project Structure

```
src
├── components
│   ├── ChatInput.js
│   ├── ChatWindow.js
│   └── Message.js
├── App.js
├── index.js
└── styles.css
```

-   `src`: The main folder containing all the application's source code.
-   `src/components`: A folder to hold our reusable React components.
-   `App.js`: The main component of our application.
-   `index.js`: The entry point of our React application.
-   `styles.css`: The stylesheet for our application.

### Components

#### `App.js`

This is the main component that brings everything together.

-   It uses React's `useState` hook to manage the `messages` of the conversation.
-   The `handleSendMessage` function is responsible for:
    1.  Adding the user's message to the chat.
    2.  Simulating a bot response after a short delay. **This is where you will eventually connect to your backend agent.**

#### `ChatWindow.js`

This component is responsible for displaying the conversation.

-   It receives the `messages` array as a prop.
-   It maps over the `messages` and renders a `Message` component for each one.

#### `Message.js`

This component displays a single message in the chat.

-   It receives the `text` of the message and the `sender` (`'user'` or `'bot'`).
-   It applies different styling to the message based on who the sender is, aligning user messages to the right and bot messages to the left.

#### `ChatInput.js`

This component is the input field where the user can type and send a message.

-   It manages the state of the input field.
-.  When the "Send" button is clicked or the "Enter" key is pressed, it calls the `onSendMessage` function (passed down from `App.js`) with the message text.

### Styling

The styling is done in `src/styles.css`. It's a simple stylesheet that uses CSS Flexbox to create the chat layout. The colors and fonts are chosen to match the light and blue theme.

## Next Steps: Connecting to an Agent

Currently, the chatbot's responses are simulated in the frontend. To make it a real chatbot, you need to connect it to your backend agent, which you plan to build with Google ADK.

### 1. Understanding the Frontend-Backend Connection

The React frontend will communicate with your backend agent over the internet using HTTP requests. The typical flow is:

1.  The user types a message and clicks "Send" in the React app.
2.  The React app sends the user's message to an API endpoint on your backend server (your Google ADK agent).
3.  Your backend agent processes the message and generates a response.
4.  Your backend sends the response back to the React app.
5.  The React app displays the agent's response in the chat window.

### 2. Modifying the Frontend to Call an API

You'll need to modify the `handleSendMessage` function in `src/App.js` to send the user's message to your backend. You can use the `fetch` API, which is built into modern browsers.

Here's an example of how you might modify `handleSendMessage`:

```javascript
const handleSendMessage = async (text) => {
  const newMessage = { text, sender: 'user' };
  const newMessages = [...messages, newMessage];
  setMessages(newMessages);

  try {
    const response = await fetch('YOUR_AGENT_API_ENDPOINT', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ message: text }),
    });

    const data = await response.json();
    const botResponse = { text: data.reply, sender: 'bot' }; // Assuming your API returns a 'reply' field
    setMessages([...newMessages, botResponse]);

  } catch (error) {
    console.error("Error fetching from agent:", error);
    const errorResponse = { text: 'Sorry, I am having trouble connecting.', sender: 'bot' };
    setMessages([...newMessages, errorResponse]);
  }
};
```

### 3. Setting Up Your Google ADK Backend

You will need to create a backend service (e.g., using a Google Cloud Function or Cloud Run) that hosts your ADK agent. This service will expose an API endpoint (like `YOUR_AGENT_API_ENDPOINT` in the example above) that your React app can call.

Your backend code will be responsible for:

-   Receiving the HTTP request from the frontend.
-   Extracting the user's message from the request.
-   Using the ADK to process the message and generate a response.
-   Sending the response back in JSON format.

### 4. CORS (Cross-Origin Resource Sharing)

When you call an API on a different domain (or port) from your frontend, you'll likely encounter CORS errors. You'll need to configure your backend service to allow requests from your frontend's domain (e.g., `http://localhost:3000` during development). This is typically done by setting the `Access-Control-Allow-Origin` header in your backend's HTTP response.