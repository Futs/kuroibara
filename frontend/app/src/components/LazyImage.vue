<template>
  <div 
    ref="imageContainer"
    class="lazy-image-container"
    :class="containerClass"
    :style="containerStyle"
  >
    <!-- Loading skeleton -->
    <div 
      v-if="!loaded && !error"
      class="lazy-image-skeleton"
      :class="skeletonClass"
    >
      <div class="animate-pulse bg-gray-200 dark:bg-gray-700 w-full h-full rounded">
        <div class="flex items-center justify-center h-full">
          <svg 
            v-if="showIcon"
            class="w-8 h-8 text-gray-400 dark:text-gray-500"
            fill="currentColor" 
            viewBox="0 0 20 20"
          >
            <path fill-rule="evenodd" d="M4 3a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V5a2 2 0 00-2-2H4zm12 12H4l4-8 3 6 2-4 3 6z" clip-rule="evenodd" />
          </svg>
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div 
      v-else-if="error"
      class="lazy-image-error"
      :class="errorClass"
    >
      <div class="flex flex-col items-center justify-center h-full text-gray-400 dark:text-gray-500">
        <svg class="w-8 h-8 mb-2" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span class="text-xs">Failed to load</span>
      </div>
    </div>

    <!-- Actual image -->
    <img
      v-show="loaded && !error"
      ref="image"
      :src="currentSrc"
      :alt="alt"
      :class="imageClass"
      :style="imageStyle"
      @load="onLoad"
      @error="onError"
    />

    <!-- Progressive loading overlay -->
    <div 
      v-if="progressive && loading"
      class="absolute inset-0 bg-white bg-opacity-75 dark:bg-gray-900 dark:bg-opacity-75 flex items-center justify-center transition-opacity duration-300"
      :class="{ 'opacity-0': !loading }"
    >
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue';

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  alt: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: ''
  },
  containerClass: {
    type: String,
    default: ''
  },
  containerStyle: {
    type: Object,
    default: () => ({})
  },
  imageClass: {
    type: String,
    default: 'w-full h-full object-cover'
  },
  imageStyle: {
    type: Object,
    default: () => ({})
  },
  skeletonClass: {
    type: String,
    default: ''
  },
  errorClass: {
    type: String,
    default: ''
  },
  lazy: {
    type: Boolean,
    default: true
  },
  progressive: {
    type: Boolean,
    default: false
  },
  quality: {
    type: String,
    default: 'high',
    validator: (value) => ['low', 'medium', 'high'].includes(value)
  },
  showIcon: {
    type: Boolean,
    default: true
  },
  rootMargin: {
    type: String,
    default: '50px'
  },
  threshold: {
    type: Number,
    default: 0.1
  },
  retryCount: {
    type: Number,
    default: 3
  },
  retryDelay: {
    type: Number,
    default: 1000
  }
});

const emit = defineEmits(['load', 'error', 'visible']);

// Reactive state
const imageContainer = ref(null);
const image = ref(null);
const loaded = ref(false);
const loading = ref(false);
const error = ref(false);
const visible = ref(false);
const currentRetry = ref(0);

// Intersection Observer
let observer = null;

// Computed properties
const currentSrc = computed(() => {
  if (!props.src) return '';
  
  // Add quality parameter for optimization
  const url = new URL(props.src, window.location.origin);
  if (props.quality !== 'high') {
    url.searchParams.set('quality', props.quality);
  }
  
  return url.toString();
});

// Methods
const createObserver = () => {
  if (!props.lazy || !window.IntersectionObserver) {
    loadImage();
    return;
  }

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          visible.value = true;
          emit('visible');
          loadImage();
          observer?.unobserve(entry.target);
        }
      });
    },
    {
      rootMargin: props.rootMargin,
      threshold: props.threshold
    }
  );

  if (imageContainer.value) {
    observer.observe(imageContainer.value);
  }
};

const loadImage = async () => {
  if (loading.value || loaded.value || !props.src) return;

  loading.value = true;
  error.value = false;

  try {
    // Progressive loading: load low quality first if enabled
    if (props.progressive && props.quality === 'high') {
      await loadProgressiveImage();
    } else {
      await loadSingleImage();
    }
  } catch (err) {
    handleError(err);
  }
};

const loadSingleImage = () => {
  return new Promise((resolve, reject) => {
    const img = new Image();
    
    img.onload = () => {
      loaded.value = true;
      loading.value = false;
      emit('load', img);
      resolve(img);
    };
    
    img.onerror = (err) => {
      reject(err);
    };
    
    img.src = currentSrc.value;
  });
};

const loadProgressiveImage = async () => {
  // First load low quality
  const lowQualityUrl = new URL(props.src, window.location.origin);
  lowQualityUrl.searchParams.set('quality', 'low');
  
  try {
    await new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = resolve;
      img.onerror = reject;
      img.src = lowQualityUrl.toString();
    });
    
    // Show low quality image immediately
    if (image.value) {
      image.value.src = lowQualityUrl.toString();
      loaded.value = true;
    }
    
    // Then load high quality in background
    await nextTick();
    await loadSingleImage();
  } catch (err) {
    // Fallback to single image loading
    await loadSingleImage();
  }
};

const handleError = async (err) => {
  console.warn('Image load error:', err);
  
  if (currentRetry.value < props.retryCount) {
    currentRetry.value++;
    
    // Exponential backoff
    const delay = props.retryDelay * Math.pow(2, currentRetry.value - 1);
    
    setTimeout(() => {
      loadImage();
    }, delay);
  } else {
    error.value = true;
    loading.value = false;
    emit('error', err);
  }
};

const onLoad = (event) => {
  loaded.value = true;
  loading.value = false;
  emit('load', event);
};

const onError = (event) => {
  handleError(event);
};

const retry = () => {
  currentRetry.value = 0;
  error.value = false;
  loaded.value = false;
  loadImage();
};

// Lifecycle
onMounted(() => {
  createObserver();
});

onUnmounted(() => {
  if (observer) {
    observer.disconnect();
  }
});

// Watch for src changes
watch(() => props.src, () => {
  loaded.value = false;
  error.value = false;
  loading.value = false;
  currentRetry.value = 0;
  
  if (visible.value || !props.lazy) {
    loadImage();
  }
});

// Expose methods for parent components
defineExpose({
  retry,
  reload: loadImage
});
</script>

<style scoped>
.lazy-image-container {
  position: relative;
  overflow: hidden;
}

.lazy-image-skeleton,
.lazy-image-error {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.lazy-image-error {
  background-color: #f3f4f6;
}

.dark .lazy-image-error {
  background-color: #374151;
}

/* Animation for smooth loading */
img {
  transition: opacity 0.3s ease-in-out;
}

img[v-show="false"] {
  opacity: 0;
}
</style>
