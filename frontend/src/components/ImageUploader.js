import React, { useState, useRef } from 'react';

const ImageUploader = ({ onImageUpload }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
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
      onImageUpload(selectedFile);
    }
  };

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  return (
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
          <span className="material-symbols-outlined">precision_manufacturing</span>
          <h3>IA Avanzada</h3>
          <p>Powered by Moondream2</p>
        </div>
        <div className="feature">
          <span className="material-symbols-outlined">health_and_safety</span>
          <h3>Información Nutricional</h3>
          <p>Calorías, macros y más</p>
        </div>
      </div>
    </div>
  );
};

export default ImageUploader;