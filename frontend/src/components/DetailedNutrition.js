import React from 'react';

const DetailedNutrition = ({ results }) => {
  if (!results) return null;

  const nutritionItems = [
    {
      key: 'calorías',
      icon: 'local_fire_department',
      color: '#ff6b6b'
    },
    {
      key: 'proteínas',
      icon: 'fitness_center',
      color: '#4ecdc4'
    },
    {
      key: 'carbohidratos',
      icon: 'bakery_dining',
      color: '#45b7d1'
    },
    {
      key: 'grasas',
      icon: 'oil_barrel',
      color: '#96ceb4'
    },
    {
      key: 'fibra',
      icon: 'grass',
      color: '#feca57'
    },
    {
      key: 'confianza',
      icon: 'verified',
      color: '#38e07b'
    }
  ];

  const formatValue = (item) => {
    const data = results[item.key];
    if (!data) return null;
    
    if (typeof data === 'object') {
      return {
        value: `${data.value || 0} ${data.unit || ''}`,
        description: data.description || ''
      };
    }
    return {
      value: data,
      description: ''
    };
  };

  return (
    <div className="detailed-nutrition">
      <h3>
        <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', marginRight: '0.5rem' }}>
          analytics
        </span>
        Análisis Nutricional Detallado
      </h3>

      <div className="nutrition-details-grid">
        {nutritionItems.map((item) => {
          const formatted = formatValue(item);
          if (!formatted) return null;

          return (
            <div key={item.key} className="nutrition-detail-item">
              <span 
                className="material-symbols-outlined" 
                style={{ 
                  fontSize: '2rem', 
                  color: item.color,
                  marginBottom: '0.5rem'
                }}
              >
                {item.icon}
              </span>
              <span className="label">
                {item.key.charAt(0).toUpperCase() + item.key.slice(1)}
              </span>
              <span className="value" style={{ color: item.color }}>
                {formatted.value}
              </span>
              {formatted.description && (
                <span className="description">{formatted.description}</span>
              )}
            </div>
          );
        })}
      </div>

      {results.food_type && (
        <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
          <h4 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.5rem' }}>
            Alimento Identificado
          </h4>
          <p style={{ fontSize: '1.25rem', fontWeight: '700', color: 'var(--primary)' }}>
            {results.food_type}
          </p>
        </div>
      )}

      {results.raw_analysis && (
        <div className="raw-analysis">
          <h4>
            <span className="material-symbols-outlined" style={{ verticalAlign: 'middle', marginRight: '0.5rem', fontSize: '1.125rem' }}>
              description
            </span>
            Análisis Completo del Modelo
          </h4>
          <p>{results.raw_analysis}</p>
        </div>
      )}

      {results.model && (
        <div style={{ textAlign: 'center' }}>
          <span className="model-badge">
            <span className="material-symbols-outlined">psychology</span>
            Analizado con {results.model}
          </span>
        </div>
      )}
    </div>
  );
};

export default DetailedNutrition;
