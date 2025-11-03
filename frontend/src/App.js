import React, { useState } from 'react';
import IndexView from './components/IndexView';
import ResultView from './components/ResultView';
import { analyzeImage, getResults } from './services/api';

function App() {
  const [currentView, setCurrentView] = useState('index'); // 'index', 'result'
  const [taskId, setTaskId] = useState(null);
  const [results, setResults] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleImageUpload = async (imageFile) => {
    try {
      setIsLoading(true);
      
      // Guardar la imagen subida para mostrarla en resultados
      const imageUrl = URL.createObjectURL(imageFile);
      setUploadedImage(imageUrl);
      
      // Enviar imagen para análisis
      const response = await analyzeImage(imageFile);
      setTaskId(response.task_id);
      
      // Cambiar a vista de resultado
      setCurrentView('result');
      
      // Polling para obtener resultados
      pollForResults(response.task_id);
      
    } catch (err) {
      setIsLoading(false);
      alert('Error: ' + err.message);
    }
  };

  const pollForResults = async (taskId) => {
    const maxAttempts = 30;
    let attempts = 0;
    
    const poll = async () => {
      try {
        attempts++;
        const response = await getResults(taskId);
        
        if (response.status === 'completed') {
          setResults(response.results);
          setIsLoading(false);
        } else if (response.status === 'processing' && attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setIsLoading(false);
          alert('Tiempo de espera agotado');
        }
      } catch (err) {
        setIsLoading(false);
        alert('Error: ' + err.message);
      }
    };
    
    poll();
  };

  const handleNewAnalysis = () => {
    setCurrentView('index');
    setTaskId(null);
    setResults(null);
    setIsLoading(false);
    if (uploadedImage) {
      URL.revokeObjectURL(uploadedImage);
      setUploadedImage(null);
    }
  };

  return (
    <>
      {currentView === 'index' && (
        <IndexView onImageUpload={handleImageUpload} />
      )}
      
      {currentView === 'result' && (
        <ResultView 
          results={results}
          imageUrl={uploadedImage}
          isLoading={isLoading}
          onNewAnalysis={handleNewAnalysis}
        />
      )}
    </>
  );
}

export default App;