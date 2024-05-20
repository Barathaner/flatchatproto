import React, { useState, useRef, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import axios from 'axios';
import 'mapbox-gl/dist/mapbox-gl.css';
import './MapboxComponent.css';  // Import the CSS file for styling
import { useCoordinates } from './CoordinatesContext';

mapboxgl.accessToken = process.env.REACT_APP_MAPBOX_TOKEN;

const MapboxComponent = () => {
    const mapContainer = useRef(null);
    const map = useRef(null);
    const [markers, setMarkers] = useState([]);
    const [mapMarkers, setMapMarkers] = useState([]); // Array to store map marker objects
    const { minLat, setMinLat, maxLat, setMaxLat, minLon, setMinLon, maxLon, setMaxLon } = useCoordinates();

    useEffect(() => {
        if (map.current) return; // Initialize map only once
        map.current = new mapboxgl.Map({
            container: mapContainer.current,
            style: 'mapbox://styles/mapbox/streets-v11',
            center: [2.1734, 41.3851], // Default center
            zoom: 13
        });
    }, []);

    const addMarker = (marker) => {
        let carouselHTML = '';
        if (marker.urls && marker.urls.length) {
            carouselHTML = '<div class="carousel-container" style="display: flex; overflow-x: auto;">';
            marker.urls.forEach((url, index) => {
                carouselHTML += `<div class="carousel-item" style="min-width: 100%;"><img src="${url}" style="width: 100%; height: auto; display: block;"></div>`;
            });
            carouselHTML += `</div>`;
        }
    
        var popup = new mapboxgl.Popup().setHTML(`
            <div>
                <strong>Marker ID:</strong> ${marker.id}<br>
                <strong>Price:</strong> ${marker.price}<br>
                <strong>Number of Roomates:</strong> ${marker.numberofroomates}<br>
                <strong>Images:</strong>
                ${carouselHTML}
            </div>
        `);

        const mapMarker = new mapboxgl.Marker()
            .setLngLat([marker.longitude, marker.latitude])
            .setPopup(popup)
            .addTo(map.current);

        return mapMarker;
    };

    const handleSearch = async () => {
        // Clear existing markers from the map
        mapMarkers.forEach(marker => marker.remove());
        setMapMarkers([]);

        try {
            const response = await axios.post('http://localhost:5000/search_by_coordinates', {
                min_lat: parseFloat(minLat),
                max_lat: parseFloat(maxLat),
                min_lon: parseFloat(minLon),
                max_lon: parseFloat(maxLon)
            });
            const newMarkers = response.data.matches.map(item => ({
                id: item.id,
                latitude: item.metadata.latitude,
                longitude: item.metadata.longitude,
                price: item.metadata.price,
                numberofroomates: item.metadata.numberofroomates,
                urls: JSON.parse(item.metadata.url.replace(/'/g, '"')) // Convert single quotes to double quotes for valid JSON
            }));
            setMarkers(newMarkers); // Update state with new markers
            const newMapMarkers = newMarkers.map(addMarker); // Add new markers to the map and store them
            setMapMarkers(newMapMarkers);
        } catch (error) {
            console.error('Error fetching markers:', error);
        }
    };

    return (
        <div style={{ position: 'relative' }}>
            <div ref={mapContainer} style={{ width: '100%', height: '50vh' }}>
                <div className="input-container">
                    <input className="input-field" type="text" value={minLat} onChange={e => setMinLat(e.target.value)} placeholder="Min Latitude" />
                    <input className="input-field" type="text" value={maxLat} onChange={e => setMaxLat(e.target.value)} placeholder="Max Latitude" />
                    <input className="input-field" type="text" value={minLon} onChange={e => setMinLon(e.target.value)} placeholder="Min Longitude" />
                    <input className="input-field" type="text" value={maxLon} onChange={e => setMaxLon(e.target.value)} placeholder="Max Longitude" />
                    <button className="search-button" onClick={handleSearch}>Search in Area</button>
                </div>
            </div>
        </div>
    );
};

export default MapboxComponent;
