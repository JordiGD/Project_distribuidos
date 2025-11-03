import React from 'react';

const ErrorDisplay = ({ error, onRetry }) => {
  const getErrorDetails = (errorMessage) => {
    const errorMap = {
      'Error al analizar la imagen': {
        icon: 'image_not_supported',
        title: 'Error al procesar imagen',
        suggestions: [
          'Verifica que el archivo sea una imagen válida',
          'Intenta con una imagen de mejor calidad',
          'Asegúrate de que el archivo no esté corrupto'
        ]
      },
      'Error al obtener resultados': {
        icon: 'cloud_off',
        title: 'Error de conexión',
        suggestions: [
          'Verifica tu conexión a internet',
          'El servidor puede estar temporalmente ocupado',
          'Intenta nuevamente en unos momentos'
        ]
      },
      'Tiempo de espera agotado': {
        icon: 'timer_off',
        title: 'Tiempo de análisis agotado',
        suggestions: [
          'El análisis está tomando más tiempo de lo esperado',
          'Intenta con una imagen más simple',
          'El servidor puede estar procesando muchas solicitudes'
        ]
      }
    };

    // Buscar coincidencia parcial
    for (const [key, details] of Object.entries(errorMap)) {
      if (errorMessage.includes(key)) {
        return details;
      }
    }

    // Error genérico
    return {
      icon: 'error',
      title: 'Error inesperado',
      suggestions: [
        'Ha ocurrido un error inesperado',
        'Intenta recargar la página',
        'Si el problema persiste, contacta soporte'
      ]
    };
  };

  const errorDetails = getErrorDetails(error);

  return (
    <div className="error-section">
      <div className="error-container">
        <div className="error-icon">
          <span className="material-symbols-outlined">{errorDetails.icon}</span>
        </div>

        <h2>{errorDetails.title}</h2>
        <p className="error-message">{error}</p>

        <div className="error-suggestions">
          <h3>Posibles soluciones:</h3>
          <ul>
            {errorDetails.suggestions.map((suggestion, index) => (
              <li key={index}>
                <span className="material-symbols-outlined">check_circle</span>
                {suggestion}
              </li>
            ))}
          </ul>
        </div>

        <div className="error-actions">
          <button 
            className="btn btn-primary retry-btn"
            onClick={onRetry}
          >
            <span className="material-symbols-outlined">refresh</span>
            Intentar de nuevo
          </button>

          <button 
            className="btn btn-secondary"
            onClick={() => window.location.reload()}
          >
            <span className="material-symbols-outlined">home</span>
            Recargar página
          </button>
        </div>

        <div className="error-info">
          <div className="info-item">
            <span className="material-symbols-outlined">support_agent</span>
            <div>
              <strong>¿Necesitas ayuda?</strong>
              <p>Si el problema persiste, nuestro sistema de IA puede estar experimentando alta demanda.</p>
            </div>
          </div>

          <div className="info-item">
            <span className="material-symbols-outlined">bug_report</span>
            <div>
              <strong>Reportar problema</strong>
              <p>Ayúdanos a mejorar reportando este error a nuestro equipo técnico.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay;