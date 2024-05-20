import React, { createContext, useState, useContext } from 'react';

const CoordinatesContext = createContext();

export const useCoordinates = () => useContext(CoordinatesContext);

export const CoordinatesProvider = ({ children }) => {
    const [minLat, setMinLat] = useState(41);
    const [maxLat, setMaxLat] = useState(43);
    const [minLon, setMinLon] = useState(2);
    const [maxLon, setMaxLon] = useState(3);

    return (
        <CoordinatesContext.Provider value={{
            minLat,
            setMinLat,
            maxLat,
            setMaxLat,
            minLon,
            setMinLon,
            maxLon,
            setMaxLon
        }}>
            {children}
        </CoordinatesContext.Provider>
    );
};
