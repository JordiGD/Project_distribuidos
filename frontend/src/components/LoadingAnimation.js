import React, { useState, useEffect } from 'react';

const LoadingAnimation = () => {
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(0);

  const steps = [
    'Procesando imagen...',
    'Analizando con IA...',
    'Calculando nutrientes...',
    'Generando resultados...'
  ];

  useEffect(() => {
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 2;
        if (newProgress >= 100) {
          clearInterval(progressInterval);
          return 100;
        }
        return newProgress;
      });
    }, 200);

    const stepInterval = setInterval(() => {
      setCurrentStep(prev => (prev + 1) % steps.length);
    }, 3000);

    return () => {
      clearInterval(progressInterval);
      clearInterval(stepInterval);
    };
  }, []);

  return (
    <div className="loading-section">
      <div className="loading-container">
        <div className="ai-animation">
          <div className="brain-icon">
            <span className="material-symbols-outlined">psychology</span>
          </div>
          <div className="pulse-rings">
            <div className="pulse-ring"></div>
            <div className="pulse-ring"></div>
            <div className="pulse-ring"></div>
          </div>
        </div>

        <h2>Analizando tu imagen</h2>
        <p className="loading-step">{steps[currentStep]}</p>

        <div className="progress-container">
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ width: `${Math.min(progress, 95)}%` }}
            ></div>
          </div>
          <span className="progress-text">
            {Math.floor(Math.min(progress, 95))}%
          </span>
        </div>

        <div className="loading-details">
          <div className="detail">
            <span className="material-symbols-outlined">memory</span>
            <span>IA Moondream2 procesando</span>
          </div>
          <div className="detail">
            <span className="material-symbols-outlined">timer</span>
            <span>Tiempo estimado: 30-60s</span>
          </div>
        </div>

        <div className="loading-tips">
          <h3>¿Sabías que?</h3>
          <p>Nuestro modelo de IA puede identificar más de 1000 tipos de alimentos diferentes y calcular sus valores nutricionales con alta precisión.</p>
        </div>
      </div>
    </div>
  );
};

export default LoadingAnimation;