import React, { useEffect, useState } from 'react';

const ResultView = ({ results, imageUrl, isLoading, onNewAnalysis }) => {
  const [displayCalories, setDisplayCalories] = useState(0);
  const [foodName, setFoodName] = useState('Analizando...');
  const [nutritionData, setNutritionData] = useState({
    proteins: '0 g',
    carbs: '0 g', 
    fats: '0 g'
  });

  useEffect(() => {
    if (results && !isLoading) {
      // Extraer calorías del resultado
      const calories = results.calorías || results.calories || results.Calorías || 0;
      setDisplayCalories(typeof calories === 'object' ? calories.value || 0 : calories);
      
      // Extraer nombre del alimento si está disponible
      setFoodName(results.nombre || results.name || results.alimento || 'Alimento analizado');
      
      // Extraer datos nutricionales
      setNutritionData({
        proteins: formatNutrient(results.proteínas || results.proteins || results.Proteínas),
        carbs: formatNutrient(results.carbohidratos || results.carbohydrates || results.Carbohidratos),
        fats: formatNutrient(results.grasas || results.fats || results.Grasas)
      });
    }
  }, [results, isLoading]);

  const formatNutrient = (value) => {
    if (!value) return '0 g';
    if (typeof value === 'object') {
      return `${value.value || 0} ${value.unit || 'g'}`;
    }
    return typeof value === 'number' ? `${value} g` : value;
  };

  return (
    <div className="root-container">
      <div className="layout-container">
        <div className="layout-wrapper-results">
          <div className="layout-content-container">
            <div className="header-section">
              <div className="header-content-left">
                <p className="title">Resultado del Análisis</p>
                <p className="subtitle-results">Información Nutricional</p>
              </div>
            </div>

            <div className="results-container">
              <div className="results-card">
                <div className="results-layout">
                  {/* Imagen del alimento */}
                  <div className="image-section">
                    <div 
                      className="food-image" 
                      style={{
                        backgroundImage: imageUrl ? `url(${imageUrl})` : 'none',
                        backgroundSize: 'cover',
                        backgroundPosition: 'center',
                        backgroundColor: imageUrl ? 'transparent' : '#f0f0f0'
                      }}
                      data-alt="Imagen del alimento analizado"
                    ></div>
                  </div>

                  {/* Información principal */}
                  <div className="info-section">
                    <p className="food-name">{isLoading ? 'Analizando...' : foodName}</p>
                    <div className="calories-display">
                      <span className="material-symbols-outlined calories-icon">local_fire_department</span>
                      <p className="calories-number">{isLoading ? '...' : displayCalories}</p>
                      <p className="calories-label">Calorías</p>
                    </div>
                    <p className="disclaimer">Los valores son aproximados y pueden variar.</p>
                  </div>
                </div>

                {/* Separador */}
                <div className="section-divider"></div>

                {/* Resumen nutricional */}
                <h2 className="nutrition-title">Resumen Nutricional</h2>
                <div className="nutrition-grid">
                  <div className="nutrition-card">
                    <span className="material-symbols-outlined nutrition-icon">fitness_center</span>
                    <div>
                      <p className="nutrition-label">Proteínas</p>
                      <p className="nutrition-value">{isLoading ? '...' : nutritionData.proteins}</p>
                    </div>
                  </div>

                  <div className="nutrition-card">
                    <span className="material-symbols-outlined nutrition-icon">bakery_dining</span>
                    <div>
                      <p className="nutrition-label">Carbohidratos</p>
                      <p className="nutrition-value">{isLoading ? '...' : nutritionData.carbs}</p>
                    </div>
                  </div>

                  <div className="nutrition-card">
                    <span className="material-symbols-outlined nutrition-icon">oil_barrel</span>
                    <div>
                      <p className="nutrition-label">Grasas</p>
                      <p className="nutrition-value">{isLoading ? '...' : nutritionData.fats}</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="button-container">
              <button className="action-button" onClick={onNewAnalysis}>
                <span className="truncate">Analizar otro alimento</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResultView;