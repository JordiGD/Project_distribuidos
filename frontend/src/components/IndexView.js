import React, { useRef } from 'react';

const IndexView = ({ onImageUpload }) => {
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      onImageUpload(file);
    }
  };

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onImageUpload(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  return (
    <div className="root-container">
      <div className="layout-container">
        <div className="layout-wrapper">
          <div className="layout-content-container">
            <div className="header-section">
              <div className="header-content">
                <p className="title">
                  Analiza las Calorías de tu Comida
                </p>
                <p className="subtitle">
                  Sube una foto y descubre su información nutricional.
                </p>
              </div>
            </div>
            <div className="upload-section">
              <div 
                className="upload-container"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
              >
                <div className="upload-content">
                  <span className="material-symbols-outlined upload-icon">cloud_upload</span>
                  <p className="upload-title">
                    Arrastra y suelta tu imagen aquí
                  </p>
                  <p className="upload-subtitle">
                    Formatos aceptados: JPG, PNG
                  </p>
                </div>
                <button className="upload-button" onClick={handleButtonClick}>
                  <span className="truncate">Seleccionar Imagen</span>
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                />
              </div>
            </div>
            <div className="progress-section" style={{ display: 'none' }}>
              <div className="progress-header">
                <p className="progress-text">
                  Analizando imagen...
                </p>
              </div>
              <div className="progress-bar-container">
                <div className="progress-bar" style={{ width: '50%' }}></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IndexView;