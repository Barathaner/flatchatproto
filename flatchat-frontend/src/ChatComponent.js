import React, { useState } from 'react';
import axios from 'axios';
import { useCoordinates } from './CoordinatesContext';
import ReactMarkdown from 'react-markdown';
import styled, { keyframes } from 'styled-components';

// Styled components
const ChatContainer = styled.div`
  display: flex;
  flex-direction: column;
  height: 50vh;
  background-color: #1a1a1a;
  color: #ccc;
`;

const MessageContainer = styled.div`
  flex-grow: 1;
  overflow-y: auto;
  padding: 10px;
`;

const Message = styled.div`
  display: flex;
  justify-content: ${({ sender }) => sender === 'user' ? 'flex-end' : 'flex-start'};
  margin-bottom: 10px;
`;

const MessageBox = styled.div`
  max-width: 70%;
  padding: 8px;
  border-radius: 10px;
  background-color: ${({ sender }) => sender === 'user' ? '#333' : '#555'};
  color: ${({ sender }) => sender === 'user' ? '#FFF' : '#EEE'};
  border: ${({ sender }) => sender === 'user' ? '1px solid #444' : '1px solid #666'};
`;

const InputContainer = styled.div`
  display: flex;
  padding: 10px;
`;

const Input = styled.input`
  flex-grow: 1;
  padding: 8px;
  border: none;
  border-radius: 4px;
  margin-right: 8px;
`;

const Button = styled.button`
  padding: 8px 16px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
`;

const TypingAnimation = keyframes`
  0% { content: ''; }
  33% { content: '.'; }
  66% { content: '..'; }
  100% { content: '...'; }
`;

const TypingIndicator = styled.div`
  color: #888;
  font-style: italic;
  &:after {
    content: '';
    animation: ${TypingAnimation} 1.5s step-start infinite;
  }
`;

const ChatComponent = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const { minLat, maxLat, minLon, maxLon } = useCoordinates();

  const sendMessage = async () => {
    const newMessages = [...messages, { text: input, sender: 'user' }];
    setMessages(newMessages);
    setInput('');
    setIsTyping(true);

    try {
      const response = await axios.post('http://127.0.0.1:5000/search_by_prompt', {
        prompt: input,
        ...{min_lat: parseFloat(minLat), max_lat: parseFloat(maxLat), min_lon: parseFloat(minLon), max_lon: parseFloat(maxLon)}
      });
      setIsTyping(false);
      setMessages([...newMessages, { text: response.data, sender: 'api' }]);
    } catch (error) {
      setIsTyping(false);
      console.error('Error sending message:', error);
      setMessages([...newMessages, { text: 'Error receiving response.', sender: 'api' }]);
    }
  };

  return (
    <ChatContainer>
      <MessageContainer>
        {messages.map((msg, index) => (
          <Message key={index} sender={msg.sender}>
            <MessageBox sender={msg.sender}>
              <ReactMarkdown>
                {msg.text}
              </ReactMarkdown>
            </MessageBox>
          </Message>
        ))}
        {isTyping && <TypingIndicator>Typing</TypingIndicator>}
      </MessageContainer>
      <InputContainer>
        <Input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={event => event.key === 'Enter' && sendMessage()}
        />
        <Button onClick={sendMessage}>Send</Button>
      </InputContainer>
    </ChatContainer>
  );
};

export default ChatComponent;
