import React from 'react';

const NutritionResults = ({ results, imageUrl, onNewAnalysis }) => {
  const formatNutrientValue = (value, unit) => {
    if (typeof value === 'number') {
      return `${value.toFixed(1)} ${unit}`;
    }
    return `${value} ${unit}`;
  };

  const getNutrientColor = (nutrient) => {
    const colors = {
      'calorías': '#ff6b6b',
      'proteínas': '#4ecdc4',
      'carbohidratos': '#45b7d1',
      'grasas': '#96ceb4',
      'fibra': '#feca57',
      'azúcares': '#ff9ff3'
    };
    return colors[nutrient.toLowerCase()] || '#38e07b';
  };

  return (
    <div className="results-section">
      <div className="results-header">
        <h2>
          <span className="material-symbols-outlined">analytics</span>
          Análisis Nutricional Completo
        </h2>
        <button 
          className="btn btn-secondary new-analysis-btn"
          onClick={onNewAnalysis}
        >
          <span className="material-symbols-outlined">refresh</span>
          Nuevo Análisis
        </button>
      </div>

      <div className="results-content">
        {imageUrl && (
          <div className="analyzed-image">
            <img src={imageUrl} alt="Imagen analizada" />
            <div className="image-overlay">
              <span className="material-symbols-outlined">check_circle</span>
              <span>Análisis completado</span>
            </div>
          </div>
        )}

        <div className="nutrition-grid">
          {results && Object.entries(results).map(([nutrient, data]) => (
            <div key={nutrient} className="nutrition-card">
              <div className="card-header">
                <h3>{nutrient}</h3>
                <div 
                  className="nutrient-icon"
                  style={{ backgroundColor: getNutrientColor(nutrient) }}
                >
                  <span className="material-symbols-outlined">
                    {nutrient.toLowerCase().includes('calor') ? 'local_fire_department' :
                     nutrient.toLowerCase().includes('prote') ? 'fitness_center' :
                     nutrient.toLowerCase().includes('carb') ? 'grain' :
                     nutrient.toLowerCase().includes('gras') ? 'water_drop' :
                     'nutrition'}
                  </span>
                </div>
              </div>
              
              <div className="card-content">
                <div className="main-value">
                  {typeof data === 'object' ? 
                    formatNutrientValue(data.value, data.unit) : 
                    data
                  }
                </div>
                
                {typeof data === 'object' && data.percentage && (
                  <div className="percentage">
                    <div className="percentage-bar">
                      <div 
                        className="percentage-fill"
                        style={{ 
                          width: `${Math.min(data.percentage, 100)}%`,
                          backgroundColor: getNutrientColor(nutrient)
                        }}
                      ></div>
                    </div>
                    <span>{data.percentage}% CDR</span>
                  </div>
                )}
                
                {typeof data === 'object' && data.description && (
                  <p className="nutrient-description">{data.description}</p>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="results-summary">
          <div className="summary-card">
            <h3>
              <span className="material-symbols-outlined">insights</span>
              Resumen Nutricional
            </h3>
            <div className="summary-content">
              <p>Este análisis ha sido generado por nuestro modelo de IA Moondream2, 
                 que identifica los alimentos en la imagen y estima sus valores nutricionales.</p>
              
              <div className="summary-stats">
                <div className="stat">
                  <span className="material-symbols-outlined">psychology</span>
                  <div>
                    <strong>Modelo de IA</strong>
                    <span>Moondream2</span>
                  </div>
                </div>
                <div className="stat">
                  <span className="material-symbols-outlined">precision_manufacturing</span>
                  <div>
                    <strong>Precisión</strong>
                    <span>~85-90%</span>
                  </div>
                </div>
                <div className="stat">
                  <span className="material-symbols-outlined">schedule</span>
                  <div>
                    <strong>Procesado en</strong>
                    <span>&lt; 60 segundos</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="disclaimer">
            <span className="material-symbols-outlined">info</span>
            <p>Los valores nutricionales son estimaciones basadas en análisis de IA. 
               Para información precisa, consulta el etiquetado del producto o un profesional de la salud.</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NutritionResults;