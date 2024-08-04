import React, { useState } from 'react';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';

function App() {
  const [mp3Url, setMp3Url] = useState(null);
  const [error, setError] = useState(null);

  const onDrop = (acceptedFiles) => {
    const formData = new FormData();
    formData.append('audio', acceptedFiles[0]);

    axios.post('http://127.0.0.1:5000/process-audio', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    .then(response => {
      if (response.data.mp3_url) {
        setMp3Url(response.data.mp3_url);
        setError(null);
      } else {
        setError("No MP3 URL returned.");
      }
    })
    .catch(error => {
      setError("Error processing audio: " + error.message);
    });
  };

  const { getRootProps, getInputProps } = useDropzone({ onDrop });

  return (
    <div className="App">
      <h1>Audio to Piano Music</h1>
      <div {...getRootProps()} style={{ border: '2px dashed #ccc', padding: '20px', textAlign: 'center' }}>
        <input {...getInputProps()} />
        <p>Drag 'n' drop an audio file here, or click to select one</p>
      </div>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      {mp3Url && (
        <div>
          <h2>Download MP3:</h2>
          <a href={mp3Url} download="output_music.mp3">Download MP3</a>
        </div>
      )}
    </div>
  );
}

export default App;
