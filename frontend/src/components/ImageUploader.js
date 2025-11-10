import React, { useState, useRef } from 'react';

const ImageUploader = ({ onImageUpload }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [isPriority, setIsPriority] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
    }
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUpload = () => {
    if (selectedFile) {
      onImageUpload(selectedFile, isPriority);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="root-container">
      <div className="layout-container">
        <div className="layout-wrapper">
          <div className="layout-content-container">
            <div className="header-section">
              <div className="header-content">
                <p className="title">Analiza las Calorías de tu Comida</p>
                <p className="subtitle">Sube una foto y descubre su información nutricional.</p>
              </div>
            </div>

            <div className="upload-section">
              <div 
                className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleClick}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileInputChange}
                  style={{ display: 'none' }}
                />
                
                <div className="upload-content">
                  <span className="material-symbols-outlined upload-icon">cloud_upload</span>
                  <h2>Sube una imagen de tu comida</h2>
                  <p>Arrastra y suelta una imagen aquí o haz clic para seleccionar</p>
                  <div className="upload-formats">
                    <span>Formatos: JPG, PNG, WEBP</span>
                  </div>
                </div>
              </div>

      {selectedFile && (
        <div className="selected-file">
          <div className="file-info">
            <span className="material-symbols-outlined">image</span>
            <span className="file-name">{selectedFile.name}</span>
            <span className="file-size">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </span>
          </div>
          
          <div className="priority-selector">
            <label className="priority-option">
              <input
                type="checkbox"
                checked={isPriority}
                onChange={(e) => setIsPriority(e.target.checked)}
              />
              <span className="material-symbols-outlined">
                {isPriority ? 'bolt' : 'schedule'}
              </span>
              <span className="priority-text">
                {isPriority ? 'Análisis Prioritario (15-30s)' : 'Análisis Normal (30-60s)'}
              </span>
            </label>
          </div>
          
          <button 
            className="btn btn-primary analyze-btn"
            onClick={handleUpload}
          >
            <span className="material-symbols-outlined">psychology</span>
            Analizar Imagen
          </button>
        </div>
      )}

              <div className="features">
                <div className="feature">
                  <span className="material-symbols-outlined">speed</span>
                  <h3>Análisis Rápido</h3>
                  <p>Resultados en 30-60 segundos</p>
                </div>
                <div className="feature">
                  <span className="material-symbols-outlined">health_and_safety</span>
                  <h3>Información Nutricional</h3>
                  <p>Calorías, macros y más</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ImageUploader;