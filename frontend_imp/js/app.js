// app.js - Funcionalidad visual del analizador de calorías

// ==================== PÁGINA DE CARGA (index.html) ====================

if (document.querySelector('.upload-container')) {
  const uploadContainer = document.querySelector('.upload-container');
  const uploadButton = document.querySelector('.upload-button');
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = 'image/jpeg, image/png, image/jpg';
  fileInput.style.display = 'none';
  document.body.appendChild(fileInput);

  // Click en el botón para seleccionar imagen
  uploadButton.addEventListener('click', () => {
    fileInput.click();
  });

  // Prevenir comportamiento por defecto del drag and drop
  uploadContainer.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadContainer.style.borderColor = '#38e07b';
    uploadContainer.style.backgroundColor = 'rgba(56, 224, 123, 0.05)';
  });

  uploadContainer.addEventListener('dragleave', (e) => {
    e.preventDefault();
    uploadContainer.style.borderColor = '';
    uploadContainer.style.backgroundColor = '';
  });

  // Soltar imagen
  uploadContainer.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadContainer.style.borderColor = '';
    uploadContainer.style.backgroundColor = '';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleImageUpload(files[0]);
    }
  });

  // Seleccionar imagen desde el input
  fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
      handleImageUpload(file);
    }
  });

  // Función para manejar la carga de imagen
  function handleImageUpload(file) {
    // Validar que sea una imagen
    if (!file.type.match('image/jpeg') && !file.type.match('image/png')) {
      alert('Por favor, selecciona una imagen en formato JPG o PNG');
      return;
    }

    // Validar tamaño (máximo 10MB)
    if (file.size > 10 * 1024 * 1024) {
      alert('La imagen es demasiado grande. Por favor, selecciona una imagen menor a 10MB');
      return;
    }

    // Leer la imagen y guardarla en sessionStorage
    const reader = new FileReader();
    reader.onload = (e) => {
      const imageData = e.target.result;
      
      // Guardar la imagen en sessionStorage
      sessionStorage.setItem('uploadedImage', imageData);
      sessionStorage.setItem('uploadedImageName', file.name);
      
      // Mostrar barra de progreso y simular análisis
      showProgressBar();
    };
    reader.readAsDataURL(file);
  }

  // Función para mostrar la barra de progreso
  function showProgressBar() {
    const progressSection = document.querySelector('.progress-section');
    const progressBar = document.querySelector('.progress-bar');
    const progressText = document.querySelector('.progress-text');
    
    // Mostrar la sección de progreso
    progressSection.style.display = 'flex';
    
    // Animar la barra de progreso
    let progress = 0;
    const interval = setInterval(() => {
      progress += 5;
      progressBar.style.width = progress + '%';
      
      // Actualizar texto según el progreso
      if (progress < 30) {
        progressText.textContent = 'Cargando imagen...';
      } else if (progress < 60) {
        progressText.textContent = 'Procesando imagen...';
      } else if (progress < 90) {
        progressText.textContent = 'Analizando contenido...';
      } else {
        progressText.textContent = 'Finalizando...';
      }
      
      // Al llegar al 100%, redirigir a la página de resultados
      if (progress >= 100) {
        clearInterval(interval);
        setTimeout(() => {
          window.location.href = 'resultado.html';
        }, 500);
      }
    }, 100); // Actualizar cada 100ms (total ~3 segundos)
  }
}

// ==================== PÁGINA DE RESULTADOS (resultado.html) ====================

if (document.querySelector('.results-card')) {
  // Cargar la imagen guardada
  const uploadedImage = sessionStorage.getItem('uploadedImage');
  const uploadedImageName = sessionStorage.getItem('uploadedImageName');
  
  if (uploadedImage) {
    const foodImage = document.querySelector('.food-image');
    foodImage.style.backgroundImage = `url(${uploadedImage})`;
    
    // Actualizar el alt text con el nombre del archivo
    if (uploadedImageName) {
      foodImage.setAttribute('data-alt', `Imagen de ${uploadedImageName}`);
    }
  } else {
    // Si no hay imagen, mostrar imagen por defecto o redirigir
    console.log('No hay imagen cargada');
    // Opcional: redirigir a index.html
    // window.location.href = 'index.html';
  }

  // Datos de ejemplo para la simulación (cuando se agregue el backend, esto se reemplazará)
  const mockData = {
    nombre: 'Alimento Detectado',
    calorias: 0,
    proteinas: 0,
    carbohidratos: 0,
    grasas: 0
  };

  // Actualizar la UI con los datos (por ahora vacíos)
  updateResultsUI(mockData);

  // Función para actualizar la interfaz con los resultados
  function updateResultsUI(data) {
    // Actualizar nombre del alimento
    const foodName = document.querySelector('.food-name');
    if (foodName) {
      foodName.textContent = data.nombre;
    }

    // Actualizar calorías
    const caloriesNumber = document.querySelector('.calories-number');
    if (caloriesNumber) {
      caloriesNumber.textContent = data.calorias;
    }

    // Actualizar proteínas
    const nutritionValues = document.querySelectorAll('.nutrition-value');
    if (nutritionValues[0]) {
      nutritionValues[0].textContent = data.proteinas + ' g';
    }

    // Actualizar carbohidratos
    if (nutritionValues[1]) {
      nutritionValues[1].textContent = data.carbohidratos + ' g';
    }

    // Actualizar grasas
    if (nutritionValues[2]) {
      nutritionValues[2].textContent = data.grasas + ' g';
    }
  }

  // Botón para analizar otro alimento
  const actionButton = document.querySelector('.action-button');
  if (actionButton) {
    actionButton.addEventListener('click', () => {
      // Limpiar sessionStorage
      sessionStorage.removeItem('uploadedImage');
      sessionStorage.removeItem('uploadedImageName');
      sessionStorage.removeItem('analysisResults');
      
      // Redirigir a la página principal
      window.location.href = 'index.html';
    });
  }
}

// ==================== FUNCIONES PARA INTEGRAR CON EL BACKEND ====================

// Esta función se llamará cuando recibas los datos del backend
function updateWithBackendData(backendResponse) {
  const data = {
    nombre: backendResponse.foodName || 'Alimento no identificado',
    calorias: backendResponse.calories || 0,
    proteinas: backendResponse.protein || 0,
    carbohidratos: backendResponse.carbs || 0,
    grasas: backendResponse.fats || 0
  };

  // Guardar en sessionStorage para persistencia
  sessionStorage.setItem('analysisResults', JSON.stringify(data));

  // Actualizar la UI
  if (document.querySelector('.results-card')) {
    updateResultsUI(data);
  }
}

// Función para enviar la imagen al backend (placeholder)
async function sendImageToBackend(imageData) {
  try {
    // Aquí irá la llamada real a tu backend
    // const response = await fetch('TU_API_ENDPOINT', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify({ image: imageData })
    // });
    // const data = await response.json();
    // return data;

    // Por ahora, retorna datos de ejemplo
    return {
      foodName: 'Esperando análisis...',
      calories: 0,
      protein: 0,
      carbs: 0,
      fats: 0
    };
  } catch (error) {
    console.error('Error al enviar imagen al backend:', error);
    throw error;
  }
}

// ==================== MODO OSCURO (OPCIONAL) ====================

// Detectar preferencia del sistema
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
  document.documentElement.classList.add('dark');
} else {
  document.documentElement.classList.remove('dark');
}

// Escuchar cambios en la preferencia del sistema
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
  if (e.matches) {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
});