import React, { createContext, useContext, useReducer, useEffect } from 'react';
import chatService from '../services/chatService';

const ChatContext = createContext();

const initialState = {
  messages: [],
  isLoading: false,
  error: null,
  threads: [], // For multiple threads
  currentThreadId: 'default' // Default thread
};

function chatReducer(state, action) {
  switch (action.type) {
    case 'ADD_MESSAGE':
      // Update messages for the current thread
      return {
        ...state,
        messages: [...state.messages, action.payload],
        threads: state.threads.map(thread => 
          thread.id === state.currentThreadId 
            ? { 
                ...thread, 
                lastMessageTime: action.payload.timestamp,
                // Extract first line of first message as title if it's the first message
                name: thread.messages.length === 0 && action.payload.sender === 'user' 
                  ? action.payload.text.split('\n')[0].substring(0, 30) 
                  : thread.name
              }
            : thread
        )
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload
      };
    
    case 'CREATE_THREAD':
      return {
        ...state,
        threads: [...state.threads, action.payload],
        currentThreadId: action.payload.id,
        messages: [] // Clear messages when creating a new thread
      };
    
    case 'SWITCH_THREAD':
      // Filter messages to only show those for the selected thread
      return {
        ...state,
        currentThreadId: action.payload,
        messages: state.threads.find(thread => thread.id === action.payload)?.messages || []
      };
    
    default:
      return state;
  }
}

export const ChatProvider = ({ children }) => {
  const [state, dispatch] = useReducer(chatReducer, initialState);

  useEffect(() => {
    // Create a default thread if none exist
    if (state.threads.length === 0) {
      const defaultThread = {
        id: 'default',
        name: 'New Conversation',
        messages: [],
        lastMessageTime: new Date().toISOString()
      };
      
      dispatch({
        type: 'CREATE_THREAD',
        payload: defaultThread
      });
      
      // Add welcome message to default thread
      setTimeout(() => {
        dispatch({
          type: 'ADD_MESSAGE',
          payload: {
            text: "# Welcome to SQL Matic! 👋\n\nI'm your SQL assistant. You can ask me questions about SQL queries, database design, or specific SQL commands.\n\nSome examples you can try:\n- How do I create a table?\n- Show me how to write a SELECT query\n- Explain JOINs\n- How to use aggregate functions?",
            sender: 'bot',
            userId: 'SQL-Bot',
            timestamp: new Date().toISOString(),
            threadId: 'default'
          }
        });
      }, 100);
    }
  }, [state.threads.length]);

  const sendMessage = async (text, userId = 'User1') => {
    // Add user message to state
    const userMessage = {
      text,
      sender: 'user',
      userId: userId,
      timestamp: new Date().toISOString(),
      threadId: state.currentThreadId
    };
    
    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    dispatch({ type: 'SET_LOADING', payload: true });
    
    try {
      // Call mock API service
      const response = await chatService.sendMessage(text);
      
      // Add bot response to state
      dispatch({
        type: 'ADD_MESSAGE',
        payload: {
          text: response.text,
          sender: 'bot',
          userId: 'SQL-Bot',
          timestamp: new Date().toISOString(),
          threadId: state.currentThreadId
        }
      });
    } catch (error) {
      console.error('Error sending message:', error);
      dispatch({
        type: 'SET_ERROR',
        payload: 'Failed to get response. Please try again.'
      });
      
      // Add error message
      dispatch({
        type: 'ADD_MESSAGE',
        payload: {
          text: 'Sorry, I encountered an error. Please try again.',
          sender: 'bot',
          userId: 'SQL-Bot',
          timestamp: new Date().toISOString(),
          threadId: state.currentThreadId
        }
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  // Function to create a new thread
  const createNewThread = () => {
    const threadId = `thread-${Date.now()}`;
    dispatch({
      type: 'CREATE_THREAD',
      payload: {
        id: threadId,
        name: `New Conversation`,
        messages: [],
        lastMessageTime: new Date().toISOString()
      }
    });
    
    // Add welcome message to new thread
    setTimeout(() => {
      dispatch({
        type: 'ADD_MESSAGE',
        payload: {
          text: "# New Thread Started\n\nHow can I help you with SQL today?",
          sender: 'bot',
          userId: 'SQL-Bot',
          timestamp: new Date().toISOString(),
          threadId
        }
      });
    }, 100);
  };

  // Function to switch between threads
  const switchThread = (threadId) => {
    dispatch({
      type: 'SWITCH_THREAD',
      payload: threadId
    });
  };

  return (
    <ChatContext.Provider
      value={{
        messages: state.messages,
        isLoading: state.isLoading,
        error: state.error,
        sendMessage,
        threads: state.threads,
        currentThreadId: state.currentThreadId,
        createNewThread,
        switchThread
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChatContext = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within a ChatProvider');
  }
  return context;
};
