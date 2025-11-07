from pydantic import BaseModel, Field, validator

class NutritionInfo(BaseModel):
    comida: str = Field(description="Nombre y descripción específica del alimento identificado")
    calorias: float = Field(ge=0, description="Calorías totales en kcal")
    proteinas: float = Field(ge=0, description="Proteínas en gramos")
    carbohidratos: float = Field(ge=0, description="Carbohidratos en gramos")
    grasas: float = Field(ge=0, description="Grasas en gramos")
    fibra: float = Field(ge=0, default=0, description="Fibra en gramos")
    confianza: float = Field(ge=0, le=100, default=85, description="Nivel de confianza del análisis en porcentaje")
    
    @validator('comida')
    def validate_comida(cls, v):
        if not v or v.lower() in ['no identificado', 'unknown', '']:
            return "Alimento no identificado"
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "comida": "Pizza Margherita con tomate y mozzarella",
                "calorias": 450,
                "proteinas": 25,
                "carbohidratos": 50,
                "grasas": 18,
                "fibra": 3,
                "confianza": 90
            }
        }