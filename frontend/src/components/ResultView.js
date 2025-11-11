import React, { useEffect, useState } from 'react';
import LoadingDots from './LoadingDots';

const ResultView = ({ results, imageUrl, isLoading, onNewAnalysis }) => {
  const [displayCalories, setDisplayCalories] = useState(0);
  const [foodName, setFoodName] = useState('Analizando...');
  const [foodDescription, setFoodDescription] = useState('');
  const [nutritionData, setNutritionData] = useState({
    proteins: '0 g',
    carbs: '0 g', 
    fats: '0 g',
    fiber: '0 g'
  });

  useEffect(() => {
    console.log('ResultView - results:', results);
    console.log('ResultView - isLoading:', isLoading);
    
    if (results && !isLoading) {
      // Extraer calorías del resultado
      const calories = results.calorías || results.calories || results.Calorías || 0;
      const calorieValue = typeof calories === 'object' ? calories.value || 0 : calories;
      setDisplayCalories(Math.round(calorieValue));
      
      // Extraer nombre del alimento si está disponible
      const name = results.nombre || results.name || results.alimento || results.food_type || 'Alimento analizado';
      setFoodName(name);
      
      // Extraer descripción del análisis raw
      const rawAnalysis = results.raw_analysis || '';
      setFoodDescription(rawAnalysis);
      
      // Extraer datos nutricionales
      const newNutritionData = {
        proteins: formatNutrient(results.proteínas || results.proteins || results.Proteínas),
        carbs: formatNutrient(results.carbohidratos || results.carbohydrates || results.Carbohidratos),
        fats: formatNutrient(results.grasas || results.fats || results.Grasas),
        fiber: formatNutrient(results.fibra || results.fiber)
      };
      
      console.log('Nutrition data extracted:', newNutritionData);
      setNutritionData(newNutritionData);
    }
  }, [results, isLoading]);

  const formatNutrient = (value) => {
    if (!value) return '0 g';
    if (typeof value === 'object') {
      const num = value.value || 0;
      const unit = value.unit || 'g';
      return `${Math.round(num * 10) / 10} ${unit}`;
    }
    return typeof value === 'number' ? `${Math.round(value * 10) / 10} g` : value;
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
                    <p className="food-name">{isLoading ? <span>Analizando<LoadingDots /></span> : foodName}</p>
                    <div className="calories-display">
                      <span className="material-symbols-outlined calories-icon">local_fire_department</span>
                      <p className="calories-number">{isLoading ? <LoadingDots /> : displayCalories}</p>
                      <p className="calories-label">Calorías</p>
                    </div>
                    {!isLoading && foodDescription && (
                      (nutritionData.proteins !== '0 g' && nutritionData.carbs !== '0 g' && nutritionData.fats !== '0 g' && nutritionData.fiber !== '0 g') ? (
                        <div className="food-description">
                          <p>{foodDescription}</p>
                        </div>
                      ) : (
                        <div className="food-description-badge">
                          <p>{foodDescription}</p>
                        </div>
                      )
                    )}
                  </div>
                </div>

                {/* Separador */}
                <div className="section-divider"></div>

                {/* Resumen nutricional */}
                {!isLoading && (nutritionData.proteins === '0 g' && nutritionData.carbs === '0 g' && nutritionData.fats === '0 g' && nutritionData.fiber === '0 g') ? (
                  <p className="no-nutrition-data">No se encontraron datos nutricionales adicionales.</p>
                ) : (
                <h2 className="nutrition-title">Resumen Nutricional</h2>
                )}
                <div className="nutrition-grid">
                  {!isLoading && nutritionData.proteins && nutritionData.proteins !== '0 g' && (
                  <div className="nutrition-card">
                    <span className="material-symbols-outlined nutrition-icon">fitness_center</span>
                    <div>
                      <p className="nutrition-label">Proteínas</p>
                      <p className="nutrition-value">{isLoading ? <LoadingDots /> : nutritionData.proteins}</p>
                    </div>
                  </div>
                  )}

                  {!isLoading && nutritionData.carbs && nutritionData.carbs !== '0 g' && (
                  <div className="nutrition-card">
                    <span className="material-symbols-outlined nutrition-icon">bakery_dining</span>
                    <div>
                      <p className="nutrition-label">Carbohidratos</p>
                      <p className="nutrition-value">{isLoading ? <LoadingDots /> : nutritionData.carbs}</p>
                    </div>
                  </div>
                  )}

                  {!isLoading && nutritionData.fats && nutritionData.fats !== '0 g' && (
                  <div className="nutrition-card">
                    <span className="material-symbols-outlined nutrition-icon">oil_barrel</span>
                    <div>
                      <p className="nutrition-label">Grasas</p>
                      <p className="nutrition-value">{isLoading ? <LoadingDots /> : nutritionData.fats}</p>
                    </div>
                  </div>
                  )}

                  {!isLoading && nutritionData.fiber && nutritionData.fiber !== '0 g' && (
                    <div className="nutrition-card">
                      <span className="material-symbols-outlined nutrition-icon">grass</span>
                      <div>
                        <p className="nutrition-label">Fibra</p>
                        <p className="nutrition-value">{nutritionData.fiber}</p>
                      </div>
                    </div>
                  )}
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