// contexts/SensorContext.js
import React, { createContext, useState, useEffect } from 'react';
import io from 'socket.io-client';

const SensorContext = createContext();

export const SensorProvider = ({ children }) => {
  const [sensorData, setSensorData] = useState([]);
  const [socketConnected1, setSocketConnected1] = useState(false);
  const [socketConnected2, setSocketConnected2] = useState(false);
  const [gaugeValue, setGaugeValue] = useState(0);
  const [totalDistance, setTotalDistance] = useState(0);
  const [prevTimestamp, setPrevTimestamp] = useState(null);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleString());
  const [rfidData, setRfidData] = useState([]);

  const MAX_DATA_COUNT = 20;
  const MAX_SPEED = 350;

  const kmhToMs = (value) => {
    if (value === undefined) {
      return { value: 'N/A', unit: 'Km/h' };
    }
    if (value >= 1) {
      const msValue = value / 1;
      return { value: msValue.toFixed(2), unit: 'Kmph' };
    } else {
      return { value: value.toFixed(2), unit: 'Km/h' };
    }
  };

  useEffect(() => {
    const URL1 = "http://localhost:5002";
    const URL2 = "http://localhost:5000";
    const socket1 = io(URL1, {
      transports: ['websocket'],
      pingTimeout: 30000,
      pingInterval: 5000,
      upgradeTimeout: 30000,
      cors: {
        origin: "http://localhost:5173",
      }
    });
    const socket2 = io(URL2, {
      transports: ['websocket'],
      pingTimeout: 30000,
      pingInterval: 5000,
      upgradeTimeout: 30000,
      cors: {
        origin: "http://localhost:5173",
      }
    });

    socket1.connect();
    socket2.connect();

    socket1.on("connect_error", (err) => {
      console.log(`connect_error due to ${err.message}`);
    });

    socket2.on("connect_error", (err) => {
      console.log(`connect_error due to ${err.message}`);
    });

    socket1.on('connect', () => {
      setSocketConnected1(true);
    });

    socket2.on('connect', () => {
      setSocketConnected2(true);
    });

    socket1.on('disconnect', () => {
      setSocketConnected1(false);
    });

    socket2.on('disconnect', () => {
      setSocketConnected2(false);
    });

    socket1.on('speed_update', (data) => {
      const parsedData = typeof data === 'string' ? JSON.parse(data) : data;
      const { speed, timestamp } = parsedData;
      const newTimestamp = new Date(timestamp).getTime();
    
      setSensorData(prevData => {
        const newData = [...prevData, { date: newTimestamp, speed, time: new Date(newTimestamp).toLocaleString(), distance: totalDistance }].slice(-MAX_DATA_COUNT);
    
        const newGaugeValue = speed > MAX_SPEED ? MAX_SPEED : speed;
        setGaugeValue(newGaugeValue);
    
        if (prevTimestamp !== null) {
          const timeDiff = (newTimestamp - prevTimestamp) / 3600000; // time difference in hours
          const incrementalDistance = speed * timeDiff; // distance in kilometers
    
          const updatedDistance = totalDistance + incrementalDistance;
    
          setTotalDistance(updatedDistance);
    
          const updatedData = newData.map((point, index) => ({
            ...point,
            distance: index === 0 ? 0 : parseFloat(updatedDistance.toFixed(2)),
          }));
    
          setPrevTimestamp(newTimestamp);
          return updatedData;
        }
    
        setPrevTimestamp(newTimestamp);
        return newData;
      });
    });

    socket2.on('tag_data', (data) => {
      try {
        const parsedData = typeof data === 'string' ? JSON.parse(data) : data;

        setRfidData(prevData => {
          const updatedData = [...prevData, parsedData].slice(-MAX_DATA_COUNT);
          return updatedData;
        });
      } catch (error) {
        console.error('Error parsing data:', error); // Log any parsing errors
      }
    });

    const interval = setInterval(() => {
      setCurrentTime(new Date().toLocaleString());
    }, 1000);

    return () => {
      socket1.disconnect();
      socket2.disconnect();
      clearInterval(interval);
    };
  }, [prevTimestamp, totalDistance]);

  return (
    <SensorContext.Provider value={{
      sensorData,
      socketConnected1,
      socketConnected2,
      gaugeValue,
      totalDistance,
      currentTime,
      rfidData,
      kmhToMs
    }}>
      {children}
    </SensorContext.Provider>
  );
};

export default SensorContext;
