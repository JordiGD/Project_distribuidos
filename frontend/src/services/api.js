import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://identical.localhost';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analyzeImage = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);

    const response = await api.post('/api/analyze-food', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Error al analizar la imagen');
  }
};

export const getResults = async (taskId) => {
  try {
    const response = await api.get(`/api/results/${taskId}`);
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Error al obtener resultados');
  }
};

export default api;
