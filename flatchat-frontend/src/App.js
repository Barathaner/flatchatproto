import React from 'react';
import { CoordinatesProvider } from './CoordinatesContext';
import ChatComponent from './ChatComponent';
import MapboxComponent from './MapboxComponent';

const App = () => {
    return (
        <CoordinatesProvider>
        <MapboxComponent />
            <ChatComponent />
        </CoordinatesProvider>
    );
};

export default App;
